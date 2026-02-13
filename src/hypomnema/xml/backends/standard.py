"""Standard library xml.etree backend implementation.

Provides XmlBackend implementation using Python's standard library
xml.etree.ElementTree module. This backend has no external dependencies
and is always available.
"""

from collections.abc import Generator, Iterable, Mapping
from os import PathLike
from typing import Literal, overload
import xml.etree.ElementTree as et

from hypomnema.xml.backends.base import TagLike, XmlBackend
from hypomnema.xml.utils import QNameLike, make_usable_path, normalize_encoding


class StandardBackend(XmlBackend[et.Element]):
  """XML backend using Python's standard library xml.etree.ElementTree.

  This backend provides portable XML parsing without external dependencies.
  While functional, it is slower than lxml for large files and has
  less sophisticated namespace handling.

  Args:
      logger: Logger for backend operations.
      default_encoding: Default character encoding.
      namespace_handler: Handler for namespace operations.

  Note:
      This backend uses xml.etree.ElementTree.Element as the underlying
      element type.
  """

  __slots__: tuple[str, ...] = tuple()

  def __init__(self, logger=None, default_encoding=None, *, namespace_handler=None):
    super().__init__(logger, default_encoding, namespace_handler=namespace_handler)

  def get_tag(
    self, element: et.Element, notation: Literal["prefixed", "qualified", "local"] = "local"
  ) -> str:
    """Get element tag name.

    Args:
        element: XML element.
        notation: Name format.

    Returns:
        Tag name in requested format.
    """
    tag = self.normalize_tag_name(element.tag)
    prefix, uri, localname = self._namespace_handler.qualify_name(tag, nsmap=self.nsmap)
    match notation:
      case "prefixed":
        return f"{prefix}:{localname}" if prefix is not None else localname
      case "qualified":
        return f"{{{uri}}}{localname}" if uri is not None else localname
      case "local":
        return localname
      case _:
        raise ValueError(
          f"Invalid notation {notation!r} expected one of 'prefixed', 'qualified' or 'local'"
        )

  def create_element(self, tag: TagLike, attributes: Mapping[str, str] | None = None) -> et.Element:
    """Create a new XML element.

    Args:
        tag: Element tag name.
        attributes: Element attributes.

    Returns:
        New XML element.
    """
    tag = self.normalize_tag_name(tag)
    prefix, uri, localname = self._namespace_handler.qualify_name(tag, nsmap=self.nsmap)
    attrib = {k: v for k, v in attributes.items()} if attributes is not None else {}
    match prefix, uri, localname:
      case None, None, str():
        return et.Element(localname, attrib=attrib)
      case str() | None, str(), str():
        return et.Element(f"{{{uri}}}{localname}", attrib=attrib)
      case str(), None, str():
        self._log(
          self._namespace_handler.policy.inexistent_namespace,
          "Namespace prefix %r is not registered. Creating element with localname only.",
          prefix,
        )
        return et.Element(localname, attrib=attrib)
      case _:
        raise ValueError("Could not resolve a usable tag name for element")

  def append_child(self, parent: et.Element, child: et.Element) -> None:
    """Append child element to parent.

    Args:
        parent: Parent element.
        child: Child element to append.
    """
    parent.append(child)

  @overload
  def get_attribute(self, element: et.Element, attribute_name: TagLike) -> str | None: ...
  @overload
  def get_attribute[TypeOfDefault](
    self, element: et.Element, attribute_name: TagLike, *, default: TypeOfDefault
  ) -> str | TypeOfDefault: ...
  def get_attribute[TypeOfDefault](
    self, element: et.Element, attribute_name: TagLike, *, default: TypeOfDefault | None = None
  ) -> str | TypeOfDefault | None:
    """Get attribute value from element.

    Args:
        element: XML element.
        attribute_name: Attribute name.
        default: Default value if attribute not present.

    Returns:
        Attribute value or default.
    """
    key = self.normalize_tag_name(attribute_name)
    return element.get(key, default)

  def set_attribute(
    self, element: et.Element, attribute_name: TagLike, attribute_value: str
  ) -> None:
    """Set attribute value on element.

    Args:
        element: XML element.
        attribute_name: Attribute name.
        attribute_value: Attribute value.
    """
    key = self.normalize_tag_name(attribute_name)
    element.set(key, attribute_value)

  def delete_attribute(self, element: et.Element, attribute_name: TagLike) -> None:
    """Delete attribute from element.

    Args:
        element: XML element.
        attribute_name: Attribute name.
    """
    key = self.normalize_tag_name(attribute_name)
    element.attrib.pop(key, None)

  def get_attribute_map(self, element: et.Element) -> dict[str, str]:
    """Get all attributes as a dictionary.

    Args:
        element: XML element.

    Returns:
        Mapping of attribute names to values.
    """
    return {k: v for k, v in element.attrib.items()}

  def get_text(self, element: et.Element) -> str | None:
    """Get text content of element."""
    return element.text

  def set_text(self, element: et.Element, text: str | None) -> None:
    """Set text content of element."""
    element.text = text

  def get_tail(self, element: et.Element) -> str | None:
    """Get tail text (text following element)."""
    return element.tail

  def set_tail(self, element: et.Element, tail: str | None) -> None:
    """Set tail text."""
    element.tail = tail

  def iter_children(
    self, element: et.Element, tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None
  ) -> Generator[et.Element]:
    """Iterate over child elements.

    Args:
        element: Parent element.
        tag_filter: Optional tag filter for child elements.

    Yields:
        Child elements matching filter.
    """
    if not len(element):
      return
    tag_set = self.prep_tag_set(tag_filter) if tag_filter is not None else None
    for child in element:
      child_tag = self.get_tag(child)
      if tag_set is None or child_tag in tag_set:
        yield child

  def parse(self, path: str | PathLike, encoding: str | None = None) -> et.Element:
    """Parse XML file and return root element.

    Args:
        path: Path to XML file.
        encoding: Character encoding.

    Returns:
        Root element of parsed document.
    """
    encoding = normalize_encoding(encoding)
    source = make_usable_path(path, mkdir=False)
    return et.parse(source, parser=et.XMLParser(encoding=encoding)).getroot()

  def write(self, element: et.Element, path: str | PathLike, encoding: str | None = None) -> None:
    """Write XML element to file.

    Args:
        element: Root element to write.
        path: Output file path.
        encoding: Character encoding.
    """
    encoding = normalize_encoding(encoding)
    source = make_usable_path(path, mkdir=True)
    tree = et.ElementTree(element)
    with open(source, "wb") as f:
      f.write(b'<?xml version="1.0" encoding="' + encoding.encode(encoding) + b'"?>\n')
      f.write(b'<!DOCTYPE tmx SYSTEM "tmx14.dtd">\n')
      tree.write(f, encoding=encoding, xml_declaration=False, short_empty_elements=False)

  def clear(self, element: et.Element) -> None:
    """Clear element to free memory."""
    element.clear()

  def to_bytes(
    self, element: et.Element, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    """Serialize element to bytes.

    Args:
        element: Element to serialize.
        encoding: Character encoding.
        self_closing: Whether to use self-closing tags.

    Returns:
        Serialized XML bytes.
    """
    encoding = normalize_encoding(encoding)
    return et.tostring(
      element, encoding=encoding, xml_declaration=False, short_empty_elements=self_closing
    )

  def iterparse(
    self,
    path: str | PathLike,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[et.Element]:
    """Iteratively parse XML file yielding matching elements.

    Args:
        path: Path to XML file.
        tag_filter: Tags to yield.

    Yields:
        Elements matching filter.
    """
    source = make_usable_path(path, mkdir=False)
    ctx = et.iterparse(source, events=("start", "end"))
    _tag_set = self.prep_tag_set(tag_filter) if tag_filter is not None else None
    yield from self._iterparse(ctx, _tag_set)  # type: ignore[arg-type]
