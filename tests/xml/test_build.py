"""Unit tests for the per-node builders in ``xml.build``.

The golden corpus doubles as the output oracle: fragments are written in
the models' field order, so a validated node rebuilds to the byte-identical
fragment. The writer gate is exercised per node with one planted defect.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

import pytest
from lxml import etree

from hypomnema.errors import TmxDeprecationWarning, TmxErrorGroup, TmxSpecError
from hypomnema.models import Bpt, Header, Map, Note, Sub, TmxNode, TranslationUnit, TranslationUnitVariant, Ude, Ut
from hypomnema.xml.build import (
  bpt_to_element,
  ept_to_element,
  header_to_element,
  hi_to_element,
  it_to_element,
  map_to_element,
  note_to_element,
  ph_to_element,
  prop_to_element,
  sub_to_element,
  to_element,
  tu_to_element,
  tuv_to_element,
  ude_to_element,
  ut_to_element,
)
from hypomnema.xml.names import xml_attribute_name
from hypomnema.xml.parse import from_element

TAGS = ("bpt", "ept", "header", "hi", "it", "map", "note", "ph", "prop", "sub", "tu", "tuv", "ude", "ut")

TO_FUNCTIONS = cast(
  dict[str, Callable[[TmxNode], etree._Element]],
  {
    "note": note_to_element,
    "prop": prop_to_element,
    "map": map_to_element,
    "ude": ude_to_element,
    "header": header_to_element,
    "tu": tu_to_element,
    "tuv": tuv_to_element,
    "bpt": bpt_to_element,
    "ept": ept_to_element,
    "it": it_to_element,
    "ph": ph_to_element,
    "hi": hi_to_element,
    "ut": ut_to_element,
    "sub": sub_to_element,
  },
)

# One defect per node kind, planted on a corpus-parsed model: the
# writer gate must catch it. Nested defects ride the deep paths.
DEFECTS = {
  "note": lambda note: setattr(note, "text", 42),
  "prop": lambda prop: setattr(prop, "type", None),
  "map": lambda mapping: setattr(mapping, "unicode", 0xD800),
  "ude": lambda ude: setattr(ude, "base", None),
  "bpt": lambda bpt: setattr(bpt, "i", -1),
  "ept": lambda ept: setattr(ept, "i", -1),
  "it": lambda it: setattr(it, "pos", "middle"),
  "ph": lambda ph: setattr(ph, "assoc", "both"),
  "hi": lambda hi: hi.content.append(42),
  "ut": lambda ut: ut.content.append(42),
  "sub": lambda sub: setattr(sub, "datatype", 42),
  "tuv": lambda tuv: setattr(tuv, "xml_lang", 42),
  "tu": lambda tu: setattr(tu.variants[0], "xml_lang", 42),
  "header": lambda header: setattr(header, "adminlang", "not a tag!"),
}


# The writer gate: validation before anything is built.


@pytest.mark.parametrize("tag", TAGS)
def test_to_element_gates_through_validation(tag, corpus):
  """One planted defect per node kind: the writer must refuse to build."""
  model = from_element(etree.fromstring(corpus[tag]))
  DEFECTS[tag](model)
  with pytest.raises(TmxErrorGroup):
    TO_FUNCTIONS[tag](model)


def test_writer_gate_raises_tmx_error_groups_not_tmx_spec_error(corpus):
  """Expose model validation failures as field-error groups before building XML."""
  tu = cast(TranslationUnit, from_element(etree.fromstring(corpus["tu"])))
  first_bpt = tu.variants[0].content[1]
  assert isinstance(first_bpt, Bpt)
  first_bpt.i = 99
  with pytest.raises(TmxErrorGroup) as excinfo:
    tu_to_element(tu)
  assert not isinstance(excinfo.value, TmxSpecError)


def test_writer_gate_attaches_advisories_to_the_group(corpus):
  """Attach a legacy-code deprecation advisory to the group containing its error."""
  ut = cast(Ut, from_element(etree.fromstring(corpus["ut"])))
  ut.content.append(42)  # ty: ignore[invalid-argument-type]  # the planted defect
  with pytest.raises(TmxErrorGroup) as excinfo:
    ut_to_element(ut)
  assert len(excinfo.value.exceptions) == 1
  assert [advisory.category for advisory in excinfo.value.advisories] == [TmxDeprecationWarning]


def test_writer_gate_rides_the_deep_paths(corpus):
  """Report invalid nested maps and subflows with their full model-relative paths."""
  ude = cast(Ude, from_element(etree.fromstring(corpus["ude"])))
  ude.maps[0].unicode = 0xD800
  with pytest.raises(TmxErrorGroup) as excinfo:
    ude_to_element(ude)
  assert str(excinfo.value.exceptions[0]).startswith("maps[0].unicode")

  tu = cast(TranslationUnit, from_element(etree.fromstring(corpus["tu"])))
  first_bpt = tu.variants[0].content[1]
  assert isinstance(first_bpt, Bpt)
  first_bpt.content.append(Sub.model_construct(element="sub", datatype=42, type=None, content=[]))
  with pytest.raises(TmxErrorGroup) as excinfo:
    tu_to_element(tu)
  assert str(excinfo.value.exceptions[0]).startswith("variants[0].content[1].content[1].datatype")


def test_valid_writer_gate_raises_nothing(corpus):
  """Build every corpus node, including legacy nodes with nonfatal advisories."""
  for tag in TAGS:
    TO_FUNCTIONS[tag](from_element(etree.fromstring(corpus[tag])))


# Verbatim rendering: the corpus is written in field order, so a
# validated model rebuilds to the byte-identical fragment.


@pytest.mark.parametrize("tag", TAGS)
def test_to_element_renders_the_corpus_verbatim(tag, corpus):
  """Reproduce the hand-written fragment's XML and attribute order exactly."""
  model = from_element(etree.fromstring(corpus[tag]))
  built = TO_FUNCTIONS[tag](model)
  assert etree.tostring(built).decode() == corpus[tag]


