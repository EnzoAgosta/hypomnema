"""Value contracts of the coercion layer: unsigned numbers, the
ValidationError boundary, and fromisoformat-bounded datetimes.

Expectations are explicit examples with asserted values, not echoes of the
implementation's own round trips. The datetime examples derive their
boundaries from datetime.fromisoformat's measured behavior on Python 3.14
(date-only detection, any-character separator, 24:00 normalization,
sub-microsecond truncation, offsets with seconds), not from a re-reading of
ISO 8601: the policy is deliberately bounded to that parser.

Every adapter is built from an alias imported from ``models.py`` -- the
same object the field annotations use, so an adapter cannot drift from the
field it mirrors. An alias that does not exist yet is a reason to create
one, not to hand-build the annotation here.
"""

import warnings
from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from hypomnema.coercion import format_datetime, format_hex_integer, parse_datetime, parse_hex_integer, parse_integer
from hypomnema.models import (
  AsciiText,
  Association,
  Datetime,
  EncodingName,
  HexInteger,
  Integer,
  LanguageTag,
  Position,
  SegType,
  SourceLanguage,
  Tuid,
  UnicodeCodePoint,
)

STRICT = ConfigDict(strict=True, validation_error_cause=True)

INTEGER = TypeAdapter(Integer, config=STRICT)
DATETIME = TypeAdapter(Datetime, config=STRICT)
HEX_INTEGER = TypeAdapter(HexInteger, config=STRICT)
CODE_POINT = TypeAdapter(UnicodeCodePoint, config=STRICT)
IDENTIFIER = TypeAdapter(Tuid, config=STRICT)
LANGUAGE_TAG = TypeAdapter(LanguageTag, config=STRICT)
SOURCE_LANGUAGE = TypeAdapter(SourceLanguage, config=STRICT)
ENCODING = TypeAdapter(EncodingName, config=STRICT)
SEG_TYPE = TypeAdapter(SegType, config=STRICT)
POS = TypeAdapter(Position, config=STRICT)
ASSOC = TypeAdapter(Association, config=STRICT)
ASCII_TEXT = TypeAdapter(AsciiText, config=STRICT)


ACCEPTED_INTEGERS = (
  ("42", 42),
  ("0042", 42),  # leading zeros accepted, spelling not retained
  ("0", 0),
  ("000", 0),
  ("9" * 50, int("9" * 50)),
  (42, 42),
  (0, 0),
  (2**64, 2**64),
)


@pytest.mark.parametrize(("value", "expected"), ACCEPTED_INTEGERS)
def test_parse_integer_accepts_unsigned_decimal(value: object, expected: int) -> None:
  assert parse_integer(value) == expected
  assert INTEGER.validate_python(value) == expected


REJECTED_INTEGERS = (
  # Native forms outside the unsigned domain.
  True,
  False,
  -1,
  1.5,
  42.0,  # a float is rejected even when it is integral
  # int() conveniences and signs are not decimal digits.
  " 42",
  "42 ",
  "+42",
  "-42",
  "4_2",
  "0x10",
  "12.5",
  # Unicode digits are not ASCII digits, e.g. Arabic-Indic and fullwidth.
  "٤٢",
  "４２",
  "①",
  # Other types.
  "",
  "abc",
  None,
  b"42",
  [],
  {},
)


@pytest.mark.parametrize("value", REJECTED_INTEGERS)
def test_parse_integer_rejects_everything_outside_the_domain(value: object) -> None:
  with pytest.raises(ValueError):
    parse_integer(value)
  with pytest.raises(ValidationError):
    INTEGER.validate_python(value)


def test_format_integer_renders_canonical_decimal_digits() -> None:
  # Leading zeros are accepted by the parser but not retained by the format.
  assert str(parse_integer("0042")) == "42"


ACCEPTED_HEX_INTEGERS = (
  ("#xF8FF", 0xF8FF),
  ("#xf8ff", 0xF8FF),  # digits are case-insensitive
  ("#x00E9", 0xE9),  # leading zeros accepted, spelling not retained
  ("#x0", 0),
  ("#x10FFFF", 0x10FFFF),
  ("#" + "x" + "F" * 20, 0xFFFFFFFFFFFFFFFFFFFF),
  (0xF8FF, 0xF8FF),
  (0, 0),
)


