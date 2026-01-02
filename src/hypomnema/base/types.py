from __future__ import annotations
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

__all__ = [
  "BaseElement",
  "Bpt",
  "Ept",
  "Hi",
  "It",
  "Ph",
  "Sub",
  "Pos",
  "Segtype",
  "Assoc",
  "Header",
  "Note",
  "Prop",
  "Tu",
  "Tuv",
  "Tmx",
]

type BaseElement = Tmx | Header | Prop | Note | Tu | Tuv | Bpt | Ept | It | Ph | Hi | Sub
type InlineElementAndStr = str | Bpt | Ept | It | Ph | Hi
type SubElementAndStr = str | Sub

IterableOfProps = TypeVar("IterableOfProps", bound=Iterable["Prop"])
IterableOfNotes = TypeVar("IterableOfNotes", bound=Iterable["Note"])
IterableOfInlineElementsAndStr = TypeVar(
  "IterableOfInlineElementsAndStr", bound=Iterable[InlineElementAndStr]
)
IterableOfSubElementsAndStr = TypeVar(
  "IterableOfSubElementsAndStr", bound=Iterable[SubElementAndStr]
)
IterableOfTuvs = TypeVar("IterableOfTuvs", bound=Iterable["Tuv"])
IterableOfTus = TypeVar("IterableOfTus", bound=Iterable["Tu"])


class Pos(StrEnum):
  BEGIN = "begin"
  END = "end"


class Assoc(StrEnum):
  P = "p"
  F = "f"
  B = "b"


class Segtype(StrEnum):
  BLOCK = "block"
  PARAGRAPH = "paragraph"
  SENTENCE = "sentence"
  PHRASE = "phrase"


@dataclass(slots=True)
class Prop:
  text: str
  type: str
  lang: str | None = None
  o_encoding: str | None = None


@dataclass(slots=True)
class Note:
  text: str
  lang: str | None = None
  o_encoding: str | None = None


@dataclass(slots=True)
class Header(Generic[IterableOfProps, IterableOfNotes]):
  creationtool: str
  creationtoolversion: str
  segtype: Segtype
  o_tmf: str
  adminlang: str
  srclang: str
  datatype: str
  o_encoding: str | None = None
  creationdate: datetime | None = None
  creationid: str | None = None
  changedate: datetime | None = None
  changeid: str | None = None
  props: IterableOfProps = field(default_factory=list)
  notes: IterableOfNotes = field(default_factory=list)


@dataclass(slots=True)
class Bpt(Generic[IterableOfSubElementsAndStr]):
  i: int
  x: int | None = None
  type: str | None = None
  content: IterableOfSubElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class Ept(Generic[IterableOfSubElementsAndStr]):
  i: int
  content: IterableOfSubElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class Hi(Generic[IterableOfInlineElementsAndStr]):
  x: int | None = None
  type: str | None = None
  content: IterableOfInlineElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class It(Generic[IterableOfSubElementsAndStr]):
  pos: Pos
  x: int | None = None
  type: str | None = None
  content: IterableOfSubElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class Ph(Generic[IterableOfSubElementsAndStr]):
  x: int | None = None
  type: str | None = None
  assoc: Assoc | None = None
  content: IterableOfSubElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class Sub(Generic[IterableOfInlineElementsAndStr]):
  datatype: str | None = None
  type: str | None = None
  content: IterableOfInlineElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class Tuv(Generic[IterableOfProps, IterableOfNotes, IterableOfInlineElementsAndStr]):
  lang: str
  o_encoding: str | None = None
  datatype: str | None = None
  usagecount: int | None = None
  lastusagedate: datetime | None = None
  creationtool: str | None = None
  creationtoolversion: str | None = None
  creationdate: datetime | None = None
  creationid: str | None = None
  changedate: datetime | None = None
  changeid: str | None = None
  o_tmf: str | None = None
  props: IterableOfProps = field(default_factory=list)
  notes: IterableOfNotes = field(default_factory=list)
  content: IterableOfInlineElementsAndStr = field(default_factory=list)


@dataclass(slots=True)
class Tu(Generic[IterableOfNotes, IterableOfProps, IterableOfTuvs]):
  tuid: str | None = None
  o_encoding: str | None = None
  datatype: str | None = None
  usagecount: int | None = None
  lastusagedate: datetime | None = None
  creationtool: str | None = None
  creationtoolversion: str | None = None
  creationdate: datetime | None = None
  creationid: str | None = None
  changedate: datetime | None = None
  segtype: Segtype | None = None
  changeid: str | None = None
  o_tmf: str | None = None
  srclang: str | None = None
  props: IterableOfProps = field(default_factory=list)
  notes: IterableOfNotes = field(default_factory=list)
  variants: IterableOfTuvs = field(default_factory=list)


@dataclass(slots=True)
class Tmx(Generic[IterableOfTus]):
  version: str
  header: Header
  body: IterableOfTus = field(default_factory=list)
