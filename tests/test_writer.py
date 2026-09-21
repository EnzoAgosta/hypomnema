from collections.abc import Iterator
from io import BytesIO, StringIO
from os import PathLike, fsencode
from pathlib import Path

import pytest
from lxml import etree

from hypomnema.errors import TmxErrorGroup, TmxFieldValueError, TmxSpecError
from hypomnema.io import TmxReader, TmxWriter, TuValidationError
from hypomnema.models import Bpt, Ept, Header, TranslationUnit, TranslationUnitVariant
from hypomnema.xml.dtd import load_dtd


def header() -> Header:
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
  return TranslationUnit(
    tuid=tuid,
    variants=[TranslationUnitVariant(xml_lang=lang, content=[text])],
  )


def write_document(
  units: Iterator[TranslationUnit] | list[TranslationUnit] | tuple[TranslationUnit, ...],
) -> bytes:
  destination = BytesIO()
  with TmxWriter(destination, header=header()) as writer:
    for unit in units:
      writer.write(unit)
  return destination.getvalue()


def read_document(data: bytes) -> tuple[Header, list[TranslationUnit]]:
  with TmxReader(BytesIO(data)) as reader:
    parsed_header = reader.read_header()
    return parsed_header, list(reader)


def invalid_unit() -> TranslationUnit:
  unit = translation_unit()
  unit.variants.clear()
  return unit


class BytesPath(PathLike[bytes]):
  def __init__(self, path: Path) -> None:
    self.path = path

  def __fspath__(self) -> bytes:
    return fsencode(self.path)


class BufferedSink:
  """A small network-like sink whose writes are visible only after flush."""

  def __init__(self) -> None:
    self.pending = bytearray()
    self.visible = bytearray()
    self.flush_count = 0

  def write(self, data: bytes, /) -> int:
    self.pending.extend(data)
    return len(data)

  def flush(self) -> None:
    self.visible.extend(self.pending)
    self.pending.clear()
    self.flush_count += 1


class FailOnceOnFlush(BytesIO):
  def __init__(self) -> None:
    super().__init__()
    self.failure = OSError("the destination stopped accepting data")
    self.fail_next_flush = False

  def flush(self) -> None:
    if self.fail_next_flush:
      self.fail_next_flush = False
      raise self.failure
    super().flush()


# Document output


def test_writes_an_empty_dtd_valid_document() -> None:
  data = write_document([])
  root = etree.fromstring(data)

  load_dtd().assertValid(root)
  assert root.tag == "tmx"
  assert root.get("version") == "1.4"
  assert root.find("body") is not None
  assert root.findall("body/tu") == []


def test_round_trips_header_and_translation_units() -> None:
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
  data = write_document([translation_unit()])

  assert data.startswith(b"<?xml version='1.0' encoding='UTF-8'?>\n")
  assert b"<!DOCTYPE" not in data


def test_preserves_translation_unit_order() -> None:
  expected = [translation_unit(tuid=str(index)) for index in range(5)]

  _, actual = read_document(write_document(expected))

  assert [unit.tuid for unit in actual] == [unit.tuid for unit in expected]


def test_round_trips_mixed_inline_content() -> None:
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
  writer = TmxWriter(BytesIO(), header=header())

  with pytest.raises(RuntimeError, match="open TmxWriter context"):
    writer.write(translation_unit())


def test_rejects_write_after_close() -> None:
  writer = TmxWriter(BytesIO(), header=header())
  writer.__enter__()
  writer.close()

  with pytest.raises(RuntimeError, match="open TmxWriter context"):
    writer.write(translation_unit())


def test_writer_can_only_be_entered_once() -> None:
  writer = TmxWriter(BytesIO(), header=header())

  with writer:
    pass

  with pytest.raises(RuntimeError, match="only be entered once"):
    writer.__enter__()


def test_close_is_idempotent() -> None:
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
  class UserFailure(Exception):
    pass

  destination = BytesIO()

  with pytest.raises(UserFailure):
    with TmxWriter(destination, header=header()) as writer:
      writer.write(translation_unit())
      raise UserFailure

  load_dtd().assertValid(etree.fromstring(destination.getvalue()))


