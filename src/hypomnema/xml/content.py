"""The one implementation of XML text/child/tail interleave.

A child's tail belongs to its parent's content, never to the child model.
No indentation or whitespace stripping happens here.
"""

from collections.abc import Iterable, Iterator

from lxml import etree

from ..errors import TmxSpecError

type XmlContentItem = str | etree._Element


def _is_content_element(node: etree._Element) -> bool:
  if isinstance(node, etree._Comment | etree._ProcessingInstruction):
    return False
  if isinstance(node, etree._Entity):
    raise TmxSpecError(f"unresolved entity in content at line {node.sourceline}")
  return True


def child_elements(element: etree._Element) -> Iterator[etree._Element]:
  """Structural children only; the caller validates before discarding text."""
  for child in element:
    if _is_content_element(child):
      yield child


def read_mixed_content(element: etree._Element) -> Iterator[XmlContentItem]:
  """Ignore comments/PIs but retain their tails, joining adjacent text."""
  text_parts: list[str] = []
  if element.text is not None:
    text_parts.append(element.text)
  for child in element:
    if _is_content_element(child):
      if text_parts:
        yield "".join(text_parts)
        text_parts.clear()
      yield child
    if child.tail is not None:
      text_parts.append(child.tail)
  if text_parts:
    yield "".join(text_parts)


def read_text(element: etree._Element) -> str | None:
  """Read plain text, preserving None versus an explicitly empty XML slot."""
  parts: list[str] = []
  for item in read_mixed_content(element):
    if not isinstance(item, str):
      raise TmxSpecError(f"expected text only inside <{element.tag}> at line {element.sourceline}")
    parts.append(item)
  return "".join(parts) if parts else None


def write_text(element: etree._Element, text: str | None) -> None:
  """Set a plain-text node without collapsing None and empty string."""
  try:
    element.text = text
  except ValueError as error:
    raise TmxSpecError(f"XML-illegal text inside <{element.tag}>: {error}") from error


def write_mixed_content(element: etree._Element, items: Iterable[XmlContentItem]) -> None:
  """Populate a fresh element, folding consecutive strings into XML slots."""
  previous_child: etree._Element | None = None
  for item in items:
    if isinstance(item, str):
      try:
        if previous_child is None:
          element.text = item if element.text is None else element.text + item
        else:
          previous_child.tail = item if previous_child.tail is None else previous_child.tail + item
      except ValueError as error:
        raise TmxSpecError(f"XML-illegal text inside <{element.tag}>: {error}") from error
    else:
      element.append(item)
      previous_child = item
