from logging import Logger, getLogger

from hypomnema.base.errors import MissingHandlerError
from hypomnema.base.types import BaseElement
from hypomnema.xml.backends.base import XmlBackend, T_Attributes
from hypomnema.xml.deserialization._handlers import (
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
from hypomnema.xml.policy import DeserializationPolicy


__all__ = ["Deserializer"]


class Deserializer[BackendElementType]:
  """
  Orchestrator for converting XML elements into TMX objects using registered handlers.

  Parameters
  ----------
  backend : XMLBackend
      The XML library wrapper used for element inspection.
  policy : DeserializationPolicy | None, optional
      The configuration for error handling and logging. Defaults to a standard
      DeserializationPolicy.
  logger : Logger | None, optional
      The logger for reporting operations and policy violations. Defaults to
       the module-level logger.
  handlers : dict[str, BaseElementDeserializer] | None, optional
      A mapping of XML tags to their respective deserializer instances. If None,
      default TMX handlers are used.

  Attributes
  ----------
  backend : XMLBackend
      The XML library wrapper.
  policy : DeserializationPolicy
      The active deserialization policy.
  logger : Logger
      The active logger.
  handlers : dict[str, BaseElementDeserializer]
      The registered tag-to-handler mapping.
  """

  def __init__(
    self,
    backend: XmlBackend[BackendElementType, T_Attributes],
    policy: DeserializationPolicy | None = None,
    logger: Logger | None = None,
    handlers: dict[str, BaseElementDeserializer] | None = None,
  ):
    self.backend: XmlBackend[BackendElementType, T_Attributes] = backend
    self.policy: DeserializationPolicy = policy or DeserializationPolicy()
    self.logger: Logger = logger or getLogger(str(self))
    if handlers is None:
      self.logger.info("Using default handlers")
      handlers = self._get_default_handlers()
    else:
      self.logger.debug("Using custom handlers")
    self.handlers = handlers

    for handler in self.handlers.values():
      if handler._emit is None:
        handler._set_emit(self.deserialize)

  def _get_default_handlers(self) -> dict[str, BaseElementDeserializer]:
    """
    Initialize the internal mapping of default TMX element deserializers.

    Returns
    -------
    dict[str, BaseElementDeserializer]
        A dictionary mapping TMX tags to their default deserializer instances.
    """
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

  def deserialize(self, element: BackendElementType) -> BaseElement | None:
    """
    Dispatch an XML element to a handler and return the resulting TMX object.

    Parameters
    ----------
    element : BackendElementType
        The backend XML element to deserialize.

    Returns
    -------
    BaseElement | None
        The deserialized TMX object, or None if the policy is set to "ignore"
        on missing handlers.

    Raises
    ------
    MissingHandlerError
        If no handler is found for the element tag and the policy is set to
        "raise", or if "default" fallback fails to find a handler.
    """
    tag = self.backend.get_tag(element)
    self.logger.debug("Deserializing <%s>", tag)
    handler = self.handlers.get(tag)
    if handler is None:
      self.logger.log(self.policy.missing_handler.log_level, "Missing handler for <%s>", tag)
      if self.policy.missing_handler.behavior == "raise":
        raise MissingHandlerError(f"Missing handler for <{tag}>") from None
      elif self.policy.missing_handler.behavior == "ignore":
        return None
      else:
        self.logger.log(
          self.policy.missing_handler.log_level, "Falling back to default handler for <%s>", tag
        )
        handler = self._get_default_handlers().get(tag)
        if handler is None:
          raise MissingHandlerError(f"Missing handler for <{tag}>") from None
    return handler._deserialize(element)
