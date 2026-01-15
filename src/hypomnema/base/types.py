"""
TMX 1.4b object model with type-safe inline markup support.

This package provides dataclasses that map 1-to-1 to TMX 1.4b
elements.  Generic type parameters let callers swap ``list`` for any
``Iterable`` (tuple, set, generator) to fit their performance or
immutability needs.

All datetime values must be ISO-8601 strings ending with 'Z' and
seconds precision, e.g. ``2025-12-31T23:59:59Z``. As per the TMX 1.4b
official specification, the recommended date format is ``YYYYMMDDTHHMMSSZ``.
Language codes should be BCP-47; Enforcement will tighten in a future release.
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
  Position of an isolated tag (`<it>`).
  """

  BEGIN = "begin"
  """Tag opens at this point."""

  END = "end"
  """Tag closes at this point."""


class Assoc(StrEnum):
  """
  Association of a placeholder (`<ph>`) with surrounding text.
  """

  P = "p"
  """Previous – placeholder belongs to the text before it."""

  F = "f"
  """Following – placeholder belongs to the text after it."""

  B = "b"
  """Both – placeholder belongs to both sides."""


class Segtype(StrEnum):
  """
  Segmentation level declared in the header or override in `<tu>`.
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
  Property attached to `<header>`, `<tu>` or `<tuv>`.
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
  Note attached to `<header>`, `<tu>` or `<tuv>`.
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
  TMX header element (`<header>`).
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
  Begin paired tag (`<bpt>`) – opening half of an inline tag pair.
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
  End paired tag (`<ept>`) – closing half of an inline tag pair.
  """

  i: int
  """Unique identifier matching the corresponding `<bpt>`."""

  content: IterableOfSubElementsAndStr = field(default_factory=list)
  """Mixed inline content (optional)."""


@dataclass(slots=True)
class Hi(Generic[IterableOfInlineElementsAndStr]):
  """
  Highlighted inline span (`<hi>`).
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
  Isolated tag (`<it>`) – standalone placeholder.
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
  Placeholder tag (`<ph>`) – replaces a native code fragment.
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
  Sub-flow segment (`<sub>`) – nested translatable unit.
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
  Translation unit variant (`<tuv>`) – one language version of a `<tu>`.
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
  Translation unit (`<tu>`) – container for one or more `<tuv>` variants.
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
  Root TMX container (`<tmx>`).
  """

  header: Header
  """Global metadata for the file."""

  version: str = "1.4"
  """TMX version (fixed to "1.4" for this model)."""

  body: IterableOfTus = field(default_factory=list)
  """Container of translation units (optional)."""


type BaseElement = Tmx | Header | Prop | Note | Tu | Tuv | Bpt | Ept | It | Ph | Hi | Sub
type InlineElement = Bpt | Ept | It | Ph | Hi | Sub
