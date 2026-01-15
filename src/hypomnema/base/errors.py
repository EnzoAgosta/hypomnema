__all__ = [
  "XmlSerializationError",
  "XmlDeserializationError",
  "AttributeSerializationError",
  "AttributeDeserializationError",
  "InvalidTagError",
  "InvalidContentError",
  "MissingHandlerError",
]


class XmlSerializationError(Exception):
  """Raised when serialization to XML fails."""

  pass


class XmlDeserializationError(Exception):
  """Raised when deserialization from XML fails."""

  pass


class AttributeSerializationError(Exception):
  """Raised when serializing an attribute fails."""

  pass


class AttributeDeserializationError(Exception):
  """Raised when deserializing an attribute fails."""

  pass


class InvalidTagError(Exception):
  """Raised when an unexpected XML tag is encountered."""

  pass


class InvalidContentError(Exception):
  """Raised when element content is invalid."""

  pass


class MissingHandlerError(Exception):
  """Raised when no handler is registered for an element type."""

  pass
