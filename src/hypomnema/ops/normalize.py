from collections.abc import Generator
from typing import Literal

from hypomnema.domain.model import InlineContentItem, InlineNode
from hypomnema.domain.nodes import TranslationVariant
from hypomnema.ops import walk

type ContentNode = InlineNode | TranslationVariant


def _iter_inline_nodes(node: ContentNode) -> Generator[InlineNode, None, None]:
  stack = list(walk.walk_content(node, yield_text=False, recurse=False, yield_unknown=False))
  while stack:
    child = stack.pop()
    yield child
    stack.extend(walk.walk_content(child, yield_text=False, recurse=False, yield_unknown=False))


def _collapsed_items(items: list[InlineContentItem]) -> list[InlineContentItem]:
  result: list[InlineContentItem] = []
  for item in items:
    if isinstance(item, str) and result and isinstance(result[-1], str):
      result[-1] = result[-1] + item
    else:
      result.append(item)
  return result


def collapse_text[T: ContentNode](node: T, recurse: bool = False) -> T:
  if isinstance(node, TranslationVariant):
    node.segment = _collapsed_items(node.segment)
  else:
    node.content = _collapsed_items(node.content)

  if recurse:
    for child in _iter_inline_nodes(node):
      child.content = _collapsed_items(child.content)
  return node


def _without_empty_text(items: list[InlineContentItem]) -> list[InlineContentItem]:
  return [item for item in items if item != ""]


def remove_empty_text[T: ContentNode](node: T, recurse: bool = False) -> T:
  if isinstance(node, TranslationVariant):
    node.segment = _without_empty_text(node.segment)
  else:
    node.content = _without_empty_text(node.content)

  if recurse:
    for child in _iter_inline_nodes(node):
      child.content = _without_empty_text(child.content)
  return node


def _strip_items(
  items: list[InlineContentItem], mode: Literal["both", "leading", "trailing"]
) -> list[InlineContentItem]:
  first_idx = next((i for i, item in enumerate(items) if isinstance(item, str)), None)
  last_idx = next((i for i, item in enumerate(reversed(items)) if isinstance(item, str)), None)
  if last_idx is None or first_idx is None:
    return items

  # because we're iterating in reverse, we need to adjust the index
  last_idx = len(items) - last_idx - 1

  result = list(items)

  # need the type ignore because mypy can't understand that we know for sure the
  # values at those indices are strings
  if mode in ("both", "leading"):
    result[first_idx] = result[first_idx].lstrip()  # type: ignore[union-attr]
  if mode in ("both", "trailing"):
    result[last_idx] = result[last_idx].rstrip()  # type: ignore[union-attr]

  return result


def strip_whitespace[T: ContentNode](
  node: T, mode: Literal["both", "leading", "trailing"] = "both", recurse: bool = False
) -> T:
  if isinstance(node, TranslationVariant):
    node.segment = _strip_items(node.segment, mode)
  else:
    node.content = _strip_items(node.content, mode)

  if recurse:
    for child in _iter_inline_nodes(node):
      child.content = _strip_items(child.content, mode)

  return node
