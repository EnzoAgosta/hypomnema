"""Streaming TMX input."""

import codecs
import re
from collections.abc import Iterator
from enum import Enum, auto
from os import PathLike
from typing import BinaryIO

from lxml import etree

from .errors import TmxSpecError
from .models import Header, TranslationUnit
from .xml.parse import header_from_element, tu_from_element

type TmxPath = str | bytes | PathLike[str] | PathLike[bytes]
type TmxSource = TmxPath | BinaryIO

_XML_DECLARATION_LIMIT = 1024
_ENCODING_DECLARATION = re.compile(r"[ \t\r\n]encoding[ \t\r\n]*=[ \t\r\n]*(['\"])([A-Za-z][A-Za-z0-9._-]*)\1")
_TMX_ENCODINGS = frozenset({"utf-8", "utf-16", "us-ascii"})
_UTF32_PREFIXES = tuple("<".encode(encoding) for encoding in ("utf-32-be", "utf-32-le"))
_UTF16_PREFIXES = tuple("<".encode(encoding) for encoding in ("utf-16-be", "utf-16-le"))
_EBCDIC_XML_PREFIX = "<?xm".encode("cp037")


class _ReaderState(Enum):
  NEW = auto()
  HEADER = auto()
  BODY = auto()
  EXHAUSTED = auto()
  CLOSED = auto()


class TmxReader(Iterator[TranslationUnit]):
  """A single-pass, bounded-memory reader for a TMX path or borrowed stream.

  Borrowed streams must be binary, seekable, and positioned at byte zero.
  The caller retains ownership and the reader leaves the stream open.
  """

  def __init__(self, source: TmxSource) -> None:
    self.source = source
    self.header_peek: dict[str, str] | None = None
    self._state = _ReaderState.NEW
    self._source: BinaryIO | None = None
    self._owns_source = False
    self._events: Iterator[tuple[str, etree._Element]] | None = None
    self._root: etree._Element | None = None
    self._header_element: etree._Element | None = None
    self._body: etree._Element | None = None

  def __enter__(self) -> TmxReader:
    if self._state is not _ReaderState.NEW:
      raise RuntimeError("a TmxReader can only be entered once")

    if isinstance(self.source, (str, bytes, PathLike)):
      self._source = open(self.source, "rb")
      self._owns_source = True
    else:
      self._source = self.source

    try:
      if not self._owns_source:
        if not isinstance(self._source.read(0), bytes):
          raise TypeError("a borrowed TMX stream must be opened in binary mode")
        if not self._source.seekable():
          raise ValueError("a borrowed TMX stream must be seekable")
        if self._source.tell() != 0:
          raise ValueError("a borrowed TMX stream must be positioned at byte zero")

      _validate_document_encoding(self._source)
      self._events = etree.iterparse(
        self._source,
        events=("start", "end"),
        resolve_entities=False,
        no_network=True,
        recover=False,
        huge_tree=False,
        remove_comments=True,
        remove_pis=True,
      )

      root = self._expect_event("start", "tmx")
      if dict(root.attrib) != {"version": "1.4"}:
        raise TmxSpecError("<tmx> must have exactly version='1.4'")
      self._root = root

      header = self._expect_event("start", "header")
      self._header_element = header
      self.header_peek = dict(header.attrib)
      self._state = _ReaderState.HEADER
    except BaseException:
      self.close()
      raise

    return self

  def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
    self.close()

  def close(self) -> None:
    if self._source is not None and self._owns_source:
      self._source.close()
    self._source = None
    self._owns_source = False
    self._events = None
    self._root = None
    self._header_element = None
    self._body = None
    self._state = _ReaderState.CLOSED

  def read_header(self) -> Header:
    if self._state is not _ReaderState.HEADER:
      raise RuntimeError("read_header() must be called once, after entering the reader")
    assert self._header_element is not None, "HEADER state requires a retained <header> element"
    assert self._root is not None, "HEADER state requires a retained <tmx> element"

    header_element = self._header_element
    while True:
      event, element = self._next_event()
      if event == "end" and element is header_element:
        break

    header = header_from_element(header_element)
    body = self._expect_event("start", "body")
    if body.attrib:
      raise TmxSpecError("<body> must not have attributes")
    _require_only_xml_whitespace(self._root.text, "before <header>")
    _require_only_xml_whitespace(header_element.tail, "between <header> and <body>")

    header_element.clear()
    self._root.remove(header_element)
    self._root = None
    self._header_element = None
    self._body = body
    self._state = _ReaderState.BODY
    return header

  def __iter__(self) -> TmxReader:
    return self

  def __next__(self) -> TranslationUnit:
    if self._state is _ReaderState.EXHAUSTED:
      raise StopIteration
    if self._state is not _ReaderState.BODY:
      raise RuntimeError("read_header() must be called before iterating translation units")
    assert self._body is not None, "BODY state requires a retained <body> element"

    while True:
      event, element = self._next_event()
      parent = element.getparent()

      if event == "start" and parent is self._body:
        _require_only_xml_whitespace(self._body.text, "inside <body>")
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
    assert self._body is not None, "finishing the document requires a retained <body> element"
    _require_only_xml_whitespace(self._body.text, "inside <body>")
    self._expect_event("end", "tmx")
    _require_only_xml_whitespace(self._body.tail, "after <body>")

    assert self._events is not None, "finishing the document requires an active event iterator"
    try:
      next(self._events)
    except StopIteration:
      pass
    except etree.XMLSyntaxError as error:
      raise TmxSpecError(f"malformed XML: {error}") from error
    else:
      raise TmxSpecError("unexpected content after </tmx>")

    assert self._source is not None, "finishing the document requires an open source"
    if self._owns_source:
      self._source.close()
    self._source = None
    self._owns_source = False
    self._events = None
    self._root = None
    self._body = None

  def _expect_event(self, expected_event: str, expected_tag: str) -> etree._Element:
    event, element = self._next_event()
    if event != expected_event:
      raise TmxSpecError(f"expected the {expected_event} of <{expected_tag}>")
    _require_tag(element, expected_tag)
    return element

  def _next_event(self) -> tuple[str, etree._Element]:
    if self._events is None:
      raise RuntimeError("the reader is not open")
    try:
      return next(self._events)
    except StopIteration:
      raise TmxSpecError("unexpected end of XML document") from None
    except etree.XMLSyntaxError as error:
      raise TmxSpecError(f"malformed XML: {error}") from error


