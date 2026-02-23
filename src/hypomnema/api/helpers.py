"""Factory functions for creating TMX elements.

This module provides convenience functions for constructing TMX dataclass
instances. These helpers handle common defaults, type conversions, and
validation to simplify element creation.
"""

from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from importlib.metadata import version
from typing import Any, Literal, overload

from hypomnema.base.types import (
  Assoc,
  Bpt,
  BptLike,
  Ept,
  EptLike,
  Header,
  HeaderLike,
  Hi,
  HiLike,
  It,
  ItLike,
  Note,
  NoteLike,
  Ph,
  PhLike,
  Pos,
  Prop,
  PropLike,
  Segtype,
  Sub,
  SubLike,
  Tmx,
  Tu,
  TuLike,
  Tuv,
  TuvLike,
)


def text(source: BptLike | EptLike | ItLike | PhLike | HiLike | SubLike | TuvLike) -> str:
  """
  Extract plain text from mixed content.

  Concatenates all string items in content, skipping inline elements.

  Returns:
      Plain text without inline markup
  """
  return "".join(item for item in source.content if isinstance(item, str))


def iter_text(
  source: BptLike | EptLike | ItLike | HiLike | PhLike | SubLike | TuvLike,
  *,
  ignore: Iterable[type[BptLike | EptLike | ItLike | HiLike | SubLike]] | None = None,
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
    _source: BptLike | EptLike | ItLike | HiLike | PhLike | SubLike | TuvLike,
    _ignore: tuple[type[BptLike | EptLike | ItLike | HiLike | PhLike | SubLike | TuvLike], ...],
  ) -> Generator[str]:
    for item in _source.content:
      if isinstance(item, str):
        if not isinstance(_source, _ignore):
          yield item
      else:
        yield from _iter_text(item, _ignore=_ignore)

  ignore = tuple(ignore) if ignore else ()
  yield from _iter_text(source, _ignore=ignore)


def create_tmx(
  *, header: HeaderLike | None = None, body: Iterable[TuLike] | None = None, version: str = "1.4"
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
    _header = create_header()
  else:
    _header = create_header(
      creationtool=header.creationtool,
      creationtoolversion=header.creationtoolversion,
      segtype=header.segtype,
      o_tmf=header.o_tmf,
      adminlang=header.adminlang,
      srclang=header.srclang,
      datatype=header.datatype,
      o_encoding=header.o_encoding,
      creationdate=header.creationdate,
      creationid=header.creationid,
      changedate=header.changedate,
      changeid=header.changeid,
      notes=header.notes,
      props=header.props,
    )
  if body is None:
    _body = list()
  else:
    _body = [
      create_tu(
        tuid=tu.tuid,
        srclang=tu.srclang,
        segtype=tu.segtype,
        variants=tu.variants,
        o_encoding=tu.o_encoding,
        datatype=tu.datatype,
        usagecount=tu.usagecount,
        lastusagedate=tu.lastusagedate,
        creationtool=tu.creationtool,
        creationtoolversion=tu.creationtoolversion,
        creationdate=tu.creationdate,
        creationid=tu.creationid,
        changedate=tu.changedate,
        changeid=tu.changeid,
        o_tmf=tu.o_tmf,
        notes=tu.notes,
        props=tu.props,
      )
      for tu in body
    ]
  return Tmx(header=_header, body=_body, version=version or "1.4")


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
  notes: Iterable[NoteLike] | None = None,
  props: Iterable[PropLike] | None = None,
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
  _notes = (
    [create_note(text=note.text, lang=note.lang, o_encoding=note.o_encoding) for note in notes]
    if notes is not None
    else []
  )
  _props = (
    [
      create_prop(text=prop.text, type=prop.type, lang=prop.lang, o_encoding=prop.o_encoding)
      for prop in props
    ]
    if props is not None
    else []
  )
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
    notes=_notes,
    props=_props,
  )


