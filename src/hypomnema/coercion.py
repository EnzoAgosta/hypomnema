"""Parse, validate, and serialize the annotated value types in ``models``.

Before-validators reject unsupported input with ValueError so Pydantic can
wrap failures in ValidationError. After-validators receive already-typed
values. Formatters expect validated input and provide the same strings for
JSON and XML output; Python model dumps retain native values.
"""

from datetime import UTC, date, datetime, timedelta
from string import digits, hexdigits


def lowercase_string(value: object) -> object:
  """Lowercase strings and return all other objects unchanged.

  Used before field validation so Pydantic can reject non-string values.
  """
  return value.lower() if isinstance(value, str) else value


def validate_unsigned_integer(value: int) -> int:
  """Return a nonnegative integer unchanged after the caller checks its type."""
  if value < 0:
    raise ValueError(f"expected an unsigned integer, got {value!r}")
  return value


def parse_integer(value: object) -> int:
  """Parse a nonnegative integer from a native integer or ASCII digits.

  Args:
      value: Integer or nonempty decimal string. Leading zeros are accepted.

  Returns:
      The integer value, without preserving the input spelling.

  Raises:
      ValueError: Input is negative, boolean, an unsupported type, or a string
          containing signs, whitespace, underscores, or non-ASCII digits.
  """
  if isinstance(value, bool):
    raise ValueError("a boolean is not a number here, even though bool subclasses int")
  if isinstance(value, int):
    return validate_unsigned_integer(value)
  if isinstance(value, str):
    if not value or any(digit not in digits for digit in value):
      raise ValueError(f"expected decimal digits, e.g. '42', got {value!r}")
    return int(value)
  raise ValueError(f"expected an unsigned integer or a decimal-digit string, got {type(value).__name__!r}")


def parse_datetime(value: object) -> datetime:
  """Parse a timestamp and attach UTC when it has no effective offset.

  Args:
      value: A datetime or a string accepted by ``datetime.fromisoformat``
          that contains both a date and a time. Native dates are not accepted.

  Returns:
      A datetime preserving any explicit offset and microsecond precision.
      Strings with finer fractional seconds are truncated by ``fromisoformat``.
      Naive datetimes, including those whose ``utcoffset()`` is None, acquire
      UTC without changing the clock time.

  Raises:
      ValueError: Input has an unsupported type, is date-only, or cannot be
          parsed as an ISO date and time.
  """
  if isinstance(value, datetime):
    parsed = value
  elif isinstance(value, str):
    try:
      date.fromisoformat(value)
    except ValueError:
      pass
    else:
      raise ValueError(f"a date without a time is not an instant: {value!r}")
    try:
      parsed = datetime.fromisoformat(value)
    except ValueError as error:
      raise ValueError(f"not an ISO 8601 date-time: {value!r}") from error
  else:
    raise ValueError(f"expected a datetime or an ISO 8601 date-time string, got {type(value).__name__!r}")
  if parsed.utcoffset() is None:
    parsed = parsed.replace(tzinfo=UTC)
  return parsed


def format_datetime(value: datetime) -> str:
  """Serialize a datetime in basic ISO format while preserving its offset.

  Args:
      value: Timestamp to format. An absent effective offset is treated as UTC.

  Returns:
      A ``YYYYMMDDTHHMMSS`` string with ``Z`` for zero or absent offset, or a
      signed ``HHMM`` offset otherwise. Nonzero fractional seconds use six
      digits. Offset seconds and microseconds are included when present, so
      parsing the output preserves the instant and offset.
  """
  offset = value.utcoffset()
  if offset is None or offset == timedelta(0):
    suffix = "Z"
  else:
    sign = "+" if offset > timedelta(0) else "-"
    magnitude = abs(offset)
    hours, offset_remainder = divmod(magnitude, timedelta(hours=1))
    minutes, offset_remainder = divmod(offset_remainder, timedelta(minutes=1))
    offset_seconds, offset_fraction = divmod(offset_remainder, timedelta(seconds=1))
    suffix = f"{sign}{hours:02d}{minutes:02d}"
    if offset_seconds or offset_fraction:
      suffix += f"{offset_seconds:02d}"
    if offset_fraction:
      suffix += f".{offset_fraction // timedelta(microseconds=1):06d}"
  second_fraction = f".{value.microsecond:06d}" if value.microsecond else ""
  return (
    f"{value.year:04d}{value.month:02d}{value.day:02d}"
    f"T{value.hour:02d}{value.minute:02d}{value.second:02d}"
    f"{second_fraction}{suffix}"
  )


def validate_tuid(value: str) -> str:
  """Return a translation-unit identifier unchanged if it has no whitespace.

  Empty strings are accepted.

  Raises:
      ValueError: Any character satisfies ``str.isspace``.
  """
  if any(character.isspace() for character in value):
    raise ValueError(f"expected a string without whitespace, got {value!r}")
  return value


def parse_hex_integer(value: object) -> int:
  """Parse a nonnegative integer or a TMX ``#x`` hexadecimal string.

  Args:
      value: Native integer or lowercase ``#x`` followed by one or more ASCII
          hexadecimal digits. Digits may use either case and leading zeros.

  Returns:
      The integer value, without preserving the input spelling.

  Raises:
      ValueError: Input is negative, boolean, an unsupported type, or a string
          with an invalid prefix or digits. Signs and whitespace are rejected.
  """
  if isinstance(value, bool):
    raise ValueError("a boolean is not a number here, even though bool subclasses int")
  if isinstance(value, int):
    return validate_unsigned_integer(value)
  if isinstance(value, str):
    if not value.startswith("#x"):
      raise ValueError(f"expected a '#x' prefix, e.g. '#xF8FF', got {value!r}")
    digits = value[2:]
    if not digits or any(digit not in hexdigits for digit in digits):
      raise ValueError(f"expected hexadecimal digits after '#x', e.g. '#xF8FF', got {value!r}")
    return int(digits, 16)
  raise ValueError(f"expected an unsigned integer or a '#x'-prefixed string, got {type(value).__name__!r}")


def format_hex_integer(value: int) -> str:
  """Return ``value`` as uppercase hexadecimal digits prefixed with ``#x``.

  Expects a validated nonnegative integer and does not repeat validation.
  """
  return f"#x{value:X}"


def validate_unicode_scalar(value: int) -> int:
  """Return a Unicode scalar value unchanged, including private-use values.

  Raises:
      ValueError: The value is outside 0 through 0x10FFFF or is a surrogate
          in 0xD800 through 0xDFFF.
  """
  if not (0 <= value <= 0x10FFFF) or (0xD800 <= value <= 0xDFFF):
    raise ValueError(f"expected a valid Unicode scalar value, got {value!r}")
  return value


def validate_ascii(value: str) -> str:
  """Return ASCII text unchanged, including an empty string.

  Raises:
      ValueError: The text contains a non-ASCII character.
  """
  if not value.isascii():
    raise ValueError(f"expected ASCII text, got {value!r}")
  return value
