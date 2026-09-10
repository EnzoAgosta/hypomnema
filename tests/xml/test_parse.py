"""Parse direction: handwritten XML fragments projected to expected models.

Every expected model is written by hand; nothing here round-trips through
the builder. TmxWarning advisories are muted only where legitimately emitted
(the happy-path table and the bare-<map> value case, via narrowly applied
filterwarnings marks); error messages are matched by tag/line/substring,
never frozen, since the full lxml/Pydantic wording is not the contract.
"""

import warnings
from datetime import UTC, datetime, timedelta, timezone

import pytest
from lxml import etree
from pydantic import ValidationError

from hypomnema.errors import TmxSpecError, TmxWarning
from hypomnema.models import (
  Bpt,
  Ept,
  Header,
  Hi,
  It,
  Map,
  Note,
  Ph,
  Property,
  Sub,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ut,
  Ude,
)
from hypomnema.xml.parse import from_element

OFFSET_PLUS_0230 = timezone(timedelta(hours=2, minutes=30))


# All fourteen node types, each with every attribute set to a distinct value
# so a field swap cannot hide behind a duplicate, and with the mechanical
# name mapping (xml:lang, o-encoding, o-tmf) exercised where it applies.
with warnings.catch_warnings():
  warnings.filterwarnings(
    "ignore", category=TmxWarning
  )  # the unknown-encoding advisory for the Alpha/Beta/Epsilon spellings

  HAPPY_PATH = [
    (
      "note",
      '<note o-encoding="Alpha" xml:lang="fr-CA" lang="fr">Bonjour</note>',
      Note(o_encoding="Alpha", xml_lang="fr-CA", lang="fr", text="Bonjour"),
    ),
    (
      "prop",
      '<prop type="x-prop" xml:lang="de" o-encoding="Beta" lang="fr">Wert</prop>',
      Property(type="x-prop", xml_lang="de", o_encoding="Beta", lang="fr", text="Wert"),
    ),
    (
      "map",
      '<map unicode="#xF8FF" code="#x00E9" ent="&amp;" subst="e-grave"/>',
      Map(unicode=0xF8FF, code=0xE9, ent="&", subst="e-grave"),
    ),
    (
      "ude",
      '<ude name="UdeName" base="ISO-8859-1"><map unicode="#xF8FF" code="#x00E9"/>'
      '<map unicode="#x00E8" subst="e-grave"/></ude>',
      Ude(name="UdeName", base="ISO-8859-1", maps=(Map(unicode=0xF8FF, code=0xE9), Map(unicode=0xE8, subst="e-grave"))),
    ),
    (
      "bpt",
      '<bpt i="7" x="12" type="bold">Hi<sub datatype="x-sub">sub text</sub></bpt>',
      Bpt(i=7, x=12, type="bold", content=("Hi", Sub(datatype="x-sub", content=("sub text",)))),
    ),
    ("ept", '<ept i="7">done</ept>', Ept(i=7, content=("done",))),
    ("it", '<it pos="end" x="3" type="x-it">t</it>', It(pos="end", x=3, type="x-it", content=("t",))),
    (
      "ph",
      '<ph x="1" assoc="p" type="var">var text<sub>inner</sub></ph>',
      Ph(x=1, assoc="p", type="var", content=("var text", Sub(content=("inner",)))),
    ),
    (
      "hi",
      '<hi x="9" type="emph">outer <hi x="10">nested</hi></hi>',
      Hi(x=9, type="emph", content=("outer ", Hi(x=10, content=("nested",)))),
    ),
    ("ut", '<ut x="5">unknown</ut>', Ut(x=5, content=("unknown",))),
    (
      "sub",
      '<sub type="s" datatype="d">a<bpt i="1"/>b<ept i="1"/></sub>',
      Sub(type="s", datatype="d", content=("a", Bpt(i=1), "b", Ept(i=1))),
    ),
    (
      "header",
      '<header creationtool="Alpha" creationtoolversion="1.2" segtype="block" o-tmf="Gamma"'
      ' adminlang="fr" srclang="de" datatype="Delta" o-encoding="Epsilon"'
      ' creationdate="20240102T030405Z" creationid="Zeta" changedate="20240102T030405+0230"'
      ' changeid="Eta">'
      '<note>one</note><prop type="p-two">two</prop>'
      '<ude name="UdeName" base="ISO-8859-1"><map unicode="#xF8FF" code="#x00E9"/></ude>'
      "<note>four</note></header>",
      Header(
        creationtool="Alpha",
        creationtoolversion="1.2",
        segtype="block",
        o_tmf="Gamma",
        adminlang="fr",
        srclang="de",
        datatype="Delta",
        o_encoding="Epsilon",
        creationdate=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
        creationid="Zeta",
        changedate=datetime(2024, 1, 2, 3, 4, 5, tzinfo=OFFSET_PLUS_0230),
        changeid="Eta",
        metadata=(
          Note(text="one"),
          Property(type="p-two", text="two"),
          Ude(name="UdeName", base="ISO-8859-1", maps=(Map(unicode=0xF8FF, code=0xE9),)),
          Note(text="four"),
        ),
      ),
    ),
    (
      "tu",
      '<tu tuid="T-1" o-encoding="Alpha" datatype="Delta" usagecount="3"'
      ' lastusagedate="20240203T040506Z" creationtool="CT" creationtoolversion="9"'
      ' creationdate="20240304T050607Z" creationid="CI" changedate="20240506T070809Z"'
      ' segtype="paragraph" changeid="CH" o-tmf="Gamma" srclang="en">'
      '<note>meta note</note><prop type="p">meta prop</prop>'
      '<tuv xml:lang="en" usagecount="0"><seg>lead <bpt i="1"/> tail <ept i="1"/></seg></tuv>'
      '<tuv xml:lang="de" o-encoding="Epsilon"><seg/></tuv></tu>',
      TranslationUnit(
        tuid="T-1",
        o_encoding="Alpha",
        datatype="Delta",
        usagecount=3,
        lastusagedate=datetime(2024, 2, 3, 4, 5, 6, tzinfo=UTC),
        creationtool="CT",
        creationtoolversion="9",
        creationdate=datetime(2024, 3, 4, 5, 6, 7, tzinfo=UTC),
        creationid="CI",
        changedate=datetime(2024, 5, 6, 7, 8, 9, tzinfo=UTC),
        segtype="paragraph",
        changeid="CH",
        o_tmf="Gamma",
        srclang="en",
        metadata=(Note(text="meta note"), Property(type="p", text="meta prop")),
        variants=(
          TranslationUnitVariant(xml_lang="en", usagecount=0, content=("lead ", Bpt(i=1), " tail ", Ept(i=1))),
          TranslationUnitVariant(xml_lang="de", o_encoding="Epsilon"),
        ),
      ),
    ),
    (
      "tuv",
      '<tuv xml:lang="fr" lang="fr-CH" o-encoding="Alpha" datatype="Delta" usagecount="2"'
      ' lastusagedate="20240203T040506Z" creationtool="CT" creationtoolversion="9"'
      ' creationdate="20240102T030405Z" creationid="CI" changedate="20240506T070809Z"'
      ' o-tmf="Gamma" changeid="CH">'
      '<note>n</note><prop type="p">p</prop>'
      '<seg>Hi <hi x="1">there</hi>!</seg></tuv>',
      TranslationUnitVariant(
        xml_lang="fr",
        o_encoding="Alpha",
        datatype="Delta",
        usagecount=2,
        lastusagedate=datetime(2024, 2, 3, 4, 5, 6, tzinfo=UTC),
        creationtool="CT",
        creationtoolversion="9",
        creationdate=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
        creationid="CI",
        changedate=datetime(2024, 5, 6, 7, 8, 9, tzinfo=UTC),
        o_tmf="Gamma",
        changeid="CH",
        lang="fr-CH",
        metadata=(Note(text="n"), Property(type="p", text="p")),
        content=("Hi ", Hi(x=1, content=("there",)), "!"),
      ),
    ),
  ]


