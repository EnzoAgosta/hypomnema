"""Element serializers for TMX 1.4b.

This module provides serializer implementations for all TMX element types.
Each class handles serialization of a dataclass to its corresponding XML element.
"""

from hypomnema.base.types import (
  BptLike,
  EptLike,
  HeaderLike,
  HiLike,
  ItLike,
  NoteLike,
  PhLike,
  PropLike,
  SubLike,
  TmxLike,
  TuLike,
  TuvLike,
)
from hypomnema.xml.serialization.base import BaseElementSerializer


class PropSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, PropLike]):
  """Serializer for Prop dataclasses."""

  def _serialize(self, obj: PropLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, PropLike):
      if self._handle_invalid_element_type(obj, PropLike) is None:
        return None

    element = self.backend.create_element("prop")

    # Text content
    text = obj.text
    if text is None:
      text = self._handle_missing_text_content(obj)
    self.backend.set_text(element, text)

    # Required attributes
    self._set_required_attribute(element, "type", obj.type)

    # Optional attributes
    self._set_attribute(element, "{http://www.w3.org/XML/1998/namespace}lang", obj.lang)
    self._set_attribute(element, "o-encoding", obj.o_encoding)

    return element


class NoteSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, NoteLike]):
  """Serializer for Note dataclasses."""

  def _serialize(self, obj: NoteLike) -> TypeOfBackendElement | None:
    # A Prop is just a note with a type attribute so it's also a NoteLike
    # so we explicitly check for both here to avoid serializing what should
    # be a Prop as a Note
    if not isinstance(obj, NoteLike) or isinstance(obj, PropLike):
      if self._handle_invalid_element_type(obj, NoteLike) is None:
        return None

    element = self.backend.create_element("note")

    # Text content
    text = obj.text
    if text is None:
      text = self._handle_missing_text_content(obj)
    self.backend.set_text(element, text)

    # Optional attributes
    self._set_attribute(element, "{http://www.w3.org/XML/1998/namespace}lang", obj.lang)
    self._set_attribute(element, "o-encoding", obj.o_encoding)
    return element


class HeaderSerializer[TypeOfBackendElement](
  BaseElementSerializer[TypeOfBackendElement, HeaderLike]
):
  """Serializer for Header dataclasses."""

  def _serialize(self, obj: HeaderLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, HeaderLike):
      if self._handle_invalid_element_type(obj, HeaderLike) is None:
        return None

    element = self.backend.create_element("header")

    # Required attributes
    self._set_required_attribute(element, "creationtool", obj.creationtool)
    self._set_required_attribute(element, "creationtoolversion", obj.creationtoolversion)
    self._set_required_attribute(element, "segtype", obj.segtype)
    self._set_required_attribute(element, "o-tmf", obj.o_tmf)
    self._set_required_attribute(element, "adminlang", obj.adminlang)
    self._set_required_attribute(element, "srclang", obj.srclang)
    self._set_required_attribute(element, "datatype", obj.datatype)

    # Optional attributes
    self._set_attribute(element, "o-encoding", obj.o_encoding)
    self._set_attribute(element, "creationdate", obj.creationdate)
    self._set_attribute(element, "creationid", obj.creationid)
    self._set_attribute(element, "changedate", obj.changedate)
    self._set_attribute(element, "changeid", obj.changeid)

    # Children
    self._serialize_children_into(element, obj.props, PropLike)
    self._serialize_children_into(element, obj.notes, NoteLike)

    return element


class TuvSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, TuvLike]):
  """Serializer for Tuv dataclasses."""

  def _serialize(self, obj: TuvLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, TuvLike):
      if self._handle_invalid_element_type(obj, TuvLike) is None:
        return None

    element = self.backend.create_element("tuv")

    # Required attributes
    self._set_required_attribute(element, "{http://www.w3.org/XML/1998/namespace}lang", obj.lang)

    # Optional attributes
    self._set_attribute(element, "o-encoding", obj.o_encoding)
    self._set_attribute(element, "datatype", obj.datatype)
    self._set_attribute(element, "usagecount", obj.usagecount)
    self._set_attribute(element, "lastusagedate", obj.lastusagedate)
    self._set_attribute(element, "creationtool", obj.creationtool)
    self._set_attribute(element, "creationtoolversion", obj.creationtoolversion)
    self._set_attribute(element, "creationdate", obj.creationdate)
    self._set_attribute(element, "creationid", obj.creationid)
    self._set_attribute(element, "changedate", obj.changedate)
    self._set_attribute(element, "changeid", obj.changeid)
    self._set_attribute(element, "o-tmf", obj.o_tmf)

    # Children
    self._serialize_children_into(element, obj.props, PropLike)
    self._serialize_children_into(element, obj.notes, NoteLike)

    # Content
    seg = self.backend.create_element("seg")
    self._serialize_content_into(seg, obj.content, False)
    self.backend.append_child(element, seg)

    return element


class TuSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, TuLike]):
  """Serializer for Tu dataclasses."""

  def _serialize(self, obj: TuLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, TuLike):
      if self._handle_invalid_element_type(obj, TuLike) is None:
        return None

    element = self.backend.create_element("tu")

    # Optional attributes
    self._set_attribute(element, "tuid", obj.tuid)
    self._set_attribute(element, "o-encoding", obj.o_encoding)
    self._set_attribute(element, "datatype", obj.datatype)
    self._set_attribute(element, "usagecount", obj.usagecount)
    self._set_attribute(element, "lastusagedate", obj.lastusagedate)
    self._set_attribute(element, "creationtool", obj.creationtool)
    self._set_attribute(element, "creationtoolversion", obj.creationtoolversion)
    self._set_attribute(element, "creationdate", obj.creationdate)
    self._set_attribute(element, "creationid", obj.creationid)
    self._set_attribute(element, "changedate", obj.changedate)
    self._set_attribute(element, "segtype", obj.segtype)
    self._set_attribute(element, "changeid", obj.changeid)
    self._set_attribute(element, "o-tmf", obj.o_tmf)
    self._set_attribute(element, "srclang", obj.srclang)

    # Children
    self._serialize_children_into(element, obj.props, PropLike)
    self._serialize_children_into(element, obj.notes, NoteLike)
    self._serialize_children_into(element, obj.variants, TuvLike)

    return element


class TmxSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, TmxLike]):
  """Serializer for Tmx dataclasses."""

  def _serialize(self, obj: TmxLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, TmxLike):
      if self._handle_invalid_element_type(obj, TmxLike) is None:
        return None

    element = self.backend.create_element("tmx")
    self._set_required_attribute(element, "version", obj.version)
    if obj.header is None:
      self._handle_required_attribute_missing("tmx", "header")
    else:
      header = self.emit(obj.header)
      if header is not None:
        self.backend.append_child(element, header)

    body = self.backend.create_element("body")
    self._serialize_children_into(body, obj.body, TuLike)
    self.backend.append_child(element, body)

    return element


class BptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, BptLike]):
  """Serializer for Bpt dataclasses."""

  def _serialize(self, obj: BptLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, BptLike):
      if self._handle_invalid_element_type(obj, BptLike) is None:
        return None

    element = self.backend.create_element("bpt")

    # Required attributes
    self._set_required_attribute(element, "i", obj.i)

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content)

    return element


class EptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, EptLike]):
  """Serializer for Ept dataclasses."""

  def _serialize(self, obj: EptLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, EptLike):
      if self._handle_invalid_element_type(obj, EptLike) is None:
        return None

    element = self.backend.create_element("ept")

    # Required attributes
    self._set_required_attribute(element, "i", obj.i)

    # Content
    self._serialize_content_into(element, obj.content)

    return element


class HiSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, HiLike]):
  """Serializer for Hi dataclasses."""

  def _serialize(self, obj: HiLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, HiLike):
      if self._handle_invalid_element_type(obj, HiLike) is None:
        return None

    element = self.backend.create_element("hi")

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, False)

    return element


class ItSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, ItLike]):
  """Serializer for It dataclasses."""

  def _serialize(self, obj: ItLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, ItLike):
      if self._handle_invalid_element_type(obj, ItLike) is None:
        return None

    element = self.backend.create_element("it")

    # Required attributes
    self._set_required_attribute(element, "pos", obj.pos)

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content)

    return element


class PhSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, PhLike]):
  """Serializer for Ph dataclasses."""

  def _serialize(self, obj: PhLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, PhLike):
      if self._handle_invalid_element_type(obj, PhLike) is None:
        return None

    element = self.backend.create_element("ph")

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "assoc", obj.assoc)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content)

    return element


class SubSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, SubLike]):
  """Serializer for Sub dataclasses."""

  def _serialize(self, obj: SubLike) -> TypeOfBackendElement | None:
    if not isinstance(obj, SubLike):
      if self._handle_invalid_element_type(obj, SubLike) is None:
        return None

    element = self.backend.create_element("sub")

    # Optional attributes
    self._set_attribute(element, "datatype", obj.datatype)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, False)

    return element
