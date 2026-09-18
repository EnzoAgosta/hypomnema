"""Behavioral tests for the streaming TMX reader."""

import codecs
from io import BytesIO, StringIO
from os import PathLike, fsencode
from pathlib import Path

import pytest
from lxml import etree

from hypomnema.errors import TmxSpecError
from hypomnema.io import TmxReader, TmxSource
from hypomnema.models import Header, TranslationUnit, TranslationUnitVariant
from hypomnema.xml.names import XML_LANG
from hypomnema.xml.parse import tu_from_element

HEADER = (
  '<header creationtool="test" creationtoolversion="1.0" segtype="sentence"'
  ' o-tmf="tmf" adminlang="en" srclang="EN" datatype="plaintext"/>'
)


def translation_unit(tuid: str, text: str = "text", *, language: str | None = "en") -> str:
  language_attribute = f' xml:lang="{language}"' if language is not None else ""
  return f'<tu tuid="{tuid}"><tuv{language_attribute}><seg>{text}</seg></tuv></tu>'


def document(
  body: str = "",
  *,
  header: str = HEADER,
  root_attributes: str = 'version="1.4"',
  before_header: str = "",
  between_header_and_body: str = "",
  body_attributes: str = "",
  after_body: str = "",
) -> str:
  body_open = f"<body{body_attributes}>"
  return (
    f"<tmx {root_attributes}>{before_header}{header}{between_header_and_body}{body_open}{body}</body>{after_body}</tmx>"
  )


def read_document(source: TmxSource) -> tuple[Header, list[TranslationUnit]]:
  with TmxReader(source) as reader:
    header = reader.read_header()
    return header, list(reader)


class BytesPath(PathLike[bytes]):
  def __init__(self, path: bytes) -> None:
    self.path = path

  def __fspath__(self) -> bytes:
    return self.path


class NonSeekableBytesIO(BytesIO):
  def seekable(self) -> bool:
    return False


# Normal reading and lifecycle.


def test_header_peek_starts_empty() -> None:
  reader = TmxReader(BytesIO(document().encode()))
  assert reader.header_peek is None


def test_reader_peeks_header_then_projects_header_and_units() -> None:
  source = BytesIO(document(translation_unit("one", "first") + translation_unit("two", "second")).encode())
  reader = TmxReader(source)

  with reader:
    header_peek = reader.header_peek
    assert header_peek is not None
    assert header_peek["srclang"] == "EN"
    header = reader.read_header()
    units = list(reader)

  assert header.srclang == "en"
  assert [unit.tuid for unit in units] == ["one", "two"]
  assert [unit.variants[0].content for unit in units] == [["first"], ["second"]]


def test_empty_body_is_an_empty_iterator() -> None:
  reader = TmxReader(BytesIO(document().encode()))
  with reader:
    reader.read_header()
    assert list(reader) == []
    with pytest.raises(StopIteration):
      next(reader)
    with pytest.raises(StopIteration):
      next(reader)


def test_iter_returns_the_reader_before_and_after_entry() -> None:
  reader = TmxReader(BytesIO(document().encode()))
  assert iter(reader) is reader
  with reader:
    assert iter(reader) is reader


def test_next_before_entry_is_rejected() -> None:
  with pytest.raises(RuntimeError, match="read_header"):
    next(TmxReader(BytesIO(document().encode())))


def test_read_header_before_entry_is_rejected() -> None:
  with pytest.raises(RuntimeError, match="after entering"):
    TmxReader(BytesIO(document().encode())).read_header()


def test_next_before_reading_header_is_rejected() -> None:
  with TmxReader(BytesIO(document().encode())) as reader:
    with pytest.raises(RuntimeError, match="read_header"):
      next(reader)


def test_header_can_only_be_read_once() -> None:
  with TmxReader(BytesIO(document().encode())) as reader:
    reader.read_header()
    with pytest.raises(RuntimeError, match="called once"):
      reader.read_header()


def test_reader_can_only_be_entered_once() -> None:
  reader = TmxReader(BytesIO(document().encode()))
  with reader:
    reader.read_header()
  with pytest.raises(RuntimeError, match="entered once"):
    reader.__enter__()


def test_close_is_idempotent() -> None:
  source = BytesIO(document().encode())
  reader = TmxReader(source)
  reader.__enter__()
  reader.close()
  reader.close()
  assert not source.closed


def test_valid_units_are_yielded_before_a_later_projection_error() -> None:
  body = translation_unit("valid") + translation_unit("broken", language=None)
  with TmxReader(BytesIO(document(body).encode())) as reader:
    reader.read_header()
    assert next(reader).tuid == "valid"
    with pytest.raises(TmxSpecError):
      next(reader)


