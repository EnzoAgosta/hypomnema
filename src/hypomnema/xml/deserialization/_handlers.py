from hypomnema.xml.utils import check_tag
from hypomnema.base.errors import XmlDeserializationError
from hypomnema.base.types import (
  Assoc,
  InlineElement,
  Bpt,
  Ept,
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
  Header,
  Tuv,
)
from hypomnema.xml.deserialization.base import BaseElementDeserializer

__all__ = [
  "NoteDeserializer",
  "PropDeserializer",
  "HeaderDeserializer",
  "BptDeserializer",
  "EptDeserializer",
  "ItDeserializer",
  "PhDeserializer",
  "SubDeserializer",
  "HiDeserializer",
  "TuvDeserializer",
  "TuDeserializer",
  "TmxDeserializer",
]


class NoteDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Note]):
  """Deserializer for the TMX `<note>` element."""

  def _deserialize(self, element: BackendElementType) -> Note:
    """
    Convert a `<note>` XML element into a Note object.

    Parameters
    ----------
    element : BackendElementType
        The `<note>` element to deserialize.

    Returns
    -------
    Note
        The deserialized Note instance.

    Raises
    ------
    XmlDeserializationError
        If the element has no text content or contains invalid child elements
        and the respective policy behavior is "raise".
    """
    check_tag(self.backend.get_tag(element), "note", self.logger, self.policy)
    lang = self._parse_attribute_as_str(element, "xml:lang", required=False)
    o_encoding = self._parse_attribute_as_str(element, "o-encoding", required=False)
    text = self.backend.get_text(element)

    if text is None:
      self.logger.log(
        self.policy.empty_content.log_level, "Element <note> does not have any text content"
      )
      if self.policy.empty_content.behavior == "raise":
        raise XmlDeserializationError("Element <note> does not have any text content")
      if self.policy.empty_content.behavior == "empty":
        self.logger.log(self.policy.empty_content.log_level, "Falling back to an empty string")
        text = ""

    for child in self.backend.iter_children(element):
      self.logger.log(
        self.policy.invalid_child_element.log_level,
        "Invalid child element <%s> in <note>",
        self.backend.get_tag(child),
      )
      if self.policy.invalid_child_element.behavior == "raise":
        raise XmlDeserializationError(
          f"Invalid child element <{self.backend.get_tag(child)}> in <note>"
        )
    return Note(text=text, lang=lang, o_encoding=o_encoding)  # type: ignore[arg-type]


class PropDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Prop]):
  """Deserializer for the TMX `<prop>` element."""

  def _deserialize(self, element: BackendElementType) -> Prop:
    """
    Convert a `<prop>` XML element into a Prop object.

    Parameters
    ----------
    element : BackendElementType
        The `<prop>` element to deserialize.

    Returns
    -------
    Prop
        The deserialized Prop instance.

    Raises
    ------
    XmlDeserializationError
        If the element has no text content or contains invalid child elements
        and the respective policy behavior is "raise".
    """
    check_tag(self.backend.get_tag(element), "prop", self.logger, self.policy)
    _type = self._parse_attribute_as_str(element, "type", required=True)
    lang = self._parse_attribute_as_str(element, "xml:lang", required=False)
    o_encoding = self._parse_attribute_as_str(element, "o-encoding", required=False)
    text = self.backend.get_text(element)

    if text is None:
      self.logger.log(
        self.policy.empty_content.log_level, "Element <prop> does not have any text content"
      )
      if self.policy.empty_content.behavior == "raise":
        raise XmlDeserializationError("Element <prop> does not have any text content")
      if self.policy.empty_content.behavior == "empty":
        self.logger.log(self.policy.empty_content.log_level, "Falling back to an empty string")
        text = ""

    for child in self.backend.iter_children(element):
      self.logger.log(
        self.policy.invalid_child_element.log_level,
        "Invalid child element <%s> in <prop>",
        self.backend.get_tag(child),
      )
      if self.policy.invalid_child_element.behavior == "raise":
        raise XmlDeserializationError(
          f"Invalid child element <{self.backend.get_tag(child)}> in <prop>"
        )
    return Prop(text=text, type=_type, lang=lang, o_encoding=o_encoding)  # type: ignore[arg-type]


class HeaderDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Header]):
  """Deserializer for the TMX `<header>` element."""

  def _deserialize(self, element: BackendElementType) -> Header:
    """
    Convert a `<header>` XML element and its children into a Header object.

    Parameters
    ----------
    element : BackendElementType
        The `<header>` element to deserialize.

    Returns
    -------
    Header
        The deserialized Header instance.

    Raises
    ------
    XmlDeserializationError
        If extra text is found or an invalid child element is encountered
        and the respective policy behavior is "raise".
    """
    check_tag(self.backend.get_tag(element), "header", self.logger, self.policy)

    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self.logger.log(
          self.policy.extra_text.log_level, "Element <header> has extra text content '%s'", text
        )
        if self.policy.extra_text.behavior == "raise":
          raise XmlDeserializationError(f"Element <header> has extra text content '{text}'")

    creationtool = self._parse_attribute_as_str(element, "creationtool", required=True)
    creationtoolversion = self._parse_attribute_as_str(
      element, "creationtoolversion", required=True
    )
    segtype = self._parse_attribute_as_enum(element, "segtype", Segtype, required=True)
    o_tmf = self._parse_attribute_as_str(element, "o-tmf", required=True)
    adminlang = self._parse_attribute_as_str(element, "adminlang", required=True)
    srclang = self._parse_attribute_as_str(element, "srclang", required=True)
    datatype = self._parse_attribute_as_str(element, "datatype", required=True)
    o_encoding = self._parse_attribute_as_str(element, "o-encoding", required=False)
    creationdate = self._parse_attribute_as_datetime(element, "creationdate", required=False)
    creationid = self._parse_attribute_as_str(element, "creationid", required=False)
    changedate = self._parse_attribute_as_datetime(element, "changedate", required=False)
    changeid = self._parse_attribute_as_str(element, "changeid", required=False)

    notes: list[Note] = []
    props: list[Prop] = []

    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      if tag == "prop":
        prop = self.emit(child)
        if isinstance(prop, Prop):
          props.append(prop)
      elif tag == "note":
        note = self.emit(child)
        if isinstance(note, Note):
          notes.append(note)
      else:
        self.logger.log(
          self.policy.invalid_child_element.log_level, "Invalid child element <%s> in <header>", tag
        )
        if self.policy.invalid_child_element.behavior == "raise":
          raise XmlDeserializationError(f"Invalid child element <{tag}> in <header>")

    return Header(
      creationtool=creationtool,  # type: ignore[arg-type]
      creationtoolversion=creationtoolversion,  # type: ignore[arg-type]
      segtype=segtype,  # type: ignore[arg-type]
      o_tmf=o_tmf,  # type: ignore[arg-type]
      adminlang=adminlang,  # type: ignore[arg-type]
      srclang=srclang,  # type: ignore[arg-type]
      datatype=datatype,  # type: ignore[arg-type]
      o_encoding=o_encoding,
      creationdate=creationdate,
      creationid=creationid,
      changedate=changedate,
      changeid=changeid,
      props=props,
      notes=notes,
    )


class BptDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Bpt]):
  """Deserializer for the TMX `<bpt>` (Begin Paired Tag) element."""

  def _deserialize(self, element: BackendElementType) -> Bpt:
    """
    Convert a `<bpt>` XML element into a Bpt object.

    Parameters
    ----------
    element : BackendElementType
        The `<bpt>` element to deserialize.

    Returns
    -------
    Bpt
        The deserialized Bpt instance.
    """
    check_tag(self.backend.get_tag(element), "bpt", self.logger, self.policy)
    i = self._parse_attribute_as_int(element, "i", True)
    x = self._parse_attribute_as_int(element, "x", False)
    type = self._parse_attribute_as_str(element, "type", False)
    content = self._deserialize_content(element, ("sub",))
    return Bpt(i=i, x=x, type=type, content=content)  # type: ignore[arg-type]


class EptDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Ept]):
  """Deserializer for the TMX `<ept>` (End Paired Tag) element."""

  def _deserialize(self, element: BackendElementType) -> Ept:
    """
    Convert an `<ept>` XML element into an Ept object.

    Parameters
    ----------
    element : BackendElementType
        The `<ept>` element to deserialize.

    Returns
    -------
    Ept
        The deserialized Ept instance.
    """
    check_tag(self.backend.get_tag(element), "ept", self.logger, self.policy)
    i = self._parse_attribute_as_int(element, "i", True)
    content = self._deserialize_content(element, ("sub",))
    return Ept(i=i, content=content)  # type: ignore[arg-type]


class ItDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, It]):
  """Deserializer for the TMX `<it>` (Isolated Tag) element."""

  def _deserialize(self, element: BackendElementType) -> It:
    """
    Convert an `<it>` XML element into an It object.

    Parameters
    ----------
    element : BackendElementType
        The `<it>` element to deserialize.

    Returns
    -------
    It
        The deserialized It instance.
    """
    check_tag(self.backend.get_tag(element), "it", self.logger, self.policy)
    pos = self._parse_attribute_as_enum(element, "pos", Pos, True)
    x = self._parse_attribute_as_int(element, "x", False)
    type = self._parse_attribute_as_str(element, "type", False)
    content = self._deserialize_content(element, ("sub",))
    return It(pos=pos, x=x, type=type, content=content)  # type: ignore[arg-type]


class PhDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Ph]):
  """Deserializer for the TMX `<ph>` (Placeholder) element."""

  def _deserialize(self, element: BackendElementType) -> Ph:
    """
    Convert a `<ph>` XML element into a Ph object.

    Parameters
    ----------
    element : BackendElementType
        The `<ph>` element to deserialize.

    Returns
    -------
    Ph
        The deserialized Ph instance.
    """
    check_tag(self.backend.get_tag(element), "ph", self.logger, self.policy)
    x = self._parse_attribute_as_int(element, "x", False)
    assoc = self._parse_attribute_as_enum(element, "assoc", Assoc, False)
    type = self._parse_attribute_as_str(element, "type", False)
    content = self._deserialize_content(element, ("sub",))
    return Ph(x=x, assoc=assoc, type=type, content=content)  # type: ignore[arg-type]


class SubDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Sub]):
  """Deserializer for the TMX `<sub>` (Sub-flow) element."""

  def _deserialize(self, element: BackendElementType) -> Sub:
    """
    Convert a `<sub>` XML element into a Sub object.

    Parameters
    ----------
    element : BackendElementType
        The `<sub>` element to deserialize.

    Returns
    -------
    Sub
        The deserialized Sub instance.
    """
    check_tag(self.backend.get_tag(element), "sub", self.logger, self.policy)
    datatype = self._parse_attribute_as_str(element, "datatype", False)
    type = self._parse_attribute_as_str(element, "type", False)
    content = self._deserialize_content(element, ("bpt", "ept", "ph", "it", "hi"))
    return Sub(datatype=datatype, type=type, content=content)


class HiDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Hi]):
  """Deserializer for the TMX `<hi>` (Highlight) element."""

  def _deserialize(self, element: BackendElementType) -> Hi:
    """
    Convert a `<hi>` XML element into a Hi object.

    Parameters
    ----------
    element : BackendElementType
        The `<hi>` element to deserialize.

    Returns
    -------
    Hi
        The deserialized Hi instance.
    """
    check_tag(self.backend.get_tag(element), "hi", self.logger, self.policy)
    x = self._parse_attribute_as_int(element, "x", False)
    type = self._parse_attribute_as_str(element, "type", False)
    content = self._deserialize_content(element, ("bpt", "ept", "ph", "it", "hi"))
    return Hi(x=x, type=type, content=content)


class TuvDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Tuv]):
  """Deserializer for the TMX `<tuv>` (Translation Unit Variant) element."""

  def _deserialize(self, element: BackendElementType) -> Tuv:
    """
    Convert a `<tuv>` XML element and its `<seg>` into a Tuv object.

    Parameters
    ----------
    element : BackendElementType
        The `<tuv>` element to deserialize.

    Returns
    -------
    Tuv
        The deserialized Tuv instance.

    Raises
    ------
    XmlDeserializationError
        If extra text is found, multiple `<seg>` elements are present, or
        the `<seg>` element is missing and respective policy behavior is "raise".
    """
    check_tag(self.backend.get_tag(element), "tuv", self.logger, self.policy)

    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self.logger.log(
          self.policy.extra_text.log_level, "Element <tuv> has extra text content '%s'", text
        )
        if self.policy.extra_text.behavior == "raise":
          raise XmlDeserializationError(f"Element <tuv> has extra text content '{text}'")

    lang = self._parse_attribute_as_str(element, "xml:lang", True)
    o_encoding = self._parse_attribute_as_str(element, "o-encoding", False)
    datatype = self._parse_attribute_as_str(element, "datatype", False)
    usagecount = self._parse_attribute_as_int(element, "usagecount", False)
    lastusagedate = self._parse_attribute_as_datetime(element, "lastusagedate", False)
    creationtool = self._parse_attribute_as_str(element, "creationtool", False)
    creationtoolversion = self._parse_attribute_as_str(element, "creationtoolversion", False)
    creationdate = self._parse_attribute_as_datetime(element, "creationdate", False)
    creationid = self._parse_attribute_as_str(element, "creationid", False)
    changedate = self._parse_attribute_as_datetime(element, "changedate", False)
    changeid = self._parse_attribute_as_str(element, "changeid", False)
    o_tmf = self._parse_attribute_as_str(element, "o-tmf", False)

    props: list[Prop] = []
    notes: list[Note] = []
    content: list[str | InlineElement] | None = None
    seg_found = False

    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      if tag == "prop":
        prop = self.emit(child)
        if isinstance(prop, Prop):
          props.append(prop)
      elif tag == "note":
        note = self.emit(child)
        if isinstance(note, Note):
          notes.append(note)
      elif tag == "seg":
        if seg_found:
          self.logger.log(self.policy.multiple_seg.log_level, "Multiple <seg> elements in <tuv>")
          if self.policy.multiple_seg.behavior == "raise":
            raise XmlDeserializationError("Multiple <seg> elements in <tuv>")
          if self.policy.multiple_seg.behavior == "keep_first":
            continue
        seg_found = True
        content = self._deserialize_content(child, ("bpt", "ept", "ph", "it", "hi"))
      else:
        self.logger.log(
          self.policy.invalid_child_element.log_level, "Invalid child element <%s> in <tuv>", tag
        )
        if self.policy.invalid_child_element.behavior == "raise":
          raise XmlDeserializationError(f"Invalid child element <{tag}> in <tuv>")

    if not seg_found:
      self.logger.log(
        self.policy.missing_seg.log_level, "Element <tuv> is missing a <seg> child element"
      )
      if self.policy.missing_seg.behavior == "raise":
        raise XmlDeserializationError("Element <tuv> is missing a <seg> child element")
      elif self.policy.missing_seg.behavior == "ignore":
        content = []
      else:
        self.logger.log(self.policy.missing_seg.log_level, "Falling back to an empty string")
        content = [""]

    return Tuv(
      lang=lang,  # type: ignore[arg-type]
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
      content=content,  # type: ignore[arg-type]
    )


