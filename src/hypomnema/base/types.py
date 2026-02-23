"""TMX dataclasses and type definitions.

This module defines the core data structures for representing TMX 1.4b
elements as Python dataclasses. All dataclasses use ``slots=True`` for
memory efficiency when working with large translation memory files.

Note:
    All datetime fields follow ISO 8601 format with 'Z' suffix (UTC) as
    per TMX spec. Language codes follow BCP-47 but are not validated to
    maintain zero-dependency constraint.
"""

from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

type BaseElement = Tmx | Header | Prop | Note | Tu | Tuv | Bpt | Ept | It | Ph | Hi | Sub
type InlineElement = Bpt | Ept | It | Ph | Hi | Sub

type TmxElementLike = (
  TmxLike
  | HeaderLike
  | PropLike
  | NoteLike
  | TuLike
  | TuvLike
  | BptLike
  | EptLike
  | ItLike
  | PhLike
  | HiLike
  | SubLike
)
type InlineElementLike = BptLike | EptLike | ItLike | PhLike | HiLike | SubLike


@runtime_checkable
class BptLike[AnySequenceOfStrOrSubBase: Sequence[str | SubLike]](Protocol):
  i: int
  x: int | None
  type: str | None
  content: AnySequenceOfStrOrSubBase


@runtime_checkable
class EptLike[AnySequenceOfStrOrSubBase: Sequence[str | SubLike]](Protocol):
  i: int
  content: AnySequenceOfStrOrSubBase


@runtime_checkable
class HiLike[
  AnySequenceOfStrOrInlineBase: Sequence[str | BptLike | EptLike | ItLike | PhLike | HiLike]
](Protocol):
  x: int | None
  type: str | None
  content: AnySequenceOfStrOrInlineBase


@runtime_checkable
class ItLike[AnySequenceOfStrOrSubBase: Sequence[str | SubLike]](Protocol):
  pos: Pos
  x: int | None
  type: str | None
  content: AnySequenceOfStrOrSubBase


@runtime_checkable
class PhLike[AnySequenceOfStrOrSubBase: Sequence[str | SubLike]](Protocol):
  x: int | None
  type: str | None
  assoc: Assoc | None
  content: AnySequenceOfStrOrSubBase


@runtime_checkable
class SubLike[
  AnySequenceOfStrOrInlineBase: Sequence[str | BptLike | EptLike | ItLike | PhLike | HiLike]
](Protocol):
  datatype: str | None
  type: str | None
  content: AnySequenceOfStrOrInlineBase


@runtime_checkable
class TuvLike[
  AnySequenceOfProp: Sequence[PropLike],
  AnySequenceOfNote: Sequence[NoteLike],
  AnySequenceOfStrOrInlineBase: Sequence[str | BptLike | EptLike | ItLike | PhLike | HiLike],
](Protocol):
  lang: str
  o_encoding: str | None
  datatype: str | None
  usagecount: int | None
  lastusagedate: datetime | None
  creationtool: str | None
  creationtoolversion: str | None
  creationdate: datetime | None
  creationid: str | None
  changedate: datetime | None
  changeid: str | None
  o_tmf: str | None
  props: AnySequenceOfProp
  notes: AnySequenceOfNote
  content: AnySequenceOfStrOrInlineBase


@runtime_checkable
class TuLike[
  AnySequenceOfTuvBase: Sequence[TuvLike],
  AnySequenceOfProp: Sequence[PropLike],
  AnySequenceOfNote: Sequence[NoteLike],
](Protocol):
  tuid: str | None
  o_encoding: str | None
  datatype: str | None
  usagecount: int | None
  lastusagedate: datetime | None
  creationtool: str | None
  creationtoolversion: str | None
  creationdate: datetime | None
  creationid: str | None
  changedate: datetime | None
  segtype: Segtype | None
  changeid: str | None
  o_tmf: str | None
  srclang: str | None
  variants: AnySequenceOfTuvBase
  props: AnySequenceOfProp
  notes: AnySequenceOfNote


@runtime_checkable
class HeaderLike[AnySequenceOfProp: Sequence[PropLike], AnySequenceOfNote: Sequence[NoteLike]](
  Protocol
):
  creationtool: str
  creationtoolversion: str
  segtype: Segtype
  o_tmf: str
  adminlang: str
  srclang: str
  datatype: str
  o_encoding: str | None
  creationdate: datetime | None
  creationid: str | None
  changedate: datetime | None
  changeid: str | None
  props: AnySequenceOfProp
  notes: AnySequenceOfNote


@runtime_checkable
class TmxLike[AnySequenceOfTuBase: Sequence[TuLike]](Protocol):
  version: str
  header: HeaderLike[Sequence[PropLike], Sequence[NoteLike]]
  body: AnySequenceOfTuBase


