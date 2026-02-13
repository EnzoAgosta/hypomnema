"""Exception hierarchy for Hypomnema.

This module defines all custom exceptions used throughout the library.
Exceptions are organized hierarchically to allow fine-grained error handling.

Exception Hierarchy:
    Exception
    ├── DeserializationError
    │   ├── InvalidTagError
    │   ├── InvalidChildTagError
    │   ├── DuplicateChildError
    │   ├── ExtraTextError
    │   ├── MissingSegError
    │   ├── MissingBodyError
    │   ├── MissingHeaderError
    │   ├── MissingDeserializationHandlerError
    │   ├── InvalidEnumValueError
    │   ├── InvalidIntValueError
    │   └── InvalidDatetimeValueError
    ├── SerializationError
    │   ├── InvalidElementTypeError
    │   ├── InvalidChildElementError
    │   ├── MissingSerializationHandlerError
    │   └── MissingTextContentError
    ├── AttributeError
    │   ├── RequiredAttributeMissingError
    │   ├── InvalidEnumValueError
    │   ├── InvalidIntValueError
    │   ├── InvalidDatetimeValueError
    │   └── InvalidAttributeTypeError
    └── NamespaceError
        ├── MultiplePrefixesError
        ├── RestrictedURIError
        ├── RestrictedPrefixError
        ├── ExistingNamespaceError
        ├── InvalidNCNameError
        ├── UnregisteredPrefixError
        └── UnregisteredURIError

Note:
    Some exception classes inherit from multiple parents (e.g., InvalidEnumValueError
    inherits from both DeserializationError and AttributeError) to allow catching
    them through different exception hierarchies.
"""

from collections.abc import Iterable, Mapping
from enum import Enum
from typing import Any


class DeserializationError(Exception):
  """Base class for all deserialization errors."""

  pass


class SerializationError(Exception):
  """Base class for all serialization errors."""

  pass


class AttributeError(Exception):
  """Base class for attribute-related errors."""

  pass


class NamespaceError(Exception):
  """Base class for XML namespace-related errors."""

  pass


class InvalidTagError(DeserializationError):
  """Raised when an unexpected XML tag is encountered during deserialization.

  Args:
      received: The actual tag name found.
      expected: The expected tag name.

  Attributes:
      received: The actual tag name.
      expected: The expected tag name.
      message: Human-readable error message.
  """

  def __init__(self, received: str, expected: str) -> None:
    self.received = received
    self.expected = expected
    self.message = f"Invalid tag {self.received!r}, expected {self.expected!r}"
    super().__init__(self.message)


class InvalidChildTagError(DeserializationError):
  """Raised when an element contains an invalid child element.

  Args:
      parent: The parent element tag name.
      received: The invalid child tag name.
      expected: Expected child tag name(s).

  Attributes:
      parent: Parent element tag.
      received: Invalid child tag.
      expected: Expected child tag(s).
      message: Human-readable error message.
  """

  def __init__(self, parent: str, received: str, expected: str | Iterable[str]) -> None:
    self.parent = parent
    self.received = received
    self.expected = expected
    self.message = (
      f"Invalid child tag for element <{parent}>, received {received!r}, expected {expected!r}"
    )
    super().__init__(self.message)


class MissingTextContentError(DeserializationError, SerializationError):
  """Raised when an element lacks required text content.

  Args:
      element: The tag name of the element missing text.

  Attributes:
      element: Element tag name.
      message: Human-readable error message.
  """

  def __init__(self, element: str) -> None:
    self.element = element
    self.message = f"Element <{element}> does not have any text content"
    super().__init__(self.message)


class RequiredAttributeMissingError(DeserializationError, AttributeError, SerializationError):
  """Raised when a required XML attribute is missing.

  Args:
      element: The element tag name.
      attribute: The missing attribute name.

  Attributes:
      element: Element tag name.
      attribute: Missing attribute name.
      message: Human-readable error message.
  """

  def __init__(self, element: str, attribute: str) -> None:
    self.element = element
    self.attribute = attribute
    self.message = f"Required attribute {attribute!r} is  missing from element <{element}>"
    super().__init__(self.message)


class ExtraTextError(DeserializationError):
  """Raised when an element has unexpected text content.

  Args:
      element: The element tag name.
      text: The unexpected text content.

  Attributes:
      element: Element tag name.
      text: Unexpected text content.
      message: Human-readable error message.
  """

  def __init__(self, element: str, text: str) -> None:
    self.element = element
    self.text = text
    self.message = f"Element <{element}> has extra text content:\n{text!r}"
    super().__init__(self.message)


class MissingHeaderError(DeserializationError, SerializationError):
  """Raised when the TMX root lacks a required <header> element."""

  def __init__(self) -> None:
    self.message = "tmx element does not have a <header> element"
    super().__init__(self.message)


