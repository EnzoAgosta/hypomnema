"""Abstract base classes for XML backend implementations.

This module defines the XmlBackend abstract base class and NamespaceHandler
for abstracting XML parser implementations. The backend abstraction allows
Hypomnema to work with different XML libraries (stdlib xml.etree, lxml, etc.)
without code changes.

All code outside this module must interact with XML elements only through
the XmlBackend interface - never access element.tag, element.attrib, etc.
directly.

Classes:
    NamespaceHandler: Manages XML namespace prefix-to-URI mappings with
        policy-driven handling of namespace conflicts and resolution.
    XmlBackend: Abstract base class defining the XML backend interface.
        Implementations must provide concrete versions of all abstract methods.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Iterator, Mapping
from contextlib import nullcontext
from io import BufferedIOBase
from logging import Logger, getLogger
from os import PathLike
from pathlib import Path
from typing import Literal, overload

from hypomnema.base.errors import (
  ExistingNamespaceError,
  InvalidPolicyActionError,
  MultiplePrefixesError,
  RestrictedPrefixError,
  RestrictedURIError,
  UnregisteredPrefixError,
  UnregisteredURIError,
)
from hypomnema.xml.policy import Behavior, NamespacePolicy, RaiseIgnore, RaiseIgnoreOverwrite
from hypomnema.xml.utils import (
  QNameLike,
  make_usable_path,
  normalize_encoding,
  validate_ncname,
  fast_validate_uri,
)


class NamespaceHandler:
  """Manages XML namespace prefix-to-URI mappings.

  Handles namespace registration, deregistration, and qualified name
  resolution with configurable policy-driven error handling.

  The "xml" prefix and "http://www.w3.org/XML/1998/namespace" URI are
  reserved per XML specification and cannot be modified.

  Args:
      nsmap: Initial namespace mappings (prefix -> URI).
      logger: Logger for namespace operations.
      policy: Policy for handling namespace errors.

  Attributes:
      nsmap: Current namespace prefix-to-URI mappings.

  Example:
      >>> handler = NamespaceHandler({"ns": "http://example.com/ns"})
      >>> handler.qualify_name("ns:tag", nsmap=handler.nsmap)
      ('ns', 'http://example.com/ns', 'tag')
  """

  def __init__(
    self,
    nsmap: Mapping[str, str] | None = None,
    logger: Logger | None = None,
    policy: NamespacePolicy | None = None,
  ) -> None:
    self.logger = logger if logger is not None else getLogger(__name__)
    self.policy = policy if policy is not None else NamespacePolicy()
    self.nsmap: dict[str, str] = {}
    for prefix, uri in (nsmap if nsmap is not None else {}).items():
      self.register_namespace(prefix, uri)

  def _log(self, behavior: Behavior, message: str, *args: object) -> None:
    """Log a message at the behavior's configured log level.

    Args:
        behavior: Behavior containing the log level.
        message: Log message format string.
        *args: Format arguments.

    Note:
        Private method used internally by handlers.
    """
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, message, *args)

  def _handle_existing_namespace(self, prefix: str, existing_uri: str, given_uri: str) -> None:
    """Handle attempt to register an already-registered prefix.

    Args:
        prefix: The namespace prefix.
        existing_uri: URI already registered for this prefix.
        given_uri: New URI being registered.

    Note:
        Private method. Behavior controlled by policy.existing_namespace.
    """
    behavior = self.policy.existing_namespace
    self._log(behavior, "prefix %r is already registered with URI %r", existing_uri, given_uri)
    match behavior.action:
      case RaiseIgnoreOverwrite.RAISE:
        raise ExistingNamespaceError(prefix, existing_uri, given_uri, self.nsmap)
      case RaiseIgnoreOverwrite.IGNORE:
        return
      case RaiseIgnoreOverwrite.OVERWRITE:
        self._log(
          behavior,
          "Overwriting existing uri %r for prefix %r with URI %r",
          existing_uri,
          prefix,
          given_uri,
        )
        validate_ncname(prefix)
        fast_validate_uri(given_uri)
        self.nsmap[prefix] = given_uri
      case _:
        raise InvalidPolicyActionError("existing_namespace", behavior.action, RaiseIgnoreOverwrite)

  def _handle_inexistent_prefix(self, prefix: str) -> None:
    """Handle resolution of an unregistered prefix.

    Args:
        prefix: The unregistered prefix.

    Note:
        Private method. Behavior controlled by policy.inexistent_namespace.
    """
    behavior = self.policy.inexistent_namespace
    self._log(behavior, "prefix %r is not registered in nsmap %r", prefix, self.nsmap)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise UnregisteredPrefixError(prefix, self.nsmap)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("inexistent_namespace", behavior.action, RaiseIgnore)

  def _handle_inexistent_uri(self, uri: str) -> None:
    """Handle resolution of an unregistered URI.

    Args:
        uri: The unregistered URI.

    Note:
        Private method. Behavior controlled by policy.inexistent_namespace.
    """
    behavior = self.policy.inexistent_namespace
    self._log(behavior, "uri %r is not registered in nsmap %r", uri, self.nsmap)
    match behavior.action:
      case RaiseIgnore.RAISE:
        raise UnregisteredURIError(uri, self.nsmap)
      case RaiseIgnore.IGNORE:
        return
      case _:
        raise InvalidPolicyActionError("inexistent_namespace", behavior.action, RaiseIgnore)

  def register_namespace(self, prefix: str, uri: str) -> None:
    """Register a namespace prefix-to-URI mapping.

    Args:
        prefix: Namespace prefix.
        uri: Namespace URI.

    Raises:
        RestrictedPrefixError: If prefix is "xml".
        RestrictedURIError: If uri is the XML namespace.
        ExistingNamespaceError: If prefix already registered and policy raises.
        InvalidNCNameError: If prefix is not a valid NCName.
        InvalidURIError: If uri is not a valid URI.
    """
    if not prefix or not uri:
      raise ValueError("prefix and uri cannot be empty")
    if prefix == "xml":
      raise RestrictedPrefixError(prefix)
    if uri == "http://www.w3.org/XML/1998/namespace":
      raise RestrictedURIError(uri)
    if prefix in self.nsmap:
      self._handle_existing_namespace(prefix, self.nsmap[prefix], uri)
      return
    validate_ncname(prefix)
    fast_validate_uri(uri)
    self.nsmap[prefix] = uri

  def deregister_prefix(self, prefix: str) -> None:
    """Remove a namespace prefix mapping.

    Args:
        prefix: Prefix to deregister.

    Raises:
        RestrictedPrefixError: If prefix is "xml".
    """
    if not prefix:
      raise ValueError("prefix cannot be empty")
    if prefix == "xml":
      raise RestrictedPrefixError(prefix)
    if prefix not in self.nsmap:
      self._handle_inexistent_prefix(prefix)
      return
    del self.nsmap[prefix]

  def qualify_name(
    self, tag: str | QNameLike, nsmap: Mapping[str, str]
  ) -> tuple[str | None, str | None, str]:
    """Parse and validate a qualified name.

    Handles Clark notation ({uri}local), prefixed names (prefix:local),
    and simple local names.

    Args:
        tag: Tag name to parse.
        nsmap: Namespace prefix mappings for resolution.

    Returns:
        Tuple of (prefix, uri, localname). prefix/uri may be None for unprefixed names.

    Raises:
        ValueError: If tag is empty or malformed.
        MultiplePrefixesError: If tag contains multiple colons.
    """
    if isinstance(tag, QNameLike):
      _tag = tag.text
    else:
      _tag = tag
    if not _tag:
      raise ValueError("Tag cannot be empty")

    if _tag[0] == "{":
      if "}" not in _tag[1:]:
        raise ValueError(f"Malformed Clark notation: missing }} in {_tag!r}")
      uri, localname = _tag[1:].split("}", 1)
      fast_validate_uri(uri)
      validate_ncname(localname)
      reverse_map = {v: k for k, v in nsmap.items()}
      if uri not in reverse_map:
        self._handle_inexistent_uri(uri)
        return None, uri, localname
      return reverse_map[uri], uri, localname

    match _tag.split(":"):
      case [prefix, localname]:
        if prefix not in nsmap:
          self._handle_inexistent_prefix(prefix)
          return prefix, None, localname
        uri = nsmap[prefix]
        validate_ncname(localname)
        fast_validate_uri(uri)
        return prefix, uri, localname
      case [localname]:
        validate_ncname(localname)
        return None, None, localname
      case _:
        raise MultiplePrefixesError(_tag)


type TagLike = str | QNameLike | bytearray | bytes


class XmlBackend[TypeOfBackendElement](ABC):
  """Abstract base class for XML backend implementations.

  Defines the interface that all XML backends must implement. This abstraction
  allows Hypomnema to work with different XML libraries without code changes.

  Backend implementations must provide concrete versions of all abstract
  methods. Code outside the backends module should never access XML element
  attributes directly - always use these backend methods.

  Args:
      logger: Logger for backend operations.
      default_encoding: Default character encoding.
      namespace_handler: Handler for namespace operations.

  Attributes:
      logger: Logger instance.
      default_encoding: Default encoding name.
      nsmap: Namespace prefix mappings (read-only property).

  Note:
      The generic type parameter TypeOfBackendElement represents the underlying
      XML element type (e.g., xml.etree.ElementTree.Element for StandardBackend).
  """

  __slots__ = ("_namespace_handler", "logger", "default_encoding", "policy")
  _namespace_handler: NamespaceHandler
  logger: Logger
  default_encoding: str

  def __init__(
    self,
    logger: Logger | None = None,
    default_encoding: str | None = None,
    *,
    namespace_handler: NamespaceHandler | None = None,
  ) -> None:
    self.logger = logger if logger is not None else getLogger(__name__)
    self.default_encoding = normalize_encoding(default_encoding)
    self._namespace_handler = (
      namespace_handler if namespace_handler is not None else NamespaceHandler()
    )

  def prep_tag_set(self, to_prep: TagLike | Iterable[TagLike]) -> set[str] | None:
    """Flatten and normalize tag filters to a set.

    Args:
        to_prep: Tags to prepare. Can be nested iterables.

    Returns:
        Set of normalized tag names, or None if empty.
    """
    result: set[str] = set()

    def _flatten(x: TagLike | Iterable[TagLike | Iterable]) -> None:
      if isinstance(x, (str, bytes, bytearray, QNameLike)):
        x = self.normalize_tag_name(x)
        result.add(x)
      else:
        for item in x:
          _flatten(item)

    _flatten(to_prep)
    return result

  def normalize_tag_name(self, tag: TagLike) -> str:
    """Convert tag to normalized string form.

    Args:
        tag: Tag to normalize (str, bytes, QNameLike, etc.).

    Returns:
        Normalized tag string.

    Raises:
        TypeError: If tag type is not supported.
    """
    match tag:
      case QNameLike():
        return tag.text
      case bytearray() | bytes():
        return tag.decode(self.default_encoding)
      case str():
        return tag
      case _:
        raise TypeError(f"Unexpected tag type: {type(tag)}")

  def _log(self, behavior: Behavior, message: str, *args: object) -> None:
    """Log a message at the behavior's configured log level.

    Args:
        behavior: Behavior containing the log level.
        message: Log message format string.
        *args: Format arguments.

    Note:
        Private method used internally.
    """
    if behavior.log_level is not None:
      self.logger.log(behavior.log_level, message, *args)

  def register_namespace(self, prefix: str, uri: str) -> None:
    """Register a namespace through the namespace handler.

    Args:
        prefix: Namespace prefix.
        uri: Namespace URI.
    """
    self._namespace_handler.register_namespace(prefix, uri)

  def deregister_prefix(self, prefix: str) -> None:
    """Deregister a namespace prefix.

    Args:
        prefix: Prefix to deregister.
    """
    self._namespace_handler.deregister_prefix(prefix)

  @property
  def nsmap(self) -> dict[str, str]:
    """Current namespace prefix mappings."""
    return {k: v for k, v in self._namespace_handler.nsmap.items()}

  @abstractmethod
  def get_tag(
    self,
    element: TypeOfBackendElement,
    notation: Literal["prefixed", "qualified", "local"] = "local",
  ) -> str:
    """Get element tag name.

    Args:
        element: XML element.
        notation: Name format: prefixed (prefix:local), qualified ({uri}local),
            or local (just localname).

    Returns:
        Tag name in requested format.
    """
    ...

  @abstractmethod
  def create_element(
    self, tag: str, attributes: Mapping[str, str] | None = None
  ) -> TypeOfBackendElement:
    """Create a new XML element.

    Args:
        tag: Element tag name.
        attributes: Element attributes.

    Returns:
        New XML element.
    """
    ...

  @abstractmethod
  def append_child(self, parent: TypeOfBackendElement, child: TypeOfBackendElement) -> None:
    """Append child element to parent.

    Args:
        parent: Parent element.
        child: Child element to append.
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
    """Get attribute value from element.

    Args:
        element: XML element.
        attribute_name: Attribute name.
        default: Default value if attribute not present.

    Returns:
        Attribute value or default.
    """
    ...

  @abstractmethod
  def set_attribute(
    self, element: TypeOfBackendElement, attribute_name: str | QNameLike, attribute_value: str
  ) -> None:
    """Set attribute value on element.

    Args:
        element: XML element.
        attribute_name: Attribute name.
        attribute_value: Attribute value.
    """
    ...

  @abstractmethod
  def delete_attribute(
    self, element: TypeOfBackendElement, attribute_name: str | QNameLike
  ) -> None:
    """Delete attribute from element.

    Args:
        element: XML element.
        attribute_name: Attribute name.
    """
    ...

  @abstractmethod
  def get_attribute_map(self, element: TypeOfBackendElement) -> dict[str, str]:
    """Get all attributes as a dictionary.

    Args:
        element: XML element.

    Returns:
        Mapping of attribute names to values.
    """
    ...

  @abstractmethod
  def get_text(self, element: TypeOfBackendElement) -> str | None:
    """Get text content of element.

    Args:
        element: XML element.

    Returns:
        Text content or None.
    """
    ...

  @abstractmethod
  def set_text(self, element: TypeOfBackendElement, text: str | None) -> None:
    """Set text content of element.

    Args:
        element: XML element.
        text: Text content.
    """
    ...

  @abstractmethod
  def get_tail(self, element: TypeOfBackendElement) -> str | None:
    """Get tail text (text following element).

    Args:
        element: XML element.

    Returns:
        Tail text or None.
    """
    ...

  @abstractmethod
  def set_tail(self, element: TypeOfBackendElement, tail: str | None) -> None:
    """Set tail text.

    Args:
        element: XML element.
        tail: Tail text.
    """
    ...

  @abstractmethod
  def iter_children(
    self,
    element: TypeOfBackendElement,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[TypeOfBackendElement]:
    """Iterate over child elements.

    Args:
        element: Parent element.
        tag_filter: Optional tag filter for child elements.

    Yields:
        Child elements matching filter.
    """
    ...

  @abstractmethod
  def parse(self, path: str | PathLike, encoding: str | None = None) -> TypeOfBackendElement:
    """Parse XML file and return root element.

    Args:
        path: Path to XML file.
        encoding: Character encoding.

    Returns:
        Root element of parsed document.
    """
    ...

  @abstractmethod
  def write(
    self, element: TypeOfBackendElement, path: str | PathLike, encoding: str | None = None
  ) -> None:
    """Write XML element to file.

    Args:
        element: Root element to write.
        path: Output file path.
        encoding: Character encoding.
    """
    ...

  @abstractmethod
  def clear(self, element: TypeOfBackendElement) -> None:
    """Clear element to free memory.

    Args:
        element: Element to clear.
    """
    ...

  @abstractmethod
  def to_bytes(
    self, element: TypeOfBackendElement, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    """Serialize element to bytes.

    Args:
        element: Element to serialize.
        encoding: Character encoding.
        self_closing: Whether to use self-closing tags.

    Returns:
        Serialized XML bytes.
    """
    ...

  @abstractmethod
  def iterparse(
    self,
    path: str | PathLike,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Iterator[TypeOfBackendElement]:
    """Iteratively parse XML file yielding matching elements.

    Memory-efficient for large files - elements are cleared after yield.

    Args:
        path: Path to XML file.
        tag_filter: Tags to yield.

    Yields:
        Elements matching filter.
    """
    ...

  def _iterparse(
    self,
    ctx: Iterator[tuple[Literal["start", "end"], TypeOfBackendElement]],
    tag_filter: set[str] | None,
  ) -> Generator[TypeOfBackendElement]:
    """Internal helper for implementing iterparse.

    Processes start/end events from XML parser and yields complete elements.

    Args:
        ctx: Iterator yielding (event, element) tuples.
        tag_filter: Set of tag names to filter for, or None for all.

    Yields:
        Complete elements matching filter.

    Note:
        Private method for use by backend implementations. Manages element
        lifecycle for streaming parsing.
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
    """Write elements iteratively to file (streaming).

    Memory-efficient for large datasets - processes elements in batches.

    Args:
        path: Output path or file-like object.
        elements: Elements to write.
        encoding: Character encoding.
        root_elem: Root element wrapper (default: <tmx version="1.4"/>).
        max_number_of_elements_in_buffer: Buffer size for batch writing (default: 1000).
        write_xml_declaration: Whether to write XML declaration.
        write_doctype: Whether to write DOCTYPE.

    Raises:
        ValueError: If buffer size < 1 or root element formatting is invalid.
    """
    if max_number_of_elements_in_buffer < 1:
      raise ValueError("buffer_size must be >= 1")
    if isinstance(path, (str, PathLike)):
      path = make_usable_path(path)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    if root_elem is None:
      root_elem = self.create_element("tmx", attributes={"version": "1.4"})

    root_string = self.to_bytes(root_elem, encoding, self_closing=False)
    closing_tag = f"</{self.get_tag(root_elem)}>".encode(encoding)
    if not root_string.endswith(closing_tag):
      raise ValueError(
        "to_bytes() implementation returned an incorrectly formatted root element."
        f"Expected string to end with {closing_tag!r}, got {root_string[-len(closing_tag) :]!r}"
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
      output.write(root_string[: -len(closing_tag)])
      for elem in elements:
        buffer.append(self.to_bytes(elem, encoding))
        if len(buffer) == max_number_of_elements_in_buffer:
          output.write(b"".join(buffer))
          buffer.clear()
      if buffer:
        output.write(b"".join(buffer))
      output.write(root_string[-len(closing_tag) :])
