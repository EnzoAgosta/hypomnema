from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.policy import XmlPolicy
from typing import overload, Literal
from logging import Logger
from collections.abc import Mapping, Collection, Generator, Iterator
from hypomnema.xml.utils import prep_tag_set, make_usable_path, normalize_encoding
from hypomnema.xml.backends.base import XmlBackend
import xml.etree.ElementTree as et
from collections.abc import Generator, Iterable, Iterator, Mapping
from logging import Logger
from os import PathLike
from typing import Literal, overload

from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.utils import (make_usable_path, normalize_encoding,
                                 prep_tag_set)

__all__ = ["StandardBackend"]


class StandardBackend(XmlBackend[et.Element]):
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
  def get_tag(self, element: et.Element, as_qname: Literal[True]) -> QName: ...
  @overload
  def get_tag(self, element: et.Element, as_qname: bool = False) -> str: ...
  def get_tag(self, element: et.Element, as_qname: bool = False) -> str | QName:
    tag = element.tag
    result: QName
    match tag:
      case et.QName():
        result = QName(tag.text, nsmap=self.nsmap)
      case str():
        result = QName(tag, nsmap=self.nsmap)
      case _:
        raise TypeError(f"Unexpected tag type: {type(tag)}")
    return result if as_qname else result.text

  def create_element(
    self, tag: str | QNameLike, attributes: Mapping[str, str] | None = None
  ) -> et.Element:
    if attributes is None:
      attributes = {}
    _tag = QName(tag, nsmap=self.nsmap)
    return et.Element(_tag.qualified_name, attrib=dict(attributes))

  def append_child(self, parent: et.Element, child: et.Element) -> None:
    parent.append(child)

  def get_attribute[TypeOfDefault](
    self, element: et.Element, attribute_name: str | QNameLike, default: TypeOfDefault | None = None
  ) -> str | TypeOfDefault | None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    return element.get(_key.text, default)

  def set_attribute(
    self, element: et.Element, attribute_name: str | QNameLike, attribute_value: str
  ) -> None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    element.set(_key.text, attribute_value)

  def delete_attribute(self, element: et.Element, attribute_name: str | QNameLike) -> None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    element.attrib.pop(_key.text, None)

  def get_attribute_map(self, element: et.Element) -> dict[str, str]:
    return {k: v for k, v in element.attrib.items()}

  def get_text(self, element: et.Element) -> str | None:
    return element.text

  def set_text(self, element: et.Element, text: str | None) -> None:
    element.text = text

  def get_tail(self, element: et.Element) -> str | None:
    return element.tail

  def set_tail(self, element: et.Element, tail: str | None) -> None:
    element.tail = tail

  def iter_children(
    self,
    element: et.Element,
    tag_filter: str | QNameLike | Collection[str | QNameLike] | None = None,
  ) -> Generator[et.Element]:
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    for child in element:
      if tag_set is None or child.tag in tag_set:
        yield child

  def parse(self, path: str | PathLike, encoding: str | None = None) -> et.Element:
    path = make_usable_path(path, mkdir=False)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    root = et.parse(path, parser=et.XMLParser(encoding=encoding)).getroot()
    return root

  def write(self, element: et.Element, path: str | PathLike, encoding: str | None = None) -> None:
    path = make_usable_path(path, mkdir=True)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    with open(path, "wb") as f:
      f.write(et.tostring(element, encoding=encoding, xml_declaration=True))

  def clear(self, element: et.Element) -> None:
    element.clear()

  def to_bytes(
    self, element: et.Element, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return et.tostring(
      element, encoding=encoding, xml_declaration=False, short_empty_elements=self_closing
    )

  def iterparse(
    self, path: str | PathLike, tag_filter: str | Collection[str] | None = None
  ) -> Iterator[et.Element]:
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    ctx = et.iterparse(path, events=("start", "end"))
    yield from self._iterparse(ctx, tag_set)
