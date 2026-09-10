"""Enums, Annotated value aliases, parse/format functions.

Value aliases are public Pydantic functional metadata so a value is honestly
its Python type: a ``TMXDatetime`` is a ``datetime``. BeforeValidators accept
a narrow input repertoire and reject everything else with ``ValueError``, so
Pydantic surfaces rejections as ``ValidationError`` with the cause retained;
no parser raises ``TypeError``, which Pydantic would not catch. Serializers
split Python from JSON: ``model_dump()`` keeps native values, JSON mode and
XML output share one string formatter per type (``when_used="json"``).

Language-tag validation lives in ``bcp47.py`` (grammar-only, RFC 5646) and is
used here through its ``validate_well_formed_language_tag``.
"""

import codecs
import warnings
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal

from pydantic import AfterValidator, BeforeValidator, PlainSerializer

from .bcp47 import validate_well_formed_language_tag
from .errors import TmxDeprecationWarning, TmxWarning


def warn_unknown_encoding(value: str) -> str:
  """Nudge when an encoding name is unknown to Python's codecs.

  The spec recommends IANA charset identifiers for ``o-encoding`` and
  ``<ude base>`` but only as a soft "if possible" -- not enforceable, so
  this warns and keeps the value instead of rejecting it.
  """
  try:
    codecs.lookup(value)
  except LookupError:
    warnings.warn(
      f"encoding {value!r} is not recognized by Python's codecs; the spec recommends IANA charset identifiers",
      TmxWarning,
    )
  return value


def warn_deprecated_lang(lang: str | None, xml_lang: str | None) -> None:
  """Advisory checks for the deprecated ``lang`` attribute (GAPS #8).

  Legacy ``lang`` without ``xml_lang`` is deprecated-but-correct: warn.
  Both present but differing -- compared case-insensitively, since tags
  are case-insensitive -- is suspicious: warn. One attribute is never
  synthesized or normalized from the other.
  """
  if lang is None:
    return
  if xml_lang is None:
    warnings.warn("the deprecated lang attribute is set without xml_lang; prefer xml:lang", TmxDeprecationWarning)
  elif lang.lower() != xml_lang.lower():
    warnings.warn(f"lang {lang!r} and xml_lang {xml_lang!r} differ", TmxWarning)


def warn_deprecated_ut() -> None:
  """The ``<ut>`` element is deprecated (since TMX 1.3) but still legal."""
  warnings.warn("the <ut> element is deprecated; prefer <bpt>, <ept>, <it>, or <ph>", TmxDeprecationWarning)


def warn_map_without_target(code: int | None, ent: str | None, subst: str | None) -> None:
  """The spec recommends at least one of ``code``, ``ent``, ``subst`` on a
  ``<map>`` -- a soft "should", so this warns instead of rejecting."""
  if code is None and ent is None and subst is None:
    warnings.warn("a <map> should specify at least one of code, ent, or subst", TmxWarning)


type TMXEncodingName = Annotated[str, AfterValidator(warn_unknown_encoding)]


type TMXSegType = Literal["block", "paragraph", "sentence", "phrase"]
"""The ``%segtypes;`` entity the DTD enumerates: the segment's granularity."""

type TMXPos = Literal["begin", "end"]
"""``<it pos>``: whether the isolated tag opens or closes markup."""

type TMXAssoc = Literal["p", "f", "b"]
"""``<ph assoc>``: whether the placeholder belongs to preceding, following,
or both-sides text (spec prose, not the DTD)."""


_DECIMAL_DIGITS = "0123456789"


def parse_integer(value: object) -> int:
  """Parse a decimal integer, e.g. ``usagecount``, ``i``, ``x``.

  The spec types these attributes as numbers, so the same unsigned domain
  holds for every input form: native integers must be non-negative, and
  strings must be pure ASCII digits -- no sign, whitespace, underscore, or
  other ``int()`` conveniences. Leading zeros are accepted but their
  spelling is not retained. Booleans are rejected even though ``bool`` is
  an ``int`` subclass; so are floats. Raises ``ValueError`` for all of it.
  """
  if isinstance(value, bool):
    raise ValueError("a boolean is not a number here, even though bool subclasses int")
  if isinstance(value, int):
    if value < 0:
      raise ValueError(f"expected an unsigned integer, got {value!r}")
    return value
  if isinstance(value, str):
    if not value or any(digit not in _DECIMAL_DIGITS for digit in value):
      raise ValueError(f"expected decimal digits, e.g. '42', got {value!r}")
    return int(value)
  raise ValueError(f"expected an unsigned integer or a decimal-digit string, got {type(value).__name__!r}")


def format_integer(value: int) -> str:
  """Format an integer as canonical decimal digits (JSON and XML)."""
  return str(value)


type TMXInteger = Annotated[
  int, BeforeValidator(parse_integer), PlainSerializer(format_integer, return_type=str, when_used="json")
]


