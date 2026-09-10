"""Build direction: handwritten models projected to expected XML.

Every expected XML fragment is written by hand and parsed independently;
nothing here round-trips through the parser. The comparison is structural
(tag, attribute dict, exact text/tails, ordered children), never byte-equal:
attribute order and self-closing spelling are serialization detail, not
contract. None versus empty-string text is asserted in memory through
element.text, because both serialize-to-distinguishable spellings parse
back to None, so no golden fragment carries intentional empty-string text.
Only TmxWarning advisories are muted while constructing the shared table;
errors are matched by substring, never frozen.
"""

import copy
import warnings
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from lxml import etree

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
  TmxModel,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ut,
  Ude,
)
from hypomnema.xml.build import to_element

OFFSET_PLUS_0230 = timezone(timedelta(hours=2, minutes=30))


def assert_same_tree(actual: etree._Element, expected: etree._Element) -> None:
  """Structural equality: tag, attribute dict, exact text/tail, ordered children.

  Recursing level by level so a mismatch is reported at the differing
  subtree rather than as an opaque whole-tree blob.
  """
  assert actual.tag == expected.tag
  assert dict(actual.attrib) == dict(expected.attrib)
  assert actual.text == expected.text
  assert actual.tail == expected.tail
  assert len(actual) == len(expected)
  for actual_child, expected_child in zip(actual, expected, strict=True):
    assert_same_tree(actual_child, expected_child)


def as_runtime_input(value: object) -> Any:
  """A value ty must not static-check against the node union; its rejection is the behavior under test."""
  return value


with warnings.catch_warnings():
  warnings.filterwarnings(
    "ignore", category=TmxWarning
  )  # the unknown-encoding advisory for the Alpha/Beta/Epsilon spellings

  # All fourteen node types, attributes with distinct values, datetimes in
  # native form, hex Map values, hyphen and xml:lang names.
  BUILD_CASES = [
    (
      "note",
      Note(o_encoding="Alpha", xml_lang="fr", lang="fr", text="Bonjour"),
      '<note o-encoding="Alpha" xml:lang="fr" lang="fr">Bonjour</note>',
    ),
    (
      "prop",
      Property(type="x-prop", xml_lang="de", o_encoding="Beta", lang="fr", text="Wert"),
      '<prop type="x-prop" xml:lang="de" o-encoding="Beta" lang="fr">Wert</prop>',
    ),
    (
      "map",
      Map(unicode=0xF8FF, code=0xE9, ent="&", subst="e-grave"),
      '<map unicode="#xF8FF" code="#xE9" ent="&amp;" subst="e-grave"/>',
    ),
    (
      "ude",
      Ude(name="UdeName", base="ISO-8859-1", maps=(Map(unicode=0xE9, code=0x2019),)),
      '<ude name="UdeName" base="ISO-8859-1"><map unicode="#xE9" code="#x2019"/></ude>',
    ),
    (
      "bpt",
      Bpt(i=7, x=12, type="bold", content=("Hi", Sub(datatype="x-sub", content=("sub text",)))),
      '<bpt i="7" x="12" type="bold">Hi<sub datatype="x-sub">sub text</sub></bpt>',
    ),
    ("ept", Ept(i=7, content=("done",)), '<ept i="7">done</ept>'),
    ("it", It(pos="begin", x=3, type="x-it", content=("t",)), '<it pos="begin" x="3" type="x-it">t</it>'),
    (
      "ph",
      Ph(x=1, assoc="p", type="var", content=("var ", Sub(content=("in ", Bpt(i=1), " tail", Ept(i=1))), " end")),
      '<ph x="1" assoc="p" type="var">var <sub>in <bpt i="1"/> tail<ept i="1"/></sub> end</ph>',
    ),
    (
      "sub",
      Sub(type="s", datatype="d", content=("a", Bpt(i=1), "b", Ept(i=1))),
      '<sub datatype="d" type="s">a<bpt i="1"/>b<ept i="1"/></sub>',
    ),
    (
      "hi",
      Hi(x=9, type="emph", content=("outer ", Hi(x=10, content=("nested",)))),
      '<hi x="9" type="emph">outer <hi x="10">nested</hi></hi>',
    ),
    ("ut", Ut(x=5, content=("unknown",)), '<ut x="5">unknown</ut>'),
    (
      "header",
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
      '<header creationtool="Alpha" creationtoolversion="1.2" segtype="block" o-tmf="Gamma"'
      ' adminlang="fr" srclang="de" datatype="Delta" o-encoding="Epsilon"'
      ' creationdate="20240102T030405Z" creationid="Zeta" changedate="20240102T030405+0230"'
      ' changeid="Eta"><note>one</note><prop type="p-two">two</prop>'
      '<ude name="UdeName" base="ISO-8859-1"><map unicode="#xF8FF" code="#xE9"/></ude>'
      "<note>four</note></header>",
    ),
    (
      "tu",
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
      '<tu tuid="T-1" o-encoding="Alpha" datatype="Delta" usagecount="3"'
      ' lastusagedate="20240203T040506Z" creationtool="CT" creationtoolversion="9"'
      ' creationdate="20240304T050607Z" creationid="CI" changedate="20240506T070809Z"'
      ' segtype="paragraph" changeid="CH" o-tmf="Gamma" srclang="en">'
      '<note>meta note</note><prop type="p">meta prop</prop>'
      '<tuv xml:lang="en" usagecount="0"><seg>lead <bpt i="1"/> tail <ept i="1"/></seg></tuv>'
      '<tuv xml:lang="de" o-encoding="Epsilon"><seg/></tuv></tu>',
    ),
    (
      "tuv",
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
      '<tuv xml:lang="fr" o-encoding="Alpha" datatype="Delta" usagecount="2"'
      ' lastusagedate="20240203T040506Z" creationtool="CT" creationtoolversion="9"'
      ' creationdate="20240102T030405Z" creationid="CI" changedate="20240506T070809Z"'
      ' o-tmf="Gamma" changeid="CH" lang="fr-CH"><note>n</note><prop type="p">p</prop>'
      '<seg>Hi <hi x="1">there</hi>!</seg></tuv>',
    ),
  ]


