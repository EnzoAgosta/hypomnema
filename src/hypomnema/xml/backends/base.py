from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Iterator, Mapping
from contextlib import nullcontext
from io import BufferedIOBase
from logging import DEBUG, Logger, getLogger
from os import PathLike
from pathlib import Path
from typing import Literal, overload

from hypomnema.base.errors import NamespaceError
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.utils import (is_ncname, is_valid_uri, make_usable_path,
                                 normalize_encoding)

__all__ = ["XmlBackend"]


class XmlBackend[TypeOfBackendElement](ABC):
  """Abstract base class for XML backend implementations.

  Provides a unified interface for XML operations across different
  XML libraries (e.g., stdlib xml.etree, lxml). Subclasses must
  implement all abstract methods.

  Parameters
  ----------
  nsmap : Mapping[str, str] | None
      Custom namespace prefix to URI mappings to register.
  logger : Logger | None
      Logger instance for debug and error messages.
  default_encoding : str | None
      Default encoding for XML operations. Defaults to "utf-8".
  policy : XmlPolicy | None
      Policy configuration for error handling behavior.

  Attributes
  ----------
  nsmap : dict[str | None, str]
      Read-only mapping of namespace prefixes to URIs.
      Use register_namespace() and deregister_namespace() to modify.
  logger : Logger
      Logger instance for debug and error messages.
  default_encoding : str
      Default encoding for XML operations.
  policy : XmlPolicy
      Policy configuration for error handling.

  Examples
  --------
  .. code-block:: python

      from hypomnema.xml.backends.standard import StandardBackend

      backend = StandardBackend(default_encoding="utf-8")
      elem = backend.create_element("tmx", attributes={"version": "1.4"})
      backend.set_text(elem, "Hello World")
  """

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
    """Initialize the XML backend.

    Sets up default namespace mappings (xml and TMX namespaces),
    configures encoding, and registers any custom namespaces.

    Parameters
    ----------
    nsmap : Mapping[str, str] | None
        Custom namespace prefix to URI mappings.
    logger : Logger | None
        Logger instance. Creates default logger if None.
    default_encoding : str | None
        Default encoding for XML operations.
    policy : XmlPolicy | None
        Policy for error handling behavior.
    """
    self.logger = logger if logger is not None else getLogger("XmlBackendLogger")
    self._nsmap = {"xml": "http://www.w3.org/XML/1998/namespace", None: "http://www.lisa.org/tmx14"}
    self.default_encoding = (
      normalize_encoding(default_encoding) if default_encoding is not None else "utf-8"
    )
    self.logger.log(DEBUG, "Initialized with default encoding %s", self.default_encoding)
    self.policy = policy if policy is not None else XmlPolicy()
    if nsmap is not None:
      for prefix, uri in nsmap.items():
        self.register_namespace(prefix, uri)

  def register_namespace(self, prefix: str, uri: str) -> None:
    """Register a namespace prefix to URI mapping.

    Parameters
    ----------
    prefix : str
        Namespace prefix to register.
    uri : str
        URI associated with the prefix.

    Raises
    ------
    NamespaceError
        If prefix or URI is reserved, invalid, or already registered
        (depending on policy configuration).

    Examples
    --------
    .. code-block:: python

        backend.register_namespace("xhtml", "http://www.w3.org/1999/xhtml")
    """
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
        self.logger.log(DEBUG, "Overwrote namespace: %s -> %s", prefix, uri)
        return
      else:
        return
    self._nsmap[prefix] = uri
    self.logger.log(DEBUG, "Registered namespace: %s -> %s", prefix, uri)

  def deregister_namespace(self, prefix: str) -> None:
    """Remove a namespace prefix registration.

    Parameters
    ----------
    prefix : str
        Namespace prefix to deregister.

    Raises
    ------
    NamespaceError
        If prefix is reserved or not registered (depending on policy).

    Examples
    --------
    .. code-block:: python

        backend.deregister_namespace("custom")
    """
    if prefix in ("xml", None):
      raise NamespaceError(f"{prefix} is reserved and cannot be deregistered")
    if prefix in self._nsmap:
      del self._nsmap[prefix]
      self.logger.log(DEBUG, "Deregistered namespace: %s", prefix)
    else:
      self.logger.log(
        self.policy.missing_namespace.log_level, "Namespace %s is not registered", prefix
      )
      if self.policy.missing_namespace.behavior == "ignore":
        return
      raise NamespaceError(f"{prefix} is not registered and cannot be deregistered")

  @property
  def nsmap(self) -> dict[str | None, str]:
    """Shallow copy of the internal namespace map."""
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
  def get_tag(self, element: TypeOfBackendElement, *, as_qname: Literal[True]) -> QName: ...
  @overload
  def get_tag(self, element: TypeOfBackendElement, *, as_qname: Literal[False] = False) -> str: ...
  @abstractmethod
  def get_tag(self, element: TypeOfBackendElement, *, as_qname: bool = False) -> str | QName:
    """Get the tag name of an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.
    as_qname : bool
        If True, return QName object. If False, return string.

    Returns
    -------
    str | QName
        The tag name of the element.
    """
    ...

  @abstractmethod
  def create_element(
    self, tag: str, attributes: Mapping[str, str] | None = None
  ) -> TypeOfBackendElement:
    """Create a new XML element.

    Parameters
    ----------
    tag : str
        Tag name for the element.
    attributes : Mapping[str, str] | None
        Optional attribute name-value pairs.

    Returns
    -------
    TypeOfBackendElement
        The created element.
    """
    ...

  @abstractmethod
  def append_child(self, parent: TypeOfBackendElement, child: TypeOfBackendElement) -> None:
    """Append a child element to a parent.

    Parameters
    ----------
    parent : TypeOfBackendElement
        Parent element.
    child : TypeOfBackendElement
        Child element to append.
    """
    ...

  @overload
  def get_attribute(self, element: TypeOfBackendElement, attribute_name: str) -> str | None: ...
  @overload
  def get_attribute[TypeOfDefault](
    self, element: TypeOfBackendElement, attribute_name: str, *, default: TypeOfDefault
  ) -> str | TypeOfDefault: ...
  @abstractmethod
  def get_attribute[TypeOfDefault](
    self,
    element: TypeOfBackendElement,
    attribute_name: str,
    *,
    default: TypeOfDefault | None = None,
  ) -> str | TypeOfDefault | None:
    """Get an attribute value from an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.
    attribute_name : str
        Name of the attribute.
    default : TypeOfDefault | None
        Default value if attribute is not present.

    Returns
    -------
    str | TypeOfDefault | None
        The attribute value, or default if not found.
    """
    ...

  @abstractmethod
  def set_attribute(
    self, element: TypeOfBackendElement, attribute_name: str | QNameLike, attribute_value: str
  ) -> None:
    """Set an attribute on an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.
    attribute_name : str | QNameLike
        Name of the attribute (can be QName for namespaced attributes).
    attribute_value : str
        Value to set.
    """
    ...

  @abstractmethod
  def delete_attribute(
    self, element: TypeOfBackendElement, attribute_name: str | QNameLike
  ) -> None:
    """Delete an attribute from an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.
    attribute_name : str | QNameLike
        Name of the attribute to delete.
    """
    ...

  @abstractmethod
  def get_attribute_map(self, element: TypeOfBackendElement) -> dict[str, str]:
    """Get all attributes of an element as a dictionary.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.

    Returns
    -------
    dict[str, str]
        Mapping of attribute names to values.
    """
    ...

  @abstractmethod
  def get_text(self, element: TypeOfBackendElement) -> str | None:
    """Get text content of an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.

    Returns
    -------
    str | None
        Text content, or None if empty.
    """
    ...

  @abstractmethod
  def set_text(self, element: TypeOfBackendElement, text: str | None) -> None:
    """Set text content of an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.
    text : str | None
        Text content to set.
    """
    ...

  @abstractmethod
  def get_tail(self, element: TypeOfBackendElement) -> str | None:
    """Get tail text (text after element's closing tag).

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.

    Returns
    -------
    str | None
        Tail text, or None if empty.
    """
    ...

  @abstractmethod
  def set_tail(self, element: TypeOfBackendElement, tail: str | None) -> None:
    """Set tail text of an element.

    Parameters
    ----------
    element : TypeOfBackendElement
        The XML element.
    tail : str | None
        Tail text to set.
    """
    ...

  @abstractmethod
  def iter_children(
    self,
    element: TypeOfBackendElement,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Iterator[TypeOfBackendElement]:
    """Iterate over child elements.

    Parameters
    ----------
    element : TypeOfBackendElement
        Parent element.
    tag_filter : str | QNameLike | Iterable[str | QNameLike] | None
        Optional tag filter(s) to match.

    Returns
    -------
    Iterator[TypeOfBackendElement]
        Iterator over matching child elements.
    """
    ...

  @abstractmethod
  def parse(self, path: str | PathLike, encoding: str | None = None) -> TypeOfBackendElement:
    """Parse an XML file and return the root element.

    Parameters
    ----------
    path : str | PathLike
        Path to the XML file.
    encoding : str | None
        Optional encoding override.

    Returns
    -------
    TypeOfBackendElement
        Root element of the parsed document.
    """
    ...

  @abstractmethod
  def write(
    self, element: TypeOfBackendElement, path: str | PathLike, encoding: str | None = None
  ) -> None:
    """Write an element to a file.

    Parameters
    ----------
    element : TypeOfBackendElement
        Root element to write.
    path : str | PathLike
        Path to write the file.
    encoding : str | None
        Optional encoding override.
    """
    ...

  @abstractmethod
  def clear(self, element: TypeOfBackendElement) -> None:
    """Clear element content and free memory.

    Parameters
    ----------
    element : TypeOfBackendElement
        Element to clear.
    """
    ...

  @abstractmethod
  def to_bytes(
    self, element: TypeOfBackendElement, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    """Serialize an element to bytes.

    Parameters
    ----------
    element : TypeOfBackendElement
        Element to serialize.
    encoding : str | None
        Optional encoding override.
    self_closing : bool
        If True, output as self-closing tag if empty.

    Returns
    -------
    bytes
        Serialized XML as bytes.
    """
    ...

  @abstractmethod
  def iterparse(
    self,
    path: str | PathLike,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Iterator[TypeOfBackendElement]:
    """Parse XML incrementally, yielding matching elements.

    Parameters
    ----------
    path : str | PathLike
        Path to the XML file.
    tag_filter : str | QNameLike | Iterable[str | QNameLike] | None
        Tag(s) to match and yield.

    Returns
    -------
    Iterator[TypeOfBackendElement]
        Iterator over matching elements.

    Examples
    --------
    .. code-block:: python

        for tu in backend.iterparse("large.tmx", "tu"):
          process(tu)
    """
    ...

  def _iterparse(
    self,
    ctx: Iterator[tuple[Literal["start", "end"], TypeOfBackendElement]],
    tag_filter: set[str] | None,
  ) -> Generator[TypeOfBackendElement]:
    """Internal helper for incremental parsing.

    Processes start/end events from the underlying XML parser
    and yields elements matching the tag filter.

    Parameters
    ----------
    ctx : Iterator[tuple[Literal["start", "end"], TypeOfBackendElement]]
        Iterator yielding (event, element) tuples.
    tag_filter : set[str] | None
        Set of tag names to match.

    Yields
    ------
    TypeOfBackendElement
        Elements matching the filter.

    Notes
    -----
    This is an internal method used by concrete backend implementations.
    Clears elements from memory after yielding to reduce memory usage.
    """
    elements_pending_yield: list[TypeOfBackendElement] = []

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
    elements: Iterable[TypeOfBackendElement],
    encoding: str | None = None,
    *,
    root_elem: TypeOfBackendElement | None = None,
    max_number_of_elements_in_buffer: int = 1000,
    write_xml_declaration: bool = False,
    write_doctype: bool = False,
  ) -> None:
    """Write elements incrementally to a file.

    Efficiently writes large XML files by buffering elements
    and writing them in batches. Creates a root element wrapper
    and inserts serialized elements into it.

    Parameters
    ----------
    path : str | PathLike | BufferedIOBase
        Path or file handle to write to.
    elements : Iterable[TypeOfBackendElement]
        Elements to serialize and write.
    encoding : str | None
        Optional encoding override. Defaults to backend encoding.
    root_elem : TypeOfBackendElement | None
        Root element wrapper. Creates a <tmx version="1.4"> if None.
    max_number_of_elements_in_buffer : int
        Number of elements to buffer before writing. Default 1000.
    write_xml_declaration : bool
        If True, write XML declaration at start.
    write_doctype : bool
        If True, write DOCTYPE declaration.

    Raises
    ------
    ValueError
        If buffer size is less than 1.

    Examples
    --------
    .. code-block:: python

        backend.iterwrite(
          "output.tmx",
          elements,
          root_elem=backend.create_element("tmx", {"version": "1.4"}),
          write_xml_declaration=True,
        )
    """
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
        output.write(
          '<?xml version="1.0" encoding="'.encode(encoding)
          + encoding.encode(encoding)
          + '"?>\n'.encode(encoding)
        )
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