# Path and stream sources.


def test_path_source_types_are_accepted(tmp_path: Path) -> None:
  path = tmp_path / "memory.tmx"
  path.write_bytes(document(translation_unit("one")).encode())
  sources: dict[str, TmxSource] = {
    "str": str(path),
    "bytes": fsencode(path),
    "str-pathlike": path,
    "bytes-pathlike": BytesPath(fsencode(path)),
  }

  for source_kind, source in sources.items():
    _, units = read_document(source)
    assert [unit.tuid for unit in units] == ["one"], source_kind


def test_missing_path_propagates_file_not_found(tmp_path: Path) -> None:
  with pytest.raises(FileNotFoundError):
    TmxReader(tmp_path / "missing.tmx").__enter__()


def test_borrowed_stream_remains_open_after_exhaustion() -> None:
  source = BytesIO(document().encode())
  read_document(source)
  assert not source.closed


def test_borrowed_stream_remains_open_after_early_close() -> None:
  source = BytesIO(document(translation_unit("one")).encode())
  with TmxReader(source) as reader:
    reader.read_header()
  assert not source.closed


def test_borrowed_stream_remains_open_after_entry_error() -> None:
  source = BytesIO(b"<wrong/>")
  with pytest.raises(TmxSpecError):
    TmxReader(source).__enter__()
  assert not source.closed


def test_text_stream_is_rejected_without_being_closed() -> None:
  source = StringIO(document())
  with pytest.raises(TypeError, match="binary mode"):
    TmxReader(source).__enter__()  # ty: ignore[invalid-argument-type]
  assert not source.closed


def test_non_seekable_stream_is_rejected_without_being_closed() -> None:
  source = NonSeekableBytesIO(document().encode())
  with pytest.raises(ValueError, match="seekable"):
    TmxReader(source).__enter__()
  assert not source.closed


def test_stream_past_byte_zero_is_rejected_without_being_closed() -> None:
  source = BytesIO(document().encode())
  source.seek(1)
  with pytest.raises(ValueError, match="byte zero"):
    TmxReader(source).__enter__()
  assert not source.closed


# Character encodings.


PLAIN_DOCUMENT = document(translation_unit("one"))

VALID_ENCODINGS = (
  pytest.param(PLAIN_DOCUMENT.encode(), id="implicit-utf8"),
  pytest.param(('<?xml version="1.0" encoding="uTf-8"?>' + PLAIN_DOCUMENT).encode(), id="declared-utf8"),
  pytest.param(('<?xml\nversion="1.0"\nencoding="UTF-8"?>' + PLAIN_DOCUMENT).encode(), id="multiline-declaration"),
  pytest.param(codecs.BOM_UTF8 + PLAIN_DOCUMENT.encode(), id="utf8-bom"),
  pytest.param(('<?xml version="1.0" encoding="US-ASCII"?>' + PLAIN_DOCUMENT).encode("ascii"), id="us-ascii"),
  pytest.param(
    codecs.BOM_UTF16_LE + ('<?xml version="1.0" encoding="UTF-16"?>' + PLAIN_DOCUMENT).encode("utf-16-le"),
    id="utf16-le",
  ),
  pytest.param(
    codecs.BOM_UTF16_BE + ('<?xml version="1.0" encoding="UTF-16"?>' + PLAIN_DOCUMENT).encode("utf-16-be"),
    id="utf16-be",
  ),
  pytest.param(codecs.BOM_UTF16_LE + PLAIN_DOCUMENT.encode("utf-16-le"), id="implicit-utf16-le"),
  pytest.param(codecs.BOM_UTF16_BE + PLAIN_DOCUMENT.encode("utf-16-be"), id="implicit-utf16-be"),
)


@pytest.mark.parametrize("encoded_document", VALID_ENCODINGS)
def test_supported_document_encodings_are_accepted(encoded_document: bytes) -> None:
  _, units = read_document(BytesIO(encoded_document))
  assert [unit.tuid for unit in units] == ["one"]


