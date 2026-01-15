from collections.abc import Iterable
from datetime import datetime
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
]


def create_tmx(
  *, header: Header | None = None, body: Iterable[Tu] | None = None, version: str = "1.4"
) -> Tmx:
  """Create a Tmx instance with common defaults.

  Parameters
  ----------
  header : Header | None, optional
      Header element. If None, creates a default header.
  body : Iterable[Tu] | None, optional
      Collection of translation units.
  version : str, optional
      TMX version (default: "1.4").

  Returns
  -------
  Tmx
      A new TMX container.
  """
  if header is None:
    header = create_header()
  if body is None:
    body = []
  return Tmx(header=header, body=list(body), version=version or "1.4")


def create_header(
  *,
  creationtool: str = "hypomnema",
  creationtoolversion: str = "",
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
  """Create a Header instance with common defaults.

  Parameters
  ----------
  creationtool : str, optional
      Name of the tool that created the file (default: "hypomnema").
  creationtoolversion : str, optional
      Version of the tool.
  segtype : Segtype | str, optional
      Default segmentation level.
  o_tmf : str, optional
      Original TMF format (default: "tmx").
  adminlang : str, optional
      Administrative language (BCP-47).
  srclang : str, optional
      Source language (BCP-47).
  datatype : str, optional
      Data type (default: "plaintext").
  o_encoding : str | None, optional
      Original encoding.
  creationdate : datetime | None, optional
      Creation timestamp.
  creationid : str | None, optional
      User who created the file.
  changedate : datetime | None, optional
      Last modification timestamp.
  changeid : str | None, optional
      User who last modified the file.
  notes : Iterable[Note] | None, optional
      Collection of notes.
  props : Iterable[Prop] | None, optional
      Collection of properties.

  Returns
  -------
  Header
      A new Header instance.
  """
  segtype_enum = Segtype(segtype) if isinstance(segtype, str) else segtype
  return Header(
    creationtool=creationtool,
    creationtoolversion=creationtoolversion,
    segtype=segtype_enum,
    o_tmf=o_tmf,
    adminlang=adminlang,
    srclang=srclang,
    datatype=datatype,
    o_encoding=o_encoding,
    creationdate=creationdate,
    creationid=creationid,
    changedate=changedate,
    changeid=changeid,
    notes=list(notes) if notes else [],
    props=list(props) if props else [],
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
  """Create a Tu instance with common defaults.

  Parameters
  ----------
  tuid : str | None, optional
      Unique identifier for the unit.
  srclang : str | None, optional
      Source language (BCP-47).
  segtype : Segtype | str | None, optional
      Segmentation level override.
  variants : Iterable[Tuv] | None, optional
      Collection of language variants.
  o_encoding : str | None, optional
      Original encoding.
  datatype : str | None, optional
      Data type override.
  usagecount : int | None, optional
      Number of times reused.
  lastusagedate : datetime | None, optional
      Last reuse timestamp.
  creationtool : str | None, optional
      Tool that created the unit.
  creationtoolversion : str | None, optional
      Tool version.
  creationdate : datetime | None, optional
      Creation timestamp.
  creationid : str | None, optional
      User who created the unit.
  changedate : datetime | None, optional
      Last modification timestamp.
  changeid : str | None, optional
      User who last modified the unit.
  o_tmf : str | None, optional
      Original TMF format.
  notes : Iterable[Note] | None, optional
      Collection of notes.
  props : Iterable[Prop] | None, optional
      Collection of properties.

  Returns
  -------
  Tu
      A new Translation Unit instance.
  """
  segtype_enum = Segtype(segtype) if isinstance(segtype, str) else segtype
  return Tu(
    tuid=tuid,
    srclang=srclang,
    segtype=segtype_enum,
    variants=list(variants) if variants else [],
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
    notes=list(notes) if notes else [],
    props=list(props) if props else [],
  )


def create_tuv(
  lang: str,
  *,
  content: Iterable[str | Bpt | Ept | It | Ph | Hi] | None = None,
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
  """Create a Tuv instance with common defaults.

  Parameters
  ----------
  lang : str
      Language code (BCP-47, required).
  content : Iterable[str | InlineElement] | None, optional
      Segment content (text and inline elements).
  o_encoding : str | None, optional
      Original encoding.
  datatype : str | None, optional
      Data type override.
  usagecount : int | None, optional
      Number of times reused.
  lastusagedate : datetime | None, optional
      Last reuse timestamp.
  creationtool : str | None, optional
      Tool that created the variant.
  creationtoolversion : str | None, optional
      Tool version.
  creationdate : datetime | None, optional
      Creation timestamp.
  creationid : str | None, optional
      User who created the variant.
  changedate : datetime | None, optional
      Last modification timestamp.
  changeid : str | None, optional
      User who last modified the variant.
  o_tmf : str | None, optional
      Original TMF format.
  notes : Iterable[Note] | None, optional
      Collection of notes.
  props : Iterable[Prop] | None, optional
      Collection of properties.

  Returns
  -------
  Tuv
      A new Translation Unit Variant instance.
  """
  return Tuv(
    lang=lang,
    content=list(content) if content else [],
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
    notes=list(notes) if notes else [],
    props=list(props) if props else [],
  )


def create_note(text: str, *, lang: str | None = None, o_encoding: str | None = None) -> Note:
  """Create a Note instance.

  Parameters
  ----------
  text : str
      The note content.
  lang : str | None, optional
      Language code (BCP-47).
  o_encoding : str | None, optional
      Original encoding.

  Returns
  -------
  Note
      A new Note instance.
  """
  return Note(text=text, lang=lang, o_encoding=o_encoding)


def create_prop(
  text: str, type: str, *, lang: str | None = None, o_encoding: str | None = None
) -> Prop:
  """Create a Prop instance.

  Parameters
  ----------
  text : str
      The property value.
  type : str
      The property name (user-defined).
  lang : str | None, optional
      Language code (BCP-47).
  o_encoding : str | None, optional
      Original encoding.

  Returns
  -------
  Prop
      A new Prop instance.
  """
  return Prop(text=text, type=type, lang=lang, o_encoding=o_encoding)


def create_bpt(
  i: int,
  *,
  content: Iterable[str | Sub] | None = None,
  x: int | None = None,
  type: str | None = None,
) -> Bpt:
  """Create a Bpt (Begin Paired Tag) instance.

  Parameters
  ----------
  i : int
      Unique identifier matching the corresponding Ept (required).
  content : Iterable[str | Sub] | None, optional
      Mixed inline content.
  x : int | None, optional
      External reference identifier.
  type : str | None, optional
      Tag type (user-defined).

  Returns
  -------
  Bpt
      A new Begin Paired Tag instance.
  """
  return Bpt(i=i, x=x, type=type, content=list(content) if content else [])


def create_ept(i: int, *, content: Iterable[str | Sub] | None = None) -> Ept:
  """Create an Ept (End Paired Tag) instance.

  Parameters
  ----------
  i : int
      Unique identifier matching the corresponding Bpt (required).
  content : Iterable[str | Sub] | None, optional
      Mixed inline content.

  Returns
  -------
  Ept
      A new End Paired Tag instance.
  """
  return Ept(i=i, content=list(content) if content else [])


def create_it(
  pos: Pos | Literal["begin", "end"],
  *,
  content: Iterable[str | Sub] | None = None,
  x: int | None = None,
  type: str | None = None,
) -> It:
  """Create an It (Isolated Tag) instance.

  Parameters
  ----------
  pos : Pos | str
      Position: "begin" for opening, "end" for closing (required).
  content : Iterable[str | Sub] | None, optional
      Mixed inline content.
  x : int | None, optional
      External reference identifier.
  type : str | None, optional
      Tag type (user-defined).

  Returns
  -------
  It
      A new Isolated Tag instance.
  """
  pos_enum = Pos(pos) if isinstance(pos, str) else pos
  return It(pos=pos_enum, x=x, type=type, content=list(content) if content else [])


def create_ph(
  *,
  content: Iterable[str | Sub] | None = None,
  x: int | None = None,
  assoc: Assoc | Literal["p", "f", "b"] | None = None,
  type: str | None = None,
) -> Ph:
  """Create a Ph (Placeholder) instance.

  Parameters
  ----------
  content : Iterable[str | Sub] | None, optional
      Mixed inline content.
  x : int | None, optional
      External reference identifier.
  assoc : Assoc | str | None, optional
      Association: "p" (previous), "f" (following), "b" (both).
  type : str | None, optional
      Placeholder type (user-defined).

  Returns
  -------
  Ph
      A new Placeholder instance.
  """
  assoc_enum = Assoc(assoc) if isinstance(assoc, str) else assoc
  return Ph(x=x, assoc=assoc_enum, type=type, content=list(content) if content else [])


def create_hi(
  *,
  content: Iterable[str | InlineElement] | None = None,
  x: int | None = None,
  type: str | None = None,
) -> Hi:
  """Create a Hi (Highlight) instance.

  Parameters
  ----------
  content : Iterable[str | InlineElement] | None, optional
      Mixed inline content.
  x : int | None, optional
      External reference identifier.
  type : str | None, optional
      Highlight type (user-defined).

  Returns
  -------
  Hi
      A new Highlight instance.
  """
  return Hi(x=x, type=type, content=list(content) if content else [])


def create_sub(
  *,
  content: Iterable[str | InlineElement] | None = None,
  datatype: str | None = None,
  type: str | None = None,
) -> Sub:
  """Create a Sub (Sub-flow) instance.

  Parameters
  ----------
  content : Iterable[str | InlineElement] | None, optional
      Mixed inline content.
  datatype : str | None, optional
      Data type of the sub-flow.
  type : str | None, optional
      Sub-flow type (user-defined).

  Returns
  -------
  Sub
      A new Sub-flow instance.
  """
  return Sub(datatype=datatype, type=type, content=list(content) if content else [])
