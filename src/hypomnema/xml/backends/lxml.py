from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.policy import XmlPolicy
from copy import copy
from typing import overload, Literal
from logging import Logger
from collections.abc import Mapping, Collection, Generator, Iterator
from hypomnema.xml.utils import prep_tag_set, make_usable_path, normalize_encoding
from hypomnema.xml.backends.base import XmlBackend
import lxml.etree as et
from os import PathLike
from typing import Literal, overload

import lxml.etree as et

from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.utils import (make_usable_path, normalize_encoding,
                                 prep_tag_set)

__all__ = ["LxmlBackend"]


class LxmlBackend(XmlBackend[et._Element]):
  __slots__ = tuple()

  def __init__(
    self,
    nsmap: Mapping[str, str] | None = None,
    logger: Logger | None = None,
    default_encoding: str | None = None,
    policy: XmlPolicy | None = None,
  ):
    super().__init__(nsmap, logger, default_encoding, policy)

  @overload
  def get_tag(self, element: et._Element, as_qname: Literal[True]) -> QName: ...
  @overload
  def get_tag(self, element: et._Element, as_qname: bool = False) -> str: ...
  def get_tag(self, element: et._Element, as_qname: bool = False) -> str | QName:
    tag = element.tag
    result: QName
    match tag:
      case et.QName():
        result = QName(tag.text, nsmap=self.nsmap)
      case bytearray() | bytes():
        result = QName(tag.decode(self.default_encoding), nsmap=self.nsmap)
      case str():
        result = QName(tag, nsmap=self.nsmap)
      case _:
        raise TypeError(f"Unexpected tag type: {type(tag)}")
    return result if as_qname else result.text

  def create_element(
    self, tag: str | QNameLike, attributes: Mapping[str, str] | None = None
  ) -> et._Element:
    if attributes is None:
      attributes = {}
    _tag = QName(tag, nsmap=self.nsmap)
    return et.Element(_tag.qualified_name, attrib=attributes)

  def append_child(self, parent: et._Element, child: et._Element) -> None:
    parent.append(child)

  def get_attribute[TypeOfDefault](
    self,
    element: et._Element,
    attribute_name: str | QNameLike,
    default: TypeOfDefault | None = None,
  ) -> str | TypeOfDefault | None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    return element.get(_key.text, default)

  def set_attribute(
    self, element: et._Element, attribute_name: str | QNameLike, attribute_value: str
  ) -> None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    element.set(_key.text, attribute_value)

  def delete_attribute(self, element: et._Element, attribute_name: str | QNameLike) -> None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    element.attrib.pop(_key.text, None)

  def get_attribute_map(self, element: et._Element) -> dict[str, str]:
    return {k: v for k, v in element.attrib.items()}

  def get_text(self, element: et._Element) -> str | None:
    return element.text

  def set_text(self, element: et._Element, text: str | None) -> None:
    element.text = text

  def get_tail(self, element: et._Element) -> str | None:
    return element.tail

  def set_tail(self, element: et._Element, tail: str | None) -> None:
    element.tail = tail

  def iter_children(
    self,
    element: et._Element,
    tag_filter: str | QNameLike | Collection[str | QNameLike] | None = None,
  ) -> Generator[et._Element]:
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    for child in element:
      if tag_set is None or child.tag in tag_set:
        yield child

  def parse(self, path: str | PathLike, encoding: str | None = None) -> et._Element:
    path = make_usable_path(path, mkdir=False)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    root = et.parse(path, parser=et.XMLParser(encoding=encoding, recover=True, resolve_entities=False)).getroot()
    return root

  def write(self, element: et._Element, path: str | PathLike, encoding: str | None = None) -> None:
    path = make_usable_path(path, mkdir=True)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    with et.xmlfile(path, encoding=encoding) as f:
      f.write_declaration()
      f.write(element)

  def clear(self, element: et._Element) -> None:
    element.clear()

  def to_bytes(
    self, element: et._Element, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return et.tostring(element, encoding=encoding, xml_declaration=False)

  def iterparse(
    self, path: str | PathLike, tag_filter: str | Collection[str] | None = None
  ) -> Iterator[et._Element]:
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    ctx = et.iterparse(path, events=("start", "end"))
    yield from self._iterparse(ctx, tag_set)
