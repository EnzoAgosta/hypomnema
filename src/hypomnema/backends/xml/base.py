"""Shared XML backend abstractions.

This module defines the `XmlBackendLike` protocol (the public contract) and
`XmlBackend` abstract base class (shared concrete logic). Code outside the
backend layer should type against `XmlBackendLike`; concrete backends inherit
from `XmlBackend`.

Concrete backends are expected to provide behavioral parity, not byte-identical
serialization.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Iterator, Mapping, MutableMapping
from logging import Logger, getLogger
from os import PathLike, fspath
from typing import BinaryIO, Literal, Protocol, TextIO, overload

from hypomnema.backends.xml.namespace import (
  register_namespace,
  deregister_prefix as _deregister_prefix,
  deregister_uri as _deregister_uri,
)
from hypomnema.backends.xml.utils import make_usable_path, normalize_encoding


class XmlBackendLike[E](Protocol):
  """Protocol defining the public contract for XML backends.

  Loaders, dumpers, and external code type against this interface.
  """

  default_encoding: str

  def register_namespace(self, prefix: str, uri: str) -> None: ...
  def deregister_prefix(self, prefix: str) -> None: ...
  def deregister_uri(self, uri: str) -> None: ...
  @property
  def global_nsmap(self) -> dict[str, str]: ...

  def get_tag(
    self,
    element: E,
    *,
    notation: Literal["qualified", "local", "prefixed"] = "qualified",
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str: ...
  def create_element(
    self,
    tag: str | bytes,
    attributes: Mapping[str, str] | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> E: ...
  def append_child(self, parent: E, child: E) -> None: ...
  @overload
  def get_attribute(
    self, element: E, name: str | bytes, *, nsmap: MutableMapping[str, str] | None = None
  ) -> str | None: ...
  @overload
  def get_attribute[D](
    self,
    element: E,
    name: str | bytes,
    *,
    default: D,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str | D: ...
  def get_attribute[D](
    self,
    element: E,
    name: str | bytes,
    *,
    default: D | None = None,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str | D | None: ...
  def set_attribute(
    self,
    element: E,
    name: str | bytes,
    value: str,
    *,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> None: ...
  def delete_attribute(
    self, element: E, name: str | bytes, *, nsmap: MutableMapping[str, str] | None = None
  ) -> None: ...
  def get_attribute_map(
    self,
    element: E,
    *,
    notation: Literal["qualified", "local", "prefixed"] = "qualified",
    nsmap: MutableMapping[str, str] | None = None,
  ) -> dict[str, str]: ...
  def get_text(self, element: E) -> str | None: ...
  def set_text(self, element: E, text: str | None) -> None: ...
  def get_tail(self, element: E) -> str | None: ...
  def set_tail(self, element: E, tail: str | None) -> None: ...
  def iter_children(
    self,
    element: E,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> Generator[E]: ...
  def parse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    encoding: str | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> E: ...
  def from_bytes(
    self,
    data: bytes,
    encoding: str | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> E: ...
  def from_string(
    self,
    data: str,
    encoding: str | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> E: ...
  def write(
    self,
    element: E,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    encoding: str | None = None,
  ) -> None: ...
  def clear(self, element: E) -> None: ...
  def to_bytes(
    self,
    element: E,
    encoding: str | None = None,
    *,
    self_closing: bool = False,
    strip_tail: bool = False,
  ) -> bytes: ...
  def to_string(
    self, element: E, *, self_closing: bool = False, strip_tail: bool = False
  ) -> str: ...
  def iterparse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | TextIO | BinaryIO,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> Iterator[E]: ...
  def iterwrite(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    elements: Iterable[E],
    *,
    encoding: str | None = None,
    root_elem: E | None = None,
    max_number_of_elements_in_buffer: int = 1000,
    write_xml_declaration: bool = False,
    doctype: str | None = None,
  ) -> None: ...


class XmlBackend[E](ABC):
  """Abstract base class for XML backend implementations.

  Provides shared concrete logic for namespace management, tag resolution,
  and streaming I/O. Subclassed by :class:`StandardBackend` and
  :class:`LxmlBackend`.

  Args:
      default_encoding: Default character encoding (keyword-only).
      logger: Logger for backend operations.
      global_nsmap: Initial namespace mappings.
  """

  __slots__ = ("_global_nsmap", "logger", "default_encoding")

  _global_nsmap: dict[str, str]
  logger: Logger
  default_encoding: str

  def __init__(
    self,
    *,
    default_encoding: str | None = None,
    logger: Logger | None = None,
    global_nsmap: MutableMapping[str, str] | None = None,
  ) -> None:
    self.logger = logger if logger is not None else getLogger(__name__)
    self.default_encoding = normalize_encoding(default_encoding)
    self._global_nsmap: dict[str, str] = {}
    if global_nsmap is not None:
      for prefix, uri in global_nsmap.items():
        register_namespace(self._global_nsmap, prefix, uri)

  def register_namespace(self, prefix: str, uri: str) -> None:
    register_namespace(self._global_nsmap, prefix, uri)

  def deregister_prefix(self, prefix: str) -> None:
    _deregister_prefix(self._global_nsmap, prefix)

  def deregister_uri(self, uri: str) -> None:
    _deregister_uri(self._global_nsmap, uri)

  @property
  def global_nsmap(self) -> dict[str, str]:
    return dict(self._global_nsmap)

  def iterwrite(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    elements: Iterable[E],
    *,
    encoding: str | None = None,
    root_elem: E | None = None,
    max_number_of_elements_in_buffer: int = 1000,
    write_xml_declaration: bool = False,
    doctype: str | None = None,
  ) -> None:
    """Write elements iteratively to file (streaming).

    Memory-efficient for large datasets — processes elements in batches.

    Args:
        path: Output path or file-like object.
        elements: Elements to write.
        encoding: Character encoding.
        root_elem: Root element wrapper (None means no wrapper).
        max_number_of_elements_in_buffer: Buffer size for batch writing.
        write_xml_declaration: Whether to write XML declaration.
        doctype: Optional DOCTYPE string.

    Raises:
        ValueError: If buffer size < 1.
    """
    if max_number_of_elements_in_buffer < 1:
      raise ValueError("buffer_size must be >= 1")
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    if isinstance(path, (str, PathLike)):
      str_path = fspath(path)
      if isinstance(str_path, bytes):
        str_path = str_path.decode()
      path = make_usable_path(str_path)
      ctx: BinaryIO = open(path, "wb")
    else:
      ctx = path
    buffer: list[bytes] = []

    if root_elem is not None:
      root_string = self.to_bytes(root_elem, encoding=encoding, self_closing=False)
      closing_tag = f"</{self.get_tag(root_elem, notation='local')}>".encode(encoding)

    with ctx as output:
      if write_xml_declaration:
        output.write(
          '<?xml version="1.0" encoding="'.encode(encoding)
          + encoding.encode(encoding)
          + '"?>\n'.encode(encoding)
        )
      if doctype is not None:
        output.write((doctype + "\n").encode(encoding))
      if root_elem is not None:
        output.write(root_string[: -len(closing_tag)])
      for elem in elements:
        buffer.append(self.to_bytes(elem, encoding=encoding))
        if len(buffer) == max_number_of_elements_in_buffer:
          output.write(b"".join(buffer))
          buffer.clear()
      if buffer:
        output.write(b"".join(buffer))
      if root_elem is not None:
        output.write(closing_tag)

  @abstractmethod
  def get_tag(
    self,
    element: E,
    *,
    notation: Literal["qualified", "local", "prefixed"] = "qualified",
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str: ...

  @abstractmethod
  def create_element(
    self,
    tag: str | bytes,
    attributes: Mapping[str, str] | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> E: ...

  @abstractmethod
  def append_child(self, parent: E, child: E) -> None: ...

  @overload
  def get_attribute(self, element: E, name: str | bytes) -> str | None: ...
  @overload
  def get_attribute[D](self, element: E, name: str | bytes, *, default: D) -> str | D: ...
  @abstractmethod
  def get_attribute[D](
    self, element: E, name: str | bytes, *, default: D | None = None
  ) -> str | D | None: ...

  @abstractmethod
  def set_attribute(
    self,
    element: E,
    name: str | bytes,
    value: str,
    *,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> None: ...

  @abstractmethod
  def delete_attribute(
    self, element: E, name: str | bytes, *, nsmap: MutableMapping[str, str] | None = None
  ) -> None: ...

  @abstractmethod
  def get_attribute_map(
    self,
    element: E,
    *,
    notation: Literal["qualified", "local", "prefixed"] = "qualified",
    nsmap: MutableMapping[str, str] | None = None,
  ) -> dict[str, str]: ...

  @abstractmethod
  def get_text(self, element: E) -> str | None: ...

  @abstractmethod
  def set_text(self, element: E, text: str | None) -> None: ...

  @abstractmethod
  def get_tail(self, element: E) -> str | None: ...

  @abstractmethod
  def set_tail(self, element: E, tail: str | None) -> None: ...

  @abstractmethod
  def iter_children(
    self,
    element: E,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> Generator[E]: ...

  @abstractmethod
  def parse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    encoding: str | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> E: ...
  @abstractmethod
  def from_bytes(
    self,
    data: bytes,
    encoding: str | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> E: ...
  @abstractmethod
  def from_string(
    self, data: str, *, nsmap: MutableMapping[str, str] | None = None, populate_nsmap: bool = False
  ) -> E: ...
  @abstractmethod
  def write(
    self,
    element: E,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    encoding: str | None = None,
  ) -> None: ...
  @abstractmethod
  def clear(self, element: E) -> None: ...
  @abstractmethod
  def to_bytes(
    self,
    element: E,
    encoding: str | None = None,
    *,
    self_closing: bool = False,
    strip_tail: bool = False,
  ) -> bytes: ...
  @abstractmethod
  def to_string(
    self, element: E, *, self_closing: bool = False, strip_tail: bool = False
  ) -> str: ...
  @abstractmethod
  def iterparse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> Iterator[E]: ...
