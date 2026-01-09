from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.base.types import (
  Tmx,
  Header,
  Tu,
  Tuv,
  Prop,
  Note,
  Segtype,
  Bpt,
  Ph,
  Assoc,
)
from hypomnema.xml.policy import DeserializationPolicy, PolicyValue
import logging


def test_roundtrip_complex(backend):
  """
  Verify that an object survives a full roundtrip:
  Object -> Serialize -> XML -> Deserialize -> Object
  """

  # Header
  header = Header(
    creationtool="hypomnema-test",
    creationtoolversion="0.1",
    segtype=Segtype.SENTENCE,
    o_tmf="xml",
    adminlang="en-US",
    srclang="en-US",
    datatype="plaintext",
    props=[Prop(text="header-prop-val", type="header-prop")],
  )

  # Complex inline content
  inline_content = [
    "Text before ",
    Bpt(i=1, type="bold", content=["Bold text"]),
    " Text middle ",
    Ph(x=2, type="img", assoc=Assoc.P),
    " Text end.",
  ]

  # TUVs
  tuv_en = Tuv(lang="en-US", content=inline_content, props=[Prop(text="tuv-prop", type="tuv-type")])

  tuv_fr = Tuv(
    lang="fr-FR",
    content=["Texte avant ", Bpt(i=1, type="bold", content=["Texte gras"])],
    notes=[Note(text="Translation is rough")],
  )

  # TU
  tu = Tu(
    tuid="test-tu-1",
    segtype=Segtype.PHRASE,
    variants=[tuv_en, tuv_fr],
    notes=[Note(text="TU note")],
    props=[Prop(text="TU prop", type="tu-type")],
  )

  # TMX
  tmx = Tmx(header=header, body=[tu])

  # 1. Serialize
  serializer = Serializer(backend)
  root_element = serializer.serialize(tmx)

  # 2. Deserialize
  policy = DeserializationPolicy(empty_content=PolicyValue("ignore", logging.DEBUG))
  deserializer = Deserializer(backend, policy=policy)
  new_tmx = deserializer.deserialize(root_element)

  # 3. Verify
  # Because equality checks on dataclasses are strict, this ensures everything matches.
  assert new_tmx == tmx


def test_roundtrip_minimal(backend):
  """Roundtrip a minimal valid TMX."""
  header = Header(
    creationtool="tool",
    creationtoolversion="1",
    segtype=Segtype.BLOCK,
    o_tmf="f",
    adminlang="en",
    srclang="en",
    datatype="plain",
  )
  tmx = Tmx(header=header, body=[])

  root = Serializer(backend).serialize(tmx)
  new_tmx = Deserializer(backend).deserialize(root)

  assert new_tmx == tmx
