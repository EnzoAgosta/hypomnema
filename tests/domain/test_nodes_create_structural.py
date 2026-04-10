from datetime import UTC, datetime

import pytest

from hypomnema.domain.attributes import Segtype
from hypomnema.domain.nodes import (
  Note,
  Prop,
  TranslationMemory,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
  UnknownNode,
)


def _make_header() -> TranslationMemoryHeader:
  return TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en-US",
    source_language="fr-FR",
    original_data_type="plaintext",
    original_encoding="utf-8",
    created_at="2024-01-02T03:04:05",
    created_by="creator",
    last_modified_at="2024-02-03T04:05:06",
    last_modified_by="modifier",
    notes=[Note.create(text="header note")],
    props=[Prop.create(text="header prop", kind="domain")],
    extra_attributes={"custom": "value"},
    extra_nodes=[UnknownNode(payload=b"<custom />")],
  )


def _make_variant() -> TranslationVariant:
  return TranslationVariant.create(
    language="de-DE",
    original_encoding="utf-8",
    original_data_type="html",
    usage_count="12",
    last_used_at="2024-03-04T05:06:07",
    creation_tool="tool",
    creation_tool_version="2.0",
    created_at="2024-03-01T01:02:03",
    created_by="creator",
    last_modified_at="2024-03-05T06:07:08",
    last_modified_by="modifier",
    original_tm_format="legacy",
    notes=[Note.create(text="variant note")],
    props=[Prop.create(text="variant prop", kind="context")],
    segment=["before", "after"],
    extra_attributes={"custom": "value"},
    extra_nodes=[UnknownNode(payload=b"<custom />")],
  )


def _make_unit() -> TranslationUnit:
  return TranslationUnit.create(
    translation_unit_id="unit-1",
    original_encoding="utf-8",
    original_data_type="xml",
    usage_count="3",
    last_used_at="2024-04-05T06:07:08",
    created_at="2024-04-01T01:02:03",
    last_modified_at="2024-04-06T07:08:09",
    segmentation_type="paragraph",
    source_language="en-GB",
    notes=[Note.create(text="unit note")],
    props=[Prop.create(text="unit prop", kind="domain")],
    variants=[TranslationVariant.create(language="en", segment=["segment"])],
  )


def test_translation_memory_header_create_sets_segmentation_type() -> None:
  assert _make_header().spec_attributes.segmentation_type is Segtype.SENTENCE


def test_translation_memory_header_create_sets_admin_language() -> None:
  assert _make_header().spec_attributes.admin_language == "en-US"


def test_translation_memory_header_create_sets_source_language() -> None:
  assert _make_header().spec_attributes.source_language == "fr-FR"


def test_translation_memory_header_create_sets_original_encoding() -> None:
  assert _make_header().spec_attributes.original_encoding == "utf-8"


def test_translation_memory_header_create_parses_created_at() -> None:
  assert _make_header().spec_attributes.created_at == datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_translation_memory_header_create_parses_last_modified_at() -> None:
  assert _make_header().spec_attributes.last_modified_at == datetime(
    2024, 2, 3, 4, 5, 6, tzinfo=UTC
  )


def test_translation_memory_header_create_copies_notes() -> None:
  notes = [Note.create(text="header note")]

  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en-US",
    source_language="fr-FR",
    original_data_type="plaintext",
    notes=notes,
  )

  assert header.notes == notes
  assert header.notes is not notes


def test_translation_memory_header_create_copies_props() -> None:
  props = [Prop.create(text="header prop", kind="domain")]

  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en-US",
    source_language="fr-FR",
    original_data_type="plaintext",
    props=props,
  )

  assert header.props == props
  assert header.props is not props


def test_translation_memory_header_create_copies_extra_attributes() -> None:
  extra_attributes = {"custom": "value"}

  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en-US",
    source_language="fr-FR",
    original_data_type="plaintext",
    extra_attributes=extra_attributes,
  )

  assert header.extra_attributes == extra_attributes
  assert header.extra_attributes is not extra_attributes


def test_translation_memory_header_create_copies_extra_nodes() -> None:
  extra_nodes = [UnknownNode(payload=b"<custom />")]

  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en-US",
    source_language="fr-FR",
    original_data_type="plaintext",
    extra_nodes=extra_nodes,
  )

  assert header.extra_nodes == extra_nodes
  assert header.extra_nodes is not extra_nodes


def test_translation_memory_header_create_rejects_invalid_datetime() -> None:
  with pytest.raises(ValueError):
    TranslationMemoryHeader.create(
      creation_tool="hypomnema",
      creation_tool_version="1.0",
      segmentation_type="sentence",
      original_translation_memory_format="tmx",
      admin_language="en",
      source_language="fr",
      original_data_type="plaintext",
      created_at="not-an-iso-datetime",
    )


def test_translation_variant_create_sets_language() -> None:
  assert _make_variant().spec_attributes.language == "de-DE"


def test_translation_variant_create_sets_original_encoding() -> None:
  assert _make_variant().spec_attributes.original_encoding == "utf-8"


def test_translation_variant_create_sets_original_data_type() -> None:
  assert _make_variant().spec_attributes.original_data_type == "html"


