from collections.abc import Generator, Iterable
from datetime import UTC, datetime
from importlib.metadata import version
from typing import Literal

from hypomnema.base.types import (Assoc, Bpt, Ept, Header, Hi, InlineElement,
                                  It, Note, Ph, Pos, Prop, Segtype, Sub, Tmx,
                                  Tu, Tuv)

__all__ = [
  "create_tmx",
  "create_header",
  "create_tu",
  "create_tuv",
  "create_note",
  "create_prop",
  "create_bpt",
  "create_ept",
  "create_it",
  "create_ph",
  "create_hi",
  "create_sub",
  "iter_text",
]


def iter_text(
  source: Tuv | InlineElement, *, ignore: Iterable[type[InlineElement]] | None = None
) -> Generator[str]:
  """
  Iterate over text content recursively.

  This function traverses the entire element tree (depth-first) and yields
  text strings found within.

  Parameters
  ----------
  source : Tuv | InlineElement
      The element to extract text from.
  ignore : Iterable[Type[InlineElement]] | None
      A list of element types to "hide". Text that is a direct child of
      an ignored element type will be skipped. However, the traversal
      will still descend into ignored elements to find nested visible text.

      For example, if `ignore=[Bpt]`, the code strings inside a `<bpt>`
      tag are skipped, but a `<sub>` element inside that `<bpt>` will
      still be visited and its text yielded (unless `Sub` is also ignored).

  Yields
  ------
  str
      Text segments found in the tree.
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
  """Normalize content parameter to a list."""
  if isinstance(content, str):
    return [content]
  return list(content) if content is not None else []


def create_tmx(
  *, header: Header | None = None, body: Iterable[Tu] | None = None, version: str = "1.4"
) -> Tmx:
  """Create a Tmx with common defaults."""
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
  """Create a Header with common defaults."""
  segtype_enum = Segtype(segtype) if isinstance(segtype, str) else segtype
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
  """Create a Tu with common defaults."""
  segtype_enum = Segtype(segtype) if isinstance(segtype, str) else segtype
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
  """Create a Tuv with common defaults."""
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
  """Create a Note."""
  return Note(text=text, lang=lang, o_encoding=o_encoding)


def create_prop(
  text: str, type: str, *, lang: str | None = None, o_encoding: str | None = None
) -> Prop:
  """Create a Prop."""
  return Prop(text=text, type=type, lang=lang, o_encoding=o_encoding)


def create_bpt(
  i: int,
  *,
  content: Iterable[str | Sub] | str | None = None,
  x: int | None = None,
  type: str | None = None,
) -> Bpt:
  """Create a Bpt (Begin Paired Tag)."""
  return Bpt(i=i, x=x, type=type, content=list(content) if content else [])


def create_ept(i: int, *, content: Iterable[str | Sub] | None = None) -> Ept:
  """Create an Ept (End Paired Tag)."""
  return Ept(i=i, content=list(content) if content else [])


def create_it(
  pos: Pos | Literal["begin", "end"],
  *,
  content: Iterable[str | Sub] | str | None = None,
  x: int | None = None,
  type: str | None = None,
) -> It:
  """Create an It (Isolated Tag)."""
  pos_enum = Pos(pos) if isinstance(pos, str) else pos
  return It(pos=pos_enum, x=x, type=type, content=list(content) if content else [])


def create_ph(
  *,
  content: Iterable[str | Sub] | str | None = None,
  x: int | None = None,
  assoc: Assoc | Literal["p", "f", "b"] | None = None,
  type: str | None = None,
) -> Ph:
  """Create a Ph (Placeholder)."""
  assoc_enum = Assoc(assoc) if isinstance(assoc, str) else assoc
  return Ph(x=x, assoc=assoc_enum, type=type, content=list(content) if content else [])


def create_hi(
  *,
  content: Iterable[str | Bpt | Ept | It | Ph | Hi] | str | None = None,
  x: int | None = None,
  type: str | None = None,
) -> Hi:
  """Create a Hi (Highlight)."""
  return Hi(x=x, type=type, content=list(content) if content else [])


def create_sub(
  *,
  content: Iterable[str | Bpt | Ept | It | Ph | Hi] | str | None = None,
  datatype: str | None = None,
  type: str | None = None,
) -> Sub:
  """Create a Sub (Sub-flow)."""
  return Sub(datatype=datatype, type=type, content=list(content) if content else [])