@pytest.mark.parametrize(("value", "expected"), ACCEPTED_HEX_INTEGERS)
def test_parse_hex_integer_accepts_prefixed_hexadecimal(value: object, expected: int) -> None:
  assert parse_hex_integer(value) == expected
  assert HEX_INTEGER.validate_python(value) == expected


REJECTED_HEX_INTEGERS = (
  # Native forms outside the unsigned domain.
  True,
  False,
  -1,
  1.5,
  # Prefix and digit strictness: no 0x, no sign, no whitespace, no junk.
  "0xF8FF",
  "F8FF",
  "#X10",  # the prefix itself is lowercase '#x'
  "#x",
  "#x ",
  "#x 10",
  " #x10",
  "#x10 ",
  "#x-1",
  "#x+1",
  "#xG1",
  "１０",  # fullwidth digits are not ASCII hex digits
  None,
  b"#xF8FF",
  [],
)


@pytest.mark.parametrize("value", REJECTED_HEX_INTEGERS)
def test_parse_hex_integer_rejects_everything_outside_the_domain(value: object) -> None:
  with pytest.raises(ValueError):
    parse_hex_integer(value)
  with pytest.raises(ValidationError):
    HEX_INTEGER.validate_python(value)


@pytest.mark.parametrize(
  ("value", "expected"), [(0, "#x0"), (0xE9, "#xE9"), (0xF8FF, "#xF8FF"), (0x10FFFF, "#x10FFFF")]
)
def test_format_hex_integer_keeps_the_prefix_and_uppercases_digits(value: int, expected: str) -> None:
  assert format_hex_integer(value) == expected


ACCEPTED_CODE_POINTS = (
  ("#x0", 0),
  ("#xD7FF", 0xD7FF),
  ("#xE000", 0xE000),  # private use is a valid scalar value
  ("#xF8FF", 0xF8FF),
  ("#x10FFFF", 0x10FFFF),
  (0, 0),
  (0x10FFFF, 0x10FFFF),
  (0xE000, 0xE000),
)

REJECTED_CODE_POINTS = (
  "#x110000",  # beyond the Unicode range
  "#xD800",
  "#xDFFF",  # surrogates
  -1,  # rejected by the unsigned domain
  0xD800,  # native surrogate rejected by the scalar check
  0x110000,
)


@pytest.mark.parametrize(("value", "expected"), ACCEPTED_CODE_POINTS)
def test_code_point_accepts_scalar_values_including_private_use(value: object, expected: int) -> None:
  assert CODE_POINT.validate_python(value) == expected


@pytest.mark.parametrize("value", REJECTED_CODE_POINTS)
def test_code_point_rejects_non_scalar_values(value: object) -> None:
  with pytest.raises(ValidationError):
    CODE_POINT.validate_python(value)


OFFSET_P2 = timezone(timedelta(hours=2))
OFFSET_M530 = timezone(timedelta(hours=-5, minutes=-30))
OFFSET_P2S = timezone(timedelta(hours=2, seconds=30))
OFFSET_FRACTIONAL = timezone(timedelta(hours=2, seconds=30, microseconds=500000))
OFFSET_NEAR_24H = timezone(timedelta(hours=23, minutes=59, seconds=59, microseconds=999999))
OFFSET_NEGATIVE_SUBSECOND = timezone(timedelta(microseconds=-500000))

ACCEPTED_DATETIMES = (
  # Extended and basic forms, with and without an offset.
  ("2024-01-01T12:30:45Z", datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)),
  ("2024-01-01T12:30:45+02:00", datetime(2024, 1, 1, 12, 30, 45, tzinfo=OFFSET_P2)),
  ("20240101T123045+0200", datetime(2024, 1, 1, 12, 30, 45, tzinfo=OFFSET_P2)),
  ("2024-01-01T12:30:45", datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)),  # naive -> UTC
  ("2024-01-01 12:30:45", datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)),  # space separator
  # Measured fromisoformat leniency, kept as the bounded policy's behavior:
  ("2024-01-01t12:30:45", datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)),  # lowercase t
  ("2024-01-01X12:30:45", datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)),  # any one character
  ("2024-01-01T24:00:00", datetime(2024, 1, 2, tzinfo=UTC)),  # 24:00 -> next-day midnight
  # Fractional seconds: preserved to microseconds, truncated beyond.
  ("2024-01-01T12:30:45.5", datetime(2024, 1, 1, 12, 30, 45, 500000, tzinfo=UTC)),
  ("2024-01-01T12:30:45.123456789+02:00", datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=OFFSET_P2)),
  # More of the fromisoformat repertoire, pinned so a stdlib change cannot
  # silently move the boundary of the "bounded to fromisoformat" policy:
  ("2024-01-01T12:30:45,5", datetime(2024, 1, 1, 12, 30, 45, 500000, tzinfo=UTC)),  # comma decimal
  ("2024-W01-1T00:00", datetime(2024, 1, 1, 0, 0, tzinfo=UTC)),  # week date with time
  ("2024-01-01T12:00:00+02:00:30", datetime(2024, 1, 1, 12, 0, 0, tzinfo=OFFSET_P2S)),  # offset seconds
)


