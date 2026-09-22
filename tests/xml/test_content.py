"""Unit tests for the text/content interleave readers and writers."""

from copy import deepcopy

import pytest
from lxml import etree

from hypomnema.errors import TmxSpecError
from hypomnema.xml.content import child_elements, read_mixed_content, read_text, write_mixed_content, write_text


def test_child_elements_skips_comments_and_pis():
  """Yield element children in order without comments or processing instructions."""
  element = etree.fromstring("<wrapper><!--c--><x/><?p i?><y/></wrapper>")
  assert [child.tag for child in child_elements(element)] == ["x", "y"]


def test_read_mixed_content_of_plain_text():
  """Yield the wrapper's text as one mixed-content item."""
  assert list(read_mixed_content(etree.fromstring("<wrapper>text</wrapper>"))) == ["text"]


def test_read_mixed_content_of_empty_element():
  """Yield no mixed-content items for an empty element."""
  assert list(read_mixed_content(etree.fromstring("<wrapper/>"))) == []


def test_read_mixed_content_interleaves_text_and_elements():
  """Yield leading text, child elements, and tails in document order."""
  element = etree.fromstring("<wrapper>a<x/>b<y/>c</wrapper>")
  items = list(read_mixed_content(element))
  assert items[0] == "a"
  first_child = items[1]
  assert not isinstance(first_child, str)
  assert first_child.tag == "x"
  assert items[2] == "b"
  second_child = items[3]
  assert not isinstance(second_child, str)
  assert second_child.tag == "y"
  assert items[4] == "c"


def test_read_mixed_content_joins_text_across_comments_and_pis():
  """Join text across discarded comments and processing instructions."""
  element = etree.fromstring("<wrapper>a<!--x-->b<?p i?>c</wrapper>")
  assert list(read_mixed_content(element)) == ["abc"]


def test_read_mixed_content_with_none_text_still_yields_children():
  """Yield child elements even when the wrapper has no leading text."""
  element = etree.fromstring("<wrapper><x/></wrapper>")
  items = [item for item in read_mixed_content(element) if not isinstance(item, str)]
  assert [item.tag for item in items] == ["x"]


def test_read_mixed_content_rejects_unresolved_entities():
  """Raise a specification error for an unresolved entity in mixed content."""
  parser = etree.XMLParser(resolve_entities=False)
  element = etree.fromstring('<!DOCTYPE wrapper [<!ENTITY e "text">]><wrapper>&e;</wrapper>', parser)
  with pytest.raises(TmxSpecError, match="unresolved entity"):
    list(read_mixed_content(element))


def test_read_text_reads_plain_text_only():
  """Return plain text or None for XML elements without a body."""
  assert read_text(etree.fromstring("<note>text</note>")) == "text"
  assert read_text(etree.fromstring("<note/>")) is None
  assert read_text(etree.fromstring("<note></note>")) is None


def test_read_text_rejects_element_children():
  """Reject child elements where a text-only body is required."""
  with pytest.raises(TmxSpecError, match="expected text only"):
    read_text(etree.fromstring("<note>text <x/> more</note>"))


def test_write_text_distinguishes_none_and_empty():
  """Preserve the in-memory distinction between absent and empty text."""
  element = etree.Element("note")
  write_text(element, None)
  assert element.text is None
  assert etree.tostring(element).decode() == "<note/>"
  element = etree.Element("note")
  write_text(element, "")
  assert element.text == ""
  assert etree.tostring(element).decode() == "<note></note>"


def test_write_text_rejects_xml_illegal_characters():
  """Reject forbidden XML control characters in a text-only body."""
  with pytest.raises(TmxSpecError, match="XML-illegal"):
    write_text(etree.Element("note"), "bad \x03 text")


def test_write_mixed_content_interleaves():
  """Place leading text on the parent and trailing text on the child's tail."""
  element = etree.Element("wrapper")
  child = etree.Element("x")
  write_mixed_content(element, ["a", child, "b"])
  assert element.text == "a"
  assert element[0] is child
  assert child.tail == "b"


def test_write_mixed_content_folds_consecutive_strings():
  """Combine consecutive strings in parent text and child tail slots."""
  element = etree.Element("wrapper")
  child = etree.Element("x")
  write_mixed_content(element, ["a", "b", child, "c", "d"])
  assert element.text == "ab"
  assert child.tail == "cd"


def test_write_mixed_content_accepts_many_adjacent_chunks() -> None:
  """Consume a generator of text chunks, retaining both text and tail runs."""
  element = etree.Element("seg")
  child = etree.Element("ph")
  chunks = ["abc" * 20] * 16000
  write_mixed_content(element, (item for item in [*chunks, child, *chunks]))
  assert element.text == "".join(chunks)
  assert child.tail == element.text


@pytest.mark.parametrize("items, expected", [([], None), ([""], ""), (["", ""], "")])
def test_write_mixed_content_preserves_empty_text(items: list[str], expected: str | None) -> None:
  """Distinguish an absent text run from explicitly empty chunks."""
  element = etree.Element("seg")
  write_mixed_content(element, items)
  assert element.text == expected


def test_write_mixed_content_rejects_xml_illegal_strings():
  """Reject forbidden XML characters in leading mixed-content text."""
  element = etree.Element("wrapper")
  with pytest.raises(TmxSpecError, match="XML-illegal"):
    write_mixed_content(element, ["bad \x03 text"])


def test_write_mixed_content_rejects_xml_illegal_tails():
  """The tail slot is a distinct fold path from the element text."""
  element = etree.Element("wrapper")
  child = etree.Element("x")
  with pytest.raises(TmxSpecError, match="XML-illegal"):
    write_mixed_content(element, [child, "bad \x03"])
  assert element.text is None


def test_write_mixed_content_folds_into_existing_slots():
  """Append mixed-content strings to existing parent text and child tails."""
  element = etree.Element("wrapper")
  element.text = "start"
  child = etree.Element("x")
  child.tail = "mid"
  write_mixed_content(element, ["first ", child, "and more"])
  assert element.text == "startfirst "
  assert child.tail == "midand more"


def test_content_round_trips_through_read_and_write():
  """Reproduce comment-free XML after reading and rebuilding mixed content.

  Copy child elements and clear their tails before writing. The reader emits
  tail strings separately, so leaving the original tails would duplicate text.
  """
  element = etree.fromstring("<wrapper>before <x/> mid <y/> after</wrapper>")
  items = []
  for item in read_mixed_content(element):
    if isinstance(item, str):
      items.append(item)
    else:
      copy = deepcopy(item)
      copy.tail = None
      items.append(copy)
  rebuilt = etree.Element("wrapper")
  write_mixed_content(rebuilt, items)
  assert etree.tostring(rebuilt).decode() == etree.tostring(element).decode()


def test_content_round_trip_drops_comments_but_keeps_text_flow():
  """Omit comments when rebuilding content while preserving surrounding text."""
  element = etree.fromstring("<wrapper>a<!--note-->b</wrapper>")
  rebuilt = etree.Element("wrapper")
  write_mixed_content(rebuilt, list(read_mixed_content(element)))
  assert etree.tostring(rebuilt).decode() == "<wrapper>ab</wrapper>"