def parse_datetime(value: object) -> datetime:
  """Parse a date-time value, e.g. ``creationdate``.

  Accepts native ``datetime`` values and strings parseable by
  ``datetime.fromisoformat()`` -- deliberately bounded to that parser's
  repertoire, not the full ISO 8601 standard. Input must combine a date
  and a time: date-only strings are rejected even though ``fromisoformat``
  would accept them as midnight, detected with ``date.fromisoformat``
  (which succeeds exactly on date-only input). Native ``date`` and ``time``
  objects are rejected as unsupported types.

  A naive value is assumed to be UTC and stamped with it; an explicit
  offset is retained as-is, never converted. A ``tzinfo`` whose
  ``utcoffset()`` is ``None`` is behaviorally naive and is stamped too.
  Fractional seconds are kept
  to ``datetime``'s microsecond precision (``fromisoformat`` truncates
  beyond it, which is part of the bounded policy).
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
  """Format a date-time for JSON and XML output, keeping its offset.

  Basic ISO 8601 ``YYYYMMDDTHHMMSS`` -- the form the spec recommends --
  with ``Z`` for a zero/absent offset (naive values are assumed UTC) and
  ``+HHMM``/``-HHMM`` otherwise, so an explicitly supplied offset survives
  output instead of being normalized to UTC. Finer offset components are
  emitted losslessly when present -- seconds, then a fractional part --
  because ``fromisoformat`` re-reads every form this emits; the offset is
  never rounded, which could silently move the instant or land outside the
  representable range (``±2359`` at the extreme). Fractional seconds of
  the datetime itself are emitted to ``datetime``'s precision, only when
  nonzero, as in ``datetime.isoformat()``. Manual formatting for
  predictable year zero-padding, which ``strftime``'s ``%Y`` does not
  guarantee.
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


type TMXDatetime = Annotated[
  datetime, BeforeValidator(parse_datetime), PlainSerializer(format_datetime, return_type=str, when_used="json")
]


def validate_identifier(value: str) -> str:
  """Check an identifier contains no whitespace, as the spec requires
  for ``tuid``."""
  if any(character.isspace() for character in value):
    raise ValueError(f"expected a string without whitespace, got {value!r}")
  return value


type TMXIdentifier = Annotated[str, AfterValidator(validate_identifier)]


def validate_source_language(value: str) -> str:
  """Check a ``srclang`` value: a language tag or ``*all*``.

  The spec makes ``srclang`` values case-insensitive, so ``*ALL*`` is
  normalized to the canonical ``*all*``; language tags keep their
  spelling.
  """
  if value.lower() == "*all*":
    return "*all*"
  return validate_well_formed_language_tag(value)


type TMXLanguageTag = Annotated[str, AfterValidator(validate_well_formed_language_tag)]
type TMXSourceLanguage = Annotated[str, AfterValidator(validate_source_language)]


_HEX_DIGITS = "0123456789abcdefABCDEF"


def parse_hex_integer(value: object) -> int:
  """Parse a ``#x``-prefixed hexadecimal integer, e.g. ``#xF8FF``.

  The format the TMX spec prescribes for ``<map unicode>`` and
  ``<map code>``. Strictly ``#x`` plus ASCII hexadecimal digits: no
  ``0x``, no sign, no whitespace, no ``int()`` conveniences such as
  underscores. Native integers must be non-negative; booleans and floats
  are rejected like any other unsupported type. Leading zeros are accepted
  but their spelling is not retained. Raises ``ValueError`` for all of it.
  """
  if isinstance(value, bool):
    raise ValueError("a boolean is not a number here, even though bool subclasses int")
  if isinstance(value, int):
    if value < 0:
      raise ValueError(f"expected an unsigned value, got {value}")
    return value
  if isinstance(value, str):
    if not value.startswith("#x"):
      raise ValueError(f"expected a '#x' prefix, e.g. '#xF8FF', got {value!r}")
    digits = value[2:]
    if not digits or any(digit not in _HEX_DIGITS for digit in digits):
      raise ValueError(f"expected hexadecimal digits after '#x', e.g. '#xF8FF', got {value!r}")
    return int(digits, 16)
  raise ValueError(f"expected an unsigned integer or a '#x'-prefixed string, got {type(value).__name__!r}")


def format_hex_integer(value: int) -> str:
  """Format a hexadecimal integer the way the spec's examples spell it."""
  return f"#x{value:X}"


def validate_unicode_scalar(value: int) -> int:
  """Check a code point is a valid Unicode scalar value.

  0 to 0x10FFFF, surrogates excluded; Private Use areas allowed per spec.
  """
  if not (0 <= value <= 0x10FFFF) or (0xD800 <= value <= 0xDFFF):
    raise ValueError(f"expected a valid Unicode scalar value, got {value!r}")
  return value


def validate_ascii(value: str) -> str:
  """Check text is ASCII, as the spec requires for ``ent`` and ``subst``."""
  if not value.isascii():
    raise ValueError(f"expected ASCII text, got {value!r}")
  return value


type TMXHexInteger = Annotated[
  int, BeforeValidator(parse_hex_integer), PlainSerializer(format_hex_integer, return_type=str, when_used="json")
]
type TMXUnicodeCodePoint = Annotated[TMXHexInteger, AfterValidator(validate_unicode_scalar)]
type TMXAsciiText = Annotated[str, AfterValidator(validate_ascii)]