@runtime_checkable
class NoteLike(Protocol):
  text: str
  lang: str | None
  o_encoding: str | None


@runtime_checkable
class PropLike(Protocol):
  text: str
  type: str
  lang: str | None
  o_encoding: str | None


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


@dataclass(slots=True)
class Prop:
  """Property element for tool-specific data.

  The ``<prop>`` element is used to define the various properties of the
  parent element (or of the document when ``<prop>`` is used in the
  ``<header>`` element). These properties are not defined by the TMX standard.

  As each tool is fully responsible for handling the content of a ``<prop>``
  element, it can be used in any way. For example, the content can be a list
  of instructions a tool can parse, not only simple text.

  It is the responsibility of each tool provider to publish the types and
  values of the properties it uses. If a tool exports unpublished property
  types, their values should begin with the prefix "x-".

  See Also:
      Note: For human-readable comments.
  """

  text: str
  """Tool-specific data or text content of the property."""

  type: str
  """Specifies the kind of data the property represents. Tool providers
    should publish the types they use."""

  lang: str | None = None
  """Language code (BCP-47) for the property content."""

  o_encoding: str | None = None
  """Original or preferred code set of the data in case it is to be
    re-encoded in a non-Unicode code set. One of the IANA recommended
    "charset identifiers", if possible."""


@dataclass(slots=True)
class Note:
  """Annotation element for comments.

  The ``<note>`` element is used for human-readable comments that can be
  attached to ``<header>``, ``<tu>``, or ``<tuv>`` elements.

  See Also:
      Prop: For tool-specific properties.
  """

  text: str
  """The note content (text)."""

  lang: str | None = None
  """Language code (BCP-47) for the note."""

  o_encoding: str | None = None
  """Original or preferred code set of the data in case it is to be
    re-encoded in a non-Unicode code set."""


@dataclass(slots=True)
class Header:
  """File header containing metadata about the TMX document.

  The ``<header>`` element contains information pertaining to the whole
  document. In addition to its attributes, ``<header>`` can also store
  document-level information in ``<note>`` and ``<prop>`` elements.

  Note:
      All datetime fields use ISO 8601 Format. The recommended pattern
      is: YYYYMMDDThhmmssZ (e.g., "20020125T210600Z").
  """

  creationtool: str
  """Identifies the tool that created the TMX document. Each tool provider
    should publish the string identifier it uses."""

  creationtoolversion: str
  """Identifies the version of the tool that created the TMX document."""

  segtype: Segtype
  """Specifies the kind of segmentation used in the translation units."""

  o_tmf: str
  """Original translation memory format. Specifies the format of the
    translation memory file from which the TMX document or segment thereof
    has been generated."""

  adminlang: str
  """Administrative language. Specifies the default language for the
    administrative and informative elements ``<note>`` and ``<prop>``.
    Unlike other TMX attributes, values are not case-sensitive."""

  srclang: str
  """Source language. Specifies the language of the source text. Can be
    set to "*all*" if any language can be used as the source. Unlike other
    TMX attributes, values are not case-sensitive."""

  datatype: str
  """Data type. Specifies the type of data contained in the element.
    Default is "unknown". Common values include: plaintext, html, xml,
    rtf, etc."""

  o_encoding: str | None = None
  """Original encoding. Specifies the original or preferred code set of
    the data in case it is to be re-encoded in a non-Unicode code set.
    One of the IANA recommended "charset identifiers", if possible."""

  creationdate: datetime | None = None
  """Creation date. Specifies the date of creation of the element."""

  creationid: str | None = None
  """Creation identifier. Specifies the identifier of the user who created
    the element."""

  changedate: datetime | None = None
  """Change date. Specifies the date of the last modification of the
    element."""

  changeid: str | None = None
  """Change identifier. Specifies the identifier of the user who modified
    the element last."""

  props: list[Prop] = field(default_factory=list)
  """Metadata properties."""

  notes: list[Note] = field(default_factory=list)
  """Annotation notes."""


class TextMixin:
  """Mixin providing text extraction from mixed content.

  This mixin provides quick access to the text portions of elements that
  contain mixed content (text strings and inline elements). Use this mixin
  on any class that has a ``content`` attribute containing a sequence of
  strings and inline elements.

  The ``text`` property concatenates all string items in the content,
  skipping any inline elements.
  """

  __slots__ = tuple()
  content: Sequence[str | Any]
  """Mixed content of strings and inline elements."""

  @property
  def text(self) -> str:
    """Extract plain text from mixed content.

    Concatenates all string items in content, skipping inline elements.

    Returns:
        Plain text without inline markup.
    """
    return "".join(item for item in self.content if isinstance(item, str))


