"""DTD-driven completeness checks and integration round trips.

The DTD is loaded independently of the production loader. Attribute examples
are handwritten native/lexical pairs, not generated with production parsers
or formatters. Individual direction tests live in test_parse/test_build.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from importlib.resources import files
from typing import get_args

import pytest
from lxml import etree

from hypomnema.models import (
  Bpt,
  Ept,
  Header,
  Hi,
  Map,
  Note,
  Ph,
  Property,
  Sub,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
)
from hypomnema.xml.build import to_element
from hypomnema.xml.parse import from_element

with files("hypomnema").joinpath("resources", "tmx14.dtd").open("rb") as source:
  DTD = etree.DTD(source)
DECLARATIONS = {name: declaration for declaration in DTD.iterelements() if (name := declaration.name) is not None}
MODELED_TAGS = sorted(DECLARATIONS.keys() - {"tmx", "body", "seg"})
NODE_TYPES: tuple[type[TmxNode], ...] = get_args(TmxNode.__value__)
NODE_MODELS = {str(node_type.model_fields["element"].default): node_type for node_type in NODE_TYPES}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Distinct values make swapped fields observable. Ordinary CDATA fields get
# their own name as part of the value; these are the fields with value rules.
ATTRIBUTE_VALUES: dict[str, tuple[str, object]] = {
  "adminlang": ("en-GB", "en-GB"),
  "srclang": ("*all*", "*all*"),
  "xml:lang": ("fr-CA", "fr-CA"),
  "lang": ("FR-ca", "FR-ca"),
  "o-encoding": ("utf-8", "utf-8"),
  "base": ("ascii", "ascii"),
  "segtype": ("paragraph", "paragraph"),
  "pos": ("end", "end"),
  "assoc": ("b", "b"),
  "i": ("11", 11),
  "x": ("17", 17),
  "usagecount": ("23", 23),
  "unicode": ("#x1F642", 0x1F642),
  "code": ("#xA9", 0xA9),
  "creationdate": ("20240102T030405Z", datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)),
  "changedate": (
    "20250506T070809.123456-0430",
    datetime(2025, 5, 6, 7, 8, 9, 123456, tzinfo=timezone(-timedelta(hours=4, minutes=30))),
  ),
  "lastusagedate": ("20260607T080910Z", datetime(2026, 6, 7, 8, 9, 10, tzinfo=UTC)),
}


def attribute_examples(tag: str) -> Iterator[tuple[str, str, str, object]]:
  """Yield expanded XML name, model field, lexical value, native value."""
  for attribute in DECLARATIONS[tag].iterattributes():
    name = attribute.name
    assert name is not None
    xml_name = f"{attribute.prefix}:{name}" if attribute.prefix is not None else name
    field_name = xml_name.replace("-", "_").replace(":", "_")
    sample_text = f"{xml_name}-value"
    lexical, native = ATTRIBUTE_VALUES.get(xml_name, (sample_text, sample_text))
    expanded_name = XML_LANG if xml_name == "xml:lang" else xml_name
    yield expanded_name, field_name, lexical, native


def fragment_with_all_attributes(tag: str) -> etree._Element:
  attributes = {xml_name: lexical for xml_name, _, lexical, _ in attribute_examples(tag)}
  element = etree.Element(tag, attributes)
  # Minimal legal children, authored independently of the model builder.
  match tag:
    case "tu":
      variant = etree.SubElement(element, "tuv", {XML_LANG: "en"})
      etree.SubElement(variant, "seg")
    case "tuv":
      etree.SubElement(element, "seg")
    case "ude":
      etree.SubElement(element, "map", unicode="#x41", ent="A")
  return element


def model_with_all_attributes(minimal_node: TmxNode) -> TmxNode:
  attributes: dict[str, object] = {field: native for _, field, _, native in attribute_examples(minimal_node.element)}
  # Reuse construction scaffolding, never an XML parse result, for required
  # children. Attribute expectations still come independently from the DTD.
  match minimal_node:
    case TranslationUnit():
      attributes["variants"] = minimal_node.variants
    case Ude():
      attributes["maps"] = minimal_node.maps
  return type(minimal_node).model_validate(attributes)


def test_node_union_covers_exactly_the_dtd_elements_with_domain_models() -> None:
  assert set(NODE_MODELS) == set(MODELED_TAGS)
  assert len(NODE_TYPES) == len(NODE_MODELS)  # no duplicate tags hiding different classes


@pytest.mark.parametrize("tag", MODELED_TAGS)
def test_model_attribute_inventory_and_requiredness_agree_with_dtd(tag: str) -> None:
  content_fields = {"element", "text", "content", "metadata", "variants", "maps"}
  modeled = {
    name: field.is_required() for name, field in NODE_MODELS[tag].model_fields.items() if name not in content_fields
  }
  declared = {}
  for attribute in DECLARATIONS[tag].iterattributes():
    name = attribute.name
    assert name is not None
    xml_name = f"{attribute.prefix}:{name}" if attribute.prefix is not None else name
    declared[xml_name.replace("-", "_").replace(":", "_")] = attribute.default == "required"
  assert modeled == declared


@pytest.mark.parametrize("tag", MODELED_TAGS)
@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_every_declared_attribute_is_read_into_its_native_model_field(tag: str) -> None:
  element = fragment_with_all_attributes(tag)
  DTD.assertValid(element)
  model = from_element(element)
  assert type(model) is NODE_MODELS[tag]
  expected = {field: native for _, field, _, native in attribute_examples(tag)}
  actual = {field: getattr(model, field) for field in expected}
  assert actual == expected


@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_every_declared_attribute_is_written_with_its_xml_name_and_spelling(minimal_node: TmxNode) -> None:
  model = model_with_all_attributes(minimal_node)
  element = to_element(model)
  DTD.assertValid(element)
  assert element.tag == minimal_node.element
  assert dict(element.attrib) == {
    xml_name: lexical for xml_name, _, lexical, _ in attribute_examples(minimal_node.element)
  }


def test_header_tree_round_trip_preserves_interleaving_and_empty_text_slots(minimal_header: Header) -> None:
  original = minimal_header
  original.metadata = (
    Note(text=None),
    Property(type="empty", text=""),
    Ude(
      name="source-alphabet",
      base="ascii",
      maps=(Map(unicode=0, ent="nul"), Map(unicode=0x1F642, code=0x41, subst=":)")),
    ),
    Note(xml_lang="fr", text="  note\nintacte  "),
  )
  wrapper = etree.Element("tmx", version="1.4")
  wrapper.append(to_element(original))
  etree.SubElement(wrapper, "body")
  DTD.assertValid(wrapper)
  assert from_element(wrapper[0]) == original


@pytest.mark.filterwarnings("ignore::hypomnema.errors.TmxWarning")
def test_unit_serialized_round_trip_preserves_nested_flows_and_metadata() -> None:
  # The two variants legitimately disagree on inline x values (the en
  # variant has them, the fr one does not), so the cross-variant advisory
  # fires at both boundaries; it is not this test's subject.
  original = TranslationUnit(
    tuid="unit-1",
    changedate=datetime(2025, 2, 3, 4, 5, 6, 123456, tzinfo=timezone(timedelta(hours=2))),
    metadata=(Property(type="domain", text=" examples "), Note(text="unit note")),
    variants=(
      TranslationUnitVariant(
        xml_lang="en",
        metadata=(Note(text="variant note"), Property(type="origin", text="human")),
        content=(
          "Before ",
          Bpt(i=1, x=0, content=("<b>",)),
          Hi(type="term", content=("term", Ept(i=1, content=("</b>",)))),
          " ",
          Ph(x=2, content=('title="', Sub(content=(Bpt(i=1), "description", Ept(i=1))), '"')),
          " after\n  ",
        ),
      ),
      TranslationUnitVariant(xml_lang="fr", content=("autre texte",)),
    ),
  )
  wrapper = etree.Element("body")
  wrapper.append(to_element(original))
  DTD.assertValid(wrapper)
  reparsed = etree.fromstring(etree.tostring(wrapper))
  assert from_element(reparsed[0]) == original


def test_serialized_round_trip_only_collapses_empty_text_and_string_chunk_boundaries() -> None:
  original = TranslationUnitVariant(
    xml_lang="en",
    metadata=(Note(text=""), Property(type="absent", text=None)),
    content=("a", "", "b", Ph(content=("",)), "", "c", ""),
  )
  expected = TranslationUnitVariant(
    xml_lang="en", metadata=(Note(text=None), Property(type="absent", text=None)), content=("ab", Ph(), "c")
  )
  serialized = etree.tostring(to_element(original))
  assert from_element(etree.fromstring(serialized)) == expected
