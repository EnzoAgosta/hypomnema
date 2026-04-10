"""XML element loaders for the public TMX node model.

The classes in this module translate backend-specific XML elements into the
typed dataclasses from `hypomnema.domain.nodes`. Unknown structural children
are preserved as `UnknownNode` payloads and unknown inline children are
preserved as `UnknownInlineNode` payloads.

`XmlLoader` also exposes a tag-based override registry. Overrides let callers
swap in custom loaders for known tags or teach the built-in traversal logic how
to load additional elements while still using the same backend abstraction.
"""

from abc import ABC, abstractmethod
from logging import Logger, getLogger
from typing import Literal, Protocol, overload

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.backends.xml.namespace import XML_LANG_ATTR
from hypomnema.domain.attributes import Assoc, Pos, Segtype
from hypomnema.domain.nodes import (
  AnyNode,
  Bpt,
  Ept,
  Hi,
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


class UnknownNodeLoader[T]:
  """Load unsupported structural XML into `UnknownNode` payloads."""

  logger: Logger
  backend: XmlBackend[T]

  def __init__(self, backend: XmlBackend[T], logger: Logger | None = None) -> None:
    self.logger = logger or getLogger(__name__)
    self.backend = backend

  def load(self, element: T) -> UnknownNode:
    """Serialize an unmodelled child element for later round-tripping."""
    return UnknownNode(payload=self.backend.to_bytes(element, strip_tail=True))


class UnknownInlineNodeLoader[T]:
  """Load unsupported inline XML into `UnknownInlineNode` payloads."""

  logger: Logger
  backend: XmlBackend[T]

  def __init__(self, backend: XmlBackend[T], logger: Logger | None = None) -> None:
    self.logger = logger or getLogger(__name__)
    self.backend = backend

  def load(self, element: T) -> UnknownInlineNode:
    """Serialize an unmodelled inline child element for later round-tripping."""
    return UnknownInlineNode(payload=self.backend.to_bytes(element, strip_tail=True))


class XmlLoaderLike[T](Protocol):
  """Protocol implemented by loader objects that can turn one element into a node."""

  def load(self, element: T) -> AnyNode | UnknownNode | UnknownInlineNode: ...


class XmlLoader[T](ABC):
  """Base class for XML-to-node loaders.

  Concrete loaders are resolved by TMX tag name. The built-in registry covers
  the supported TMX elements, while `register_override()` lets callers attach
  custom loaders for additional tags.
  """

  logger: Logger
  backend: XmlBackend[T]
  _overrides: dict[str, XmlLoaderLike[T]]
  _cache: dict[str, XmlLoaderLike[T]]

  __slots__ = ("logger", "backend", "_overrides", "_cache")

  def __init__(
    self,
    backend: XmlBackend[T],
    logger: Logger | None = None,
    overrides: dict[str, XmlLoaderLike[T]] | None = None,
  ) -> None:
    self.logger = logger or getLogger(__name__)
    self.backend = backend
    self._overrides = {}
    self._cache = {}
    if overrides is not None:
      for tag, loader in overrides.items():
        self.register_override(tag, loader)

  @overload
  def _get_loader(self, tag: Literal["header"]) -> TranslationMemoryHeaderLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["note"]) -> NoteLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["prop"]) -> PropLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["bpt"]) -> BptLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["ept"]) -> EptLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["it"]) -> ItLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["ph"]) -> PhLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["hi"]) -> HiLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["sub"]) -> SubLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["tuv"]) -> TranslationVariantLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["tu"]) -> TranslationUnitLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["unknown"]) -> UnknownNodeLoader[T]: ...
  @overload
  def _get_loader(self, tag: Literal["unknown_inline"]) -> UnknownInlineNodeLoader[T]: ...
  @overload
  def _get_loader(self, tag: str) -> XmlLoaderLike[T]: ...
  def _get_loader(self, tag: str) -> XmlLoaderLike[T]:
    if tag in self._overrides:
      return self._overrides[tag]
    if tag in self._cache:
      return self._cache[tag]

    loader: XmlLoaderLike[T]

    match tag:
      case "header":
        loader = TranslationMemoryHeaderLoader(self.backend, self.logger, self._overrides)
      case "note":
        loader = NoteLoader(self.backend, self.logger, self._overrides)
      case "prop":
        loader = PropLoader(self.backend, self.logger, self._overrides)
      case "bpt":
        loader = BptLoader(self.backend, self.logger, self._overrides)
      case "ept":
        loader = EptLoader(self.backend, self.logger, self._overrides)
      case "it":
        loader = ItLoader(self.backend, self.logger, self._overrides)
      case "ph":
        loader = PhLoader(self.backend, self.logger, self._overrides)
      case "hi":
        loader = HiLoader(self.backend, self.logger, self._overrides)
      case "sub":
        loader = SubLoader(self.backend, self.logger, self._overrides)
      case "tuv":
        loader = TranslationVariantLoader(self.backend, self.logger, self._overrides)
      case "tu":
        loader = TranslationUnitLoader(self.backend, self.logger, self._overrides)
      case "tMX":
        loader = TranslationMemoryLoader(self.backend, self.logger, self._overrides)
      case "unknown":
        loader = UnknownNodeLoader(self.backend, self.logger)
      case "unknown_inline":
        loader = UnknownInlineNodeLoader(self.backend, self.logger)
      case _:
        raise ValueError(f"No loader registered for tag {tag!r}")

    self._cache[tag] = loader
    return loader

  def register_override(self, tag: str, loader: XmlLoaderLike[T]) -> None:
    """Register a custom loader for a tag name.

    Overrides are consulted before the built-in loader cache, so they apply to
    both direct use and recursive child loading.
    """
    self._overrides[tag] = loader

  @abstractmethod
  def load(self, element: T) -> AnyNode:
    """Convert a backend element into the corresponding domain node."""
    ...


