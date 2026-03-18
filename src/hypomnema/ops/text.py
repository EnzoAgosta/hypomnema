from collections.abc import Callable, Generator
import re

from hypomnema.domain.model import InlineNode, UnknownInlineNode
from hypomnema.domain.nodes import TranslationVariant
from hypomnema.ops import walk

type ContentNode = InlineNode | TranslationVariant
type FragmentSource = ContentNode | UnknownInlineNode


def iter_fragments_with_source(
  node: ContentNode,
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> Generator[tuple[str, FragmentSource], None, None]:
  for fragment in walk.walk_content(node, recurse=False, yield_unknown=True):
    match fragment:
      case UnknownInlineNode():
        if unknown_formatter is not None:
          yield unknown_formatter(fragment), fragment
      case str():
        yield fragment, node
      case InlineNode():
        if recurse:
          yield from iter_fragments_with_source(
            fragment, recurse=True, unknown_formatter=unknown_formatter
          )
      case _:
        raise TypeError(f"Unexpected type {type(fragment)}")


def iter_fragments(
  node: ContentNode,
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> Generator[str, None, None]:
  for fragment, _ in iter_fragments_with_source(
    node, recurse=recurse, unknown_formatter=unknown_formatter
  ):
    yield fragment


def is_empty(node: ContentNode, recurse: bool = False) -> bool:
  return next(iter_fragments(node, recurse=recurse), None) is None


def find(
  node: ContentNode,
  target: str | re.Pattern[str],
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> str | None:
  if isinstance(target, str):
    target = re.compile(target)

  for fragment in iter_fragments(node, recurse=recurse, unknown_formatter=unknown_formatter):
    if target.search(fragment):
      return fragment
  return None


def find_iter(
  node: ContentNode,
  target: str | re.Pattern[str],
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> Generator[str, None, None]:
  if isinstance(target, str):
    target = re.compile(target)

  for fragment in iter_fragments(node, recurse=recurse, unknown_formatter=unknown_formatter):
    if target.search(fragment):
      yield fragment


def find_all(
  node: ContentNode,
  target: str | re.Pattern[str],
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> list[str]:
  return list(find_iter(node, target, recurse=recurse, unknown_formatter=unknown_formatter))


def join(
  node: ContentNode,
  separator: str = "",
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> str:
  return separator.join(iter_fragments(node, recurse=recurse, unknown_formatter=unknown_formatter))
