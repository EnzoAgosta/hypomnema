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
  pass


class XmlDeserializationError(Exception):
  pass


class AttributeSerializationError(Exception):
  pass


class AttributeDeserializationError(Exception):
  pass


class InvalidTagError(Exception):
  pass


class InvalidContentError(Exception):
  pass


class MissingHandlerError(Exception):
  pass