class PropLoader[T](XmlLoader[T]):
  """Load TMX `<prop>` elements into `Prop` nodes."""

  __slots__ = ()

  def load(self, element: T) -> Prop:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "prop":
      raise ValueError(f"Expected <prop> element but got {parent_tag!r}")
    text = self.backend.get_text(element)
    if text is None:
      raise ValueError("Missing text content for <prop> element")
    attrs = self.backend.get_attribute_map(element, notation="qualified")
    try:
      kind = attrs.pop("type")
    except KeyError as e:
      raise ValueError(f"Missing attribute {e.args[0]!r} for <prop> element") from e
    language = attrs.pop(XML_LANG_ATTR, None)
    encoding = attrs.pop("o-encoding", None)
    unknown_loader = self._get_loader("unknown")
    extra_nodes: list[UnknownNode] = [
      unknown_loader.load(n) for n in self.backend.iter_children(element)
    ]
    return Prop.create(
      text=text,
      kind=kind,
      language=language,
      original_encoding=encoding,
      extra_attributes=attrs,
      extra_nodes=extra_nodes,
    )


class NoteLoader[T](XmlLoader[T]):
  """Load TMX `<note>` elements into `Note` nodes."""

  __slots__ = ()

  def load(self, element: T) -> Note:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "note":
      raise ValueError(f"Expected <note> element but got {parent_tag!r}")
    text = self.backend.get_text(element)
    if text is None:
      raise ValueError("Missing text content for <note> element")
    attrs = self.backend.get_attribute_map(element, notation="qualified")
    language = attrs.pop(XML_LANG_ATTR, None)
    encoding = attrs.pop("o-encoding", None)
    unknown_loader = self._get_loader("unknown")
    extra_nodes = [unknown_loader.load(n) for n in self.backend.iter_children(element)]
    return Note.create(
      text=text,
      language=language,
      original_encoding=encoding,
      extra_attributes=attrs,
      extra_nodes=extra_nodes,
    )


