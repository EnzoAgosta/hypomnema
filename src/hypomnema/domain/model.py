from __future__ import annotations

from dataclasses import dataclass, field


type AttributeValue = object
type UnknownPayload = object
type InlineContentItem = str | InlineNode[SpecDefinedAttributes] | UnknownInlineNode


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
class WithExtra:
  extra_attributes: dict[str, AttributeValue] = field(default_factory=dict)
  extra_nodes: list[UnknownNode] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Node[NodeSpecDefinedAttributes: SpecDefinedAttributes](WithExtra):
  spec_attributes: NodeSpecDefinedAttributes


@dataclass(slots=True, kw_only=True)
class InlineNode[InlineNodeSpecDefinedAttributes: SpecDefinedAttributes](WithExtra):
  spec_attributes: InlineNodeSpecDefinedAttributes
  content: list[InlineContentItem] = field(default_factory=list)
