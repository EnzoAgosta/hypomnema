from datetime import datetime, timezone

from hypomnema import XmlBackend
from hypomnema.base.types import (Bpt, Header, Hi, It, Note, Ph, Pos, Prop,
                                  Segtype, Sub, Tmx, Tu, Tuv)
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.serialization.serializer import Serializer
from tests.conftest import _append_child, _make_elem, xml_equal


def _serializer(backend: XmlBackend) -> Serializer:
  return Serializer(backend, policy=XmlPolicy())


def _deserializer(backend: XmlBackend) -> Deserializer:
  return Deserializer(backend, policy=XmlPolicy())


def test_roundtrip_serialize_deserialize_prop(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)

  prop = Prop(text="value", type="x-key", lang="en", o_encoding="utf-8")
  element = serializer.serialize(prop)
  result = deserializer.deserialize(element)

  assert result == prop


def test_roundtrip_serialize_deserialize_note(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)

  note = Note(text="note", lang="fr", o_encoding="latin-1")
  element = serializer.serialize(note)
  result = deserializer.deserialize(element)

  assert result == note


def test_roundtrip_serialize_deserialize_header(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)
  dt = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

  header = Header(
    creationtool="tool",
    creationtoolversion="1",
    segtype=Segtype.SENTENCE,
    o_tmf="tmf",
    adminlang="en",
    srclang="en",
    datatype="plain",
    creationdate=dt,
    notes=[Note(text="n")],
    props=[Prop(text="p", type="t")],
  )

  element = serializer.serialize(header)
  result = deserializer.deserialize(element)

  assert result == header


def test_roundtrip_serialize_deserialize_tuv(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)
  dt = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

  tuv = Tuv(
    lang="en",
    datatype="plain",
    usagecount=2,
    lastusagedate=dt,
    creationtool="tool",
    creationtoolversion="1",
    creationdate=dt,
    creationid="user",
    changedate=dt,
    changeid="user2",
    content=["Hello ", Ph(x=1, content=["hello"]), "World"],
    notes=[Note(text="n")],
    props=[Prop(text="p", type="t")],
  )

  element = serializer.serialize(tuv)
  result = deserializer.deserialize(element)

  assert result == tuv


def test_roundtrip_serialize_deserialize_tu(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)

  tu = Tu(
    tuid="tu1",
    segtype=Segtype.BLOCK,
    srclang="en",
    notes=[Note(text="n")],
    props=[Prop(text="p", type="t")],
    variants=[Tuv(lang="en", content=["hello"]), Tuv(lang="fr", content=["hello"])],
  )

  element = serializer.serialize(tu)
  result = deserializer.deserialize(element)

  assert result == tu


def test_roundtrip_serialize_deserialize_tmx(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)

  header = Header(
    creationtool="tool",
    creationtoolversion="1",
    segtype=Segtype.BLOCK,
    o_tmf="tmf",
    adminlang="en",
    srclang="en",
    datatype="plain",
  )
  tmx = Tmx(header=header, body=[Tu(tuid="1"), Tu(tuid="2")])

  element = serializer.serialize(tmx)
  result = deserializer.deserialize(element)

  assert result == tmx


def test_roundtrip_deserialize_serialize_xml(backend: XmlBackend):
  deserializer = _deserializer(backend)
  serializer = _serializer(backend)

  root = _make_elem(backend, "tmx", version="1.4")
  header = _make_elem(
    backend,
    "header",
    creationtool="tool",
    creationtoolversion="1",
    segtype="block",
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )
  _append_child(backend, root, header)
  body = _make_elem(backend, "body")
  tu = _make_elem(backend, "tu", tuid="1")
  tuv = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  seg = _make_elem(backend, "seg", text="Hello ")
  _append_child(backend, root, body)
  _append_child(backend, body, tu)
  _append_child(backend, tu, tuv)
  _append_child(backend, tuv, seg)
  _append_child(backend, seg, _make_elem(backend, "ph", x="1", text="text", tail="World"))

  obj = deserializer.deserialize(root)
  serialized = serializer.serialize(obj)  # type: ignore[arg-type]

  assert xml_equal(root, serialized, backend)


def test_roundtrip_inline_elements(backend: XmlBackend):
  serializer = _serializer(backend)
  deserializer = _deserializer(backend)

  bpt = serializer.serialize(Bpt(i=1, x=2, type="bold", content=["text", Sub(content=["s"])]))
  bpt_obj = deserializer.deserialize(bpt)
  assert bpt_obj == Bpt(i=1, x=2, type="bold", content=["text", Sub(content=["s"])])

  it = serializer.serialize(It(pos=Pos.BEGIN, x=1, type="code", content=["text"]))
  it_obj = deserializer.deserialize(it)
  assert it_obj == It(pos=Pos.BEGIN, x=1, type="code", content=["text"])

  hi = serializer.serialize(Hi(x=1, type="b", content=["bold"]))
  hi_obj = deserializer.deserialize(hi)
  assert hi_obj == Hi(x=1, type="b", content=["bold"])
