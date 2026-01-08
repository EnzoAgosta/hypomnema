from typing import overload, Literal
from collections.abc import Mapping, Collection, Generator, Iterator
from hypomnema.xml.utils import QName, prep_tag_set, make_usable_path, normalize_encoding
from hypomnema.xml.backends.base import XmlBackend
import lxml.etree as et
from lxml import _types as lxml_types
from os import PathLike
from typing import Literal, overload

import lxml.etree as et

from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.utils import (make_usable_path, normalize_encoding,
                                 prep_tag_set)

__all__ = ["LxmlBackend"]


class LxmlBackend(XmlBackend[et._Element, lxml_types._AttrMapping]):
  __slots__ = tuple()

  def __init__(
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
    """Set text content of an element.

    Parameters
    ----------
    element : et._Element
        The XML element.
    text : str | None
        Text content to set.
    """
    element.text = text

  def get_tail(self, element: et._Element) -> str | None:
    """Get tail text (text after element's closing tag).

    Parameters
    ----------
    element : et._Element
        The XML element.

    Returns
    -------
    str | None
        Tail text, or None if empty.
    """
    return element.tail

  def set_tail(self, element: et._Element, tail: str | None) -> None:
    """Set tail text of an element.

    Parameters
    ----------
    element : et._Element
        The XML element.
    tail : str | None
        Tail text to set.
    """
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
    path = make_usable_path(path, mkdir=False)
    root = et.parse(
      path, parser=et.XMLParser(encoding=normalize_encoding(encoding), recover=True)
    ).getroot()
    return root

  def write(
    self, element: et._Element, path: str | bytes | PathLike, encoding: str = "utf-8"
  ) -> None:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    path = make_usable_path(path, mkdir=True)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    with et.xmlfile(path, encoding=encoding) as f:
      f.write_declaration()
      f.write(element)

  def clear(self, element: et._Element) -> None:
    """Clear element content and free memory.

    Parameters
    ----------
    element : et._Element
        Element to clear.
    """
    element.clear()

  def to_bytes(
    self, element: et._Element, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    if not isinstance(element, et._Element):
      raise TypeError(f"Element is not an lxml.etree._Element: {type(element)}")
    if self_closing and not element.text:
      element.text = ""
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return et.tostring(element, encoding=encoding, xml_declaration=False)

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
    # need to ignore mypy error here because lxml typing
    # doesn't narrow to only "start" and "end" events even
    # when setting events to ("start", "end")
    yield from self._iterparse(ctx, tag_set)  # type: ignore[arg-type]