@dataclass(slots=True)
class Bpt(TextMixin):
  """Begin paired tag - opening half of a paired list of native codes.

  The ``<bpt>`` element is used to delimit the beginning of a paired
  list of native codes. Each ``<bpt>`` has a corresponding ``<ept>``
  element within the segment.

  See Also:
      Ept: End paired tag that corresponds to this element.
  """

  i: int
  """Internal matching identifier. Used to pair ``<bpt>`` elements with
    their corresponding ``<ept>`` elements. Must be unique for each ``<bpt>``
    within a given segment."""

  x: int | None = None
  """External matching identifier. Used to match inline elements between
    each ``<tuv>`` element of a given ``<tu>`` element. This facilitates the
    pairing of allied codes in source and target text, even if the order of
    code occurrence differs."""

  type: str | None = None
  """Type of the native code. Recommended values include: bold, italic,
    link, font, color, underlined, etc."""

  content: list[str | Sub] = field(default_factory=list)
  """Code data (native codes), optionally with ``<sub>`` elements for
    sub-flow text."""


@dataclass(slots=True)
class Ept(TextMixin):
  """End paired tag - closing half of a paired list of native codes.

  The ``<ept>`` element is used to delimit the end of a paired list
  of native codes. Each ``<ept>`` has a corresponding ``<bpt>`` element
  within the segment.

  See Also:
      Bpt: Begin paired tag that corresponds to this element.
  """

  i: int
  """Internal matching identifier. Matches the ``i`` attribute of the
    corresponding ``<bpt>`` element."""

  content: list[str | Sub] = field(default_factory=list)
  """Code data (native codes), optionally with ``<sub>`` elements for
    sub-flow text."""


