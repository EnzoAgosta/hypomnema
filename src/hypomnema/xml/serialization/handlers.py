"""Element serializers for TMX 1.4b.

This module provides serializer implementations for all TMX element types.
Each class handles serialization of a dataclass to its corresponding XML element.
"""

from hypomnema.base.types import Bpt, Ept, Header, Hi, It, Note, Ph, Prop, Sub, Tmx, Tu, Tuv
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


class HeaderSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Header]):
  """Serializer for Header dataclasses."""

  def _serialize(self, obj: Header) -> TypeOfBackendElement | None:
    if not isinstance(obj, Header):
      if self._handle_invalid_element_type(obj, Header) is None:
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


class TuvSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Tuv]):
  """Serializer for Tuv dataclasses."""

  def _serialize(self, obj: Tuv) -> TypeOfBackendElement | None:
    if not isinstance(obj, Tuv):
      if self._handle_invalid_element_type(obj, Tuv) is None:
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


class TuSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Tu]):
  """Serializer for Tu dataclasses."""

  def _serialize(self, obj: Tu) -> TypeOfBackendElement | None:
    if not isinstance(obj, Tu):
      if self._handle_invalid_element_type(obj, Tu) is None:
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


class TmxSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Tmx]):
  """Serializer for Tmx dataclasses."""

  def _serialize(self, obj: Tmx) -> TypeOfBackendElement | None:
    if not isinstance(obj, Tmx):
      if self._handle_invalid_element_type(obj, Tmx) is None:
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


class BptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Bpt]):
  """Serializer for Bpt dataclasses."""

  def _serialize(self, obj: Bpt) -> TypeOfBackendElement | None:
    if not isinstance(obj, Bpt):
      if self._handle_invalid_element_type(obj, Bpt) is None:
        return None

    element = self.backend.create_element("bpt")

    # Required attributes
    self._set_required_attribute(element, "i", obj.i)

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (Sub,))

    return element


class EptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Ept]):
  """Serializer for Ept dataclasses."""

  def _serialize(self, obj: Ept) -> TypeOfBackendElement | None:
    if not isinstance(obj, Ept):
      if self._handle_invalid_element_type(obj, Ept) is None:
        return None

    element = self.backend.create_element("ept")

    # Required attributes
    self._set_required_attribute(element, "i", obj.i)

    # Content
    self._serialize_content_into(element, obj.content, (Sub,))

    return element


class HiSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Hi]):
  """Serializer for Hi dataclasses."""

  def _serialize(self, obj: Hi) -> TypeOfBackendElement | None:
    if not isinstance(obj, Hi):
      if self._handle_invalid_element_type(obj, Hi) is None:
        return None

    element = self.backend.create_element("hi")

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (Bpt, Ept, Ph, It, Hi))

    return element


class ItSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, It]):
  """Serializer for It dataclasses."""

  def _serialize(self, obj: It) -> TypeOfBackendElement | None:
    if not isinstance(obj, It):
      if self._handle_invalid_element_type(obj, It) is None:
        return None

    element = self.backend.create_element("it")

    # Required attributes
    self._set_required_attribute(element, "pos", obj.pos)

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (Sub,))

    return element


class PhSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Ph]):
  """Serializer for Ph dataclasses."""

  def _serialize(self, obj: Ph) -> TypeOfBackendElement | None:
    if not isinstance(obj, Ph):
      if self._handle_invalid_element_type(obj, Ph) is None:
        return None

    element = self.backend.create_element("ph")

    # Optional attributes
    self._set_attribute(element, "x", obj.x)
    self._set_attribute(element, "assoc", obj.assoc)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (Sub,))

    return element


class SubSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Sub]):
  """Serializer for Sub dataclasses."""

  def _serialize(self, obj: Sub) -> TypeOfBackendElement | None:
    if not isinstance(obj, Sub):
      if self._handle_invalid_element_type(obj, Sub) is None:
        return None

    element = self.backend.create_element("sub")

    # Optional attributes
    self._set_attribute(element, "datatype", obj.datatype)
    self._set_attribute(element, "type", obj.type)

    # Content
    self._serialize_content_into(element, obj.content, (Bpt, Ept, Ph, It, Hi))

    return element
