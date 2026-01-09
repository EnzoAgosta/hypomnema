from typing import overload, Literal
from collections.abc import Mapping, Collection, Generator, Iterator
from hypomnema.xml.utils import QName, prep_tag_set, make_usable_path, normalize_encoding
from hypomnema.xml.backends.base import XmlBackend
import xml.etree.ElementTree as et
from os import PathLike

__all__ = ["StandardBackend"]


class StandardBackend(XmlBackend[et.Element]):
  """XML backend using the Python standard library's xml.etree.ElementTree.

  This backend provides maximum portability as it requires no external
  dependencies. It uses ``xml.etree.ElementTree.Element`` for element
  representation and ``dict[str, str]`` for attribute mappings.

  Notes
  -----
  Unlike the lxml backend, this backend does not accept bytes or QName
  objects for ``attribute_name`` in ``get_attribute`` and ``set_attribute``.

  The ``write`` method always includes an XML declaration and uses
  ``short_empty_elements=False`` to generate explicit closing tags.

  """

  __slots__ = tuple()

  @overload
  def get_tag(
    self,
    element: et.Element,
    *,
    encoding: str = "utf-8",
    as_qname: Literal[True],
    nsmap: Mapping[str | None, str] | None = None,
  ) -> QName: ...
  @overload
  def get_tag(
    self,
    element: et.Element,
    *,
    encoding: str = "utf-8",
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str: ...
  def get_tag(
    self,
    element: et.Element,
    *,
    encoding: str = "utf-8",
    as_qname: bool = False,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | QName:
    element_tag = element.tag
    _encoding = normalize_encoding(encoding)
    if isinstance(element_tag, et.QName):
      tag = element_tag.text
    elif isinstance(element_tag, (bytes, bytearray)):
      tag = element_tag.decode(_encoding)
    else:
      tag = element_tag
    qname_wrapper = QName(
      tag, nsmap if nsmap is not None else self._global_nsmap, encoding=_encoding
    )
    return qname_wrapper if as_qname else qname_wrapper.qualified_name

  def create_element(
    self,
    tag: str | QName,
    attributes: Mapping[str, str] | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> et.Element:
    if isinstance(tag, str):
      element_tag = QName(tag, nsmap if nsmap is not None else self._global_nsmap).qualified_name
    elif isinstance(tag, QName):
      element_tag = tag.qualified_name
    else:
      raise TypeError(f"Unexpected tag type: {type(tag)}")
    _attributes = {}
    if attributes is not None:
      for key, value in attributes.items():
        if not isinstance(value, str):
          raise TypeError(f"Unexpected value type: {type(value)}")
        key = QName(key, nsmap if nsmap is not None else self._global_nsmap).qualified_name
        _attributes[key] = value
    return et.Element(element_tag, attrib=_attributes)

  def append_child(self, parent: et.Element, child: et.Element) -> None:
    if not isinstance(parent, et.Element):
      raise TypeError(f"Parent is not an xml.ElementTree.Element: {type(parent)}")
    if not isinstance(child, et.Element):
      raise TypeError(f"Child is not an xml.ElementTree.Element: {type(child)}")
    parent.append(child)

  def get_attribute(
    self,
    element: et.Element,
    attribute_name: str | QName,
    default: str | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> str | None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    if isinstance(attribute_name, QName):
      attribute_name = attribute_name.qualified_name
    elif isinstance(attribute_name, str):
      attribute_name = QName(
        attribute_name, nsmap if nsmap is not None else self._global_nsmap
      ).qualified_name
    else:
      raise TypeError(f"Unexpected attribute name type: {type(attribute_name)}")
    return element.get(attribute_name, default)

  def set_attribute(
    self,
    element: et.Element,
    attribute_name: str,
    attribute_value: str | None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
    unsafe: bool = False,
  ) -> None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    attribute_name = (
      attribute_name
      if unsafe
      else QName(attribute_name, nsmap if nsmap is not None else self._global_nsmap).qualified_name
    )
    try:
      if attribute_value is None:
        element.attrib.pop(attribute_name)
      else:
        element.attrib[attribute_name] = attribute_value
    except KeyError:
      pass

  def get_attribute_map(self, element: et.Element) -> dict[str, str]:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    return element.attrib

  def get_text(self, element: et.Element) -> str | None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    return element.text

  def set_text(self, element: et.Element, text: str | None) -> None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    element.text = text

  def get_tail(self, element: et.Element) -> str | None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    return element.tail

  def set_tail(self, element: et.Element, tail: str | None) -> None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    element.tail = tail

  def iter_children(
    self,
    element: et.Element,
    tag_filter: str | QName | Collection[str | QName] | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> Generator[et.Element]:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    tag_filter = prep_tag_set(tag_filter, nsmap if nsmap is not None else self._global_nsmap)
    for child in element:
      if tag_filter is None or child.tag in tag_filter:
        yield child

  def parse(self, path: str | bytes | PathLike, encoding: str = "utf-8") -> et.Element:
    path = make_usable_path(path, mkdir=False)
    root = et.parse(path, parser=et.XMLParser(encoding=normalize_encoding(encoding))).getroot()
    return root

  def write(
    self, element: et.Element, path: str | bytes | PathLike, encoding: str = "utf-8"
  ) -> None:
    """Write an element tree to an XML file.

    This implementation uses ``ElementTree.write`` with ``short_empty_elements=False``,
    ensuring all empty elements have explicit closing tags (e.g., ``<elem></elem>``
    rather than ``<elem/>``).

    Parameters
    ----------
    element : et.Element
        The root element to write.
    path : str | bytes | PathLike
        The destination path for the XML file.
    encoding : str, optional
        The encoding to use when writing the file. Defaults to ``"utf-8"``.

    """
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    path = make_usable_path(path, mkdir=True)
    et.ElementTree(element).write(
      path, normalize_encoding(encoding), xml_declaration=True, short_empty_elements=False
    )

  def clear(self, element: et.Element) -> None:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    element.clear()

  def to_bytes(
    self, element: et.Element, encoding: str = "utf-8", self_closing: bool = False
  ) -> bytes:
    if not isinstance(element, et.Element):
      raise TypeError(f"Element is not an xml.ElementTree.Element: {type(element)}")
    return et.tostring(
      element,
      encoding=normalize_encoding(encoding),
      xml_declaration=False,
      short_empty_elements=self_closing,
    )

  def iterparse(
    self,
    path: str | bytes | PathLike,
    tag_filter: str | Collection[str] | None = None,
    *,
    nsmap: Mapping[str | None, str] | None = None,
  ) -> Iterator[et.Element]:
    tag_filter = prep_tag_set(tag_filter, nsmap if nsmap is not None else self._global_nsmap)
    path = make_usable_path(path, mkdir=False)
    ctx = et.iterparse(path, events=("start", "end"))
    yield from self._iterparse(ctx, tag_filter)
