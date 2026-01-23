import pytest

from hypomnema.api import (create_bpt, create_ept, create_header, create_hi,
                           create_it, create_note, create_ph, create_prop,
                           create_sub, create_tmx, create_tu, create_tuv)
from hypomnema.base.types import Assoc, Pos, Segtype


@pytest.mark.helpers
def test_create_prop_defaults():
  prop = create_prop("value", "key")

  assert prop.text == "value"
  assert prop.type == "key"
  assert prop.lang is None


@pytest.mark.helpers
def test_create_note_defaults():
  note = create_note("note")

  assert note.text == "note"
  assert note.lang is None


@pytest.mark.helpers
def test_create_header_defaults():
  header = create_header()

  assert header.creationtool == "hypomnema"
  assert header.segtype == Segtype.BLOCK
  assert header.adminlang == "en"


@pytest.mark.helpers
def test_create_tu_defaults():
  tu = create_tu()

  assert tu.variants == []
  assert tu.notes == []
  assert tu.props == []


@pytest.mark.helpers
def test_create_tuv_defaults():
  tuv = create_tuv("en")

  assert tuv.lang == "en"
  assert tuv.content == []


@pytest.mark.helpers
def test_create_inline_elements():
  bpt = create_bpt(1, content=["text"], type="bold")
  assert bpt.i == 1
  assert bpt.type == "bold"

  ept = create_ept(1, content=["end"])
  assert ept.i == 1

  it = create_it(Pos.BEGIN, content=["x"], type="code")
  assert it.pos == Pos.BEGIN

  ph = create_ph(content=["img"], assoc=Assoc.P, type="img")
  assert ph.assoc == Assoc.P

  hi = create_hi(content=["hi"], type="b")
  assert hi.type == "b"

  sub = create_sub(content=["sub"], datatype="html", type="link")
  assert sub.datatype == "html"


@pytest.mark.helpers
def test_create_tmx_defaults():
  tmx = create_tmx()

  assert tmx.version == "1.4"
  assert tmx.body == []
  assert tmx.header.creationtool == "hypomnema"
