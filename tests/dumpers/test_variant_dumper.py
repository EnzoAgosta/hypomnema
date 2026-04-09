from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import Note, Ph, Prop, TranslationVariant
from hypomnema.dumpers.xml import TranslationVariantDumper


def dump_variant(backend: XmlBackend[object]) -> object:
  node = TranslationVariant.create(
    language="en",
    original_encoding="utf-8",
    original_data_type="html",
    usage_count=3,
    creation_tool="tool",
    creation_tool_version="1.0",
    created_by="creator",
    last_modified_by="modifier",
    original_tm_format="legacy",
    notes=[Note.create(text="note")],
    props=[Prop.create(text="finance", kind="domain")],
    segment=["lead", Ph.create(content=["ph"], kind="fmt"), "tail"],
  )
  return TranslationVariantDumper(backend).dump(node)


def test_variant_dumper_emits_tuv_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(dump_variant(backend)) == "tuv"


def test_variant_dumper_emits_language_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "xml:lang") == "en"


def test_variant_dumper_emits_original_encoding_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "o-encoding") == "utf-8"


def test_variant_dumper_emits_original_data_type_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "datatype") == "html"


def test_variant_dumper_emits_usage_count_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "usagecount") == "3"


def test_variant_dumper_emits_creation_tool_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "creationtool") == "tool"


def test_variant_dumper_emits_creation_tool_version_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "creationtoolversion") == "1.0"


def test_variant_dumper_emits_created_by_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "creationid") == "creator"


def test_variant_dumper_emits_last_modified_by_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "changeid") == "modifier"


def test_variant_dumper_emits_original_tm_format_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_variant(backend), "o-tmf") == "legacy"


def test_variant_dumper_emits_seg_as_first_child(backend: XmlBackend[object]) -> None:
  assert [backend.get_tag(child) for child in backend.iter_children(dump_variant(backend))][
    0
  ] == "seg"


def test_variant_dumper_emits_note_after_seg(backend: XmlBackend[object]) -> None:
  assert [backend.get_tag(child) for child in backend.iter_children(dump_variant(backend))][
    1
  ] == "note"


def test_variant_dumper_emits_prop_after_note(backend: XmlBackend[object]) -> None:
  assert [backend.get_tag(child) for child in backend.iter_children(dump_variant(backend))][
    2
  ] == "prop"


def test_variant_dumper_emits_seg_leading_text(backend: XmlBackend[object]) -> None:
  seg = next(backend.iter_children(dump_variant(backend)))

  assert backend.get_text(seg) == "lead"


def test_variant_dumper_emits_seg_placeholder_tag(backend: XmlBackend[object]) -> None:
  seg = next(backend.iter_children(dump_variant(backend)))

  assert backend.get_tag(next(backend.iter_children(seg))) == "ph"


def test_variant_dumper_emits_seg_placeholder_text(backend: XmlBackend[object]) -> None:
  seg = next(backend.iter_children(dump_variant(backend)))
  placeholder = next(backend.iter_children(seg))

  assert backend.get_text(placeholder) == "ph"


def test_variant_dumper_emits_text_after_placeholder(backend: XmlBackend[object]) -> None:
  seg = next(backend.iter_children(dump_variant(backend)))
  placeholder = next(backend.iter_children(seg))

  assert backend.get_tail(placeholder) == "tail"