class TranslationMemoryHeaderLoader[T](XmlLoader[T]):
  """Load TMX `<header>` elements into `TranslationMemoryHeader` nodes."""

  __slots__ = ()

  def load(self, element: T) -> TranslationMemoryHeader:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "header":
      raise ValueError(f"Expected <header> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    try:
      creation_tool = attrs.pop("creationtool")
      creation_tool_version = attrs.pop("creationtoolversion")
      segmentation_type = Segtype(attrs.pop("segtype"))
      original_translation_memory_format = attrs.pop("o-tmf")
      admin_language = attrs.pop("adminlang")
      source_language = attrs.pop("srclang")
      original_data_type = attrs.pop("datatype")
    except KeyError as e:
      raise ValueError(f"Missing attribute {e.args[0]!r} for <header> element") from e
    original_encoding = attrs.pop("o-encoding", None)
    created_at = attrs.pop("creationdate", None)
    created_by = attrs.pop("creationid", None)
    last_modified_at = attrs.pop("changedate", None)
    last_modified_by = attrs.pop("changeid", None)
    note_loader = self._get_loader("note")
    prop_loader = self._get_loader("prop")
    unknown_loader = self._get_loader("unknown")
    notes: list[Note] = []
    props: list[Prop] = []
    extra_nodes: list[UnknownNode] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "note":
          notes.append(note_loader.load(child))
        case "prop":
          props.append(prop_loader.load(child))
        case _:
          extra_nodes.append(unknown_loader.load(child))
    return TranslationMemoryHeader.create(
      creation_tool=creation_tool,
      creation_tool_version=creation_tool_version,
      segmentation_type=segmentation_type,
      original_translation_memory_format=original_translation_memory_format,
      admin_language=admin_language,
      source_language=source_language,
      original_data_type=original_data_type,
      original_encoding=original_encoding,
      created_at=created_at,
      created_by=created_by,
      last_modified_at=last_modified_at,
      last_modified_by=last_modified_by,
      notes=notes,
      props=props,
      extra_attributes=attrs,
      extra_nodes=extra_nodes,
    )


class BptLoader[T](XmlLoader[T]):
  """Load TMX `<bpt>` elements into `Bpt` inline nodes."""

  __slots__ = ()

  def load(self, element: T) -> Bpt:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "bpt":
      raise ValueError(f"Expected <bpt> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    try:
      internal_id = attrs.pop("i")
    except KeyError as e:
      raise ValueError(f"Missing attribute {e.args[0]!r} for <bpt> element") from e
    external_id = attrs.pop("x", None)
    kind = attrs.pop("type", None)
    sub_loader = self._get_loader("sub")
    unknown_inline_loader = self._get_loader("unknown_inline")
    content: list[str | UnknownInlineNode | Sub] = []
    if (text := self.backend.get_text(element)) is not None:
      content.append(text)
    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      match tag:
        case "sub":
          content.append(sub_loader.load(child))
        case _:
          if tag in self._overrides:
            loader = self._get_loader(tag)
            content.append(loader.load(child))  # type: ignore[arg-type]
          else:
            content.append(unknown_inline_loader.load(child))
      if (tail := self.backend.get_tail(child)) is not None:
        content.append(tail)
    return Bpt.create(
      content=content,
      internal_id=internal_id,
      external_id=external_id,
      kind=kind,
      extra_attributes=attrs,
    )


class SubLoader[T](XmlLoader[T]):
  """Load TMX `<sub>` elements into `Sub` inline nodes."""

  __slots__ = ()

  def load(self, element: T) -> Sub:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "sub":
      raise ValueError(f"Expected <sub> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    datatype = attrs.pop("datatype", None)
    kind = attrs.pop("type", None)
    bpt_loader = self._get_loader("bpt")
    ept_loader = self._get_loader("ept")
    it_loader = self._get_loader("it")
    ph_loader = self._get_loader("ph")
    hi_loader = self._get_loader("hi")
    unknown_inline_loader = self._get_loader("unknown_inline")
    content: list[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] = []
    if (text := self.backend.get_text(element)) is not None:
      content.append(text)
    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      match tag:
        case "bpt":
          content.append(bpt_loader.load(child))
        case "ept":
          content.append(ept_loader.load(child))
        case "it":
          content.append(it_loader.load(child))
        case "ph":
          content.append(ph_loader.load(child))
        case "hi":
          content.append(hi_loader.load(child))
        case _:
          if tag in self._overrides:
            loader = self._get_loader(tag)
            content.append(loader.load(child))  # type: ignore[arg-type]
          else:
            content.append(unknown_inline_loader.load(child))
      if (tail := self.backend.get_tail(child)) is not None:
        content.append(tail)
    return Sub.create(
      content=content, original_data_type=datatype, kind=kind, extra_attributes=attrs
    )


class EptLoader[T](XmlLoader[T]):
  """Load TMX `<ept>` elements into `Ept` inline nodes."""

  __slots__ = ()

  def load(self, element: T) -> Ept:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "ept":
      raise ValueError(f"Expected <ept> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    try:
      internal_id = attrs.pop("i")
    except KeyError as e:
      raise ValueError(f"Missing attribute {e.args[0]!r} for <ept> element") from e
    sub_loader = self._get_loader("sub")
    unknown_inline_loader = self._get_loader("unknown_inline")
    content: list[str | UnknownInlineNode | Sub] = []
    if (text := self.backend.get_text(element)) is not None:
      content.append(text)
    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      match tag:
        case "sub":
          content.append(sub_loader.load(child))
        case _:
          if tag in self._overrides:
            loader = self._get_loader(tag)
            content.append(loader.load(child))  # type: ignore[arg-type]
          else:
            content.append(unknown_inline_loader.load(child))
      if (tail := self.backend.get_tail(child)) is not None:
        content.append(tail)
    return Ept.create(content=content, internal_id=internal_id, extra_attributes=attrs)


class ItLoader[T](XmlLoader[T]):
  """Load TMX `<it>` elements into `It` inline nodes."""

  __slots__ = ()

  def load(self, element: T) -> It:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "it":
      raise ValueError(f"Expected <it> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    try:
      position = Pos(attrs.pop("pos"))
    except KeyError as e:
      raise ValueError(f"Missing attribute {e.args[0]!r} for <it> element") from e
    external_id = attrs.pop("x", None)
    kind = attrs.pop("type", None)
    sub_loader = self._get_loader("sub")
    unknown_inline_loader = self._get_loader("unknown_inline")
    content: list[str | UnknownInlineNode | Sub] = []
    if (text := self.backend.get_text(element)) is not None:
      content.append(text)
    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      match tag:
        case "sub":
          content.append(sub_loader.load(child))
        case _:
          if tag in self._overrides:
            loader = self._get_loader(tag)
            content.append(loader.load(child))  # type: ignore[arg-type]
          else:
            content.append(unknown_inline_loader.load(child))
      if (tail := self.backend.get_tail(child)) is not None:
        content.append(tail)
    return It.create(
      content=content, position=position, external_id=external_id, kind=kind, extra_attributes=attrs
    )


class PhLoader[T](XmlLoader[T]):
  """Load TMX `<ph>` elements into `Ph` inline nodes."""

  __slots__ = ()

  def load(self, element: T) -> Ph:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "ph":
      raise ValueError(f"Expected <ph> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    association = attrs.pop("assoc", None)
    if association is not None:
      association = Assoc(association)
    external_id = attrs.pop("x", None)
    kind = attrs.pop("type", None)
    sub_loader = self._get_loader("sub")
    unknown_inline_loader = self._get_loader("unknown_inline")
    content: list[str | UnknownInlineNode | Sub] = []
    if (text := self.backend.get_text(element)) is not None:
      content.append(text)
    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      match tag:
        case "sub":
          content.append(sub_loader.load(child))
        case _:
          if tag in self._overrides:
            loader = self._get_loader(tag)
            content.append(loader.load(child))  # type: ignore[arg-type]
          else:
            content.append(unknown_inline_loader.load(child))
      if (tail := self.backend.get_tail(child)) is not None:
        content.append(tail)
    return Ph.create(
      content=content,
      association=association,
      external_id=external_id,
      kind=kind,
      extra_attributes=attrs,
    )


class HiLoader[T](XmlLoader[T]):
  """Load TMX `<hi>` elements into `Hi` inline nodes."""

  __slots__ = ()

  def load(self, element: T) -> Hi:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "hi":
      raise ValueError(f"Expected <hi> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    external_id = attrs.pop("x", None)
    kind = attrs.pop("type", None)
    bpt_loader = self._get_loader("bpt")
    ept_loader = self._get_loader("ept")
    it_loader = self._get_loader("it")
    ph_loader = self._get_loader("ph")
    unknown_inline_loader = self._get_loader("unknown_inline")
    content: list[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] = []
    if (text := self.backend.get_text(element)) is not None:
      content.append(text)
    for child in self.backend.iter_children(element):
      tag = self.backend.get_tag(child)
      match tag:
        case "bpt":
          content.append(bpt_loader.load(child))
        case "ept":
          content.append(ept_loader.load(child))
        case "it":
          content.append(it_loader.load(child))
        case "ph":
          content.append(ph_loader.load(child))
        case "hi":
          content.append(self.load(child))
        case _:
          if tag in self._overrides:
            loader = self._get_loader(tag)
            content.append(loader.load(child))  # type: ignore[arg-type]
          else:
            content.append(unknown_inline_loader.load(child))
      if (tail := self.backend.get_tail(child)) is not None:
        content.append(tail)
    return Hi.create(content=content, external_id=external_id, kind=kind, extra_attributes=attrs)


class TranslationVariantLoader[T](XmlLoader[T]):
  """Load TMX `<tuv>` elements into `TranslationVariant` nodes.

  The loader expects exactly one `<seg>` child. Notes, props, extra
  attributes, and unknown structural children remain attached to the variant,
  while unknown inline children inside `<seg>` become `UnknownInlineNode`
  payloads.
  """

  __slots__ = ()

  def load(self, element: T) -> TranslationVariant:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "tuv":
      raise ValueError(f"Expected <tuv> element but got {parent_tag!r}")
    if (text := self.backend.get_text(element)) is not None:
      if text.strip():
        raise ValueError(f"Text content for <tuv> element must be empty, got {text!r}")
    attrs = self.backend.get_attribute_map(element, notation="qualified")
    try:
      language = attrs.pop(XML_LANG_ATTR)
    except KeyError:
      raise ValueError("Missing attribute 'xml:lang' for <tuv> element") from None
    original_encoding = attrs.pop("o-encoding", None)
    original_data_type = attrs.pop("datatype", None)
    usage_count = attrs.pop("usagecount", None)
    last_used_at = attrs.pop("lastusagedate", None)
    creation_tool = attrs.pop("creationtool", None)
    creation_tool_version = attrs.pop("creationtoolversion", None)
    created_at = attrs.pop("creationdate", None)
    created_by = attrs.pop("creationid", None)
    last_modified_at = attrs.pop("changedate", None)
    last_modified_by = attrs.pop("changeid", None)
    original_tm_format = attrs.pop("o-tmf", None)
    note_loader = self._get_loader("note")
    prop_loader = self._get_loader("prop")
    unknown_loader = self._get_loader("unknown")
    unknown_inline_loader = self._get_loader("unknown_inline")
    bpt_loader = self._get_loader("bpt")
    ept_loader = self._get_loader("ept")
    it_loader = self._get_loader("it")
    ph_loader = self._get_loader("ph")
    hi_loader = self._get_loader("hi")
    notes: list[Note] = []
    props: list[Prop] = []
    extra_nodes: list[UnknownNode] = []
    segment_elements: list[T] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "seg":
          segment_elements.append(child)
        case "note":
          notes.append(note_loader.load(child))
        case "prop":
          props.append(prop_loader.load(child))
        case _:
          try:
            loader = self._get_loader(child_tag)
          except ValueError:
            loader = unknown_loader
          extra_nodes.append(loader.load(child))  # type: ignore[arg-type]
    segment: list[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] = []
    if not segment_elements:
      raise ValueError("Missing <seg> element")
    elif len(segment_elements) > 1:
      raise ValueError("Multiple <seg> elements")
    segment_element = segment_elements[0]
    if segment_element is not None:
      if (text := self.backend.get_text(segment_element)) is not None:
        segment.append(text)
      for child in self.backend.iter_children(segment_element):
        child_tag = self.backend.get_tag(child)
        match child_tag:
          case "bpt":
            segment.append(bpt_loader.load(child))
          case "ept":
            segment.append(ept_loader.load(child))
          case "it":
            segment.append(it_loader.load(child))
          case "ph":
            segment.append(ph_loader.load(child))
          case "hi":
            segment.append(hi_loader.load(child))
          case _:
            try:
              loader = self._get_loader(child_tag)
            except ValueError:
              loader = unknown_inline_loader
            segment.append(loader.load(child))  # type: ignore[arg-type]
        if (tail := self.backend.get_tail(child)) is not None:
          segment.append(tail)
    return TranslationVariant.create(
      language=language,
      original_encoding=original_encoding,
      original_data_type=original_data_type,
      usage_count=usage_count,
      last_used_at=last_used_at,
      creation_tool=creation_tool,
      creation_tool_version=creation_tool_version,
      created_at=created_at,
      created_by=created_by,
      last_modified_at=last_modified_at,
      last_modified_by=last_modified_by,
      original_tm_format=original_tm_format,
      notes=notes,
      props=props,
      segment=segment,
      extra_attributes=attrs,
      extra_nodes=extra_nodes,
    )


class TranslationUnitLoader[T](XmlLoader[T]):
  """Load TMX `<tu>` elements into `TranslationUnit` nodes."""

  __slots__ = ()

  def load(self, element: T) -> TranslationUnit:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "tu":
      raise ValueError(f"Expected <tu> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    translation_unit_id = attrs.pop("tuid", None)
    original_encoding = attrs.pop("o-encoding", None)
    original_data_type = attrs.pop("datatype", None)
    usage_count = attrs.pop("usagecount", None)
    last_used_at = attrs.pop("lastusagedate", None)
    creation_tool = attrs.pop("creationtool", None)
    creation_tool_version = attrs.pop("creationtoolversion", None)
    created_at = attrs.pop("creationdate", None)
    created_by = attrs.pop("creationid", None)
    last_modified_at = attrs.pop("changedate", None)
    segmentation_type = attrs.pop("segtype", None)
    if segmentation_type is not None:
      segmentation_type = Segtype(segmentation_type)
    last_modified_by = attrs.pop("changeid", None)
    original_tm_format = attrs.pop("o-tmf", None)
    source_language = attrs.pop("srclang", None)
    note_loader = self._get_loader("note")
    prop_loader = self._get_loader("prop")
    variants_loader = self._get_loader("tuv")
    notes: list[Note] = []
    props: list[Prop] = []
    extra_nodes: list[UnknownNode] = []
    variants: list[TranslationVariant] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "tuv":
          variants.append(variants_loader.load(child))
        case "note":
          notes.append(note_loader.load(child))
        case "prop":
          props.append(prop_loader.load(child))
        case _:
          try:
            loader = self._get_loader(child_tag)
          except ValueError:
            loader = self._get_loader("unknown")
          extra_nodes.append(loader.load(child))  # type: ignore[arg-type]
    return TranslationUnit.create(
      translation_unit_id=translation_unit_id,
      original_encoding=original_encoding,
      original_data_type=original_data_type,
      usage_count=usage_count,
      last_used_at=last_used_at,
      creation_tool=creation_tool,
      creation_tool_version=creation_tool_version,
      created_at=created_at,
      created_by=created_by,
      last_modified_at=last_modified_at,
      segmentation_type=segmentation_type,
      last_modified_by=last_modified_by,
      original_tm_format=original_tm_format,
      source_language=source_language,
      notes=notes,
      props=props,
      variants=variants,
      extra_attributes=attrs,
      extra_nodes=extra_nodes,
    )


class TranslationMemoryLoader[T](XmlLoader[T]):
  """Load TMX `<tmx>` documents into `TranslationMemory` nodes.

  The loader requires exactly one `<header>` and one `<body>` child. Unknown
  top-level children are preserved as `UnknownNode` payloads on the returned
  translation memory.
  """

  __slots__ = ()

  def load(self, element: T) -> TranslationMemory:
    parent_tag = self.backend.get_tag(element)
    if parent_tag != "tmx":
      raise ValueError(f"Expected <tmx> element but got {parent_tag!r}")
    attrs = self.backend.get_attribute_map(element, notation="local")
    version = attrs.pop("version")
    header_loader = self._get_loader("header")
    units_loader = self._get_loader("tu")
    header_elements: list[T] = []
    body_elements: list[T] = []
    extra_nodes: list[UnknownNode] = []
    for child in self.backend.iter_children(element):
      child_tag = self.backend.get_tag(child)
      match child_tag:
        case "header":
          header_elements.append(child)
        case "body":
          body_elements.append(child)
        case _:
          try:
            loader = self._get_loader(child_tag)
          except ValueError:
            loader = self._get_loader("unknown")
          extra_nodes.append(loader.load(child))  # type: ignore[arg-type]
    if not header_elements:
      raise ValueError("Missing <header> element")
    elif len(header_elements) > 1:
      raise ValueError("Multiple <header> elements")
    header_element = header_elements[0]
    header = header_loader.load(header_element)
    if not body_elements:
      raise ValueError("Missing <body> element")
    elif len(body_elements) > 1:
      raise ValueError("Multiple <body> elements")
    body_element = body_elements[0]
    units: list[TranslationUnit] = [
      units_loader.load(tu) for tu in self.backend.iter_children(body_element, tag_filter="tu")
    ]
    return TranslationMemory.create(
      header=header, version=version, units=units, extra_attributes=attrs, extra_nodes=extra_nodes
    )
