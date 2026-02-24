"""Tests for API helper functions.

Tests the factory functions for creating TMX elements and the iter_text utility.
"""

from datetime import UTC, datetime


from hypomnema.api.helpers import (
  _normalize_content,
  create_bpt,
  create_ept,
  create_header,
  create_hi,
  create_it,
  create_note,
  create_ph,
  create_prop,
  create_sub,
  create_tmx,
  create_tu,
  create_tuv,
  iter_text,
)
from hypomnema.base.types import Assoc, Bpt, Pos, Segtype, Sub, Tuv


class TestNormalizeContent:
  """Tests for _normalize_content helper function."""

  def test_normalize_content_with_string(self) -> None:
    result = _normalize_content("text")
    assert result == ["text"]

  def test_normalize_content_with_list(self) -> None:
    result = _normalize_content(["a", "b"])
    assert result == ["a", "b"]

  def test_normalize_content_with_none(self) -> None:
    result = _normalize_content(None)
    assert result == []

  def test_normalize_content_with_empty_list(self) -> None:
    result = _normalize_content([])
    assert result == []


class TestIterText:
  """Tests for iter_text function."""

  def test_iter_text_with_strings_only(self) -> None:
    tuv = Tuv(lang="en", content=["Hello", "World"])
    assert list(iter_text(tuv)) == ["Hello", "World"]

  def test_iter_text_ignores_nested(self) -> None:
    tuv = Tuv(lang="en", content=["Hello", Bpt(i=1, content=["code"]), " World"])
    assert list(iter_text(tuv, ignore=Bpt)) == ["Hello", " World"]

  def test_iter_text_recurse_inside_ignored_nested(self) -> None:
    tuv = Tuv(
      lang="en", content=["Hello", Bpt(i=1, content=["code", Sub(content=["subflow"])]), " World"]
    )
    assert list(iter_text(tuv, ignore=Bpt, recurse_inside_ignored=True)) == [
      "Hello",
      "subflow",
      " World",
    ]

  def test_iter_text_does_not_recurse_inside_ignored(self) -> None:
    tuv = Tuv(
      lang="en", content=["Hello", Bpt(i=1, content=["code", Sub(content=["subflow"])]), " World"]
    )
    assert list(iter_text(tuv, ignore=Bpt, recurse_inside_ignored=False)) == ["Hello", " World"]

  def test_iter_text_on_empty_content(self) -> None:
    tuv = Tuv(lang="en", content=[])
    assert list(iter_text(tuv)) == []


class TestCreateTmx:
  """Tests for create_tmx factory function."""

  def test_create_tmx_with_defaults(self) -> None:
    tmx = create_tmx()
    assert tmx.version == "1.4"
    assert tmx.header is not None
    assert tmx.body == []

  def test_create_tmx_with_custom_header(self) -> None:
    header = create_header(creationtool="custom")
    tmx = create_tmx(header=header)
    assert tmx.header.creationtool == "custom"

  def test_create_tmx_with_body(self) -> None:
    tu = create_tu()
    tmx = create_tmx(body=[tu])
    assert len(tmx.body) == 1

  def test_create_tmx_with_version(self) -> None:
    tmx = create_tmx(version="1.5")
    assert tmx.version == "1.5"

  def test_create_tmx_with_empty_version_uses_default(self) -> None:
    tmx = create_tmx(version="")
    assert tmx.version == "1.4"


class TestCreateHeader:
  """Tests for create_header factory function."""

  def test_create_header_with_defaults(self) -> None:
    header = create_header()
    assert header.creationtool == "hypomnema"
    assert header.segtype == Segtype.BLOCK
    assert header.o_tmf == "tmx"
    assert header.adminlang == "en"
    assert header.srclang == "en"
    assert header.datatype == "plaintext"
    assert header.creationdate is not None

  def test_create_header_with_string_segtype(self) -> None:
    header = create_header(segtype="sentence")
    assert header.segtype == Segtype.SENTENCE

  def test_create_header_with_enum_segtype(self) -> None:
    header = create_header(segtype=Segtype.PARAGRAPH)
    assert header.segtype == Segtype.PARAGRAPH

  def test_create_header_with_custom_creationdate(self) -> None:
    custom_date = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
    header = create_header(creationdate=custom_date)
    assert header.creationdate == custom_date

  def test_create_header_with_notes_and_props(self) -> None:
    note = create_note("test note")
    prop = create_prop("value", "type")
    header = create_header(notes=[note], props=[prop])
    assert len(header.notes) == 1
    assert len(header.props) == 1


