"""Test streaming TMX output, destination ownership, and unit recovery."""

from collections.abc import Iterator
from io import BytesIO, StringIO
from os import PathLike, fsencode
from pathlib import Path

import pytest
from lxml import etree

from hypomnema.errors import TmxErrorGroup, TmxFieldValueError, TmxSpecError
from hypomnema.io import TmxReader, TmxWriter, TuValidationError
from hypomnema.models import Bpt, Ept, Header, Hi, TranslationUnit, TranslationUnitVariant
from hypomnema.xml.dtd import load_dtd


def header() -> Header:
  """Return a minimal valid English document header."""
  return Header(
    creationtool="hypomnema",
    creationtoolversion="0.1.0",
    segtype="sentence",
    o_tmf="unknown",
    adminlang="en",
    srclang="en",
    datatype="plaintext",
  )


def translation_unit(text: str = "Hello, world!", *, tuid: str = "one", lang: str = "en") -> TranslationUnit:
  """Return a single-variant unit with configurable text, identifier, and language."""
  return TranslationUnit(
    tuid=tuid,
    variants=[TranslationUnitVariant(xml_lang=lang, content=[text])],
  )


def write_document(
  units: Iterator[TranslationUnit] | list[TranslationUnit] | tuple[TranslationUnit, ...],
) -> bytes:
  """Serialize the supplied units into an in-memory TMX document."""
  destination = BytesIO()
  with TmxWriter(destination, header=header()) as writer:
    for unit in units:
      writer.write(unit)
  return destination.getvalue()


def read_document(data: bytes) -> tuple[Header, list[TranslationUnit]]:
  """Read a byte-string document into its header and ordered unit list."""
  with TmxReader(BytesIO(data)) as reader:
    parsed_header = reader.read_header()
    return parsed_header, list(reader)


def invalid_unit() -> TranslationUnit:
  """Return a unit whose required variants list was emptied after construction."""
  unit = translation_unit()
  unit.variants.clear()
  return unit


def test_hook_can_skip_a_unit_with_cyclic_content() -> None:
  """Report cycles through the validation hook and keep the writer usable."""
  hi = Hi()
  hi.content.append(hi)
  cyclic = TranslationUnit(variants=[TranslationUnitVariant(xml_lang="en", content=[hi])])
  errors: list[TuValidationError] = []

  def skip(error: TuValidationError, unit: TranslationUnit) -> None:
    assert unit is cyclic
    errors.append(error)

  output = BytesIO()
  valid = translation_unit()
  with TmxWriter(output, header=header(), on_tu_validation_error=skip) as writer:
    writer.write(cyclic)
    writer.write(valid)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxErrorGroup)
  assert read_document(output.getvalue())[1] == [valid]


class BytesPath(PathLike[bytes]):
  """Expose a pathlib path as bytes through the PathLike protocol."""

  def __init__(self, path: Path) -> None:
    """Retain the path to encode when the filesystem protocol is called."""
    self.path = path

  def __fspath__(self) -> bytes:
    """Encode the stored path with the platform filesystem encoding."""
    return fsencode(self.path)


class BufferedSink:
  """A small network-like sink whose writes are visible only after flush."""

  def __init__(self) -> None:
    """Initialize empty pending and visible buffers and a zero flush count."""
    self.pending = bytearray()
    self.visible = bytearray()
    self.flush_count = 0

  def write(self, data: bytes, /) -> int:
    """Append bytes to the pending buffer and report the accepted byte count."""
    self.pending.extend(data)
    return len(data)

  def flush(self) -> None:
    """Publish pending bytes, empty the pending buffer, and count the flush."""
    self.visible.extend(self.pending)
    self.pending.clear()
    self.flush_count += 1


class FailOnceOnFlush(BytesIO):
  """Simulate a borrowed sink with an explicitly armed, one-shot flush failure."""

  def __init__(self) -> None:
    """Create the reusable failure instance with flush failure initially disabled."""
    super().__init__()
    self.failure = OSError("the destination stopped accepting data")
    self.fail_next_flush = False

  def flush(self) -> None:
    """Raise the prepared OSError once when armed, then resume normal flushing."""
    if self.fail_next_flush:
      self.fail_next_flush = False
      raise self.failure
    super().flush()


# Document output


