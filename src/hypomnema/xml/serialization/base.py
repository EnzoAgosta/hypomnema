"""Base class for element serializers.

This module defines BaseElementSerializer, the abstract base class for
all TMX element serializers. It provides common functionality for:
- Policy-driven error handling
- Attribute type validation and formatting
- Mixed content serialization
- Recursive element dispatch via emit()

Implementations must subclass this and override _serialize() for each
TMX element type.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from logging import Logger
from typing import Any, Iterable, Literal, cast, overload

from hypomnema.base.errors import (
  InvalidAttributeTypeError,
  InvalidChildElementError,
  InvalidElementTypeError,
  InvalidPolicyActionError,
  MissingTextContentError,
  RequiredAttributeMissingError,
)
from hypomnema.base.types import (
  Assoc,
  BptLike,
  EptLike,
  HiLike,
  ItLike,
  Note,
  PhLike,
  Pos,
  Prop,
  Segtype,
  SubLike,
  TmxElementLike,
)
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import (
  Behavior,
  RaiseIgnore,
  RaiseIgnoreDefault,
  RaiseIgnoreForce,
  XmlSerializationPolicy,
)


class BaseElementSerializer[TypeOfBackendElement, TypeOfTmxElement](ABC):
  """Abstract base class for TMX element serializers.

  Serializers convert Python dataclass instances into XML elements
  using the backend. Each TMX element type has a dedicated
  serializer subclass.

  Args:
      backend: XML backend for element operations.
      policy: Policy for error handling.
      logger: Logger for operations.

  Attributes:
      backend: XML backend instance.
      policy: Serialization policy.
      logger: Logger instance.

  Note:
      The emit() method must be set by the orchestrator before use.
      Call _set_emit() with the dispatch function.
  """

  def __init__(
    self, backend: XmlBackend[TypeOfBackendElement], policy: XmlSerializationPolicy, logger: Logger
  ):
    self.backend: XmlBackend[TypeOfBackendElement] = backend
    self.policy: XmlSerializationPolicy = policy
    self.logger: Logger = logger
    self._emit: Callable[[TmxElementLike], TypeOfBackendElement | None] | None = None

  def _set_emit(self, emit: Callable[[TmxElementLike], TypeOfBackendElement | None]) -> None:
    """Set the emit function for recursive serialization.

    Args:
        emit: Function to dispatch to appropriate serializer.

    Note:
        Private method called by the orchestrator (Serializer).
    """
    self._emit = emit

  def emit(self, obj: TmxElementLike) -> TypeOfBackendElement | None:
    """Dispatch object to appropriate serializer.

    Args:
        obj: TMX object to serialize.

    Returns:
        Serialized element or None if skipped.

    Raises:
        AssertionError: If emit() called before _set_emit().
    """
    assert self._emit is not None, "emit() called before set_emit() was called"
    return self._emit(obj)

  @abstractmethod
  def _serialize(self, obj: TypeOfTmxElement) -> TypeOfBackendElement | None:
    """Serialize TMX dataclass to XML element.

    Args:
        obj: TMX object to serialize.

    Returns:
        Serialized element or None if skipped.
    """
    ...

  def _log(self, behavior: Behavior, message: str, *args: object) -> None:
    """Log a message at the behavior's configured log level.

    Note:
        Private method for internal use.
    """
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, message, *args)

  def _handle_invalid_element_type[TypeOfObject](
    self, obj: TypeOfObject, expected: type | tuple[type, ...]
  ) -> TypeOfObject | None:
    """Handle unexpected object type error per policy."""
    behavior = self.policy.invalid_element_type
    self._log(behavior, "Invalid element type %r, expected %r", type(obj), expected)
    match behavior.action:
      case RaiseIgnoreForce.RAISE:
        raise InvalidElementTypeError(type(obj), expected)
      case RaiseIgnoreForce.IGNORE:
        return None
      case RaiseIgnoreForce.FORCE:
        return obj
      case _:
        raise InvalidPolicyActionError("invalid_element_type", behavior.action, RaiseIgnoreForce)

  def _handle_invalid_child_element_type(
    self, received: type, expected: type | tuple[type, ...]
  ) -> None:
    """Handle invalid child element type error per policy."""
    behavior = self.policy.invalid_child_element
    self._log(behavior, "Invalid child element %r, expected one of %r", received, expected)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise InvalidChildElementError(received, expected)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("invalid_child_element", behavior.action, RaiseIgnore)

  def _handle_missing_text_content(self, obj: Prop | Note) -> str:
    """Handle missing text content error per policy."""
    behavior = self.policy.missing_text_content
    self._log(behavior, "Element %r has no text content", type(obj))
    match behavior.action:
      case RaiseIgnoreDefault.RAISE:
        raise MissingTextContentError(obj.__class__.__name__)
      case RaiseIgnoreDefault.IGNORE:
        return cast(str, None)
      case RaiseIgnoreDefault.DEFAULT:
        return ""
      case _:
        raise InvalidPolicyActionError("missing_text_content", behavior.action, RaiseIgnoreDefault)

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

  def _set_required_attribute(
    self, element: TypeOfBackendElement, attribute: str, value: Any
  ) -> None:
    """Set required attribute with policy handling for missing values."""
    if value is None:
      self._handle_required_attribute_missing(self.backend.get_tag(element), attribute)
    self._set_attribute(element, attribute, value)

  def _set_attribute(
    self, element: TypeOfBackendElement, attribute: str, value: Any | None
  ) -> None:
    """Set attribute with automatic type conversion.

    Handles datetime, int, Pos, Segtype, Assoc, and str types.
    """
    if value is None:
      return
    match attribute:
      case "creationdate" | "changedate" | "lastusagedate":
        if not isinstance(value, datetime):
          self._handle_invalid_attribute_type(value, datetime)
        else:
          self.backend.set_attribute(element, attribute, value.strftime("%Y%m%dT%H%M%SZ"))
      case "i" | "x" | "usagecount":
        if not isinstance(value, int):
          self._handle_invalid_attribute_type(value, int)
        else:
          self.backend.set_attribute(element, attribute, str(value))
      case "pos":
        if not isinstance(value, Pos):
          self._handle_invalid_attribute_type(value, Pos)
        else:
          self.backend.set_attribute(element, attribute, value.value)
      case "segtype":
        if not isinstance(value, Segtype):
          self._handle_invalid_attribute_type(value, Segtype)
        else:
          self.backend.set_attribute(element, attribute, value.value)
      case "assoc":
        if not isinstance(value, Assoc):
          self._handle_invalid_attribute_type(value, Assoc)
        else:
          self.backend.set_attribute(element, attribute, value.value)
      case _:
        if not isinstance(value, str):
          self._handle_invalid_attribute_type(value, str)
        else:
          self.backend.set_attribute(element, attribute, str(value))

  def _serialize_children_into(
    self, element: TypeOfBackendElement, children: Iterable, expected_type: type | tuple[type, ...]
  ) -> None:
    """Serialize child elements into parent."""
    for child in children:
      if not isinstance(child, expected_type):
        self._handle_invalid_child_element_type(type(child), expected_type)
        continue
      child_element = self.emit(child)
      if child_element is not None:
        self.backend.append_child(element, child_element)

  @overload
  def _serialize_content_into(
    self,
    target: TypeOfBackendElement,
    content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike],
    sub_only: Literal[False],
  ) -> None: ...
  @overload
  def _serialize_content_into(
    self, target: TypeOfBackendElement, content: Iterable[str | SubLike], sub_only: bool = True
  ) -> None: ...
  def _serialize_content_into(
    self,
    target: TypeOfBackendElement,
    content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike] | Iterable[str | SubLike],
    sub_only: bool = True,
  ) -> None:
    """Serialize mixed content (text + inline elements) into target."""
    last_child: TypeOfBackendElement | None = None
    for item in content:
      match item:
        case str():
          if last_child is None:
            if (text := self.backend.get_text(target)) is not None:
              self.backend.set_text(target, text + item)
            else:
              self.backend.set_text(target, item)
          else:
            if (tail := self.backend.get_tail(last_child)) is not None:
              self.backend.set_tail(last_child, tail + item)
            else:
              self.backend.set_tail(last_child, item)
        case SubLike() if not sub_only:
          self._handle_invalid_child_element_type(type(item), SubLike)
        case BptLike() | EptLike() | ItLike() | PhLike() | HiLike() if sub_only:
          self._handle_invalid_child_element_type(
            type(item), (BptLike, EptLike, ItLike, PhLike, HiLike)
          )
        case SubLike() | BptLike() | EptLike() | ItLike() | PhLike() | HiLike():
          child_elem = self.emit(item)
          if child_elem is not None:
            self.backend.append_child(target, child_elem)
            last_child = child_elem
        case _:
          self._handle_invalid_child_element_type(
            type(item), (SubLike if sub_only else (BptLike, EptLike, ItLike, PhLike, HiLike))
          )

  def _handle_invalid_attribute_type(self, value: Any, expected: type | tuple[type, ...]) -> None:
    """Handle invalid attribute type error per policy."""
    behavior = self.policy.invalid_attribute_type
    self._log(behavior, "Invalid attribute type %r, expected %r", type(value), expected)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise InvalidAttributeTypeError(type(value), expected)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("invalid_attribute_type", behavior.action, RaiseIgnore)
