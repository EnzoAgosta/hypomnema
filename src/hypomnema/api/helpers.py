"""Factory functions for creating TMX elements.

This module provides convenience functions for constructing TMX dataclass
instances. These helpers handle common defaults, type conversions, and
validation to simplify element creation.
"""

from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from importlib.metadata import version
from typing import Literal

from hypomnema.base.types import (
  Assoc,
  Bpt,
  Ept,
  Header,
  Hi,
  InlineElement,
  It,
  Note,
  Ph,
  Pos,
  Prop,
  Segtype,
  Sub,
  Tmx,
  Tu,
  Tuv,
)


def iter_text(
  source: Tuv | InlineElement, *, ignore: Iterable[type[InlineElement]] | None = None
) -> Generator[str]:
  """Iterate over text content, optionally skipping specific element types.

  Extracts text from mixed content, optionally ignoring specified
  inline element types.

  Args:
      source: Element to extract text from.
      ignore: Element types to skip during text extraction.

  Yields:
      Text segments from the content.

  Example:
      >>> tuv = create_tuv("en", content=["Hello ", create_bpt(i=1), "World"])
      >>> list(iter_text(tuv))
      ['Hello ', 'World']
      >>> list(iter_text(tuv, ignore=[Bpt]))
      ['Hello ', 'World']
  """

  def _iter_text(
    _source: InlineElement | Tuv, _ignore: tuple[type[InlineElement], ...]
  ) -> Generator[str]:
    for item in _source.content:
      if isinstance(item, str):
        if not isinstance(_source, _ignore):
          yield item
      else:
        yield from _iter_text(item, _ignore=_ignore)

  ignore = tuple(ignore) if ignore else ()
  yield from _iter_text(source, _ignore=ignore)


def _normalize_content[T](content: Iterable[T] | str | None) -> list[T | str]:
  """Normalize content parameter to a list.

  Internal helper that converts string to single-item list or
  wraps iterable in list.

  Args:
      content: Content to normalize.

  Returns:
      Normalized list of content items.

  Note:
      This is a private function intended for internal use by factory functions.
  """
  if isinstance(content, str):
    return [content]
  return list(content) if content is not None else []


def create_tmx(
  *, header: Header | None = None, body: Iterable[Tu] | None = None, version: str = "1.4"
) -> Tmx:
  """Create a TMX root element.

  Args:
      header: The header element. If None, a default header is created.
      body: Collection of translation units.
      version: TMX version number (default: "1.4").

  Returns:
      Configured TMX root element.
  """
  if header is None:
    header = create_header()
  if body is None:
    body = []
  return Tmx(header=header, body=list(body), version=version or "1.4")


def create_header(
  *,
  creationtool: str = "hypomnema",
  creationtoolversion: str = version("hypomnema"),
  segtype: Segtype | Literal["block", "paragraph", "sentence", "phrase"] = Segtype.BLOCK,
  o_tmf: str = "tmx",
  adminlang: str = "en",
  srclang: str = "en",
  datatype: str = "plaintext",
  o_encoding: str | None = None,
  creationdate: datetime | None = None,
  creationid: str | None = None,
  changedate: datetime | None = None,
  changeid: str | None = None,
  notes: Iterable[Note] | None = None,
  props: Iterable[Prop] | None = None,
) -> Header:
  """Create a TMX header element.

  Args:
      creationtool: Name of the creating tool.
      creationtoolversion: Version of the creating tool.
      segtype: Segmentation level (block, paragraph, sentence, phrase).
      o_tmf: Original translation memory format.
      adminlang: Administrative language (BCP-47).
      srclang: Source language (BCP-47).
      datatype: Data type (e.g., "plaintext", "html").
      o_encoding: Original encoding reference.
      creationdate: Creation timestamp (defaults to now).
      creationid: Creator identifier.
      changedate: Last modification timestamp.
      changeid: Last modifier identifier.
      notes: Header notes.
      props: Header properties.

  Returns:
      Configured header element.
  """
  segtype = Segtype(segtype) if isinstance(segtype, str) else segtype
  notes = list(notes) if notes is not None else []
  props = list(props) if props is not None else []
  creationdate = creationdate if creationdate is not None else datetime.now(UTC)

  return Header(
    creationtool=creationtool,
    creationtoolversion=creationtoolversion,
    segtype=segtype,
    o_tmf=o_tmf,
    adminlang=adminlang,
    srclang=srclang,
    datatype=datatype,
    o_encoding=o_encoding,
    creationdate=creationdate,
    creationid=creationid,
    changedate=changedate,
    changeid=changeid,
    notes=notes,
    props=props,
  )


