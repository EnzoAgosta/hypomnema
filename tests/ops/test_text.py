import re

from hypomnema.domain.nodes import Hi, Ph, Sub, UnknownInlineNode
from hypomnema.ops.text import (
  find,
  find_all,
  find_iter,
  is_empty,
  iter_fragments,
  iter_fragments_with_source,
  join,
)


def _make_node() -> tuple[Ph, Hi, UnknownInlineNode]:
  unknown = UnknownInlineNode(payload=b"<opaque />")
  nested = Hi.create(content=["inner", unknown, "tail"])
  return Ph.create(content=["lead", nested, "after"]), nested, unknown


def test_iter_fragments_with_source_yields_top_level_text_without_recursion() -> None:
  node, _, _ = _make_node()

  assert list(iter_fragments_with_source(node)) == [("lead", node), ("after", node)]


def test_iter_fragments_with_source_recurses_into_nested_content() -> None:
  node, nested, _ = _make_node()

  assert list(iter_fragments_with_source(node, recurse=True)) == [
    ("lead", node),
    ("inner", nested),
    ("tail", nested),
    ("after", node),
  ]


def test_iter_fragments_with_source_formats_unknown_nodes_when_requested() -> None:
  node, _, unknown = _make_node()

  assert ("unknown:10", unknown) in list(
    iter_fragments_with_source(
      node, recurse=True, unknown_formatter=lambda item: f"unknown:{len(item.payload)}"
    )
  )


def test_iter_fragments_yields_fragment_text() -> None:
  node, _, _ = _make_node()

  assert list(iter_fragments(node, recurse=True, unknown_formatter=lambda _: "?")) == [
    "lead",
    "inner",
    "?",
    "tail",
    "after",
  ]


def test_join_joins_fragments() -> None:
  node, _, _ = _make_node()

  assert (
    join(node, separator="|", recurse=True, unknown_formatter=lambda _: "?")
    == "lead|inner|?|tail|after"
  )


def test_find_returns_first_matching_fragment_for_string_pattern() -> None:
  node, _, _ = _make_node()

  assert find(node, "inn", recurse=True) == "inner"


def test_find_returns_first_matching_fragment_for_regex_pattern() -> None:
  node, _, _ = _make_node()

  assert find(node, re.compile("after$"), recurse=True) == "after"


def test_find_iter_yields_all_matching_fragments() -> None:
  node, _, _ = _make_node()

  assert list(find_iter(node, "a", recurse=True, unknown_formatter=lambda _: "?")) == [
    "lead",
    "tail",
    "after",
  ]


def test_find_all_returns_matching_fragments_as_list() -> None:
  node, _, _ = _make_node()

  assert find_all(node, re.compile("[?n]"), recurse=True, unknown_formatter=lambda _: "?") == [
    "inner",
    "?",
  ]


def test_is_empty_returns_false_when_fragments_exist() -> None:
  node, _, _ = _make_node()

  assert not is_empty(node, recurse=True)


def test_is_empty_returns_true_when_no_fragments_exist() -> None:
  empty = Sub.create(content=[UnknownInlineNode(payload=b"<opaque />")])

  assert is_empty(empty, recurse=True)