@pytest.mark.parametrize(("value", "expected"), ACCEPTED_DATETIMES)
def test_parse_datetime_accepts_fromisoformat_date_times(value: str, expected: datetime) -> None:
  assert parse_datetime(value) == expected
  assert DATETIME.validate_python(value) == expected


def test_parse_datetime_keeps_a_native_offset_untouched() -> None:
  native = datetime(2024, 1, 1, 12, 30, 45, tzinfo=OFFSET_P2)
  assert parse_datetime(native) == native


def test_parse_datetime_stamps_a_native_naive_value_as_utc() -> None:
  native = datetime(2024, 1, 1, 12, 30, 45)
  assert parse_datetime(native) == native.replace(tzinfo=UTC)
  assert DATETIME.validate_python(native) == native.replace(tzinfo=UTC)


class NullOffsetTz(tzinfo):
  """A pathological tzinfo whose utcoffset() is None: behaviorally naive."""

  def utcoffset(self, dt: datetime | None) -> timedelta | None:
    return None

  def dst(self, dt: datetime | None) -> timedelta | None:
    return None

  def tzname(self, dt: datetime | None) -> str | None:
    return None


def test_parse_datetime_stamps_a_none_offset_tzinfo_as_utc() -> None:
  # tzinfo is not None here, but the value has no effective timezone.
  pathological = datetime(2024, 1, 1, 12, 30, 45, tzinfo=NullOffsetTz())
  stamped = parse_datetime(pathological)
  assert stamped == datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)
  assert parse_datetime(format_datetime(stamped)) == stamped


def test_parse_datetime_keeps_native_microseconds() -> None:
  native = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=OFFSET_M530)
  assert parse_datetime(native) == native


REJECTED_DATETIMES = (
  # Date-only: fromisoformat would accept these as midnight; we do not.
  "2024-01-01",
  "20240101",
  "2024-W01-1",
  # Time-only or truncated.
  "12:30",
  "T12:30",
  "2024-01-01T",
  # Not date-times at all.
  "",
  "nonsense",
  "  ",
  "2024-01-01T12:30:45 ",
  # Supported native types only; date, time, and everything else is out.
  date(2024, 1, 1),
  time(12, 30),
  20240101,
  True,
  None,
  1.5,
  b"2024-01-01T12:30:45Z",
  [],
)


@pytest.mark.parametrize("value", REJECTED_DATETIMES)
def test_parse_datetime_rejects_non_instants(value: object) -> None:
  with pytest.raises(ValueError):
    parse_datetime(value)
  with pytest.raises(ValidationError):
    DATETIME.validate_python(value)


EXPECTED_FORMATS = (
  (datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC), "20240101T123045Z"),
  (datetime(2024, 1, 1, 12, 30, 45), "20240101T123045Z"),  # naive assumed UTC
  (datetime(2024, 1, 1, 12, 30, 45, tzinfo=OFFSET_P2), "20240101T123045+0200"),  # offset kept
  (datetime(2024, 1, 1, 12, 30, 45, tzinfo=OFFSET_M530), "20240101T123045-0530"),
  (datetime(2024, 1, 1, 12, 30, 45, tzinfo=timezone(timedelta(hours=2, seconds=30))), "20240101T123045+020030"),
  # Finer offsets are emitted losslessly: rounding could move the instant
  # or land outside the representable range.
  (datetime(2024, 1, 1, 12, 0, 0, tzinfo=OFFSET_FRACTIONAL), "20240101T120000+020030.500000"),
  (datetime(2024, 1, 1, 12, 0, 0, tzinfo=OFFSET_NEAR_24H), "20240101T120000+235959.999999"),
  (datetime(2024, 1, 1, 12, 0, 0, tzinfo=OFFSET_NEGATIVE_SUBSECOND), "20240101T120000-000000.500000"),
  (datetime(2024, 1, 1, 12, 30, 45, 500000, tzinfo=UTC), "20240101T123045.500000Z"),
  (datetime(2024, 1, 1, 12, 30, 45, 1), "20240101T123045.000001Z"),
  (datetime(999, 1, 1), "09990101T000000Z"),  # year zero-padded, not platform-dependent
  (datetime.min, "00010101T000000Z"),
)