@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
@pytest.mark.parametrize(
  ["markup", "expected"], [(case[1], case[2]) for case in HAPPY_PATH], ids=[case[0] for case in HAPPY_PATH]
)
def test_parses_to_expected_model(markup: str, expected: TmxNode) -> None:
  assert from_element(etree.fromstring(markup)) == expected


def test_header_metadata_preserves_interleaved_document_order() -> None:
  markup = (
    '<header creationtool="CT" creationtoolversion="1" segtype="block" o-tmf="G" adminlang="en"'
    ' srclang="en" datatype="txt"><note>n</note><prop type="p">p</prop>'
    '<ude name="U" base="ISO-8859-1"><map unicode="#x41" code="#x42"/></ude><note>n2</note></header>'
  )
  parsed = from_element(etree.fromstring(markup))
  assert isinstance(parsed, Header)
  assert [child.element for child in parsed.metadata] == ["note", "prop", "ude", "note"]
  assert [child.text for child in parsed.metadata if isinstance(child, Note)] == ["n", "n2"]


def test_tu_metadata_stays_separate_from_variants() -> None:
  markup = (
    '<tu><note>n</note><prop type="p">p</prop>'
    '<tuv xml:lang="en"><seg>s</seg></tuv><tuv xml:lang="de"><seg>s</seg></tuv></tu>'
  )
  parsed = from_element(etree.fromstring(markup))
  assert isinstance(parsed, TranslationUnit)
  assert [child.element for child in parsed.metadata] == ["note", "prop"]
  assert [variant.xml_lang for variant in parsed.variants] == ["en", "de"]


