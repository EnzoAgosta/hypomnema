from logging import DEBUG

import pytest

from hypomnema import XmlBackend
from hypomnema.base.errors import (
  AttributeDeserializationError,
  AttributeSerializationError,
  InvalidTagError,
  MissingHandlerError,
  NamespaceError,
  XmlDeserializationError,
  XmlSerializationError,
)
from hypomnema.base.types import Bpt, Header, Note, Prop, Tmx, Tuv
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.policy import PolicyValue, XmlPolicy
from hypomnema.xml.serialization._handlers import NoteSerializer
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.xml.utils import check_tag
from tests.conftest import _append_child, _make_elem


def _make_header_elem(backend: XmlBackend, creationtool: str, text: str | None = None):
  return _make_elem(
    backend,
    "header",
    text=text,
    creationtool=creationtool,
    creationtoolversion="1",
    segtype="block",
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )


def _make_tuv_elem(backend: XmlBackend, text: str):
  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  seg_elem = _make_elem(backend, "seg", text=text)
  _append_child(backend, tuv_elem, seg_elem)
  return tuv_elem


@pytest.mark.policy
def test_policy_existing_namespace_ignore(backend: XmlBackend):
  policy = XmlPolicy(existing_namespace=PolicyValue("ignore", DEBUG))
  backend.policy = policy

  backend.register_namespace("ex", "http://example.com")
  backend.register_namespace("ex", "http://other.example.com")

  assert backend.nsmap["ex"] == "http://example.com"


@pytest.mark.policy
def test_policy_existing_namespace_overwrite(backend: XmlBackend):
  policy = XmlPolicy(existing_namespace=PolicyValue("overwrite", DEBUG))
  backend.policy = policy

  backend.register_namespace("ex", "http://example.com")
  backend.register_namespace("ex", "http://other.example.com")

  assert backend.nsmap["ex"] == "http://other.example.com"


@pytest.mark.policy
def test_policy_existing_namespace_raise(backend: XmlBackend):
  backend.register_namespace("ex", "http://example.com")

  with pytest.raises(NamespaceError):
    backend.register_namespace("ex", "http://other.example.com")


@pytest.mark.policy
def test_policy_missing_namespace_ignore(backend: XmlBackend):
  policy = XmlPolicy(missing_namespace=PolicyValue("ignore", DEBUG))
  backend.policy = policy

  backend.deregister_namespace("missing")


@pytest.mark.policy
def test_policy_missing_namespace_raise(backend: XmlBackend):
  with pytest.raises(NamespaceError):
    backend.deregister_namespace("missing")


@pytest.mark.policy
def test_policy_invalid_namespace_ignore(backend: XmlBackend):
  policy = XmlPolicy(invalid_namespace=PolicyValue("ignore", DEBUG))
  backend.policy = policy

  backend.register_namespace("1bad", "http://example.com")

  assert "1bad" not in backend.nsmap


@pytest.mark.policy
def test_policy_invalid_namespace_raise(backend: XmlBackend):
  with pytest.raises(NamespaceError):
    backend.register_namespace("1bad", "http://example.com")


@pytest.mark.policy
def test_policy_invalid_tag_ignore(test_logger):
  policy = XmlPolicy(invalid_tag=PolicyValue("ignore", DEBUG))

  check_tag("note", "prop", test_logger, policy)


@pytest.mark.policy
def test_policy_invalid_tag_raise(test_logger):
  policy = XmlPolicy(invalid_tag=PolicyValue("raise", DEBUG))

  with pytest.raises(InvalidTagError):
    check_tag("note", "prop", test_logger, policy)


@pytest.mark.policy
def test_policy_missing_deserialization_handler_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_deserialization_handler=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger, handlers={})

  element = _make_elem(backend, "unknown")

  assert deserializer.deserialize(element) is None


