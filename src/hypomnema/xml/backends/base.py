from logging import Logger
from contextlib import nullcontext
from pathlib import Path
from io import BufferedIOBase
from hypomnema.xml.utils import prep_tag_set, make_usable_path, normalize_encoding
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterator, Generator, Iterable, Mapping
from os import PathLike
from hypomnema.base.errors import MissingNamespaceError
from hypomnema.xml.policy import XmlBackendPolicy

__all__ = ["XmlBackend"]


class XmlBackend[BackendElementType](ABC):
  __slots__ = ("_global_nsmap", "policy", "logger")
  _global_nsmap: dict[str | None, str]
  """
  Global namespace map for all elements in the form of {prefix: uri}.
  Individual elements may override this map with their own (like in the
  case of lxml).
  Each applicable function also accepts a `nsmap` parameter
  that can be used to override the global map on a per-function basis.
  Can be set on Backend instantiation and must be updated manually via
  the `register_namespace` method.
  """
  policy: XmlBackendPolicy
  logger: Logger

  @abstractmethod
  def get_tag(self, element: BackendElementType) -> str: ...
  @abstractmethod
  def get_localname(
    self, element: BackendElementType, *, nsmap: dict[str | None, str] | None = None
  ) -> str: ...
  @abstractmethod
  def get_prefix(
    self, element: BackendElementType, *, nsmap: dict[str | None, str] | None = None
  ) -> str | None: ...
  @abstractmethod
  def get_uri(
    self, element: BackendElementType, *, nsmap: dict[str | None, str] | None = None
  ) -> str | None: ...
  @abstractmethod
  def create(
    self,
    tag: str,
    attributes: Mapping[str, str] | None = None,
    nsmap: dict[str | None, str] | None = None,
  ) -> BackendElementType: ...
  @abstractmethod
  def append_child(self, parent: BackendElementType, child: BackendElementType) -> None: ...
  @abstractmethod
  def get_attribute(
    self,
    element: BackendElementType,
    key: str,
    default: str | None = None,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> str | None: ...
  @abstractmethod
  def set_attribute(
    self,
    element: BackendElementType,
    key: str,
    val: str,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> None: ...
  @abstractmethod
  def get_attributes(self, element: BackendElementType) -> dict[str, str]: ...
  @abstractmethod
  def get_text(self, element: BackendElementType) -> str | None: ...
  @abstractmethod
  def set_text(self, element: BackendElementType, text: str | None) -> None: ...
  @abstractmethod
  def get_tail(self, element: BackendElementType) -> str | None: ...
  @abstractmethod
  def set_tail(self, element: BackendElementType, tail: str | None) -> None: ...
  @abstractmethod
  def iter_children(
    self,
    element: BackendElementType,
    tags: str | Collection[str] | None = None,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> Iterator[BackendElementType]: ...
  @abstractmethod
  def parse(
    self,
    path: str | bytes | PathLike,
    encoding: str | None = None,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> BackendElementType: ...
  @abstractmethod
  def write(
    self,
    element: BackendElementType,
    path: str | bytes | PathLike,
    encoding: str | None = None,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> None: ...
  @abstractmethod
  def iterparse(
    self,
    path: str | bytes | PathLike,
    tags: str | Collection[str] | None = None,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> Iterator[BackendElementType]: ...
  @abstractmethod
  def clear(self, element: BackendElementType) -> None: ...
  @abstractmethod
  def to_bytes(
    self, element: BackendElementType, encoding: str | None = None, self_closing: bool = False
  ) -> bytes: ...
  def register_namespace(self, prefix: str, uri: str) -> None:
    """
    Register a namespace prefix. The namespace map is global for all elements.
    """
    if not isinstance(prefix, str):
      raise TypeError(f"Prefix must be a string, got {type(prefix)}")
    if not isinstance(uri, str):
      raise TypeError(f"URI must be a string, got {type(uri)}")
    self._global_nsmap[prefix] = uri

  def _iterparse(
    self,
    ctx: Iterator[tuple[str, BackendElementType]],
    tags: str | Collection[str] | None = None,
    *,
    nsmap: dict[str | None, str] | None = None,
  ) -> Generator[BackendElementType]:
    try:
      tag_set = prep_tag_set(tags)
    except MissingNamespaceError as e:
      if self.policy.missing_namespace.behavior == "raise":
        raise e
      elif self.policy.missing_namespace.behavior == "global":
        self.logger.log(self.policy.missing_namespace.log_level, "Falling back to global nsmap")
        tag_set = prep_tag_set(tags, self._global_nsmap)
      else:
        tag_set = prep_tag_set(tags, None)
    pending_yield_stack: list[BackendElementType] = []

    for event, elem in ctx:
      if event == "start":
        tag = self.get_localname(elem, nsmap=nsmap)
        if tag_set is None or tag in tag_set:
          pending_yield_stack.append(elem)
        continue
      if not pending_yield_stack:
        self.clear(elem)
        continue
      if elem is pending_yield_stack[-1]:
        pending_yield_stack.pop()
        yield elem
      if not pending_yield_stack:
        self.clear(elem)

  def iterwrite(
    self,
    path: str | bytes | PathLike | BufferedIOBase,
    elements: Iterable[BackendElementType],
    encoding: str | None = None,
    *,
    root_elem: BackendElementType | None = None,
    max_elements_in_buffer: int = 1000,
  ) -> None:
    if isinstance(path, (str, bytes, PathLike)):
      path = make_usable_path(path)
    if max_elements_in_buffer < 1:
      raise ValueError("buffer_size must be >= 1")
    _encoding: str = normalize_encoding(encoding)
    if root_elem is None:
      root_elem = self.create("tmx", attributes={"version": "1.4"})

    root_string = self.to_bytes(root_elem, _encoding)
    pos = root_string.rfind(b"</")
    if pos == -1:
      raise ValueError("Cannot find closing tag for root element: " + root_string.decode(_encoding))

    buffer = []
    ctx = open(path, "wb") if isinstance(path, Path) else nullcontext(path)

    with ctx as output:
      output.seek(0)
      output.truncate(0)
      output.write(b'<?xml version="1.0" encoding="' + _encoding.encode("ascii") + b'"?>\n')
      output.write(b'<!DOCTYPE tmx SYSTEM "tmx14.dtd">\n')
      output.write(root_string[:pos])
      for elem in elements:
        buffer.append(self.to_bytes(elem, _encoding))
        if len(buffer) == max_elements_in_buffer:
          output.write(b"".join(buffer))
          buffer.clear()
      if buffer:
        output.write(b"".join(buffer))
      output.write(root_string[pos:])
