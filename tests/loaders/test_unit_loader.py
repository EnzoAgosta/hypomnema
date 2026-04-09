from pathlib import Path

import pytest

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.attributes import Segtype
from hypomnema.domain.nodes import TranslationUnit, UnknownNode
from hypomnema.loaders.xml import TranslationUnitLoader


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def parse_payload[T](backend: XmlBackend[T], tmp_path: Path, filename: str, payload: object) -> T:
  path = tmp_path / filename
  assert isinstance(payload, bytes)
  path.write_bytes(payload)
  return backend.parse(path)


def load_minimal_unit(backend: XmlBackend[object], tmp_path: Path) -> TranslationUnit:
  element = parse_xml(
    backend, tmp_path, "unit-minimal.xml", '<tu><tuv lang="en"><seg>Hello</seg></tuv></tu>'
  )
  return TranslationUnitLoader(backend).load(element)


def load_rich_unit(backend: XmlBackend[object], tmp_path: Path) -> TranslationUnit:
  element = parse_xml(
    backend,
    tmp_path,
    "unit-rich.xml",
    (
      '<tu tuid="tu-1" o-encoding="utf-8" datatype="xml" usagecount="9" '
      'lastusagedate="2024-04-05T06:07:08" creationtool="tool" '
      'creationtoolversion="2.0" creationdate="2024-04-01T01:02:03" creationid="creator" '
      'changedate="2024-04-06T07:08:09" segtype="paragraph" changeid="modifier" '
      'o-tmf="legacy" srclang="en-US" custom="value">'
      "<note>unit note</note>"
      '<prop type="domain">finance</prop>'
      '<extra-unit kind="opaque">keep me</extra-unit>'
      '<tuv lang="en"><seg>Source</seg></tuv>'
      '<tuv lang="fr"><seg>Cible</seg></tuv>'
      "</tu>"
    ),
  )
  return TranslationUnitLoader(backend).load(element)


def test_unit_loader_defaults_translation_unit_id_to_none(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_unit(backend, tmp_path).spec_attributes.translation_unit_id is None


def test_unit_loader_loads_minimal_variant(backend: XmlBackend[object], tmp_path: Path) -> None:
  unit = load_minimal_unit(backend, tmp_path)

  assert len(unit.variants) == 1
  assert unit.variants[0].segment == ["Hello"]


def test_unit_loader_defaults_notes_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_unit(backend, tmp_path).notes == []


def test_unit_loader_defaults_props_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_unit(backend, tmp_path).props == []


def test_unit_loader_defaults_extra_attributes_to_empty_dict(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_unit(backend, tmp_path).extra_attributes == {}


def test_unit_loader_defaults_extra_nodes_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_unit(backend, tmp_path).extra_nodes == []


def test_unit_loader_sets_translation_unit_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_unit(backend, tmp_path).spec_attributes.translation_unit_id == "tu-1"


def test_unit_loader_sets_original_encoding(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_unit(backend, tmp_path).spec_attributes.original_encoding == "utf-8"


def test_unit_loader_sets_original_data_type(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_unit(backend, tmp_path).spec_attributes.original_data_type == "xml"


def test_unit_loader_coerces_usage_count(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_unit(backend, tmp_path).spec_attributes.usage_count == 9


def test_unit_loader_sets_segmentation_type(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_unit(backend, tmp_path).spec_attributes.segmentation_type is Segtype.PARAGRAPH


def test_unit_loader_sets_source_language(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_unit(backend, tmp_path).spec_attributes.source_language == "en-US"


def test_unit_loader_preserves_extra_attributes(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_unit(backend, tmp_path).extra_attributes == {"custom": "value"}


def test_unit_loader_loads_note_children(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [note.text for note in load_rich_unit(backend, tmp_path).notes] == ["unit note"]


def test_unit_loader_loads_prop_children(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [prop.text for prop in load_rich_unit(backend, tmp_path).props] == ["finance"]


def test_unit_loader_loads_variant_languages(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [
    variant.spec_attributes.language for variant in load_rich_unit(backend, tmp_path).variants
  ] == ["en", "fr"]


def test_unit_loader_loads_variant_segments(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [variant.segment for variant in load_rich_unit(backend, tmp_path).variants] == [
    ["Source"],
    ["Cible"],
  ]


def test_unit_loader_preserves_unknown_children(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  extra_nodes = load_rich_unit(backend, tmp_path).extra_nodes

  assert len(extra_nodes) == 1
  assert isinstance(extra_nodes[0], UnknownNode)


def test_unit_loader_preserves_unknown_child_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  payload = load_rich_unit(backend, tmp_path).extra_nodes[0].payload

  assert (
    backend.get_tag(parse_payload(backend, tmp_path, "unit-extra.xml", payload)) == "extra-unit"
  )


def test_unit_loader_rejects_wrong_tag(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(
    backend, tmp_path, "unit-wrong-tag.xml", '<tuv lang="en"><seg>Hello</seg></tuv>'
  )

  with pytest.raises(ValueError, match="Expected <tu> element"):
    TranslationUnitLoader(backend).load(element)