class DuplicateChildError(DeserializationError):
  """Raised when multiple child elements appear where only one is allowed.

  Args:
      parent: The parent element tag name.
      child: The duplicate child element tag name.

  Attributes:
      parent: Parent element tag.
      child: Duplicate child tag.
      message: Human-readable error message.
  """

  def __init__(self, parent: str, child: str) -> None:
    self.parent = parent
    self.child = child
    self.message = f"Multiple <{child}> elements in <{parent}>"
    super().__init__(self.message)


class InvalidEnumValueError(DeserializationError, AttributeError):
  """Raised when an attribute value cannot be converted to an enum.

  Args:
      element: The element tag name.
      attribute: The attribute name.
      value: The invalid value.
      expected: The expected enum type.

  Attributes:
      element: Element tag name.
      attribute: Attribute name.
      value: Invalid value.
      expected: Expected enum type.
      message: Human-readable error message.
  """

  def __init__(self, element: str, attribute: str, value: str, expected: type) -> None:
    self.element = element
    self.attribute = attribute
    self.value = value
    self.expected = expected
    self.message = (
      f"value {value!r} is not convertible to {expected!r}"
      f" for attribute {attribute!r} of element {element!r}"
    )
    super().__init__(self.message)


class MissingDeserializationHandlerError(DeserializationError):
  """Raised when no handler exists for a tag during deserialization.

  Args:
      obj: The tag name missing a handler.

  Attributes:
      tag: Tag name.
      message: Human-readable error message.
  """

  def __init__(self, obj: str) -> None:
    self.tag = obj
    self.message = f"Missing handler for <{obj}>"
    super().__init__(self.message)


class InvalidPolicyActionError(Exception):
  """Raised when a policy specifies an invalid action.

  Args:
      policy_name: The policy setting name.
      action: The invalid action value.
      expected: The expected action enum type.

  Attributes:
      policy_name: Policy setting name.
      action: Invalid action value.
      expected: Expected enum type.
      message: Human-readable error message.
  """

  def __init__(self, policy_name: str, action: Any, expected: type[Enum]) -> None:
    self.policy_name = policy_name
    self.action = action
    self.expected = expected
    self.message = (
      f"Invalid behavior for {policy_name!r}: received {action!r}, expected {expected!r}"
    )
    super().__init__(self.message)


class InvalidDatetimeValueError(DeserializationError, AttributeError):
  """Raised when an attribute value cannot be parsed as datetime.

  Args:
      element: The element tag name.
      attribute: The attribute name.
      value: The invalid datetime string.

  Attributes:
      element: Element tag name.
      attribute: Attribute name.
      value: Invalid value.
      message: Human-readable error message.
  """

  def __init__(self, element: str, attribute: str, value: str) -> None:
    self.element = element
    self.attribute = attribute
    self.value = value
    self.message = f"value {value!r} is not convertible to datetime for attribute {attribute!r} of element {element!r}"
    super().__init__(self.message)


class InvalidIntValueError(DeserializationError, AttributeError):
  """Raised when an attribute value cannot be parsed as integer.

  Args:
      element: The element tag name.
      attribute: The attribute name.
      value: The invalid integer string.

  Attributes:
      element: Element tag name.
      attribute: Attribute name.
      value: Invalid value.
      message: Human-readable error message.
  """

  def __init__(self, element: str, attribute: str, value: str) -> None:
    self.element = element
    self.attribute = attribute
    self.value = value
    self.message = f"value {value!r} is not convertible to int for attribute {attribute!r} of element {element!r}"
    super().__init__(self.message)


class InvalidElementTypeError(SerializationError):
  """Raised when serializing an unexpected object type.

  Args:
      received: The actual type received.
      expected: The expected type(s).

  Attributes:
      received: Actual type.
      expected: Expected type(s).
      message: Human-readable error message.
  """

  def __init__(self, received: type, expected: type | tuple[type, ...]) -> None:
    self.received = received
    self.expected = expected
    self.message = f"Invalid element type {received!r}, expected {expected!r}"
    super().__init__(self.message)


class InvalidChildElementError(SerializationError):
  """Raised when serializing contains an invalid child element type.

  Args:
      received: The actual child type received.
      expected: The expected child type(s).

  Attributes:
      received: Actual child type.
      expected: Expected child type(s).
      message: Human-readable error message.
  """

  def __init__(self, received: type, expected: type | tuple[type, ...]) -> None:
    self.received = received
    self.expected = expected
    self.message = f"Invalid child element {received!r}, expected {expected!r}"
    super().__init__(self.message)


class InvalidAttributeTypeError(AttributeError, SerializationError):
  """Raised when an attribute has an invalid type during serialization.

  Args:
      received: The actual type received.
      expected: The expected type(s).

  Attributes:
      received: Actual type.
      expected: Expected type(s).
      message: Human-readable error message.
  """

  def __init__(self, received: type, expected: type | tuple[type, ...]) -> None:
    self.received = received
    self.expected = expected
    self.message = f"Invalid attribute type {received!r}, expected {expected!r}"
    super().__init__(self.message)