def create_tu(
  *,
  tuid: str | None = None,
  srclang: str | None = None,
  segtype: Segtype | str | None = None,
  variants: Iterable[Tuv] | None = None,
  o_encoding: str | None = None,
  datatype: str | None = None,
  usagecount: int | None = None,
  lastusagedate: datetime | None = None,
  creationtool: str | None = None,
  creationtoolversion: str | None = None,
  creationdate: datetime | None = None,
  creationid: str | None = None,
  changedate: datetime | None = None,
  changeid: str | None = None,
  o_tmf: str | None = None,
  notes: Iterable[Note] | None = None,
  props: Iterable[Prop] | None = None,
) -> Tu:
  """Create a translation unit (TU) element.

  Args:
      tuid: Unique identifier for this TU.
      srclang: Source language override.
      segtype: Segmentation type.
      variants: Language variants.
      o_encoding: Original encoding reference.
      datatype: Data type.
      usagecount: Usage count.
      lastusagedate: Last usage timestamp.
      creationtool: Creating tool name.
      creationtoolversion: Creating tool version.
      creationdate: Creation timestamp (defaults to now).
      creationid: Creator identifier.
      changedate: Last modification timestamp.
      changeid: Last modifier identifier.
      o_tmf: Original TM format.
      notes: TU notes.
      props: TU properties.

  Returns:
      Configured translation unit.
  """
  segtype = Segtype(segtype) if isinstance(segtype, str) else segtype
  variants = list(variants) if variants is not None else []
  notes = list(notes) if notes is not None else []
  props = list(props) if props is not None else []
  creationdate = creationdate if creationdate is not None else datetime.now(UTC)

  return Tu(
    tuid=tuid,
    srclang=srclang,
    segtype=segtype,
    variants=variants,
    o_encoding=o_encoding,
    datatype=datatype,
    usagecount=usagecount,
    lastusagedate=lastusagedate,
    creationtool=creationtool,
    creationtoolversion=creationtoolversion,
    creationdate=creationdate,
    creationid=creationid,
    changedate=changedate,
    changeid=changeid,
    o_tmf=o_tmf,
    notes=notes,
    props=props,
  )


def create_tuv(
  lang: str,
  *,
  content: Iterable[str | Bpt | Ept | It | Ph | Hi] | str | None = None,
  o_encoding: str | None = None,
  datatype: str | None = None,
  usagecount: int | None = None,
  lastusagedate: datetime | None = None,
  creationtool: str | None = None,
  creationtoolversion: str | None = None,
  creationdate: datetime | None = None,
  creationid: str | None = None,
  changedate: datetime | None = None,
  changeid: str | None = None,
  o_tmf: str | None = None,
  notes: Iterable[Note] | None = None,
  props: Iterable[Prop] | None = None,
) -> Tuv:
  """Create a translation unit variant (TUV) element.

  Args:
      lang: Language code (BCP-47) for this variant.
      content: Translatable content: text and inline elements.
      o_encoding: Original encoding reference.
      datatype: Data type.
      usagecount: Usage count.
      lastusagedate: Last usage timestamp.
      creationtool: Creating tool name.
      creationtoolversion: Creating tool version.
      creationdate: Creation timestamp.
      creationid: Creator identifier.
      changedate: Last modification timestamp.
      changeid: Last modifier identifier.
      o_tmf: Original TM format.
      notes: TUV notes.
      props: TUV properties.

  Returns:
      Configured translation unit variant.
  """
  content = _normalize_content(content)
  notes = list(notes) if notes is not None else []
  props = list(props) if props is not None else []

  return Tuv(
    lang=lang,
    content=content,
    o_encoding=o_encoding,
    datatype=datatype,
    usagecount=usagecount,
    lastusagedate=lastusagedate,
    creationtool=creationtool,
    creationtoolversion=creationtoolversion,
    creationdate=creationdate,
    creationid=creationid,
    changedate=changedate,
    changeid=changeid,
    o_tmf=o_tmf,
    notes=notes,
    props=props,
  )


