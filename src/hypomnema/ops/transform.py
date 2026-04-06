from __future__ import annotations

from ast import Sub
from collections.abc import Callable, Iterable, Iterator
import re
from typing import Any, cast

from hypomnema.domain.nodes import (
  Bpt,
  ContentNode,
  Ept,
  Hi,
  InlineContentItem,
  InlineNode,
  It,
  Ph,
  TranslationVariant,
  UnknownInlineNode,
)
from hypomnema.ops import walk

type TagPredicate = Callable[[InlineNode], bool]


def _with_processed_items[T: InlineContentItem](
  items: Iterable[T], predicate: TagPredicate, on_match: Callable[[InlineNode], Iterable[Any]]
) -> list[T]:
  result: list[T] = []
  stack: list[Iterator[T]] = [iter(items)]

  while stack:
    for item in stack[-1]:
      match item:
        case str() | UnknownInlineNode():
          result.append(item)
        case Bpt() | Ept() | It() | Ph() | Hi() | Sub():
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


def _as_predicate[T: InlineNode](
  predicate: type[T] | tuple[type[T], ...] | TagPredicate,
) -> TagPredicate:
  if isinstance(predicate, type) or isinstance(predicate, tuple):
    return lambda node: isinstance(node, predicate)
  return predicate


def remove[T: InlineNode](
  node: T,
  predicate: type[InlineNode] | tuple[type[InlineNode], ...] | TagPredicate,
  recurse: bool = False,
) -> T:
  resolved = _as_predicate(predicate)

  match node:
    case TranslationVariant():
      node.segment = _with_processed_items(node.segment, resolved, on_match=lambda _: ())
    case Hi() | Sub():
      node.content = _with_processed_items(node.content, resolved, on_match=lambda _: ())
    case Bpt() | Ept() | It() | Ph():
      node.content = _with_processed_items(node.content, resolved, on_match=lambda _: ())
    case _:
      raise TypeError(f"Unexpected type {type(node)}")

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      remove(child, predicate, recurse=True)

  return node


def unwrap[T: InlineNode](
  node: T,
  predicate: type[InlineNode] | tuple[type[InlineNode], ...] | TagPredicate,
  recurse: bool = False,
) -> T:
  resolved = _as_predicate(predicate)

  match node:
    case TranslationVariant():
      node.segment = _with_processed_items(node.segment, resolved, on_match=lambda n: n.content)
    case Hi() | Sub():
      node.content = _with_processed_items(node.content, resolved, on_match=lambda n: n.content)
    case Bpt() | Ept() | It() | Ph():
      node.content = _with_processed_items(node.content, resolved, on_match=lambda n: n.content)
    case _:
      raise TypeError(f"Unexpected type {type(node)}")

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      unwrap(child, predicate, recurse=True)

  return node


def _with_promoted_items[T: InlineContentItem](
  items: Iterable[T], pattern: re.Pattern[str], factory: Callable[[re.Match[str]], Any]
) -> list[T]:
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
  # TODO: figure out better typing to avoid the cast
  return cast(list[T], result)


def promote_match[T: ContentNode](
  node: T, pattern: re.Pattern[str], factory: Callable[[re.Match[str]], Any], recurse: bool = False
) -> T:
  match node:
    case TranslationVariant():
      node.segment = _with_promoted_items(node.segment, pattern, factory)
    case Hi() | Sub():
      node.content = _with_promoted_items(node.content, pattern, factory)
    case Bpt() | Ept() | It() | Ph():
      node.content = _with_promoted_items(node.content, pattern, factory)
    case _:
      raise TypeError(f"Unexpected type {type(node)}")

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      promote_match(child, pattern, factory, recurse=True)

  return node


def _with_replaced_items[T: InlineContentItem](
  items: Iterable[T], pattern: re.Pattern[str], replacement: str | Callable[[re.Match[str]], str]
) -> list[T]:
  result: list[InlineContentItem] = []
  for item in items:
    if isinstance(item, str):
      result.append(pattern.sub(replacement, item))
    else:
      result.append(item)
  # TODO: figure out better typing to avoid the cast
  return cast(list[T], result)


def replace_text[T: ContentNode](
  node: T,
  pattern: re.Pattern[str],
  replacement: str | Callable[[re.Match[str]], str],
  recurse: bool = False,
) -> T:
  match node:
    case TranslationVariant():
      node.segment = _with_replaced_items(node.segment, pattern, replacement)
    case Hi() | Sub():
      node.content = _with_replaced_items(node.content, pattern, replacement)
    case Bpt() | Ept() | It() | Ph():
      node.content = _with_replaced_items(node.content, pattern, replacement)
    case _:
      raise TypeError(f"Unexpected type {type(node)}")

  if recurse:
    for child in walk.walk_inline_nodes(node, recurse=True):
      replace_text(child, pattern, replacement, recurse=True)

  return node
