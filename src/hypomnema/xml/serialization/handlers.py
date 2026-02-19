"""Element serializers for TMX 1.4b.

This module provides serializer implementations for all TMX element types.
Each class handles serialization of a dataclass to its corresponding XML element.
"""

from hypomnema.base.types import (
  Bpt,
  BptBase,
  Ept,
  EptBase,
  HeaderBase,
  Hi,
  HiBase,
  It,
  ItBase,
  Note,
  Ph,
  PhBase,
  Prop,
  SubBase,
  TmxBase,
  Tu,
  TuBase,
  Tuv,
  TuvBase,
)
from hypomnema.xml.serialization.base import BaseElementSerializer


class PropSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Prop]):
  """Serializer for Prop dataclasses."""

  def _serialize(self, obj: Prop) -> TypeOfBackendElement | None:
    if not isinstance(obj, Prop):
      if self._handle_invalid_element_type(obj, Prop) is None:
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


class NoteSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Note]):
  """Serializer for Note dataclasses."""

  def _serialize(self, obj: Note) -> TypeOfBackendElement | None:
    if not isinstance(obj, Note):
      if self._handle_invalid_element_type(obj, Note) is None:
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
  BaseElementSerializer[TypeOfBackendElement, HeaderBase]
):
  """Serializer for Header dataclasses."""

  def _serialize(self, obj: HeaderBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, HeaderBase):
      if self._handle_invalid_element_type(obj, HeaderBase) is None:
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
    self._serialize_children_into(element, obj.props, Prop)
    self._serialize_children_into(element, obj.notes, Note)

    return element


class TuvSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, TuvBase]):
  """Serializer for Tuv dataclasses."""

  def _serialize(self, obj: TuvBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, TuvBase):
      if self._handle_invalid_element_type(obj, TuvBase) is None:
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
    self._serialize_children_into(element, obj.props, Prop)
    self._serialize_children_into(element, obj.notes, Note)

    # Content
    seg = self.backend.create_element("seg")
    self._serialize_content_into(seg, obj.content, (Bpt, Ept, It, Ph, Hi))
    self.backend.append_child(element, seg)

    return element


class TuSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, TuBase]):
  """Serializer for Tu dataclasses."""

  def _serialize(self, obj: TuBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, TuBase):
      if self._handle_invalid_element_type(obj, TuBase) is None:
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
    self._serialize_children_into(element, obj.props, Prop)
    self._serialize_children_into(element, obj.notes, Note)
    self._serialize_children_into(element, obj.variants, Tuv)

    return element


class TmxSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, TmxBase]):
  """Serializer for Tmx dataclasses."""

  def _serialize(self, obj: TmxBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, TmxBase):
      if self._handle_invalid_element_type(obj, TmxBase) is None:
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
    self._serialize_children_into(body, obj.body, Tu)
    self.backend.append_child(element, body)

    return element


class BptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, BptBase]):
  """Serializer for Bpt dataclasses."""

  def _serialize(self, obj: BptBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, BptBase):
      if self._handle_invalid_element_type(obj, BptBase) is None:
        return None

    element = self.backend.create_element("bpt")

    # Required attributes
    self._set_required_attribute(element, "i", obj.i)

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (SubBase,))

    return element


class EptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, EptBase]):
  """Serializer for Ept dataclasses."""

  def _serialize(self, obj: EptBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, EptBase):
      if self._handle_invalid_element_type(obj, EptBase) is None:
        return None

    element = self.backend.create_element("ept")

    # Required attributes
    self._set_required_attribute(element, "i", obj.i)

    # Content
    self._serialize_content_into(element, obj.content, (SubBase,))

    return element


class HiSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, HiBase]):
  """Serializer for Hi dataclasses."""

  def _serialize(self, obj: HiBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, HiBase):
      if self._handle_invalid_element_type(obj, HiBase) is None:
        return None

    element = self.backend.create_element("hi")

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (BptBase, EptBase, PhBase, ItBase, HiBase))

    return element


class ItSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, ItBase]):
  """Serializer for It dataclasses."""

  def _serialize(self, obj: ItBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, ItBase):
      if self._handle_invalid_element_type(obj, ItBase) is None:
        return None

    element = self.backend.create_element("it")

    # Required attributes
    self._set_required_attribute(element, "pos", obj.pos)

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (SubBase,))

    return element


class PhSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, PhBase]):
  """Serializer for Ph dataclasses."""

  def _serialize(self, obj: PhBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, PhBase):
      if self._handle_invalid_element_type(obj, PhBase) is None:
        return None

    element = self.backend.create_element("ph")

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "assoc", obj.assoc)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (SubBase,))

    return element


class SubSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, SubBase]):
  """Serializer for Sub dataclasses."""

  def _serialize(self, obj: SubBase) -> TypeOfBackendElement | None:
    if not isinstance(obj, SubBase):
      if self._handle_invalid_element_type(obj, SubBase) is None:
        return None

    element = self.backend.create_element("sub")

    # Optional attributes
    self._set_attribute(element, "datatype", obj.datatype)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (BptBase, EptBase, PhBase, ItBase, HiBase))

    return element
