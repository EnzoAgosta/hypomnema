from __future__ import annotations
import codecs
from collections.abc import Iterable, Mapping, Buffer
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, SupportsIndex, SupportsInt, cast


from hypomnema.base.types import Assoc, Pos, Segtype
from hypomnema.domain.attributes import (
  BptSpecDefinedAttributes,
  EptSpecDefinedAttributes,
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
)
from hypomnema.domain.model import (
  AttributeValue,
  InlineContentItem,
  InlineNode,
  StructuralNode,
  UnknownNode,
)

# basically anything that can be passed to int()
type IntOrConvertibleToInt = str | Buffer | SupportsIndex | SupportsInt


# This one doesn't follow the below pattern as we'll actualy convert it to a datetime
# when creating a node, so it's only used for typing in functions to let users know the
# str should be a valid ISO 8601 datetime string
type ISODateString = str


# Python's type system is not able to narrow the type of a string literal like TypeScript
# does. To get around it we define two types:
#
# - A public alias `type Foo = str`: used in public-facing signatures to signal intent
#   ("this should be a valid Foo") without burdening callers with a custom type. Follows
#   the "lax input" half of the "lax input, strict output" philosophy.
#
# - An internal subclass `class _VerifiedFoo(str)`: a nominally distinct type used in
#   internal APIs to indicate the value has been validated. At runtime it remains a plain
#   str (we use `cast` rather than constructing a subclass instance), so the distinction
#   is purely for the type checker. This enforces that validation happens at the boundary
#   before values flow into internal code.
#
# The intended flow is:
#   1. Public functions accept the wide alias (e.g. `Encoding`, `LanguageCode`).
#   2. A `_verify_*` function validates and narrows the type to the internal subclass.
#   3. Internal APIs declare the subclass in their signatures, making the validation
#      requirement explicit and statically checkable.
#
# This gives us self-documenting APIs, enforced validation boundaries, and zero runtime
# overhead from the type narrowing itself.

type LanguageCode = str
type Encoding = str


class _VerifiedEncoding(str):
  """A str that has been verified to be a valid encoding via codecs.lookup."""

  pass


class _VerifiedLanguageCode(str):
  """A str that has been verified to be a valid language code via iso639.db."""

  pass


def _verify_encoding(encoding: str) -> _VerifiedEncoding:
  codecs.lookup(encoding)
  return cast(_VerifiedEncoding, encoding)


def _verify_language_code(language_code: str) -> _VerifiedLanguageCode:
  # TODO: fiure out how we want to handle language codes
  return cast(_VerifiedLanguageCode, language_code)


@dataclass(slots=True, kw_only=True)
class Note(StructuralNode[NoteSpecDefinedAttributes]):
  spec_attributes: NoteSpecDefinedAttributes
  text: str

  @classmethod
  def create(
    cls,
    text: str,
    language: LanguageCode | None = None,
    original_encoding: Encoding | None = None,
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
class Prop(StructuralNode[PropSpecDefinedAttributes]):
  spec_attributes: PropSpecDefinedAttributes
  text: str

  @classmethod
  def create(
    cls,
    text: str,
    kind: str,
    language: LanguageCode | None = None,
    original_encoding: Encoding | None = None,
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
class TranslationMemoryHeader(StructuralNode[TranslationMemoryHeaderSpecDefinedAttributes]):
  spec_attributes: TranslationMemoryHeaderSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    creation_tool: str,
    creation_tool_version: str,
    segmentation_type: Segtype | Literal["block", "paragraph", "sentence", "phrase"],
    original_translation_memory_format: str,
    admin_language: LanguageCode,
    source_language: LanguageCode,
    original_data_type: str,
    original_encoding: Encoding | None = None,
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
        creation_tool_version=str(creation_tool_version),
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
class Bpt(InlineNode[BptSpecDefinedAttributes]):
  spec_attributes: BptSpecDefinedAttributes

  @classmethod
  def create(
    cls,
    content: Iterable[InlineContentItem],
    internal_id: IntOrConvertibleToInt,
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
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
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class Ept(InlineNode[EptSpecDefinedAttributes]):
  spec_attributes: EptSpecDefinedAttributes

  @classmethod
  def create(
    cls,
    content: Iterable[InlineContentItem],
    internal_id: IntOrConvertibleToInt,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> Ept:
    internal_id = int(internal_id)
    return Ept(
      spec_attributes=EptSpecDefinedAttributes(internal_id=internal_id),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class It(InlineNode[ItSpecDefinedAttributes]):
  spec_attributes: ItSpecDefinedAttributes

  @classmethod
  def create(
    cls,
    content: Iterable[InlineContentItem],
    position: Literal["begin", "end"] | Pos,
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
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
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class Ph(InlineNode[PhSpecDefinedAttributes]):
  spec_attributes: PhSpecDefinedAttributes

  @classmethod
  def create(
    cls,
    content: Iterable[InlineContentItem],
    association: Literal["p", "f", "b"] | Assoc | None = None,
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
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
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class Hi(InlineNode[HiSpecDefinedAttributes]):
  spec_attributes: HiSpecDefinedAttributes

  @classmethod
  def create(
    cls,
    content: Iterable[InlineContentItem],
    external_id: IntOrConvertibleToInt | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> Hi:
    if external_id is not None:
      external_id = int(external_id)
    return Hi(
      spec_attributes=HiSpecDefinedAttributes(external_id=external_id, kind=kind),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class Sub(InlineNode[SubSpecDefinedAttributes]):
  spec_attributes: SubSpecDefinedAttributes

  @classmethod
  def create(
    cls,
    content: Iterable[InlineContentItem],
    original_data_type: str | None = None,
    kind: str | None = None,
    extra_attributes: Mapping[str, AttributeValue] | None = None,
    extra_nodes: Iterable[UnknownNode] | None = None,
  ) -> Sub:
    return Sub(
      spec_attributes=SubSpecDefinedAttributes(original_data_type=original_data_type, kind=kind),
      content=list(content),
      extra_attributes={k: v for k, v in (extra_attributes or {}).items()},
      extra_nodes=list(extra_nodes or []),
    )


@dataclass(slots=True, kw_only=True)
class TranslationVariant(StructuralNode[TranslationVariantSpecDefinedAttributes]):
  spec_attributes: TranslationVariantSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)
  segment: list[InlineContentItem] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    language: LanguageCode,
    original_encoding: Encoding | None = None,
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
    segment: Iterable[InlineContentItem] | None = None,
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
class TranslationUnit(StructuralNode[TranslationUnitSpecDefinedAttributes]):
  spec_attributes: TranslationUnitSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)
  variants: list[TranslationVariant] = field(default_factory=list)

  @classmethod
  def create(
    cls,
    translation_unit_id: str | None = None,
    original_encoding: Encoding | None = None,
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
    source_language: LanguageCode | None = None,
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
class TranslationMemory(StructuralNode[TranslationMemorySpecDefinedAttributes]):
  spec_attributes: TranslationMemorySpecDefinedAttributes
  header: TranslationMemoryHeader
  units: list[TranslationUnit] = field(default_factory=list)

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


type ContentNode = InlineNode | TranslationVariant