def test_translation_variant_create_coerces_usage_count() -> None:
  assert _make_variant().spec_attributes.usage_count == 12


def test_translation_variant_create_parses_last_used_at() -> None:
  assert _make_variant().spec_attributes.last_used_at == datetime(2024, 3, 4, 5, 6, 7, tzinfo=UTC)


def test_translation_variant_create_parses_created_at() -> None:
  assert _make_variant().spec_attributes.created_at == datetime(2024, 3, 1, 1, 2, 3, tzinfo=UTC)


def test_translation_variant_create_parses_last_modified_at() -> None:
  assert _make_variant().spec_attributes.last_modified_at == datetime(
    2024, 3, 5, 6, 7, 8, tzinfo=UTC
  )


def test_translation_variant_create_copies_notes() -> None:
  notes = [Note.create(text="variant note")]

  variant = TranslationVariant.create(language="de-DE", notes=notes)

  assert variant.notes == notes
  assert variant.notes is not notes


def test_translation_variant_create_copies_props() -> None:
  props = [Prop.create(text="variant prop", kind="context")]

  variant = TranslationVariant.create(language="de-DE", props=props)

  assert variant.props == props
  assert variant.props is not props


def test_translation_variant_create_copies_segment() -> None:
  segment = ["before", "after"]

  variant = TranslationVariant.create(language="de-DE", segment=segment)

  assert variant.segment == segment
  assert variant.segment is not segment


def test_translation_variant_create_copies_extra_attributes() -> None:
  extra_attributes = {"custom": "value"}

  variant = TranslationVariant.create(language="de-DE", extra_attributes=extra_attributes)

  assert variant.extra_attributes == extra_attributes
  assert variant.extra_attributes is not extra_attributes


def test_translation_variant_create_copies_extra_nodes() -> None:
  extra_nodes = [UnknownNode(payload=b"<custom />")]

  variant = TranslationVariant.create(language="de-DE", extra_nodes=extra_nodes)

  assert variant.extra_nodes == extra_nodes
  assert variant.extra_nodes is not extra_nodes


def test_translation_unit_create_sets_translation_unit_id() -> None:
  assert _make_unit().spec_attributes.translation_unit_id == "unit-1"


def test_translation_unit_create_sets_original_encoding() -> None:
  assert _make_unit().spec_attributes.original_encoding == "utf-8"


def test_translation_unit_create_coerces_usage_count() -> None:
  assert _make_unit().spec_attributes.usage_count == 3


def test_translation_unit_create_parses_last_used_at() -> None:
  assert _make_unit().spec_attributes.last_used_at == datetime(2024, 4, 5, 6, 7, 8, tzinfo=UTC)


def test_translation_unit_create_parses_created_at() -> None:
  assert _make_unit().spec_attributes.created_at == datetime(2024, 4, 1, 1, 2, 3, tzinfo=UTC)


def test_translation_unit_create_parses_last_modified_at() -> None:
  assert _make_unit().spec_attributes.last_modified_at == datetime(2024, 4, 6, 7, 8, 9, tzinfo=UTC)


def test_translation_unit_create_sets_segmentation_type() -> None:
  assert _make_unit().spec_attributes.segmentation_type is Segtype.PARAGRAPH


def test_translation_unit_create_sets_source_language() -> None:
  assert _make_unit().spec_attributes.source_language == "en-GB"


def test_translation_unit_create_copies_notes() -> None:
  notes = [Note.create(text="unit note")]

  unit = TranslationUnit.create(notes=notes)

  assert unit.notes == notes
  assert unit.notes is not notes


def test_translation_unit_create_copies_props() -> None:
  props = [Prop.create(text="unit prop", kind="domain")]

  unit = TranslationUnit.create(props=props)

  assert unit.props == props
  assert unit.props is not props


def test_translation_unit_create_copies_variants() -> None:
  variants = [TranslationVariant.create(language="en", segment=["segment"])]

  unit = TranslationUnit.create(variants=variants)

  assert unit.variants == variants
  assert unit.variants is not variants


def test_translation_memory_create_preserves_header_reference() -> None:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )

  assert TranslationMemory.create(header=header).header is header


def test_translation_memory_create_sets_version() -> None:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )

  assert TranslationMemory.create(header=header, version="1.5").spec_attributes.version == "1.5"


def test_translation_memory_create_copies_units() -> None:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )
  units = [TranslationUnit.create(translation_unit_id="tu-1")]

  memory = TranslationMemory.create(header=header, units=units)

  assert memory.units == units
  assert memory.units is not units


def test_translation_memory_create_copies_extra_attributes() -> None:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )
  extra_attributes = {"custom": "value"}

  memory = TranslationMemory.create(header=header, extra_attributes=extra_attributes)

  assert memory.extra_attributes == extra_attributes
  assert memory.extra_attributes is not extra_attributes


def test_translation_memory_create_copies_extra_nodes() -> None:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )
  extra_nodes = [UnknownNode(payload=b"<custom />")]

  memory = TranslationMemory.create(header=header, extra_nodes=extra_nodes)

  assert memory.extra_nodes == extra_nodes
  assert memory.extra_nodes is not extra_nodes
