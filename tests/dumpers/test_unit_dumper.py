from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.attributes import Segtype
from hypomnema.domain.nodes import TranslationUnit, TranslationVariant
from hypomnema.dumpers.xml import TranslationUnitDumper


def dump_unit(backend: XmlBackend[object]) -> object:
  variant = TranslationVariant.create(language="en", segment=["Hello"])
  node = TranslationUnit.create(
    translation_unit_id="tu-1",
    original_encoding="utf-8",
    original_data_type="xml",
    usage_count=4,
    segmentation_type=Segtype.SENTENCE,
    source_language="fr",
    variants=[variant],
  )
  return TranslationUnitDumper(backend).dump(node)


def test_unit_dumper_emits_tu_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(dump_unit(backend)) == "tu"


def test_unit_dumper_emits_translation_unit_id_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_unit(backend), "tuid") == "tu-1"


def test_unit_dumper_emits_original_encoding_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_unit(backend), "o-encoding") == "utf-8"


def test_unit_dumper_emits_original_data_type_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_unit(backend), "datatype") == "xml"


def test_unit_dumper_emits_usage_count_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_unit(backend), "usagecount") == "4"


def test_unit_dumper_emits_segmentation_type_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_unit(backend), "segtype") == "sentence"


def test_unit_dumper_emits_source_language_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_unit(backend), "srclang") == "fr"


def test_unit_dumper_emits_variant_child(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(next(backend.iter_children(dump_unit(backend)))) == "tuv"


def test_unit_dumper_emits_variant_seg_child(backend: XmlBackend[object]) -> None:
  variant = next(backend.iter_children(dump_unit(backend)))

  assert backend.get_tag(next(backend.iter_children(variant))) == "seg"


def test_unit_dumper_emits_variant_segment_text(backend: XmlBackend[object]) -> None:
  variant = next(backend.iter_children(dump_unit(backend)))
  seg = next(backend.iter_children(variant))

  assert backend.get_text(seg) == "Hello"
