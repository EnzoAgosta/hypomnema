from hypomnema.domain.nodes import (
  Hi,
  Note,
  Ph,
  Prop,
  TranslationMemory,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
  UnknownInlineNode,
)
from hypomnema.ops.walk import (
  walk,
  walk_content,
  walk_content_filtered,
  walk_filtered,
  walk_inline_nodes,
)


def _make_nested_variant() -> tuple[TranslationVariant, Hi, Ph, UnknownInlineNode]:
  unknown = UnknownInlineNode(payload=b"<unknown />")
  placeholder = Ph.create(content=["placeholder"])
  highlight = Hi.create(content=["inner", placeholder, "tail"])
  variant = TranslationVariant.create(
    language="en", segment=["leading", highlight, "trailing", unknown]
  )
  return variant, highlight, placeholder, unknown


def _make_memory() -> tuple[
  TranslationMemory, TranslationMemoryHeader, TranslationUnit, TranslationVariant, Note
]:
  note = Note.create(text="matching note")
  variant = TranslationVariant.create(language="en", notes=[note])
  unit = TranslationUnit.create(variants=[variant])
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
  )
  return TranslationMemory.create(header=header, units=[unit]), header, unit, variant, note


def test_walk_content_non_recursive_yields_leading_text() -> None:
  variant, _, _, _ = _make_nested_variant()

  assert list(walk_content(variant, yield_unknown=True))[0] == "leading"


def test_walk_content_non_recursive_yields_inline_node() -> None:
  variant, highlight, _, _ = _make_nested_variant()

  assert list(walk_content(variant, yield_unknown=True))[1] is highlight


def test_walk_content_non_recursive_yields_trailing_text() -> None:
  variant, _, _, _ = _make_nested_variant()

  assert list(walk_content(variant, yield_unknown=True))[2] == "trailing"


def test_walk_content_non_recursive_yields_unknown_item_when_requested() -> None:
  variant, _, _, unknown = _make_nested_variant()

  assert list(walk_content(variant, yield_unknown=True))[3] is unknown


def test_walk_content_recursive_keeps_depth_first_order() -> None:
  variant, highlight, placeholder, unknown = _make_nested_variant()

  assert list(walk_content(variant, recurse=True, yield_unknown=True)) == [
    "leading",
    highlight,
    "inner",
    placeholder,
    "placeholder",
    "tail",
    "trailing",
    unknown,
  ]


def test_walk_content_can_exclude_text_items() -> None:
  variant, highlight, placeholder, _ = _make_nested_variant()

  assert list(walk_content(variant, yield_text=False, recurse=True)) == [highlight, placeholder]


def test_walk_inline_nodes_returns_recursive_inline_nodes() -> None:
  variant, highlight, placeholder, _ = _make_nested_variant()

  assert list(walk_inline_nodes(variant, recurse=True)) == [highlight, placeholder]


def test_walk_content_filtered_applies_predicate() -> None:
  variant, _, placeholder, unknown = _make_nested_variant()

  assert list(
    walk_content_filtered(
      variant, lambda item: item == "tail" or item is placeholder or item is unknown, recurse=True
    )
  ) == [placeholder, "tail", unknown]


def test_walk_without_recursion_yields_header_before_unit() -> None:
  header_note = Note.create(text="header note")
  header_prop = Prop.create(text="header prop", kind="domain")
  variant_note = Note.create(text="variant note")
  variant_prop = Prop.create(text="variant prop", kind="domain")
  variant = TranslationVariant.create(language="en", notes=[variant_note], props=[variant_prop])
  unit_note = Note.create(text="unit note")
  unit_prop = Prop.create(text="unit prop", kind="domain")
  unit = TranslationUnit.create(notes=[unit_note], props=[unit_prop], variants=[variant])
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
    notes=[header_note],
    props=[header_prop],
  )
  memory = TranslationMemory.create(header=header, units=[unit])

  assert list(walk(memory, recurse=False)) == [header, unit]


def test_walk_with_recursion_descends_into_children() -> None:
  header_note = Note.create(text="header note")
  header_prop = Prop.create(text="header prop", kind="domain")
  variant_note = Note.create(text="variant note")
  variant_prop = Prop.create(text="variant prop", kind="domain")
  variant = TranslationVariant.create(language="en", notes=[variant_note], props=[variant_prop])
  unit_note = Note.create(text="unit note")
  unit_prop = Prop.create(text="unit prop", kind="domain")
  unit = TranslationUnit.create(notes=[unit_note], props=[unit_prop], variants=[variant])
  header = TranslationMemoryHeader.create(
    creation_tool="hypomnema",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="tmx",
    admin_language="en",
    source_language="fr",
    original_data_type="plaintext",
    notes=[header_note],
    props=[header_prop],
  )
  memory = TranslationMemory.create(header=header, units=[unit])

  assert list(walk(memory, recurse=True)) == [
    header,
    header_note,
    header_prop,
    unit,
    unit_note,
    unit_prop,
    variant,
    variant_note,
    variant_prop,
  ]


def test_walk_filtered_returns_only_matching_nodes() -> None:
  memory, _, _, _, note = _make_memory()

  assert list(walk_filtered(memory, lambda child: isinstance(child, Note), recurse=True)) == [note]
