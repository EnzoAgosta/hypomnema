import re

from hypomnema.domain.nodes import Hi, Ph, Sub, TranslationVariant, UnknownInlineNode
from hypomnema.ops.transform import promote_match, remove, replace_text, unwrap


def test_remove_returns_same_node() -> None:
  variant = TranslationVariant.create(language="en", segment=["lead"])

  assert remove(variant, Ph) is variant


def test_remove_deletes_matching_top_level_nodes() -> None:
  nested_placeholder = Ph.create(content=["nested"])
  nested = Hi.create(content=["inner", nested_placeholder, "tail"])
  top_placeholder = Ph.create(content=["top"])
  variant = TranslationVariant.create(
    language="en", segment=["lead", top_placeholder, nested, "after"]
  )

  remove(variant, Ph)

  assert variant.segment == ["lead", nested, "after"]


def test_remove_does_not_recurse_by_default() -> None:
  nested_placeholder = Ph.create(content=["nested"])
  nested = Hi.create(content=["inner", nested_placeholder, "tail"])
  variant = TranslationVariant.create(language="en", segment=[nested])

  remove(variant, Ph)

  assert nested.content == ["inner", nested_placeholder, "tail"]


def test_remove_recurses_when_requested() -> None:
  nested_placeholder = Ph.create(content=["nested"])
  nested = Hi.create(content=["inner", nested_placeholder, "tail"])
  variant = TranslationVariant.create(language="en", segment=[nested])

  remove(variant, Ph, recurse=True)

  assert nested.content == ["inner", "tail"]


def test_unwrap_returns_same_node() -> None:
  variant = TranslationVariant.create(language="en", segment=["lead"])

  assert unwrap(variant, Hi) is variant


def test_unwrap_promotes_child_content() -> None:
  nested = Hi.create(content=["inner"])
  variant = TranslationVariant.create(language="en", segment=["lead", nested, "after"])

  unwrap(variant, Hi)

  assert variant.segment == ["lead", "inner", "after"]


def test_promote_match_returns_same_node() -> None:
  variant = TranslationVariant.create(language="en", segment=["a-1-b"])

  assert (
    promote_match(
      variant,
      re.compile(r"\d+"),
      lambda match: UnknownInlineNode(payload=match.group(0).encode("ascii")),
    )
    is variant
  )


def test_promote_match_splits_top_level_strings() -> None:
  variant = TranslationVariant.create(language="en", segment=["a-1-b"])

  promote_match(
    variant,
    re.compile(r"\d+"),
    lambda match: UnknownInlineNode(payload=match.group(0).encode("ascii")),
  )

  assert variant.segment[0] == "a-"
  assert isinstance(variant.segment[1], UnknownInlineNode)
  assert variant.segment[2] == "-b"


def test_promote_match_recurses_when_requested() -> None:
  nested = Hi.create(content=["x-2-y"])
  variant = TranslationVariant.create(language="en", segment=[nested])

  promote_match(
    variant,
    re.compile(r"\d+"),
    lambda match: UnknownInlineNode(payload=match.group(0).encode("ascii")),
    recurse=True,
  )

  assert nested.content[0] == "x-"
  assert isinstance(nested.content[1], UnknownInlineNode)
  assert nested.content[2] == "-y"


def test_replace_text_returns_same_node() -> None:
  variant = TranslationVariant.create(language="en", segment=["outer 123"])

  assert replace_text(variant, re.compile(r"123"), "456") is variant


def test_replace_text_replaces_top_level_strings() -> None:
  variant = TranslationVariant.create(language="en", segment=["outer 123"])

  replace_text(variant, re.compile(r"123"), "456")

  assert variant.segment == ["outer 456"]


def test_replace_text_recurses_when_requested() -> None:
  nested = Hi.create(content=["inner 123"])
  variant = TranslationVariant.create(language="en", segment=[nested])

  replace_text(variant, re.compile(r"123"), "456", recurse=True)

  assert nested.content == ["inner 456"]


def test_unwrap_supports_sub_nodes() -> None:
  child = Hi.create(content=["inner"])
  node = Sub.create(content=["lead", child, "after"])

  unwrap(node, Hi)

  assert node.content == ["lead", "inner", "after"]


def test_replace_text_supports_sub_nodes() -> None:
  node = Sub.create(content=["lead", "inner", "after"])

  replace_text(node, re.compile("inner"), "middle")

  assert node.content == ["lead", "middle", "after"]
