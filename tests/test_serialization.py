import pytest
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.base.types import (
  Prop,
  Note,
  Header,
  Tu,
  Tuv,
  Bpt,
  Ept,
  It,
  Ph,
  Hi,
  Sub,
  Segtype,
  Pos,
  Assoc,
  Tmx,
)
from hypomnema.base.errors import MissingHandlerError
from hypomnema.xml.policy import SerializationPolicy, PolicyValue


def test_serialize_prop(backend):
  prop = Prop(text="value", type="x")
  serializer = Serializer(backend)
  el = serializer.serialize(prop)

  assert backend.get_tag(el) == "prop"
  assert backend.get_attribute(el, "type") == "x"
  assert backend.get_text(el) == "value"


def test_serialize_note(backend):
  note = Note(text="some note")
  serializer = Serializer(backend)
  el = serializer.serialize(note)

  assert backend.get_tag(el) == "note"
  assert backend.get_text(el) == "some note"


def test_serialize_header(backend):
  header = Header(
    creationtool="tool",
    creationtoolversion="1.0",
    segtype=Segtype.SENTENCE,
    o_tmf="fmt",
    adminlang="en",
    srclang="en",
    datatype="plain",
  )
  serializer = Serializer(backend)
  el = serializer.serialize(header)

  assert backend.get_tag(el) == "header"
  assert backend.get_attribute(el, "creationtool") == "tool"
  assert backend.get_attribute(el, "segtype") == "sentence"


def test_serialize_inline_elements(backend):
  serializer = Serializer(backend)

  # Bpt
  bpt = Bpt(i=1, type="bold")
  el = serializer.serialize(bpt)
  assert backend.get_tag(el) == "bpt"
  assert backend.get_attribute(el, "i") == "1"
  assert backend.get_attribute(el, "type") == "bold"

  # Ept
  ept = Ept(i=1)
  el = serializer.serialize(ept)
  assert backend.get_tag(el) == "ept"
  assert backend.get_attribute(el, "i") == "1"

  # It
  it = It(pos=Pos.BEGIN)
  el = serializer.serialize(it)
  assert backend.get_tag(el) == "it"
  assert backend.get_attribute(el, "pos") == "begin"


def test_serialize_tuv(backend):
  tuv = Tuv(lang="fr", content=["Bonjour"])
  serializer = Serializer(backend)
  el = serializer.serialize(tuv)

  assert backend.get_tag(el) == "tuv"
  # Usually tuv serializes lang attribute with xml: prefix or resolves it.
  # The Serializer might use the 'xml' prefix internally.
  # We check if it has the attribute.

  # The attribute key might be 'xml:lang' or '{http://www.w3.org/XML/1998/namespace}lang'
  # depending on how serializer sets it.
  # Most serializers set 'xml:lang'.
  val = backend.get_attribute(el, "xml:lang")
  if val is None:
    # Try namespaced
    val = backend.get_attribute(el, "{http://www.w3.org/XML/1998/namespace}lang")

  assert val == "fr"

  # Check children - expects <seg>
  children = list(backend.iter_children(el))
  assert len(children) == 1
  seg = children[0]
  assert backend.get_tag(seg) == "seg"
  assert backend.get_text(seg) == "Bonjour"


def test_serialize_tmx(backend):
  header = Header(
    creationtool="tool",
    creationtoolversion="1.0",
    segtype=Segtype.BLOCK,
    o_tmf="fmt",
    adminlang="en",
    srclang="en",
    datatype="plain",
  )
  tmx = Tmx(header=header, body=[])
  serializer = Serializer(backend)
  el = serializer.serialize(tmx)

  assert backend.get_tag(el) == "tmx"
  assert backend.get_attribute(el, "version") == "1.4"

  children = list(backend.iter_children(el))
  # Expect header and body
  tags = [backend.get_tag(c) for c in children]
  assert "header" in tags
  assert "body" in tags


def test_missing_handler_policy(backend):
  @dataclass_stub
  class UnknownThing:
    pass

  thing = UnknownThing()

  # Default: raise
  serializer = Serializer(backend)
  with pytest.raises(MissingHandlerError):
    serializer.serialize(thing)


# Helper stub for dataclass
class dataclass_stub:
  def __init__(self, cls):
    self.cls = cls

  def __call__(self, *args, **kwargs):
    return self.cls