def create_tu(
  *,
  tuid: str | None = None,
  srclang: str | None = None,
  segtype: Segtype | str | None = None,
  variants: Iterable[TuvLike] | None = None,
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
  notes: Iterable[NoteLike] | None = None,
  props: Iterable[PropLike] | None = None,
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
  _notes = (
    [create_note(text=note.text, lang=note.lang, o_encoding=note.o_encoding) for note in notes]
    if notes is not None
    else []
  )
  _props = (
    [
      create_prop(text=prop.text, type=prop.type, lang=prop.lang, o_encoding=prop.o_encoding)
      for prop in props
    ]
    if props is not None
    else []
  )
  creationdate = creationdate if creationdate is not None else datetime.now(UTC)
  _variants = (
    [
      create_tuv(
        lang=variant.lang,
        content=variant.content,
        o_encoding=variant.o_encoding,
        datatype=variant.datatype,
        usagecount=variant.usagecount,
        lastusagedate=variant.lastusagedate,
        creationtool=variant.creationtool,
        creationtoolversion=variant.creationtoolversion,
        creationdate=variant.creationdate,
        creationid=variant.creationid,
        changedate=variant.changedate,
        changeid=variant.changeid,
        o_tmf=variant.o_tmf,
        notes=variant.notes,
        props=variant.props,
      )
      for variant in variants
    ]
    if variants is not None
    else []
  )

  return Tu(
    tuid=tuid,
    srclang=srclang,
    segtype=segtype,
    variants=_variants,
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
    notes=_notes,
    props=_props,
  )


def create_tuv(
  lang: str,
  *,
  content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike] | str | None = None,
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
  notes: Iterable[NoteLike] | None = None,
  props: Iterable[PropLike] | None = None,
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
  _content = _normalize_content(content, sub_only=False)
  _notes = (
    [create_note(text=note.text, lang=note.lang, o_encoding=note.o_encoding) for note in notes]
    if notes is not None
    else []
  )
  _props = (
    [
      create_prop(text=prop.text, type=prop.type, lang=prop.lang, o_encoding=prop.o_encoding)
      for prop in props
    ]
    if props is not None
    else []
  )

  return Tuv(
    lang=lang,
    content=_content,
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
    notes=_notes,
    props=_props,
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
  content: Iterable[str | SubLike] | str | None = None,
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
  _content = _normalize_content(content)
  return Bpt(i=i, x=x, type=type, content=_content)


def create_ept(i: int, *, content: Iterable[str | SubLike] | str | None = None) -> Ept:
  """Create an end paired tag (EPT) element.

  Args:
      i: Internal matching identifier linking to corresponding BPT.
      content: Code data with optional sub-flow elements.

  Returns:
      Configured end paired tag.
  """
  _content = _normalize_content(content)
  return Ept(i=i, content=_content)


def create_it(
  pos: Pos | Literal["begin", "end"],
  *,
  content: Iterable[str | SubLike] | str | None = None,
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
  _content = _normalize_content(content)
  pos = Pos(pos) if isinstance(pos, str) else pos
  return It(pos=pos, x=x, type=type, content=_content)


def create_ph(
  *,
  content: Iterable[str | SubLike] | str | None = None,
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
  _content = _normalize_content(content)
  assoc = Assoc(assoc) if isinstance(assoc, str) else assoc
  return Ph(x=x, assoc=assoc, type=type, content=_content)


def create_hi(
  *,
  content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike] | str | None = None,
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
  _content = _normalize_content(content, sub_only=False)
  return Hi(x=x, type=type, content=_content)


def create_sub(
  *,
  content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike] | str | None = None,
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
  _content = _normalize_content(content, sub_only=False)
  return Sub(datatype=datatype, type=type, content=_content)


@overload
def _normalize_content(
  content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike] | str | None,
  sub_only: Literal[False],
) -> list[str | Bpt | Ept | It | Ph | Hi]: ...
@overload
def _normalize_content(
  content: Iterable[str | SubLike] | str | None, sub_only: Literal[True] = True
) -> list[str | Sub]: ...
def _normalize_content(
  content: Iterable[str | BptLike | EptLike | ItLike | PhLike | HiLike]
  | Iterable[str | SubLike]
  | str
  | None,
  sub_only: bool = True,
) -> list[str | Bpt | Ept | It | Ph | Hi] | list[str | Sub]:
  if content is None:
    return []
  content = [content] if isinstance(content, str) else content
  result: list[Any] = []
  for item in content:
    match item:
      case str():
        result.append(item)
      case SubLike() if not sub_only:
        raise TypeError(f"Invalid item, expected str or SubLike, got {type(item)}")
      case BptLike() | EptLike() | ItLike() | PhLike() | HiLike() if sub_only:
        raise TypeError(f"Invalid item, expected str or SubLike, got {type(item)}")
      case SubLike():
        result.append(create_sub(content=item.content, datatype=item.datatype, type=item.type))
      case BptLike():
        result.append(create_bpt(i=item.i, content=item.content, x=item.x, type=item.type))
      case EptLike():
        result.append(create_ept(i=item.i, content=item.content))
      case ItLike():
        result.append(create_it(pos=item.pos, x=item.x, type=item.type, content=item.content))
      case PhLike():
        result.append(create_ph(x=item.x, assoc=item.assoc, type=item.type, content=item.content))
      case HiLike():
        result.append(create_hi(x=item.x, type=item.type, content=item.content))
      case _:
        raise TypeError(f"Invalid item: {type(item)}")
  return result
