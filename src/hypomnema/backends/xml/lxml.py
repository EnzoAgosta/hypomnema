"""`lxml.etree` implementation of the shared XML backend contract.

`LxmlBackend` provides the same public `XmlBackend` interface as the standard
library backend while using `lxml`'s parser and serializer primitives under the
covers.
"""

from collections.abc import Generator, Iterable, Mapping
from copy import copy
from logging import Logger
from os import PathLike
from typing import Literal, overload
import lxml.etree as et

from hypomnema.backends.xml.base import NamespaceHandler, TagLike, XmlBackend
from hypomnema.backends.xml.utils import QNameLike, make_usable_path, normalize_encoding


class LxmlBackend(XmlBackend[et._Element]):
  """XML backend built on `lxml.etree`.

  This backend keeps the same behavioral contract as `StandardBackend` but uses
  `lxml`'s element type, parser configuration, and streaming writer.
  """

  __slots__: tuple[str, ...] = tuple()

  def _normalize_attribute_name(self, attribute_name: TagLike) -> str:
    """Resolve an attribute name into the representation expected by `lxml`."""
    key = self.normalize_tag_name(attribute_name)
    prefix, uri, localname = self._namespace_handler.qualify_name(key, nsmap=self.nsmap)
    match prefix, uri, localname:
      case None, None, str():
        return localname
      case str() | None, str(), str():
        return f"{{{uri}}}{localname}"
      case str(), None, str():
        self._log(
          self._namespace_handler.policy.inexistent_namespace,
          "Namespace prefix %r is not registered. Using local attribute name only.",
          prefix,
        )
        return localname
      case _:
        raise ValueError("Could not resolve a usable attribute name")

  def __init__(
    self,
    logger: Logger | None = None,
    default_encoding: str | None = None,
    *,
    namespace_handler: NamespaceHandler | None = None,
  ) -> None:
    super().__init__(logger, default_encoding, namespace_handler=namespace_handler)

  def get_tag(
    self, element: et._Element, notation: Literal["prefixed", "qualified", "local"] = "local"
  ) -> str:
    """Get the tag name for `element` in the requested notation."""
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

  def create_element(
    self, tag: TagLike, attributes: Mapping[str, str] | None = None
  ) -> et._Element:
    """Create a new `lxml` element using the backend namespace policy."""
    tag = self.normalize_tag_name(tag)
    prefix, uri, localname = self._namespace_handler.qualify_name(tag, nsmap=self.nsmap)
    attrib = {k: v for k, v in attributes.items()} if attributes is not None else {}
    match prefix, uri, localname:
      case None, None, str():
        return et.Element(localname, attrib=attrib)
      case str(), str(), str():
        return et.Element(f"{{{uri}}}{localname}", attrib=attrib, nsmap={prefix: uri})
      case None, str(), str():
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

  def append_child(self, parent: et._Element, child: et._Element) -> None:
    """Append `child` to `parent`."""
    parent.append(child)

  @overload
  def get_attribute(self, element: et._Element, attribute_name: TagLike) -> str | None: ...
  @overload
  def get_attribute[TypeOfDefault](
    self, element: et._Element, attribute_name: TagLike, *, default: TypeOfDefault
  ) -> str | TypeOfDefault: ...
  def get_attribute[TypeOfDefault](
    self, element: et._Element, attribute_name: TagLike, *, default: TypeOfDefault | None = None
  ) -> str | TypeOfDefault | None:
    """Return one attribute value from `element`."""
    key = self._normalize_attribute_name(attribute_name)
    return element.get(key, default)

  def set_attribute(
    self, element: et._Element, attribute_name: TagLike, attribute_value: str
  ) -> None:
    """Set one attribute on `element`."""
    key = self._normalize_attribute_name(attribute_name)
    element.set(key, attribute_value)

  def delete_attribute(self, element: et._Element, attribute_name: TagLike) -> None:
    """Delete one attribute from `element` if it exists."""
    key = self._normalize_attribute_name(attribute_name)
    element.attrib.pop(key, None)

  def get_attribute_map(self, element: et._Element) -> dict[str, str]:
    """Return element attributes keyed by local name."""
    attribute_map: dict[str, str] = {}
    for k, v in element.attrib.items():
      _, _, localname = self._namespace_handler.qualify_name(k, nsmap=self.nsmap)
      attribute_map[localname] = v
    return attribute_map

  def get_text(self, element: et._Element) -> str | None:
    """Return the element's text content."""
    return element.text

  def set_text(self, element: et._Element, text: str | None) -> None:
    """Replace the element's text content."""
    element.text = text

  def get_tail(self, element: et._Element) -> str | None:
    """Return the tail text that follows `element`."""
    return element.tail

  def set_tail(self, element: et._Element, tail: str | None) -> None:
    """Replace the tail text that follows `element`."""
    element.tail = tail

  def iter_children(
    self,
    element: et._Element,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[et._Element]:
    """Yield child elements, optionally filtering by tag."""
    if not len(element):
      return
    tag_set = self.prep_tag_set(tag_filter) if tag_filter is not None else None
    for child in element:
      child_tag = self.get_tag(child)
      if tag_set is None or child_tag in tag_set:
        yield child

  def parse(self, path: str | PathLike[str], encoding: str | None = None) -> et._Element:
    """Parse an XML file and return its root element.

    The underlying parser enables `recover=True` and disables entity
    resolution.
    """
    encoding = normalize_encoding(encoding)
    source = make_usable_path(path, mkdir=False)
    return et.parse(
      source, parser=et.XMLParser(encoding=encoding, recover=True, resolve_entities=False)
    ).getroot()

  def from_bytes(self, payload: bytes, encoding: str | None = None) -> et._Element:
    """Parse one serialized element payload into an `lxml` element."""
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return et.fromstring(
      payload, parser=et.XMLParser(encoding=encoding, recover=True, resolve_entities=False)
    )

  def write(
    self, element: et._Element, path: str | PathLike[str], encoding: str | None = None
  ) -> None:
    """Write an XML document with declaration and TMX doctype."""
    encoding = normalize_encoding(encoding)
    source = make_usable_path(path, mkdir=True)
    with et.xmlfile(source, encoding=encoding) as f:
      f.write_declaration()
      f.write_doctype("<!DOCTYPE tmx SYSTEM 'tmx14.dtd'>")
      f.write(element)

  def clear(self, element: et._Element) -> None:
    """Clear an element in place to free parser memory."""
    element.clear()

  def to_bytes(
    self,
    element: et._Element,
    encoding: str | None = None,
    self_closing: bool = False,
    *,
    strip_tail: bool = False,
  ) -> bytes:
    """Serialize one element to bytes.

    When `strip_tail` is true, the serialized payload omits the element's tail.
    This is the form the built-in unknown-node loaders use for round-tripping.
    """
    encoding = normalize_encoding(encoding)
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""

    return et.tostring(element, encoding=encoding, xml_declaration=False, with_tail=not strip_tail)

  def iterparse(
    self,
    path: str | PathLike[str],
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[et._Element]:
    """Stream elements from a document using `lxml.etree.iterparse()`."""
    source = make_usable_path(path, mkdir=False)
    ctx = et.iterparse(source, events=("start", "end"))
    _tag_set = self.prep_tag_set(tag_filter) if tag_filter is not None else None
    # Even though we restrict the events to "start" and "end" at runtime
    # lxml's typing doesn't narrow to only "start" and "end" events
    # and actually includes "comment" and "pi" in the return type.
    yield from self._iterparse(ctx, _tag_set)  # type: ignore[arg-type]
