from __future__ import annotations
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


from hypomnema.domain.attributes import (
  Assoc,
  BptSpecDefinedAttributes,
  EncodingString,
  EptSpecDefinedAttributes,
  ISODateString,
  IntOrConvertibleToInt,
  LanguageCodeString,
  Pos,
  Segtype,
  TranslationMemoryHeaderSpecDefinedAttributes,
  HiSpecDefinedAttributes,
  ItSpecDefinedAttributes,
  NoteSpecDefinedAttributes,
  PhSpecDefinedAttributes,
  PropSpecDefinedAttributes,
  SubSpecDefinedAttributes,
  TranslationMemorySpecDefinedAttributes,
  TranslationUnitSpecDefinedAttributes,
  TranslationVariantSpecDefinedAttributes,
  _verify_encoding,
  _verify_language_code,
)


type AttributeValue = object
type UnknownPayload = object


@dataclass(slots=True, kw_only=True)
class UnknownInlineNode:
  payload: UnknownPayload


@dataclass(slots=True, kw_only=True)
class UnknownNode:
  payload: UnknownPayload


@dataclass(slots=True, kw_only=True)
class Note:
  spec_attributes: NoteSpecDefinedAttributes
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)
  text: str

  @classmethod
  def create(
    cls,
    text: str,
    language: LanguageCodeString | None = None,
    original_encoding: EncodingString | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> Note:
    if original_encoding is not None:
      original_encoding = _verify_encoding(original_encoding)
    if language is not None:
      language = _verify_language_code(language)
    return Note(
      spec_attributes=NoteSpecDefinedAttributes(
        language=language, original_encoding=original_encoding
      ),
      text=text,
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class Prop:
  spec_attributes: PropSpecDefinedAttributes
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)
  text: str

  @classmethod
  def create(
    cls,
    text: str,
    kind: str,
    language: LanguageCodeString | None = None,
    original_encoding: EncodingString | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> Prop:
    if original_encoding is not None:
      original_encoding = _verify_encoding(original_encoding)
    if language is not None:
      language = _verify_language_code(language)
    return Prop(
      spec_attributes=PropSpecDefinedAttributes(
        kind=kind, language=language, original_encoding=original_encoding
      ),
      text=text,
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class TranslationMemoryHeader:
  spec_attributes: TranslationMemoryHeaderSpecDefinedAttributes
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    creation_tool: str,
    creation_tool_version: str,
    segmentation_type: Segtype | Literal["block", "paragraph", "sentence", "phrase"],
    original_translation_memory_format: str,
    admin_language: LanguageCodeString,
    source_language: LanguageCodeString,
    original_data_type: str,
    original_encoding: EncodingString | None = None,
    created_at: datetime | ISODateString | None = None,
    created_by: str | None = None,
    last_modified_at: datetime | ISODateString | None = None,
    last_modified_by: str | None = None,
    notes: Iterable[Note] | None = None,
    props: Iterable[Prop] | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> TranslationMemoryHeader:
    if isinstance(created_at, str):
      created_at = datetime.fromisoformat(created_at)
    if isinstance(last_modified_at, str):
      last_modified_at = datetime.fromisoformat(last_modified_at)
    segmentation_type = Segtype(segmentation_type)
    if original_encoding is not None:
      original_encoding = _verify_encoding(original_encoding)
    if admin_language is not None:
      admin_language = _verify_language_code(admin_language)
    if source_language is not None:
      source_language = _verify_language_code(source_language)

    return TranslationMemoryHeader(
      spec_attributes=TranslationMemoryHeaderSpecDefinedAttributes(
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
      ),
      notes=list(notes or []),
      props=list(props or []),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class Bpt:
  spec_attributes: BptSpecDefinedAttributes
  content: list[str | UnknownInlineNode | Sub] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)

  @classmethod
  def create(
    cls,
    content: Iterable[str | UnknownInlineNode | Sub],
    internal_id: IntOrConvertibleToInt,
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
  ) -> Bpt:
    internal_id = int(internal_id)
    if external_id is not None:
      external_id = int(external_id)

    return Bpt(
      spec_attributes=BptSpecDefinedAttributes(
        internal_id=internal_id, external_id=external_id, kind=kind
      ),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
    )


@dataclass(slots=True, kw_only=True)
class Ept:
  spec_attributes: EptSpecDefinedAttributes
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  content: list[str | UnknownInlineNode | Sub] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    content: Iterable[str | UnknownInlineNode | Sub],
    internal_id: IntOrConvertibleToInt,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
  ) -> Ept:
    internal_id = int(internal_id)
    return Ept(
      spec_attributes=EptSpecDefinedAttributes(internal_id=internal_id),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
    )


@dataclass(slots=True, kw_only=True)
class It:
  spec_attributes: ItSpecDefinedAttributes
  content: list[str | UnknownInlineNode | Sub] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)

  @classmethod
  def create(
    cls,
    content: Iterable[str | UnknownInlineNode | Sub],
    position: Literal["begin", "end"] | Pos,
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
  ) -> It:
    position = Pos(position)
    if external_id is not None:
      external_id = int(external_id)

    return It(
      spec_attributes=ItSpecDefinedAttributes(
        position=position, external_id=external_id, kind=kind
      ),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
    )


@dataclass(slots=True, kw_only=True)
class Ph:
  spec_attributes: PhSpecDefinedAttributes
  content: list[str | UnknownInlineNode | Sub] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)

  @classmethod
  def create(
    cls,
    content: Iterable[str | UnknownInlineNode | Sub],
    association: Literal["p", "f", "b"] | Assoc | None = None,
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
  ) -> Ph:
    if association is not None:
      association = Assoc(association)
    if external_id is not None:
      external_id = int(external_id)
    return Ph(
      spec_attributes=PhSpecDefinedAttributes(
        association=association, external_id=external_id, kind=kind
      ),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
    )


