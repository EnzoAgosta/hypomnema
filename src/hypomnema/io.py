"""Stream TMX 1.4b documents through context-managed readers and writers.

Readers check XML structure and coerce model values; writers additionally
apply strict semantic validation. Paths are opened and closed internally.
Caller-supplied binary streams remain open. Recovery hooks can replace or
skip individual units, but cannot repair document structure or I/O failures.
"""

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
from .xml.content import child_elements
from .xml.dtd import validate_fragment
from .xml.parse import header_from_element, tu_from_element

type TmxPath = str | bytes | PathLike[str] | PathLike[bytes]


class TmxBinaryReader(Protocol):
  """Binary stream interface required for a borrowed ``TmxReader`` source.

  The stream must be seekable and positioned at byte zero on entry. The
  reader does not close it, including on failure or early termination.
  """

  def read(self, size: int = -1, /) -> bytes:
    """Read up to ``size`` bytes, or all remaining bytes when ``size`` is negative."""
    ...

  def seek(self, offset: int, whence: int = 0, /) -> int:
    """Set the byte position relative to ``whence`` and return the new position."""
    ...

  def seekable(self) -> bool:
    """Return whether the stream supports random access through ``seek``."""
    ...

  def tell(self) -> int:
    """Return the current byte position from the start of the stream."""
    ...


class TmxBinaryWriter(Protocol):
  """Binary stream interface required for a borrowed ``TmxWriter`` destination.

  The writer flushes output but leaves the stream open. Seeking is not
  required, and bytes are written at the stream's current position.
  """

  def write(self, data: bytes, /) -> int:
    """Write binary data and return the number of bytes accepted."""
    ...

  def flush(self) -> None:
    """Flush pending output to the underlying destination."""
    ...


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
  """Track whether a reader can enter, read its header, iterate, or close."""

  NEW = auto()
  HEADER = auto()
  BODY = auto()
  EXHAUSTED = auto()
  CLOSED = auto()


class _WriterState(Enum):
  """Track writer entry, writable output, output failure, and closure."""

  NEW = auto()
  OPEN = auto()
  FAILED = auto()
  CLOSED = auto()


