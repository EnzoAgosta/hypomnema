"""Read and write XML mixed content while preserving text and whitespace.

A child's tail belongs to its parent's content. Comments and processing
instructions are omitted on read, but their tails are retained.
"""

from collections.abc import Iterable, Iterator

from lxml import etree

from ..errors import TmxSpecError

type XmlContentItem = str | etree._Element


def _is_content_element(node: etree._Element) -> bool:
  """Exclude comments and processing instructions; reject unresolved entities."""
  if isinstance(node, etree._Comment | etree._ProcessingInstruction):
    return False
  if isinstance(node, etree._Entity):
    raise TmxSpecError(f"unresolved entity in content at line {node.sourceline}")
  return True


def child_elements(element: etree._Element) -> Iterator[etree._Element]:
  """Yield structural children in document order, ignoring comments and PIs.

  Args:
      element: Parent whose direct children are inspected. The caller must
          validate text before discarding it.

  Yields:
      Existing child elements, without copying or removing them.

  Raises:
      TmxSpecError: A child is an unresolved entity.
  """
  for child in element:
    if _is_content_element(child):
      yield child


def read_mixed_content(element: etree._Element) -> Iterator[XmlContentItem]:
  """Yield interleaved text and children, joining adjacent text pieces.

  Args:
      element: Parent whose text and child tails form the content. Its own
          tail is excluded. Comments and PIs contribute only their tails.

  Yields:
      Text strings and existing child elements in document order. Whitespace
      and explicitly empty text slots are preserved.

  Raises:
      TmxSpecError: Content contains an unresolved entity.
  """
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
  """Read text-only content, preserving absent and explicitly empty text.

  Args:
      element: Element whose content is read, excluding its own tail.

  Returns:
      Joined text, or ``None`` if there are no text slots. Comments and
      processing instructions contribute only their tails.

  Raises:
      TmxSpecError: Content contains a child element or unresolved entity.
  """
  parts: list[str] = []
  for item in read_mixed_content(element):
    if not isinstance(item, str):
      raise TmxSpecError(f"expected text only inside <{element.tag}> at line {element.sourceline}")
    parts.append(item)
  return "".join(parts) if parts else None


def write_text(element: etree._Element, text: str | None) -> None:
  """Set an element's text slot without changing its children or tail.

  Args:
      element: Element to mutate.
      text: Text to assign. ``None`` clears the slot; an empty string keeps
          an explicitly empty slot.

  Raises:
      TmxSpecError: The text contains characters that XML cannot represent.
  """
  try:
    element.text = text
  except ValueError as error:
    raise TmxSpecError(f"XML-illegal text inside <{element.tag}>: {error}") from error


def write_mixed_content(element: etree._Element, items: Iterable[XmlContentItem]) -> None:
  """Populate a fresh element with interleaved text and child elements.

  Consecutive strings are joined in the parent's text or the preceding
  child's tail. Supplied children are moved into the parent, not copied.

  Args:
      element: Empty destination element to mutate.
      items: Ordered strings and detached child elements with no tails.

  Raises:
      TmxSpecError: A text item contains characters XML cannot represent.
          Content written before the failure remains in the element.
  """
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
