from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from hypomnema.base.types import Assoc, Pos, Segtype
from hypomnema.domain.model import SpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class TranslationMemoryHeaderSpecDefinedAttributes(SpecDefinedAttributes):
  creation_tool: str
  creation_tool_version: str
  segmentation_type: Segtype | Literal["block", "paragraph", "sentence", "phrase"]
  original_translation_memory_format: str
  admin_language: str
  source_language: str
  original_data_type: str
  original_encoding: str | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  last_modified_by: str | None = None


@dataclass(slots=True, kw_only=True)
class PropSpecDefinedAttributes(SpecDefinedAttributes):
  kind: str
  language: str | None = None
  original_encoding: str | None = None


@dataclass(slots=True, kw_only=True)
class NoteSpecDefinedAttributes(SpecDefinedAttributes):
  language: str | None = None
  original_encoding: str | None = None


@dataclass(slots=True, kw_only=True)
class BptSpecDefinedAttributes(SpecDefinedAttributes):
  internal_id: int
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class EptSpecDefinedAttributes(SpecDefinedAttributes):
  internal_id: int


@dataclass(slots=True, kw_only=True)
class HiSpecDefinedAttributes(SpecDefinedAttributes):
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class ItSpecDefinedAttributes(SpecDefinedAttributes):
  position: Literal["begin", "end"] | Pos
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class PhSpecDefinedAttributes(SpecDefinedAttributes):
  external_id: int | None = None
  kind: str | None = None
  association: Literal["p", "f", "b"] | Assoc


@dataclass(slots=True, kw_only=True)
class SubSpecDefinedAttributes(SpecDefinedAttributes):
  original_data_type: str | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class TranslationVariantSpecDefinedAttributes(SpecDefinedAttributes):
  language: str
  original_encoding: str | None = None
  original_data_type: str | None = None
  usage_count: int | None = None
  last_used_at: datetime | None = None
  creation_tool: str | None = None
  creation_tool_version: str | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  last_modified_by: str | None = None
  original_tm_format: str | None = None


@dataclass(slots=True, kw_only=True)
class TranslationUnitSpecDefinedAttributes(SpecDefinedAttributes):
  translation_unit_id: str | None = None
  original_encoding: str | None = None
  original_data_type: str | None = None
  usage_count: int | None = None
  last_used_at: datetime | None = None
  creation_tool: str | None = None
  creation_tool_version: str | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  segmentation_type: Segtype | Literal["block", "paragraph", "sentence", "phrase"] | None = None
  last_modified_by: str | None = None
  original_tm_format: str | None = None
  source_language: str | None = None


@dataclass(slots=True, kw_only=True)
class TranslationMemorySpecDefinedAttributes(SpecDefinedAttributes):
  version: str = "1.4"