@pytest.mark.parametrize(("value", "expected"), EXPECTED_FORMATS, ids=[expected for _, expected in EXPECTED_FORMATS])
def test_format_datetime_renders_and_reparses(value: datetime, expected: str) -> None:
  # The explicit table is the oracle, not a self-round-trip; every emitted
  # form must also read back equal, including the rounding-hazard offsets
  # where lossy formatting would move the instant. Naive values are
  # assumed UTC, so they are stamped before the comparison.
  value = value.replace(tzinfo=UTC) if value.tzinfo is None else value
  assert format_datetime(value) == expected
  assert parse_datetime(format_datetime(value)) == value


ACCEPTED_IDENTIFIERS = ("abc-123", "")

REJECTED_IDENTIFIERS = (
  "a b",
  "a\tb",
  "a\nb",
  " ",
  "a\u00a0b",  # non-breaking space is whitespace
  None,
  42,
)


@pytest.mark.parametrize("value", ACCEPTED_IDENTIFIERS)
def test_identifier_accepts_whitespace_free_strings(value: str) -> None:
  assert IDENTIFIER.validate_python(value) == value


@pytest.mark.parametrize("value", REJECTED_IDENTIFIERS)
def test_identifier_rejects_whitespace_and_non_strings(value: object) -> None:
  with pytest.raises(ValidationError):
    IDENTIFIER.validate_python(value)


@pytest.mark.parametrize(
  ("tag", "expected"), [("mn-Cyrl-MN", "mn-Cyrl-MN"), ("EN-GB-OED", "EN-GB-OED"), ("x-pig-latin", "x-pig-latin")]
)
def test_language_tag_keeps_the_input_spelling(tag: str, expected: str) -> None:
  assert LANGUAGE_TAG.validate_python(tag) == expected


@pytest.mark.parametrize("tag", ["en_US", "*all*", "en-US;q=0.8", "én", 42, None])
def test_language_tag_rejects_non_tags(tag: object) -> None:
  with pytest.raises(ValidationError):
    LANGUAGE_TAG.validate_python(tag)


@pytest.mark.parametrize(
  ("value", "expected"),
  [
    ("en", "en"),
    ("zh-Hant", "zh-hant"),  # srclang is case-insensitive: normalized to lowercase
    ("*all*", "*all*"),
    ("*ALL*", "*all*"),  # srclang is case-insensitive and normalized
    ("*All*", "*all*"),
  ],
)
def test_source_language_accepts_tags_and_the_all_wildcard(value: str, expected: str) -> None:
  assert SOURCE_LANGUAGE.validate_python(value) == expected


@pytest.mark.parametrize("value", ["*all", "all*", "*", "en US", "12", "", None, 42])
def test_source_language_rejects_non_values(value: object) -> None:
  with pytest.raises(ValidationError):
    SOURCE_LANGUAGE.validate_python(value)


@pytest.mark.parametrize("name", ["UTF-8", "Shift_JIS", "madeup-charset", "x-vendor", ""])
def test_encoding_accepts_any_string_silently(name: str) -> None:
  """The entry boundary is purely coercing: any string passes, unknown
  names included, with no warning side effect -- the unknown-encoding
  advisory is validation's job, gathered once at validation time."""
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    assert ENCODING.validate_python(name) == name


def test_encoding_rejects_non_strings_without_warning() -> None:
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    with pytest.raises(ValidationError):
      ENCODING.validate_python(42)


@pytest.mark.parametrize("value", ["block", "paragraph", "sentence", "phrase"])
def test_seg_type_accepts_the_dtd_enumeration(value: str) -> None:
  assert SEG_TYPE.validate_python(value) == value


@pytest.mark.parametrize("value", ["Block", "block ", "", "phrases", None, 42])
def test_seg_type_rejects_other_values(value: object) -> None:
  with pytest.raises(ValidationError):
    SEG_TYPE.validate_python(value)


@pytest.mark.parametrize("value", ["begin", "end"])
def test_pos_accepts_the_dtd_enumeration(value: str) -> None:
  assert POS.validate_python(value) == value


