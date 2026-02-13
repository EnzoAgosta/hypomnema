"""Element deserializers for TMX 1.4b.

This module provides deserializer implementations for all TMX element types.
Each class handles deserialization of a specific XML element to its corresponding
dataclass representation.
"""

from hypomnema.base.errors import (
  InvalidPolicyActionError,
  MissingBodyError,
  MissingHeaderError,
  DuplicateChildError,
  MissingSegError,
)
from hypomnema.base.types import (
  Assoc,
  Bpt,
  Ept,
  Header,
  Hi,
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
from hypomnema.xml.deserialization.base import BaseElementDeserializer
from hypomnema.xml.policy import DuplicateChildAction, RaiseIgnore


class NoteDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Note]):
  """Deserializer for <note> elements."""

  def _deserialize(self, element: BackendElementType) -> Note | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "note":
      if self._handle_invalid_tag(source_tag, "note") is None:
        return None

    # Text content
    text = self.backend.get_text(element)
    if text is None:
      text = self._handle_missing_text_content("note")

    # Optional attributes
    lang = self.backend.get_attribute(element, "{http://www.w3.org/XML/1998/namespace}lang")
    o_encoding = self.backend.get_attribute(element, "o-encoding")
    return Note(text=text, lang=lang, o_encoding=o_encoding)


class PropDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Prop]):
  """Deserializer for <prop> elements."""

  def _deserialize(self, element: BackendElementType) -> Prop | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "prop":
      if self._handle_invalid_tag(source_tag, "prop") is None:
        return None

    # Text content
    text = self.backend.get_text(element)
    if text is None:
      text = self._handle_missing_text_content("prop")

    # Required attributes
    _type = self._parse_required_attribute(element, "type")

    # Optional attributes
    lang = self.backend.get_attribute(element, "{http://www.w3.org/XML/1998/namespace}lang")
    o_encoding = self.backend.get_attribute(element, "o-encoding")
    return Prop(text=text, type=_type, lang=lang, o_encoding=o_encoding)


class HeaderDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Header]):
  """Deserializer for <header> elements."""

  def _deserialize(self, element: BackendElementType) -> Header | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "header":
      if self._handle_invalid_tag(source_tag, "header") is None:
        return None

    # Text content
    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self._handle_extra_text(source_tag, text)

    # Required attributes
    creationtool = self._parse_required_attribute(element, "creationtool")
    creationtoolversion = self._parse_required_attribute(element, "creationtoolversion")
    _segtype = self._parse_required_attribute(element, "segtype")
    segtype = self.try_convert_to_enum(source_tag, _segtype, "segtype", Segtype)
    o_tmf = self._parse_required_attribute(element, "o-tmf")
    adminlang = self._parse_required_attribute(element, "adminlang")
    srclang = self._parse_required_attribute(element, "srclang")
    datatype = self._parse_required_attribute(element, "datatype")

    # Optional attributes
    o_encoding = self.backend.get_attribute(element, "o-encoding")
    _creationdate = self.backend.get_attribute(element, "creationdate")
    creationdate = (
      self.try_convert_to_datetime(source_tag, _creationdate, "creationdate")
      if _creationdate is not None
      else None
    )
    creationid = self.backend.get_attribute(element, "creationid")
    _changedate = self.backend.get_attribute(element, "changedate")
    changedate = (
      self.try_convert_to_datetime(source_tag, _changedate, "changedate")
      if _changedate is not None
      else None
    )
    changeid = self.backend.get_attribute(element, "changeid")

    # Children
    props: list[Prop] = []
    notes: list[Note] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "prop":
          prop = self.emit(child)
          if isinstance(prop, Prop):
            props.append(prop)
        case "note":
          note = self.emit(child)
          if isinstance(note, Note):
            notes.append(note)
        case _:
          self._handle_invalid_child_tag(source_tag, child_tag, ("prop", "note"))

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
      props=props,
      notes=notes,
    )


class BptDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Bpt]):
  """Deserializer for <bpt> elements."""

  def _deserialize(self, element: BackendElementType) -> Bpt | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "bpt":
      if self._handle_invalid_tag(source_tag, "bpt") is None:
        return None

    # Required attributes
    _i = self._parse_required_attribute(element, "i")
    i = self.try_convert_to_int(source_tag, _i, "i")

    # Optional attributes
    _x = self.backend.get_attribute(element, "x")
    x = self.try_convert_to_int(source_tag, _x, "x") if _x is not None else None
    _type = self.backend.get_attribute(element, "type")

    # Content
    content = self._deserialize_content(element, ("sub",))

    return Bpt(i=i, x=x, type=_type, content=content)


class EptDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Ept]):
  """Deserializer for <ept> elements."""

  def _deserialize(self, element: BackendElementType) -> Ept | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "ept":
      if self._handle_invalid_tag(source_tag, "ept") is None:
        return None

    # Required attributes
    _i = self._parse_required_attribute(element, "i")
    i = self.try_convert_to_int(source_tag, _i, "i")

    # Content
    content = self._deserialize_content(element, ("sub",))

    return Ept(i=i, content=content)


class ItDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, It]):
  """Deserializer for <it> elements."""

  def _deserialize(self, element: BackendElementType) -> It | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "it":
      if self._handle_invalid_tag(source_tag, "it") is None:
        return None

    # Required attributes
    _pos = self._parse_required_attribute(element, "pos")
    pos = self.try_convert_to_enum(source_tag, _pos, "pos", Pos)

    # Optional attributes
    _x = self.backend.get_attribute(element, "x")
    x = self.try_convert_to_int(source_tag, _x, "x") if _x is not None else None
    _type = self.backend.get_attribute(element, "type")

    # Content
    content = self._deserialize_content(element, ("sub",))

    return It(pos=pos, x=x, type=_type, content=content)


class PhDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Ph]):
  """Deserializer for <ph> elements."""

  def _deserialize(self, element: BackendElementType) -> Ph | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "ph":
      if self._handle_invalid_tag(source_tag, "ph") is None:
        return None

    # Optional attributes
    _x = self.backend.get_attribute(element, "x")
    x = self.try_convert_to_int(source_tag, _x, "x") if _x is not None else None
    _type = self.backend.get_attribute(element, "type")
    _assoc = self.backend.get_attribute(element, "assoc")
    assoc = (
      self.try_convert_to_enum(source_tag, _assoc, "assoc", Assoc) if _assoc is not None else None
    )

    # Content
    content = self._deserialize_content(element, ("sub",))

    return Ph(assoc=assoc, x=x, type=_type, content=content)


class SubDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Sub]):
  """Deserializer for <sub> elements."""

  def _deserialize(self, element: BackendElementType) -> Sub | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "sub":
      if self._handle_invalid_tag(source_tag, "sub") is None:
        return None

    # Optional attributes
    _type = self.backend.get_attribute(element, "type")
    datatype = self.backend.get_attribute(element, "datatype")

    # Content
    content = self._deserialize_content(element, ("bpt", "ept", "it", "ph", "hi"))

    return Sub(datatype=datatype, type=_type, content=content)


class HiDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Hi]):
  """Deserializer for <hi> elements."""

  def _deserialize(self, element: BackendElementType) -> Hi | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "hi":
      if self._handle_invalid_tag(source_tag, "hi") is None:
        return None

    # Optional attributes
    _x = self.backend.get_attribute(element, "x")
    x = self.try_convert_to_int(source_tag, _x, "x") if _x is not None else None
    _type = self.backend.get_attribute(element, "type")

    # Content
    content = self._deserialize_content(element, ("bpt", "ept", "it", "ph", "hi"))

    return Hi(x=x, type=_type, content=content)


class TuvDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Tuv]):
  """Deserializer for <tuv> elements."""

  def _deserialize(self, element: BackendElementType) -> Tuv | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "tuv":
      if self._handle_invalid_tag(source_tag, "tuv") is None:
        return None

    # Text content
    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self._handle_extra_text(source_tag, text)

    # Required attributes
    lang = self._parse_required_attribute(element, "{http://www.w3.org/XML/1998/namespace}lang")

    # Optional attributes
    o_encoding = self.backend.get_attribute(element, "o-encoding")
    datatype = self.backend.get_attribute(element, "datatype")
    _usagecount = self.backend.get_attribute(element, "usagecount")
    usagecount = (
      self.try_convert_to_int(source_tag, _usagecount, "usagecount")
      if _usagecount is not None
      else None
    )
    _lastusagedate = self.backend.get_attribute(element, "lastusagedate")
    lastusagedate = (
      self.try_convert_to_datetime(source_tag, _lastusagedate, "lastusagedate")
      if _lastusagedate is not None
      else None
    )
    creationtool = self.backend.get_attribute(element, "creationtool")
    creationtoolversion = self.backend.get_attribute(element, "creationtoolversion")
    _creationdate = self.backend.get_attribute(element, "creationdate")
    creationdate = (
      self.try_convert_to_datetime(source_tag, _creationdate, "creationdate")
      if _creationdate is not None
      else None
    )
    creationid = self.backend.get_attribute(element, "creationid")
    _changedate = self.backend.get_attribute(element, "changedate")
    changedate = (
      self.try_convert_to_datetime(source_tag, _changedate, "changedate")
      if _changedate is not None
      else None
    )
    changeid = self.backend.get_attribute(element, "changeid")
    o_tmf = self.backend.get_attribute(element, "o-tmf")

    # Children
    props: list[Prop] = []
    notes: list[Note] = []
    content: list[str | Bpt | Ept | It | Ph | Hi] = []
    seg_found = False
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "prop":
          prop = self.emit(child)
          if isinstance(prop, Prop):
            props.append(prop)
        case "note":
          note = self.emit(child)
          if isinstance(note, Note):
            notes.append(note)
        case "seg":
          if seg_found:
            multiple_seg_behavior = self.policy.multiple_seg
            self._log(multiple_seg_behavior, "Multiple <seg> elements in <tuv>")
            match multiple_seg_behavior.action:
              case DuplicateChildAction.RAISE:
                raise DuplicateChildError("tuv", "seg")
              case DuplicateChildAction.KEEP_FIRST:
                continue
              case DuplicateChildAction.KEEP_LAST:
                pass
              case _:
                raise InvalidPolicyActionError(
                  "multiple_seg", multiple_seg_behavior.action, DuplicateChildAction
                )
          seg_found = True
          content = self._deserialize_content(child, ("bpt", "ept", "it", "ph", "hi"))
        case _:
          self._handle_invalid_child_tag(source_tag, child_tag, ("prop", "note", "seg"))

    if not seg_found:
      missing_seg_behavior = self.policy.missing_seg
      self._log(missing_seg_behavior, "Missing <seg> element in <tuv>")
      match missing_seg_behavior.action:
        case RaiseIgnore.RAISE:
          raise MissingSegError()
        case RaiseIgnore.IGNORE:
          content = []
        case _:
          raise InvalidPolicyActionError("missing_seg", missing_seg_behavior, RaiseIgnore)

    return Tuv(
      lang=lang,
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
      props=props,
      notes=notes,
      content=content,
    )


class TuDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Tu]):
  """Deserializer for <tu> elements."""

  def _deserialize(self, element: BackendElementType) -> Tu | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "tu":
      if self._handle_invalid_tag(source_tag, "tu") is None:
        return None

    # Text content
    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self._handle_extra_text(source_tag, text)

    # Optional attributes
    tuid = self.backend.get_attribute(element, "tuid")
    o_encoding = self.backend.get_attribute(element, "o-encoding")
    datatype = self.backend.get_attribute(element, "datatype")
    _usagecount = self.backend.get_attribute(element, "usagecount")
    usagecount = (
      self.try_convert_to_int(source_tag, _usagecount, "usagecount")
      if _usagecount is not None
      else None
    )
    _lastusagedate = self.backend.get_attribute(element, "lastusagedate")
    lastusagedate = (
      self.try_convert_to_datetime(source_tag, _lastusagedate, "lastusagedate")
      if _lastusagedate is not None
      else None
    )
    creationtool = self.backend.get_attribute(element, "creationtool")
    creationtoolversion = self.backend.get_attribute(element, "creationtoolversion")
    _creationdate = self.backend.get_attribute(element, "creationdate")
    creationdate = (
      self.try_convert_to_datetime(source_tag, _creationdate, "creationdate")
      if _creationdate is not None
      else None
    )
    creationid = self.backend.get_attribute(element, "creationid")
    _changedate = self.backend.get_attribute(element, "changedate")
    changedate = (
      self.try_convert_to_datetime(source_tag, _changedate, "changedate")
      if _changedate is not None
      else None
    )
    _segtype = self.backend.get_attribute(element, "segtype")
    segtype = (
      self.try_convert_to_enum(source_tag, _segtype, "segtype", Segtype)
      if _segtype is not None
      else None
    )
    changeid = self.backend.get_attribute(element, "changeid")
    o_tmf = self.backend.get_attribute(element, "o-tmf")
    srclang = self.backend.get_attribute(element, "srclang")

    # Children
    props: list[Prop] = []
    notes: list[Note] = []
    variants: list[Tuv] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "prop":
          prop = self.emit(child)
          if isinstance(prop, Prop):
            props.append(prop)
        case "note":
          note = self.emit(child)
          if isinstance(note, Note):
            notes.append(note)
        case "tuv":
          tuv = self.emit(child)
          if isinstance(tuv, Tuv):
            variants.append(tuv)
        case _:
          self._handle_invalid_child_tag(source_tag, child_tag, ("prop", "note", "tuv"))

    return Tu(
      tuid=tuid,
      o_encoding=o_encoding,
      datatype=datatype,
      usagecount=usagecount,
      lastusagedate=lastusagedate,
      creationtool=creationtool,
      creationtoolversion=creationtoolversion,
      creationdate=creationdate,
      creationid=creationid,
      changedate=changedate,
      segtype=segtype,
      changeid=changeid,
      o_tmf=o_tmf,
      srclang=srclang,
      props=props,
      notes=notes,
      variants=variants,
    )


class TmxDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Tmx]):
  """Deserializer for <tmx> elements."""

  def _deserialize(self, element: BackendElementType) -> Tmx | None:
    source_tag = self.backend.get_tag(element)
    if source_tag != "tmx":
      if self._handle_invalid_tag(source_tag, "tmx") is None:
        return None

    # Text content
    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self._handle_extra_text(source_tag, text)

    # Required attributes
    version = self._parse_required_attribute(element, "version")

    # Children
    header_found: bool = False
    body_found: bool = False
    header: Header | None = None
    body: list[Tu] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "header":
          if header_found:
            multiple_header_behavior = self.policy.multiple_headers
            self._log(multiple_header_behavior, "Multiple <header> elements in <tmx>")
            match multiple_header_behavior.action:
              case DuplicateChildAction.RAISE:
                raise DuplicateChildError("tmx", "header")
              case DuplicateChildAction.KEEP_FIRST:
                continue
              case DuplicateChildAction.KEEP_LAST:
                pass
              case _:
                raise InvalidPolicyActionError(
                  "multiple_headers", multiple_header_behavior, DuplicateChildAction
                )
          header_found = True
          header_obj = self.emit(child)
          if isinstance(header_obj, Header):
            header = header_obj
        case "body":
          if body_found:
            multiple_body_behavior = self.policy.multiple_body
            self._log(multiple_body_behavior, "Multiple <body> elements in <tmx>")
            match multiple_body_behavior.action:
              case DuplicateChildAction.RAISE:
                raise DuplicateChildError("tmx", "body")
              case DuplicateChildAction.KEEP_FIRST:
                continue
              case DuplicateChildAction.KEEP_LAST:
                body = []
              case _:
                raise InvalidPolicyActionError(
                  "multiple_body", multiple_body_behavior, DuplicateChildAction
                )
          body_found = True
          for grandchild in self.backend.iter_children(child):
            grandchild_tag = self.backend.get_tag(grandchild)
            if grandchild_tag == "tu":
              tu_obj = self.emit(grandchild)
              if isinstance(tu_obj, Tu):
                body.append(tu_obj)
            else:
              self._handle_invalid_child_tag("body", grandchild_tag, ("tu",))
        case _:
          self._handle_invalid_child_tag(source_tag, child_tag, ("header", "body"))
    if not header_found:
      missing_header_behavior = self.policy.missing_header
      self._log(missing_header_behavior, "Missing <header> element in <tmx>")
      match missing_header_behavior.action:
        case RaiseIgnore.RAISE:
          raise MissingHeaderError()
        case RaiseIgnore.IGNORE:
          pass
        case _:
          raise InvalidPolicyActionError(
            "missing_header", missing_header_behavior.action, RaiseIgnore
          )
    if not body_found:
      missing_body_behavior = self.policy.missing_body
      self._log(missing_body_behavior, "Missing <body> element in <tmx>")
      match missing_body_behavior.action:
        case RaiseIgnore.RAISE:
          raise MissingBodyError()
        case RaiseIgnore.IGNORE:
          pass
        case _:
          raise InvalidPolicyActionError("missing_body", missing_body_behavior.action, RaiseIgnore)

    return Tmx(version=version, header=header, body=body)  # type: ignore[arg-type]
