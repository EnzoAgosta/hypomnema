import pytest

from hypomnema import XmlBackend
from hypomnema.base.errors import (AttributeDeserializationError,
                                   XmlDeserializationError)
from hypomnema.base.types import (Bpt, Ept, Header, Hi, It, Note, Ph, Prop,
                                  Segtype, Sub, Tmx, Tu, Tuv)
from tests.conftest import _append_child, _deserializer, _make_elem


def test_deserialize_prop_all_fields(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(
    backend, "prop", text="value", type="x-key", **{"xml:lang": "en", "o-encoding": "utf-8"}
  )

  obj = deserializer.deserialize(element)

  assert isinstance(obj, Prop)
  assert obj.text == "value"
  assert obj.type == "x-key"
  assert obj.lang == "en"
  assert obj.o_encoding == "utf-8"


def test_deserialize_note_all_fields(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(backend, "note", text="note", **{"xml:lang": "fr"})

  obj = deserializer.deserialize(element)

  assert isinstance(obj, Note)
  assert obj.text == "note"
  assert obj.lang == "fr"


def test_deserialize_header_with_children(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(
    backend,
    "header",
    creationtool="tool",
    creationtoolversion="1",
    segtype="sentence",
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )
  _append_child(backend, element, _make_elem(backend, "prop", text="p", type="t"))
  _append_child(backend, element, _make_elem(backend, "note", text="n"))

  obj = deserializer.deserialize(element)

  assert isinstance(obj, Header)
  assert obj.creationtool == "tool"
  assert len(obj.props) == 1
  assert len(obj.notes) == 1


def test_deserialize_inline_elements(backend: XmlBackend):
  deserializer = _deserializer(backend)

  bpt_elem = _make_elem(backend, "bpt", text="text", i="1", x="2", type="b")
  _append_child(backend, bpt_elem, _make_elem(backend, "sub", text="s", datatype="html"))
  assert isinstance(deserializer.deserialize(bpt_elem), Bpt)

  assert isinstance(deserializer.deserialize(_make_elem(backend, "ept", text="text", i="1")), Ept)
  assert isinstance(
    deserializer.deserialize(_make_elem(backend, "it", text="text", pos="begin", x="1")), It
  )
  assert isinstance(
    deserializer.deserialize(_make_elem(backend, "ph", text="text", assoc="p", x="1")), Ph
  )
  assert isinstance(deserializer.deserialize(_make_elem(backend, "hi", text="bold")), Hi)
  assert isinstance(deserializer.deserialize(_make_elem(backend, "sub", text="s")), Sub)


def test_deserialize_tuv_with_seg(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  seg = _make_elem(backend, "seg", text="Hello ")
  _append_child(backend, seg, _make_elem(backend, "ph", text="text", x="1", tail="World"))
  _append_child(backend, element, seg)

  obj = deserializer.deserialize(element)

  assert isinstance(obj, Tuv)
  assert obj.lang == "en"
  assert obj.content[0] == "Hello "
  assert isinstance(obj.content[1], Ph)
  assert obj.content[2] == "World"


def test_deserialize_tu_with_variants(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(backend, "tu", tuid="tu1", segtype="block", srclang="en")
  tuv = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  _append_child(backend, tuv, _make_elem(backend, "seg", text="content"))
  _append_child(backend, element, tuv)

  obj = deserializer.deserialize(element)

  assert isinstance(obj, Tu)
  assert obj.tuid == "tu1"
  assert obj.segtype == Segtype.BLOCK
  assert len(obj.variants) == 1


def test_deserialize_tmx_minimal(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(backend, "tmx", version="1.4")
  _append_child(
    backend,
    element,
    _make_elem(
      backend,
      "header",
      creationtool="tool",
      creationtoolversion="1",
      segtype="block",
      **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
    ),
  )
  body = _make_elem(backend, "body")
  tu = _make_elem(backend, "tu")
  tuv = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  _append_child(backend, tuv, _make_elem(backend, "seg", text="content"))
  _append_child(backend, tu, tuv)
  _append_child(backend, body, tu)
  _append_child(backend, element, body)

  obj = deserializer.deserialize(element)

  assert isinstance(obj, Tmx)
  assert obj.version == "1.4"
  assert obj.header.creationtool == "tool"
  assert len(obj.body) == 1


def test_deserialize_missing_required_attribute(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(backend, "prop", text="value")

  with pytest.raises(AttributeDeserializationError, match="Required attribute"):
    deserializer.deserialize(element)


def test_deserialize_invalid_child(backend: XmlBackend):
  deserializer = _deserializer(backend)
  element = _make_elem(backend, "prop", text="value", type="t")
  _append_child(backend, element, _make_elem(backend, "bad"))

  with pytest.raises(XmlDeserializationError, match="Invalid child element"):
    deserializer.deserialize(element)
