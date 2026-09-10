from datetime import datetime
from typing import Annotated, Literal
from warnings import deprecated

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer

from hypomnema.bcp47 import validate_well_formed_language_tag
from hypomnema.validators import (
  format_datetime,
  format_hex_integer,
  parse_datetime,
  parse_hex_integer,
  parse_integer,
  validate_ascii,
  validate_tuid,
  validate_unicode_scalar,
  warn_unknown_encoding,
)

type LanguageTag = Annotated[str, AfterValidator(validate_well_formed_language_tag)]
type EncodingName = Annotated[str, BeforeValidator(warn_unknown_encoding)]
type HexInteger = Annotated[
  int, BeforeValidator(parse_hex_integer), PlainSerializer(format_hex_integer, return_type=str, when_used="json")
]
type UnicodeCodePoint = Annotated[HexInteger, AfterValidator(validate_unicode_scalar)]
type AsciiText = Annotated[str, AfterValidator(validate_ascii)]
type SegType = Literal["block", "paragraph", "sentence", "phrase"]
type Tuid = Annotated[str, AfterValidator(validate_tuid)]
type Datetime = Annotated[
  datetime, BeforeValidator(parse_datetime), PlainSerializer(format_datetime, return_type=str, when_used="json")
]
type Integer = Annotated[int, BeforeValidator(parse_integer), PlainSerializer(str, return_type=str, when_used="json")]

type TmxNode = Annotated[
  Header | TranslationUnit | TranslationUnitVariant | Note | Property | Ude | Map | Bpt | Ept | It | Ph | Hi | Ut | Sub,  # ty: ignore[deprecated]
  Field(discriminator="element"),
]
type StructureNode = Annotated[Header | TranslationUnit | TranslationUnitVariant | Ude, Field(discriminator="element")]
type LeafNode = Annotated[Note | Property | Map, Field(discriminator="element")]
type InlineNode = Annotated[Bpt | Ept | Ph | It | Hi | Ut, Field(discriminator="element")]  # ty: ignore[deprecated]
type InlineNodeOrStr = str | InlineNode
type SubOrStr = str | Sub


class TmxModel(BaseModel):
  model_config = ConfigDict(extra="forbid", validation_error_cause=True)


class Note(TmxModel):
  element: Annotated[Literal["note"], Field(default="note", init=False, repr=False, frozen=True)]
  o_encoding: EncodingName | None = None
  xml_lang: LanguageTag | None = None
  # Deprecated by TMX 1.3: use xml_lang.
  lang: Annotated[
    LanguageTag | None,
    Field(deprecated=deprecated("the lang attribute is deprecated since TMX 1.3 in favor of xml_lang")),
  ] = None
  text: str | None = None


class Property(TmxModel):
  element: Annotated[Literal["prop"], Field(default="prop", init=False, repr=False, frozen=True)]
  type: str
  xml_lang: LanguageTag | None = None
  o_encoding: EncodingName | None = None
  lang: Annotated[
    LanguageTag | None,
    Field(deprecated=deprecated("the lang attribute is deprecated since TMX 1.3 in favor of xml_lang")),
  ] = None
  text: str | None = None


class Map(TmxModel):
  element: Annotated[Literal["map"], Field(default="map", init=False, repr=False, frozen=True)]
  unicode: UnicodeCodePoint
  code: HexInteger | None = None
  ent: AsciiText | None = None
  subst: AsciiText | None = None


class Ude(TmxModel):
  element: Annotated[Literal["ude"], Field(default="ude", init=False, repr=False, frozen=True)]
  name: str
  base: EncodingName | None = None
  maps: Annotated[tuple[Map, ...], Field(min_length=1)]


class Sub(TmxModel):
  element: Annotated[Literal["sub"], Field(default="sub", init=False, repr=False, frozen=True)]
  datatype: str | None = None
  type: str | None = None
  content: Annotated[tuple[InlineNodeOrStr, ...], Field(default_factory=tuple)]


class Bpt(TmxModel):
  element: Annotated[Literal["bpt"], Field(default="bpt", init=False, repr=False, frozen=True)]
  i: Integer
  x: Integer | None = None
  type: str | None = None
  content: Annotated[tuple[SubOrStr, ...], Field(default_factory=tuple)]


class Ept(TmxModel):
  element: Annotated[Literal["ept"], Field(default="ept", init=False, repr=False, frozen=True)]
  i: Integer
  content: Annotated[tuple[SubOrStr, ...], Field(default_factory=tuple)]


class It(TmxModel):
  element: Annotated[Literal["it"], Field(default="it", init=False, repr=False, frozen=True)]
  pos: Literal["begin", "end"]
  x: Integer | None = None
  type: str | None = None
  content: Annotated[tuple[SubOrStr, ...], Field(default_factory=tuple)]


class Ph(TmxModel):
  element: Annotated[Literal["ph"], Field(default="ph", init=False, repr=False, frozen=True)]
  x: Integer | None = None
  assoc: Literal["p", "f", "b"] | None = None
  type: str | None = None
  content: Annotated[tuple[SubOrStr, ...], Field(default_factory=tuple)]


class Hi(TmxModel):
  element: Annotated[Literal["hi"], Field(default="hi", init=False, repr=False, frozen=True)]
  x: Integer | None = None
  type: str | None = None
  content: Annotated[tuple[InlineNodeOrStr, ...], Field(default_factory=tuple)]


@deprecated("the <ut> element is deprecated, use <bpt>, <ept>, <it>, or <ph> instead")
class Ut(TmxModel):
  model_config = ConfigDict(
    json_schema_extra={
      "deprecated": True,
      "description": "the <ut> element is deprecated, use <bpt>, <ept>, <it>, or <ph> instead",
    }
  )
  element: Annotated[Literal["ut"], Field(default="ut", init=False, repr=False, frozen=True)]
  x: Integer | None = None
  content: Annotated[tuple[SubOrStr, ...], Field(default_factory=tuple)]


class Header(TmxModel):
  element: Annotated[Literal["header"], Field(default="header", init=False, repr=False, frozen=True)]
  creationtool: str
  creationtoolversion: str
  segtype: SegType
  o_tmf: str
  adminlang: LanguageTag
  srclang: Annotated[LanguageTag | Literal["*all*"], BeforeValidator(str.lower)]
  datatype: str
  o_encoding: EncodingName | None = None
  creationdate: Datetime | None = None
  creationid: str | None = None
  changedate: Datetime | None = None
  changeid: str | None = None
  metadata: Annotated[tuple[Note | Property | Ude, ...], Field(default_factory=tuple)]


class TranslationUnitVariant(TmxModel):
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
  # Deprecated by TMX 1.3: use xml_lang.
  lang: Annotated[LanguageTag | None, Field(deprecated=True)] = None
  metadata: Annotated[tuple[Note | Property, ...], Field(default_factory=tuple)]
  content: Annotated[tuple[InlineNodeOrStr, ...], Field(default_factory=tuple)]


class TranslationUnit(TmxModel):
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
  srclang: Annotated[LanguageTag | Literal["*all*"], BeforeValidator(str.lower)]
  metadata: Annotated[tuple[Note | Property, ...], Field(default_factory=tuple)]
  variants: Annotated[tuple[TranslationUnitVariant, ...], Field(min_length=1)]