class TmxReader(Iterator[TranslationUnit]):
  """Read a TMX document once without retaining previously yielded units.

  Use as a context manager, call ``read_header()`` once, then iterate over
  translation units. Entering captures raw header attributes in
  ``header_peek`` before constructing the header model. The reader checks
  XML and DTD structure and coerces field values; it does not run strict
  semantic validation. Only UTF-8, UTF-16 with a BOM, and US-ASCII encodings
  are accepted.

  Attributes:
      source: Input path or borrowed binary stream supplied at construction.
      on_tu_creation_error: Optional hook for failed unit projection.
      header_peek: Copy of raw XML header attributes available after entry,
          or ``None`` before entry. Reading it does not consume the header.
  """

  def __init__(self, source: TmxSource, *, on_tu_creation_error: TuCreationErrorHook | None = None) -> None:
    """Configure a reader without opening or consuming its source.

    Args:
        source: Path, or binary seekable stream positioned at byte zero.
            Borrowed streams remain open when the reader closes.
        on_tu_creation_error: Called with a projection error and the failing
            ``<tu>`` element. Return a replacement unit or ``None`` to skip it.
            Replacements are not validated. The element is cleared after the
            hook returns; copy any XML that must outlive the call. Document
            structure errors outside unit projection do not invoke the hook.
    """
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
    """Open the source and read through the start of the header.

    Returns:
        This reader with ``header_peek`` populated.

    Raises:
        RuntimeError: This reader has already been entered or closed.
        TypeError: A borrowed source does not return bytes.
        ValueError: A borrowed source is not seekable or is not at byte zero.
        TmxSpecError: Encoding, XML, or the document's opening structure is
            invalid. Header content is checked later by ``read_header()``.
        OSError: The source cannot be opened or read.
    """
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
    """Close the reader without suppressing exceptions from the context body."""
    self.close()

  def close(self) -> None:
    """Release parser state and close an internally opened source.

    Borrowed streams remain open at their current position, which may be
    past the last yielded unit because the XML parser reads ahead. Repeated
    calls are harmless. Closing prevents further reads or re-entry.
    """
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
    """Consume and project the header, then position iteration at the body.

    Returns:
        Header model with coerced attributes, without strict validation.

    Raises:
        RuntimeError: The reader has not been entered, or the header has
            already been read.
        TmxSpecError: Header projection, XML, or the opening body structure
            is invalid.
        OSError: Reading the source fails.
    """
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
    # Entity references have no start/end events. Inspect wrapper children too.
    for _ in child_elements(self._root):
      pass

    header_element.clear()
    self._root.remove(header_element)
    self._root = None
    self._header_element = None
    self._body = body
    self._state = _ReaderState.BODY
    return header

  def __iter__(self) -> TmxReader:
    """Return this single-pass iterator without changing its position."""
    return self

  def __next__(self) -> TranslationUnit:
    """Read and return the next unit, applying the creation hook on failure.

    XML for a yielded or skipped unit is discarded. Exhausting iteration
    checks the document's closing structure and closes an owned source.

    Returns:
        The next projected unit or a replacement returned by the hook.

    Raises:
        StopIteration: The complete document has been consumed.
        RuntimeError: ``read_header()`` has not completed or the reader closed.
        TmxSpecError: XML or document structure is invalid, or a unit cannot
            be projected and no hook handles its error.
        OSError: Reading the source fails.
    """
    if self._state is _ReaderState.EXHAUSTED:
      raise StopIteration
    if self._state is not _ReaderState.BODY:
      raise RuntimeError("read_header() must be called before iterating translation units")
    assert self._body is not None, "BODY state requires a retained <body> element"

    while True:
      event, element = self._next_event()
      parent = element.getparent()

      if event == "start" and parent is self._body:
        previous = element.getprevious()
        if isinstance(previous, etree._Entity):
          raise TmxSpecError(f"unresolved entity inside <body> at line {previous.sourceline}")
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
    """Check closing XML and trailing content, then release the exhausted source."""
    assert self._body is not None, "finishing the document requires a retained <body> element"
    _require_only_xml_whitespace(self._body.text, "inside <body>")
    # Processed units have been removed, so this walk visits only leftovers.
    for _ in child_elements(self._body):
      pass
    root = self._expect_event("end", "tmx")
    for _ in child_elements(root):
      pass
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
    """Consume the next event and reject an unexpected event kind or tag."""
    event, element = self._next_event()
    if event != expected_event:
      raise TmxSpecError(f"expected the {expected_event} of <{expected_tag}>")
    _require_tag(element, expected_tag)
    return element

  def _next_event(self) -> tuple[str, etree._Element]:
    """Read one parser event, translating malformed or truncated XML to TMX errors."""
    if self._events is None:
      raise RuntimeError("the reader is not open")
    try:
      return next(self._events)
    except StopIteration:
      raise TmxSpecError("unexpected end of XML document") from None
    except etree.XMLSyntaxError as error:
      raise TmxSpecError(f"malformed XML: {error}") from error


