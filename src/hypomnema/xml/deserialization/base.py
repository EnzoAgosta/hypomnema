from enum import StrEnum
from abc import ABC, abstractmethod
from datetime import datetime
from logging import Logger
from typing import Callable

from hypomnema.base.errors import AttributeDeserializationError, XmlDeserializationError
from hypomnema.base.types import BaseElement, BaseInlineElement
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import DeserializationPolicy

__all__ = ["BaseElementDeserializer", "InlineContentDeserializerMixin"]


class BaseElementDeserializer[BackendElementType, TmxElementType: BaseElement](ABC):
  """
  Abstract base class for converting XML elements into TMX objects.

  Parameters
  ----------
  backend : XMLBackend
      The XML library wrapper used to traverse and inspect elements.
  policy : DeserializationPolicy
      The configuration for handling errors and logging during deserialization.
  logger : Logger
      The logging instance for reporting policy violations.

  Attributes
  ----------
  backend : XMLBackend[BackendElementType]
      The XML library wrapper.
  policy : DeserializationPolicy
      The deserialization configuration.
  logger : Logger
      The logging instance.
  """

  def __init__(self, backend: XmlBackend, policy: DeserializationPolicy, logger: Logger):
    self.backend: XmlBackend[BackendElementType] = backend
    self.policy = policy
    self.logger = logger
    self._emit: Callable[[BackendElementType], BaseElement | None] | None = None

  def _set_emit(self, emit: Callable[[BackendElementType], BaseElement | None]) -> None:
    """
    Set the dispatch function for recursive deserialization.

    Parameters
    ----------
    emit : Callable[[BackendElementType], BaseElement | None]
        A function that dispatches XML elements to their specific deserializers.
    """
    self._emit = emit

  def emit(self, obj: BackendElementType) -> BaseElement | None:
    """
    Invoke the dispatcher to deserialize an XML element.

    Parameters
    ----------
    obj : BackendElementType
        The backend-specific XML element to deserialize.

    Returns
    -------
    BaseElement | None
        The deserialized TMX object, or None if the dispatcher returns None.

    Raises
    ------
    AssertionError
        If called before the dispatcher is set via `_set_emit`.
    """
    assert self._emit is not None, "emit() called before set_emit() was called"
    return self._emit(obj)

  @abstractmethod
  def _deserialize(self, element: BackendElementType) -> BaseElement | None:
    """
    Perform the actual deserialization of the specific XML element.

    Parameters
    ----------
    element : BackendElementType
        The XML element instance to convert.

    Returns
    -------
    BaseElement | None
        The resulting TMX object instance.
    """
    ...

  def _handle_missing_attribute(
    self, element: BackendElementType, attribute: str, required: bool
  ) -> None:
    """
    Handle cases where an expected XML attribute is missing according to policy.

    Parameters
    ----------
    element : BackendElementType
        The XML element being inspected.
    attribute : str
        The name of the missing attribute.
    required : bool
        Whether the attribute is mandatory.

    Raises
    ------
    AttributeDeserializationError
        If the attribute is required and the policy behavior is "raise".
    """
    if required:
      self.logger.log(
        self.policy.required_attribute_missing.log_level, "Required attribute %r is None", attribute
      )
      if self.policy.required_attribute_missing.behavior == "raise":
        raise AttributeDeserializationError(f"Required attribute {attribute!r} is None")
    return

  def _parse_attribute_as_datetime(
    self, element: BackendElementType, attribute: str, required: bool
  ) -> datetime | None:
    """
    Retrieve and parse an attribute value as an ISO 8601 datetime.

    Parameters
    ----------
    element : BackendElementType
        The XML element containing the attribute.
    attribute : str
        The name of the attribute.
    required : bool
        Whether the attribute is mandatory.

    Returns
    -------
    datetime | None
        The parsed datetime object, or None if missing or invalid.

    Raises
    ------
    AttributeDeserializationError
        If parsing fails or a required attribute is missing and policy is "raise".
    """
    value = self.backend.get_attribute(element, attribute)
    if value is None:
      self._handle_missing_attribute(element, attribute, required)
      return
    try:
      return datetime.fromisoformat(value)
    except ValueError as e:
      self.logger.log(
        self.policy.invalid_attribute_value.log_level,
        "Cannot convert %r to a datetime object for attribute %s",
        value,
        attribute,
      )
      if self.policy.invalid_attribute_value.behavior == "raise":
        raise AttributeDeserializationError(
          f"Cannot convert {value!r} to a datetime object for attribute {attribute}"
        ) from e

  def _parse_attribute_as_int(
    self, element: BackendElementType, attribute: str, required: bool
  ) -> int | None:
    """
    Retrieve and parse an attribute value as an integer.

    Parameters
    ----------
    element : BackendElementType
        The XML element containing the attribute.
    attribute : str
        The name of the attribute.
    required : bool
        Whether the attribute is mandatory.

    Returns
    -------
    int | None
        The parsed integer, or None if missing or invalid.

    Raises
    ------
    AttributeDeserializationError
        If parsing fails or a required attribute is missing and policy is "raise".
    """
    value = self.backend.get_attribute(element, attribute)
    if value is None:
      self._handle_missing_attribute(element, attribute, required)
      return
    try:
      return int(value)
    except ValueError as e:
      self.logger.log(
        self.policy.invalid_attribute_value.log_level,
        "Cannot convert %r to an int for attribute %s",
        value,
        attribute,
      )
      if self.policy.invalid_attribute_value.behavior == "raise":
        raise AttributeDeserializationError(
          f"Cannot convert {value!r} to an int for attribute {attribute}"
        ) from e
      return

  def _parse_attribute_as_enum[EnumType: StrEnum](
    self, element: BackendElementType, attribute: str, enum_type: type[EnumType], required: bool
  ) -> EnumType | None:
    """
    Retrieve and parse an attribute value as a specific StrEnum member.

    Parameters
    ----------
    element : BackendElementType
        The XML element containing the attribute.
    attribute : str
        The name of the attribute.
    enum_type : type[EnumType]
        The StrEnum class to use for validation.
    required : bool
        Whether the attribute is mandatory.

    Returns
    -------
    EnumType | None
        The matching enum member, or None if missing or invalid.

    Raises
    ------
    AttributeDeserializationError
        If the value is not a valid enum member or a required attribute is
        missing and policy is "raise".
    """
    value = self.backend.get_attribute(element, attribute)
    if value is None:
      self._handle_missing_attribute(element, attribute, required)
      return
    try:
      return enum_type(value)
    except ValueError as e:
      self.logger.log(
        self.policy.invalid_attribute_value.log_level,
        "Value %r is not a valid enum value for attribute %s",
        value,
        attribute,
      )
      if self.policy.invalid_attribute_value.behavior == "raise":
        raise AttributeDeserializationError(
          f"Value {value!r} is not a valid enum value for attribute {attribute}"
        ) from e
      return

  def _parse_attribute_as_str(
    self, element: BackendElementType, attribute: str, required: bool
  ) -> str | None:
    """
    Retrieve an attribute value as a string.

    Parameters
    ----------
    element : BackendElementType
        The XML element containing the attribute.
    attribute : str
        The name of the attribute.
    required : bool
        Whether the attribute is mandatory.

    Returns
    -------
    str | None
        The attribute string, or None if missing.
    """
    value = self.backend.get_attribute(element, attribute)
    if value is None:
      self._handle_missing_attribute(element, attribute, required)
      return
    return value


