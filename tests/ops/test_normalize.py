from hypomnema.domain.nodes import (
  Hi,
  Note,
  Prop,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
)
from hypomnema.ops.normalize import (
  collapse_text,
  deduplicate_notes,
  deduplicate_props,
  remove_empty_text,
  strip_whitespace,
)


def test_collapse_text_returns_same_node() -> None:
  variant = TranslationVariant.create(language="en", segment=["a", "b"])

  assert collapse_text(variant) is variant


def test_collapse_text_merges_adjacent_top_level_strings() -> None:
  highlight = Hi.create(content=["nested", " text"])
  variant = TranslationVariant.create(language="en", segment=["a", "b", highlight, "c", "d"])

  collapse_text(variant)

  assert variant.segment == ["ab", highlight, "cd"]


def test_collapse_text_does_not_recurse_by_default() -> None:
  highlight = Hi.create(content=["nested", " text"])
  variant = TranslationVariant.create(language="en", segment=[highlight])

  collapse_text(variant)

  assert highlight.content == ["nested", " text"]


def test_collapse_text_recurses_when_requested() -> None:
  highlight = Hi.create(content=["nested", " text"])
  variant = TranslationVariant.create(language="en", segment=[highlight])

  collapse_text(variant, recurse=True)

  assert highlight.content == ["nested text"]


def test_remove_empty_text_returns_same_node() -> None:
  variant = TranslationVariant.create(language="en", segment=["", "value"])

  assert remove_empty_text(variant) is variant


def test_remove_empty_text_removes_empty_top_level_strings() -> None:
  highlight = Hi.create(content=["nested", "", " text"])
  variant = TranslationVariant.create(language="en", segment=["", "value", "", highlight, ""])

  remove_empty_text(variant)

  assert variant.segment == ["value", highlight]


def test_remove_empty_text_does_not_recurse_by_default() -> None:
  highlight = Hi.create(content=["nested", "", " text"])
  variant = TranslationVariant.create(language="en", segment=[highlight])

  remove_empty_text(variant)

  assert highlight.content == ["nested", "", " text"]


def test_strip_whitespace_leading_mode_strips_leading_whitespace() -> None:
  variant = TranslationVariant.create(language="en", segment=["  leading"])

  strip_whitespace(variant, mode="leading")

  assert variant.segment == ["leading"]


def test_strip_whitespace_trailing_mode_strips_trailing_whitespace() -> None:
  variant = TranslationVariant.create(language="en", segment=["trailing  "])

  strip_whitespace(variant, mode="trailing")

  assert variant.segment == ["trailing"]


def test_strip_whitespace_recurses_when_requested() -> None:
  highlight = Hi.create(content=["  nested", "value  "])
  variant = TranslationVariant.create(language="en", segment=[highlight])

  strip_whitespace(variant, mode="leading", recurse=True)
  strip_whitespace(variant, mode="trailing", recurse=True)

  assert highlight.content == ["nested", "value"]


def test_deduplicate_props_returns_same_node() -> None:
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
    props=[Prop.create(text="shared", kind="domain"), Prop.create(text="shared", kind="domain")],
  )

  assert deduplicate_props(header) is header


def test_deduplicate_props_removes_top_level_duplicates() -> None:
  duplicated_prop = Prop.create(text="shared", kind="domain")
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
    props=[duplicated_prop, duplicated_prop],
  )

  deduplicate_props(header)

  assert header.props == [duplicated_prop]


def test_deduplicate_props_recurses_when_requested() -> None:
  duplicated_prop = Prop.create(text="shared", kind="domain")
  variant = TranslationVariant.create(language="en", props=[duplicated_prop, duplicated_prop])
  unit = TranslationUnit.create(props=[duplicated_prop, duplicated_prop], variants=[variant])

  deduplicate_props(unit, recurse=True)

  assert unit.props == [duplicated_prop]
  assert variant.props == [duplicated_prop]


def test_deduplicate_notes_returns_same_node() -> None:
  unit = TranslationUnit.create(notes=[Note.create(text="shared"), Note.create(text="shared")])

  assert deduplicate_notes(unit) is unit


def test_deduplicate_notes_recurses_when_requested() -> None:
  duplicated_note = Note.create(text="shared")
  variant = TranslationVariant.create(language="en", notes=[duplicated_note, duplicated_note])
  unit = TranslationUnit.create(notes=[duplicated_note, duplicated_note], variants=[variant])

  deduplicate_notes(unit, recurse=True)

  assert unit.notes == [duplicated_note]
  assert variant.notes == [duplicated_note]
