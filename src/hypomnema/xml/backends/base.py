from typing import TypeVar, overload, Literal
from logging import Logger, getLogger
from contextlib import nullcontext
from pathlib import Path
from io import BufferedIOBase
from hypomnema.xml.utils import make_usable_path, normalize_encoding, is_ncname, QName
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterator, Generator, Iterable, Mapping, MutableMapping
from os import PathLike

__all__ = ["XmlBackend"]

T_Element = TypeVar("T_Element")
T_AttributeKey = TypeVar("T_AttributeKey")
T_AttributeValue = TypeVar("T_AttributeValue")
T_Attributes = Mapping[T_AttributeKey, T_AttributeValue]


class XmlBackend[T_Element, T_Attributes](ABC):
  __slots__ = ("_global_nsmap", "logger")
  _global_nsmap: MutableMapping[str | None, str]
  logger: Logger

  def __init__(
    self, nsmap: Mapping[str | None, str] | None = None, *, logger: Logger | None = None
  ) -> None:
    self.logger = logger if logger is not None else getLogger("XmlBackendLogger")
    self._global_nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}
    if nsmap is not None:
      for prefix, uri in nsmap.items():
        self.register_namespace(prefix, uri)

  @overload
  @abstractmethod
  def get_tag(
    self,
    element: T_Element,
    *,
    as_qname: Literal[True],
    nsmap: Mapping[str | None, str] | None = None,
  ) -> QName: ...
  @overload
  @abstractmethod
  def get_tag(
    self,
    element: T_Element,
    *,
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str: ...
  @abstractmethod
  def get_tag(
    self,
    element: T_Element,
    *,
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | QName: ...

  @abstractmethod
  def create_element(
    self,
    tag: str | QName,
    attributes: T_Attributes | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> T_Element: ...
  @abstractmethod
  def append_child(self, parent: T_Element, child: T_Element) -> None: ...
  @abstractmethod
  def get_attribute(
    self,
    element: T_Element,
    attribute_name: T_AttributeKey,
    default: T_AttributeValue | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> T_AttributeValue: ...
  @abstractmethod
  def set_attribute(
    self,
    element: T_Element,
    attribute_name: T_AttributeKey,
    attribute_value: T_AttributeValue | None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> None: ...
  @abstractmethod
  def get_attribute_map(self, element: T_Element) -> T_Attributes: ...
  @abstractmethod
  def get_text(self, element: T_Element) -> str | None: ...
  @abstractmethod
  def set_text(self, element: T_Element, text: str | None) -> None: ...
  @abstractmethod
  def get_tail(self, element: T_Element) -> str | None: ...
  @abstractmethod
  def set_tail(self, element: T_Element, tail: str | None) -> None: ...
  @abstractmethod
  def iter_children(
    self,
    element: T_Element,
    tag_filter: str | Collection[str] | None = None,
    *,
    nsmap: Mapping[str, str] | None = None,
  ) -> Iterator[T_Element]: ...
  @abstractmethod
  def parse(self, path: str | bytes | PathLike, encoding: str = "utf-8") -> T_Element: ...
  @abstractmethod
  def write(
    self, element: T_Element, path: str | bytes | PathLike, encoding: str = "utf-8"
  ) -> None: ...
  @abstractmethod
  def clear(self, element: T_Element) -> None: ...
  @abstractmethod
  def to_bytes(
    self, element: T_Element, encoding: str = "utf-8", self_closing: bool = False
  ) -> bytes: ...
  def register_namespace(self, prefix: str | None, uri: str) -> None:
    if not isinstance(uri, str):
      raise TypeError(f"given uri is not a str: {uri}")
    if not isinstance(prefix, str):
      raise TypeError(f"given prefix is not a str: {prefix}")
    if not is_ncname(prefix):
      raise ValueError(f"NCName {prefix} is not a valid xml prefix")
    self._global_nsmap[prefix] = uri

  @abstractmethod
  def iterparse(
    self,
    path: str | bytes | PathLike,
    tag_filter: str | Collection[str] | None = None,
    *,
    nsmap: Mapping[str, str] | None = None,
  ) -> Iterator[T_Element]: ...

  def _iterparse(
    self, ctx: Iterator[tuple[str, T_Element]], tag_filter: set[str] | None
  ) -> Generator[T_Element]:
    elements_pending_yield: list[T_Element] = []

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
    path: str | bytes | PathLike | BufferedIOBase,
    elements: Iterable[T_Element],
    encoding: str = "utf-8",
    *,
    root_elem: T_Element | None = None,
    max_number_of_elements_in_buffer: int = 1000,
    write_xml_declaration: bool = True,
    write_doctype: bool = True,
  ) -> None:
    if max_number_of_elements_in_buffer < 1:
      raise ValueError("buffer_size must be >= 1")
    if isinstance(path, (str, bytes, PathLike)):
      path = make_usable_path(path)
    _encoding = normalize_encoding(encoding)
    if root_elem is None:
      root_elem = self.create_element("tmx", attributes={"version": "1.4"})

    root_string = self.to_bytes(root_elem, _encoding, self_closing=False)
    pos = root_string.rfind(b"</")
    if pos == -1:
      raise ValueError(
        "Cannot find closing tag for root element after converting to bytes with 'self_closing=True'. Please check to_bytes() implementation.",
        root_string.decode(_encoding),
      )

    buffer = []
    ctx = open(path, "wb") if isinstance(path, Path) else nullcontext(path)

    with ctx as output:
      if write_xml_declaration:
        output.write(b'<?xml version="1.0" encoding="' + _encoding.encode(_encoding) + b'"?>\n')
      if write_doctype:
        output.write(b'<!DOCTYPE tmx SYSTEM "tmx14.dtd">\n')
      output.write(root_string[:pos])
      for elem in elements:
        buffer.append(self.to_bytes(elem, _encoding))
        if len(buffer) == max_number_of_elements_in_buffer:
          output.write(b"".join(buffer))
          buffer.clear()
      if buffer:
        output.write(b"".join(buffer))
      output.write(root_string[pos:])