class TmxWriter:
  """Write validated TMX units once, without buffering the complete document.

  Use as a context manager and call ``write()`` for each unit. Output is
  compact UTF-8 XML with a declaration and no DOCTYPE. The header is checked
  before opening a path, which would truncate an existing file. Each unit
  passes strict model validation and DTD checks before any of its XML is
  written. Closing finishes the document even if the context body raises.

  Attributes:
      destination: Output path or borrowed binary stream.
      header: Header model written when entering the context.
      on_tu_validation_error: Optional hook for units rejected before output.
  """

  def __init__(
    self,
    destination: TmxDestination,
    *,
    header: Header,
    on_tu_validation_error: TuValidationErrorHook | None = None,
  ) -> None:
    """Configure a writer without opening or modifying its destination.

    Args:
        destination: Path to create or truncate on entry, or writable binary
            stream. Borrowed streams remain open; output starts at their current
            position.
        header: Header to validate and write on entry.
        on_tu_validation_error: Called with a validation error and rejected
            unit. Return a replacement unit or ``None`` to skip it. A
            replacement is checked once and cannot trigger the hook again.
            Header errors and output failures do not invoke the hook.
    """
    self.destination = destination
    self.header = header
    self.on_tu_validation_error = on_tu_validation_error
    self._state = _WriterState.NEW
    self._stack: ExitStack | None = None
    self._write_element: Callable[[etree._Element], None] | None = None
    self._flush_destination: Callable[[], None] | None = None

  def __enter__(self) -> TmxWriter:
    """Validate the header, open output, and write through the body start.

    Returns:
        This writer, ready to accept units.

    Raises:
        RuntimeError: This writer has already been entered or closed.
        TmxErrorGroup: Strict header validation fails.
        TmxSpecError: Header projection or DTD validation fails.
        TypeError: A borrowed destination rejects binary data.
        OSError: Opening, writing, or flushing the destination fails.
            Failures after opening output may leave partial bytes.
    """
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
    """Finish and close output without suppressing exceptions from the context body."""
    self.close()

  def close(self) -> None:
    """Write closing tags, flush output, and release writer resources.

    Internally opened files are closed; borrowed streams remain open.
    Repeated calls are harmless after cleanup. Output errors propagate, but
    the writer remains closed and cannot be re-entered.
    """
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
    """Validate a unit, write its XML, and flush the destination.

    A rejected unit can be replaced or skipped by the validation hook.
    Validation failures leave the writer available for subsequent calls.
    An output failure prevents further writes and may leave partial XML.

    Args:
        unit: Translation unit whose complete subtree must pass strict
            validation and DTD checks before output starts for that unit.

    Raises:
        RuntimeError: The writer is not open or a previous output failed.
        TmxErrorGroup: Strict validation fails without a hook, or the hook's
            replacement fails strict validation.
        TmxSpecError: Projection or DTD checks fail without a hook, or fail
            for a replacement.
        OSError: Writing or flushing output fails.
    """
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
  """Build a strictly validated unit subtree and check it against the DTD."""
  element = tu_to_element(unit)
  validate_fragment(element)
  return element


def _validate_document_encoding(source: TmxBinaryReader) -> None:
  """Check the initial byte signature and declared encoding, then rewind.

  Reads at most the declaration limit and restores the source to byte zero
  before examining the prefix. Unsupported or malformed declarations raise
  ``TmxSpecError``. XML syntax outside the declaration is checked later.
  """
  prefix = source.read(_XML_DECLARATION_LIMIT)
  source.seek(0)
  declaration = _xml_declaration(prefix)
  if declaration is None:
    return

  match = _ENCODING_DECLARATION.search(declaration)
  if match is not None and match[2].lower() not in _TMX_ENCODINGS:
    raise TmxSpecError(f"TMX supports only UTF-8, UTF-16, and US-ASCII, not {match[2]!r}")


def _xml_declaration(prefix: bytes) -> str | None:
  """Decode a declaration prefix using the byte signature, if present.

  Reject UTF-32, UTF-16 without a BOM, and EBCDIC signatures with
  ``TmxSpecError``. Return ``None`` when there is no XML declaration.
  """
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
  """Decode an XML declaration wholly contained in the supplied prefix.

  Return ``None`` if the prefix does not begin with a declaration. An
  unterminated, oversized, or undecodable declaration raises ``TmxSpecError``.
  """
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
  """Raise ``TmxSpecError`` unless the element has the expected namespace-free tag."""
  try:
    qname = etree.QName(element)
  except ValueError as error:
    raise TmxSpecError(f"expected namespace-free <{expected}>, got {element.tag!r}") from error
  if qname.namespace is not None or qname.localname != expected:
    raise TmxSpecError(f"expected namespace-free <{expected}>, got {element.tag!r} at line {element.sourceline}")


def _require_only_xml_whitespace(text: str | None, location: str) -> None:
  """Reject non-XML-whitespace text with an error naming its document location."""
  if text is not None and any(character not in " \t\r\n" for character in text):
    raise TmxSpecError(f"expected only XML whitespace {location}")
