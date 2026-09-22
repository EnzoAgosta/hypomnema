"""Pydantic models and annotated value types for TMX elements.

Constructors validate field types and reject unknown fields. Ordered lists
preserve metadata and mixed-content order. Cross-field and cross-node TMX
rules require the separate validation API. Optional attributes default to
None, and each optional list starts empty. Every concrete model has a frozen
``element`` discriminator matching its XML tag.

Annotated value types parse TMX integers and timestamps, validate language
tag syntax, and supply JSON serializers. Python dumps retain native values;
JSON dumps use decimal strings, ``#x`` hexadecimal strings, and ISO timestamps.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer

from hypomnema.bcp47 import validate_well_formed_language_tag
from hypomnema.coercion import (
  format_datetime,
  format_hex_integer,
  lowercase_string,
  parse_datetime,
  parse_hex_integer,
  parse_integer,
  validate_ascii,
  validate_tuid,
  validate_unicode_scalar,
)

type LanguageTag = Annotated[str, AfterValidator(validate_well_formed_language_tag)]
type EncodingName = str
type HexInteger = Annotated[
  int, BeforeValidator(parse_hex_integer), PlainSerializer(format_hex_integer, return_type=str, when_used="json")
]
type UnicodeCodePoint = Annotated[HexInteger, AfterValidator(validate_unicode_scalar)]
type AsciiText = Annotated[str, AfterValidator(validate_ascii)]
type SegType = Literal["block", "paragraph", "sentence", "phrase"]
type Position = Literal["begin", "end"]
type Association = Literal["p", "f", "b"]
type SourceLanguage = Annotated[LanguageTag | Literal["*all*"], BeforeValidator(lowercase_string)]
type Tuid = Annotated[str, AfterValidator(validate_tuid)]
type Datetime = Annotated[
  datetime, BeforeValidator(parse_datetime), PlainSerializer(format_datetime, return_type=str, when_used="json")
]
type Integer = Annotated[int, BeforeValidator(parse_integer), PlainSerializer(str, return_type=str, when_used="json")]

type TmxNode = Annotated[
  Header | TranslationUnit | TranslationUnitVariant | Note | Property | Ude | Map | Bpt | Ept | It | Ph | Hi | Ut | Sub,
  Field(discriminator="element"),
]
type StructureNode = Annotated[Header | TranslationUnit | TranslationUnitVariant | Ude, Field(discriminator="element")]
type LeafNode = Annotated[Note | Property | Map, Field(discriminator="element")]
type InlineNode = Annotated[Bpt | Ept | Ph | It | Hi | Ut, Field(discriminator="element")]
type InlineNodeOrStr = str | InlineNode
type SubOrStr = str | Sub


class TmxModel(BaseModel):
  """Base model that rejects unknown fields and retains validation causes.

  Construction validates fields through Pydantic. Instances remain mutable;
  assignment does not automatically revalidate fields. Concrete subclasses
  freeze their ``element`` discriminator.
  """

  model_config = ConfigDict(extra="forbid", validation_error_cause=True)


class Note(TmxModel):
  """A plain-text annotation attached to a header, unit, or variant.

  Attributes:
      element: Fixed XML tag, ``note``.
      o_encoding: Original encoding name, recorded without codec lookup.
      xml_lang: Language tag for the note, preserving input case.
      lang: Deprecated language attribute retained separately from ``xml_lang``.
      text: Note text, or None when the element has no text.
  """

  element: Annotated[Literal["note"], Field(default="note", init=False, repr=False, frozen=True)]
  o_encoding: EncodingName | None = None
  xml_lang: LanguageTag | None = None
  lang: Annotated[
    LanguageTag | None,
    Field(
      json_schema_extra={
        "deprecated": True,
        "description": "the lang attribute is deprecated since TMX 1.3 in favor of xml_lang",
      }
    ),
  ] = None
  text: str | None = None


class Property(TmxModel):
  """A named, plain-text property attached to a header, unit, or variant.

  Attributes:
      element: Fixed XML tag, ``prop``.
      type: Required property name, including application-defined names.
      xml_lang: Language tag for the property text.
      o_encoding: Original encoding name, recorded without codec lookup.
      lang: Deprecated language attribute retained separately from ``xml_lang``.
      text: Property value, or None when the element has no text.
  """

  element: Annotated[Literal["prop"], Field(default="prop", init=False, repr=False, frozen=True)]
  type: str
  xml_lang: LanguageTag | None = None
  o_encoding: EncodingName | None = None
  lang: Annotated[
    LanguageTag | None,
    Field(
      json_schema_extra={
        "deprecated": True,
        "description": "the lang attribute is deprecated since TMX 1.3 in favor of xml_lang",
      }
    ),
  ] = None
  text: str | None = None


class Map(TmxModel):
  """One character mapping in a user-defined encoding.

  Construction checks individual values. ``validate_ude`` reports an advisory
  when a mapping has no ``code``, ``ent``, or ``subst`` target, and requires
  the containing encoding's ``base`` when ``code`` is set.

  Attributes:
      element: Fixed XML tag, ``map``.
      unicode: Unicode scalar value, excluding surrogate code points.
      code: Optional nonnegative encoded character number.
      ent: Optional ASCII entity name.
      subst: Optional ASCII substitution text.
  """

  element: Annotated[Literal["map"], Field(default="map", init=False, repr=False, frozen=True)]
  unicode: UnicodeCodePoint
  code: HexInteger | None = None
  ent: AsciiText | None = None
  subst: AsciiText | None = None


class Ude(TmxModel):
  """A named user-defined encoding with at least one character mapping.

  Attributes:
      element: Fixed XML tag, ``ude``.
      name: Encoding name referenced by TMX encoding attributes.
      base: Optional name of the encoding extended by this definition.
      maps: Character mappings in document order; must not be empty.
  """

  element: Annotated[Literal["ude"], Field(default="ude", init=False, repr=False, frozen=True)]
  name: str
  base: EncodingName | None = None
  maps: Annotated[list[Map], Field(min_length=1)]


class Sub(TmxModel):
  """Translatable text embedded inside an inline code.

  Attributes:
      element: Fixed XML tag, ``sub``.
      datatype: Optional format of the embedded text.
      type: Optional application-defined subflow type.
      content: Ordered strings and inline nodes comprising the subflow.
  """

  element: Annotated[Literal["sub"], Field(default="sub", init=False, repr=False, frozen=True)]
  datatype: str | None = None
  type: str | None = None
  content: Annotated[list[InlineNodeOrStr], Field(default_factory=list)]


class Bpt(TmxModel):
  """Opening code of a paired inline element.

  Validate the enclosing segment to check pairing with ``Ept``. Pairs may
  overlap; strict stack nesting is not required.

  Attributes:
      element: Fixed XML tag, ``bpt``.
      i: Nonnegative identifier linking this code to its closing ``Ept``.
      x: Optional nonnegative identifier for correspondence across variants.
      type: Optional description of the original code's type.
      content: Ordered original-code strings and translatable ``Sub`` nodes.
  """

  element: Annotated[Literal["bpt"], Field(default="bpt", init=False, repr=False, frozen=True)]
  i: Integer
  x: Integer | None = None
  type: str | None = None
  content: Annotated[list[SubOrStr], Field(default_factory=list)]


class Ept(TmxModel):
  """Closing code of a paired inline element.

  Attributes:
      element: Fixed XML tag, ``ept``.
      i: Nonnegative identifier matching the opening ``Bpt``.
      content: Ordered original-code strings and translatable ``Sub`` nodes.
  """

  element: Annotated[Literal["ept"], Field(default="ept", init=False, repr=False, frozen=True)]
  i: Integer
  content: Annotated[list[SubOrStr], Field(default_factory=list)]


class It(TmxModel):
  """An isolated opening or closing code whose partner is outside the segment.

  Attributes:
      element: Fixed XML tag, ``it``.
      pos: Whether the isolated code is an opening ``begin`` or closing ``end``.
      x: Optional nonnegative identifier for correspondence across variants.
      type: Optional description of the original code's type.
      content: Ordered original-code strings and translatable ``Sub`` nodes.
  """

  element: Annotated[Literal["it"], Field(default="it", init=False, repr=False, frozen=True)]
  pos: Position
  x: Integer | None = None
  type: str | None = None
  content: Annotated[list[SubOrStr], Field(default_factory=list)]


class Ph(TmxModel):
  """A standalone inline placeholder for original-format code.

  Attributes:
      element: Fixed XML tag, ``ph``.
      x: Optional nonnegative identifier for correspondence across variants.
      assoc: Association with preceding text, ``p``, following text, ``f``,
          or both, ``b``.
      type: Optional description of the original code's type.
      content: Ordered original-code strings and translatable ``Sub`` nodes.
  """

  element: Annotated[Literal["ph"], Field(default="ph", init=False, repr=False, frozen=True)]
  x: Integer | None = None
  assoc: Association | None = None
  type: str | None = None
  content: Annotated[list[SubOrStr], Field(default_factory=list)]


class Hi(TmxModel):
  """A highlighted span of translatable mixed content.

  Attributes:
      element: Fixed XML tag, ``hi``.
      x: Optional nonnegative identifier for correspondence across variants.
      type: Optional description of the highlighted span.
      content: Ordered strings and nested inline nodes.
  """

  element: Annotated[Literal["hi"], Field(default="hi", init=False, repr=False, frozen=True)]
  x: Integer | None = None
  type: str | None = None
  content: Annotated[list[InlineNodeOrStr], Field(default_factory=list)]


class Ut(TmxModel):
  """A deprecated inline code retained for older TMX documents.

  Prefer ``Bpt``, ``Ept``, ``It``, or ``Ph`` for new data.

  Attributes:
      element: Fixed XML tag, ``ut``.
      x: Optional nonnegative identifier for correspondence across variants.
      content: Ordered original-code strings and translatable ``Sub`` nodes.
  """

  model_config = ConfigDict(
    json_schema_extra={
      "deprecated": True,
      "description": "the <ut> element is deprecated, use <bpt>, <ept>, <it>, or <ph> instead",
    }
  )
  element: Annotated[Literal["ut"], Field(default="ut", init=False, repr=False, frozen=True)]
  x: Integer | None = None
  content: Annotated[list[SubOrStr], Field(default_factory=list)]


class Header(TmxModel):
  """Document metadata and default settings for translation units.

  Attributes:
      element: Fixed XML tag, ``header``.
      creationtool: Required name of the tool that created the document.
      creationtoolversion: Required version of that tool.
      segtype: Required segmentation level: block, paragraph, sentence, or phrase.
      o_tmf: Required original translation-memory format name.
      adminlang: Required language tag for administrative text.
      srclang: Required source language or ``*all*``; normalized to lowercase.
      datatype: Required format of the original content.
      o_encoding: Optional original encoding name.
      creationdate: Optional creation timestamp; naive inputs acquire UTC.
      creationid: Optional identifier of the creator.
      changedate: Optional last-change timestamp; naive inputs acquire UTC.
      changeid: Optional identifier of the last editor.
      metadata: Notes, properties, and encoding definitions in document order.
  """

  element: Annotated[Literal["header"], Field(default="header", init=False, repr=False, frozen=True)]
  creationtool: str
  creationtoolversion: str
  segtype: SegType
  o_tmf: str
  adminlang: LanguageTag
  srclang: SourceLanguage
  datatype: str
  o_encoding: EncodingName | None = None
  creationdate: Datetime | None = None
  creationid: str | None = None
  changedate: Datetime | None = None
  changeid: str | None = None
  metadata: Annotated[list[Note | Property | Ude], Field(default_factory=list)]


class TranslationUnitVariant(TmxModel):
  """One language's segment and metadata within a translation unit.

  Language tags retain their spelling. Construction does not resolve inherited
  settings from the unit or header.

  Attributes:
      element: Fixed XML tag, ``tuv``.
      xml_lang: Required language tag for this variant.
      o_encoding: Optional original encoding name.
      datatype: Optional original-content format.
      usagecount: Optional nonnegative usage count.
      lastusagedate: Optional timestamp of the most recent use.
      creationtool: Optional name of the creation tool.
      creationtoolversion: Optional version of the creation tool.
      creationdate: Optional creation timestamp.
      creationid: Optional identifier of the creator.
      changedate: Optional last-change timestamp.
      o_tmf: Optional original translation-memory format name.
      changeid: Optional identifier of the last editor.
      lang: Deprecated language attribute retained separately from ``xml_lang``.
      metadata: Notes and properties in document order.
      content: Segment strings and inline nodes in document order.
  """

  element: Annotated[Literal["tuv"], Field(default="tuv", init=False, repr=False, frozen=True)]
  xml_lang: LanguageTag
  o_encoding: EncodingName | None = None
  datatype: str | None = None
  usagecount: Integer | None = None
  lastusagedate: Datetime | None = None
  creationtool: str | None = None
  creationtoolversion: str | None = None
  creationdate: Datetime | None = None
  creationid: str | None = None
  changedate: Datetime | None = None
  o_tmf: str | None = None
  changeid: str | None = None
  lang: Annotated[
    LanguageTag | None,
    Field(
      json_schema_extra={
        "deprecated": True,
        "description": "the lang attribute is deprecated since TMX 1.3 in favor of xml_lang",
      }
    ),
  ] = None
  metadata: Annotated[list[Note | Property], Field(default_factory=list)]
  content: Annotated[list[InlineNodeOrStr], Field(default_factory=list)]


class TranslationUnit(TmxModel):
  """A translation unit containing at least one language variant.

  Construction validates individual fields. Use validate_translation_unit to
  check paired codes and compare external identifiers across variants. Header
  consistency and document-wide identifier uniqueness remain caller policies.

  Attributes:
      element: Fixed XML tag, ``tu``.
      tuid: Optional identifier containing no whitespace.
      o_encoding: Optional original encoding name.
      datatype: Optional original-content format.
      usagecount: Optional nonnegative usage count.
      lastusagedate: Optional timestamp of the most recent use.
      creationtool: Optional name of the creation tool.
      creationtoolversion: Optional version of the creation tool.
      creationdate: Optional creation timestamp.
      creationid: Optional identifier of the creator.
      changedate: Optional last-change timestamp.
      segtype: Optional segmentation level overriding the header setting.
      changeid: Optional identifier of the last editor.
      o_tmf: Optional original translation-memory format name.
      srclang: Optional source language or ``*all*``; normalized to lowercase.
      metadata: Notes and properties in document order.
      variants: Language variants in document order; must not be empty.
  """

  element: Annotated[Literal["tu"], Field(default="tu", init=False, repr=False, frozen=True)]
  tuid: Tuid | None = None
  o_encoding: EncodingName | None = None
  datatype: str | None = None
  usagecount: Integer | None = None
  lastusagedate: Datetime | None = None
  creationtool: str | None = None
  creationtoolversion: str | None = None
  creationdate: Datetime | None = None
  creationid: str | None = None
  changedate: Datetime | None = None
  segtype: SegType | None = None
  changeid: str | None = None
  o_tmf: str | None = None
  srclang: SourceLanguage | None = None
  metadata: Annotated[list[Note | Property], Field(default_factory=list)]
  variants: Annotated[list[TranslationUnitVariant], Field(min_length=1)]
