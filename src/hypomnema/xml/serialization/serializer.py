"""Serializer orchestrator for TMX serialization.

This module provides the Serializer class that coordinates serialization
of TMX documents. It maintains a registry of object handlers and dispatches
dataclass instances to the appropriate handler.
"""

from collections.abc import Mapping
from functools import cached_property
from logging import Logger, getLogger
from hypomnema.base.errors import MissingSerializationHandlerError
from hypomnema.base.types import (
  BaseElement,
  Bpt,
  BptBase,
  Ept,
  EptBase,
  Header,
  HeaderBase,
  Hi,
  HiBase,
  It,
  ItBase,
  Note,
  Ph,
  PhBase,
  Prop,
  Sub,
  SubBase,
  Tmx,
  TmxBase,
  Tu,
  TuBase,
  Tuv,
  TuvBase,
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
      Note: NoteSerializer(self.backend, self.policy, self.logger),
      Prop: PropSerializer(self.backend, self.policy, self.logger),
      HeaderBase: HeaderSerializer(self.backend, self.policy, self.logger),
      TuBase: TuSerializer(self.backend, self.policy, self.logger),
      TuvBase: TuvSerializer(self.backend, self.policy, self.logger),
      BptBase: BptSerializer(self.backend, self.policy, self.logger),
      EptBase: EptSerializer(self.backend, self.policy, self.logger),
      ItBase: ItSerializer(self.backend, self.policy, self.logger),
      PhBase: PhSerializer(self.backend, self.policy, self.logger),
      SubBase: SubSerializer(self.backend, self.policy, self.logger),
      HiBase: HiSerializer(self.backend, self.policy, self.logger),
      TmxBase: TmxSerializer(self.backend, self.policy, self.logger),
      Header: HeaderSerializer(self.backend, self.policy, self.logger),
      Tu: TuSerializer(self.backend, self.policy, self.logger),
      Tuv: TuvSerializer(self.backend, self.policy, self.logger),
      Bpt: BptSerializer(self.backend, self.policy, self.logger),
      Ept: EptSerializer(self.backend, self.policy, self.logger),
      It: ItSerializer(self.backend, self.policy, self.logger),
      Ph: PhSerializer(self.backend, self.policy, self.logger),
      Sub: SubSerializer(self.backend, self.policy, self.logger),
      Hi: HiSerializer(self.backend, self.policy, self.logger),
      Tmx: TmxSerializer(self.backend, self.policy, self.logger),
    }

  def _resolve_handler(self, obj_type: type) -> BaseElementSerializer | None:
    """Resolve handler for object type, applying policy for missing handlers.

    Args:
        obj_type: Object type to serialize.

    Returns:
        Handler instance or None if skipped per policy.

    Raises:
        MissingSerializationHandlerError: If no handler found and policy raises.
    """
    _handler = self.handlers.get(obj_type)
    if _handler is not None:
      return _handler

    behavior = self.policy.missing_serialization_handler
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, "Missing handler for <%s>", obj_type)
    match behavior.action:
      case RaiseIgnoreDefault.RAISE:
        raise MissingSerializationHandlerError(obj_type)
      case RaiseIgnoreDefault.IGNORE:
        pass
      case RaiseIgnoreDefault.DEFAULT:
        _handler = self._default_handlers.get(obj_type)
        if _handler is None:
          raise MissingSerializationHandlerError(obj_type)
    return _handler

  def serialize(
    self, obj: BaseElement, *, handler: BaseElementSerializer | None = None
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