def test_writes_an_empty_dtd_valid_document() -> None:
  """Write a DTD-valid TMX 1.4 document with an empty body."""
  data = write_document([])
  root = etree.fromstring(data)

  load_dtd().assertValid(root)
  assert root.tag == "tmx"
  assert root.get("version") == "1.4"
  assert root.find("body") is not None
  assert root.findall("body/tu") == []


def test_round_trips_header_and_translation_units() -> None:
  """Preserve the header and unit models through writing and reading."""
  expected_header = header()
  expected_units = [
    translation_unit("Hello", tuid="first", lang="en"),
    translation_unit("Bonjour", tuid="second", lang="fr"),
  ]
  destination = BytesIO()

  with TmxWriter(destination, header=expected_header) as writer:
    for unit in expected_units:
      writer.write(unit)

  actual_header, actual_units = read_document(destination.getvalue())
  assert actual_header == expected_header
  assert actual_units == expected_units


def test_writes_utf8_xml_without_a_doctype() -> None:
  """Emit a UTF-8 XML declaration and omit a document type declaration."""
  data = write_document([translation_unit()])

  assert data.startswith(b"<?xml version='1.0' encoding='UTF-8'?>\n")
  assert b"<!DOCTYPE" not in data


def test_preserves_translation_unit_order() -> None:
  """Serialize units in the same order they are supplied to write."""
  expected = [translation_unit(tuid=str(index)) for index in range(5)]

  _, actual = read_document(write_document(expected))

  assert [unit.tuid for unit in actual] == [unit.tuid for unit in expected]


def test_round_trips_mixed_inline_content() -> None:
  """Preserve text and paired inline codes through a document round trip."""
  unit = TranslationUnit(
    tuid="inline",
    variants=[
      TranslationUnitVariant(
        xml_lang="en",
        content=[
          "The ",
          Bpt(i=1, x=1, content=["<strong>"]),
          "important part",
          Ept(i=1, content=["</strong>"]),
          ".",
        ],
      )
    ],
  )

  _, actual = read_document(write_document([unit]))

  assert actual == [unit]


# Lifecycle and destination ownership


def test_rejects_write_before_entry() -> None:
  """Reject writes before the writer context has opened."""
  writer = TmxWriter(BytesIO(), header=header())

  with pytest.raises(RuntimeError, match="open TmxWriter context"):
    writer.write(translation_unit())


def test_rejects_write_after_close() -> None:
  """Reject writes after the writer has closed its XML document."""
  writer = TmxWriter(BytesIO(), header=header())
  writer.__enter__()
  writer.close()

  with pytest.raises(RuntimeError, match="open TmxWriter context"):
    writer.write(translation_unit())


def test_writer_can_only_be_entered_once() -> None:
  """Reject reentry after a writer context has completed."""
  writer = TmxWriter(BytesIO(), header=header())

  with writer:
    pass

  with pytest.raises(RuntimeError, match="only be entered once"):
    writer.__enter__()


def test_close_is_idempotent() -> None:
  """Write closing tags only once and leave a DTD-valid document."""
  destination = BytesIO()
  writer = TmxWriter(destination, header=header())
  writer.__enter__()
  writer.write(translation_unit())

  writer.close()
  data_after_first_close = destination.getvalue()
  writer.close()

  assert destination.getvalue() == data_after_first_close
  load_dtd().assertValid(etree.fromstring(data_after_first_close))


def test_context_exit_closes_xml_scopes_when_user_code_raises() -> None:
  """Finish the XML document while propagating an exception from user code."""

  class UserFailure(Exception):
    """Identify the user exception whose propagation the context must preserve."""

    pass

  destination = BytesIO()

  with pytest.raises(UserFailure):
    with TmxWriter(destination, header=header()) as writer:
      writer.write(translation_unit())
      raise UserFailure

  load_dtd().assertValid(etree.fromstring(destination.getvalue()))


@pytest.mark.parametrize("kind", ["str", "bytes", "path", "path-like"])
def test_accepts_path_destinations(tmp_path: Path, kind: str) -> None:
  """Write documents to strings, bytes, and both PathLike representations."""
  path = tmp_path / "document.tmx"
  destinations: dict[str, str | bytes | Path | BytesPath] = {
    "str": str(path),
    "bytes": fsencode(path),
    "path": path,
    "path-like": BytesPath(path),
  }

  with TmxWriter(destinations[kind], header=header()) as writer:
    writer.write(translation_unit())

  _, units = read_document(path.read_bytes())
  assert units == [translation_unit()]


