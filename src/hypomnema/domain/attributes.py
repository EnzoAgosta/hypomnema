from dataclasses import dataclass
from datetime import datetime
from hypomnema.base.types import Assoc, Pos, Segtype
from hypomnema.domain.model import SpecDefinedAttributes
from hypomnema.domain.nodes import _VerifiedEncoding, _VerifiedLanguageCode


@dataclass(slots=True, kw_only=True)
class TranslationMemoryHeaderSpecDefinedAttributes(SpecDefinedAttributes):
  creation_tool: str
  creation_tool_version: str
  segmentation_type: Segtype
  original_translation_memory_format: str
  admin_language: _VerifiedLanguageCode
  source_language: _VerifiedLanguageCode
  original_data_type: str
  original_encoding: _VerifiedEncoding | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  last_modified_by: str | None = None


@dataclass(slots=True, kw_only=True)
class PropSpecDefinedAttributes(SpecDefinedAttributes):
  kind: str
  language: _VerifiedLanguageCode | None = None
  original_encoding: _VerifiedEncoding | None = None


@dataclass(slots=True, kw_only=True)
class NoteSpecDefinedAttributes(SpecDefinedAttributes):
  language: _VerifiedLanguageCode | None = None
  original_encoding: _VerifiedEncoding | None = None


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
  position: Pos
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class PhSpecDefinedAttributes(SpecDefinedAttributes):
  association: Assoc | None = None
  external_id: int | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class SubSpecDefinedAttributes(SpecDefinedAttributes):
  original_data_type: str | None = None
  kind: str | None = None


@dataclass(slots=True, kw_only=True)
class TranslationVariantSpecDefinedAttributes(SpecDefinedAttributes):
  language: _VerifiedLanguageCode
  original_encoding: _VerifiedEncoding | None = None
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
  original_encoding: _VerifiedEncoding | None = None
  original_data_type: str | None = None
  usage_count: int | None = None
  last_used_at: datetime | None = None
  creation_tool: str | None = None
  creation_tool_version: str | None = None
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  segmentation_type: Segtype | None = None
  last_modified_by: str | None = None
  original_tm_format: str | None = None
  source_language: _VerifiedLanguageCode | None = None


@dataclass(slots=True, kw_only=True)
class TranslationMemorySpecDefinedAttributes(SpecDefinedAttributes):
  version: str = "1.4"