class MissingSerializationHandlerError(SerializationError):
  """Raised when no handler exists for an object type during serialization.

  Args:
      obj_type: The object type missing a handler.

  Attributes:
      obj_type: Object type.
      message: Human-readable error message.
  """

  def __init__(self, obj_type: type) -> None:
    self.obj_type = obj_type
    self.message = f"Missing handler for {obj_type!r}"
    super().__init__(self.message)


class MultiplePrefixesError(NamespaceError):
  """Raised when a tag contains multiple namespace prefixes.

  Args:
      tag: The tag with multiple prefixes.

  Attributes:
      tag: Tag with multiple prefixes.
      message: Human-readable error message.
  """

  def __init__(self, tag: str) -> None:
    self.tag = tag
    self.message = f"tag {tag!r} has multiple prefixes"
    super().__init__(self.message)


class RestrictedURIError(NamespaceError):
  """Raised when attempting to modify a restricted namespace URI.

  Args:
      uri: The restricted URI.

  Attributes:
      uri: Restricted URI.
      message: Human-readable error message.
  """

  def __init__(self, uri: str) -> None:
    self.uri = uri
    self.message = f"URI {uri!r} is restricted and cannot be removed or modified"
    super().__init__(self.message)


class RestrictedPrefixError(NamespaceError):
  """Raised when attempting to modify a restricted namespace prefix.

  Args:
      prefix: The restricted prefix.

  Attributes:
      prefix: Restricted prefix.
      message: Human-readable error message.
  """

  def __init__(self, prefix: str) -> None:
    self.prefix = prefix
    self.message = f"Prefix {prefix!r} is restricted and cannot be removed or modified"
    super().__init__(self.message)


class ExistingNamespaceError(NamespaceError):
  """Raised when attempting to register an already-existing namespace.

  Args:
      prefix: The namespace prefix.
      existing_uri: The URI already registered for this prefix.
      given_uri: The new URI being registered.
      nsmap: The current namespace mapping.

  Attributes:
      prefix: Namespace prefix.
      existing_uri: Already registered URI.
      given_uri: New URI being registered.
      nsmap: Current namespace map.
      message: Human-readable error message.
  """

  def __init__(
    self, prefix: str, existing_uri: str, given_uri: str, nsmap: Mapping[str, str]
  ) -> None:
    self.prefix = prefix
    self.existing_uri = existing_uri
    self.given_uri = given_uri
    self.nsmap = nsmap
    self.message = f"Cannot register prefix {prefix!r} with URI {given_uri!r} because it is already registered with URI {existing_uri!r} in nsmap {nsmap!r}"
    super().__init__(self.message)


class InvalidNCNameError(NamespaceError):
  """Raised when a name is not a valid NCName.

  NCName (non-colonized name) is an XML identifier without colons.

  Args:
      name: The invalid name.

  Attributes:
      name: Invalid name.
      message: Human-readable error message.
  """

  def __init__(self, name: str) -> None:
    self.name = name
    self.message = f"{name!r} is not a valid NCName"
    super().__init__(self.message)


class UnregisteredPrefixError(NamespaceError):
  """Raised when a namespace prefix is not registered.

  Args:
      prefix: The unregistered prefix.
      nsmap: The current namespace mapping.

  Attributes:
      prefix: Unregistered prefix.
      nsmap: Current namespace map.
      message: Human-readable error message.
  """

  def __init__(self, prefix: str, nsmap: Mapping[str, str]) -> None:
    self.prefix = prefix
    self.nsmap = nsmap
    self.message = f"prefix {prefix!r} is not registered in nsmap {nsmap!r}"
    super().__init__(self.message)


class UnregisteredURIError(NamespaceError):
  """Raised when a namespace URI is not registered.

  Args:
      uri: The unregistered URI.
      nsmap: The current namespace mapping.

  Attributes:
      uri: Unregistered URI.
      nsmap: Current namespace map.
      message: Human-readable error message.
  """

  def __init__(self, uri: str, nsmap: Mapping[str, str]) -> None:
    self.uri = uri
    self.nsmap = nsmap
    self.message = f"URI {uri!r} is not registered in nsmap {nsmap!r}"
    super().__init__(self.message)


class MissingSegError(DeserializationError):
  """Raised when a <tuv> element lacks a required <seg> child."""

  def __init__(self) -> None:
    self.message = "tuv element does not have a <seg> element"
    super().__init__(self.message)


class MissingBodyError(DeserializationError):
  """Raised when a <tmx> element lacks a required <body> child."""

  def __init__(self) -> None:
    self.message = "tmx element does not have a <body> element"
    super().__init__(self.message)