@dataclass(slots=True)
class Hi(TextMixin):
  """Highlight element for text with special meaning.

  The ``<hi>`` element delimits a section of text that has special meaning,
  such as a terminological unit, a proper name, an item that should not be
  modified, etc. It can be used for various processing tasks, such as
  indicating proper names to a Machine Translation tool or marking suspect
  expressions after grammar checking.
  """

  x: int | None = None
  """External matching identifier. Used to match inline elements between
    each ``<tuv>`` element of a given ``<tu>`` element."""

  type: str | None = None
  """Type of highlighting. Specifies what kind of special meaning the
    highlighted text has."""

  content: list[str | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
  """Text data mixed with inline elements (``<bpt>``, ``<ept>``, ``<it>``,
    ``<ph>``, and nested ``<hi>``)."""


@dataclass(slots=True)
class It(TextMixin):
  """Isolated tag - standalone code without its corresponding pair.

  The ``<it>`` element is used to delimit a beginning/ending list of
  native codes that does not have its corresponding ending/beginning within
  the segment. This occurs when segmentation breaks a paired list
  across segment boundaries.
  """

  pos: Pos
  """Position. Indicates whether the isolated tag is a beginning or an
    ending tag."""

  x: int | None = None
  """External matching identifier. Used to match inline elements between
    each ``<tuv>`` element of a given ``<tu>`` element."""

  type: str | None = None
  """Type of the native code."""

  content: list[str | Sub] = field(default_factory=list)
  """Code data, optionally with ``<sub>`` elements for sub-flow text."""


@dataclass(slots=True)
class Ph(TextMixin):
  """Placeholder element for standalone native codes.

  The ``<ph>`` element is used to delimit a list of native standalone
  codes in the segment. These are self-contained functions that do not
  require explicit ending instructions, such as image references,
  cross-reference tokens, line breaks, etc.
  """

  x: int | None = None
  """External matching identifier. Used to match inline elements between
    each ``<tuv>`` element of a given ``<tu>`` element."""

  type: str | None = None
  """Type of the native code. Recommended values include: index, date,
    time, fnote (footnote), enote (end-note), alt (alternate text), image,
    pb (page break), lb (line break), cb (column break), inset."""

  assoc: Assoc | None = None
  """Association. Indicates whether the placeholder is associated with the
    text preceding ("p"), following ("f"), or on both sides ("b")."""

  content: list[str | Sub] = field(default_factory=list)
  """Code data, optionally with ``<sub>`` elements for sub-flow text."""


@dataclass(slots=True)
class Sub(TextMixin):
  """Sub-flow element for text inside native codes.

  The ``<sub>`` element is used to delimit sub-flow text inside a list
  of native code, for example: the definition of a footnote, the text of
  a title in an HTML anchor element, or the content of an index marker.

  Note:
      Sub-flows are related to segmentation and can cause interoperability
      issues when one tool uses sub-flow within its main segment, while
      another extracts the sub-flow text as an independent segment.
  """

  datatype: str | None = None
  """Data type. Specifies the type of data contained in the sub-flow.
    Same values as the datatype attribute on other elements."""

  type: str | None = None
  """Type of the sub-flow."""

  content: list[str | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
  """Text data mixed with inline elements."""


@dataclass(slots=True)
class Tuv(TextMixin):
  """Translation Unit Variant - text in a specific language.

  The ``<tuv>`` element specifies text in a given language. It contains
  the segment text and information pertaining to that segment for the
  given language. Each ``<tuv>`` element must contain exactly one
  ``<seg>`` element.
  """

  lang: str
  """Language code (BCP-47) for this variant. Unlike other TMX attributes,
    the value is not case-sensitive."""

  o_encoding: str | None = None
  """Original encoding. Specifies the original or preferred code set of
    the data in case it is to be re-encoded in a non-Unicode code set."""

  datatype: str | None = None
  """Data type. Specifies the type of data contained in the element."""

  usagecount: int | None = None
  """Usage count. Specifies the number of times the content of this
    ``<tuv>`` has been accessed in the original TM environment."""

  lastusagedate: datetime | None = None
  """Last usage date. Specifies when the content was last accessed in the
    original TM environment."""

  creationtool: str | None = None
  """Creation tool. Identifies the tool that created this element."""

  creationtoolversion: str | None = None
  """Creation tool version. Identifies the version of the tool."""

  creationdate: datetime | None = None
  """Creation date. Specifies when this element was created."""

  creationid: str | None = None
  """Creation identifier. Specifies the identifier of the user who created
    this element."""

  changedate: datetime | None = None
  """Change date. Specifies when this element was last modified."""

  changeid: str | None = None
  """Change identifier. Specifies the identifier of the user who last
    modified this element."""

  o_tmf: str | None = None
  """Original translation memory format. Specifies the format of the TM
    file from which this element was generated."""

  props: list[Prop] = field(default_factory=list)
  """Tool-specific properties."""

  notes: list[Note] = field(default_factory=list)
  """Human-readable notes."""

  content: list[str | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
  """The segment content - text mixed with inline elements. In TMX XML,
    this corresponds to the content of the ``<seg>`` element."""


@dataclass(slots=True)
class Tu:
  """Translation Unit - a group of aligned segments in different languages.

  The ``<tu>`` element contains the data for a given translation unit.
  It groups multiple ``<tuv>`` elements (variants) that represent the same
  content in different languages. A complete translation memory database
  will contain at least two ``<tuv>`` elements in each ``<tu>``.
  """

  tuid: str | None = None
  """Translation unit identifier. Specifies an identifier for the ``<tu>``
    element. The value is not defined by the standard (it could be unique or
    not, numeric or alphanumeric). Text without white spaces."""

  o_encoding: str | None = None
  """Original encoding. Specifies the original or preferred code set of
    the data in case it is to be re-encoded in a non-Unicode code set."""

  datatype: str | None = None
  """Data type. Specifies the type of data contained in the element."""

  usagecount: int | None = None
  """Usage count. Specifies the number of times the content has been
    accessed in the original TM environment."""

  lastusagedate: datetime | None = None
  """Last usage date. Specifies when the content was last accessed."""

  creationtool: str | None = None
  """Creation tool. Identifies the tool that created this element."""

  creationtoolversion: str | None = None
  """Creation tool version. Identifies the version of the tool."""

  creationdate: datetime | None = None
  """Creation date. Specifies when this element was created."""

  creationid: str | None = None
  """Creation identifier. Specifies the identifier of the creator."""

  changedate: datetime | None = None
  """Change date. Specifies when this element was last modified."""

  segtype: Segtype | None = None
  """Segment type. Specifies the kind of segmentation used. If not
    specified, uses the value from the ``<header>`` element."""

  changeid: str | None = None
  """Change identifier. Specifies the identifier of the last modifier."""

  o_tmf: str | None = None
  """Original translation memory format. Specifies the format of the TM
    file from which this element was generated."""

  srclang: str | None = None
  """Source language. Specifies the language of the source text. The
    ``<tuv>`` holding the source segment will have its ``lang`` attribute
    set to the same value (unless srclang is "*all*"). If not specified,
    uses the value from the ``<header>`` element."""

  props: list[Prop] = field(default_factory=list)
  """Tool-specific properties."""

  notes: list[Note] = field(default_factory=list)
  """Human-readable notes."""

  variants: list[Tuv] = field(default_factory=list)
  """Language variants. One ``<tuv>`` element for each language."""


@dataclass(slots=True)
class Tmx:
  """Root element for TMX documents.

  The ``<tmx>`` element is the root element that encloses all other
  elements of the TMX document. It contains exactly one ``<header>``
  element followed by one ``<body>`` element.
  """

  header: Header
  """File header containing metadata about the document."""

  version: str = "1.4"
  """TMX version number. Format is major.minor (e.g., "1.4")."""

  body: list[Tu] = field(default_factory=list)
  """Collection of translation units (``<tu>`` elements)."""