@pytest.mark.parametrize(
  ["model", "expected_xml"], [(case[1], case[2]) for case in BUILD_CASES], ids=[case[0] for case in BUILD_CASES]
)
# The prop/ut/map fixtures legitimately emit their advisories at the build
# boundary now (GAPS decision 19); the emitted warnings are not the subject.
@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_builds_expected_xml(model: TmxNode, expected_xml: str) -> None:
  assert_same_tree(to_element(model), etree.fromstring(expected_xml))


# Expectations stay independent of fixture construction and production name
# conversion. Exact equality also proves every optional attribute is absent.
REQUIRED_ATTRIBUTES = {
  "note": {},
  "prop": {"type": "p"},
  "map": {"unicode": "#xE9"},
  "ude": {"name": "u"},
  "bpt": {"i": "1"},
  "ept": {"i": "1"},
  "it": {"pos": "begin"},
  "ph": {},
  "hi": {},
  "ut": {},
  "sub": {},
  "header": {
    "creationtool": "ct",
    "creationtoolversion": "1",
    "segtype": "sentence",
    "o-tmf": "g",
    "adminlang": "en",
    "srclang": "en",
    "datatype": "txt",
  },
  "tu": {},
  "tuv": {"{http://www.w3.org/XML/1998/namespace}lang": "en"},
}


# The map/ude/ut minimal nodes legitimately emit their advisories at the
# build boundary now (GAPS decision 19); the warnings are not the subject.
@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_absent_optional_attributes_are_omitted(minimal_node: TmxNode) -> None:
  assert dict(to_element(minimal_node).attrib) == REQUIRED_ATTRIBUTES[minimal_node.element]


@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_empty_content_does_not_invent_text(minimal_node: TmxNode) -> None:
  element = to_element(minimal_node)
  # Include required descendants such as tuv/seg and ude/map, not just the
  # structural root whose text slot is always absent.
  assert all(child.text is None for child in element.iter())


@pytest.mark.parametrize(
  ["build_model", "expected_text"],
  [
    (lambda: Note(), None),
    (lambda: Note(text=""), ""),
    (lambda: Property(type="p"), None),
    (lambda: Property(type="p", text=""), ""),
  ],
  ids=["note-none", "note-empty-string", "prop-none", "prop-empty-string"],
)
def test_none_text_and_empty_text_stay_distinct(build_model: Callable[[], TmxNode], expected_text: str | None) -> None:
  # Read back in memory: both spellings would parse to None, so the
  # distinction is asserted on the built element's own text slot.
  assert to_element(build_model()).text == expected_text


