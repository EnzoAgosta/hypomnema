from hypomnema.xml.utils import assert_object_type
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
from hypomnema.xml.serialization.base import BaseElementSerializer

__all__ = [
  "PropSerializer",
  "NoteSerializer",
  "HeaderSerializer",
  "BptSerializer",
  "EptSerializer",
  "ItSerializer",
  "PhSerializer",
  "SubSerializer",
  "HiSerializer",
  "TuvSerializer",
  "TuSerializer",
  "TmxSerializer",
]


class PropSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Prop]):
  """Serializer for the TMX `<prop>` element."""

  def _serialize(self, obj: Prop) -> TypeOfBackendElement | None:
    """
    Convert a Prop object into a `<prop>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Prop instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<prop>` element, or None if type validation fails.
    """
    if not assert_object_type(obj, Prop, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("prop")
    self._set_str_attribute(element, obj.type, "type", required=True)
    self._set_str_attribute(element, obj.lang, "xml:lang", required=False)
    self._set_str_attribute(element, obj.o_encoding, "o-encoding", required=False)
    self.backend.set_text(element, obj.text)
    return element


class NoteSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Note]):
  """Serializer for the TMX `<note>` element."""

  def _serialize(self, obj: Note) -> TypeOfBackendElement | None:
    """
    Convert a Note object into a `<note>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Note instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<note>` element, or None if type validation fails.
    """
    if not assert_object_type(obj, Note, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("note")
    self._set_str_attribute(element, obj.lang, "xml:lang", required=False)
    self._set_str_attribute(element, obj.o_encoding, "o-encoding", required=False)
    self.backend.set_text(element, obj.text)
    return element


class HeaderSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Header]):
  """Serializer for the TMX `<header>` element."""

  def _serialize(self, obj: Header) -> TypeOfBackendElement | None:
    """
    Convert a Header object into a `<header>` XML element including children.

    Parameters
    ----------
    obj : BaseElement
        The Header instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<header>` element, or None if type validation fails.
    """
    if not assert_object_type(obj, Header, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("header")
    self._set_str_attribute(element, obj.creationtool, "creationtool", required=True)
    self._set_str_attribute(element, obj.creationtoolversion, "creationtoolversion", required=True)
    self._set_enum_attribute(element, obj.segtype, "segtype", Segtype, required=True)
    self._set_str_attribute(element, obj.o_tmf, "o-tmf", required=False)
    self._set_str_attribute(element, obj.adminlang, "adminlang", required=True)
    self._set_str_attribute(element, obj.srclang, "srclang", required=True)
    self._set_str_attribute(element, obj.datatype, "datatype", required=True)
    self._set_str_attribute(element, obj.o_encoding, "o-encoding", required=False)
    self._set_datetime_attribute(element, obj.creationdate, "creationdate", required=False)
    self._set_str_attribute(element, obj.creationid, "creationid", required=False)
    self._set_datetime_attribute(element, obj.changedate, "changedate", required=False)
    self._set_str_attribute(element, obj.changeid, "changeid", required=False)
    self._serialize_children(obj.notes, element, Note)
    self._serialize_children(obj.props, element, Prop)
    return element


class TuvSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Tuv]):
  """Serializer for the TMX `<tuv>` (Translation Unit Variant) element."""

  def _serialize(self, obj: Tuv) -> TypeOfBackendElement | None:
    """
    Convert a Tuv object into a `<tuv>` XML element with nested `<seg>`.

    Parameters
    ----------
    obj : BaseElement
        The Tuv instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<tuv>` element, or None if type validation fails.
    """
    if not assert_object_type(obj, Tuv, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("tuv")
    self._set_str_attribute(element, obj.lang, "xml:lang", required=True)
    self._set_str_attribute(element, obj.o_encoding, "o-encoding", required=False)
    self._set_str_attribute(element, obj.datatype, "datatype", required=False)
    self._set_int_attribute(element, obj.usagecount, "usagecount", required=False)
    self._set_datetime_attribute(element, obj.lastusagedate, "lastusagedate", required=False)
    self._set_str_attribute(element, obj.creationtool, "creationtool", required=False)
    self._set_str_attribute(element, obj.creationtoolversion, "creationtoolversion", required=False)
    self._set_datetime_attribute(element, obj.creationdate, "creationdate", required=False)
    self._set_str_attribute(element, obj.creationid, "creationid", required=False)
    self._set_datetime_attribute(element, obj.changedate, "changedate", required=False)
    self._set_str_attribute(element, obj.changeid, "changeid", required=False)
    self._set_str_attribute(element, obj.o_tmf, "o-tmf", required=False)
    self._serialize_children(obj.notes, element, Note)
    self._serialize_children(obj.props, element, Prop)
    seg_element = self.backend.create_element("seg")
    self._serialize_content_into(obj, seg_element, (Bpt, Ept, Ph, It, Hi))
    self.backend.append_child(element, seg_element)
    return element


class TuSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Tu]):
  """Serializer for the TMX `<tr>` (Translation Unit) element."""

  def _serialize(self, obj: Tu) -> TypeOfBackendElement | None:
    """
    Convert a Tu object into a `<tu>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Tu instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<tu>` element, or None if type validation fails.
    """
    if not assert_object_type(obj, Tu, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("tu")
    self._set_str_attribute(element, obj.tuid, "tuid", required=False)
    self._set_str_attribute(element, obj.o_encoding, "o-encoding", required=False)
    self._set_str_attribute(element, obj.datatype, "datatype", required=False)
    self._set_int_attribute(element, obj.usagecount, "usagecount", required=False)
    self._set_datetime_attribute(element, obj.lastusagedate, "lastusagedate", required=False)
    self._set_str_attribute(element, obj.creationtool, "creationtool", required=False)
    self._set_str_attribute(element, obj.creationtoolversion, "creationtoolversion", required=False)
    self._set_datetime_attribute(element, obj.creationdate, "creationdate", required=False)
    self._set_str_attribute(element, obj.creationid, "creationid", required=False)
    self._set_datetime_attribute(element, obj.changedate, "changedate", required=False)
    self._set_enum_attribute(element, obj.segtype, "segtype", Segtype, required=False)
    self._set_str_attribute(element, obj.changeid, "changeid", required=False)
    self._set_str_attribute(element, obj.o_tmf, "o-tmf", required=False)
    self._set_str_attribute(element, obj.srclang, "srclang", required=False)
    self._serialize_children(obj.notes, element, Note)
    self._serialize_children(obj.props, element, Prop)
    self._serialize_children(obj.variants, element, Tuv)
    return element


class TmxSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Tmx]):
  """Serializer for the root `<tmx>` element."""

  def _serialize(self, obj: Tmx) -> TypeOfBackendElement | None:
    """
    Convert a Tmx object into a `<tmx>` XML document structure.

    Parameters
    ----------
    obj : BaseElement
        The Tmx instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The root `<tmx>` element, or None if type validation fails.

    Raises
    ------
    XmlSerializationError
        If the mandatory header is not a Header instance and policy is "raise".
    """
    if not assert_object_type(obj, Tmx, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("tmx")
    self._set_str_attribute(element, obj.version, "version", required=True)
    self._serialize_children([obj.header], element, Header)
    body = self.backend.create_element("body")
    self._serialize_children(obj.body, body, Tu)
    self.backend.append_child(element, body)
    return element


class BptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Bpt]):
  """Serializer for the TMX `<bpt>` (Begin Paired Tag) element."""

  def _serialize(self, obj: Bpt) -> TypeOfBackendElement | None:
    """
    Convert a Bpt object into a `<bpt>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Bpt instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<bpt>` element.
    """
    if not assert_object_type(obj, Bpt, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("bpt")
    self._set_int_attribute(element, obj.i, "i", required=True)
    self._set_int_attribute(element, obj.x, "x", required=False)
    self._set_str_attribute(element, obj.type, "type", required=False)
    self._serialize_content_into(obj, element, (Sub,))
    return element


class EptSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Ept]):
  """Serializer for the TMX `<ept>` (End Paired Tag) element."""

  def _serialize(self, obj: Ept) -> TypeOfBackendElement | None:
    """
    Convert an Ept object into an `<ept>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Ept instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<ept>` element.
    """
    if not assert_object_type(obj, Ept, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("ept")
    self._set_int_attribute(element, obj.i, "i", required=True)
    self._serialize_content_into(obj, element, (Sub,))
    return element


class HiSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Hi]):
  """Serializer for the TMX `<hi>` (Highlight) element."""

  def _serialize(self, obj: Hi) -> TypeOfBackendElement | None:
    """
    Convert a Hi object into a `<hi>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Hi instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<hi>` element.
    """
    if not assert_object_type(obj, Hi, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("hi")
    self._set_int_attribute(element, obj.x, "x", required=False)
    self._set_str_attribute(element, obj.type, "type", required=False)
    self._serialize_content_into(obj, element, (Bpt, Ept, Ph, It, Hi))
    return element


class ItSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, It]):
  """Serializer for the TMX `<it>` (Isolated Tag) element."""

  def _serialize(self, obj: It) -> TypeOfBackendElement | None:
    """
    Convert an It object into an `<it>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The It instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<it>` element.
    """
    if not assert_object_type(obj, It, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("it")
    self._set_enum_attribute(element, obj.pos, "pos", Pos, required=True)
    self._set_int_attribute(element, obj.x, "x", required=False)
    self._set_str_attribute(element, obj.type, "type", required=False)
    self._serialize_content_into(obj, element, (Sub,))
    return element


class PhSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Ph]):
  """Serializer for the TMX `<ph>` (Placeholder) element."""

  def _serialize(self, obj: Ph) -> TypeOfBackendElement | None:
    """
    Convert a Ph object into a `<ph>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Ph instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<ph>` element.
    """
    if not assert_object_type(obj, Ph, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("ph")
    self._set_int_attribute(element, obj.x, "x", required=False)
    self._set_enum_attribute(element, obj.assoc, "assoc", Assoc, required=False)
    self._set_str_attribute(element, obj.type, "type", required=False)
    self._serialize_content_into(obj, element, (Sub,))
    return element


class SubSerializer[TypeOfBackendElement](BaseElementSerializer[TypeOfBackendElement, Sub]):
  """Serializer for the TMX `<sub>` (Sub-flow) element."""

  def _serialize(self, obj: Sub) -> TypeOfBackendElement | None:
    """
    Convert a Sub object into a `<sub>` XML element.

    Parameters
    ----------
    obj : BaseElement
        The Sub instance to serialize.

    Returns
    -------
    TypeOfBackendElement | None
        The `<sub>` element.
    """
    if not assert_object_type(obj, Sub, logger=self.logger, policy=self.policy):
      return None
    element = self.backend.create_element("sub")
    self._set_str_attribute(element, obj.datatype, "datatype", required=False)
    self._set_str_attribute(element, obj.type, "type", required=False)
    self._serialize_content_into(obj, element, (Bpt, Ept, Ph, It, Hi))
    return element