@pytest.mark.parametrize(
  ("encoded_document", "message"),
  [
    pytest.param(
      ('<?xml version="1.0" encoding="ISO-8859-1"?>' + PLAIN_DOCUMENT).encode("iso-8859-1"),
      "ISO-8859-1",
      id="iso-8859-1",
    ),
    pytest.param(codecs.BOM_UTF32_LE + PLAIN_DOCUMENT.encode("utf-32-le"), "UTF-32", id="utf32-le"),
    pytest.param(codecs.BOM_UTF32_BE + PLAIN_DOCUMENT.encode("utf-32-be"), "UTF-32", id="utf32-be"),
    pytest.param(PLAIN_DOCUMENT.encode("utf-16-le"), "byte-order mark", id="bomless-utf16-le"),
    pytest.param(PLAIN_DOCUMENT.encode("utf-16-be"), "byte-order mark", id="bomless-utf16-be"),
    pytest.param(
      ('<?xml version="1.0" encoding="IBM037"?>' + PLAIN_DOCUMENT).encode("cp037"),
      "supports only",
      id="ebcdic",
    ),
  ],
)
def test_unsupported_document_encodings_are_rejected(encoded_document: bytes, message: str) -> None:
  with pytest.raises(TmxSpecError, match=message):
    TmxReader(BytesIO(encoded_document)).__enter__()


def test_oversized_xml_declaration_is_rejected() -> None:
  declaration = "<?xml " + " " * 1024 + 'version="1.0"?>'
  with pytest.raises(TmxSpecError, match="exceeds 1024 bytes"):
    TmxReader(BytesIO((declaration + PLAIN_DOCUMENT).encode())).__enter__()


def test_unterminated_xml_declaration_is_rejected() -> None:
  with pytest.raises(TmxSpecError, match="not terminated"):
    TmxReader(BytesIO(b'<?xml version="1.0" encoding="UTF-8"')).__enter__()


def test_malformed_xml_declaration_is_reported_as_malformed_xml() -> None:
  malformed = b'<?xml encoding="UTF-8" version="1.0"?>' + PLAIN_DOCUMENT.encode()
  with pytest.raises(TmxSpecError, match="malformed XML"):
    TmxReader(BytesIO(malformed)).__enter__()


def test_declared_encoding_must_match_actual_bytes() -> None:
  mismatched = ('<?xml version="1.0" encoding="UTF-16"?>' + PLAIN_DOCUMENT).encode()
  with pytest.raises(TmxSpecError, match="malformed XML"):
    TmxReader(BytesIO(mismatched)).__enter__()


# Document structure owned by the reader.


INVALID_DOCUMENTS = (
  pytest.param("<wrong/>", id="wrong-root"),
  pytest.param('<tmx version="1.3"></tmx>', id="wrong-version"),
  pytest.param('<tmx version="1.4" extra="x"></tmx>', id="extra-root-attribute"),
  pytest.param('<tmx xmlns="urn:tmx" version="1.4"></tmx>', id="namespaced-root"),
  pytest.param('<tmx version="1.4"><body/></tmx>', id="missing-header"),
  pytest.param(f'<tmx version="1.4"><body/>{HEADER}</tmx>', id="body-before-header"),
  pytest.param(f'<tmx version="1.4">{HEADER}</tmx>', id="missing-body"),
  pytest.param(f'<tmx version="1.4">{HEADER}{HEADER}<body/></tmx>', id="duplicate-header"),
  pytest.param(document(body_attributes=' extra="x"'), id="body-attribute"),
  pytest.param(document("<junk/>"), id="unexpected-body-child"),
  pytest.param(
    document(header=HEADER.replace(' creationtool="test"', "")),
    id="invalid-header-fragment",
  ),
)


@pytest.mark.parametrize("xml", INVALID_DOCUMENTS)
def test_invalid_document_structure_is_rejected(xml: str) -> None:
  with pytest.raises(TmxSpecError):
    with TmxReader(BytesIO(xml.encode())) as reader:
      reader.read_header()
      list(reader)


@pytest.mark.parametrize(
  "xml",
  [
    pytest.param(document(before_header="text"), id="before-header"),
    pytest.param(document(between_header_and_body="text"), id="between-header-and-body"),
    pytest.param(document("text"), id="empty-body-text"),
    pytest.param(document("text" + translation_unit("one")), id="before-first-tu"),
    pytest.param(document(translation_unit("one") + "text" + translation_unit("two")), id="between-tus"),
    pytest.param(document(after_body="text"), id="after-body"),
  ],
)
def test_non_whitespace_structural_text_is_rejected(xml: str) -> None:
  with pytest.raises(TmxSpecError, match="XML whitespace"):
    with TmxReader(BytesIO(xml.encode())) as reader:
      reader.read_header()
      list(reader)


