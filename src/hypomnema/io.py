"""Streaming TMX input."""

from collections.abc import Iterator
from enum import Enum, auto
from os import PathLike

from lxml import etree

from .errors import TmxSpecError
from .models import Header, TranslationUnit
from .xml.parse import header_from_element, tu_from_element


class _ReaderState(Enum):
  NEW = auto()
  HEADER_START = auto()
  BODY_START = auto()
  ITERATING = auto()
  EXHAUSTED = auto()
  CLOSED = auto()


class TmxReader(Iterator[TranslationUnit]):
  """A single-pass, bounded-memory reader for a TMX file."""

  def __init__(self, path: str | PathLike[str]) -> None:
    self.path = path
    self.header_peek: dict[str, str] | None = None
    self._state = _ReaderState.NEW
    self._source = None
    self._events: Iterator[tuple[str, etree._Element]] | None = None
    self._root: etree._Element | None = None
    self._header_element: etree._Element | None = None
    self._body: etree._Element | None = None

  def __enter__(self) -> "TmxReader":
    if self._state is not _ReaderState.NEW:
      raise RuntimeError("a TmxReader can only be entered once")

    self._source = open(self.path, "rb")
    self._events = etree.iterparse(
      self._source,
      events=("start", "end"),
      resolve_entities=False,
      no_network=True,
      recover=False,
      huge_tree=False,
    )

    try:
      _, root = self._expect_event("start", "tmx")
      if dict(root.attrib) != {"version": "1.4"}:
        raise TmxSpecError("<tmx> must have exactly version='1.4'")
      self._root = root

      _, header = self._expect_event("start", "header")
      if header.getparent() is not root:
        raise TmxSpecError("<header> must be the first child of <tmx>")
      self._header_element = header
      self.header_peek = dict(header.attrib)
      self._state = _ReaderState.HEADER_START
    except BaseException:
      self.close()
      raise

    return self

  def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
    self.close()

  def close(self) -> None:
    if self._source is not None:
      self._source.close()
      self._source = None
    self._events = None
    self._state = _ReaderState.CLOSED

  def read_header(self) -> Header:
    if self._state is not _ReaderState.HEADER_START:
      raise RuntimeError("read_header() must be called once, after entering the reader")
    if self._header_element is None or self._root is None:
      raise RuntimeError("reader state is inconsistent")

    header_element = self._header_element
    while True:
      event, element = self._next_event()
      if event == "end" and element is header_element:
        break

    header = header_from_element(header_element)
    _, body = self._expect_event("start", "body")
    if body.getparent() is not self._root:
      raise TmxSpecError("<body> must immediately follow <header>")
    if body.attrib:
      raise TmxSpecError("<body> must not have attributes")
    _require_only_xml_whitespace(self._root.text, "before <header>")
    _require_only_xml_whitespace(header_element.tail, "between <header> and <body>")

    header_element.clear()
    self._root.remove(header_element)
    self._header_element = None
    self._body = body
    self._state = _ReaderState.BODY_START
    return header

  def __iter__(self) -> "TmxReader":
    if self._state is _ReaderState.HEADER_START:
      raise RuntimeError("read_header() must be called before iterating translation units")
    if self._state in (_ReaderState.NEW, _ReaderState.CLOSED):
      raise RuntimeError("the reader must be open before it can be iterated")
    if self._state is _ReaderState.BODY_START:
      self._state = _ReaderState.ITERATING
    return self

  def __next__(self) -> TranslationUnit:
    if self._state is _ReaderState.BODY_START:
      self._state = _ReaderState.ITERATING
    elif self._state is _ReaderState.EXHAUSTED:
      raise StopIteration
    elif self._state is not _ReaderState.ITERATING:
      raise RuntimeError("read_header() must be called before iterating translation units")
    if self._body is None:
      raise RuntimeError("reader state is inconsistent")

    while True:
      event, element = self._next_event()
      parent = element.getparent()

      if event == "start" and parent is self._body:
        _require_tag(element, "tu")
        continue

      if event == "end" and parent is self._body:
        _require_tag(element, "tu")
        _require_only_xml_whitespace(element.tail, "between <tu> elements")
        unit = tu_from_element(element)
        element.clear()
        self._body.remove(element)
        return unit

      if event == "end" and element is self._body:
        self._finish_document()
        self._state = _ReaderState.EXHAUSTED
        raise StopIteration

  def _finish_document(self) -> None:
    if self._body is None or self._root is None:
      raise RuntimeError("reader state is inconsistent")
    _require_only_xml_whitespace(self._body.text, "inside <body>")
    _, root = self._expect_event("end", "tmx")
    if root is not self._root:
      raise TmxSpecError("unexpected </tmx>")
    _require_only_xml_whitespace(self._body.tail, "after <body>")

    if self._events is None:
      raise RuntimeError("the reader is not open")
    try:
      next(self._events)
    except StopIteration:
      return
    except etree.XMLSyntaxError as error:
      raise TmxSpecError(f"malformed XML: {error}") from error
    raise TmxSpecError("unexpected content after </tmx>")

  def _expect_event(self, expected_event: str, expected_tag: str) -> tuple[str, etree._Element]:
    event, element = self._next_event()
    if event != expected_event:
      raise TmxSpecError(f"expected the {expected_event} of <{expected_tag}>")
    _require_tag(element, expected_tag)
    return event, element

  def _next_event(self) -> tuple[str, etree._Element]:
    if self._events is None:
      raise RuntimeError("the reader is not open")
    try:
      return next(self._events)
    except StopIteration:
      raise TmxSpecError("unexpected end of XML document") from None
    except etree.XMLSyntaxError as error:
      raise TmxSpecError(f"malformed XML: {error}") from error


def _require_tag(element: etree._Element, expected: str) -> None:
  try:
    qname = etree.QName(element)
  except ValueError as error:
    raise TmxSpecError(f"expected namespace-free <{expected}>, got {element.tag!r}") from error
  if qname.namespace is not None or qname.localname != expected:
    raise TmxSpecError(f"expected namespace-free <{expected}>, got {element.tag!r} at line {element.sourceline}")


def _require_only_xml_whitespace(text: str | None, location: str) -> None:
  if text is not None and any(character not in " \t\r\n" for character in text):
    raise TmxSpecError(f"expected only XML whitespace {location}")