# Attribute formatting: the mechanical name rule and the serializers.


def test_attributes_are_formatted_per_type():
  """Format dates and hex values, map attribute names, and omit None values."""
  header = Header(
    creationtool="tool",
    creationtoolversion="1.0",
    segtype="paragraph",
    o_tmf="tmf",
    adminlang="en",
    srclang="en",
    datatype="plaintext",
    creationdate=datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC),
  )
  element = header_to_element(header)
  assert element.get("creationdate") == "20240101T123045Z"
  assert element.get("o-tmf") == "tmf"
  assert element.get("o-encoding") is None  # None attributes are omitted

  mapping = Map(unicode=0xF8FF)
  map_element = map_to_element(mapping)
  assert map_element.get("unicode") == "#xF8FF"


def test_integer_attributes_render_as_decimal():
  """Render usage counts as decimal and variant timestamps in TMX notation."""
  tu = TranslationUnit(
    tuid="tu-1",
    srclang="en",
    usagecount=3,
    variants=[TranslationUnitVariant(xml_lang="en", lastusagedate=datetime(2024, 6, 1, 12, 0, tzinfo=UTC))],
  )
  element = tu_to_element(tu)
  assert element.get("usagecount") == "3"
  tuv = element.find("tuv")
  assert tuv is not None
  assert tuv.get(xml_attribute_name("lastusagedate")) == "20240601T120000Z"


def test_xml_lang_uses_the_qualified_name():
  """Write xml:lang with its XML namespace rather than the Python field name."""
  tuv = tuv_to_element(TranslationUnitVariant(xml_lang="en"))
  assert tuv.get("{http://www.w3.org/XML/1998/namespace}lang") == "en"
  assert tuv.get("xml_lang") is None


def test_xml_illegal_attribute_values_are_reported(corpus):
  """Reject XML-illegal attribute text even when the model accepts the string."""
  header = cast(Header, from_element(etree.fromstring(corpus["header"])))
  header.creationtool = "bad \x03 tool"
  with pytest.raises(TmxSpecError, match="XML-illegal"):
    header_to_element(header)


def test_xml_illegal_text_is_reported():
  """Report forbidden XML control characters in note text."""
  with pytest.raises(TmxSpecError, match="XML-illegal"):
    note_to_element(Note(text="bad \x03 text"))


def test_xml_illegal_text_is_reported_through_the_content_walk():
  """Identify the enclosing inline element when its text is XML-illegal."""
  from hypomnema.models import Ph

  with pytest.raises(TmxSpecError, match="XML-illegal text inside <ph>"):
    ph_to_element(Ph(content=["bad \x03"]))


def test_unsupported_attribute_value_is_reported_as_type_error():
  """Reject attribute values outside the string, datetime, and integer types."""
  from hypomnema.xml import build

  note = Note.model_construct(element="note", text="x")
  note.__dict__["junk"] = object()
  with pytest.raises(TypeError, match="unsupported attribute value"):
    build._write_attributes(etree.Element("note"), note)


# The generic dispatcher agrees with the per-node builders.


@pytest.mark.parametrize("tag", TAGS)
def test_to_element_dispatch_matches_per_node_builders(tag, corpus):
  """Make generic and per-node builders emit identical XML for every node kind."""
  model = from_element(etree.fromstring(corpus[tag]))
  assert etree.tostring(to_element(model)).decode() == etree.tostring(TO_FUNCTIONS[tag](model)).decode()
