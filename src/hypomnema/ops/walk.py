from collections.abc import Callable, Generator
from functools import singledispatch
from typing import Any, Literal, TypeIs, overload

from hypomnema.domain.model import InlineContentItem, InlineNode, StructuralNode, UnknownInlineNode
from hypomnema.domain.nodes import (
  TranslationMemoryHeader,
  Note,
  Prop,
  TranslationMemory,
  TranslationUnit,
  TranslationVariant,
)


type ContentNode = InlineNode | TranslationVariant
type StructuralPredicate = Callable[[StructuralNode], bool]
type ContentPredicate = Callable[[InlineContentItem], bool]


@singledispatch
def walk(node, recurse=False):
  raise TypeError(f"Unexpected type {type(node)} in walk")


def _iter_items(
  items: list[InlineContentItem], yield_text: bool, recurse: bool, yield_unknown: bool
) -> Generator[InlineContentItem, None, None]:
  for item in items:
    match item:
      case str():
        if yield_text:
          yield item
      case InlineNode():
        yield item
        if recurse:
          yield from _iter_items(item.content, yield_text, recurse, yield_unknown)
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
  if isinstance(node, TranslationVariant):
    yield from _iter_items(node.segment, yield_text, recurse, yield_unknown)
  else:
    yield from _iter_items(node.content, yield_text, recurse, yield_unknown)


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


@walk.register
def walk_translation_memory(
  node: TranslationMemory, recurse: bool = False
) -> Generator[StructuralNode, None, None]:
  yield node.header
  if recurse:
    yield from walk(node.header, recurse=recurse)
  for unit in node.units:
    yield unit
    if recurse:
      yield from walk(unit, recurse=recurse)


@walk.register
def walk_header(
  node: TranslationMemoryHeader | TranslationVariant, recurse: bool = False
) -> Generator[Prop | Note, None, None]:
  yield from node.notes
  yield from node.props


@walk.register
def walk_unit(
  node: TranslationUnit, recurse: bool = False
) -> Generator[StructuralNode, None, None]:
  yield from node.notes
  yield from node.props
  for variant in node.variants:
    yield variant
    if recurse:
      yield from walk(variant, recurse=recurse)


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
    if isinstance(child, target_type):
      yield child
