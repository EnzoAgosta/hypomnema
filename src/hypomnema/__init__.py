from hypomnema.base.errors import (
  XmlSerializationError,
  XmlDeserializationError,
  AttributeSerializationError,
  AttributeDeserializationError,
  InvalidTagError,
  InvalidContentError,
  MissingHandlerError,
)
import hypomnema.base.types as t
from hypomnema.xml import (
  # Backends
  XmlBackend,
  LxmlBackend,
  StandardBackend,
  # Deserialization
  Deserializer,
  # Serialization
  Serializer,
)

from hypomnema.xml.policy import PolicyValue, DeserializationPolicy, SerializationPolicy

BaseElement = t.BaseElement
Note = t.Note
Prop = t.Prop
Assoc = t.Assoc
Segtype = t.Segtype
Pos = t.Pos

Bpt = t.Bpt[list[t.SubElementAndStr]]
Ept = t.Ept[list[t.SubElementAndStr]]
It = t.It[list[t.SubElementAndStr]]
Ph = t.Ph[list[t.SubElementAndStr]]
Sub = t.Sub[list[t.InlineElementAndStr]]
Hi = t.Hi[list[t.InlineElementAndStr]]

Tuv = t.Tuv[list[t.Prop], list[t.Note], list[t.InlineElementAndStr]]
Tu = t.Tu[list[t.Note], list[t.Prop], list[t.Tuv]]
Header = t.Header[list[t.Prop], list[t.Note]]
Tmx = t.Tmx[list[t.Tu]]


__all__ = [
  # Type aliases
  "BaseElement",
  # Enums
  "Pos",
  "Assoc",
  "Segtype",
  # Structural elements
  "Tmx",
  "Header",
  "Prop",
  "Note",
  "Tu",
  "Tuv",
  # Inline elements
  "Bpt",
  "Ept",
  "It",
  "Ph",
  "Sub",
  "Hi",
  # Errors
  "XmlSerializationError",
  "XmlDeserializationError",
  "AttributeSerializationError",
  "AttributeDeserializationError",
  "InvalidTagError",
  "InvalidContentError",
  "MissingHandlerError",
  # Backends
  "XmlBackend",
  "LxmlBackend",
  "StandardBackend",
  # Deserialization
  "Deserializer",
  # Serialization
  "Serializer",
  # Policies
  "PolicyValue",
  "DeserializationPolicy",
  "SerializationPolicy",
]
