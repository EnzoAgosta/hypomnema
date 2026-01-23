import logging
from datetime import datetime, timezone
from typing import Any, cast

import pytest

from hypomnema import XmlBackend
from hypomnema.base.errors import (AttributeSerializationError,
                                   XmlSerializationError)
from hypomnema.base.types import (Assoc, Bpt, Ept, Header, Hi, It, Note, Ph,
                                  Pos, Prop, Segtype, Sub, Tmx, Tu, Tuv)
from hypomnema.xml.policy import PolicyValue
from tests.conftest import (_assert_attr, _assert_children, _assert_tag,
                                _assert_text, _serializer)


@pytest.mark.backend
def test_serialize_prop_all_fields(backend: XmlBackend):
  serializer = _serializer(backend)
  prop = Prop(text="value", type="x-key", lang="en", o_encoding="utf-8")

  element = serializer.serialize(prop)

  _assert_tag(backend, element, "prop")
  _assert_attr(backend, element, "type", "x-key")
  _assert_attr(backend, element, "xml:lang", "en")
  _assert_attr(backend, element, "o-encoding", "utf-8")
  _assert_text(backend, element, "value")


@pytest.mark.backend
def test_serialize_note_all_fields(backend: XmlBackend):
  serializer = _serializer(backend)
  note = Note(text="note", lang="fr", o_encoding="latin-1")

  element = serializer.serialize(note)

  _assert_tag(backend, element, "note")
  _assert_attr(backend, element, "xml:lang", "fr")
  _assert_attr(backend, element, "o-encoding", "latin-1")
  _assert_text(backend, element, "note")


@pytest.mark.backend
def test_serialize_header_with_children(backend: XmlBackend):
  serializer = _serializer(backend)
  dt = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
  header = Header(
    creationtool="tool",
    creationtoolversion="1",
    segtype=Segtype.SENTENCE,
    o_tmf="tmf",
    adminlang="en",
    srclang="en-US",
    datatype="plain",
    o_encoding="utf-8",
    creationdate=dt,
    creationid="user",
    changedate=dt,
    changeid="user2",
    notes=[Note(text="n1")],
    props=[Prop(text="p1", type="t1")],
  )

  element = serializer.serialize(header)

  _assert_tag(backend, element, "header")
  _assert_attr(backend, element, "creationtool", "tool")
  _assert_attr(backend, element, "segtype", "sentence")
  _assert_attr(backend, element, "creationdate", dt.isoformat())
  _assert_children(backend, element, 1, tag_filter="note")
  _assert_children(backend, element, 1, tag_filter="prop")


@pytest.mark.backend
def test_serialize_tuv_with_seg(backend: XmlBackend):
  serializer = _serializer(backend)
  dt = datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
  tuv = cast(
    Any,
    Tuv(
      lang="en",
      o_encoding="utf-8",
      datatype="plain",
      usagecount=2,
      lastusagedate=dt,
      creationtool="tool",
      creationtoolversion="1",
      creationdate=dt,
      creationid="user",
      changedate=dt,
      changeid="user2",
      o_tmf="tmf",
      content=["Hello ", Ph(x=1), "World"],
      notes=[Note(text="n")],
      props=[Prop(text="p", type="t")],
    ),
  )

  element = serializer.serialize(tuv)

  _assert_tag(backend, element, "tuv")
  _assert_attr(backend, element, "xml:lang", "en")
  _assert_attr(backend, element, "usagecount", "2")
  _assert_children(backend, element, 1, tag_filter="note")
  _assert_children(backend, element, 1, tag_filter="prop")
  seg = _assert_children(backend, element, 1, tag_filter="seg")[0]
  _assert_text(backend, seg, "Hello ")
  ph = _assert_children(backend, seg, 1, tag_filter="ph")[0]
  assert backend.get_tail(ph) == "World"


