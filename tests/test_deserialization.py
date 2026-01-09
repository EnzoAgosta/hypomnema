import pytest
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.base.types import (
  Prop,
  Note,
  Segtype,
  Pos,
  Assoc,
  Header,
  Ept,
  It,
  Ph,
  Hi,
  Sub,
  Tuv,
  Bpt,
)
from hypomnema.base.errors import MissingHandlerError
from hypomnema.xml.policy import DeserializationPolicy, PolicyValue


def test_deserialize_prop(backend):
  el = backend.create_element("prop", {"type": "x"})
  backend.set_text(el, "value")

  deserializer = Deserializer(backend)
  obj = deserializer.deserialize(el)

  assert isinstance(obj, Prop)
  assert obj.type == "x"
  assert obj.text == "value"


def test_deserialize_note(backend):
  el = backend.create_element("note")
  backend.set_text(el, "some note")

  deserializer = Deserializer(backend)
  obj = deserializer.deserialize(el)
  assert isinstance(obj, Note)
  assert obj.text == "some note"


def test_deserialize_header(backend):
  # <header creationtool="tool" creationtoolversion="1.0" segtype="sentence"
  #         o-tmf="fmt" adminlang="en" srclang="en" datatype="plain">
  attrs = {
    "creationtool": "tool",
    "creationtoolversion": "1.0",
    "segtype": "sentence",
    "o-tmf": "fmt",
    "adminlang": "en",
    "srclang": "en",
    "datatype": "plain",
  }
  el = backend.create_element("header", attrs)

  deserializer = Deserializer(backend)
  obj = deserializer.deserialize(el)

  assert isinstance(obj, Header)
  assert obj.creationtool == "tool"
  assert obj.segtype == Segtype.SENTENCE


def test_deserialize_inline_elements(backend):
  deserializer = Deserializer(backend)

  # <bpt i="1" type="bold">
  bpt = backend.create_element("bpt", {"i": "1", "type": "bold"})
  backend.set_text(bpt, "text")
  obj = deserializer.deserialize(bpt)
  assert isinstance(obj, Bpt)
  assert obj.i == 1
  assert obj.type == "bold"

  # <ept i="1">
  ept = backend.create_element("ept", {"i": "1"})
  backend.set_text(ept, "text")
  obj = deserializer.deserialize(ept)
  assert isinstance(obj, Ept)
  assert obj.i == 1

  # <it pos="begin">
  it = backend.create_element("it", {"pos": "begin"})
  backend.set_text(it, "text")
  obj = deserializer.deserialize(it)
  assert isinstance(obj, It)
  assert obj.pos == Pos.BEGIN

  # <ph assoc="p">
  ph = backend.create_element("ph", {"assoc": "p"})
  backend.set_text(ph, "text")
  obj = deserializer.deserialize(ph)
  assert isinstance(obj, Ph)
  assert obj.assoc == Assoc.P

  # <hi type="b">
  hi = backend.create_element("hi", {"type": "b"})
  backend.set_text(hi, "text")
  obj = deserializer.deserialize(hi)
  assert isinstance(obj, Hi)
  assert obj.type == "b"

  # <sub>
  sub = backend.create_element("sub", {"datatype": "html"})
  backend.set_text(sub, "text")
  obj = deserializer.deserialize(sub)
  assert isinstance(obj, Sub)
  assert obj.datatype == "html"


def test_deserialize_tuv(backend):
  # <tuv xml:lang="fr"><seg>Bonjour</seg></tuv>

  tuv = backend.create_element("tuv")
  backend.set_attribute(tuv, "xml:lang", "fr")

  seg = backend.create_element("seg")
  backend.set_text(seg, "Bonjour")
  backend.append_child(tuv, seg)

  deserializer = Deserializer(backend)
  obj = deserializer.deserialize(tuv)

  assert isinstance(obj, Tuv)
  assert obj.lang == "fr"

  assert obj.content == ["Bonjour"]


def test_deserialize_missing_handler_policy(backend):
  el = backend.create_element("unknown_tag")

  # Default policy: raise
  deserializer = Deserializer(backend)
  with pytest.raises(MissingHandlerError):
    deserializer.deserialize(el)

  # Ignore policy
  policy = DeserializationPolicy(missing_handler=PolicyValue("ignore", 10))
  deserializer = Deserializer(backend, policy=policy)
  assert deserializer.deserialize(el) is None


def test_deserialize_required_attribute_missing(backend):
  # <tuv> without lang
  tuv = backend.create_element("tuv")
  seg = backend.create_element("seg")
  backend.append_child(tuv, seg)

  # Default policy: raise
  deserializer = Deserializer(backend)

  with pytest.raises(Exception):  # Broad catch for now, narrow down later if needed
    deserializer.deserialize(tuv)
