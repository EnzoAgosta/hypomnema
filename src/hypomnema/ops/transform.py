from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
import re

from hypomnema.domain.model import InlineContentItem, InlineNode, UnknownInlineNode
from hypomnema.domain.nodes import ContentNode, TranslationVariant
from hypomnema.ops import walk

type TagPredicate = Callable[[InlineNode], bool]


def _process_items(
  items: list[InlineContentItem],
  predicate: TagPredicate,
  on_match: Callable[[InlineNode], Iterable[InlineContentItem]],
) -> list[InlineContentItem]:
  result: list[InlineContentItem] = []
  stack: list[Iterator[InlineContentItem]] = [iter(items)]

  while stack:
    for item in stack[-1]:
      match item:
        case str() | UnknownInlineNode():
          result.append(item)
        case InlineNode():
          if predicate(item):
            replacement = list(on_match(item))
            if replacement:
              stack.append(iter(replacement))
              break
          else:
            result.append(item)
        case _:
          raise TypeError(f"Unexpected type {type(item)}")
    else:
      stack.pop()

  return result


def _as_predicate(
  predicate: type[InlineNode] | tuple[type[InlineNode], ...] | TagPredicate,
) -> TagPredicate:
  if isinstance(predicate, type) or isinstance(predicate, tuple):
    return lambda node: isinstance(node, predicate)
  return predicate


def remove[T: ContentNode](
  node: T,
  predicate: type[InlineNode] | tuple[type[InlineNode], ...] | TagPredicate,
  recurse: bool = False,
) -> T:
  resolved = _as_predicate(predicate)

  if isinstance(node, TranslationVariant):
    node.segment = _process_items(node.segment, resolved, on_match=lambda _: ())
  else:
    node.content = _process_items(node.content, resolved, on_match=lambda _: ())

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      child.content = _process_items(child.content, resolved, on_match=lambda _: ())

  return node


def unwrap[T: ContentNode](
  node: T,
  predicate: type[InlineNode] | tuple[type[InlineNode], ...] | TagPredicate,
  recurse: bool = False,
) -> T:
  resolved = _as_predicate(predicate)

  if isinstance(node, TranslationVariant):
    node.segment = _process_items(node.segment, resolved, on_match=lambda n: n.content)
  else:
    node.content = _process_items(node.content, resolved, on_match=lambda n: n.content)

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      child.content = _process_items(child.content, resolved, on_match=lambda n: n.content)

  return node


def _promoted_items(
  items: list[InlineContentItem],
  pattern: re.Pattern[str],
  factory: Callable[[re.Match[str]], InlineNode],
) -> list[InlineContentItem]:
  result: list[InlineContentItem] = []
  for item in items:
    if not isinstance(item, str):
      result.append(item)
      continue
    matches = list(pattern.finditer(item))
    if not matches:
      result.append(item)
      continue
    cursor = 0
    for match in matches:
      before = item[cursor : match.start()]
      if before:
        result.append(before)
      result.append(factory(match))
      cursor = match.end()
    tail = item[cursor:]
    if tail:
      result.append(tail)
  return result


def promote_match[T: ContentNode](
  node: T,
  pattern: re.Pattern[str],
  factory: Callable[[re.Match[str]], InlineNode],
  recurse: bool = False,
) -> T:
  if isinstance(node, TranslationVariant):
    node.segment = _promoted_items(node.segment, pattern, factory)
  else:
    node.content = _promoted_items(node.content, pattern, factory)

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      child.content = _promoted_items(child.content, pattern, factory)

  return node


def _replaced_items(
  items: list[InlineContentItem],
  pattern: re.Pattern[str],
  replacement: str | Callable[[re.Match[str]], str],
) -> list[InlineContentItem]:
  return [pattern.sub(replacement, item) if isinstance(item, str) else item for item in items]


def replace_text[T: ContentNode](
  node: T,
  pattern: re.Pattern[str],
  replacement: str | Callable[[re.Match[str]], str],
  recurse: bool = False,
) -> T:
  if isinstance(node, TranslationVariant):
    node.segment = _replaced_items(node.segment, pattern, replacement)
  else:
    node.content = _replaced_items(node.content, pattern, replacement)

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      child.content = _replaced_items(child.content, pattern, replacement)

  return node
