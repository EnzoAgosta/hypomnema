"""XML dumpers for the public TMX node model.

The classes in this module turn Hypomnema's typed domain nodes back into
backend-specific XML elements through the shared `XmlBackend` abstraction.
Unknown structural and inline payloads are re-materialized through the backend
so preserved XML can round-trip back into output.

`XmlDumper` also exposes a type-based override registry. Overrides let callers
swap in custom dumpers for supported node classes or extend dumping for custom
node types used alongside the built-in tree.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from logging import Logger, getLogger
from typing import Protocol, TypeVar, overload

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import (
  AnyNode,
  Bpt,
  Ept,
  Hi,
  InlineContentItem,
  It,
  Note,
  Ph,
  Prop,
  Sub,
  TranslationMemory,
  TranslationMemoryHeader,
  TranslationUnit,
  TranslationVariant,
  UnknownInlineNode,
  UnknownNode,
)

DumperType = TypeVar("DumperType", contravariant=True)


class XmlDumperLike[BackendType, DumperType](Protocol):
  """Protocol implemented by objects that can dump a node into one element."""

  def dump(self, node: DumperType) -> BackendType: ...


type XmlRegisteredDumper[BackendType] = (
  XmlDumperLike[BackendType, Prop]
  | XmlDumperLike[BackendType, Note]
  | XmlDumperLike[BackendType, TranslationMemoryHeader]
  | XmlDumperLike[BackendType, Bpt]
  | XmlDumperLike[BackendType, Ept]
  | XmlDumperLike[BackendType, It]
  | XmlDumperLike[BackendType, Ph]
  | XmlDumperLike[BackendType, Hi]
  | XmlDumperLike[BackendType, Sub]
  | XmlDumperLike[BackendType, TranslationVariant]
  | XmlDumperLike[BackendType, TranslationUnit]
  | XmlDumperLike[BackendType, TranslationMemory]
  | XmlDumperLike[BackendType, UnknownNode]
  | XmlDumperLike[BackendType, UnknownInlineNode]
)


class XmlDumper[BackendType, NodeType: AnyNode | UnknownNode | UnknownInlineNode](ABC):
  """Base class for node-to-XML dumpers.

  Concrete dumpers are resolved by node type. The built-in registry covers the
  supported TMX node classes, while `register_override()` lets callers provide
  custom dumpers that participate in recursive dumping.
  """

  logger: Logger
  backend: XmlBackend[BackendType]
  _overrides: dict[type, XmlRegisteredDumper[BackendType]]
  _cache: dict[type, XmlRegisteredDumper[BackendType]]

  __slots__ = ("logger", "backend", "_overrides", "_cache")

  def __init__(
    self,
    backend: XmlBackend[BackendType],
    logger: Logger | None = None,
    overrides: dict[type, XmlRegisteredDumper[BackendType]] | None = None,
  ) -> None:
    self.logger = logger or getLogger(__name__)
    self.backend = backend
    self._overrides = {}
    self._cache = {}
    if overrides is not None:
      for tag, dumper in overrides.items():
        self.register_override(tag, dumper)

  @overload
  def register_override(
    self, node_type: type[Prop], dumper: XmlDumperLike[BackendType, Prop]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[Note], dumper: XmlDumperLike[BackendType, Note]
  ) -> None: ...
  @overload
  def register_override(
    self,
    node_type: type[TranslationMemoryHeader],
    dumper: XmlDumperLike[BackendType, TranslationMemoryHeader],
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[Bpt], dumper: XmlDumperLike[BackendType, Bpt]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[Ept], dumper: XmlDumperLike[BackendType, Ept]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[It], dumper: XmlDumperLike[BackendType, It]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[Ph], dumper: XmlDumperLike[BackendType, Ph]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[Hi], dumper: XmlDumperLike[BackendType, Hi]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[Sub], dumper: XmlDumperLike[BackendType, Sub]
  ) -> None: ...
  @overload
  def register_override(
    self,
    node_type: type[TranslationVariant],
    dumper: XmlDumperLike[BackendType, TranslationVariant],
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[TranslationUnit], dumper: XmlDumperLike[BackendType, TranslationUnit]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[TranslationMemory], dumper: XmlDumperLike[BackendType, TranslationMemory]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[UnknownNode], dumper: XmlDumperLike[BackendType, UnknownNode]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type[UnknownInlineNode], dumper: XmlDumperLike[BackendType, UnknownInlineNode]
  ) -> None: ...
  @overload
  def register_override(
    self, node_type: type, dumper: XmlRegisteredDumper[BackendType]
  ) -> None: ...
  def register_override(self, node_type: type, dumper: XmlRegisteredDumper[BackendType]) -> None:
    """Register a custom dumper for a node class.

    Overrides are consulted before the built-in dumper cache, so nested dumping
    uses the custom dumper automatically.
    """
    self._overrides[node_type] = dumper

  @overload
  def _get_dumper(self, node_type: type[Prop]) -> PropDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[Note]) -> NoteDumper[BackendType]: ...
  @overload
  def _get_dumper(
    self, node_type: type[TranslationMemoryHeader]
  ) -> TranslationMemoryHeaderDumper[BackendType]: ...
  @overload
  def _get_dumper(
    self, node_type: type[TranslationVariant]
  ) -> TranslationVariantDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[Sub]) -> SubDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[Hi]) -> HiDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[It]) -> ItDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[Ph]) -> PhDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[Ept]) -> EptDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[Bpt]) -> BptDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[TranslationUnit]) -> TranslationUnitDumper[BackendType]: ...
  @overload
  def _get_dumper(
    self, node_type: type[TranslationMemory]
  ) -> TranslationMemoryDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type[UnknownNode]) -> UnknownNodeDumper[BackendType]: ...
  @overload
  def _get_dumper(
    self, node_type: type[UnknownInlineNode]
  ) -> UnknownInlineNodeDumper[BackendType]: ...
  @overload
  def _get_dumper(self, node_type: type) -> XmlRegisteredDumper[BackendType]: ...
  def _get_dumper(self, node_type: type) -> XmlRegisteredDumper[BackendType]:
    if node_type in self._overrides:
      return self._overrides[node_type]
    if node_type in self._cache:
      return self._cache[node_type]

    if node_type is Prop:
      dumper: XmlRegisteredDumper[BackendType] = PropDumper(
        self.backend, self.logger, self._overrides
      )
    elif node_type is Note:
      dumper = NoteDumper(self.backend, self.logger, self._overrides)
    elif node_type is TranslationMemoryHeader:
      dumper = TranslationMemoryHeaderDumper(self.backend, self.logger, self._overrides)
    elif node_type is Bpt:
      dumper = BptDumper(self.backend, self.logger, self._overrides)
    elif node_type is Ept:
      dumper = EptDumper(self.backend, self.logger, self._overrides)
    elif node_type is It:
      dumper = ItDumper(self.backend, self.logger, self._overrides)
    elif node_type is Ph:
      dumper = PhDumper(self.backend, self.logger, self._overrides)
    elif node_type is Hi:
      dumper = HiDumper(self.backend, self.logger, self._overrides)
    elif node_type is Sub:
      dumper = SubDumper(self.backend, self.logger, self._overrides)
    elif node_type is TranslationVariant:
      dumper = TranslationVariantDumper(self.backend, self.logger, self._overrides)
    elif node_type is TranslationUnit:
      dumper = TranslationUnitDumper(self.backend, self.logger, self._overrides)
    elif node_type is TranslationMemory:
      dumper = TranslationMemoryDumper(self.backend, self.logger, self._overrides)
    elif node_type is UnknownNode:
      dumper = UnknownNodeDumper(self.backend, self.logger, self._overrides)
    elif node_type is UnknownInlineNode:
      dumper = UnknownInlineNodeDumper(self.backend, self.logger, self._overrides)
    else:
      raise ValueError(f"No dumper registered for type {node_type!r}")

    self._cache[node_type] = dumper
    return dumper

  @abstractmethod
  def dump(self, node: NodeType) -> BackendType:
    """Convert one domain node into a backend XML element."""
    ...

  def _add_extra(self, elem: BackendType, node: NodeType) -> None:
    if hasattr(node, "extra_attributes") and node.extra_attributes:
      for name, value in node.extra_attributes.items():
        self.backend.set_attribute(elem, name, str(value))
    if hasattr(node, "extra_nodes") and node.extra_nodes:
      unknown_dumper = self._get_dumper(UnknownNode)
      for child_node in node.extra_nodes:
        self.backend.append_child(elem, unknown_dumper.dump(child_node))

  def _add_notes_and_props(self, elem: BackendType, node: NodeType) -> None:
    if hasattr(node, "notes") and node.notes:
      note_dumper = self._get_dumper(Note)
      for note in node.notes:
        self.backend.append_child(elem, note_dumper.dump(note))
    if hasattr(node, "props") and node.props:
      prop_dumper = self._get_dumper(Prop)
      for prop in node.props:
        self.backend.append_child(elem, prop_dumper.dump(prop))

  def _populate_content[T: InlineContentItem](
    self, elem: BackendType, content: Iterable[T]
  ) -> None:
    last_child: BackendType | None = None
    for item in content:
      if isinstance(item, str):
        if last_child is None:
          if (text := self.backend.get_text(elem)) is not None:
            self.backend.set_text(elem, text + item)
          else:
            self.backend.set_text(elem, item)
        else:
          if (tail := self.backend.get_tail(last_child)) is not None:
            self.backend.set_tail(last_child, tail + item)
          else:
            self.backend.set_tail(last_child, item)
      else:
        dumper = self._get_dumper(type(item))
        # TODO: figure out why mypy is complaining about the type of dumper
        child = dumper.dump(item)  # type: ignore[arg-type]
        last_child = child
        self.backend.append_child(elem, child)


class UnknownNodeDumper[BackendType](XmlDumper[BackendType, UnknownNode]):
  """Dump preserved structural payloads back into backend elements."""

  def dump(self, node: UnknownNode) -> BackendType:
    if not isinstance(node.payload, bytes):
      raise TypeError(
        f"UnknownNode payload must be bytes for the built-in XML dumper, got {type(node.payload)!r}"
      )
    return self.backend.from_bytes(node.payload)


class UnknownInlineNodeDumper[BackendType](XmlDumper[BackendType, UnknownInlineNode]):
  """Dump preserved inline payloads back into backend elements."""

  def dump(self, node: UnknownInlineNode) -> BackendType:
    if not isinstance(node.payload, bytes):
      raise TypeError(
        "UnknownInlineNode payload must be bytes for the built-in XML dumper, "
        f"got {type(node.payload)!r}"
      )
    return self.backend.from_bytes(node.payload)


class PropDumper[BackendType](XmlDumper[BackendType, Prop]):
  """Dump `Prop` nodes as TMX `<prop>` elements."""

  def dump(self, node: Prop) -> BackendType:
    prop_elem = self.backend.create_element(
      tag="prop", attributes={"type": node.spec_attributes.kind}
    )
    self.backend.set_text(prop_elem, node.text)

    if node.spec_attributes.language is not None:
      self.backend.set_attribute(prop_elem, "xml:lang", node.spec_attributes.language)
    if node.spec_attributes.original_encoding is not None:
      self.backend.set_attribute(prop_elem, "o-encoding", node.spec_attributes.original_encoding)
    self._add_extra(prop_elem, node)

    return prop_elem


class NoteDumper[BackendType](XmlDumper[BackendType, Note]):
  """Dump `Note` nodes as TMX `<note>` elements."""

  def dump(self, node: Note) -> BackendType:
    note_elem = self.backend.create_element(tag="note")
    self.backend.set_text(note_elem, node.text)

    if node.spec_attributes.language is not None:
      self.backend.set_attribute(note_elem, "xml:lang", node.spec_attributes.language)
    if node.spec_attributes.original_encoding is not None:
      self.backend.set_attribute(note_elem, "o-encoding", node.spec_attributes.original_encoding)
    self._add_extra(note_elem, node)

    return note_elem


class TranslationMemoryHeaderDumper[BackendType](XmlDumper[BackendType, TranslationMemoryHeader]):
  """Dump `TranslationMemoryHeader` nodes as TMX `<header>` elements."""

  def dump(self, node: TranslationMemoryHeader) -> BackendType:
    header_elem = self.backend.create_element(
      tag="header",
      attributes={
        "creationtool": node.spec_attributes.creation_tool,
        "creationtoolversion": node.spec_attributes.creation_tool_version,
        "segtype": node.spec_attributes.segmentation_type.value,
        "o-tmf": node.spec_attributes.original_translation_memory_format,
        "adminlang": node.spec_attributes.admin_language,
        "srclang": node.spec_attributes.source_language,
        "datatype": node.spec_attributes.original_data_type,
      },
    )

    if node.spec_attributes.original_encoding is not None:
      self.backend.set_attribute(header_elem, "o-encoding", node.spec_attributes.original_encoding)
    if node.spec_attributes.created_at is not None:
      self.backend.set_attribute(
        header_elem, "creationdate", node.spec_attributes.created_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.created_by is not None:
      self.backend.set_attribute(header_elem, "creationid", node.spec_attributes.created_by)
    if node.spec_attributes.last_modified_at is not None:
      self.backend.set_attribute(
        header_elem, "changedate", node.spec_attributes.last_modified_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.last_modified_by is not None:
      self.backend.set_attribute(header_elem, "changeid", node.spec_attributes.last_modified_by)

    self._add_notes_and_props(header_elem, node)
    self._add_extra(header_elem, node)

    return header_elem


class BptDumper[BackendType](XmlDumper[BackendType, Bpt]):
  """Dump `Bpt` nodes as TMX `<bpt>` elements."""

  def dump(self, node: Bpt) -> BackendType:
    bpt_elem = self.backend.create_element(
      tag="bpt", attributes={"i": str(node.spec_attributes.internal_id)}
    )
    if node.spec_attributes.external_id is not None:
      self.backend.set_attribute(bpt_elem, "x", str(node.spec_attributes.external_id))
    if node.spec_attributes.kind is not None:
      self.backend.set_attribute(bpt_elem, "type", node.spec_attributes.kind)

    self._populate_content(bpt_elem, node.content)

    return bpt_elem


class EptDumper[BackendType](XmlDumper[BackendType, Ept]):
  """Dump `Ept` nodes as TMX `<ept>` elements."""

  def dump(self, node: Ept) -> BackendType:
    ept_elem = self.backend.create_element(
      tag="ept", attributes={"i": str(node.spec_attributes.internal_id)}
    )

    self._populate_content(ept_elem, node.content)

    return ept_elem


class ItDumper[BackendType](XmlDumper[BackendType, It]):
  """Dump `It` nodes as TMX `<it>` elements."""

  def dump(self, node: It) -> BackendType:
    it_elem = self.backend.create_element(
      tag="it", attributes={"pos": node.spec_attributes.position.value}
    )
    if node.spec_attributes.external_id is not None:
      self.backend.set_attribute(it_elem, "x", str(node.spec_attributes.external_id))
    if node.spec_attributes.kind is not None:
      self.backend.set_attribute(it_elem, "type", node.spec_attributes.kind)

    self._populate_content(it_elem, node.content)

    return it_elem


class PhDumper[BackendType](XmlDumper[BackendType, Ph]):
  """Dump `Ph` nodes as TMX `<ph>` elements."""

  def dump(self, node: Ph) -> BackendType:
    ph_elem = self.backend.create_element(tag="ph")
    if node.spec_attributes.association is not None:
      self.backend.set_attribute(ph_elem, "assoc", node.spec_attributes.association.value)
    if node.spec_attributes.external_id is not None:
      self.backend.set_attribute(ph_elem, "x", str(node.spec_attributes.external_id))
    if node.spec_attributes.kind is not None:
      self.backend.set_attribute(ph_elem, "type", node.spec_attributes.kind)

    self._populate_content(ph_elem, node.content)

    return ph_elem


class HiDumper[BackendType](XmlDumper[BackendType, Hi]):
  """Dump `Hi` nodes as TMX `<hi>` elements."""

  def dump(self, node: Hi) -> BackendType:
    hi_elem = self.backend.create_element(tag="hi")
    if node.spec_attributes.external_id is not None:
      self.backend.set_attribute(hi_elem, "x", str(node.spec_attributes.external_id))
    if node.spec_attributes.kind is not None:
      self.backend.set_attribute(hi_elem, "type", node.spec_attributes.kind)

    self._populate_content(hi_elem, node.content)

    return hi_elem


class SubDumper[BackendType](XmlDumper[BackendType, Sub]):
  """Dump `Sub` nodes as TMX `<sub>` elements."""

  def dump(self, node: Sub) -> BackendType:
    sub_elem = self.backend.create_element(tag="sub")
    if node.spec_attributes.original_data_type is not None:
      self.backend.set_attribute(sub_elem, "datatype", node.spec_attributes.original_data_type)
    if node.spec_attributes.kind is not None:
      self.backend.set_attribute(sub_elem, "type", node.spec_attributes.kind)

    self._populate_content(sub_elem, node.content)

    return sub_elem


class TranslationVariantDumper[BackendType](XmlDumper[BackendType, TranslationVariant]):
  """Dump `TranslationVariant` nodes as TMX `<tuv>` elements.

  The variant's inline content is always written into a single `<seg>` child.
  Notes, props, extra attributes, and preserved unknown structural children are
  emitted on the surrounding `<tuv>` element.
  """

  def dump(self, node: TranslationVariant) -> BackendType:
    variant_elem = self.backend.create_element(tag="tuv")
    if node.spec_attributes.language is not None:
      self.backend.set_attribute(variant_elem, "xml:lang", node.spec_attributes.language)
    if node.spec_attributes.original_encoding is not None:
      self.backend.set_attribute(variant_elem, "o-encoding", node.spec_attributes.original_encoding)
    if node.spec_attributes.original_data_type is not None:
      self.backend.set_attribute(variant_elem, "datatype", node.spec_attributes.original_data_type)
    if node.spec_attributes.usage_count is not None:
      self.backend.set_attribute(variant_elem, "usagecount", str(node.spec_attributes.usage_count))
    if node.spec_attributes.last_used_at is not None:
      self.backend.set_attribute(
        variant_elem, "lastusagedate", node.spec_attributes.last_used_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.creation_tool is not None:
      self.backend.set_attribute(variant_elem, "creationtool", node.spec_attributes.creation_tool)
    if node.spec_attributes.creation_tool_version is not None:
      self.backend.set_attribute(
        variant_elem, "creationtoolversion", node.spec_attributes.creation_tool_version
      )
    if node.spec_attributes.created_at is not None:
      self.backend.set_attribute(
        variant_elem, "creationdate", node.spec_attributes.created_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.created_by is not None:
      self.backend.set_attribute(variant_elem, "creationid", node.spec_attributes.created_by)
    if node.spec_attributes.last_modified_at is not None:
      self.backend.set_attribute(
        variant_elem,
        "changedate",
        node.spec_attributes.last_modified_at.strftime("%Y%m%dT%H%M%S%Z"),
      )
    if node.spec_attributes.last_modified_by is not None:
      self.backend.set_attribute(variant_elem, "changeid", node.spec_attributes.last_modified_by)
    if node.spec_attributes.original_tm_format is not None:
      self.backend.set_attribute(variant_elem, "o-tmf", node.spec_attributes.original_tm_format)

    seg_elem = self.backend.create_element(tag="seg")
    self.backend.append_child(variant_elem, seg_elem)

    self._populate_content(seg_elem, node.segment)

    self._add_notes_and_props(variant_elem, node)
    self._add_extra(variant_elem, node)

    return variant_elem


class TranslationUnitDumper[BackendType](XmlDumper[BackendType, TranslationUnit]):
  """Dump `TranslationUnit` nodes as TMX `<tu>` elements."""

  def dump(self, node: TranslationUnit) -> BackendType:
    tu_elem = self.backend.create_element(tag="tu")
    if node.spec_attributes.translation_unit_id is not None:
      self.backend.set_attribute(tu_elem, "tuid", node.spec_attributes.translation_unit_id)
    if node.spec_attributes.original_encoding is not None:
      self.backend.set_attribute(tu_elem, "o-encoding", node.spec_attributes.original_encoding)
    if node.spec_attributes.original_data_type is not None:
      self.backend.set_attribute(tu_elem, "datatype", node.spec_attributes.original_data_type)
    if node.spec_attributes.usage_count is not None:
      self.backend.set_attribute(tu_elem, "usagecount", str(node.spec_attributes.usage_count))
    if node.spec_attributes.last_used_at is not None:
      self.backend.set_attribute(
        tu_elem, "lastusagedate", node.spec_attributes.last_used_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.creation_tool is not None:
      self.backend.set_attribute(tu_elem, "creationtool", node.spec_attributes.creation_tool)
    if node.spec_attributes.creation_tool_version is not None:
      self.backend.set_attribute(
        tu_elem, "creationtoolversion", node.spec_attributes.creation_tool_version
      )
    if node.spec_attributes.created_at is not None:
      self.backend.set_attribute(
        tu_elem, "creationdate", node.spec_attributes.created_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.created_by is not None:
      self.backend.set_attribute(tu_elem, "creationid", node.spec_attributes.created_by)
    if node.spec_attributes.last_modified_at is not None:
      self.backend.set_attribute(
        tu_elem, "changedate", node.spec_attributes.last_modified_at.strftime("%Y%m%dT%H%M%S%Z")
      )
    if node.spec_attributes.segmentation_type is not None:
      self.backend.set_attribute(tu_elem, "segtype", node.spec_attributes.segmentation_type.value)
    if node.spec_attributes.last_modified_by is not None:
      self.backend.set_attribute(tu_elem, "changeid", node.spec_attributes.last_modified_by)
    if node.spec_attributes.original_tm_format is not None:
      self.backend.set_attribute(tu_elem, "o-tmf", node.spec_attributes.original_tm_format)
    if node.spec_attributes.source_language is not None:
      self.backend.set_attribute(tu_elem, "srclang", node.spec_attributes.source_language)

    if node.variants:
      variant_dumper = self._get_dumper(TranslationVariant)
      for variant in node.variants:
        self.backend.append_child(tu_elem, variant_dumper.dump(variant))

    self._add_notes_and_props(tu_elem, node)
    self._add_extra(tu_elem, node)

    return tu_elem


class TranslationMemoryDumper[BackendType](XmlDumper[BackendType, TranslationMemory]):
  """Dump `TranslationMemory` nodes as TMX `<tmx>` documents."""

  def dump(self, node: TranslationMemory) -> BackendType:
    tmx_elem = self.backend.create_element(
      tag="tmx", attributes={"version": node.spec_attributes.version}
    )
    header_dumper = self._get_dumper(TranslationMemoryHeader)
    header_elem = header_dumper.dump(node.header)
    self.backend.append_child(tmx_elem, header_elem)

    body_elem = self.backend.create_element(tag="body")
    self.backend.append_child(tmx_elem, body_elem)

    if node.units:
      unit_dumper = self._get_dumper(TranslationUnit)
      for unit in node.units:
        self.backend.append_child(body_elem, unit_dumper.dump(unit))

    self._add_extra(tmx_elem, node)

    return tmx_elem