def test_seg_wrapper_dissolves_into_tuv_content() -> None:
  parsed = from_element(etree.fromstring('<tuv xml:lang="en"><seg>a<bpt i="1"/>b<ept i="1"/></seg></tuv>'))
  assert isinstance(parsed, TranslationUnitVariant)
  assert parsed.content == ("a", Bpt(i=1), "b", Ept(i=1))


def test_empty_seg_is_empty_content_not_missing() -> None:
  parsed = from_element(etree.fromstring('<tuv xml:lang="en"><seg/></tuv>'))
  assert isinstance(parsed, TranslationUnitVariant)
  assert parsed.content == ()


def test_whitespace_is_kept_exactly() -> None:
  note = from_element(etree.fromstring("<note>  spaced  </note>"))
  assert isinstance(note, Note)
  assert note.text == "  spaced  "
  variant = from_element(etree.fromstring('<tuv xml:lang="en"><seg> a <bpt i="1"/> b <ept i="1"/></seg></tuv>'))
  assert isinstance(variant, TranslationUnitVariant)
  assert variant.content == (" a ", Bpt(i=1), " b ", Ept(i=1))


def test_absent_attributes_and_text_are_none() -> None:
  parsed = from_element(etree.fromstring('<ept i="2"/>'))
  assert parsed == Ept(i=2)
  note = from_element(etree.fromstring("<note/>"))
  assert isinstance(note, Note)
  assert note.text is None


def test_read_text_keeps_none_and_explicitly_empty_distinct() -> None:
  """In-memory elements distinguish an absent text slot from an empty one."""
  absent = etree.Element("note")
  assert from_element(absent) == Note()
  explicit = etree.Element("note")
  explicit.text = ""
  assert from_element(explicit) == Note(text="")
  absent_prop = etree.Element("prop")
  absent_prop.set("type", "p")
  assert from_element(absent_prop) == Property(type="p")
  explicit_prop = etree.Element("prop")
  explicit_prop.set("type", "p")
  explicit_prop.text = ""
  assert from_element(explicit_prop) == Property(type="p", text="")


with warnings.catch_warnings():
  warnings.filterwarnings("ignore", category=TmxWarning)  # a bare <map> has no target advisory
  VALUE_CASES = [
    ('<ph x="0">t</ph>', Ph(x=0, content=("t",))),
    ('<ept i="007"/>', Ept(i=7)),
    ('<map unicode="#x00E9"/>', Map(unicode=0xE9)),
    ('<prop type="">t</prop>', Property(type="", text="t")),
  ]


@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
@pytest.mark.parametrize(
  ["markup", "expected"], VALUE_CASES, ids=["zero-int", "leading-zeros", "hex-leading-zeros", "empty-string-attr"]
)
def test_zero_and_empty_values_are_retained(markup: str, expected: TmxNode) -> None:
  assert from_element(etree.fromstring(markup)) == expected


