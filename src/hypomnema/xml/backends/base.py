from typing import overload, Literal
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.policy import XmlPolicy
import logging
from hypomnema.base import NamespaceError
from logging import Logger, getLogger
from contextlib import nullcontext
from pathlib import Path
from io import BufferedIOBase
from hypomnema.xml.utils import make_usable_path, normalize_encoding, is_ncname, is_valid_uri
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterator, Generator, Iterable, Mapping
from os import PathLike
from pathlib import Path
from typing import Literal, overload

from hypomnema.base.errors import NamespaceError
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.utils import (is_ncname, is_valid_uri, make_usable_path,
                                 normalize_encoding)

__all__ = ["XmlBackend"]


class XmlBackend[TypeOfElement](ABC):
  __slots__ = ("_nsmap", "logger", "default_encoding", "policy")
  _nsmap: dict[str | None, str]
  logger: Logger
  default_encoding: str
  policy: XmlPolicy

  def __init__(
    self,
    nsmap: Mapping[str, str] | None = None,
    logger: Logger | None = None,
    default_encoding: str | None = None,
    policy: XmlPolicy | None = None,
  ) -> None:
    self.logger = logger if logger is not None else getLogger("XmlBackendLogger")
    self._nsmap = {"xml": "http://www.w3.org/XML/1998/namespace", None: "http://www.lisa.org/tmx14"}
    self.default_encoding = normalize_encoding(default_encoding) if default_encoding is not None else "utf-8"
    self.logger.log(logging.DEBUG, "Initialized with default encoding %s", self.default_encoding)
    self.policy = policy if policy is not None else XmlPolicy()
    if nsmap is not None:
      for prefix, uri in nsmap.items():
        self.register_namespace(prefix, uri)

  def register_namespace(self, prefix: str, uri: str) -> None:
    if prefix in ("xml", None):
      raise NamespaceError(f"{prefix} is a reserved prefix and cannot be registered again")
    if uri in ("http://www.w3.org/XML/1998/namespace", "http://www.lisa.org/tmx14"):
      raise NamespaceError(f"{uri} is reserved URI and cannot be registered again")
    try:
      if not is_ncname(prefix):
        raise NamespaceError(f"{prefix} is not a valid xml prefix")
      if not is_valid_uri(uri):
        raise NamespaceError(f"{uri} is not a valid xml uri")
    except NamespaceError as e:
      self.logger.log(
        self.policy.invalid_namespace.log_level, "Failed to register namespace: %s", e
      )
      if self.policy.invalid_namespace.behavior == "raise":
        raise 
      else:
        return
    if prefix in self._nsmap:
      self.logger.log(
        self.policy.existing_namespace.log_level, "Namespace %s already registered", prefix
      )
      if self.policy.existing_namespace.behavior == "raise":
        raise NamespaceError(f"Namespace {prefix} is already registered")
      elif self.policy.existing_namespace.behavior == "overwrite":
        self._nsmap[prefix] = uri
        self.logger.log(logging.DEBUG, "Overwrote namespace: %s -> %s", prefix, uri)
        return
      else:
        return
    self._nsmap[prefix] = uri
    self.logger.log(logging.DEBUG, "Registered namespace: %s -> %s", prefix, uri)

  def deregister_namespace(self, prefix: str) -> None:
    if prefix in ("xml", None):
      raise NamespaceError(f"{prefix} is reserved and cannot be deregistered")
    if prefix in self._nsmap:
      del self._nsmap[prefix]
      self.logger.log(logging.DEBUG, "Deregistered namespace: %s", prefix)
    else:
      self.logger.log(
        self.policy.missing_namespace.log_level, "Namespace %s is not registered", prefix
      )
      if self.policy.missing_namespace.behavior == "ignore":
        return
      raise NamespaceError(f"{prefix} is not registered and cannot be deregistered")

  @property
  def nsmap(self) -> dict[str | None, str]:
    return {k: v for k, v in self._nsmap.items()}

  @nsmap.setter
  def nsmap(self, value: dict[str | None, str]) -> None:
    raise AttributeError(
      "nsmap is read-only. Use register_namespace() and deregister_namespace() instead."
    )

  @nsmap.deleter
  def nsmap(self) -> None:
    raise AttributeError(
      "nsmap is read-only. Use register_namespace() and deregister_namespace() instead."
    )

  @overload
  def get_tag(self, element: TypeOfElement, as_qname: Literal[True]) -> QName: ...
  @overload
  def get_tag(self, element: TypeOfElement, as_qname: bool = False) -> str: ...
  @abstractmethod
  def get_tag(self, element: TypeOfElement, as_qname: bool = False) -> str | QName: ...

  @abstractmethod
  def create_element(
    self, tag: str, attributes: Mapping[str, str] | None = None
  ) -> TypeOfElement: ...

  @abstractmethod
  def append_child(self, parent: TypeOfElement, child: TypeOfElement) -> None: ...

  @abstractmethod
  def get_attribute[TypeOfDefault](
    self, element: TypeOfElement, attribute_name: str, default: TypeOfDefault | None = None
  ) -> str | TypeOfDefault | None: ...

  @abstractmethod
  def set_attribute(
    self, element: TypeOfElement, attribute_name: str | QNameLike, attribute_value: str
  ) -> None: ...

  @abstractmethod
  def delete_attribute(self, element: TypeOfElement, attribute_name: str | QNameLike) -> None: ...

  @abstractmethod
  def get_attribute_map(self, element: TypeOfElement) -> dict[str, str]: ...

  @abstractmethod
  def get_text(self, element: TypeOfElement) -> str | None: ...

  @abstractmethod
  def set_text(self, element: TypeOfElement, text: str | None) -> None: ...

  @abstractmethod
  def get_tail(self, element: TypeOfElement) -> str | None: ...

  @abstractmethod
  def set_tail(self, element: TypeOfElement, tail: str | None) -> None: ...

  @abstractmethod
  def iter_children(
    self,
    element: TypeOfElement,
    tag_filter: str | QNameLike | Collection[str | QNameLike] | None = None,
  ) -> Iterator[TypeOfElement]: ...

  @abstractmethod
  def parse(self, path: str | PathLike, encoding: str | None = None) -> TypeOfElement: ...

  @abstractmethod
  def write(
    self, element: TypeOfElement, path: str | PathLike, encoding: str | None = None
  ) -> None: ...

  @abstractmethod
  def clear(self, element: TypeOfElement) -> None: ...

  @abstractmethod
  def to_bytes(
    self, element: TypeOfElement, encoding: str | None = None, self_closing: bool = False
  ) -> bytes: ...

  @abstractmethod
  def iterparse(
    self, path: str | PathLike, tag_filter: str | Collection[str] | None = None
  ) -> Iterator[TypeOfElement]: ...

  def _iterparse(
    self, ctx: Iterator[tuple[str, TypeOfElement]], tag_filter: set[str] | None
  ) -> Generator[TypeOfElement]:
    elements_pending_yield: list[TypeOfElement] = []

    for event, elem in ctx:
      if event == "start":
        tag = self.get_tag(elem)
        if tag_filter is None or tag in tag_filter:
          elements_pending_yield.append(elem)
        continue
      if not elements_pending_yield:
        self.clear(elem)
        continue
      if elem is elements_pending_yield[-1]:
        elements_pending_yield.pop()
        yield elem
      if not elements_pending_yield:
        self.clear(elem)

  def iterwrite(
    self,
    path: str | PathLike | BufferedIOBase,
    elements: Iterable[TypeOfElement],
    encoding: str | None = None,
    *,
    root_elem: TypeOfElement | None = None,
    max_number_of_elements_in_buffer: int = 1000,
    write_xml_declaration: bool = False,
    write_doctype: bool = False,
  ) -> None:
    if max_number_of_elements_in_buffer < 1:
      raise ValueError("buffer_size must be >= 1")
    if isinstance(path, (str, PathLike)):
      path = make_usable_path(path)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    if root_elem is None:
      root_elem = self.create_element("tmx", attributes={"version": "1.4"})

    root_string = self.to_bytes(root_elem, encoding, self_closing=False)
    pos = root_string.rfind("</".encode(encoding))
    if pos == -1:
      raise ValueError(
        "Cannot find closing tag for root element after converting to bytes with 'self_closing=True'. Please check to_bytes() implementation.",
        root_string.decode(encoding),
      )

    buffer = []
    ctx = open(path, "wb") if isinstance(path, Path) else nullcontext(path)

    with ctx as output:
      if write_xml_declaration:
        output.write('<?xml version="1.0" encoding="'.encode(encoding) + encoding.encode(encoding) + '"?>\n'.encode(encoding))
      if write_doctype:
        output.write('<!DOCTYPE tmx SYSTEM "tmx14.dtd">\n'.encode(encoding))
      output.write(root_string[:pos])
      for elem in elements:
        buffer.append(self.to_bytes(elem, encoding))
        if len(buffer) == max_number_of_elements_in_buffer:
          output.write(b"".join(buffer))
          buffer.clear()
      if buffer:
        output.write(b"".join(buffer))
      output.write(root_string[pos:])
