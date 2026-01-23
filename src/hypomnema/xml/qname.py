from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from hypomnema.base.errors import NamespaceError
from hypomnema.xml.utils import is_ncname, is_valid_uri

__all__ = ["QName", "QNameLike"]


@runtime_checkable
class QNameLike(Protocol):
  text: str


class QName:
  uri: str | None
  prefix: str | None
  local_name: str

  def __init__(
    self, tag: str | QNameLike, *, nsmap: Mapping[str | None, str] | None = None
  ) -> None:
    if isinstance(tag, QNameLike):
      tag = tag.text
    if not tag:
      raise ValueError("tag must not be empty")
    self.prefix = None
    self.uri = None

    # Clark notation {uri}localname
    if tag[0] == "{":
      ns, tag = tag[1:].split("}", 1)
      if not is_valid_uri(ns):
        raise ValueError(f"{ns} is not a valid xml uri")
      if not is_ncname(tag):
        raise ValueError(f"{tag} is not a valid xml localname")
      self.uri = ns
      self.local_name = tag
      if nsmap is not None:
        for prefix, uri in nsmap.items():
          if uri == ns:
            self.prefix = prefix
            break
        else:
          raise NamespaceError(f"{ns} is not registered")
      else:
        raise NamespaceError("nsmap is required to resolve uri tags")

    # Prefixed notation prefix:localname (usually never given by xml libraries)
    elif tag.count(":") == 1:
      prefix, localname = tag.split(":", 1)
      if not is_ncname(prefix):
        raise ValueError(f"NCName {prefix} is not a valid xml prefix")
      if not is_ncname(localname):
        raise ValueError(f"NCName {localname} is not a valid xml localname")
      self.prefix = prefix
      self.local_name = localname
      if nsmap is not None:
        for _prefix, uri in nsmap.items():
          if _prefix == prefix:
            self.uri = uri
            break
        else:
          raise NamespaceError(f"{prefix} is not registered")
      else:
        raise NamespaceError("nsmap is required to resolve prefixed tags")
    else:
      if not is_ncname(tag):
        raise ValueError(f"{tag} is not a valid xml tag")
      self.local_name = tag
      self.uri = None
      self.prefix = None

  @property
  def qualified_name(self) -> str:
    if self.uri is None:
      return self.local_name
    return "{" + self.uri + "}" + self.local_name

  @property
  def prefixed_name(self) -> str:
    if self.prefix is None:
      return self.local_name
    return self.prefix + ":" + self.local_name

  @property
  def text(self) -> str:
    return self.qualified_name

  def __str__(self) -> str:
    return self.qualified_name

  def __repr__(self) -> str:
    return f"QName({self.qualified_name!r})"
