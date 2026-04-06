"""TMX attribute enums, verified-string helpers, and spec-defined dataclasses.

The public aliases in this module describe the shape user code may pass into
node constructors. The private `_Verified*` subclasses are a static-typing tool
used internally to mark values that have already crossed the library's current
validation boundary.
"""

import codecs
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import SupportsIndex, SupportsInt, cast
from collections.abc import Buffer


# basically anything that can be passed to int()
type IntOrConvertibleToInt = str | Buffer | SupportsIndex | SupportsInt


# This one doesn't follow the below pattern as we'll actualy convert it to a datetime
# when creating a node, so it's only used for typing in functions to let users know the
# str should be a valid ISO 8601 datetime string
type ISODateString = str


# Python's type system is not able to narrow the type of a string literal like TypeScript
# does. To get around it we define two types:
#
# - A public alias `type Foo = str`: used in public-facing signatures to signal intent
#   ("this should be a valid Foo") without burdening callers with a custom type. Follows
#   the "lax input" half of the "lax input, strict output" philosophy.
#
# - An internal subclass `class _VerifiedFoo(str)`: a nominally distinct type used in
#   internal APIs to indicate the value has been validated. At runtime it remains a plain
#   str (we use `cast` rather than constructing a subclass instance), so the distinction
#   is purely for the type checker. This enforces that validation happens at the boundary
#   before values flow into internal code.
#
# The intended flow is:
#   1. Public functions accept the wide alias (e.g. `EncodingString`, `LanguageCodeString`).
#   2. A `_verify_*` function validates and narrows the type to the internal subclass.
#   3. Internal APIs declare the subclass in their signatures, making the validation
#      requirement explicit and statically checkable.
#
# This gives us self-documenting APIs, enforced validation boundaries, and zero runtime
# overhead from the type narrowing itself.

type LanguageCodeString = str
type EncodingString = str


class _VerifiedEncoding(str):
  """A str that has been verified to be a valid encoding via codecs.lookup."""

  pass


class _VerifiedLanguageCode(str):
  """A language-code string that has crossed Hypomnema's current boundary check."""

  pass


def _verify_encoding(encoding: str) -> _VerifiedEncoding:
  """Validate an encoding name with `codecs.lookup()` and narrow its type."""
  codecs.lookup(encoding)
  return cast(_VerifiedEncoding, encoding)


def _verify_language_code(language_code: str) -> _VerifiedLanguageCode:
  """Narrow a language-code string for internal use.

  The current implementation does not perform standards validation yet; it only
  marks the boundary between public input aliases and internal verified types.
  """
  # TODO: fiure out how we want to handle language codes
  return cast(_VerifiedLanguageCode, language_code)


@dataclass(slots=True, kw_only=True)
class SpecDefinedAttributes:
  """Base class for dataclasses that store TMX spec-defined attributes."""

  pass


class Pos(StrEnum):
  """Position indicator for isolated tags.

  The ``pos`` attribute is used in the ``<it>`` element to indicate
  whether an isolated tag is a beginning or an ending tag.
  """

  BEGIN = "begin"
  """Indicates the isolated tag is a beginning tag."""

  END = "end"
  """Indicates the isolated tag is an ending tag."""


class Assoc(StrEnum):
  """Association attribute for placeholders.

  The ``assoc`` attribute indicates the association of a ``<ph>`` element
  with the text preceding or following the element.
  """

  P = "p"
  """The element is associated with the text preceding the element."""

  F = "f"
  """The element is associated with the text following the element."""

  B = "b"
  """The element is associated with the text on both sides."""


class Segtype(StrEnum):
  """Segmentation type indicator.

  The ``segtype`` attribute specifies the kind of segmentation used in the
  translation unit. It indicates how the text has been segmented.
  """

  BLOCK = "block"
  """Used when the segment does not correspond to paragraph, sentence, or
    phrase level, for example when storing a chapter composed of several
    paragraphs in a single translation unit."""

  PARAGRAPH = "paragraph"
  """Segmented at paragraph boundaries."""

  SENTENCE = "sentence"
  """Segmented at sentence boundaries. This is the recommended level for
    maximum portability."""

  PHRASE = "phrase"
  """Segmented at phrase boundaries."""


@dataclass(slots=True, kw_only=True)
class TranslationMemoryHeaderSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `TranslationMemoryHeader`."""

  creation_tool: str
  creation_tool_version: str
  segmentation_type: Segtype
  original_translation_memory_format: str
  admin_language: _VerifiedLanguageCode
  source_language: _VerifiedLanguageCode
  original_data_type: str
  original_encoding: _VerifiedEncoding | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  last_modified_by: str | None = None


@dataclass(slots=True, kw_only=True)
class PropSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Prop`."""

  kind: str
  language: _VerifiedLanguageCode | None = None
  original_encoding: _VerifiedEncoding | None = None


@dataclass(slots=True, kw_only=True)
class NoteSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Note`."""

  language: _VerifiedLanguageCode | None = None
  original_encoding: _VerifiedEncoding | None = None


@dataclass(slots=True, kw_only=True)
class BptSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Bpt`."""

  internal_id: int
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class EptSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Ept`."""

  internal_id: int


@dataclass(slots=True, kw_only=True)
class HiSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Hi`."""

  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class ItSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `It`."""

  position: Pos
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class PhSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Ph`."""

  association: Assoc | None = None
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class SubSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `Sub`."""

  original_data_type: str | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class TranslationVariantSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `TranslationVariant`."""

  language: _VerifiedLanguageCode
  original_encoding: _VerifiedEncoding | None = None
  original_data_type: str | None = None
  usage_count: int | None = None
  last_used_at: datetime | None = None
  creation_tool: str | None = None
  creation_tool_version: str | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  last_modified_by: str | None = None
  original_tm_format: str | None = None


@dataclass(slots=True, kw_only=True)
class TranslationUnitSpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `TranslationUnit`."""

  translation_unit_id: str | None = None
  original_encoding: _VerifiedEncoding | None = None
  original_data_type: str | None = None
  usage_count: int | None = None
  last_used_at: datetime | None = None
  creation_tool: str | None = None
  creation_tool_version: str | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  segmentation_type: Segtype | None = None
  last_modified_by: str | None = None
  original_tm_format: str | None = None
  source_language: _VerifiedLanguageCode | None = None


@dataclass(slots=True, kw_only=True)
class TranslationMemorySpecDefinedAttributes(SpecDefinedAttributes):
  """Spec-defined attributes stored on `TranslationMemory`."""

  version: str = "1.4"