def create_note(text: str, *, lang: str | None = None, o_encoding: str | None = None) -> Note:
  """Create a note element.

  Args:
      text: Note content.
      lang: Language code (BCP-47).
      o_encoding: Original encoding reference.

  Returns:
      Configured note element.
  """
  return Note(text=text, lang=lang, o_encoding=o_encoding)


def create_prop(
  text: str, type: str, *, lang: str | None = None, o_encoding: str | None = None
) -> Prop:
  """Create a property element.

  Args:
      text: Property value.
      type: Property type/key.
      lang: Language code (BCP-47).
      o_encoding: Original encoding reference.

  Returns:
      Configured property element.
  """
  return Prop(text=text, type=type, lang=lang, o_encoding=o_encoding)


def create_bpt(
  i: int,
  *,
  content: Iterable[str | Sub] | str | None = None,
  x: int | None = None,
  type: str | None = None,
) -> Bpt:
  """Create a begin paired tag (BPT) element.

  Args:
      i: Internal matching identifier linking to corresponding EPT.
      content: Code data with optional sub-flow elements.
      x: External matching identifier for cross-language pairing.
      type: Tag type (e.g., "bold", "italic", "link").

  Returns:
      Configured begin paired tag.
  """
  content = _normalize_content(content)
  return Bpt(i=i, x=x, type=type, content=content)


def create_ept(i: int, *, content: Iterable[str | Sub] | str | None = None) -> Ept:
  """Create an end paired tag (EPT) element.

  Args:
      i: Internal matching identifier linking to corresponding BPT.
      content: Code data with optional sub-flow elements.

  Returns:
      Configured end paired tag.
  """
  content = _normalize_content(content)
  return Ept(i=i, content=content)


def create_it(
  pos: Pos | Literal["begin", "end"],
  *,
  content: Iterable[str | Sub] | str | None = None,
  x: int | None = None,
  type: str | None = None,
) -> It:
  """Create an isolated tag (IT) element.

  Args:
      pos: Position (BEGIN or END of segment).
      content: Code data with optional sub-flow elements.
      x: External matching identifier for cross-language pairing.
      type: Tag type.

  Returns:
      Configured isolated tag.
  """
  content = _normalize_content(content)
  pos = Pos(pos) if isinstance(pos, str) else pos
  return It(pos=pos, x=x, type=type, content=content)


def create_ph(
  *,
  content: Iterable[str | Sub] | str | None = None,
  x: int | None = None,
  assoc: Assoc | Literal["p", "f", "b"] | None = None,
  type: str | None = None,
) -> Ph:
  """Create a placeholder (PH) element.

  Args:
      content: Code data with optional sub-flow elements.
      x: External matching identifier for cross-language pairing.
      assoc: Association with surrounding text (p=previous, f=following, b=both).
      type: Placeholder type (e.g., "image", "fnote", "lb").

  Returns:
      Configured placeholder element.
  """
  content = _normalize_content(content)
  assoc = Assoc(assoc) if isinstance(assoc, str) else assoc
  return Ph(x=x, assoc=assoc, type=type, content=content)


def create_hi(
  *,
  content: Iterable[str | Bpt | Ept | It | Ph | Hi] | str | None = None,
  x: int | None = None,
  type: str | None = None,
) -> Hi:
  """Create a highlight (HI) element.

  Args:
      content: Highlighted content with optional inline elements.
      x: External matching identifier for cross-language pairing.
      type: Highlight type (purpose of the highlighting).

  Returns:
      Configured highlight element.
  """
  content = _normalize_content(content)
  return Hi(x=x, type=type, content=content)


def create_sub(
  *,
  content: Iterable[str | Bpt | Ept | It | Ph | Hi] | str | None = None,
  datatype: str | None = None,
  type: str | None = None,
) -> Sub:
  """Create a sub-flow (SUB) element.

  Args:
      content: Sub-flow content with optional inline elements.
      datatype: Data type of the sub-flow.
      type: Sub-flow type.

  Returns:
      Configured sub-flow element.
  """
  content = _normalize_content(content)
  return Sub(datatype=datatype, type=type, content=content)