class TestCreateTu:
  """Tests for create_tu factory function."""

  def test_create_tu_with_defaults(self) -> None:
    tu = create_tu()
    assert tu.tuid is None
    assert tu.variants == []
    assert tu.creationdate is not None

  def test_create_tu_with_tuid(self) -> None:
    tu = create_tu(tuid="tu-001")
    assert tu.tuid == "tu-001"

  def test_create_tu_with_string_segtype(self) -> None:
    tu = create_tu(segtype="phrase")
    assert tu.segtype == Segtype.PHRASE

  def test_create_tu_with_enum_segtype(self) -> None:
    tu = create_tu(segtype=Segtype.SENTENCE)
    assert tu.segtype == Segtype.SENTENCE

  def test_create_tu_with_variants(self) -> None:
    tuv_en = create_tuv("en", content="Hello")
    tuv_fr = create_tuv("fr", content="Bonjour")
    tu = create_tu(variants=[tuv_en, tuv_fr])
    assert len(tu.variants) == 2

  def test_create_tu_with_notes_and_props(self) -> None:
    note = create_note("tu note")
    prop = create_prop("value", "type")
    tu = create_tu(notes=[note], props=[prop])
    assert len(tu.notes) == 1
    assert len(tu.props) == 1


class TestCreateTuv:
  """Tests for create_tuv factory function."""

  def test_create_tuv_with_string_content(self) -> None:
    tuv = create_tuv("en", content="Hello World")
    assert tuv.lang == "en"
    assert tuv.content == ["Hello World"]

  def test_create_tuv_with_list_content(self) -> None:
    tuv = create_tuv("en", content=["Hello", " ", "World"])
    assert tuv.content == ["Hello", " ", "World"]

  def test_create_tuv_with_none_content(self) -> None:
    tuv = create_tuv("en", content=None)
    assert tuv.content == []

  def test_create_tuv_with_inline_elements(self) -> None:
    bpt = create_bpt(1)
    tuv = create_tuv("en", content=["Hello ", bpt, " World"])
    assert len(tuv.content) == 3
    assert isinstance(tuv.content[1], Bpt)

  def test_create_tuv_with_attributes(self) -> None:
    tuv = create_tuv("en", content="text", o_encoding="utf-8", datatype="html", usagecount=5)
    assert tuv.o_encoding == "utf-8"
    assert tuv.datatype == "html"
    assert tuv.usagecount == 5

  def test_create_tuv_with_notes_and_props(self) -> None:
    note = create_note("note")
    prop = create_prop("value", "type")
    tuv = create_tuv("en", content="text", notes=[note], props=[prop])
    assert len(tuv.notes) == 1
    assert len(tuv.props) == 1


class TestCreateNote:
  """Tests for create_note factory function."""

  def test_create_note_with_text(self) -> None:
    note = create_note("A note")
    assert note.text == "A note"
    assert note.lang is None
    assert note.o_encoding is None

  def test_create_note_with_all_attributes(self) -> None:
    note = create_note("A note", lang="en", o_encoding="utf-8")
    assert note.text == "A note"
    assert note.lang == "en"
    assert note.o_encoding == "utf-8"


class TestCreateProp:
  """Tests for create_prop factory function."""

  def test_create_prop_required_fields(self) -> None:
    prop = create_prop("value", "category")
    assert prop.text == "value"
    assert prop.type == "category"

  def test_create_prop_with_all_attributes(self) -> None:
    prop = create_prop("value", "category", lang="en", o_encoding="utf-8")
    assert prop.text == "value"
    assert prop.type == "category"
    assert prop.lang == "en"
    assert prop.o_encoding == "utf-8"


