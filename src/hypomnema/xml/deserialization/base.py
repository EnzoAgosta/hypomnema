"""Base class for element deserializers.

This module defines BaseElementDeserializer, the abstract base class for
all TMX element deserializers. It provides common functionality for:
- Policy-driven error handling
- Type conversion (datetime, int, enum)
- Mixed content parsing
- Recursive element dispatch via emit()

Implementations must subclass this and override _deserialize() for each
TMX element type.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from logging import Logger
from typing import Any, Callable, Literal, cast, overload

from hypomnema.base.errors import (
  ExtraTextError,
  InvalidChildTagError,
  InvalidDatetimeValueError,
  InvalidEnumValueError,
  InvalidIntValueError,
  InvalidPolicyActionError,
  InvalidTagError,
  MissingTextContentError,
  RequiredAttributeMissingError,
)
from hypomnema.base.types import BaseElement, Bpt, Ept, Hi, It, Ph, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import (
  RaiseIgnore,
  Behavior,
  RaiseIgnoreForce,
  RaiseNoneKeep,
  XmlDeserializationPolicy,
)


class BaseElementDeserializer[TypeOfBackendElement, TypeOfTmxElement: BaseElement](ABC):
  """Abstract base class for TMX element deserializers.

  Deserializers convert XML elements from the backend representation
  into Python dataclass instances. Each TMX element type has a dedicated
  deserializer subclass.

  Args:
      backend: XML backend for element operations.
      policy: Policy for error handling.
      logger: Logger for operations.

  Attributes:
      backend: XML backend instance.
      policy: Deserialization policy.
      logger: Logger instance.

  Note:
      The emit() method must be set by the orchestrator before use.
      Call _set_emit() with the dispatch function.
  """

  def __init__(
    self,
    backend: XmlBackend[TypeOfBackendElement],
    policy: XmlDeserializationPolicy,
    logger: Logger,
  ) -> None:
    self.backend = backend
    self.policy = policy
    self.logger = logger
    self._emit: Callable[[TypeOfBackendElement], BaseElement | None] | None = None

  def _log(self, behavior: Behavior, message: str, *args: object) -> None:
    """Log a message at the behavior's configured log level.

    Args:
        behavior: Behavior containing log level.
        message: Log message format.
        *args: Format arguments.

    Note:
        Private method for internal use.
    """
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, message, *args)

  def _set_emit(self, emit: Callable[[TypeOfBackendElement], BaseElement | None]) -> None:
    """Set the emit function for recursive deserialization.

    Args:
        emit: Function to dispatch to appropriate deserializer.

    Note:
        Private method called by the orchestrator (Deserializer).
    """
    self._emit = emit

  def emit(self, obj: TypeOfBackendElement) -> BaseElement | None:
    """Dispatch element to appropriate deserializer.

    Args:
        obj: XML element to deserialize.

    Returns:
        Deserialized object or None if skipped.

    Raises:
        AssertionError: If emit() called before _set_emit().
    """
    assert self._emit is not None, "emit() called before set_emit() was called"
    return self._emit(obj)

  @abstractmethod
  def _deserialize(self, element: TypeOfBackendElement) -> TypeOfTmxElement | None:
    """Deserialize XML element to TMX dataclass.

    Args:
        element: XML element from backend.

    Returns:
        Deserialized object or None if skipped.
    """
    ...

  def _parse_required_attribute(self, element: TypeOfBackendElement, attribute: str) -> str:
    """Parse required attribute with policy handling.

    Args:
        element: XML element.
        attribute: Attribute name.

    Returns:
        Attribute value.
    """
    value = self.backend.get_attribute(element, attribute)
    if value is None:
      self._handle_required_attribute_missing(self.backend.get_tag(element), attribute)
    return cast(str, value)

  def try_convert_to_datetime(self, element: str, value: str, attribute: str) -> datetime:
    """Convert string to datetime with policy handling.

    Args:
        element: Element tag name (for error messages).
        value: Attribute value.
        attribute: Attribute name.

    Returns:
        Parsed datetime or fallback per policy.
    """
    try:
      return datetime.fromisoformat(value)
    except ValueError:
      return self._handle_invalid_datetime_value(element, attribute, value, datetime)

  def try_convert_to_int(self, element: str, value: str, attribute: str) -> int:
    """Convert string to int with policy handling.

    Args:
        element: Element tag name (for error messages).
        value: Attribute value.
        attribute: Attribute name.

    Returns:
        Parsed integer or fallback per policy.
    """
    try:
      return int(value)
    except ValueError:
      return self._handle_invalid_int_value(element, attribute, value, int)

  def try_convert_to_enum[TypeOfEnum: Enum](
    self, element: str, value: str, attribute: str, enum_type: type[TypeOfEnum]
  ) -> TypeOfEnum:
    """Convert string to enum with policy handling.

    Args:
        element: Element tag name (for error messages).
        value: Attribute value.
        attribute: Attribute name.
        enum_type: Target enum type.

    Returns:
        Enum value or fallback per policy.
    """
    try:
      return enum_type(value)
    except ValueError:
      return self._handle_invalid_enum_value(element, attribute, value, enum_type)

  @overload
  def _deserialize_content(
    self, source: TypeOfBackendElement, allowed_tags: tuple[Literal["sub"]]
  ) -> list[Sub | str]: ...
  @overload
  def _deserialize_content(
    self,
    source: TypeOfBackendElement,
    allowed_tags: tuple[Literal["bpt", "ept", "it", "ph", "hi"], ...],
  ) -> list[Bpt | Ept | It | Ph | Hi | str]: ...
  def _deserialize_content(
    self,
    source: TypeOfBackendElement,
    allowed_tags: tuple[Literal["sub"]] | tuple[Literal["bpt", "ept", "it", "ph", "hi"], ...],
  ) -> list[Bpt | Ept | It | Ph | Hi | str] | list[Sub | str]:
    """Deserialize mixed content (text + inline elements).

    Args:
        source: XML element containing mixed content.
        allowed_tags: Allowed child element tag names.

    Returns:
        List of strings and inline element objects.
    """
    result: list[Any] = []
    if (text := self.backend.get_text(source)) is not None:
      result.append(text)
    for child in self.backend.iter_children(source):
      child_tag = self.backend.get_tag(child)
      if child_tag not in allowed_tags:
        self._handle_invalid_child_tag(self.backend.get_tag(source), child_tag, allowed_tags)
        continue

      child_obj = self.emit(child)
      if child_obj is not None:
        result.append(child_obj)
      if (tail := self.backend.get_tail(child)) is not None:
        result.append(tail)
    return result

  def _handle_invalid_tag(self, received: str, expected: str) -> None | str:
    """Handle unexpected tag error per policy.

    Args:
        received: Actual tag name.
        expected: Expected tag name.

    Returns:
        None to skip, or string to use per FORCE policy.
    """
    behavior = self.policy.invalid_tag
    self._log(behavior, "Invalid tag %r, expected %r", received, expected)
    match behavior.action:
      case RaiseIgnoreForce.RAISE:
        raise InvalidTagError(received, expected)
      case RaiseIgnoreForce.IGNORE:
        return None
      case RaiseIgnoreForce.FORCE:
        return received
      case _:
        raise InvalidPolicyActionError("invalid_tag", behavior.action, RaiseIgnoreForce)

  def _handle_invalid_child_tag(
    self, parent: str, received: str, expected: str | tuple[str, ...]
  ) -> None:
    """Handle invalid child tag error per policy."""
    behavior = self.policy.invalid_child_tag
    self._log(
      behavior,
      "Invalid child tag for element <%s>, received %r, expected %r",
      parent,
      received,
      expected,
    )
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise InvalidChildTagError(parent, received, expected)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("invalid_child_tag", behavior.action, RaiseIgnore)

  def _handle_missing_text_content(self, element: str) -> str:
    """Handle missing text content error per policy."""
    behavior = self.policy.missing_text_content
    self._log(behavior, "Element %r has no text content", element)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise MissingTextContentError(element)
      case RaiseIgnore.IGNORE:
        return cast(str, None)
      case _:
        raise InvalidPolicyActionError("missing_text_content", behavior.action, RaiseIgnore)

  def _handle_extra_text(self, element: str, text: str) -> None:
    """Handle unexpected text content error per policy."""
    behavior = self.policy.extra_text
    self._log(behavior, "Element %r has extra text content:\n%s", element, text)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise ExtraTextError(element, text)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("extra_text", behavior.action, RaiseIgnore)

  def _handle_required_attribute_missing(self, element: str, attribute: str) -> None:
    """Handle missing required attribute error per policy."""
    behavior = self.policy.required_attribute_missing
    self._log(behavior, "Required attribute %r is missing from element %r", attribute, element)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise RequiredAttributeMissingError(element, attribute)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("required_attribute_missing", behavior.action, RaiseIgnore)

  def _handle_invalid_enum_value[TypeOfEnum: Enum](
    self, element: str, attribute: str, value: str, enum_type: type[TypeOfEnum]
  ) -> TypeOfEnum:
    """Handle invalid enum value error per policy."""
    behavior = self.policy.invalid_enum_value
    self._log(behavior, "Invalid attribute %r for element %r.", attribute, element)
    match behavior.action:
      case RaiseNoneKeep.RAISE:
        raise InvalidEnumValueError(element, attribute, value, enum_type)
      case RaiseNoneKeep.NONE:
        return cast(TypeOfEnum, None)
      case RaiseNoneKeep.KEEP:
        return cast(TypeOfEnum, value)
      case _:
        raise InvalidPolicyActionError("invalid_enum_value", behavior.action, RaiseNoneKeep)

  def _handle_invalid_datetime_value(
    self, element: str, attribute: str, value: str, expected: type[datetime]
  ) -> datetime:
    """Handle invalid datetime value error per policy."""
    behavior = self.policy.invalid_datetime_value
    self._log(behavior, "Invalid attribute %r for element %r.", attribute, element)
    match behavior.action:
      case RaiseNoneKeep.RAISE:
        raise InvalidDatetimeValueError(element, attribute, value)
      case RaiseNoneKeep.NONE:
        return cast(datetime, None)
      case RaiseNoneKeep.KEEP:
        return cast(datetime, value)
      case _:
        raise InvalidPolicyActionError("invalid_datetime_value", behavior.action, RaiseNoneKeep)

  def _handle_invalid_int_value(
    self, element: str, attribute: str, value: str, expected: type[int]
  ) -> int:
    """Handle invalid int value error per policy."""
    behavior = self.policy.invalid_int_value
    self._log(behavior, "Invalid attribute %r for element %r.", attribute, element)
    match behavior.action:
      case RaiseNoneKeep.RAISE:
        raise InvalidIntValueError(element, attribute, value)
      case RaiseNoneKeep.NONE:
        return cast(int, None)
      case RaiseNoneKeep.KEEP:
        return cast(int, value)
      case _:
        raise InvalidPolicyActionError("invalid_int_value", behavior.action, RaiseNoneKeep)
