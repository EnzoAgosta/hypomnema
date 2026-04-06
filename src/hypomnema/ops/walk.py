"""Traversal helpers for Hypomnema's domain tree.

These helpers do not mutate nodes. They provide typed iteration over the
structural TMX hierarchy and over inline content lists.
"""

from collections.abc import Callable, Generator, Iterator
from typing import Literal, overload


from hypomnema.domain.nodes import (
  Bpt,
  ContentNode,
  Ept,
  Hi,
  InlineNode,
  It,
  LeafNode,
  Ph,
  StructuralNode,
  Sub,
  TranslationMemoryHeader,
  TranslationMemory,
  TranslationUnit,
  TranslationVariant,
  UnknownInlineNode,
)

type StructuralPredicate = Callable[[StructuralNode | LeafNode], bool]
type ContentPredicate = Callable[[str | InlineNode | UnknownInlineNode], bool]


def _iter_items_flat[T: InlineNode | str | UnknownInlineNode](
  items: list[T], yield_text: bool, yield_unknown: bool
) -> Generator[T]:
  for item in items:
    match item:
      case str():
        if yield_text:
          yield item
      case Bpt() | Ept() | It() | Ph() | Hi() | Sub():
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
) -> Generator[InlineNode]: ...
@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[True] = True,
  recurse: bool = False,
  yield_unknown: Literal[False] = False,
) -> Generator[str | InlineNode]: ...
@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[False],
  recurse: bool = False,
  yield_unknown: Literal[True] = True,
) -> Generator[InlineNode | UnknownInlineNode]: ...
@overload
def walk_content(
  node: ContentNode,
  yield_text: Literal[True] = True,
  recurse: bool = False,
  yield_unknown: Literal[True] = True,
) -> Generator[str | InlineNode | UnknownInlineNode]: ...
def walk_content(
  node: ContentNode, yield_text: bool = True, recurse: bool = False, yield_unknown: bool = False
) -> Generator[str | InlineNode | UnknownInlineNode]:
  """Yield items from a node's inline content.

  When `recurse` is false, only direct children are yielded. When `recurse` is
  true, nested inline containers are yielded depth-first together with their
  contents.
  """
  initial = node.segment if isinstance(node, TranslationVariant) else node.content

  if not recurse:
    match node:
      case TranslationVariant():
        yield from _iter_items_flat(node.segment, yield_text, yield_unknown)
      case Hi() | Sub():
        yield from _iter_items_flat(node.content, yield_text, yield_unknown)
      case Bpt() | Ept() | It() | Ph():
        yield from _iter_items_flat(node.content, yield_text, yield_unknown)
      case _:
        raise TypeError(f"Unexpected type {type(node)}")
    return

  stack: list[Iterator[str | InlineNode | UnknownInlineNode]] = [iter(initial)]
  while stack:
    for item in stack[-1]:
      match item:
        case str():
          if yield_text:
            yield item
        case Bpt() | Ept() | It() | Ph() | Hi() | Sub():
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
) -> Generator[str | InlineNode | UnknownInlineNode]:
  """Yield inline content items whose value matches `predicate`."""
  for child in walk_content(node, yield_text=True, recurse=recurse, yield_unknown=True):
    if predicate(child):
      yield child


@overload
def walk(
  node: TranslationMemory, recurse: bool = False
) -> Generator[TranslationMemoryHeader | TranslationUnit | TranslationVariant | LeafNode]: ...
@overload
def walk(node: TranslationMemoryHeader, recurse: bool = False) -> Generator[LeafNode]: ...
@overload
def walk(
  node: TranslationUnit, recurse: bool = False
) -> Generator[TranslationVariant | LeafNode]: ...
@overload
def walk(node: TranslationVariant, recurse: bool = False) -> Generator[LeafNode]: ...
def walk(
  node: StructuralNode, recurse: bool = False
) -> Generator[TranslationMemoryHeader | TranslationUnit | TranslationVariant | LeafNode]:
  """Yield structural children and leaf attachments from a TMX node.

  `TranslationMemory` yields its header and units. `TranslationUnit` yields its
  notes, props, and variants. Header and variant nodes yield their notes and
  props.
  """
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
) -> Generator[StructuralNode | LeafNode]:
  """Yield structural items from `walk()` that satisfy `predicate`."""
  for child in walk(node, recurse=recurse):
    if predicate(child):
      yield child


def walk_inline_nodes(node: ContentNode, recurse: bool = False) -> Generator[InlineNode]:
  """Yield only inline node objects from a content-bearing node."""
  yield from walk_content(node, yield_text=False, recurse=recurse, yield_unknown=False)