@pytest.mark.policy
def test_policy_missing_deserialization_handler_default(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_deserialization_handler=PolicyValue("default", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger, handlers={})

  element = _make_elem(backend, "prop", text="value", type="key")

  result = deserializer.deserialize(element)

  assert isinstance(result, Prop)


@pytest.mark.policy
def test_policy_missing_deserialization_handler_raise(backend: XmlBackend, test_logger):
  deserializer = Deserializer(backend, logger=test_logger, handlers={})

  element = _make_elem(backend, "unknown")

  with pytest.raises(MissingHandlerError):
    deserializer.deserialize(element)


@pytest.mark.policy
def test_policy_required_attribute_missing_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(required_attribute_missing=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "prop", text="value")

  result = deserializer.deserialize(element)

  assert isinstance(result, Prop)
  assert result.type is None


@pytest.mark.policy
def test_policy_required_attribute_missing_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(required_attribute_missing=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "prop", text="value")

  with pytest.raises(AttributeDeserializationError):
    deserializer.deserialize(element)


@pytest.mark.policy
def test_policy_invalid_attribute_value_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_attribute_value=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(
    backend,
    "header",
    creationtool="tool",
    creationtoolversion="1",
    segtype="not-valid",
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )

  result = deserializer.deserialize(element)

  assert isinstance(result, Header)
  assert result.segtype is None


@pytest.mark.policy
def test_policy_invalid_attribute_value_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_attribute_value=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  header_elem = _make_elem(
    backend,
    "header",
    creationtool="tool",
    creationtoolversion="1",
    segtype="not-valid",
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )

  with pytest.raises(AttributeDeserializationError):
    deserializer.deserialize(header_elem)


@pytest.mark.policy
def test_policy_extra_text_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(extra_text=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_header_elem(backend, "tool", text="extra")

  result = deserializer.deserialize(element)

  assert isinstance(result, Header)
  assert result.creationtool == "tool"


@pytest.mark.policy
def test_policy_extra_text_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(extra_text=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_header_elem(backend, "tool", text="extra")

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(element)


@pytest.mark.policy
def test_policy_invalid_child_element_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_child_element=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "prop", text="value", type="key")
  _append_child(backend, element, _make_elem(backend, "bad"))

  result = deserializer.deserialize(element)

  assert isinstance(result, Prop)


@pytest.mark.policy
def test_policy_invalid_child_element_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_child_element=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "prop", text="value", type="key")
  _append_child(backend, element, _make_elem(backend, "bad"))

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(element)


@pytest.mark.policy
def test_policy_multiple_headers_keep_first(backend: XmlBackend, test_logger):
  policy = XmlPolicy(multiple_headers=PolicyValue("keep_first", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tmx_elem = _make_elem(backend, "tmx", version="1.4")
  _append_child(backend, tmx_elem, _make_header_elem(backend, "first"))
  _append_child(backend, tmx_elem, _make_header_elem(backend, "second"))

  result = deserializer.deserialize(tmx_elem)

  assert isinstance(result, Tmx)
  assert result.header.creationtool == "first"


@pytest.mark.policy
def test_policy_multiple_headers_keep_last(backend: XmlBackend, test_logger):
  policy = XmlPolicy(multiple_headers=PolicyValue("keep_last", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tmx_elem = _make_elem(backend, "tmx", version="1.4")
  _append_child(backend, tmx_elem, _make_header_elem(backend, "first"))
  _append_child(backend, tmx_elem, _make_header_elem(backend, "second"))

  result = deserializer.deserialize(tmx_elem)

  assert isinstance(result, Tmx)
  assert result.header.creationtool == "second"


@pytest.mark.policy
def test_policy_multiple_headers_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(multiple_headers=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tmx_elem = _make_elem(backend, "tmx", version="1.4")
  _append_child(backend, tmx_elem, _make_header_elem(backend, "first"))
  _append_child(backend, tmx_elem, _make_header_elem(backend, "second"))

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(tmx_elem)


@pytest.mark.policy
def test_policy_missing_header_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_header=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tmx_elem = _make_elem(backend, "tmx", version="1.4")

  result = deserializer.deserialize(tmx_elem)

  assert isinstance(result, Tmx)
  assert result.header is None


@pytest.mark.policy
def test_policy_missing_header_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_header=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tmx_elem = _make_elem(backend, "tmx", version="1.4")

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(tmx_elem)


@pytest.mark.policy
def test_policy_missing_seg_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_seg=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})

  result = deserializer.deserialize(tuv_elem)

  assert isinstance(result, Tuv)
  assert result.content == []


@pytest.mark.policy
def test_policy_missing_seg_empty(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_seg=PolicyValue("empty", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})

  result = deserializer.deserialize(tuv_elem)

  assert isinstance(result, Tuv)
  assert result.content == [""]


@pytest.mark.policy
def test_policy_missing_seg_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_seg=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(tuv_elem)


@pytest.mark.policy
def test_policy_multiple_seg_keep_first(backend: XmlBackend, test_logger):
  policy = XmlPolicy(multiple_seg=PolicyValue("keep_first", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  _append_child(backend, tuv_elem, _make_elem(backend, "seg", text="first"))
  _append_child(backend, tuv_elem, _make_elem(backend, "seg", text="second"))

  result = deserializer.deserialize(tuv_elem)

  assert isinstance(result, Tuv)
  assert result.content == ["first"]


@pytest.mark.policy
def test_policy_multiple_seg_keep_last(backend: XmlBackend, test_logger):
  policy = XmlPolicy(multiple_seg=PolicyValue("keep_last", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  _append_child(backend, tuv_elem, _make_elem(backend, "seg", text="first"))
  _append_child(backend, tuv_elem, _make_elem(backend, "seg", text="second"))

  result = deserializer.deserialize(tuv_elem)

  assert isinstance(result, Tuv)
  assert result.content == ["second"]


@pytest.mark.policy
def test_policy_multiple_seg_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(multiple_seg=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  _append_child(backend, tuv_elem, _make_elem(backend, "seg", text="first"))
  _append_child(backend, tuv_elem, _make_elem(backend, "seg", text="second"))

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(tuv_elem)


@pytest.mark.policy
def test_policy_empty_content_empty(backend: XmlBackend, test_logger):
  policy = XmlPolicy(empty_content=PolicyValue("empty", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "note")

  result = deserializer.deserialize(element)

  assert isinstance(result, Note)
  assert result.text == ""


@pytest.mark.policy
def test_policy_empty_content_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(empty_content=PolicyValue("ignore", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "note")

  note = deserializer.deserialize(element)

  assert isinstance(note, Note)
  assert note.text is None


@pytest.mark.policy
def test_policy_empty_content_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(empty_content=PolicyValue("raise", DEBUG))
  deserializer = Deserializer(backend, policy=policy, logger=test_logger)

  element = _make_elem(backend, "note")

  with pytest.raises(XmlDeserializationError):
    deserializer.deserialize(element)


@pytest.mark.policy
def test_policy_missing_serialization_handler_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_serialization_handler=PolicyValue("ignore", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger, handlers={})

  result = serializer.serialize(Prop(text="value", type="key"))

  assert result is None


@pytest.mark.policy
def test_policy_missing_serialization_handler_default(backend: XmlBackend, test_logger):
  policy = XmlPolicy(missing_serialization_handler=PolicyValue("default", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger, handlers={})

  result = serializer.serialize(Prop(text="value", type="key"))

  assert result is not None


@pytest.mark.policy
def test_policy_missing_serialization_handler_raise(backend: XmlBackend, test_logger):
  serializer = Serializer(backend, logger=test_logger, handlers={})

  with pytest.raises(MissingHandlerError):
    serializer.serialize(Prop(text="value", type="key"))


@pytest.mark.policy
def test_policy_invalid_attribute_type_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_attribute_type=PolicyValue("ignore", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  prop = Prop(text="value", type=123)  # type: ignore[arg-type]
  element = serializer.serialize(prop)

  assert element is not None
  assert backend.get_attribute(element, "type") is None


@pytest.mark.policy
def test_policy_invalid_attribute_type_coerce(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_attribute_type=PolicyValue("coerce", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  prop = Prop(text="value", type=123)  # type: ignore[arg-type]
  element = serializer.serialize(prop)

  assert element is not None
  assert backend.get_attribute(element, "type") is None


@pytest.mark.policy
def test_policy_invalid_attribute_type_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_attribute_type=PolicyValue("raise", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  prop = Prop(text="value", type=123)  # type: ignore[arg-type]

  with pytest.raises(AttributeSerializationError):
    serializer.serialize(prop)


@pytest.mark.policy
def test_policy_invalid_content_element_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_content_element=PolicyValue("ignore", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  result = serializer.serialize(Bpt(i=1, content=[Prop(text="value", type="key")]))  # type: ignore[list-item]

  assert result is not None


@pytest.mark.policy
def test_policy_invalid_content_element_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_content_element=PolicyValue("raise", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  with pytest.raises(XmlSerializationError):
    serializer.serialize(Bpt(i=1, content=[Prop(text="value", type="key")]))  # type: ignore[list-item]


@pytest.mark.policy
def test_policy_invalid_object_type_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_object_type=PolicyValue("ignore", DEBUG))
  serializer = Serializer(
    backend,
    policy=policy,
    logger=test_logger,
    handlers={Prop: NoteSerializer(backend, policy, test_logger)},
  )

  result = serializer.serialize(Prop(text="value", type="key"))

  assert result is None


@pytest.mark.policy
def test_policy_invalid_object_type_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(invalid_object_type=PolicyValue("raise", DEBUG))
  serializer = Serializer(
    backend,
    policy=policy,
    logger=test_logger,
    handlers={Prop: NoteSerializer(backend, policy, test_logger)},
  )

  with pytest.raises(XmlSerializationError):
    serializer.serialize(Prop(text="value", type="key"))


@pytest.mark.policy
def test_policy_required_attribute_missing_serialization_ignore(backend: XmlBackend, test_logger):
  policy = XmlPolicy(required_attribute_missing=PolicyValue("ignore", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  prop = Prop(text="value", type=None)  # type: ignore[arg-type]
  element = serializer.serialize(prop)

  assert element is not None
  assert backend.get_attribute(element, "type") is None


@pytest.mark.policy
def test_policy_required_attribute_missing_serialization_raise(backend: XmlBackend, test_logger):
  policy = XmlPolicy(required_attribute_missing=PolicyValue("raise", DEBUG))
  serializer = Serializer(backend, policy=policy, logger=test_logger)

  prop = Prop(text="value", type=None)  # type: ignore[arg-type]

  with pytest.raises(AttributeSerializationError):
    serializer.serialize(prop)