def test_comments_and_processing_instructions_are_ignored_without_losing_text() -> None:
  xml = (
    '<?xml version="1.0"?><!-- before root --><?before root?>'
    '<tmx version="1.4"><!-- before header -->'
    + HEADER
    + "<?between nodes?><!-- before body --><body>"
    + "<!-- before tu -->"
    + translation_unit("one", "before<!-- inside seg --><?inside seg?>after")
    + "<?after tu?><!-- after tu --></body></tmx>"
  )
  _, units = read_document(BytesIO(xml.encode()))
  assert units[0].variants[0].content == ["beforeafter"]


@pytest.mark.parametrize(
  "xml",
  [
    pytest.param(f'<tmx version="1.4">{HEADER}<body>', id="truncated"),
    pytest.param(document() + "<extra/>", id="extra-root"),
    pytest.param(f'<tmx version="1.4">{HEADER}<body><tu></body></tmx>', id="mismatched-tags"),
  ],
)
def test_malformed_xml_is_wrapped_as_a_spec_error(xml: str) -> None:
  with pytest.raises(TmxSpecError, match="malformed XML|unexpected end"):
    with TmxReader(BytesIO(xml.encode())) as reader:
      reader.read_header()
      list(reader)


# Translation-unit recovery hook.


BROKEN_TU = translation_unit("broken", "repair me", language=None)
VALID_TU = translation_unit("valid", "keep me")


def test_tu_creation_error_is_fatal_without_a_hook() -> None:
  with TmxReader(BytesIO(document(BROKEN_TU).encode())) as reader:
    reader.read_header()
    with pytest.raises(TmxSpecError):
      next(reader)


def test_hook_can_skip_a_bad_tu_and_continue() -> None:
  errors: list[TmxSpecError] = []

  def skip(error: TmxSpecError, element: etree._Element) -> None:
    errors.append(error)
    assert element.get("tuid") == "broken"
    return None

  with TmxReader(BytesIO(document(BROKEN_TU + VALID_TU).encode()), on_tu_creation_error=skip) as reader:
    reader.read_header()
    units = list(reader)

  assert [unit.tuid for unit in units] == ["valid"]
  assert len(errors) == 1


def test_hook_can_return_a_replacement_tu() -> None:
  replacement = TranslationUnit(
    tuid="replacement",
    variants=[TranslationUnitVariant(xml_lang="en", content=["replacement text"])],
  )

  def replace(error: TmxSpecError, element: etree._Element) -> TranslationUnit:
    del error, element
    return replacement

  with TmxReader(BytesIO(document(BROKEN_TU).encode()), on_tu_creation_error=replace) as reader:
    reader.read_header()
    assert list(reader) == [replacement]


def test_hook_can_repair_and_reproject_the_element() -> None:
  def repair(error: TmxSpecError, element: etree._Element) -> TranslationUnit:
    del error
    variant = element.find("tuv")
    assert variant is not None
    variant.set(XML_LANG, "en")
    return tu_from_element(element)

  with TmxReader(BytesIO(document(BROKEN_TU).encode()), on_tu_creation_error=repair) as reader:
    reader.read_header()
    unit = next(reader)

  assert unit.tuid == "broken"
  assert unit.variants[0].xml_lang == "en"


def test_handled_element_is_cleared_after_the_hook_returns() -> None:
  elements: list[etree._Element] = []

  def skip(error: TmxSpecError, element: etree._Element) -> None:
    del error
    elements.append(element)
    return None

  with TmxReader(BytesIO(document(BROKEN_TU).encode()), on_tu_creation_error=skip) as reader:
    reader.read_header()
    assert list(reader) == []

  assert elements[0].attrib == {}
  assert len(elements[0]) == 0


def test_hook_exception_propagates() -> None:
  failure = RuntimeError("hook failed")

  def fail(error: TmxSpecError, element: etree._Element) -> None:
    del error, element
    raise failure

  with TmxReader(BytesIO(document(BROKEN_TU).encode()), on_tu_creation_error=fail) as reader:
    reader.read_header()
    with pytest.raises(RuntimeError, match="hook failed") as raised:
      next(reader)
  assert raised.value is failure


@pytest.mark.parametrize(
  "xml",
  [
    pytest.param(document("<junk/>"), id="body-structure"),
    pytest.param(document(header=HEADER.replace(' creationtool="test"', "")), id="header-projection"),
  ],
)
def test_non_tu_errors_bypass_the_hook(xml: str) -> None:
  calls = 0

  def skip(error: TmxSpecError, element: etree._Element) -> None:
    nonlocal calls
    del error, element
    calls += 1
    return None

  with pytest.raises(TmxSpecError):
    with TmxReader(BytesIO(xml.encode()), on_tu_creation_error=skip) as reader:
      reader.read_header()
      list(reader)
  assert calls == 0
