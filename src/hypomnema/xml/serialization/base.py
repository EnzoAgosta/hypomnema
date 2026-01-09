from enum import StrEnum
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from logging import Logger

from hypomnema.base.errors import AttributeSerializationError, XmlSerializationError
from hypomnema.base.types import InlineElement, Tuv, BaseElement, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import SerializationPolicy

__all__ = ["BaseElementSerializer"]


class BaseElementSerializer[TypeOfBackendElement, TypeOfTmxElement: BaseElement](ABC):
  """
  Abstract base class for converting TMX objects into XML elements.

  Parameters
  ----------
  backend : XMLBackend[BackendElementType]
      The XML library wrapper used to create and manipulate elements.
  policy : SerializationPolicy
      The configuration for handling errors and logging during serialization.
  logger : Logger
      The logging instance for reporting policy violations.

  Attributes
  ----------
  backend : XMLBackend[BackendElementType]
      The XML library wrapper.
  policy : SerializationPolicy
      The serialization configuration.
  logger : Logger
      The logging instance.
  """

  def __init__(
    self, backend: XmlBackend[TypeOfBackendElement], policy: SerializationPolicy, logger: Logger
  ):
    self.backend: XmlBackend[TypeOfBackendElement] = backend
    self.policy: SerializationPolicy = policy
    self.logger: Logger = logger
    self._emit: Callable[[BaseElement], TypeOfBackendElement | None] | None = None

  def _set_emit(self, emit: Callable[[BaseElement], TypeOfBackendElement | None]) -> None:
    """
    Set the dispatch function for recursive serialization.
    Must be called before `emit()` is called.

    Parameters
    ----------
    emit : Callable[[BaseElement], BackendElementType | None]
        A function that dispatches objects to their specific serializers.
    """
    self._emit = emit

  def emit(self, obj: BaseElement) -> TypeOfBackendElement | None:
    """
    Invoke the dispatcher to serialize a BaseElement object.

    Parameters
    ----------
    obj : BaseElement
        The object to serialize.

    Returns
    -------
    BackendElementType | None
        The serialized XML element, or None if the dispatcher returns None.

    Raises
    ----------
    AssertionError
        If called before the dispatcher is set via `_set_emit`.
    """
    assert self._emit is not None, "emit() called before set_emit() was called"
    return self._emit(obj)

  @abstractmethod
  def _serialize(self, obj: TypeOfTmxElement) -> TypeOfBackendElement | None:
    """
    Perform the actual serialization of the specific TMX object type.

    Parameters
    ----------
    obj : TmxElementType
        The TMX object instance to convert.

    Returns
    -------
    BackendElementType | None
        The resulting XML element.
    """
    ...

  def _handle_missing_attribute(
    self, target: TypeOfBackendElement, attribute: str, required: bool
  ) -> None:
    """
    Handle cases where an attribute value is None according to policy.

    Parameters
    ----------
    target : BackendElementType
        The XML element where the attribute would be set.
    attribute : str
        The name of the attribute.
    required : bool
        Whether the TMX specification requires this attribute.

    Raises
    ------
    AttributeSerializationError
        If the attribute is required and the policy behavior is "raise".
    """
    if required:
      self.logger.log(
        self.policy.required_attribute_missing.log_level,
        "Required attribute %r is missing on element <%s>",
        attribute,
        self.backend.get_tag(target),
      )
      if self.policy.required_attribute_missing.behavior == "raise":
        raise AttributeSerializationError(
          f"Required attribute {attribute!r} is missing on element <{self.backend.get_tag(target)}>"
        )
    return

  def _set_datetime_attribute(
    self, target: TypeOfBackendElement, value: datetime | None, attribute: str, required: bool
  ) -> None:
    """
    Serialize and set a datetime attribute in ISO 8601 format.

    Parameters
    ----------
    target : BackendElementType
        The XML element to modify.
    value : datetime | None
        The datetime object to serialize.
    attribute : str
        The name of the attribute in the XML element.
    required : bool
        Whether the attribute is mandatory.
    """
    if value is None:
      self._handle_missing_attribute(target, attribute, required)
      return
    if not isinstance(value, datetime):
      self.logger.log(
        self.policy.invalid_attribute_type.log_level,
        "Attribute %r is not a datetime object",
        attribute,
      )
      if self.policy.invalid_attribute_type.behavior == "raise":
        raise AttributeSerializationError(f"Attribute {attribute!r} is not a datetime object")
      return
    self.backend.set_attribute(target, attribute, value.isoformat(), unsafe=True)

  def _set_int_attribute(
    self, target: TypeOfBackendElement, value: int | None, attribute: str, required: bool
  ) -> None:
    """
    Serialize and set an integer attribute.

    Parameters
    ----------
    target : BackendElementType
        The XML element to modify.
    value : int | None
        The integer value to serialize.
    attribute : str
        The name of the attribute in the XML element.
    required : bool
        Whether the attribute is mandatory.
    """
    if value is None:
      self._handle_missing_attribute(target, attribute, required)
      return
    if not isinstance(value, int):
      self.logger.log(
        self.policy.invalid_attribute_type.log_level, "Attribute %r is not an int", attribute
      )
      if self.policy.invalid_attribute_type.behavior == "raise":
        raise AttributeSerializationError(f"Attribute {attribute!r} is not an int")
      return
    self.backend.set_attribute(target, attribute, str(value))

  def _set_enum_attribute[EnumType: StrEnum](
    self,
    target: TypeOfBackendElement,
    value: EnumType | None,
    attribute: str,
    enum_type: type[EnumType],
    required: bool,
  ) -> None:
    """
    Serialize and set an attribute from a string-based Enum.

    Parameters
    ----------
    target : BackendElementType
        The XML element to modify.
    value : EnumType | None
        The enum member to serialize.
    attribute : str
        The name of the attribute in the XML element.
    enum_type : type[EnumType]
        The specific Enum class for type validation.
    required : bool
        Whether the attribute is mandatory.
    """
    if value is None:
      self._handle_missing_attribute(target, attribute, required)
      return
    if not isinstance(value, enum_type):
      self.logger.log(
        self.policy.invalid_attribute_type.log_level,
        "Attribute %r is not a member of %s",
        attribute,
        enum_type,
      )
      if self.policy.invalid_attribute_type.behavior == "raise":
        raise AttributeSerializationError(
          f"Attribute {attribute!r} is not a member of {enum_type!r}"
        )
      return
    self.backend.set_attribute(target, attribute, value.value)

  def _set_str_attribute(
    self, target: TypeOfBackendElement, value: str | None, attribute: str, required: bool
  ) -> None:
    """
    Serialize and set a string attribute.

    Parameters
    ----------
    target : BackendElementType
        The XML element to modify.
    value : str | None
        The string value to serialize.
    attribute : str
        The name of the attribute in the XML element.
    required : bool
        Whether the attribute is mandatory.
    """
    if value is None:
      self._handle_missing_attribute(target, attribute, required)
      return
    if not isinstance(value, str):
      self.logger.log(
        self.policy.invalid_attribute_type.log_level, "Attribute %r is not a string", attribute
      )
      if self.policy.invalid_attribute_type.behavior == "raise":
        raise AttributeSerializationError(f"Attribute {attribute!r} is not a string")
      return
    self.backend.set_attribute(target, attribute, value)

  def _serialize_content_into(
    self,
    source: InlineElement | Tuv,
    target: TypeOfBackendElement,
    allowed: tuple[type[BaseElement | Sub], ...],
  ) -> None:
    """
    Iteratively serialize mixed text and XML elements into a target element.

    Parameters
    ----------
    source : InlineElement | Tuv
        The object containing the mixed content list.
    target : BackendElementType
        The XML element to populate.
    allowed : tuple[type[InlineElement], ...]
        The permitted types for inline child elements.

    Raises
    ------
    XmlSerializationError
        If a child object type is not a string or in the allowed tuple,        and policy behavior is "raise".
    """
    last_child: TypeOfBackendElement | None = None
    for item in source.content:
      if isinstance(item, str):
        if last_child is None:
          text = self.backend.get_text(target) or ""
          self.backend.set_text(target, text + item)
        else:
          tail = self.backend.get_tail(last_child) or ""
          self.backend.set_tail(last_child, tail + item)

      elif isinstance(item, allowed):
        child_elem = self.emit(item)
        if child_elem is not None:
          self.backend.append_child(target, child_elem)
          last_child = child_elem

      else:
        allowed_names = ", ".join(x.__name__ for x in allowed)
        self.logger.log(
          self.policy.invalid_content_type.log_level,
          "Incorrect child element in %s: expected one of %s, got %r",
          source.__class__.__name__,
          allowed_names,
          item.__class__.__name__,
        )
        if self.policy.invalid_content_type.behavior == "raise":
          raise XmlSerializationError(
            f"Incorrect child element in {source.__class__.__name__}:"
            f" expected one of {allowed_names},"
            f" got {item.__class__.__name__!r}"
          )
        continue

  def _serialize_children[TypeofChildItem: BaseElement](
    self,
    children: list[TypeofChildItem],
    target: TypeOfBackendElement,
    expected_type: type[TypeofChildItem],
  ) -> None:
    """
    Serialize a list of child objects and append them to a target element.

    Parameters
    ----------
    children : list[ChildType]
        The list of TMX objects to serialize.
    target : BackendElementType
        The parent XML element to receive the children.
    expected_type : type[ChildType]
        The required type for objects in the children list.

    Raises
    ------
    XmlSerializationError
        If a child object does not match `expected_type` and policy
        behavior is "raise".
    """
    for child in children:
      if isinstance(child, expected_type):
        child_element = self.emit(child)
        if child_element is not None:
          self.backend.append_child(target, child_element)
      else:
        self.logger.log(
          self.policy.invalid_child_element.log_level,
          "Invalid child element %r when serializing <%s>",
          child.__class__.__name__,
          self.backend.get_tag(target),
        )
        if self.policy.invalid_child_element.behavior == "raise":
          raise XmlSerializationError(
            f"Invalid child element {child.__class__.__name__!r} when serializing <{self.backend.get_tag(target)}>"
          )
