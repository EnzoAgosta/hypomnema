from hypomnema.base.errors import MissingHandlerError
from hypomnema.xml.serialization._handlers import (
  NoteSerializer,
  PropSerializer,
  HeaderSerializer,
  BptSerializer,
  EptSerializer,
  ItSerializer,
  PhSerializer,
  SubSerializer,
  HiSerializer,
  TuvSerializer,
  TuSerializer,
  TmxSerializer,
)
from hypomnema.xml.serialization.base import BaseElementSerializer
from hypomnema.xml.backends.base import XmlBackend, T_Attributes
from hypomnema.xml.policy import SerializationPolicy
from hypomnema.base.types import BaseElement
from collections.abc import Mapping
from logging import Logger, getLogger


__all__ = ["Serializer"]


class Serializer[BackendElementType]:
  def __init__(
    self,
    backend: XmlBackend[BackendElementType, T_Attributes],
    policy: SerializationPolicy | None = None,
    logger: Logger | None = None,
    handlers: Mapping[str, BaseElementSerializer] | None = None,
  ):
    self.backend: XmlBackend[BackendElementType, T_Attributes] = backend
    self.policy: SerializationPolicy = policy or SerializationPolicy()
    self.logger: Logger = logger or getLogger(str(self))
    if handlers is None:
      self.logger.debug("Using default handlers")
      handlers = self._get_default_handlers()
    else:
      self.logger.debug("Using custom handlers")
    self.handlers = handlers

    for handler in self.handlers.values():
      if handler._emit is None:
        handler._set_emit(self.serialize)

  def _get_default_handlers(self) -> dict[str, BaseElementSerializer]:
    return {
      "Note": NoteSerializer(self.backend, self.policy, self.logger),
      "Prop": PropSerializer(self.backend, self.policy, self.logger),
      "Header": HeaderSerializer(self.backend, self.policy, self.logger),
      "Tu": TuSerializer(self.backend, self.policy, self.logger),
      "Tuv": TuvSerializer(self.backend, self.policy, self.logger),
      "Bpt": BptSerializer(self.backend, self.policy, self.logger),
      "Ept": EptSerializer(self.backend, self.policy, self.logger),
      "It": ItSerializer(self.backend, self.policy, self.logger),
      "Ph": PhSerializer(self.backend, self.policy, self.logger),
      "Sub": SubSerializer(self.backend, self.policy, self.logger),
      "Hi": HiSerializer(self.backend, self.policy, self.logger),
      "Tmx": TmxSerializer(self.backend, self.policy, self.logger),
    }

  def serialize(self, obj: BaseElement) -> BackendElementType | None:
    obj_type = obj.__class__.__name__
    self.logger.debug("Serializing %r", obj_type)
    handler = self.handlers.get(obj_type)
    if handler is None:
      self.logger.log(self.policy.missing_handler.log_level, "Missing handler for %r", obj_type)
      if self.policy.missing_handler.behavior == "raise":
        raise MissingHandlerError(f"Missing handler for {obj_type!r}") from None
      elif self.policy.missing_handler.behavior == "ignore":
        return None
      else:
        self.logger.log(
          self.policy.missing_handler.log_level, "Falling back to default handler for %r", obj_type
        )
        handler = self._get_default_handlers().get(obj_type)
        if handler is None:
          raise MissingHandlerError(f"Missing handler for {obj_type!r}") from None
    return handler._serialize(obj)
