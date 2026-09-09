"""All Pydantic TMX models (recursive family, one module).

Node shapes, the mechanical field naming, and the two inline content
grammars. Value typing and conversion live in ``validators.py``; this module only
references the aliases.

Field naming is mechanical: the TMX attribute name with ``-`` and ``:``
replaced by ``_``, otherwise verbatim -- ``o_tmf``, ``xml_lang``, and plain
``type``, ``i``, ``x``. No translation table.

``lang`` is the deprecated attribute; ``xml_lang`` is the standard one.
The deprecated attribute still exists in TMX 1.4b and is modeled.

The models are a typed, permissive IR (GAPS decision 19): typing -- strict
values, tuple fields, ``validate_assignment``, and the nonempty
``variants``/``maps`` -- is enforced at construction and assignment. Every TMX
*contract* rule (cross-field, prose pairing, advisories) lives in the pure
validation functions in ``validation.py``, which projection and the future
I/O layer invoke at every XML-IR boundary crossing.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from .validators import (
  TMXAsciiText,
  TMXAssoc,
  TMXDatetime,
  TMXEncodingName,
  TMXHexInteger,
  TMXIdentifier,
  TMXInteger,
  TMXLanguageTag,
  TMXPos,
  TMXSegType,
  TMXSourceLanguage,
  TMXUnicodeCodePoint,
)


def _as_tuple[T](value: list[T] | tuple[T, ...]) -> tuple[T, ...]:
  """Accept a list or a tuple for a repeated field; store a tuple.

  Tuples close the mutation hole that ``validate_assignment`` cannot see:
  ``model.items.append(x)`` is invisible, ``model.items += (x,)`` rebinds and
  revalidates. A list operand to ``+=`` is a plain ``TypeError`` (tuple and
  list do not concatenate) -- convert first. Values of any other type pass
  through untouched so the strict tuple check rejects them with a proper
  Pydantic error.
  """
  return tuple(value) if isinstance(value, list) else value


type ModelSequence[T] = Annotated[tuple[T, ...], BeforeValidator(_as_tuple)]
type HeaderChild = Annotated[Note | Property | Ude, Field(discriminator="element")]
type MetadataChild = Annotated[Note | Property, Field(discriminator="element")]
type InlineNode = Annotated[Bpt | Ept | Ph | It | Hi | Ut, Field(discriminator="element")]
type SegContentItem = str | InlineNode
type SubContentItem = str | Sub

type TmxNode = (
  Header | TranslationUnit | TranslationUnitVariant | Note | Property | Ude | Map | Bpt | Ept | It | Ph | Hi | Ut | Sub
)


class TmxModel(BaseModel):
  model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True, validation_error_cause=True)


class Note(TmxModel):
  """``<note>``: free-form comment.

  DTD: ``<!ELEMENT note (#PCDATA)>`` -- text only.
  """

  element: Literal["note"] = Field(default="note", frozen=True)
  o_encoding: TMXEncodingName | None = None
  xml_lang: TMXLanguageTag | None = None
  # Deprecated by TMX 1.3: use xml_lang.
  lang: TMXLanguageTag | None = None
  text: str | None = None


class Property(TmxModel):
  """``<prop>``: property name/value pair.

  DTD: ``<!ELEMENT prop (#PCDATA)>`` -- text only; ``type`` required.
  """

  element: Literal["prop"] = Field(default="prop", frozen=True)
  type: str
  xml_lang: TMXLanguageTag | None = None
  o_encoding: TMXEncodingName | None = None
  # Deprecated by TMX 1.3: use xml_lang.
  lang: TMXLanguageTag | None = None
  text: str | None = None


class Map(TmxModel):
  """``<map>``: character mapping inside a ``<ude>``.

  DTD: ``<!ELEMENT map EMPTY>`` -- no content; ``unicode`` required.
  The spec types the values beyond what the DTD can express: ``unicode``
  and ``code`` are ``#x``-prefixed hexadecimal integers, ``ent`` and
  ``subst`` must be ASCII text. The target advisory is a contract rule:
  ``validate_ude()`` emits it (GAPS decision 19).
  """

  element: Literal["map"] = Field(default="map", frozen=True)
  unicode: TMXUnicodeCodePoint
  code: TMXHexInteger | None = None
  ent: TMXAsciiText | None = None
  subst: TMXAsciiText | None = None


class Ude(TmxModel):
  """``<ude>``: user-defined encoding.

  DTD: ``<!ELEMENT ude (map+)>`` -- at least one map; ``name`` required.
  The spec's cross-field rule (``base`` required when any ``<map>`` carries
  ``code``) is a contract rule, not typing: ``validate_ude()`` enforces it at
  boundaries (GAPS decision 19).
  """

  element: Literal["ude"] = Field(default="ude", frozen=True)
  name: str
  base: TMXEncodingName | None = None
  maps: ModelSequence[Map] = Field(min_length=1)


class Sub(TmxModel):
  """``<sub>``: inline code content of a content element.

  DTD: ``<!ELEMENT sub (#PCDATA|bpt|ept|it|ph|hi|ut)*>`` -- the general
  inline grammar, same as ``<seg>``.
  """

  element: Literal["sub"] = Field(default="sub", frozen=True)
  datatype: str | None = None
  type: str | None = None
  content: "ModelSequence[SegContentItem]" = ()


class Bpt(TmxModel):
  """``<bpt>``: beginning of a paired inline tag.

  DTD: ``<!ELEMENT bpt (#PCDATA|sub)*>`` -- text plus ``<sub>`` only;
  ``i`` required.
  """

  element: Literal["bpt"] = Field(default="bpt", frozen=True)
  i: TMXInteger
  x: TMXInteger | None = None
  type: str | None = None
  content: ModelSequence[SubContentItem] = ()


class Ept(TmxModel):
  """``<ept>``: end of a paired inline tag.

  DTD: ``<!ELEMENT ept (#PCDATA|sub)*>`` -- text plus ``<sub>`` only;
  ``i`` required.
  """

  element: Literal["ept"] = Field(default="ept", frozen=True)
  i: TMXInteger
  content: ModelSequence[SubContentItem] = ()


class It(TmxModel):
  """``<it>``: isolated inline tag.

  DTD: ``<!ELEMENT it (#PCDATA|sub)*>`` -- text plus ``<sub>`` only;
  ``pos`` required.
  """

  element: Literal["it"] = Field(default="it", frozen=True)
  pos: TMXPos
  x: TMXInteger | None = None
  type: str | None = None
  content: ModelSequence[SubContentItem] = ()


class Ph(TmxModel):
  """``<ph>``: placeholder inline tag.

  DTD: ``<!ELEMENT ph (#PCDATA|sub)*>`` -- text plus ``<sub>`` only.
  """

  element: Literal["ph"] = Field(default="ph", frozen=True)
  x: TMXInteger | None = None
  assoc: TMXAssoc | None = None
  type: str | None = None
  content: ModelSequence[SubContentItem] = ()


class Hi(TmxModel):
  """``<hi>``: highlight, user-defined emphasis.

  DTD: ``<!ELEMENT hi (#PCDATA|bpt|ept|it|ph|hi|ut)*>`` -- the general
  inline grammar, recursively containing ``<hi>``.
  """

  element: Literal["hi"] = Field(default="hi", frozen=True)
  x: TMXInteger | None = None
  type: str | None = None
  content: "ModelSequence[SegContentItem]" = ()


class Ut(TmxModel):
  """``<ut>``: unknown tag. Deprecated; modeled because TMX 1.4b allows it.

  DTD: ``<!ELEMENT ut (#PCDATA|sub)*>`` -- text plus ``<sub>`` only.
  """

  element: Literal["ut"] = Field(default="ut", frozen=True)
  x: TMXInteger | None = None
  content: ModelSequence[SubContentItem] = ()


class Header(TmxModel):
  """``<header>``: TMX file header.

  DTD: ``<!ELEMENT header (note|prop|ude)*>`` -- interleaved children in
  document order, not grouped by kind. All seven core attributes required.
  """

  element: Literal["header"] = Field(default="header", frozen=True)
  creationtool: str
  creationtoolversion: str
  segtype: TMXSegType
  o_tmf: str
  adminlang: TMXLanguageTag
  srclang: TMXSourceLanguage
  datatype: str
  o_encoding: TMXEncodingName | None = None
  creationdate: TMXDatetime | None = None
  creationid: str | None = None
  changedate: TMXDatetime | None = None
  changeid: str | None = None
  metadata: ModelSequence[HeaderChild] = ()


class TranslationUnitVariant(TmxModel):
  """``<tuv>``: one language variant inside a ``<tu>``.

  DTD: ``<!ELEMENT tuv ((note|prop)*, seg)>`` -- ``metadata`` (interleaved
  notes and properties) stays separate from the segment ``content``. There
  is no ``Segment`` model: ``<seg>`` has no attributes or identity, so its
  mixed inline content is carried directly as this node's ``content``.
  """

  element: Literal["tuv"] = Field(default="tuv", frozen=True)
  xml_lang: TMXLanguageTag
  o_encoding: TMXEncodingName | None = None
  datatype: str | None = None
  usagecount: TMXInteger | None = None
  lastusagedate: TMXDatetime | None = None
  creationtool: str | None = None
  creationtoolversion: str | None = None
  creationdate: TMXDatetime | None = None
  creationid: str | None = None
  changedate: TMXDatetime | None = None
  o_tmf: str | None = None
  changeid: str | None = None
  # Deprecated by TMX 1.3: use xml_lang.
  lang: TMXLanguageTag | None = None
  metadata: ModelSequence[MetadataChild] = ()
  content: ModelSequence[SegContentItem] = ()


class TranslationUnit(TmxModel):
  """``<tu>``: one translation unit.

  DTD: ``<!ELEMENT tu ((note|prop)*, tuv+)>`` -- the model keeps the two
  groups separate: ``metadata`` (interleaved notes and properties, order
  preserved) then ``variants`` (at least one). There is no legal
  interleaving across the groups to preserve. No attributes are required;
  the header supplies the defaults.
  """

  element: Literal["tu"] = Field(default="tu", frozen=True)
  tuid: TMXIdentifier | None = None
  o_encoding: TMXEncodingName | None = None
  datatype: str | None = None
  usagecount: TMXInteger | None = None
  lastusagedate: TMXDatetime | None = None
  creationtool: str | None = None
  creationtoolversion: str | None = None
  creationdate: TMXDatetime | None = None
  creationid: str | None = None
  changedate: TMXDatetime | None = None
  segtype: TMXSegType | None = None
  changeid: str | None = None
  o_tmf: str | None = None
  srclang: TMXSourceLanguage | None = None
  metadata: ModelSequence[MetadataChild] = ()
  variants: ModelSequence[TranslationUnitVariant] = Field(min_length=1)