def test_leaves_borrowed_destination_open_after_context_exit() -> None:
  """Keep a caller-owned destination open after the writer context exits."""
  destination = BytesIO()

  with TmxWriter(destination, header=header()) as writer:
    writer.write(translation_unit())

  assert not destination.closed


def test_leaves_borrowed_destination_open_after_early_close() -> None:
  """Keep a caller-owned destination open after an explicit early close."""
  destination = BytesIO()
  writer = TmxWriter(destination, header=header())
  writer.__enter__()

  writer.close()

  assert not destination.closed


def test_rejects_a_text_destination_without_closing_it() -> None:
  """Reject text destinations without closing the caller's stream."""
  destination = StringIO()

  with pytest.raises(TypeError, match="binary"):
    TmxWriter(destination, header=header()).__enter__()  # ty: ignore[invalid-argument-type]

  assert not destination.closed


def test_invalid_header_does_not_truncate_a_path_destination(tmp_path: Path) -> None:
  """Validate the header before opening and truncating an existing path."""
  destination = tmp_path / "document.tmx"
  destination.write_bytes(b"existing contents")
  invalid_header = header()
  invalid_header.adminlang = "not a language tag!"

  with pytest.raises(TmxErrorGroup):
    TmxWriter(destination, header=invalid_header).__enter__()

  assert destination.read_bytes() == b"existing contents"


# Streaming and flushing


def test_flushes_each_complete_stage_to_the_destination() -> None:
  """Make the header, each whole unit, and closing tags visible after flushing."""
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    after_entry = bytes(destination.visible)
    assert after_entry.endswith(b"<body>")
    assert destination.pending == b""

    writer.write(translation_unit())
    after_write = bytes(destination.visible)
    assert after_write.startswith(after_entry)
    assert after_write.endswith(b"</tu>")
    assert destination.pending == b""

  assert bytes(destination.visible).endswith(b"</body></tmx>")
  assert destination.pending == b""


def test_flushes_once_for_entry_each_unit_and_close() -> None:
  """Flush the destination once per entry, unit write, and close."""
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    assert destination.flush_count == 1
    writer.write(translation_unit(tuid="one"))
    assert destination.flush_count == 2
    writer.write(translation_unit(tuid="two"))
    assert destination.flush_count == 3

  assert destination.flush_count == 4


def test_only_requires_write_and_flush_from_a_destination() -> None:
  """Accept a binary sink that supplies only write and flush methods."""
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    writer.write(translation_unit())

  _, units = read_document(bytes(destination.visible))
  assert units == [translation_unit()]


# Translation unit validation


def test_invalid_unit_is_not_committed() -> None:
  """Leave both sink buffers unchanged when unit validation fails."""
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    before = bytes(destination.visible)

    with pytest.raises(TmxErrorGroup):
      writer.write(invalid_unit())

    assert bytes(destination.visible) == before
    assert destination.pending == b""


def test_writer_remains_usable_after_a_caught_validation_error() -> None:
  """Allow a valid write after the caller catches a unit validation failure."""
  destination = BytesIO()

  with TmxWriter(destination, header=header()) as writer:
    with pytest.raises(TmxErrorGroup):
      writer.write(invalid_unit())
    writer.write(translation_unit(tuid="valid"))

  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="valid")]


def test_xml_illegal_text_raises_a_spec_error_without_committing() -> None:
  """Reject XML-illegal segment text before any unit bytes become visible."""
  destination = BufferedSink()
  unit = translation_unit("illegal \x01 text")

  with TmxWriter(destination, header=header()) as writer:
    before = bytes(destination.visible)

    with pytest.raises(TmxSpecError):
      writer.write(unit)

    assert bytes(destination.visible) == before


def test_valid_units_do_not_invoke_the_validation_hook() -> None:
  """Write valid units without invoking the validation recovery hook."""
  calls: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Record unexpected recovery calls and return the skip sentinel."""
    calls.append((error, unit))
    return None

  destination = BytesIO()
  expected = translation_unit()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(expected)

  assert calls == []
  _, units = read_document(destination.getvalue())
  assert units == [expected]


# Validation recovery hook


def test_hook_receives_the_error_and_original_unit_and_can_skip_it() -> None:
  """Pass the original unit and error to a hook that skips the failed write."""
  received: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Record the exact error and unit received, then skip the unit."""
    received.append((error, unit))
    return None

  broken = invalid_unit()
  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(broken)
    writer.write(translation_unit(tuid="later"))

  assert len(received) == 1
  error, unit = received[0]
  assert isinstance(error, TmxErrorGroup)
  assert unit is broken
  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="later")]


