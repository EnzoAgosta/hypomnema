from pathlib import Path

import pytest

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.attributes import Segtype
from hypomnema.domain.nodes import TranslationMemory, UnknownNode
from hypomnema.loaders.xml import TranslationMemoryLoader


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def parse_payload[T](backend: XmlBackend[T], tmp_path: Path, filename: str, payload: object) -> T:
  path = tmp_path / filename
  assert isinstance(payload, bytes)
  path.write_bytes(payload)
  return backend.parse(path)


def load_minimal_memory(backend: XmlBackend[object], tmp_path: Path) -> TranslationMemory:
  element = parse_xml(
    backend,
    tmp_path,
    "memory-minimal.xml",
    (
      '<tmx version="1.4">'
      '<header creationtool="hypomnema" creationtoolversion="1.0" segtype="sentence" '
      'o-tmf="tmx" adminlang="en" srclang="fr" datatype="plaintext" />'
      '<body><tu><tuv xml:lang="en"><seg>Hello</seg></tuv></tu></body>'
      "</tmx>"
    ),
  )
  return TranslationMemoryLoader(backend).load(element)


def load_rich_memory(backend: XmlBackend[object], tmp_path: Path) -> TranslationMemory:
  element = parse_xml(
    backend,
    tmp_path,
    "memory-rich.xml",
    (
      '<tmx version="1.5" custom="value">'
      '<extra-root source="external">keep me</extra-root>'
      '<header creationtool="hypomnema" creationtoolversion="1.0" segtype="paragraph" '
      'o-tmf="tmx" adminlang="en-US" srclang="fr-FR" datatype="xml" '
      'o-encoding="utf-8" creationdate="2024-01-02T03:04:05" creationid="creator" '
      'changedate="2024-02-03T04:05:06" changeid="modifier">'
      "<note>header note</note>"
      '<prop type="domain">finance</prop>'
      "</header>"
      '<body><tu tuid="tu-1"><tuv xml:lang="en"><seg>Hello</seg></tuv></tu></body>'
      "</tmx>"
    ),
  )
  return TranslationMemoryLoader(backend).load(element)


def test_memory_loader_sets_version_from_minimal_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_memory(backend, tmp_path).spec_attributes.version == "1.4"


def test_memory_loader_loads_header_from_minimal_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_memory(backend, tmp_path).header.spec_attributes.creation_tool == "hypomnema"


def test_memory_loader_loads_header_segmentation_type(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert (
    load_minimal_memory(backend, tmp_path).header.spec_attributes.segmentation_type
    is Segtype.SENTENCE
  )


def test_memory_loader_loads_units_from_minimal_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert len(load_minimal_memory(backend, tmp_path).units) == 1


def test_memory_loader_loads_variant_segment_from_minimal_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_memory(backend, tmp_path).units[0].variants[0].segment == ["Hello"]


def test_memory_loader_defaults_extra_attributes_to_empty_dict(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_memory(backend, tmp_path).extra_attributes == {}


def test_memory_loader_defaults_extra_nodes_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_memory(backend, tmp_path).extra_nodes == []


def test_memory_loader_sets_version_from_rich_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_memory(backend, tmp_path).spec_attributes.version == "1.5"


def test_memory_loader_preserves_extra_attributes(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_memory(backend, tmp_path).extra_attributes == {"custom": "value"}


def test_memory_loader_sets_header_segmentation_type(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert (
    load_rich_memory(backend, tmp_path).header.spec_attributes.segmentation_type
    is Segtype.PARAGRAPH
  )


def test_memory_loader_sets_header_original_encoding(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_memory(backend, tmp_path).header.spec_attributes.original_encoding == "utf-8"


def test_memory_loader_loads_header_notes(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [note.text for note in load_rich_memory(backend, tmp_path).header.notes] == ["header note"]


def test_memory_loader_loads_header_props(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [prop.text for prop in load_rich_memory(backend, tmp_path).header.props] == ["finance"]


def test_memory_loader_loads_unit_ids(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [
    unit.spec_attributes.translation_unit_id for unit in load_rich_memory(backend, tmp_path).units
  ] == ["tu-1"]


def test_memory_loader_preserves_unknown_top_level_children(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  extra_nodes = load_rich_memory(backend, tmp_path).extra_nodes

  assert len(extra_nodes) == 1
  assert isinstance(extra_nodes[0], UnknownNode)


def test_memory_loader_preserves_unknown_top_level_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  payload = load_rich_memory(backend, tmp_path).extra_nodes[0].payload

  assert (
    backend.get_tag(parse_payload(backend, tmp_path, "memory-extra-root.xml", payload))
    == "extra-root"
  )


def test_memory_loader_requires_header(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(
    backend, tmp_path, "memory-missing-header.xml", '<tmx version="1.4"><body /></tmx>'
  )

  with pytest.raises(ValueError, match="Missing <header> element"):
    TranslationMemoryLoader(backend).load(element)


def test_memory_loader_rejects_multiple_header_elements(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  element = parse_xml(
    backend,
    tmp_path,
    "memory-multiple-header.xml",
    (
      '<tmx version="1.4">'
      '<header creationtool="a" creationtoolversion="1" segtype="sentence" o-tmf="tmx" adminlang="en" srclang="fr" datatype="txt" />'
      '<header creationtool="b" creationtoolversion="1" segtype="sentence" o-tmf="tmx" adminlang="en" srclang="fr" datatype="txt" />'
      "<body />"
      "</tmx>"
    ),
  )

  with pytest.raises(ValueError, match="Multiple <header> elements"):
    TranslationMemoryLoader(backend).load(element)


def test_memory_loader_requires_body(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(
    backend,
    tmp_path,
    "memory-missing-body.xml",
    (
      '<tmx version="1.4">'
      '<header creationtool="a" creationtoolversion="1" segtype="sentence" o-tmf="tmx" adminlang="en" srclang="fr" datatype="txt" />'
      "</tmx>"
    ),
  )

  with pytest.raises(ValueError, match="Missing <body> element"):
    TranslationMemoryLoader(backend).load(element)


def test_memory_loader_rejects_multiple_body_elements(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  element = parse_xml(
    backend,
    tmp_path,
    "memory-multiple-body.xml",
    (
      '<tmx version="1.4">'
      '<header creationtool="a" creationtoolversion="1" segtype="sentence" o-tmf="tmx" adminlang="en" srclang="fr" datatype="txt" />'
      "<body />"
      "<body />"
      "</tmx>"
    ),
  )

  with pytest.raises(ValueError, match="Multiple <body> elements"):
    TranslationMemoryLoader(backend).load(element)


def test_memory_loader_rejects_wrong_tag(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(backend, tmp_path, "memory-wrong-tag.xml", "<body />")

  with pytest.raises(ValueError, match="Expected <tmx> element"):
    TranslationMemoryLoader(backend).load(element)
