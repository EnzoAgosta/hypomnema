from typing import overload, Literal
from collections.abc import Mapping, Collection, Generator, Iterator
from hypomnema.xml.utils import QName, prep_tag_set, make_usable_path, normalize_encoding
from hypomnema.xml.backends.base import XmlBackend
import lxml.etree as et
from lxml import _types as lxml_types
from os import PathLike

__all__ = ["LxmlBackend"]


class LxmlBackend(XmlBackend[et._Element, lxml_types._AttrMapping]):
  """XML backend using the lxml library.

  This backend provides higher performance and additional features compared
  to the standard library implementation, including better XPath support
  and more efficient memory handling for large documents.

  The backend uses ``lxml.etree._Element`` for element representation and
  ``lxml._types._AttrMapping`` for attribute dictionaries.

  Notes
  -----
  When ``get_tag`` encounters bytes or bytearray tags (as lxml may return
  for certain encodings), it decodes them using the specified encoding.

  The ``get_attribute`` and ``set_attribute`` methods accept ``lxml.etree.QName``
  objects in addition to strings for the ``attribute_name`` parameter.

  """

  __slots__ = tuple()

  @overload
  def get_tag(
    self,
    element: et._Element,
    *,
    encoding: str = "utf-8",
    as_qname: Literal[True],
    nsmap: Mapping[str | None, str] | None = None,
  ) -> QName: ...
  @overload
  def get_tag(
    self,
    element: et._Element,
    *,
    encoding: str = "utf-8",
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str: ...
  def get_tag(
    self,
    element: et._Element,
    *,
    encoding: str = "utf-8",
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | QName:
    """Return the tag name of an element.

    This implementation handles lxml's internal QName representation
    and decodes byte/bytearray tags when necessary.

    Parameters
    ----------
    encoding : str, optional
        Encoding to use when decoding bytearray tags. Defaults to ``"utf-8"``.
        This parameter is specific to the lxml backend.
    as_qname : bool, optional
        If True, return a ``QName`` object. If False (default), return
        the fully qualified tag name as a string.
    nsmap : Mapping[str | None, str] | None, optional
        Namespace map for resolution. Defaults to the element's intrinsic
        namespace map.

    Returns
    -------
    str | QName
        The tag name as a string or ``QName`` object.

    """
    element_tag = element.tag
    _encoding = normalize_encoding(encoding)
    if isinstance(element_tag, et.QName):
      tag = element_tag.text
    elif isinstance(element_tag, (bytes, bytearray)):
      tag = element_tag.decode(_encoding)
    else:
      tag = element_tag
    qname_wrapper = QName(tag, nsmap if nsmap is not None else element.nsmap, encoding=_encoding)
    return qname_wrapper if as_qname else qname_wrapper.qualified_name

  def create_element(
    self,
    tag: str | QName,
    attributes: lxml_types._AttrMapping | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> et._Element:
    if isinstance(tag, str):
      element_tag = QName(tag, nsmap if nsmap is not None else self._global_nsmap)
    elif isinstance(tag, QName):
      element_tag = tag
    else:
      raise TypeError(f"Unexpected tag type: {type(tag)}")
    return et.Element(
      element_tag.qualified_name,
      attrib=attributes,
      nsmap=nsmap if nsmap is not None else self._global_nsmap,
    )

  def append_child(self, parent: et._Element, child: et._Element) -> None:
    if not isinstance(parent, et._Element):
      raise TypeError(f"Parent is not an lxml.etree._Element: {type(parent)}")
    if not isinstance(child, et._Element):
      raise TypeError(f"Child is not an lxml.etree._Element: {type(child)}")
    parent.append(child)

  def get_attribute(
    self,
    element: et._Element,
    attribute_name: lxml_types._AttrNameKey,
    default: str | None = None,
    *,
    encoding: str = "utf-8",
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | None:
    """Retrieve the value of an attribute.

    This implementation accepts ``lxml.etree.QName`` objects for
    ``attribute_name`` and handles bytes/bytearray attribute names.

    Parameters
    ----------
    attribute_name : str | bytes | QName
        The attribute name. Can be a string, bytes, bytearray, or
        ``lxml.etree.QName`` object.
    encoding : str, optional
        Encoding to use when decoding bytearray attribute names.
        Defaults to ``"utf-8"``. Specific to lxml backend.
    default : str | None, optional
        Value to return if the attribute does not exist.

    Returns
    -------
    str | None
        The attribute value or ``default``.

    """
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    if isinstance(attribute_name, et.QName):
      attribute_name = attribute_name.text
    if isinstance(attribute_name, (bytes, bytearray)):
      attribute_name = attribute_name.decode(normalize_encoding(encoding))
    if attribute_name[0] == "{" or ":" in attribute_name:
      attribute_name = QName(
        attribute_name, nsmap if nsmap is not None else element.nsmap
      ).qualified_name
    return element.get(attribute_name, default)

  def set_attribute(
    self,
    element: et._Element,
    attribute_name: lxml_types._AttrName,
    attribute_value: lxml_types._AttrVal | None,
    *,
    encoding: str = "utf-8",
    nsmap: Mapping[str | None, str] | None = None,
  ) -> None:
    """Set or remove an attribute on an element.

    This implementation accepts ``lxml.etree.QName`` objects for
    ``attribute_name`` and handles bytes/bytearray attribute names.
    Silently ignores KeyError when removing non-existent attributes.

    Parameters
    ----------
    attribute_name : str | bytes | bytearray | QName
        The attribute name. Can be a string, bytes, bytearray, or
        ``lxml.etree.QName`` object.
    attribute_value : str | None
        The value to set. If None, the attribute is removed.
    encoding : str, optional
        Encoding to use when decoding bytearray attribute names.
        Defaults to ``"utf-8"``. Specific to lxml backend.

    """
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    if isinstance(attribute_name, et.QName):
      attribute_name = attribute_name.text
    if isinstance(attribute_name, (bytes, bytearray)):
      attribute_name = attribute_name.decode(normalize_encoding(encoding))
    if attribute_name[0] == "{" or ":" in attribute_name:
      attribute_name = QName(
        attribute_name, nsmap if nsmap is not None else element.nsmap
      ).qualified_name
    try:
      if attribute_value is None:
        element.attrib.pop(attribute_name)
      else:
        element.attrib[attribute_name] = attribute_value
    except KeyError:
      pass

  def get_attribute_map(self, element: et._Element) -> lxml_types._AttrMapping:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    return element.attrib

  def get_text(self, element: et._Element) -> str | None:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    return element.text

  def set_text(self, element: et._Element, text: str | None) -> None:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    element.text = text

  def get_tail(self, element: et._Element) -> str | None:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    return element.tail

  def set_tail(self, element: et._Element, tail: str | None) -> None:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    element.tail = tail

  def iter_children(
    self,
    element: et._Element,
    tag_filter: str | Collection[str] | None = None,
    *,
    nsmap: Mapping[str, str] | None = None,
  ) -> Generator[et._Element]:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    tag_filter = prep_tag_set(tag_filter)
    for child in element:
      if tag_filter is None or child.tag in tag_filter:
        yield child

  def parse(self, path: str | bytes | PathLike, encoding: str = "utf-8") -> et._Element:
    """Parse an XML file and return the root element.

    This implementation uses lxml's XMLParser with ``recover=True``,
    allowing parsing of malformed XML where possible.

    Parameters
    ----------
    path : str | bytes | PathLike
        The path to the XML file to parse.
    encoding : str, optional
        The encoding to use when reading the file. Defaults to ``"utf-8"``.

    Returns
    -------
    et._Element
        The root element of the parsed XML document.

    """
    path = make_usable_path(path, mkdir=False)
    root = et.parse(
      path, parser=et.XMLParser(encoding=normalize_encoding(encoding), recover=True)
    ).getroot()
    return root

  def write(
    self, element: et._Element, path: str | bytes | PathLike, encoding: str = "utf-8"
  ) -> None:
    """Write an element tree to an XML file.

    This implementation uses lxml's ``xmlfile`` context manager for
    efficient writing with proper XML declaration handling.

    Parameters
    ----------
    element : et._Element
        The root element to write.
    path : str | bytes | PathLike
        The destination path for the XML file.
    encoding : str, optional
        The encoding to use when writing the file. Defaults to ``"utf-8"``.

    """
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    path = make_usable_path(path, mkdir=True)
    with et.xmlfile(path, encoding=normalize_encoding(encoding)) as f:
      f.write_declaration()
      f.write(element)

  def clear(self, element: et._Element) -> None:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    element.clear()

  def to_bytes(
    self, element: et._Element, encoding: str = "utf-8", self_closing: bool = False
  ) -> bytes:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    if self_closing and not element.text:
      element.text = ""
    return et.tostring(element, encoding=normalize_encoding(encoding), xml_declaration=False)

  def iterparse(
    self,
    path: str | bytes | PathLike,
    tag_filter: str | Collection[str] | None = None,
    *,
    nsmap: Mapping[str, str] | None = None,
  ) -> Iterator[et._Element]:
    tag_filter = prep_tag_set(tag_filter)
    path = make_usable_path(path, mkdir=False)
    ctx = et.iterparse(path, events=("start", "end"))
    yield from self._iterparse(ctx, tag_filter)
