from datetime import datetime
from pathlib import Path

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import (
  Note,
  Prop,
  TranslationMemory,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
  UnknownNode,
)
from hypomnema.dumpers.xml import TranslationMemoryDumper, TranslationUnitDumper
from hypomnema.loaders.xml import TranslationMemoryLoader, TranslationUnitLoader


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def canonicalize[T](
  backend: XmlBackend[T], element: T
) -> tuple[str, tuple[tuple[str, str], ...], str | None, str | None, tuple[object, ...]]:
  return (
    backend.get_tag(element),
    tuple(sorted(backend.get_attribute_map(element).items())),
    backend.get_text(element),
    backend.get_tail(element),
    tuple(canonicalize(backend, child) for child in backend.iter_children(element)),
  )


def dump_and_reload_unit(
  backend: XmlBackend[object], tmp_path: Path, node: TranslationUnit, filename: str
) -> TranslationUnit:
  element = TranslationUnitDumper(backend).dump(node)
  payload = backend.to_bytes(element, strip_tail=True)
  path = tmp_path / filename
  path.write_bytes(payload)
  return TranslationUnitLoader(backend).load(backend.parse(path))


def dump_and_reload_memory(
  backend: XmlBackend[object], tmp_path: Path, node: TranslationMemory, filename: str
) -> TranslationMemory:
  element = TranslationMemoryDumper(backend).dump(node)
  payload = backend.to_bytes(element, strip_tail=True)
  path = tmp_path / filename
  path.write_bytes(payload)
  return TranslationMemoryLoader(backend).load(backend.parse(path))


def make_unknown_node(backend: XmlBackend[object], tmp_path: Path) -> UnknownNode:
  payload_element = parse_xml(
    backend, tmp_path, "unknown-node.xml", '<extra-root source="external">keep me</extra-root>'
  )
  return UnknownNode(payload=backend.to_bytes(payload_element, strip_tail=True))


def test_translation_unit_node_roundtrip_preserves_semantics(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  node = TranslationUnit.create(
    translation_unit_id="tu-1",
    original_encoding="utf-8",
    original_data_type="xml",
    usage_count=4,
    last_used_at=datetime(2024, 4, 5, 6, 7, 8),
    created_at=datetime(2024, 4, 1, 1, 2, 3),
    last_modified_at=datetime(2024, 4, 6, 7, 8, 9),
    segmentation_type="sentence",
    source_language="fr",
    notes=[Note.create(text="unit note")],
    props=[Prop.create(text="finance", kind="domain")],
    variants=[
      TranslationVariant.create(language="en", segment=["Hello"]),
      TranslationVariant.create(language="fr", segment=["Bonjour"]),
    ],
  )

  assert dump_and_reload_unit(backend, tmp_path, node, "unit-known.xml") == node


def test_translation_memory_node_roundtrip_preserves_semantics(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  node = TranslationMemory.create(
    header=TranslationMemoryHeader.create(
      creation_tool="hypomnema",
      creation_tool_version="1.0",
      segmentation_type="sentence",
      original_translation_memory_format="tmx",
      admin_language="en",
      source_language="fr",
      original_data_type="plaintext",
      original_encoding="utf-8",
      created_at=datetime(2024, 1, 2, 3, 4, 5),
      created_by="creator",
      last_modified_at=datetime(2024, 2, 3, 4, 5, 6),
      last_modified_by="modifier",
      notes=[Note.create(text="header note")],
      props=[Prop.create(text="header prop", kind="domain")],
    ),
    version="1.5",
    units=[
      TranslationUnit.create(
        translation_unit_id="tu-1",
        variants=[TranslationVariant.create(language="en", segment=["Hello"])],
      )
    ],
  )

  assert dump_and_reload_memory(backend, tmp_path, node, "memory-known.xml") == node


def test_translation_memory_xml_roundtrip_preserves_structure(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  original = parse_xml(
    backend,
    tmp_path,
    "memory-structure.xml",
    (
      '<tmx version="1.5">'
      '<header creationtool="hypomnema" creationtoolversion="1.0" segtype="sentence" '
      'o-tmf="tmx" adminlang="en" srclang="fr" datatype="plaintext" o-encoding="utf-8" '
      'creationdate="20240102T030405" creationid="creator" changedate="20240203T040506" '
      'changeid="modifier"><note>header note</note><prop type="domain">header prop</prop></header>'
      '<body><tu tuid="tu-1"><tuv xml:lang="en"><seg>Hello</seg></tuv></tu></body>'
      "</tmx>"
    ),
  )

  node = TranslationMemoryLoader(backend).load(original)
  reparsed = parse_xml(
    backend,
    tmp_path,
    "memory-structure-reparsed.xml",
    backend.to_bytes(TranslationMemoryDumper(backend).dump(node), strip_tail=True).decode("utf-8"),
  )

  assert canonicalize(backend, reparsed) == canonicalize(backend, original)


def test_translation_memory_node_roundtrip_preserves_unknown_top_level_payload(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  unknown = make_unknown_node(backend, tmp_path)
  node = TranslationMemory.create(
    header=TranslationMemoryHeader.create(
      creation_tool="hypomnema",
      creation_tool_version="1.0",
      segmentation_type="sentence",
      original_translation_memory_format="tmx",
      admin_language="en",
      source_language="fr",
      original_data_type="plaintext",
    ),
    extra_nodes=[unknown],
  )

  reloaded = dump_and_reload_memory(backend, tmp_path, node, "memory-unknown.xml")

  assert len(reloaded.extra_nodes) == 1
  assert reloaded.extra_nodes[0].payload == unknown.payload


def test_translation_memory_xml_roundtrip_preserves_unknown_top_level_structure(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  original = parse_xml(
    backend,
    tmp_path,
    "memory-unknown-structure.xml",
    (
      '<tmx version="1.4">'
      '<header creationtool="hypomnema" creationtoolversion="1.0" segtype="sentence" '
      'o-tmf="tmx" adminlang="en" srclang="fr" datatype="plaintext" />'
      '<body><tu><tuv xml:lang="en"><seg>Hello</seg></tuv></tu></body>'
      '<extra-root source="external">keep me</extra-root>'
      "</tmx>"
    ),
  )

  node = TranslationMemoryLoader(backend).load(original)
  reparsed = parse_xml(
    backend,
    tmp_path,
    "memory-unknown-structure-reparsed.xml",
    backend.to_bytes(TranslationMemoryDumper(backend).dump(node), strip_tail=True).decode("utf-8"),
  )

  assert canonicalize(backend, reparsed) == canonicalize(backend, original)
