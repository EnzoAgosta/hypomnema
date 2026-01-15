from typing import overload, Literal
from logging import Logger, getLogger
from contextlib import nullcontext
from pathlib import Path
from io import BufferedIOBase
from hypomnema.xml.utils import make_usable_path, normalize_encoding, is_ncname, QName
from abc import ABC, abstractmethod
from collections.abc import Collection, Iterator, Generator, Iterable, Mapping, MutableMapping
from os import PathLike

__all__ = ["XmlBackend"]


class XmlBackend[TypeOfElement](ABC):
  """Abstract base class for XML document manipulation backends.

  This class defines the interface for creating, reading, modifying, and writing
  XML elements. Concrete implementations provide backend-specific logic using
  different XML libraries (e.g., stdlib ElementTree, lxml).

  All implementations handle namespace resolution consistently, supporting
  both Clark notation ``{uri}localname`` and prefixed notation ``prefix:localname``.

  Attributes
  ----------
  logger : Logger
      Logger instance for diagnostic messages. Defaults to ``"XmlBackendLogger"``.

  """

  __slots__ = ("_global_nsmap", "logger")
  _global_nsmap: MutableMapping[str | None, str]
  logger: Logger

  def __init__(
    self, nsmap: Mapping[str | None, str] | None = None, *, logger: Logger | None = None
  ) -> None:
    """Initialize the backend with an optional namespace map.

    Parameters
    ----------
    nsmap : Mapping[str | None, str] | None, optional
        Initial namespace mappings from prefix to URI. Each prefix will be
        registered via ``register_namespace``.
    logger : Logger | None, optional
        Custom logger instance. If not provided, a default logger named
        ``"XmlBackendLogger"`` is used.

    """
    self.logger = logger if logger is not None else getLogger("XmlBackendLogger")
    self._global_nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}
    if nsmap is not None:
      for prefix, uri in nsmap.items():
        self.register_namespace(prefix, uri)

  @overload
  @abstractmethod
  def get_tag(
    self,
    element: TypeOfElement,
    *,
    as_qname: Literal[True],
    nsmap: Mapping[str | None, str] | None = None,
  ) -> QName: ...
  @overload
  @abstractmethod
  def get_tag(
    self,
    element: TypeOfElement,
    *,
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str: ...
  @abstractmethod
  def get_tag(
    self,
    element: TypeOfElement,
    *,
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | QName:
    """Return the tag name of an element.

    Parameters
    ----------
    element : T_Element
        The element whose tag to retrieve.
    as_qname : bool, optional
        If True, return a ``QName`` object containing namespace information.
        If False (default), return the fully qualified tag name as a string
        (e.g., ``{http://example.com}element``).
    nsmap : Mapping[str | None, str] | None, optional
        Namespace map to use for resolving prefixes. If not provided,
        uses the element's intrinsic namespace map if available or the
        backend's global namespace map if not.

    Returns
    -------
    str | QName
        The tag name, either as a string or ``QName`` object depending on
        ``as_qname``.

    """
    ...

  @abstractmethod
  def create_element[TagType, KeyType, ValueType](
    self,
    tag: TagType,
    attributes: Mapping[KeyType, ValueType] | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> TypeOfElement:
    """Create a new element with the given tag and attributes.

    Parameters
    ----------
    tag : str | QName
        The tag name for the new element. Can be a plain local name,
        a prefixed name (``prefix:localname``), or a Clark-notation name
        (``{uri}localname``). If a ``QName`` is provided, its namespace
        information is used directly.
    attributes : TAttributes | None, optional
        A mapping of attribute names to values. Attribute names follow the
        same resolution rules as tags.
    nsmap : Mapping[str | None, str] | None, optional
        Namespace map to use for resolving the tag and any prefixed attributes.
        If not provided, uses the element's intrinsic namespace map if available
        or the backend's global namespace map if not.

    Returns
    -------
    T_Element
        A newly created element with the specified tag and attributes.

    Notes
    -----
    The created element is not attached to any parent. Use ``append_child``
    to add it to an existing element tree.

    """
    ...

  @abstractmethod
  def append_child(self, parent: TypeOfElement, child: TypeOfElement) -> None:
    """Attach a child element to a parent element.

    Parameters
    ----------
    parent : T_Element
        The parent element to which the child will be attached.
    child : T_Element
        The child element to attach. The child becomes a direct child
        of the parent and is removed from its previous location if any.

    Raises
    ------
    TypeError
        If either ``parent`` or ``child`` is not a valid element type
        for this backend.

    """
    ...

  @abstractmethod
  def get_attribute[TypeOfDefault](
    self,
    element: TypeOfElement,
    attribute_name: str,
    default: TypeOfDefault | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | TypeOfDefault | None:
    """Retrieve the value of an attribute.

    Parameters
    ----------
    element : T_Element
        The element from which to retrieve the attribute.
    attribute_name : T_AttributeKey
        The name of the attribute. Can be a local name, prefixed name,
        or Clark-notation name.
    default : T_AttributeValue | None, optional
        Value to return if the attribute does not exist. Defaults to None.
    nsmap : Mapping[str | None, str] | None, optional
        Namespace map to use for resolving prefixed attribute names.
        If not provided, uses the element's intrinsic namespace map.

    Returns
    -------
    T_AttributeValue
        The attribute value if found, otherwise ``default``.

    """
    ...

  @abstractmethod
  def set_attribute(
    self,
    element: TypeOfElement,
    attribute_name: str,
    attribute_value: str | None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
    unsafe: bool = False,
  ) -> None:
    """Set or remove an attribute on an element.

    Parameters
    ----------
    element : T_Element
        The element on which to set the attribute.
    attribute_name : T_AttributeKey
        The name of the attribute. Can be a local name, prefixed name,
        or Clark-notation name.
    attribute_value : T_AttributeValue | None
        The value to set. If None, the attribute is removed if it exists.
    nsmap : Mapping[str | None, str] | None, optional
        Namespace map to use for resolving prefixed attribute names.
        If not provided, uses the element's intrinsic namespace map
        if available or the backend's global namespace map if not.

    Notes
    -----
    If the attribute already exists, its value is replaced. If ``attribute_value``
    is None, the attribute is removed entirely in the defaults backend implementation
    as it is not possible to have a None value for an attribute in XML.

    """
    ...

  @abstractmethod
  def get_attribute_map(self, element: TypeOfElement) -> dict[str, str]:
    """Return all attributes of an element as a mapping.

    Parameters
    ----------
    element : T_Element
        The element whose attributes to retrieve.

    Returns
    -------
    TAttributes
        A mapping of attribute names to values. The returned mapping is
        typically a live view of the element's attributes, but this
        depends on the backend implementation.

    """
    ...

  @abstractmethod
  def get_text(self, element: TypeOfElement) -> str | None:
    """Return the text content of an element.

    Parameters
    ----------
    element : T_Element
        The element whose text to retrieve.

    Returns
    -------
    str | None
        The text content between the element's opening tag and its first
        child element, or None if no text exists.

    Notes
    -----
    This retrieves only the text before the first child element. To get
    text after child elements, use ``get_tail``.

    See Also
    --------
    set_text : Set the text content of an element.
    get_tail : Get trailing text after an element.

    """
    ...

  @abstractmethod
  def set_text(self, element: TypeOfElement, text: str | None) -> None:
    """Set the text content of an element.

    Parameters
    ----------
    element : T_Element
        The element whose text to set.
    text : str | None
        The text content to set. If None, any existing text is removed.

    Notes
    -----
    This sets only the text before the first child element. To set
    text after an element, use ``set_tail``.

    See Also
    --------
    get_text : Get the text content of an element.
    set_tail : Set trailing text after an element.

    """
    ...

  @abstractmethod
  def get_tail(self, element: TypeOfElement) -> str | None:
    """Return the trailing text of an element.

    Parameters
    ----------
    element : T_Element
        The element whose tail text to retrieve.

    Returns
    -------
    str | None
        The text appearing after the element's closing tag and before
        the next sibling element's opening tag, or None if no tail exists.

    See Also
    --------
    set_tail : Set trailing text after an element.
    get_text : Get text content before child elements.

    """
    ...

  @abstractmethod
  def set_tail(self, element: TypeOfElement, tail: str | None) -> None:
    """Set the trailing text of an element.

    Parameters
    ----------
    element : T_Element
        The element whose tail text to set.
    tail : str | None
        The tail text to set. If None, any existing tail is removed.

    See Also
    --------
    get_tail : Get trailing text after an element.
    set_text : Set text content before child elements.

    """
    ...

  @abstractmethod
  def iter_children(
    self,
    element: TypeOfElement,
    tag_filter: str | QName | Collection[str | QName] | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> Iterator[TypeOfElement]:
    """Iterate over direct child elements.

    Parameters
    ----------
    element : T_Element
        The element whose children to iterate.
    tag_filter : str | Collection[str] | None, optional
        If provided, only yield children with matching tags. Supports
        a single tag string or a collection of tags for multiple matches.
        Tag names follow the same resolution rules as ``get_tag``.
    nsmap : Mapping[str, str] | None, optional
        Namespace map to use for resolving prefixed tag names in the filter.
        If not provided, uses the element's intrinsic namespace map if available
        or the backend's global namespace map if not.

    Yields
    ------
    T_Element
        Each direct child element matching the filter.

    Notes
    -----
    This method only yields direct (immediate) children, not nested descendants.
    Use recursive iteration or multiple calls to traverse deeper levels.
    If the tag filter is None, all elements are yielded.

    """
    ...

  @abstractmethod
  def parse(self, path: str | bytes | PathLike, encoding: str = "utf-8") -> TypeOfElement:
    """Parse an XML file and return the root element.

    Parameters
    ----------
    path : str | bytes | PathLike
        The path to the XML file to parse. Can be a string, bytes path,
        or PathLike object.
    encoding : str, optional
        The encoding to use when reading the file. Defaults to ``"utf-8"``.

    Returns
    -------
    T_Element
        The root element of the parsed XML document.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the file is not valid XML.
    TypeError
        If ``path`` is not a valid path type.

    """
    ...

  @abstractmethod
  def write(
    self, element: TypeOfElement, path: str | bytes | PathLike, encoding: str = "utf-8"
  ) -> None:
    """Write an element tree to an XML file.

    Parameters
    ----------
    element : T_Element
        The root element to write.
    path : str | bytes | PathLike
        The destination path for the XML file.
    encoding : str, optional
        The encoding to use when writing the file. Defaults to ``"utf-8"``.

    Raises
    ------
    TypeError
        If ``element`` is not a valid element type for this backend.
    OSError
        If the file cannot be written (e.g., permission denied, invalid path).

    Notes
    -----
    The implementation determines whether an XML declaration is written.
    Some backends may include additional headers or formatting.

    """
    ...

  @abstractmethod
  def clear(self, element: TypeOfElement) -> None:
    """Clear an element's text, attributes, tail and children.

    Parameters
    ----------
    element : T_Element
        The element to clear.

    Notes
    -----
    This method removes all child elements and resets attributes.
    The element itself remains in place.

    """
    ...

  @abstractmethod
  def to_bytes(
    self, element: TypeOfElement, encoding: str = "utf-8", self_closing: bool = False
  ) -> bytes:
    """Convert an element to its XML byte representation.

    Parameters
    ----------
    element : T_Element
        The element to serialize.
    encoding : str, optional
        The encoding to use. Defaults to ``"utf-8"``.
    self_closing : bool, optional
        If True, empty elements are written as self-closing tags
        (e.g., ``<element/>``). If False (default), empty elements
        have explicit opening and closing tags (``<element></element>``).

    Returns
    -------
    bytes
        The XML representation of the element as bytes.

    Raises
    ------
    TypeError
        If ``element`` is not a valid element type for this backend.

    """
    ...

  def register_namespace(self, prefix: str | None, uri: str) -> None:
    """Register a namespace mapping for use in tag and attribute resolution.

    Parameters
    ----------
    prefix : str | None
        The namespace prefix to register. Can be None for the default
        namespace (no prefix required). Must be a valid NCName.
    uri : str
        The namespace URI to associate with the prefix.

    Raises
    ------
    TypeError
        If ``prefix`` or ``uri`` is not a string.
    ValueError
        If ``prefix`` is not a valid NCName.

    Notes
    -----
    Registered namespaces are stored in the backend's global namespace map
    and used for resolving prefixed tag and attribute names when no explicit
    ``nsmap`` is provided. Namespace prefixes must be unique within a backend.

    """
    if not isinstance(uri, str):
      raise TypeError(f"given uri is not a str: {uri}")
    if prefix is not None and not isinstance(prefix, str):
      raise TypeError(f"given prefix is not a str: {prefix}")
    if prefix is not None and not is_ncname(prefix):
      raise ValueError(f"NCName {prefix} is not a valid xml prefix")
    if prefix == "xml":
      raise ValueError(f"NCName {prefix} is reserved for the xml namespace")
    self._global_nsmap[prefix] = uri

  @abstractmethod
  def iterparse(
    self,
    path: str | bytes | PathLike,
    tag_filter: str | Collection[str] | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> Iterator[TypeOfElement]:
    """Iteratively parse an XML file, yielding elements as they are closed.

    This method provides memory-efficient parsing of large XML files by
    processing elements incrementally rather than loading the entire
    document into memory.

    It yields elements Depth-First and in document order. It is also intended
    to be as memory-efficient as possible, as such as soon as an element that
    has been yielded is deemed safe to clear (e.g., all its possible ancestors
    have also been yielded), it is cleared to free up memory.

    This means that the caller must be careful to not keep references to
    elements yielded by this method as they may be cleared at any time
    and without warning.

    It also **strongly** recommended that a ``tag_filter`` is provided
    and for it to be as narrow as possible so as to not defeat the
    memory efficiency benefits of this method.

    Parameters
    ----------
    path : str | bytes | PathLike
        The path to the XML file to parse.
    tag_filter : str | Collection[str] | None, optional
        If provided, only yield elements with matching tags. This can
        significantly reduce memory usage when only specific elements
        are needed. Tag names follow the same resolution rules as ``get_tag``.
    nsmap : Mapping[str, str] | None, optional
        Namespace map to use for resolving prefixed tag names in the filter.
        If not provided, uses the backend's global namespace map.

    Yields
    ------
    T_Element
        Each element that matches ``tag_filter`` as it is fully parsed.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the file is not valid XML.

    Notes
    -----
    If the tag filter is None, all elements are yielded and the entire
    tree will slowly be built into memory.
    namespaces are NOT automatically registered to the backend's global
    namespace map as they encountered

    """
    ...

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
    path: str | bytes | PathLike | BufferedIOBase,
    elements: Iterable[TypeOfElement],
    encoding: str = "utf-8",
    *,
    root_elem: TypeOfElement | None = None,
    max_number_of_elements_in_buffer: int = 1000,
    write_xml_declaration: bool = True,
    write_doctype: bool = True,
  ) -> None:
    """Iteratively write elements to an XML file with streaming.

    This method provides memory-efficient writing of large XML files by
    buffering elements and writing them incrementally.

    Also useful any BufferedIOBase objects, making it suitable for streaming
    to a network socket or other streaming destination.

    Parameters
    ----------
    path : str | bytes | PathLike | BufferedIOBase
        The destination path or file-like object for the XML output.
        If a PathLike or string, the file is created (or overwritten).
        If a BufferedIOBase, it must be opened in binary write mode.
    elements : Iterable[T_Element]
        The elements to write. Elements are processed lazily and buffered
        to minimize memory usage.
    encoding : str, optional
        The encoding to use for the output file. Defaults to ``"utf-8"``.
    root_elem : T_Element | None, optional
        A custom root element to wrap the output. If not provided, a
        default ``<tmx version="1.4">`` element is created.
        If provided, the elements are written as children of this element.
    max_number_of_elements_in_buffer : int, optional
        The number of elements to buffer before flushing.
        Larger values may improve performance but increase memory usage.
        Must be at least 1. Defaults to 1000.
    write_declaration : bool, optional
        If True (default), include the xml declaration.
    write_doctype : bool, optional
        If True (default), include the TMX DOCTYPE declaration.

    Raises
    ------
    ValueError
        If ``max_number_of_elements_in_buffer`` is less than 1.
    OSError
        If the file cannot be written.

    Notes
    -----
    The output format is::

        <?xml version="1.0" encoding="..."?>
        <!DOCTYPE tmx SYSTEM "tmx14.dtd">
        <root_elem>
            <elem1/>
            <elem2/>
            ...
        </root_elem>

    Elements are written as self-closing tags (e.g., ``<elem/>``) when
    they have no text content.

    """
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