@dataclass(slots=True, kw_only=True)
class Hi:
  spec_attributes: HiSpecDefinedAttributes
  content: list[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)

  @classmethod
  def create(
    cls,
    content: Iterable[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi],
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
  ) -> Hi:
    if external_id is not None:
      external_id = int(external_id)
    return Hi(
      spec_attributes=HiSpecDefinedAttributes(external_id=external_id, kind=kind),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
    )


@dataclass(slots=True, kw_only=True)
class Sub:
  spec_attributes: SubSpecDefinedAttributes
  content: list[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)

  @classmethod
  def create(
    cls,
    content: Iterable[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi],
    original_data_type: str | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
  ) -> Sub:
    return Sub(
      spec_attributes=SubSpecDefinedAttributes(original_data_type=original_data_type, kind=kind),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
    )


@dataclass(slots=True, kw_only=True)
class TranslationVariant:
  spec_attributes: TranslationVariantSpecDefinedAttributes
  segment: list[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    language: LanguageCodeString,
    original_encoding: EncodingString | None = None,
    original_data_type: str | None = None,
    usage_count: IntOrConvertibleToInt | None = None,
    last_used_at: datetime | ISODateString | None = None,
    creation_tool: str | None = None,
    creation_tool_version: str | None = None,
    created_at: datetime | ISODateString | None = None,
    created_by: str | None = None,
    last_modified_at: datetime | ISODateString | None = None,
    last_modified_by: str | None = None,
    original_tm_format: str | None = None,
    notes: Iterable[Note] | None = None,
    props: Iterable[Prop] | None = None,
    segment: Iterable[str | UnknownInlineNode | Bpt | Ept | It | Ph | Hi] | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> TranslationVariant:
    language = _verify_language_code(language)
    if original_encoding is not None:
      original_encoding = _verify_encoding(original_encoding)
    if usage_count is not None:
      usage_count = int(usage_count)
    if isinstance(last_used_at, str):
      last_used_at = datetime.fromisoformat(last_used_at)
    if isinstance(created_at, str):
      created_at = datetime.fromisoformat(created_at)
    if isinstance(last_modified_at, str):
      last_modified_at = datetime.fromisoformat(last_modified_at)

    return TranslationVariant(
      spec_attributes=TranslationVariantSpecDefinedAttributes(
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
      ),
      notes=list(notes or []),
      props=list(props or []),
      segment=list(segment or []),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class TranslationUnit:
  spec_attributes: TranslationUnitSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)
  variants: list[TranslationVariant] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    translation_unit_id: str | None = None,
    original_encoding: EncodingString | None = None,
    original_data_type: str | None = None,
    usage_count: IntOrConvertibleToInt | None = None,
    last_used_at: datetime | ISODateString | None = None,
    creation_tool: str | None = None,
    creation_tool_version: str | None = None,
    created_at: datetime | ISODateString | None = None,
    created_by: str | None = None,
    last_modified_at: datetime | ISODateString | None = None,
    segmentation_type: Segtype | None = None,
    last_modified_by: str | None = None,
    original_tm_format: str | None = None,
    source_language: LanguageCodeString | None = None,
    notes: Iterable[Note] | None = None,
    props: Iterable[Prop] | None = None,
    variants: Iterable[TranslationVariant] | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> TranslationUnit:
    if original_encoding is not None:
      original_encoding = _verify_encoding(original_encoding)
    if usage_count is not None:
      usage_count = int(usage_count)
    if isinstance(last_used_at, str):
      last_used_at = datetime.fromisoformat(last_used_at)
    if isinstance(created_at, str):
      created_at = datetime.fromisoformat(created_at)
    if isinstance(last_modified_at, str):
      last_modified_at = datetime.fromisoformat(last_modified_at)
    if segmentation_type is not None:
      segmentation_type = Segtype(segmentation_type)
    if source_language is not None:
      source_language = _verify_language_code(source_language)

    return TranslationUnit(
      spec_attributes=TranslationUnitSpecDefinedAttributes(
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
      ),
      notes=list(notes or []),
      props=list(props or []),
      variants=list(variants or []),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class TranslationMemory:
  spec_attributes: TranslationMemorySpecDefinedAttributes
  header: TranslationMemoryHeader
  units: list[TranslationUnit] = field(default_factory=list)
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    header: TranslationMemoryHeader,
    version: str = "1.4",
    units: Iterable[TranslationUnit] | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> TranslationMemory:
    return TranslationMemory(
      spec_attributes=TranslationMemorySpecDefinedAttributes(version=version),
      header=header,
      units=list(units or []),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


type StructuralNode = (
  TranslationMemory | TranslationMemoryHeader | TranslationUnit | TranslationVariant
)
type LeafNode = Prop | Note
type InlineNode = Bpt | Ept | It | Ph | Hi | Sub
type ContentNode = InlineNode | TranslationVariant
type AnyNode = StructuralNode | LeafNode | InlineNode
type InlineContentItem = str | InlineNode | UnknownInlineNode