def test_datetime_offsets_survive_as_native_values() -> None:
  parsed = from_element(etree.fromstring('<tuv xml:lang="en" lastusagedate="20240203T040506.123456+0230"><seg/></tuv>'))
  assert isinstance(parsed, TranslationUnitVariant)
  assert parsed.lastusagedate is not None
  assert parsed.lastusagedate == datetime(2024, 2, 3, 4, 5, 6, 123456, tzinfo=OFFSET_PLUS_0230)
  # Equality of aware datetimes alone would also accept normalization to UTC.
  assert parsed.lastusagedate.utcoffset() == timedelta(hours=2, minutes=30)


@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_parse_leaves_the_source_tree_untouched() -> None:
  element = etree.fromstring('<note o-encoding="Alpha">hi</note>')
  from_element(element)
  assert element.attrib == {"o-encoding": "Alpha"}
  assert element.text == "hi"
  assert len(element) == 0


# --- Errors: unknown vocabulary, invalid structure and values, context. ---


@pytest.mark.parametrize(
  ["markup", "match"],
  [("<frobnicate/>", "frobnicate"), ('<note xmlns="http://example.com/ns">x</note>', "http://example.com")],
  ids=["unknown-element", "namespaced-element"],
)
def test_unknown_vocabulary_is_rejected(markup: str, match: str) -> None:
  with pytest.raises(TmxSpecError, match=match):
    from_element(etree.fromstring(markup))


def test_unknown_attribute_is_rejected_with_dtd_cause() -> None:
  with pytest.raises(TmxSpecError, match="bogus") as excinfo:
    from_element(etree.fromstring('<note bogus="1">x</note>'))
  assert isinstance(excinfo.value.__cause__, etree.DocumentInvalid)


def test_missing_required_child_is_rejected_with_dtd_cause() -> None:
  with pytest.raises(TmxSpecError) as excinfo:
    from_element(etree.fromstring('<tuv xml:lang="en"/>'))
  assert isinstance(excinfo.value.__cause__, etree.DocumentInvalid)


@pytest.mark.parametrize(
  "markup",
  [
    '<tu><tuv xml:lang="en"><seg/></tuv><note>too late</note></tu>',
    '<tuv xml:lang="en"><seg/><note>too late</note></tuv>',
    '<tuv xml:lang="en"><seg/><seg/></tuv>',
    "<tu><note>no variants</note></tu>",
    '<ude name="empty"/>',
    '<tu>stray<tuv xml:lang="en"><seg/></tuv></tu>',
    '<tuv xml:lang="en"><seg/>stray</tuv>',
  ],
  ids=[
    "tu-order",
    "tuv-order",
    "duplicate-seg",
    "missing-variants",
    "missing-maps",
    "container-text",
    "container-tail",
  ],
)
def test_invalid_structure_is_rejected_before_projection_can_discard_it(markup: str) -> None:
  with pytest.raises(TmxSpecError) as excinfo:
    from_element(etree.fromstring(markup))
  assert isinstance(excinfo.value.__cause__, etree.DocumentInvalid)


def test_dtd_enumeration_value_is_rejected() -> None:
  markup = (
    '<header creationtool="CT" creationtoolversion="1" segtype="word" o-tmf="G"'
    ' adminlang="en" srclang="en" datatype="txt"/>'
  )
  with pytest.raises(TmxSpecError, match="segtype"):
    from_element(etree.fromstring(markup))


@pytest.mark.parametrize(
  ["markup", "match"],
  [
    ('<bpt i="1x"/>', "line 1"),
    ('<map unicode="#xZZ"/>', "line 1"),
    ('<tuv xml:lang="en" lastusagedate="not-a-date"><seg/></tuv>', "line 1"),
    ('<tuv xml:lang="not a tag"><seg/></tuv>', "line 1"),
  ],
  ids=["bad-int", "bad-hex", "bad-datetime", "bad-language-tag"],
)
def test_invalid_value_is_rejected_with_pydantic_cause(markup: str, match: str) -> None:
  with pytest.raises(TmxSpecError, match=match) as excinfo:
    from_element(etree.fromstring(markup))
  assert isinstance(excinfo.value.__cause__, ValidationError)


def test_error_context_names_element_and_line() -> None:
  # The DTD rejects the tuv without xml:lang, so the wrapper reports the
  # <tu> while the lxml cause still points at the offending line 3; the
  # nested value-error case below covers projection's own checks.
  markup = '<tu>\n  <tuv xml:lang="en"><seg/></tuv>\n  <tuv><seg/></tuv>\n</tu>'
  with pytest.raises(TmxSpecError, match="<tu>.*line 3"):
    from_element(etree.fromstring(markup))


