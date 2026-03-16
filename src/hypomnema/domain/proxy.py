from dataclasses import fields
from datetime import datetime
from typing import ClassVar, Type

from hypomnema.domain.model import Node, SpecDefinedAttributes


__cache: dict[int, frozenset[str]] = {}


def _spec_field_names(spec_cls: Type[SpecDefinedAttributes]) -> frozenset[str]:
  if id(spec_cls) not in __cache:
    __cache[id(spec_cls)] = frozenset(f.name for f in fields(spec_cls))
  return __cache[id(spec_cls)]


def _merged_proxy_annotations(cls: type["ProxyBase"]) -> dict[str, object]:
  merged: dict[str, object] = {}

  for base in reversed(cls.__mro__):
    if base is object:
      continue
    if not issubclass(base, ProxyBase):
      continue

    annotations = getattr(base, "__annotations__", None)
    if annotations:
      merged.update(annotations)

  merged.pop("node", None)
  return merged


class ProxyBase:
  __slots__ = ("node",)
  __proxy_fields__: ClassVar[frozenset[str]] = frozenset()
  __allow_extra_attributes__: ClassVar[bool] = False

  node: Node

  def __init_subclass__(cls) -> None:
    super().__init_subclass__()
    cls.__proxy_fields__ = frozenset(_merged_proxy_annotations(cls))

  def __init__(self, node: Node) -> None:
    object.__setattr__(self, "node", node)

    proxy_fields = type(self).__proxy_fields__
    spec_fields = _spec_field_names(type(node.spec_attributes))
    extra_fields = (
      frozenset(node.extra_attributes) if type(self).__allow_extra_attributes__ else frozenset()
    )

    if missing := (proxy_fields - (spec_fields | extra_fields)):
      raise TypeError(
        f"{type(self).__name__} cannot wrap node {node!r}; missing fields: {sorted(missing)}"
      )

  def __getattr__(self, name: str) -> object:
    proxy_fields = type(self).__proxy_fields__
    if name not in proxy_fields:
      raise AttributeError(f"{type(self).__name__!s} has no declared attribute {name!r}")

    node: Node = object.__getattribute__(self, "node")

    if hasattr(node.spec_attributes, name):
      return getattr(node.spec_attributes, name)

    if type(self).__allow_extra_attributes__ and name in node.extra_attributes:
      return node.extra_attributes[name]

    raise AttributeError(f"{type(self).__name__!s} could not resolve attribute {name!r}")


class AuditView(ProxyBase):
  created_at: datetime | None = None
  created_by: str | None = None
  last_modified_at: datetime | None = None
  last_modified_by: str | None = None


class UsageView(ProxyBase):
  usage_count: int | None = None
  last_used_at: datetime | None = None


class ProvenanceView(ProxyBase):
  creation_tool: str | None = None
  creation_tool_version: str | None = None
  original_tm_format: str | None = None
  original_encoding: str | None = None
  original_data_type: str | None = None
