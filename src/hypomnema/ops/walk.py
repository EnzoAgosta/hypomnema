from collections.abc import Callable, Generator, Iterator
from typing import Any, Literal, TypeIs, overload

from hypomnema.domain.model import InlineContentItem, InlineNode, StructuralNode, UnknownInlineNode
from hypomnema.domain.nodes import (
  ContentNode,
  TranslationMemoryHeader,
  Note,
  Prop,
  TranslationMemory,
  TranslationUnit,
  TranslationVariant,
)


type StructuralPredicate = Callable[[StructuralNode], bool]
type ContentPredicate = Callable[[InlineContentItem], bool]


def _iter_items_flat(
  items: list[InlineContentItem], yield_text: bool, yield_unknown: bool
) -> Generator[InlineContentItem, None, None]:
  for item in items:
    match item:
      case str():
        if yield_text:
          yield item
      case InlineNode():
        yield item
      case UnknownInlineNode():
        if yield_unknown:
          yield item
      case _:
        raise TypeError(f"Unexpected type {type(item)}")


@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[False],
  recurse: bool = False,
  yield_unknown: Literal[False] = False,
) -> Generator[InlineNode, None, None]: ...
@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[True] = True,
  recurse: bool = False,
  yield_unknown: Literal[False] = False,
) -> Generator[str | InlineNode, None, None]: ...
@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[False],
  recurse: bool = False,
  yield_unknown: Literal[True] = True,
) -> Generator[InlineNode | UnknownInlineNode, None, None]: ...
@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[True] = True,
  recurse: bool = False,
  yield_unknown: Literal[True] = True,
) -> Generator[InlineContentItem, None, None]: ...
def walk_content(
  node: ContentNode, yield_text: bool = True, recurse: bool = False, yield_unknown: bool = False
) -> Generator[InlineContentItem, None, None]:
  initial = node.segment if isinstance(node, TranslationVariant) else node.content

  if not recurse:
    yield from _iter_items_flat(initial, yield_text, yield_unknown)
    return

  stack: list[Iterator[InlineContentItem]] = [iter(initial)]
  while stack:
    for item in stack[-1]:
      match item:
        case str():
          if yield_text:
            yield item
        case InlineNode():
          yield item
          stack.append(iter(item.content))
          break
        case UnknownInlineNode():
          if yield_unknown:
            yield item
        case _:
          raise TypeError(f"Unexpected type {type(item)}")
    else:
      stack.pop()


def walk_content_filtered(
  node: ContentNode, predicate: ContentPredicate, recurse: bool = False
) -> Generator[InlineContentItem, None, None]:
  for child in walk_content(node, yield_text=True, recurse=recurse, yield_unknown=True):
    if predicate(child):
      yield child


def _is_of_type[T](obj: Any, target_type: type[T] | tuple[type[T], ...]) -> TypeIs[T]:
  return isinstance(obj, target_type)


def walk_content_typed[T](
  node: ContentNode, target_type: type[T] | tuple[type[T], ...], recurse: bool = False
) -> Generator[T, None, None]:
  for child in walk_content(node, yield_text=True, recurse=recurse, yield_unknown=True):
    if _is_of_type(child, target_type):
      yield child


@overload
def walk(
  node: TranslationMemory, recurse: bool = False
) -> Generator[StructuralNode, None, None]: ...
@overload
def walk(
  node: TranslationMemoryHeader, recurse: bool = False
) -> Generator[Prop | Note, None, None]: ...
@overload
def walk(node: TranslationUnit, recurse: bool = False) -> Generator[StructuralNode, None, None]: ...
@overload
def walk(node: TranslationVariant, recurse: bool = False) -> Generator[Prop | Note, None, None]: ...
@overload
def walk(node: StructuralNode, recurse: bool = False) -> Generator[StructuralNode, None, None]: ...
def walk(
  node: StructuralNode, recurse: bool = False
) -> Generator[StructuralNode | Prop | Note, None, None]:
  match node:
    case TranslationMemory():
      yield node.header
      if recurse:
        yield from walk(node.header, recurse=recurse)
      for unit in node.units:
        yield unit
        if recurse:
          yield from walk(unit, recurse=recurse)
    case TranslationMemoryHeader() | TranslationVariant():
      yield from node.notes
      yield from node.props
    case TranslationUnit():
      yield from node.notes
      yield from node.props
      for variant in node.variants:
        yield variant
        if recurse:
          yield from walk(variant, recurse=recurse)
    case _:
      raise TypeError(f"Unexpected type {type(node)} in walk")


def walk_filtered(
  node: StructuralNode, predicate: StructuralPredicate, recurse: bool = False
) -> Generator[StructuralNode, None, None]:
  for child in walk(node, recurse=recurse):
    if predicate(child):
      yield child


def walk_typed[T: StructuralNode](
  node: StructuralNode, target_type: type[T] | tuple[type[T], ...], recurse: bool = False
) -> Generator[T, None, None]:
  for child in walk(node, recurse=recurse):
    if _is_of_type(child, target_type):
      yield child


def walk_inline_nodes(
  node: ContentNode, recurse: bool = False
) -> Generator[InlineNode, None, None]:
  return walk_content(node, yield_text=False, recurse=recurse, yield_unknown=False)
