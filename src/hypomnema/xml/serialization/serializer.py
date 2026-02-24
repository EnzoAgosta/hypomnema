"""Serializer orchestrator for TMX serialization.

This module provides the Serializer class that coordinates serialization
of TMX documents. It maintains a registry of object handlers and dispatches
dataclass instances to the appropriate handler.
"""

from collections.abc import Mapping
from functools import cached_property
from logging import Logger, getLogger
from hypomnema.base.errors import InvalidPolicyActionError, MissingSerializationHandlerError
from hypomnema.base.types import (
  BptLike,
  EptLike,
  HeaderLike,
  HiLike,
  ItLike,
  NoteLike,
  PhLike,
  PropLike,
  SubLike,
  TmxElementLike,
  TmxLike,
  TuLike,
  TuvLike,
)
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import RaiseIgnoreDefault, XmlSerializationPolicy
from hypomnema.xml.serialization.handlers import (
  BptSerializer,
  EptSerializer,
  HeaderSerializer,
  HiSerializer,
  ItSerializer,
  NoteSerializer,
  PhSerializer,
  PropSerializer,
  SubSerializer,
  TmxSerializer,
  TuSerializer,
  TuvSerializer,
)
from hypomnema.xml.serialization.base import BaseElementSerializer


class Serializer[TypeOfBackendElement]:
  """Orchestrates TMX serialization.

  The Serializer maintains a registry of object handlers and dispatches
  TMX dataclass instances to the appropriate handler based on type.
  It also injects the emit() function into handlers for recursive serialization.

  Args:
      backend: XML backend for element operations.
      policy: Policy for error handling (default: strict).
      logger: Logger for operations.
      handlers: Custom object handlers (default: built-in handlers).

  Attributes:
      backend: XML backend.
      policy: Serialization policy.
      logger: Logger instance.
  """

  def __init__(
    self,
    backend: XmlBackend[TypeOfBackendElement],
    policy: XmlSerializationPolicy | None = None,
    logger: Logger | None = None,
    handlers: Mapping[type, BaseElementSerializer] | None = None,
  ):
    self.backend: XmlBackend[TypeOfBackendElement] = backend
    self.policy: XmlSerializationPolicy = policy or XmlSerializationPolicy()
    self.logger: Logger = logger or getLogger(__name__)
    if handlers is None:
      self.logger.debug("Using default handlers")
      handlers = self._default_handlers
    self.handlers = handlers

    for handler in self.handlers.values():
      handler._set_emit(self.serialize)

  @cached_property
  def _default_handlers(self) -> dict[type, BaseElementSerializer]:
    """Default handler instances for all TMX element types.

    Returns:
        Mapping of types to handler instances.
    """
    handlers = self._get_default_handlers()
    for handler in handlers.values():
      handler._set_emit(self.serialize)
    return handlers

  def _get_default_handlers(self) -> dict[type, BaseElementSerializer]:
    """Create default handler instances."""
    return {
      HeaderLike: HeaderSerializer(self.backend, self.policy, self.logger),
      PropLike: PropSerializer(self.backend, self.policy, self.logger),
      NoteLike: NoteSerializer(self.backend, self.policy, self.logger),
      TmxLike: TmxSerializer(self.backend, self.policy, self.logger),
      TuLike: TuSerializer(self.backend, self.policy, self.logger),
      TuvLike: TuvSerializer(self.backend, self.policy, self.logger),
      PhLike: PhSerializer(self.backend, self.policy, self.logger),
      SubLike: SubSerializer(self.backend, self.policy, self.logger),
      ItLike: ItSerializer(self.backend, self.policy, self.logger),
      BptLike: BptSerializer(self.backend, self.policy, self.logger),
      HiLike: HiSerializer(self.backend, self.policy, self.logger),
      EptLike: EptSerializer(self.backend, self.policy, self.logger),
    }

  def _resolve_handler(self, obj: object) -> BaseElementSerializer | None:
    """Resolve handler for object type, applying policy for missing handlers.

    Args:
        obj_type: Object type to serialize.

    Returns:
        Handler instance or None if skipped per policy.

    Raises:
        MissingSerializationHandlerError: If no handler found and policy raises.
    """
    _handler = None
    for handler_type in self.handlers:
      if isinstance(obj, handler_type):
        _handler = self.handlers[handler_type]
        return _handler

    behavior = self.policy.missing_serialization_handler
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, "Missing handler for <%s>", obj)
    match behavior.action:
      case RaiseIgnoreDefault.RAISE:
        raise MissingSerializationHandlerError(type(obj))
      case RaiseIgnoreDefault.IGNORE:
        pass
      case RaiseIgnoreDefault.DEFAULT:
        for handler_type in self._default_handlers:
          if isinstance(obj, handler_type):
            _handler = self._default_handlers[handler_type]
            break
        else:
          raise MissingSerializationHandlerError(type(obj))
      case _:
        raise InvalidPolicyActionError(
          "missing_serialization_handler", behavior.action, RaiseIgnoreDefault
        )
    return _handler

  def serialize(
    self, obj: TmxElementLike, *, handler: BaseElementSerializer | None = None
  ) -> TypeOfBackendElement | None:
    """Serialize a TMX dataclass to an XML element.

    Args:
        obj: TMX object to serialize.
        handler: Optional specific handler to use (default: auto-resolve by type).

    Returns:
        Serialized element or None if skipped.
    """
    if handler is None:
      handler = self._resolve_handler(type(obj))
    return handler._serialize(obj) if handler is not None else None