@pytest.mark.parametrize(
  ["content", "expected_seg_text"], [((), None), (("",), "")], ids=["no-content", "empty-string-content"]
)
def test_tuv_text_lives_exclusively_in_the_seg_slot(content: tuple[str, ...], expected_seg_text: str | None) -> None:
  # <tuv> itself has no text slot: its content is the <seg> child's text,
  # so the None-versus-empty distinction is read off <seg>, never off <tuv>.
  element = to_element(TranslationUnitVariant(xml_lang="en", content=content))
  assert element.text is None
  assert element[0].text == expected_seg_text


@pytest.mark.parametrize(
  ["model", "expected_xml"],
  [
    (Ph(x=0, content=("t",)), '<ph x="0">t</ph>'),
    (Bpt(i=0), '<bpt i="0"/>'),
    (Property(type="", text="v"), '<prop type="">v</prop>'),
  ],
  ids=["zero-int", "zero-required-int", "empty-string-attr"],
)
def test_zero_and_empty_values_are_retained(model: TmxNode, expected_xml: str) -> None:
  assert_same_tree(to_element(model), etree.fromstring(expected_xml))


def test_empty_seg_is_explicit() -> None:
  assert_same_tree(
    to_element(TranslationUnitVariant(xml_lang="en")), etree.fromstring('<tuv xml:lang="en"><seg/></tuv>')
  )


def test_whitespace_is_kept_exactly() -> None:
  # <hi> carries the general inline grammar, so a bpt may interleave here;
  # <ph> may only carry text and <sub>. The pair must close for the
  # standalone fragment's own flow to be valid (GAPS decision 12).
  assert_same_tree(
    to_element(Hi(content=(" a ", Bpt(i=1), " b ", Ept(i=1)))),
    etree.fromstring('<hi> a <bpt i="1"/> b <ept i="1"/></hi>'),
  )


def test_microsecond_datetime_is_emitted(minimal_header: Header) -> None:
  minimal_header.creationdate = datetime(2024, 1, 2, 3, 4, 5, 123456, tzinfo=UTC)
  assert to_element(minimal_header).get("creationdate") == "20240102T030405.123456Z"


def test_output_is_detached() -> None:
  element = to_element(Note(text="x"))
  assert element.getparent() is None


def test_building_twice_leaves_the_source_model_untouched() -> None:
  model = TranslationUnitVariant(xml_lang="en", metadata=(Note(text="n"),), content=("a", Bpt(i=1), Ept(i=1)))
  # Snapshot before the first call: a first-build mutation must not be
  # hidden by comparing a second build against the first.
  snapshot = copy.deepcopy(model)
  to_element(model)
  to_element(model)
  assert model == snapshot
  assert isinstance(model.metadata, tuple)


# --- Boundary validation (GAPS decision 19): contract rules gate the build. ---


def test_contract_violation_raises_spec_error_before_building() -> None:
  # Prose violations fail the boundary validation pass, not the DTD run.
  with pytest.raises(TmxSpecError, match="inline_tag_pairing"):
    to_element(TranslationUnitVariant(xml_lang="en", content=(Bpt(i=1),)))


def test_cyclic_model_fails_as_spec_error_not_recursion_error() -> None:
  outer, inner = Hi(), Hi()
  outer.content = (inner,)
  inner.content = (outer,)
  with pytest.raises(TmxSpecError):
    to_element(TranslationUnitVariant(xml_lang="en", content=(outer,)))


# --- XML-illegal values and non-models. ---


def test_illegal_attribute_value_is_rejected() -> None:
  with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=TmxWarning)  # the encoding name is also unknown to codecs
    model = Note(o_encoding="bad\x0b")
  with pytest.raises(TmxSpecError, match="XML-illegal attribute"):
    to_element(model)


@pytest.mark.parametrize(
  ["model"], [(Note(text="a\x01b"),), (Ph(content=("a\x02",)),)], ids=["plain-text", "mixed-content"]
)
def test_illegal_text_is_rejected(model: TmxNode) -> None:
  with pytest.raises(TmxSpecError, match="XML-illegal text"):
    to_element(model)


@pytest.mark.parametrize("value", [object(), "note", 42, TmxModel()], ids=["object", "str", "int", "bare-model-base"])
def test_non_model_input_is_a_type_error(value: object) -> None:
  with pytest.raises(TypeError):
    to_element(as_runtime_input(value))


# --- Regression: deep recursion must not overflow. ---


def test_250_nested_hi_build_successfully() -> None:
  model: TmxNode = Hi(content=("core",))
  for _ in range(249):
    model = Hi(content=(model,))
  root = to_element(model)
  assert sum(1 for element in root.iter("hi")) == 250
  assert "".join(root.itertext()) == "core"
