"""Read-only text extraction helpers for inline TMX content."""

from collections.abc import Callable, Generator
import re

from hypomnema.domain.nodes import Bpt, Ept, Hi, InlineNode, It, Ph, Sub, UnknownInlineNode
from hypomnema.ops import walk

type FragmentSource = InlineNode | UnknownInlineNode


def iter_fragments_with_source(
  node: InlineNode,
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> Generator[tuple[str, FragmentSource], None, None]:
  """Yield text fragments together with the node that produced each fragment.

  Plain strings are associated with the inline node that owns them. Unknown
  inline nodes only contribute a fragment when `unknown_formatter` is provided.
  """
  for fragment in walk.walk_content(node, recurse=False, yield_unknown=True):
    match fragment:
      case UnknownInlineNode():
        if unknown_formatter is not None:
          yield unknown_formatter(fragment), fragment
      case str():
        yield fragment, node
      case Bpt() | Ept() | It() | Ph() | Hi() | Sub():
        if recurse:
          yield from iter_fragments_with_source(
            fragment, recurse=True, unknown_formatter=unknown_formatter
          )
      case _:
        raise TypeError(f"Unexpected type {type(fragment)}")


def iter_fragments(
  node: InlineNode,
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> Generator[str, None, None]:
  """Yield text fragments from an inline node, optionally descending into children."""
  for fragment, _ in iter_fragments_with_source(
    node, recurse=recurse, unknown_formatter=unknown_formatter
  ):
    yield fragment


def is_empty(node: InlineNode, recurse: bool = False) -> bool:
  """Return `True` when no text fragments are available from `node`."""
  return next(iter_fragments(node, recurse=recurse), None) is None


def find(
  node: InlineNode,
  target: str | re.Pattern[str],
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> str | None:
  """Return the first fragment whose text matches `target`, if any."""
  if isinstance(target, str):
    target = re.compile(target)

  for fragment in iter_fragments(node, recurse=recurse, unknown_formatter=unknown_formatter):
    if target.search(fragment):
      return fragment
  return None


def find_iter(
  node: InlineNode,
  target: str | re.Pattern[str],
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> Generator[str, None, None]:
  """Yield every fragment whose text matches `target`."""
  if isinstance(target, str):
    target = re.compile(target)

  for fragment in iter_fragments(node, recurse=recurse, unknown_formatter=unknown_formatter):
    if target.search(fragment):
      yield fragment


def find_all(
  node: InlineNode,
  target: str | re.Pattern[str],
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> list[str]:
  """Collect `find_iter()` results into a list."""
  return list(find_iter(node, target, recurse=recurse, unknown_formatter=unknown_formatter))


def join(
  node: InlineNode,
  separator: str = "",
  recurse: bool = False,
  unknown_formatter: Callable[[UnknownInlineNode], str] | None = None,
) -> str:
  """Join extracted fragments into one string."""
  return separator.join(iter_fragments(node, recurse=recurse, unknown_formatter=unknown_formatter))
