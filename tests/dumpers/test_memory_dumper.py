from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import (
  TranslationMemory,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
)
from hypomnema.dumpers.xml import TranslationMemoryDumper


def dump_memory(backend: XmlBackend[object]) -> object:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )
  unit = TranslationUnit.create(
    translation_unit_id="tu-1",
    variants=[TranslationVariant.create(language="en", segment=["Hello"])],
  )
  return TranslationMemoryDumper(backend).dump(
    TranslationMemory.create(header=header, version="1.4", units=[unit])
  )


def test_memory_dumper_emits_tmx_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(dump_memory(backend)) == "tmx"


def test_memory_dumper_emits_version_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_memory(backend), "version") == "1.4"


def test_memory_dumper_emits_header_as_first_child(backend: XmlBackend[object]) -> None:
  assert [backend.get_tag(child) for child in backend.iter_children(dump_memory(backend))][
    0
  ] == "header"


def test_memory_dumper_emits_body_as_second_child(backend: XmlBackend[object]) -> None:
  assert [backend.get_tag(child) for child in backend.iter_children(dump_memory(backend))][
    1
  ] == "body"


def test_memory_dumper_emits_unit_inside_body(backend: XmlBackend[object]) -> None:
  children = list(backend.iter_children(dump_memory(backend)))
  body = children[1]

  assert backend.get_tag(next(backend.iter_children(body))) == "tu"


def test_memory_dumper_preserves_unit_id_inside_body(backend: XmlBackend[object]) -> None:
  children = list(backend.iter_children(dump_memory(backend)))
  body = children[1]
  unit = next(backend.iter_children(body))

  assert backend.get_attribute(unit, "tuid") == "tu-1"
