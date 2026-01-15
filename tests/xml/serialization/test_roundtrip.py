import pytest
from datetime import datetime, timezone
from hypomnema.base.types import (
  Prop,
  Note,
  Header,
  Segtype,
  Tuv,
  Tu,
  Tmx,
  Bpt,
  Ept,
  It,
  Ph,
  Hi,
  Pos,
  Assoc,
)
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.policy import SerializationPolicy, DeserializationPolicy


class TestSerializationRoundTrip:
  @pytest.fixture(autouse=True)
  def setup(self, backend):
    self.backend = backend
    self.serializer = Serializer(backend, policy=SerializationPolicy())

    de_policy = DeserializationPolicy()
    self.deserializer = Deserializer(backend, policy=de_policy)

  def test_roundtrip_simple_prop(self):
    original = Prop(text="some text", type="x-test", lang="en", o_encoding="utf-8")

    xml_elem = self.serializer.serialize(original)
    result = self.deserializer.deserialize(xml_elem)

    assert original == result

  def test_roundtrip_complex_tu(self):
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    original = Tu(
      tuid="tu1",
      srclang="en",
      segtype=Segtype.BLOCK,
      creationdate=dt,
      notes=[Note(text="note1", lang="en")],
      props=[Prop(text="prop1", type="p1")],
      variants=[
        Tuv(lang="en", content=["Source text"], creationdate=dt),
        Tuv(
          lang="fr",
          content=["Target ", Ph(x=1, type="img", content=["image"]), " text"],
          creationdate=dt,
        ),
      ],
    )

    xml_elem = self.serializer.serialize(original)
    result = self.deserializer.deserialize(xml_elem)

    assert original == result

  def test_roundtrip_full_tmx(self):
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    header = Header(
      creationtool="Hypomnema",
      creationtoolversion="1.0",
      segtype=Segtype.SENTENCE,
      o_tmf="ALKS",
      adminlang="en-US",
      srclang="en",
      datatype="plain",
      creationdate=dt,
    )

    body = [
      Tu(
        tuid="1", variants=[Tuv(lang="en", content=["Hello"]), Tuv(lang="es", content=["Bonjour"])]
      ),
      Tu(tuid="2", variants=[Tuv(lang="en", content=["World"]), Tuv(lang="es", content=["Monde"])]),
    ]

    original = Tmx(header=header, body=body)

    xml_elem = self.serializer.serialize(original)
    result = self.deserializer.deserialize(xml_elem)

    assert original == result

  def test_roundtrip_inline_elements(self):
    content = [
      "Text",
      Bpt(i=1, x=2, type="b", content=["<bold>"]),
      "In between",
      Ept(i=1, content=["</bold>"]),
      Ph(x=3, type="img", assoc=Assoc.P, content=["<img />"]),
      It(pos=Pos.BEGIN, x=4, type="u", content=["It"]),
      Hi(x=5, type="color", content=["Highlighted"]),
      "tail",
    ]

    original = Tuv(lang="en", content=content)

    xml_elem = self.serializer.serialize(original)
    result = self.deserializer.deserialize(xml_elem)

    assert original == result