class InlineContentDeserializerMixin[BackendElementType]:
  """
  Mixin for deserializing mixed XML content into a list of strings and objects.

  Attributes
  ----------
  backend : XMLBackend[BackendElementType]
      The XML library wrapper.
  policy : DeserializationPolicy
      The deserialization configuration.
  logger : Logger
      The logging instance.
  emit : Callable[[BackendElementType], BaseElement | None]
      Dispatcher for deserializing child XML elements.
  """

  backend: XmlBackend[BackendElementType]
  policy: DeserializationPolicy
  logger: Logger
  emit: Callable[[BackendElementType], BaseElement | None]
  __slots__ = tuple()

  def _deserialize_content(
    self, source: BackendElementType, allowed: tuple[str, ...]
  ) -> list[BaseInlineElement | str]:
    """
    Extract text and child elements from an XML element.

    Handles recursive parsing of children and associated tail text.

    Parameters
    ----------
    source : BackendElementType
        The XML element containing mixed content.
    allowed : tuple[str, ...]
        The permitted tags for child elements.

    Returns
    -------
    list[BaseInlineElement | str]
        A list containing strings (text/tails) and deserialized objects.

    Raises
    ------
    XmlDeserializationError
        If an invalid child tag is encountered, or the element is empty,
        and the respective policy behavior is "raise".
    """
    source_tag = self.backend.get_tag(source)
    result = []
    if (text := self.backend.get_text(source)) is not None:
      result.append(text)
    for child in self.backend.iter_children(source):
      child_tag = self.backend.get_tag(child)
      if child_tag not in allowed:
        self.logger.log(
          self.policy.invalid_child_element.log_level,
          "Incorrect child element in %s: expected one of %s, got %s",
          source_tag,
          ", ".join(allowed),
          child_tag,
        )
        if self.policy.invalid_child_element.behavior == "raise":
          raise XmlDeserializationError(
            f"Incorrect child element in {source_tag}: expected one of {', '.join(allowed)}, got {child_tag}"
          )
        continue
      child_obj = self.emit(child)
      if child_obj is not None:
        result.append(child_obj)
      if (tail := self.backend.get_tail(child)) is not None:
        result.append(tail)
    if result == []:
      self.logger.log(self.policy.empty_content.log_level, "Element <%s> is empty", source_tag)
      if self.policy.empty_content.behavior == "raise":
        raise XmlDeserializationError(f"Element <{source_tag}> is empty")
      if self.policy.empty_content.behavior == "empty":
        self.logger.log(self.policy.empty_content.log_level, "Falling back to an empty string")
        result.append("")
    return result
