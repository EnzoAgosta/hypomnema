from __future__ import annotations

from dataclasses import dataclass, field


type AttributeValue = object
type UnknownPayload = object
type InlineContentItem = str | InlineNode | UnknownInlineNode


@dataclass(slots=True, kw_only=True)
class SpecDefinedAttributes:
  pass


@dataclass(slots=True, kw_only=True)
class UnknownInlineNode:
  payload: UnknownPayload


@dataclass(slots=True, kw_only=True)
class UnknownNode:
  payload: UnknownPayload


@dataclass(slots=True, kw_only=True)
class BaseNode[T_Base: SpecDefinedAttributes]:
  spec_attributes: T_Base
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class StructuralNode[T_Structural: SpecDefinedAttributes](BaseNode[T_Structural]):
  pass


@dataclass(slots=True, kw_only=True)
class InlineNode[T_Inline: SpecDefinedAttributes](BaseNode[T_Inline]):
  content: list[InlineContentItem] = field(default_factory=list)