@pytest.mark.parametrize("kind", ["str", "bytes", "path", "path-like"])
def test_accepts_path_destinations(tmp_path: Path, kind: str) -> None:
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
  destination = BytesIO()

  with TmxWriter(destination, header=header()) as writer:
    writer.write(translation_unit())

  assert not destination.closed


def test_leaves_borrowed_destination_open_after_early_close() -> None:
  destination = BytesIO()
  writer = TmxWriter(destination, header=header())
  writer.__enter__()

  writer.close()

  assert not destination.closed


def test_rejects_a_text_destination_without_closing_it() -> None:
  destination = StringIO()

  with pytest.raises(TypeError, match="binary"):
    TmxWriter(destination, header=header()).__enter__()  # ty: ignore[invalid-argument-type]

  assert not destination.closed


def test_invalid_header_does_not_truncate_a_path_destination(tmp_path: Path) -> None:
  destination = tmp_path / "document.tmx"
  destination.write_bytes(b"existing contents")
  invalid_header = header()
  invalid_header.adminlang = "not a language tag!"

  with pytest.raises(TmxErrorGroup):
    TmxWriter(destination, header=invalid_header).__enter__()

  assert destination.read_bytes() == b"existing contents"


# Streaming and flushing


def test_flushes_each_complete_stage_to_the_destination() -> None:
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
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    assert destination.flush_count == 1
    writer.write(translation_unit(tuid="one"))
    assert destination.flush_count == 2
    writer.write(translation_unit(tuid="two"))
    assert destination.flush_count == 3

  assert destination.flush_count == 4


def test_only_requires_write_and_flush_from_a_destination() -> None:
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    writer.write(translation_unit())

  _, units = read_document(bytes(destination.visible))
  assert units == [translation_unit()]


# Translation unit validation


def test_invalid_unit_is_not_committed() -> None:
  destination = BufferedSink()

  with TmxWriter(destination, header=header()) as writer:
    before = bytes(destination.visible)

    with pytest.raises(TmxErrorGroup):
      writer.write(invalid_unit())

    assert bytes(destination.visible) == before
    assert destination.pending == b""


def test_writer_remains_usable_after_a_caught_validation_error() -> None:
  destination = BytesIO()

  with TmxWriter(destination, header=header()) as writer:
    with pytest.raises(TmxErrorGroup):
      writer.write(invalid_unit())
    writer.write(translation_unit(tuid="valid"))

  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="valid")]


def test_xml_illegal_text_raises_a_spec_error_without_committing() -> None:
  destination = BufferedSink()
  unit = translation_unit("illegal \x01 text")

  with TmxWriter(destination, header=header()) as writer:
    before = bytes(destination.visible)

    with pytest.raises(TmxSpecError):
      writer.write(unit)

    assert bytes(destination.visible) == before


def test_valid_units_do_not_invoke_the_validation_hook() -> None:
  calls: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  received: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  replacement = translation_unit("Recovered", tuid="replacement")

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    del error, unit
    return replacement

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(invalid_unit())

  _, units = read_document(destination.getvalue())
  assert units == [replacement]


def test_hook_can_repair_and_return_the_original_unit() -> None:
  broken = translation_unit()
  broken.tuid = "not a valid XML name"

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
    assert isinstance(error, TmxErrorGroup)
    unit.tuid = "repaired"
    return unit

  destination = BytesIO()
  with TmxWriter(destination, header=header(), on_tu_validation_error=hook) as writer:
    writer.write(broken)

  _, units = read_document(destination.getvalue())
  assert units == [translation_unit(tuid="repaired")]


def test_hook_can_target_exception_group_leaves_with_except_star() -> None:
  caught: list[TmxFieldValueError] = []
  broken = translation_unit()
  broken.tuid = "not a valid XML name"

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  received: list[TuValidationError] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  calls = 0

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  failure = RuntimeError("hook failed")

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  calls: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
  hook_calls: list[tuple[TuValidationError, TranslationUnit]] = []

  def hook(error: TuValidationError, unit: TranslationUnit) -> TranslationUnit | None:
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
