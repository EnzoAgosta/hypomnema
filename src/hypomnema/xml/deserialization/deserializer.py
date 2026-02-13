"""Deserializer orchestrator for TMX deserialization.

This module provides the Deserializer class that coordinates deserialization
of TMX documents. It maintains a registry of element handlers and dispatches
XML elements to the appropriate handler.
"""

from collections.abc import Mapping
from functools import cached_property
from logging import Logger, getLogger

from hypomnema.base.errors import MissingDeserializationHandlerError
from hypomnema.base.types import BaseElement
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization.handlers import (
  BptDeserializer,
  EptDeserializer,
  HeaderDeserializer,
  HiDeserializer,
  ItDeserializer,
  NoteDeserializer,
  PhDeserializer,
  PropDeserializer,
  SubDeserializer,
  TmxDeserializer,
  TuDeserializer,
  TuvDeserializer,
)
from hypomnema.xml.deserialization.base import BaseElementDeserializer
from hypomnema.xml.policy import RaiseIgnoreDefault, XmlDeserializationPolicy


class Deserializer[TypeofBackendElement]:
  """Orchestrates TMX deserialization.

  The Deserializer maintains a registry of element handlers and dispatches
  XML elements to the appropriate handler based on tag name. It also
  injects the emit() function into handlers for recursive deserialization.

  Args:
      backend: XML backend for element operations.
      policy: Policy for error handling (default: strict).
      logger: Logger for operations.
      handlers: Custom element handlers (default: built-in handlers).

  Attributes:
      logger: Logger instance.
      backend: XML backend.
      policy: Deserialization policy.
      handlers: Registered element handlers.
  """

  def __init__(
    self,
    backend: XmlBackend[TypeofBackendElement],
    policy: XmlDeserializationPolicy | None = None,
    logger: Logger | None = None,
    handlers: Mapping[str, BaseElementDeserializer] | None = None,
  ):
    self.logger: Logger = logger or getLogger(__name__)
    self.backend: XmlBackend[TypeofBackendElement] = backend
    if policy is None:
      policy = XmlDeserializationPolicy()
      self.logger.debug("Using default policy")
    self.policy = policy
    if handlers is None:
      self.logger.debug("Using default handlers")
      handlers = self._default_handlers
    self.handlers = {k: v for k, v in handlers.items()}

    for handler in self.handlers.values():
      handler._set_emit(self.deserialize)

  @cached_property
  def _default_handlers(
    self,
  ) -> dict[str, BaseElementDeserializer[TypeofBackendElement, BaseElement]]:
    """Default handler instances for all TMX element types.

    Returns:
        Mapping of tag names to handler instances.
    """
    handlers = self._get_default_handlers()
    for handler in handlers.values():
      handler._set_emit(self.deserialize)
    return handlers

  def _get_default_handlers(
    self,
  ) -> dict[str, BaseElementDeserializer[TypeofBackendElement, BaseElement]]:
    """Create default handler instances."""
    return {
      "note": NoteDeserializer(self.backend, self.policy, self.logger),
      "prop": PropDeserializer(self.backend, self.policy, self.logger),
      "header": HeaderDeserializer(self.backend, self.policy, self.logger),
      "tu": TuDeserializer(self.backend, self.policy, self.logger),
      "tuv": TuvDeserializer(self.backend, self.policy, self.logger),
      "bpt": BptDeserializer(self.backend, self.policy, self.logger),
      "ept": EptDeserializer(self.backend, self.policy, self.logger),
      "it": ItDeserializer(self.backend, self.policy, self.logger),
      "ph": PhDeserializer(self.backend, self.policy, self.logger),
      "sub": SubDeserializer(self.backend, self.policy, self.logger),
      "hi": HiDeserializer(self.backend, self.policy, self.logger),
      "tmx": TmxDeserializer(self.backend, self.policy, self.logger),
    }

  def _resolve_handler(
    self, tag: str
  ) -> BaseElementDeserializer[TypeofBackendElement, BaseElement] | None:
    """Resolve handler for tag, applying policy for missing handlers.

    Args:
        tag: Element tag name.

    Returns:
        Handler instance or None if skipped per policy.

    Raises:
        MissingDeserializationHandlerError: If no handler found and policy raises.
    """
    _handler = self.handlers.get(tag)
    if _handler is not None:
      return _handler

    behavior = self.policy.missing_deserialization_handler
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, "Missing handler for <%s>", tag)
    match behavior.action:
      case RaiseIgnoreDefault.RAISE:
        raise MissingDeserializationHandlerError(tag)
      case RaiseIgnoreDefault.IGNORE:
        pass
      case RaiseIgnoreDefault.DEFAULT:
        _handler = self._default_handlers.get(tag)
        if _handler is None:
          raise MissingDeserializationHandlerError(tag)
    return _handler

  def deserialize(
    self, element: TypeofBackendElement, *, handler: BaseElementDeserializer | None = None
  ) -> BaseElement | None:
    """Deserialize an XML element to a TMX dataclass.

    Args:
        element: XML element to deserialize.
        handler: Optional specific handler to use (default: auto-resolve by tag).

    Returns:
        Deserialized object or None if skipped.
    """
    if handler is None:
      handler = self._resolve_handler(self.backend.get_tag(element))
    return handler._deserialize(element) if handler is not None else None