@pytest.mark.backend
def test_serialize_tu_with_variants(backend: XmlBackend):
  serializer = _serializer(backend)
  tu = Tu(
    tuid="tu1",
    segtype=Segtype.BLOCK,
    srclang="en",
    notes=[Note(text="n")],
    props=[Prop(text="p", type="t")],
    variants=[Tuv(lang="en"), Tuv(lang="fr")],
  )

  element = serializer.serialize(tu)

  _assert_tag(backend, element, "tu")
  _assert_attr(backend, element, "tuid", "tu1")
  _assert_attr(backend, element, "segtype", "block")
  _assert_children(backend, element, 1, tag_filter="note")
  _assert_children(backend, element, 1, tag_filter="prop")
  _assert_children(backend, element, 2, tag_filter="tuv")


@pytest.mark.backend
def test_serialize_tmx_minimal(backend: XmlBackend):
  serializer = _serializer(backend)
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

  _assert_tag(backend, element, "tmx")
  _assert_attr(backend, element, "version", "1.4")
  _assert_children(backend, element, 1, tag_filter="header")
  body = _assert_children(backend, element, 1, tag_filter="body")[0]
  _assert_children(backend, body, 2, tag_filter="tu")


@pytest.mark.backend
def test_serialize_inline_elements(backend: XmlBackend):
  serializer = _serializer(backend)

  bpt = serializer.serialize(Bpt(i=1, x=2, type="bold", content=["text", Sub(content=["s"])]))
  _assert_tag(backend, bpt, "bpt")
  _assert_attr(backend, bpt, "i", "1")
  _assert_attr(backend, bpt, "x", "2")
  _assert_text(backend, bpt, "text")
  _assert_children(backend, bpt, 1, tag_filter="sub")

  ept = serializer.serialize(Ept(i=1, content=["end"]))
  _assert_tag(backend, ept, "ept")
  _assert_attr(backend, ept, "i", "1")
  _assert_text(backend, ept, "end")

  it = serializer.serialize(It(pos=Pos.BEGIN, x=1, type="code"))
  _assert_tag(backend, it, "it")
  _assert_attr(backend, it, "pos", "begin")

  ph = serializer.serialize(Ph(x=1, assoc=Assoc.P, type="img"))
  _assert_tag(backend, ph, "ph")
  _assert_attr(backend, ph, "assoc", "p")

  hi = serializer.serialize(Hi(x=1, type="b", content=["bold"]))
  _assert_tag(backend, hi, "hi")
  _assert_text(backend, hi, "bold")

  sub = serializer.serialize(Sub(datatype="html", type="link", content=["click"]))
  _assert_tag(backend, sub, "sub")
  _assert_attr(backend, sub, "datatype", "html")


@pytest.mark.backend
def test_serialize_missing_required_attribute(backend: XmlBackend):
  serializer = _serializer(backend)
  prop = Prop(text="value", type=None)  # type: ignore[arg-type]

  with pytest.raises(AttributeSerializationError, match="Required attribute"):
    serializer.serialize(prop)


@pytest.mark.backend
def test_serialize_invalid_child_type(backend: XmlBackend):
  serializer = _serializer(backend)
  header = Header(
    creationtool="tool",
    creationtoolversion="1",
    segtype=Segtype.BLOCK,
    o_tmf="tmf",
    adminlang="en",
    srclang="en",
    datatype="plain",
    notes=[Prop(text="bad", type="t")],  # type: ignore[list-item]
  )

  with pytest.raises(XmlSerializationError, match="Invalid child element"):
    serializer.serialize(header)


@pytest.mark.backend
def test_serialize_invalid_inline_child(backend: XmlBackend):
  serializer = _serializer(backend)
  serializer.policy.invalid_content_element = PolicyValue("raise", logging.DEBUG)
  bpt = Bpt(i=1, content=[Note(text="bad")])  # type: ignore[list-item]

  with pytest.raises(XmlSerializationError, match="Incorrect child element"):
    serializer.serialize(bpt)