def test_nested_value_error_keeps_source_line_and_pydantic_cause() -> None:
  # The DTD cannot see that i="1x" is not a number, so the projection's own
  # value check fires deep inside the tree and still reports the offending
  # element and its source line, with the Pydantic cause attached.
  markup = '<tu>\n  <tuv xml:lang="en"><seg><bpt i="1x"/></seg></tuv>\n</tu>'
  with pytest.raises(TmxSpecError, match="<bpt>.*line 2") as excinfo:
    from_element(etree.fromstring(markup))
  assert isinstance(excinfo.value.__cause__, ValidationError)


@pytest.mark.parametrize("markup", ["<seg/>", "<body/>"], ids=["seg", "body"])
def test_document_wrappers_have_no_standalone_model(markup: str) -> None:
  # The wrappers pass DTD validation, so the rejection is the projection's
  # own: they have no standalone domain model.
  with pytest.raises(TmxSpecError, match="standalone"):
    from_element(etree.fromstring(markup))


def test_tmx_has_no_standalone_model(valid_tmx_document: str) -> None:
  # The full document passes DTD validation, so the rejection is the
  # projection's own: it has no standalone domain model.
  with pytest.raises(TmxSpecError, match="standalone"):
    from_element(etree.fromstring(valid_tmx_document))


def test_legacy_lang_never_substitutes_for_required_xml_lang() -> None:
  with pytest.raises(TmxSpecError):
    from_element(etree.fromstring('<tuv lang="en"><seg/></tuv>'))


@pytest.mark.parametrize(
  "markup",
  ['<bpt i="1"><hi>x</hi></bpt>', "<sub><sub/></sub>", '<ept i="1"><ept i="2"/></ept>'],
  ids=["hi-in-bpt", "sub-in-sub", "ept-in-ept"],
)
def test_illegal_inline_nesting_is_rejected(markup: str) -> None:
  with pytest.raises(TmxSpecError):
    from_element(etree.fromstring(markup))


# --- Advisories: soft warnings, kept values. ---


def test_ut_deprecation_warning() -> None:
  with pytest.warns(TmxWarning, match="deprecated"):
    from_element(etree.fromstring("<ut/>"))


def test_lang_without_xml_lang_warns() -> None:
  with pytest.warns(TmxWarning, match="prefer xml:lang"):
    from_element(etree.fromstring('<note lang="fr"/>'))


def test_differing_lang_and_xml_lang_warn() -> None:
  with pytest.warns(TmxWarning, match="differ"):
    from_element(etree.fromstring('<note lang="fr" xml:lang="de"/>'))


def test_map_without_any_target_warns() -> None:
  with pytest.warns(TmxWarning, match="code, ent, or subst"):
    from_element(etree.fromstring('<map unicode="#x41"/>'))


@pytest.mark.parametrize(
  "markup",
  [
    '<tuv xml:lang="en"><seg><bpt i="1"/></seg></tuv>',
    '<tuv xml:lang="en"><seg><bpt i="1"/><ept i="2"/></seg></tuv>',
    '<tuv xml:lang="en"><seg><bpt i="1"/><ept i="1"/><ept i="1"/></seg></tuv>',
    '<tuv xml:lang="en"><seg><ept i="1"/><bpt i="1"/></seg></tuv>',
  ],
)
def test_pairing_contract_is_enforced_on_read(markup: str) -> None:
  # The boundary validation pass applies the prose rules to the projected
  # model, not just the DTD and typing: unmatched bpt, mismatched pair,
  # duplicate ept i, and ept before bpt all fail on read. Matching the
  # pairing marker proves the failure came from that pass.
  with pytest.raises(TmxSpecError, match="inline_tag_pairing"):
    from_element(etree.fromstring(markup))


def test_equivalent_lang_and_xml_lang_do_not_warn() -> None:
  # This runs under an escalating filter to prove the advisory is absent,
  # not swallowed by any suppression elsewhere in the suite.
  with warnings.catch_warnings():
    warnings.filterwarnings("error", category=TmxWarning)
    parsed = from_element(etree.fromstring('<note lang="FR" xml:lang="fr">x</note>'))
  assert isinstance(parsed, Note)
  assert parsed.text == "x"