class TestCreateBpt:
  """Tests for create_bpt factory function."""

  def test_create_bpt_required_field(self) -> None:
    bpt = create_bpt(1)
    assert bpt.i == 1
    assert bpt.content == []

  def test_create_bpt_with_string_content(self) -> None:
    bpt = create_bpt(1, content="code")
    assert bpt.content == ["code"]

  def test_create_bpt_with_list_content(self) -> None:
    sub = create_sub(content="subflow")
    bpt = create_bpt(1, content=["code ", sub])
    assert len(bpt.content) == 2
    assert isinstance(bpt.content[1], Sub)

  def test_create_bpt_with_attributes(self) -> None:
    bpt = create_bpt(1, x=10, type="bold")
    assert bpt.x == 10
    assert bpt.type == "bold"


class TestCreateEpt:
  """Tests for create_ept factory function."""

  def test_create_ept_required_field(self) -> None:
    ept = create_ept(1)
    assert ept.i == 1
    assert ept.content == []

  def test_create_ept_with_string_content(self) -> None:
    ept = create_ept(1, content="code")
    assert ept.content == ["code"]

  def test_create_ept_with_list_content(self) -> None:
    sub = create_sub(content="subflow")
    ept = create_ept(1, content=["code ", sub])
    assert len(ept.content) == 2


class TestCreateIt:
  """Tests for create_it factory function."""

  def test_create_it_with_string_pos(self) -> None:
    it = create_it("begin")
    assert it.pos == Pos.BEGIN

  def test_create_it_with_enum_pos(self) -> None:
    it = create_it(Pos.END)
    assert it.pos == Pos.END

  def test_create_it_with_content(self) -> None:
    it = create_it("begin", content="code")
    assert it.content == ["code"]

  def test_create_it_with_attributes(self) -> None:
    it = create_it("begin", x=5, type="font")
    assert it.x == 5
    assert it.type == "font"


class TestCreatePh:
  """Tests for create_ph factory function."""

  def test_create_ph_with_defaults(self) -> None:
    ph = create_ph()
    assert ph.content == []
    assert ph.x is None
    assert ph.assoc is None

  def test_create_ph_with_content(self) -> None:
    ph = create_ph(content="placeholder")
    assert ph.content == ["placeholder"]

  def test_create_ph_with_string_assoc(self) -> None:
    ph = create_ph(assoc="p")
    assert ph.assoc == Assoc.P

  def test_create_ph_with_enum_assoc(self) -> None:
    ph = create_ph(assoc=Assoc.F)
    assert ph.assoc == Assoc.F

  def test_create_ph_with_attributes(self) -> None:
    ph = create_ph(x=1, type="image", assoc="b")
    assert ph.x == 1
    assert ph.type == "image"
    assert ph.assoc == Assoc.B


class TestCreateHi:
  """Tests for create_hi factory function."""

  def test_create_hi_with_defaults(self) -> None:
    hi = create_hi()
    assert hi.content == []
    assert hi.x is None
    assert hi.type is None

  def test_create_hi_with_string_content(self) -> None:
    hi = create_hi(content="highlighted")
    assert hi.content == ["highlighted"]

  def test_create_hi_with_inline_elements(self) -> None:
    bpt = create_bpt(1)
    hi = create_hi(content=["text ", bpt])
    assert len(hi.content) == 2

  def test_create_hi_with_attributes(self) -> None:
    hi = create_hi(x=1, type="term")
    assert hi.x == 1
    assert hi.type == "term"


class TestCreateSub:
  """Tests for create_sub factory function."""

  def test_create_sub_with_defaults(self) -> None:
    sub = create_sub()
    assert sub.content == []
    assert sub.datatype is None
    assert sub.type is None

  def test_create_sub_with_content(self) -> None:
    sub = create_sub(content="subflow text")
    assert sub.content == ["subflow text"]

  def test_create_sub_with_inline_elements(self) -> None:
    bpt = create_bpt(1)
    sub = create_sub(content=["text ", bpt])
    assert len(sub.content) == 2

  def test_create_sub_with_attributes(self) -> None:
    sub = create_sub(datatype="html", type="footnote")
    assert sub.datatype == "html"
    assert sub.type == "footnote"