@pytest.mark.parametrize("value", ["Begin", "start", "middle", "", None])
def test_pos_rejects_other_values(value: object) -> None:
  with pytest.raises(ValidationError):
    POS.validate_python(value)


@pytest.mark.parametrize("value", ["p", "f", "b"])
def test_assoc_accepts_the_spec_enumeration(value: str) -> None:
  assert ASSOC.validate_python(value) == value


@pytest.mark.parametrize("value", ["P", "both", "preceding", "", None])
def test_assoc_rejects_other_values(value: object) -> None:
  with pytest.raises(ValidationError):
    ASSOC.validate_python(value)


@pytest.mark.parametrize("value", ["", "code#1", '!"#$%', "0123456789"])
def test_ascii_text_accepts_ascii_strings(value: str) -> None:
  assert ASCII_TEXT.validate_python(value) == value


@pytest.mark.parametrize("value", ["café", "±", "\u00a0", "日本", None, 42])
def test_ascii_text_rejects_non_ascii_and_non_strings(value: object) -> None:
  with pytest.raises(ValidationError):
    ASCII_TEXT.validate_python(value)


def as_runtime_input(value: object) -> Any:
  """A value ty must not static-check against a field's nominal type.

  The aliases deliberately accept string forms of native values at runtime;
  a ``datetime`` field holding ``"2024-01-01T12:30:45Z"`` is exactly the
  contract under test, not a type error.
  """
  return value


class ValueProbe(BaseModel):
  model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True, validation_error_cause=True)

  integer: Integer
  code_point: UnicodeCodePoint | None = None
  creation_date: Datetime | None = None


BAD_MODEL_INPUTS = (
  ("integer", True),
  ("code_point", 0xD800),
  ("code_point", "#x110000"),
  ("creation_date", date(2024, 1, 1)),
  ("creation_date", "2024-01-01"),
  ("creation_date", 20240101),
  ("creation_date", time(12, 30)),
  ("creation_date", True),
)


@pytest.mark.parametrize(("field", "value"), BAD_MODEL_INPUTS)
def test_model_construction_reports_bad_input_as_validation_error_with_cause(field: str, value: object) -> None:
  kwargs: dict[str, Any] = {"integer": 1}
  kwargs[field] = value
  with pytest.raises(ValidationError) as excinfo:
    ValueProbe(**kwargs)
  cause = excinfo.value.__cause__
  assert isinstance(cause, ExceptionGroup)
  assert all(isinstance(error, ValueError) for error in cause.exceptions)


def test_python_mode_dumps_keep_native_values() -> None:
  probe = ValueProbe(
    integer=as_runtime_input("0042"),
    code_point=as_runtime_input("#x00e9"),
    creation_date=as_runtime_input("2024-01-01T12:30:45.500000+02:00"),
  )
  dumped = probe.model_dump()
  assert type(dumped["integer"]) is int and dumped["integer"] == 42
  assert type(dumped["code_point"]) is int and dumped["code_point"] == 0xE9
  assert dumped["creation_date"] == datetime(2024, 1, 1, 12, 30, 45, 500000, tzinfo=OFFSET_P2)


def test_json_mode_dumps_use_the_string_formatters() -> None:
  probe = ValueProbe(
    integer=as_runtime_input("0042"),
    code_point=as_runtime_input("#x00e9"),
    creation_date=as_runtime_input("2024-01-01T12:30:45.500000+02:00"),
  )
  assert probe.model_dump(mode="json") == {
    "integer": "42",
    "code_point": "#xE9",
    "creation_date": "20240101T123045.500000+0200",
  }
  assert probe.model_dump_json() == '{"integer":"42","code_point":"#xE9","creation_date":"20240101T123045.500000+0200"}'


def test_assignment_revalidates_the_field() -> None:
  probe = ValueProbe(integer=1)
  probe.integer = as_runtime_input("007")
  assert probe.integer == 7
  probe.creation_date = as_runtime_input("2024-01-01T12:30:45Z")
  assert probe.creation_date == datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC)
  probe.creation_date = datetime(2024, 1, 1, 12, 30)  # native naive: stamped on assignment too
  assert probe.creation_date == datetime(2024, 1, 1, 12, 30, tzinfo=UTC)
  with pytest.raises(ValidationError):
    probe.integer = -7
  with pytest.raises(ValidationError):
    probe.creation_date = as_runtime_input("2024-01-01")  # date-only is rejected here too
