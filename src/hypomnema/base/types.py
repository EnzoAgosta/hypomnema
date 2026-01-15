"""
TMX 1.4b object model with type-safe inline markup support.

This package provides dataclasses that map 1-to-1 to TMX 1.4b
elements as defined in the `TMX 1.4b specification
<https://resources.gala-global.org/tbx14b>`_.

All datetime values must be ISO-8601 strings ending with 'Z' and
seconds precision, e.g. ``2025-12-31T23:59:59Z``. Language codes
should be BCP-47.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

__all__ = [
  # type aliases
  "BaseElement",
  "InlineElement",
  # Enums
  "Assoc",
  "Pos",
  "Segtype",
  # Inline elements
  "Bpt",
  "Ept",
  "Hi",
  "It",
  "Ph",
  "Sub",
  # Structural elements
  "Header",
  "Note",
  "Prop",
  "Tmx",
  "Tu",
  "Tuv",
]


class Pos(StrEnum):
  """
  Position of an isolated tag (``<it>``) per TMX 1.4b spec.

  Indicates whether an ``<it>`` element represents a beginning or
  ending tag when the corresponding code is not within the same segment.
  """

  BEGIN = "begin"
  """Tag opens at this point."""

  END = "end"
  """Tag closes at this point."""


class Assoc(StrEnum):
  """
  Association of a placeholder (``<ph>``) per TMX 1.4b spec.

  Indicates whether the placeholder belongs to the text before,
  after, or on both sides of the element.
  """

  P = "p"
  """Previous – placeholder belongs to the text before it."""

  F = "f"
  """Following – placeholder belongs to the text after it."""

  B = "b"
  """Both – placeholder belongs to both sides."""


class Segtype(StrEnum):
  """
  Segmentation level per TMX 1.4b spec.

  Specifies the kind of segmentation used in a ``<tu>`` element.
  If not specified, falls back to the value defined in the ``<header>``.
  """

  BLOCK = "block"
  """Block level segmentation."""

  PARAGRAPH = "paragraph"
  """Paragraph level segmentation."""

  SENTENCE = "sentence"
  """Sentence level segmentation."""

  PHRASE = "phrase"
  """Phrase level segmentation."""


@dataclass(slots=True)
class Prop:
  """
  Property element (``<prop>``) per TMX 1.4b spec.

  Used to define various properties of the parent element. These
  properties are not defined by the standard; each tool provider is
  responsible for the types and values it uses.

  Attributes
  ----------
  text : str
      The property value.
  type : str
      The property name (user-defined).
  lang : str | None
      BCP-47 language code for the property text.
  o_encoding : str | None
      Original encoding of the property text.
  """

  text: str
  """Property value."""

  type: str
  """Property name (user-defined)."""

  lang: str | None = None
  """BCP-47 language code for the property text (optional)."""

  o_encoding: str | None = None
  """Original encoding (maps to `o-encoding` in TMX) (optional)."""


@dataclass(slots=True)
class Note:
  """
  Note element (``<note>``) per TMX 1.4b spec.

  Used for comments attached to ``<header>``, ``<tu>``, or ``<tuv>``.

  Attributes
  ----------
  text : str
      The note content.
  lang : str | None
      BCP-47 language code for the note text.
  o_encoding : str | None
      Original encoding of the note text.
  """

  text: str
  """Note content."""

  lang: str | None = None
  """BCP-47 language code for the note text (optional)."""

  o_encoding: str | None = None
  """Original encoding (maps to `o-encoding` in TMX) (optional)."""


IterableOfProps = TypeVar("IterableOfProps", bound=Iterable[Prop], default=list[Prop])
IterableOfNotes = TypeVar("IterableOfNotes", bound=Iterable[Note], default=list[Note])


@dataclass(slots=True)
class Header(Generic[IterableOfProps, IterableOfNotes]):
  """
  Header element (``<header>``) per TMX 1.4b spec.

  Contains metadata about the entire TMX document.

  Attributes
  ----------
  creationtool : str
      Name of the tool that created the file.
  creationtoolversion : str
      Version of the tool that created the file.
  segtype : Segtype
      Default segmentation level for the file.
  o_tmf : str
      Original TMF format (maps to ``o-tmf`` in TMX).
  adminlang : str
      Language used for administrative attributes (BCP-47).
  srclang : str
      Source language code for all ``<tu>`` elements (BCP-47).
  datatype : str
      Data type declared for the file.
  o_encoding : str | None
      Original encoding of the file.
  creationdate : datetime | None
      File creation timestamp (ISO-8601 with 'Z').
  creationid : str | None
      User that created the file.
  changedate : datetime | None
      Last change timestamp (ISO-8601 with 'Z').
  changeid : str | None
      User that last changed the file.
  props : IterableOfProps
      Collection of ``<prop>`` elements.
  notes : IterableOfNotes
      Collection of ``<note>`` elements.
  """

  creationtool: str
  """Name of the tool that created the file."""

  creationtoolversion: str
  """Version of the tool."""

  segtype: Segtype
  """Default segmentation level for the file."""

  o_tmf: str
  """Original TMF format (maps to `o-tmf` in TMX)."""

  adminlang: str
  """Language used for administrative attributes (BCP-47)."""

  srclang: str
  """Source language code for all `<tu>` elements (BCP-47)."""

  datatype: str
  """Data type declared for the file."""

  o_encoding: str | None = None
  """Original encoding (maps to `o-encoding` in TMX) (optional)."""

  creationdate: datetime | None = None
  """File creation time (ISO-8601 with 'Z') (optional)."""

  creationid: str | None = None
  """User that created the file (optional)."""

  changedate: datetime | None = None
  """Last change time (ISO-8601 with 'Z') (optional)."""

  changeid: str | None = None
  """User that last changed the file (optional)."""

  props: IterableOfProps = field(default_factory=list)
  """Container of custom properties (optional)."""

  notes: IterableOfNotes = field(default_factory=list)
  """Container of notes (optional)."""


IterableOfSubElementsAndStr = TypeVar(
  "IterableOfSubElementsAndStr", bound=Iterable["Sub | str"], default=list["Sub | str"]
)
IterableOfInlineElementsAndStr = TypeVar(
  "IterableOfInlineElementsAndStr",
  bound=Iterable["Bpt | Ept | It | Ph | Hi | Sub | str"],
  default=list["Bpt | Ept | It | Ph | Hi | Sub | str"],
)


@dataclass(slots=True)
class Bpt(Generic[IterableOfSubElementsAndStr]):
  """
  Begin paired tag element (``<bpt>``) per TMX 1.4b spec.

  Delimits the beginning of a paired sequence of native codes.
  Each ``<bpt>`` has a corresponding ``<ept>`` within the segment.

  Attributes
  ----------
  i : int
      Unique identifier matching the corresponding ``<ept>``.
  x : int | None
      External reference identifier.
  type : str | None
      Tag type (user-defined).
  content : IterableOfSubElementsAndStr
      Mixed inline content (code data and ``<sub>`` elements).
  """

  i: int
  """Unique identifier matching the corresponding `<ept>`."""

  x: int | None = None
  """External reference identifier (optional)."""

  type: str | None = None
  """Tag type (user-defined) (optional)."""

  content: IterableOfSubElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class Ept(Generic[IterableOfSubElementsAndStr]):
  """
  End paired tag element (``<ept>``) per TMX 1.4b spec.

  Delimits the end of a paired sequence of native codes.
  Each ``<ept>`` has a corresponding ``<bpt>`` within the segment.

  Attributes
  ----------
  i : int
      Unique identifier matching the corresponding ``<bpt>``.
  content : IterableOfSubElementsAndStr
      Mixed inline content (code data and ``<sub>`` elements).
  """

  i: int
  """Unique identifier matching the corresponding `<bpt>`."""

  content: IterableOfSubElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class Hi(Generic[IterableOfInlineElementsAndStr]):
  """
  Highlight element (``<hi>``) per TMX 1.4b spec.

  Delimits a section of text that has special meaning, such as a
  terminological unit, proper name, or text that should not be modified.

  Attributes
  ----------
  x : int | None
      External reference identifier.
  type : str | None
      Highlight type (user-defined).
  content : IterableOfInlineElementsAndStr
      Mixed inline content (text and inline elements).
  """

  x: int | None = None
  """External reference identifier (optional)."""

  type: str | None = None
  """Highlight type (user-defined) (optional)."""

  content: IterableOfInlineElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class It(Generic[IterableOfSubElementsAndStr]):
  """
  Isolated tag element (``<it>``) per TMX 1.4b spec.

  Delimits a beginning/ending sequence of native codes that does not
  have its corresponding ending/beginning within the same segment
  (e.g., due to segmentation).

  Attributes
  ----------
  pos : Pos
      Whether the tag is opening (``begin``) or closing (``end``).
  x : int | None
      External reference identifier.
  type : str | None
      Tag type (user-defined).
  content : IterableOfSubElementsAndStr
      Mixed inline content (code data and ``<sub>`` elements).
  """

  pos: Pos
  """Whether the tag is opening or closing."""

  x: int | None = None
  """External reference identifier (optional)."""

  type: str | None = None
  """Tag type (user-defined) (optional)."""

  content: IterableOfSubElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class Ph(Generic[IterableOfSubElementsAndStr]):
  """
  Placeholder element (``<ph>``) per TMX 1.4b spec.

  Delimits a sequence of native standalone codes in the segment
  (e.g., empty elements in XML, image tags, cross-references).

  Attributes
  ----------
  x : int | None
      External reference identifier.
  type : str | None
      Placeholder type (user-defined).
  assoc : Assoc | None
      Association with surrounding text.
  content : IterableOfSubElementsAndStr
      Mixed inline content (code data and ``<sub>`` elements).
  """

  x: int | None = None
  """External reference identifier (optional)."""

  type: str | None = None
  """Placeholder type (user-defined) (optional)."""

  assoc: Assoc | None = None
  """Association with surrounding text (optional)."""

  content: IterableOfSubElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class Sub(Generic[IterableOfInlineElementsAndStr]):
  """
  Sub-flow element (``<sub>``) per TMX 1.4b spec.

  Delimits sub-flow text inside a sequence of native code, such as
  the text of a footnote or the title in an HTML anchor element.

  Attributes
  ----------
  datatype : str | None
      Data type of the sub-flow.
  type : str | None
      Sub-flow type (user-defined).
  content : IterableOfInlineElementsAndStr
      Mixed inline content (text and inline elements).
  """

  datatype: str | None = None
  """Data type of the sub-flow (optional)."""

  type: str | None = None
  """Sub-flow type (user-defined) (optional)."""

  content: IterableOfInlineElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class Tuv(Generic[IterableOfProps, IterableOfNotes, IterableOfInlineElementsAndStr]):
  """
  Translation unit variant element (``<tuv>``) per TMX 1.4b spec.

  Specifies text in a given language. Contains the segment content
  and metadata for that language variant.

  Attributes
  ----------
  lang : str
      Language code (BCP-47, maps to ``xml:lang``).
  o_encoding : str | None
      Original encoding of the variant text.
  datatype : str | None
      Override data type for this variant.
  usagecount : int | None
      Number of times the variant has been reused.
  lastusagedate : datetime | None
      Last reuse timestamp (ISO-8601 with 'Z').
  creationtool : str | None
      Tool that created this variant.
  creationtoolversion : str | None
      Version of the tool.
  creationdate : datetime | None
      Creation timestamp (ISO-8601 with 'Z').
  creationid : str | None
      User that created the variant.
  changedate : datetime | None
      Last change timestamp (ISO-8601 with 'Z').
  changeid : str | None
      User that last changed the variant.
  o_tmf : str | None
      Original TMF format for this variant.
  props : IterableOfProps
      Collection of ``<prop>`` elements.
  notes : IterableOfNotes
      Collection of ``<note>`` elements.
  content : IterableOfInlineElementsAndStr
      Mixed inline content representing ``<seg>``.
  """

  lang: str
  """Target language code (BCP-47)."""

  o_encoding: str | None = None
  """Original encoding (maps to `o-encoding` in TMX) (optional)."""

  datatype: str | None = None
  """Override data type for this variant (optional)."""

  usagecount: int | None = None
  """Number of times the variant has been reused (optional)."""

  lastusagedate: datetime | None = None
  """Last reuse time (ISO-8601 with 'Z') (optional)."""

  creationtool: str | None = None
  """Tool that created this variant (optional)."""

  creationtoolversion: str | None = None
  """Version of that tool (optional)."""

  creationdate: datetime | None = None
  """Creation time (ISO-8601 with 'Z') (optional)."""

  creationid: str | None = None
  """User that created the variant (optional)."""

  changedate: datetime | None = None
  """Last change time (ISO-8601 with 'Z') (optional)."""

  changeid: str | None = None
  """User that last changed the variant (optional)."""

  o_tmf: str | None = None
  """Original TMF format (maps to `o-tmf` in TMX) (optional)."""

  props: IterableOfProps = field(default_factory=list)
  """Container of custom properties (optional)."""

  notes: IterableOfNotes = field(default_factory=list)
  """Container of notes (optional)."""

  content: IterableOfInlineElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


IterableOfTuvs = TypeVar("IterableOfTuvs", bound=Iterable[Tuv], default=list[Tuv])


@dataclass(slots=True)
class Tu(Generic[IterableOfNotes, IterableOfProps, IterableOfTuvs]):
  """
  Translation unit element (``<tu>``) per TMX 1.4b spec.

  Container for one or more ``<tuv>`` language variants. Each TU
  represents a single translation memory entry.

  Attributes
  ----------
  tuid : str | None
      Unique identifier for the unit.
  o_encoding : str | None
      Original encoding of the unit text.
  datatype : str | None
      Override data type for this unit.
  usagecount : int | None
      Number of times the unit has been reused.
  lastusagedate : datetime | None
      Last reuse timestamp (ISO-8601 with 'Z').
  creationtool : str | None
      Tool that created the unit.
  creationtoolversion : str | None
      Version of the tool.
  creationdate : datetime | None
      Creation timestamp (ISO-8601 with 'Z').
  creationid : str | None
      User that created the unit.
  changedate : datetime | None
      Last change timestamp (ISO-8601 with 'Z').
  changeid : str | None
      User that last changed the unit.
  segtype : Segtype | None
      Override segmentation level for this unit.
  o_tmf : str | None
      Original TMF format for this unit.
  srclang : str | None
      Source language code (BCP-47), overrides header value if specified.
  props : IterableOfProps
      Collection of ``<prop>`` elements.
  notes : IterableOfNotes
      Collection of ``<note>`` elements.
  variants : IterableOfTuvs
      Collection of ``<tuv>`` language variants.
  """

  tuid: str | None = None
  """Unique identifier for the unit (optional)."""

  o_encoding: str | None = None
  """Original encoding (maps to `o-encoding` in TMX) (optional)."""

  datatype: str | None = None
  """Override data type for this unit (optional)."""

  usagecount: int | None = None
  """Number of times the unit has been reused (optional)."""

  lastusagedate: datetime | None = None
  """Last reuse time (ISO-8601 with 'Z') (optional)."""

  creationtool: str | None = None
  """Tool that created the unit (optional)."""

  creationtoolversion: str | None = None
  """Version of that tool (optional)."""

  creationdate: datetime | None = None
  """Creation time (ISO-8601 with 'Z') (optional)."""

  creationid: str | None = None
  """User that created the unit (optional)."""

  changedate: datetime | None = None
  """Last change time (ISO-8601 with 'Z') (optional)."""

  segtype: Segtype | None = None
  """Override segmentation level for this unit (optional)."""

  changeid: str | None = None
  """User that last changed the unit (optional)."""

  o_tmf: str | None = None
  """Original TMF format (maps to `o-tmf` in TMX) (optional)."""

  srclang: str | None = None
  """Source language code (BCP-47) when differing from header (optional)."""

  props: IterableOfProps = field(default_factory=list)
  """Container of custom properties (optional)."""

  notes: IterableOfNotes = field(default_factory=list)
  """Container of notes (optional)."""

  variants: IterableOfTuvs = field(default_factory=list)
  """Container of language variants (optional)."""


IterableOfTus = TypeVar("IterableOfTus", bound=Iterable[Tu], default=list[Tu])


@dataclass(slots=True)
class Tmx(Generic[IterableOfTus]):
  """
  Root TMX container element (``<tmx>``) per TMX 1.4b spec.

  Encloses all other elements of a TMX document. Contains a single
  ``<header>`` followed by a ``<body>``.

  Attributes
  ----------
  header : Header
      Global metadata for the file.
  version : str
      TMX version (fixed to "1.4" per spec).
  body : IterableOfTus
      Collection of ``<tu>`` translation units.
  """

  header: Header
  """Global metadata for the file."""

  version: str = "1.4"
  """TMX version (fixed to "1.4" for this model)."""

  body: IterableOfTus = field(default_factory=list)
  """Container of translation units (optional)."""


type BaseElement = Tmx | Header | Prop | Note | Tu | Tuv | Bpt | Ept | It | Ph | Hi | Sub
"""Type alias for all structural TMX elements."""

type InlineElement = Bpt | Ept | It | Ph | Hi | Sub
"""Type alias for inline content markup elements."""