def _validate_document_encoding(source: BinaryIO) -> None:
  prefix = source.read(_XML_DECLARATION_LIMIT)
  source.seek(0)
  declaration = _xml_declaration(prefix)
  if declaration is None:
    return

  match = _ENCODING_DECLARATION.search(declaration)
  if match is not None and match[2].lower() not in _TMX_ENCODINGS:
    raise TmxSpecError(f"TMX supports only UTF-8, UTF-16, and US-ASCII, not {match[2]!r}")


def _xml_declaration(prefix: bytes) -> str | None:
  if prefix.startswith((codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE)):
    raise TmxSpecError("TMX does not support UTF-32")

  if prefix.startswith(codecs.BOM_UTF16_BE):
    return _extract_xml_declaration(prefix[len(codecs.BOM_UTF16_BE) :], "utf-16-be")
  if prefix.startswith(codecs.BOM_UTF16_LE):
    return _extract_xml_declaration(prefix[len(codecs.BOM_UTF16_LE) :], "utf-16-le")

  if prefix.startswith(_UTF32_PREFIXES):
    raise TmxSpecError("TMX does not support UTF-32")
  if prefix.startswith(_UTF16_PREFIXES):
    raise TmxSpecError("a UTF-16 TMX file must begin with a byte-order mark")
  if prefix.startswith(_EBCDIC_XML_PREFIX):
    raise TmxSpecError("TMX supports only UTF-8, UTF-16, and US-ASCII")

  if prefix.startswith(codecs.BOM_UTF8):
    prefix = prefix[len(codecs.BOM_UTF8) :]
  return _extract_xml_declaration(prefix, "ascii")


def _extract_xml_declaration(prefix: bytes, encoding: str) -> str | None:
  start = "<?xml".encode(encoding)
  if not prefix.startswith(start):
    return None
  end = "?>".encode(encoding)
  end_index = prefix.find(end, len(start))
  if end_index < 0:
    raise TmxSpecError(f"XML declaration exceeds {_XML_DECLARATION_LIMIT} bytes or is not terminated")
  try:
    declaration = prefix[: end_index + len(end)].decode(encoding)
  except UnicodeDecodeError as error:
    raise TmxSpecError(f"malformed XML declaration: {error}") from error
  if len(declaration) == len("<?xml") or declaration[len("<?xml")] not in " \t\r\n":
    return None
  return declaration


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