class TuDeserializer[BackendElementType](BaseElementDeserializer[BackendElementType, Tu]):
  """Deserializer for the TMX `<tu>` (Translation Unit) element."""

  def _deserialize(self, element: BackendElementType) -> Tu:
    """
    Convert a `<tu>` XML element and its variants into a Tu object.

    Parameters
    ----------
    element : BackendElementType
        The `<tu>` element to deserialize.

    Returns
    -------
    Tu
        The deserialized Tu instance.

    Raises
    ------
    XmlDeserializationError
        If extra text or an invalid child element is encountered and policy is "raise".
    """
    check_tag(self.backend.get_tag(element), "tu", self.logger, self.policy)

    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self.logger.log(
          self.policy.extra_text.log_level, "Element <tu> has extra text content '%s'", text
        )
        if self.policy.extra_text.behavior == "raise":
          raise XmlDeserializationError(f"Element <tu> has extra text content '{text}'")

    tuid = self._parse_attribute_as_str(element, "tuid", False)
    o_encoding = self._parse_attribute_as_str(element, "o-encoding", False)
    datatype = self._parse_attribute_as_str(element, "datatype", False)
    usagecount = self._parse_attribute_as_int(element, "usagecount", False)
    lastusagedate = self._parse_attribute_as_datetime(element, "lastusagedate", False)
    creationtool = self._parse_attribute_as_str(element, "creationtool", False)
    creationtoolversion = self._parse_attribute_as_str(element, "creationtoolversion", False)
    creationdate = self._parse_attribute_as_datetime(element, "creationdate", False)
    creationid = self._parse_attribute_as_str(element, "creationid", False)
    changedate = self._parse_attribute_as_datetime(element, "changedate", False)
    segtype = self._parse_attribute_as_enum(element, "segtype", Segtype, False)
    changeid = self._parse_attribute_as_str(element, "changeid", False)
    o_tmf = self._parse_attribute_as_str(element, "o-tmf", False)
    srclang = self._parse_attribute_as_str(element, "srclang", False)

    props: list[Prop] = []
    notes: list[Note] = []
    variants: list[Tuv] = []

    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      if tag == "prop":
        prop = self.emit(child)
        if isinstance(prop, Prop):
          props.append(prop)
      elif tag == "note":
        note = self.emit(child)
        if isinstance(note, Note):
          notes.append(note)
      elif tag == "tuv":
        tuv = self.emit(child)
        if isinstance(tuv, Tuv):
          variants.append(tuv)
      else:
        self.logger.log(
          self.policy.invalid_child_element.log_level, "Invalid child element <%s> in <tu>", tag
        )
        if self.policy.invalid_child_element.behavior == "raise":
          raise XmlDeserializationError(f"Invalid child element <{tag}> in <tu>")

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
  """Deserializer for the root `<tmx>` XML element."""

  def _deserialize(self, element: BackendElementType) -> Tmx:
    """
    Convert a `<tmx>` XML element into a Tmx object structure.

    Parameters
    ----------
    element : BackendElementType
        The root `<tmx>` element to deserialize.

    Returns
    -------
    Tmx
        The deserialized Tmx instance.

    Raises
    ------
    XmlDeserializationError
        If multiple headers are found, the header is missing, or invalid
        children exist and the policy is set to "raise".
    """
    check_tag(self.backend.get_tag(element), "tmx", self.logger, self.policy)
    version = self._parse_attribute_as_str(element, "version", True)
    header_found: bool = False
    header: Header | None = None
    body: list[Tu] = []

    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        self.logger.log(
          self.policy.extra_text.log_level, "Element <tmx> has extra text content '%s'", text
        )
        if self.policy.extra_text.behavior == "raise":
          raise XmlDeserializationError(f"Element <tmx> has extra text content '{text}'")

    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      if tag == "header":
        if header_found:
          self.logger.log(
            self.policy.multiple_headers.log_level, "Multiple <header> elements in <tmx>"
          )
          if self.policy.multiple_headers.behavior == "raise":
            raise XmlDeserializationError("Multiple <header> elements in <tmx>")
          if self.policy.multiple_headers.behavior == "keep_first":
            continue
        header_found = True
        header_obj = self.emit(child)
        if isinstance(header_obj, Header):
          header = header_obj
      elif tag == "body":
        for grandchild in self.backend.iter_children(child):
          if self.backend.get_tag(grandchild) == "tu":
            tu_obj = self.emit(grandchild)
            if isinstance(tu_obj, Tu):
              body.append(tu_obj)
      else:
        self.logger.log(
          self.policy.invalid_child_element.log_level, "Invalid child element <%s> in <tmx>", tag
        )
        if self.policy.invalid_child_element.behavior == "raise":
          raise XmlDeserializationError(f"Invalid child element <{tag}> in <tmx>")

    if not header_found:
      self.logger.log(
        self.policy.missing_header.log_level, "Element <tmx> is missing a <header> child element"
      )
      if self.policy.missing_header.behavior == "raise":
        raise XmlDeserializationError("Element <tmx> is missing a <header> child element")

    return Tmx(
      version=version,  # type: ignore[arg-type]
      header=header,  # type: ignore[arg-type]
      body=body,
    )