def test_hook_can_replace_an_invalid_unit() -> None:
  """Validate and write a replacement model returned by the recovery hook."""
  replacement = translation_unit("Recovered", tuid="replacement")

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Return the prepared replacement for the invalid unit."""
    del error, unit
    return replacement

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(invalid_unit())

  _, units = read_document(destination.getvalue())
  assert units == [replacement]


def test_hook_can_repair_and_return_the_original_unit() -> None:
  """Allow a hook to repair the failed model in place and return it for writing."""
  broken = translation_unit()
  broken.tuid = "not a valid XML name"

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Replace the malformed identifier on the original model and return it."""
    assert isinstance(error, TmxErrorGroup)
    unit.tuid = "repaired"
    return unit

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(broken)

  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="repaired")]


def test_hook_can_target_exception_group_leaves_with_except_star() -> None:
  """Allow selective field-error handling inside a writer recovery hook."""
  caught: list[TmxFieldValueError] = []
  broken = translation_unit()
  broken.tuid = "not a valid XML name"

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Collect value-error leaves and repair the identifier they rejected."""
    try:
      raise error
    except* TmxFieldValueError as matching:
      caught.extend(leaf for leaf in matching.exceptions if isinstance(leaf, TmxFieldValueError))
      unit.tuid = "repaired"
    return unit

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(broken)

  assert caught
  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="repaired")]


def test_hook_receives_spec_errors() -> None:
  """Recover XML projection failures through the same unit validation hook."""
  received: list[TuValidationError] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Record the projection error and return legal text under the same identifier."""
    received.append(error)
    return translation_unit("Recovered", tuid=unit.tuid or "recovered")

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(translation_unit("illegal \x01 text", tuid="original"))

  assert len(received) == 1
  assert isinstance(received[0], TmxSpecError)
  _, units = read_document(destination.getvalue())
  assert units == [translation_unit("Recovered", tuid="original")]


def test_invalid_replacement_is_rejected_without_invoking_hook_again() -> None:
  """Reject an invalid replacement once while leaving later writes possible."""
  calls = 0

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Count the recovery attempt and return another invalid unit."""
    nonlocal calls
    del error, unit
    calls += 1
    return invalid_unit()

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    with pytest.raises(TmxErrorGroup):
      writer.write(invalid_unit())
    writer.write(translation_unit(tuid="later"))

  assert calls == 1
  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="later")]


def test_hook_exception_propagates_without_poisoning_the_writer() -> None:
  """Propagate a hook failure and permit the caller to write a later valid unit."""
  failure = RuntimeError("hook failed")

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Raise the prepared exception to interrupt unit recovery."""
    del error, unit
    raise failure

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    with pytest.raises(RuntimeError) as raised:
      writer.write(invalid_unit())
    assert raised.value is failure
    writer.write(translation_unit(tuid="later"))

  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="later")]


def test_header_validation_bypasses_the_unit_hook() -> None:
  """Reject an invalid header before output without invoking unit recovery."""
  calls: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Record unexpected recovery attempts during header validation."""
    calls.append((error, unit))
    return None

  invalid_header = header()
  invalid_header.adminlang = "not a language tag!"
  destination = BytesIO()

  with pytest.raises(TmxErrorGroup):
    TmxWriter(
      destination,
      header=invalid_header,
      on_tu_validation_error=hook,
    ).__enter__()

  assert calls == []
  assert destination.getvalue() == b""


# Destination failures


def test_flush_failure_bypasses_hook_and_poisons_writer() -> None:
  """Propagate destination failure and reject further writes without recovery."""
  hook_calls: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    """Record unexpected unit-recovery calls after a destination failure."""
    hook_calls.append((error, unit))
    return None

  destination = FailOnceOnFlush()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    destination.fail_next_flush = True

    with pytest.raises(OSError) as raised:
      writer.write(translation_unit())

    assert raised.value is destination.failure
    with pytest.raises(RuntimeError, match="cannot continue"):
      writer.write(translation_unit(tuid="later"))

  assert hook_calls == []
  assert not destination.closed
