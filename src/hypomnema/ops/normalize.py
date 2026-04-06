from typing import Any, Iterable, Literal

from hypomnema.domain.nodes import (
  Bpt,
  ContentNode,
  Ept,
  Hi,
  It,
  Ph,
  Sub,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
)
from hypomnema.ops import walk


def _with_collapsed_text[T](items: Iterable[T]) -> list[T]:
  result: list[T] = []
  for item in items:
    if isinstance(item, str) and result and isinstance(result[-1], str):
      # TODO: mypy limitation, can't infer that both item and result[-1] are str
      result[-1] += item  # type: ignore[assignment]
      continue
    result.append(item)
  return result


def collapse_text[T: ContentNode](node: T, recurse: bool = False) -> T:
  match node:
    case TranslationVariant():
      node.segment = _with_collapsed_text(node.segment)
    case Hi() | Sub():
      node.content = _with_collapsed_text(node.content)
    case Bpt() | Ept() | It() | Ph():
      node.content = _with_collapsed_text(node.content)
    case _:
      raise TypeError(f"Unexpected type {type(node)}")

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      collapse_text(child, recurse=True)
  return node


def _without_empty_text[T](items: list[T]) -> list[T]:
  return [item for item in items if item != ""]


def remove_empty_text[T: ContentNode](node: T, recurse: bool = False) -> T:
  match node:
    case TranslationVariant():
      node.segment = _without_empty_text(node.segment)
    case Hi() | Sub():
      node.content = _without_empty_text(node.content)
    case Bpt() | Ept() | It() | Ph():
      node.content = _without_empty_text(node.content)
    case _:
      raise TypeError(f"Unexpected type {type(node)}")
  return node


def _with_stripped_whitespace[T: Any](
  items: list[T], mode: Literal["both", "leading", "trailing"]
) -> list[T]:
  first_idx = next((i for i, item in enumerate(items) if isinstance(item, str)), None)
  last_idx = next((i for i, item in enumerate(reversed(items)) if isinstance(item, str)), None)
  if last_idx is None or first_idx is None:
    return items

  # because we're iterating in reverse, we need to adjust the index
  last_idx = len(items) - last_idx - 1

  result = list(items)

  if mode in ("both", "leading"):
    result[first_idx] = result[first_idx].lstrip()
  if mode in ("both", "trailing"):
    result[last_idx] = result[last_idx].rstrip()

  return result


def strip_whitespace[T: ContentNode](
  node: T, mode: Literal["both", "leading", "trailing"] = "both", recurse: bool = False
) -> T:
  match node:
    case TranslationVariant():
      node.segment = _with_stripped_whitespace(node.segment, mode)
    case Hi() | Sub():
      node.content = _with_stripped_whitespace(node.content, mode)
    case Bpt() | Ept() | It() | Ph():
      node.content = _with_stripped_whitespace(node.content, mode)
    case _:
      raise TypeError(f"Unexpected type {type(node)}")

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      strip_whitespace(child, mode, recurse=True)

  return node


def _deduplicated[T](items: list[T]) -> list[T]:
  seen: list[T] = []
  for item in items:
    if item not in seen:
      seen.append(item)
  return seen


def deduplicate_props[T: TranslationVariant | TranslationMemoryHeader | TranslationUnit](
  node: T, recurse: bool = False
) -> T:
  node.props = _deduplicated(node.props)
  if not recurse:
    return node
  for child in walk.walk_filtered(node, lambda n: hasattr(n, "props")):
    assert hasattr(child, "props")  # for mypy
    child.props = _deduplicated(child.props)
  return node


def deduplicate_notes[T: TranslationVariant | TranslationMemoryHeader | TranslationUnit](
  node: T, recurse: bool = False
) -> T:
  node.notes = _deduplicated(node.notes)
  if not recurse:
    return node
  for child in walk.walk_filtered(node, lambda n: hasattr(n, "notes")):
    assert hasattr(child, "notes")  # for mypy
    child.notes = _deduplicated(child.notes)
  return node
