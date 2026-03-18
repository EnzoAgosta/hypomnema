from __future__ import annotations
from dataclasses import dataclass, field

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
from hypomnema.domain.model import InlineContentItem, InlineNode, StructuralNode


@dataclass(slots=True, kw_only=True)
class Note(StructuralNode[NoteSpecDefinedAttributes]):
  spec_attributes: NoteSpecDefinedAttributes
  text: str


@dataclass(slots=True, kw_only=True)
class Prop(StructuralNode[PropSpecDefinedAttributes]):
  spec_attributes: PropSpecDefinedAttributes
  text: str


@dataclass(slots=True, kw_only=True)
class TranslationMemoryHeader(StructuralNode[TranslationMemoryHeaderSpecDefinedAttributes]):
  spec_attributes: TranslationMemoryHeaderSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Bpt(InlineNode[BptSpecDefinedAttributes]):
  spec_attributes: BptSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class Ept(InlineNode[EptSpecDefinedAttributes]):
  spec_attributes: EptSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class It(InlineNode[ItSpecDefinedAttributes]):
  spec_attributes: ItSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class Ph(InlineNode[PhSpecDefinedAttributes]):
  spec_attributes: PhSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class Hi(InlineNode[HiSpecDefinedAttributes]):
  spec_attributes: HiSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class Sub(InlineNode[SubSpecDefinedAttributes]):
  spec_attributes: SubSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class TranslationVariant(StructuralNode[TranslationVariantSpecDefinedAttributes]):
  spec_attributes: TranslationVariantSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)
  segment: list[InlineContentItem] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class TranslationUnit(StructuralNode[TranslationUnitSpecDefinedAttributes]):
  spec_attributes: TranslationUnitSpecDefinedAttributes
  notes: list[Note] = field(default_factory=list)
  props: list[Prop] = field(default_factory=list)
  variants: list[TranslationVariant] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class TranslationMemory(StructuralNode[TranslationMemorySpecDefinedAttributes]):
  spec_attributes: TranslationMemorySpecDefinedAttributes
  header: TranslationMemoryHeader
  units: list[TranslationUnit] = field(default_factory=list)
