"""Streaming TMX input and output."""

import codecs
import re
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from enum import Enum, auto
from os import PathLike
from typing import Protocol

from lxml import etree

from .errors import TmxErrorGroup, TmxSpecError
from .models import Header, TranslationUnit
from .xml.build import header_to_element, tu_to_element
from .xml.dtd import validate_fragment
from .xml.parse import header_from_element, tu_from_element

type TmxPath = str | bytes | PathLike[str] | PathLike[bytes]


class TmxBinaryReader(Protocol):
  def read(self, size: int = -1, /) -> bytes: ...

  def seek(self, offset: int, whence: int = 0, /) -> int: ...

  def seekable(self) -> bool: ...

  def tell(self) -> int: ...


class TmxBinaryWriter(Protocol):
  def write(self, data: bytes, /) -> int: ...

  def flush(self) -> None: ...


type TmxSource = TmxPath | TmxBinaryReader
type TmxDestination = TmxPath | TmxBinaryWriter
type TuCreationErrorHook = Callable[[TmxSpecError, etree._Element], TranslationUnit | None]
type TuValidationError = TmxErrorGroup | TmxSpecError
type TuValidationErrorHook = Callable[[TuValidationError, TranslationUnit], TranslationUnit | None]

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


class _WriterState(Enum):
  NEW = auto()
  OPEN = auto()
  FAILED = auto()
  CLOSED = auto()


class TmxReader(Iterator[TranslationUnit]):
  """A single-pass, bounded-memory reader for a TMX path or borrowed stream.

  Borrowed streams must be binary, seekable, and positioned at byte zero.
  The caller retains ownership and the reader leaves the stream open.
  ``on_tu_creation_error`` may replace or skip a translation unit whose
  model projection fails. Its XML element is cleared after the hook returns.
  """

  def __init__(self, source: TmxSource, *, on_tu_creation_error: TuCreationErrorHook | None = None) -> None:
    self.source = source
    self.on_tu_creation_error = on_tu_creation_error
    self.header_peek: dict[str, str] | None = None
    self._state = _ReaderState.NEW
    self._source: TmxBinaryReader | None = None
    self._close_source: Callable[[], None] | None = None
    self._events: Iterator[tuple[str, etree._Element]] | None = None
    self._root: etree._Element | None = None
    self._header_element: etree._Element | None = None
    self._body: etree._Element | None = None

  def __enter__(self) -> TmxReader:
    if self._state is not _ReaderState.NEW:
      raise RuntimeError("a TmxReader can only be entered once")

    if isinstance(self.source, (str, bytes, PathLike)):
      self._source = open(self.source, "rb")
      self._close_source = self._source.close
    else:
      self._source = self.source

    try:
      if self._close_source is None:
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
    if self._close_source is not None:
      self._close_source()
    self._source = None
    self._close_source = None
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
        try:
          unit = tu_from_element(element)
        except TmxSpecError as error:
          if self.on_tu_creation_error is None:
            raise
          unit = self.on_tu_creation_error(error, element)
        element.clear()
        self._body.remove(element)
        if unit is not None:
          return unit
        continue

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
    if self._close_source is not None:
      self._close_source()
    self._source = None
    self._close_source = None
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


class TmxWriter:
  """A single-pass, bounded-memory writer for a TMX path or borrowed stream.

  Output is compact UTF-8 XML without a DOCTYPE. Borrowed streams must be
  binary and writable; the caller retains ownership and the writer leaves
  them open. Header and translation-unit models are strictly validated and
  projected fragments are checked against the packaged DTD before writing.
  ``on_tu_validation_error`` may replace or skip a translation unit rejected
  before output begins. Replacements pass through the complete checks once.
  """

  def __init__(
    self,
    destination: TmxDestination,
    *,
    header: Header,
    on_tu_validation_error: TuValidationErrorHook | None = None,
  ) -> None:
    self.destination = destination
    self.header = header
    self.on_tu_validation_error = on_tu_validation_error
    self._state = _WriterState.NEW
    self._stack: ExitStack | None = None
    self._write_element: Callable[[etree._Element], None] | None = None
    self._flush_destination: Callable[[], None] | None = None

  def __enter__(self) -> TmxWriter:
    if self._state is not _WriterState.NEW:
      raise RuntimeError("a TmxWriter can only be entered once")

    # Finish both checks before a path is opened and possibly truncated.
    try:
      header_element = header_to_element(self.header)
      validate_fragment(header_element)
    except BaseException:
      self._state = _WriterState.CLOSED
      raise

    stack = ExitStack()
    try:
      if isinstance(self.destination, (str, bytes, PathLike)):
        destination = stack.enter_context(open(self.destination, "wb"))
      else:
        destination = self.destination
        try:
          destination.write(b"")
        except TypeError:
          raise TypeError("a borrowed TMX destination must be opened in binary mode") from None

      stack.callback(destination.flush)
      output = stack.enter_context(etree.xmlfile(destination, encoding="UTF-8", close=False, buffered=False))
      output.write_declaration()
      stack.enter_context(output.element("tmx", version="1.4"))
      output.write(header_element)
      stack.enter_context(output.element("body"))
      destination.flush()
    except BaseException:
      self._state = _WriterState.CLOSED
      stack.close()
      raise

    self._stack = stack
    self._write_element = lambda element: output.write(element)
    self._flush_destination = destination.flush
    self._state = _WriterState.OPEN
    return self

  def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
    self.close()

  def close(self) -> None:
    stack = self._stack
    self._stack = None
    self._write_element = None
    self._flush_destination = None
    try:
      if stack is not None:
        stack.close()
    finally:
      self._state = _WriterState.CLOSED

  def write(self, unit: TranslationUnit) -> None:
    if self._state is _WriterState.FAILED:
      raise RuntimeError("the TmxWriter cannot continue after an output failure")
    if self._state is not _WriterState.OPEN:
      raise RuntimeError("write() must be called inside an open TmxWriter context")
    assert self._write_element is not None, "OPEN state requires an element writer"
    assert self._flush_destination is not None, "OPEN state requires a destination flusher"

    try:
      element = _validated_tu_element(unit)
    except (TmxErrorGroup, TmxSpecError) as error:
      if self.on_tu_validation_error is None:
        raise
      replacement = self.on_tu_validation_error(error, unit)
      if replacement is None:
        return
      element = _validated_tu_element(replacement)

    try:
      self._write_element(element)
      self._flush_destination()
    except BaseException:
      self._state = _WriterState.FAILED
      raise


def _validated_tu_element(unit: TranslationUnit) -> etree._Element:
  element = tu_to_element(unit)
  validate_fragment(element)
  return element


def _validate_document_encoding(source: TmxBinaryReader) -> None:
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
