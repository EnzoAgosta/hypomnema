from collections.abc import Generator, Iterable, Iterator, Mapping
from copy import copy
from io import BufferedIOBase
from os import PathLike
from typing import Literal, overload

import lxml.etree as et

from hypomnema import XmlBackend
from hypomnema.xml.qname import QName, QNameLike
from hypomnema.xml.utils import (make_usable_path, normalize_encoding,
                                 prep_tag_set)


class StrictBackend(XmlBackend[int]):
  __slots__ = ("_store",)

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self._store: dict[int, et.Element] = {}

  def _register(self, element):
    """Register an internal element and return a handle."""
    obj_id = id(element)
    if obj_id not in self._store:
      self._store[obj_id] = element
    return obj_id

  def _get_elem(self, handle):
    """Retrieve the internal element from a handle."""
    return self._store[handle]

  @overload
  def get_tag(self, element: int, *, as_qname: Literal[True]) -> QName: ...
  @overload
  def get_tag(self, element: int, *, as_qname: Literal[False] = False) -> str: ...
  def get_tag(self, element: int, *, as_qname: bool = False) -> str | QName:
    _element = self._get_elem(element)
    tag = _element.tag
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
  ) -> int:
    if attributes is None:
      attributes = {}
    _attributes = {QName(key, nsmap=self.nsmap).text: value for key, value in attributes.items()}
    _tag = QName(tag, nsmap=self.nsmap)
    elem = et.Element(_tag.qualified_name, attrib=_attributes)
    return self._register(elem)

  def append_child(self, parent: int, child: int) -> None:
    parent_elem = self._get_elem(parent)
    child_elem = self._get_elem(child)
    parent_elem.append(child_elem)

  @overload
  def get_attribute(self, element: int, attribute_name: str) -> str | None: ...
  @overload
  def get_attribute[TypeOfDefault](
    self, element: int, attribute_name: str, *, default: TypeOfDefault
  ) -> str | TypeOfDefault: ...
  def get_attribute[TypeOfDefault](
    self, element: int, attribute_name: str, *, default: TypeOfDefault | None = None
  ) -> str | TypeOfDefault | None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    _element = self._get_elem(element)
    return _element.get(_key.text, default)

  def set_attribute(
    self, element: int, attribute_name: str | QNameLike, attribute_value: str
  ) -> None:
    _key = QName(attribute_name, nsmap=self.nsmap)
    _element = self._get_elem(element)
    _element.set(_key.text, attribute_value)

  def set_attribute(self, element, attribute_name, attribute_value, *, nsmap=None, unsafe=False):
    elem = self._get_elem(element)

    _nsmap = nsmap if nsmap is not None else self._global_nsmap
    attribute_name = attribute_name if unsafe else QName(attribute_name, _nsmap).qualified_name

  def get_text(self, element: int) -> str | None:
    _element = self._get_elem(element)
    return _element.text

  def set_text(self, element: int, text: str | None) -> None:
    _element = self._get_elem(element)
    _element.text = text

  def get_tail(self, element: int) -> str | None:
    _element = self._get_elem(element)
    return _element.tail

  def set_tail(self, element: int, tail: str | None) -> None:
    _element = self._get_elem(element)
    _element.tail = tail

  def iter_children(
    self, element: int, tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None
  ) -> Generator[int]:
    _element = self._get_elem(element)
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    for child in _element:
      if tag_set is None or child.tag in tag_set:
        yield self._register(child)

  def parse(self, path: str | PathLike, encoding: str | None = None) -> int:
    path = make_usable_path(path, mkdir=False)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    root = et.parse(
      path, parser=et.XMLParser(encoding=encoding, recover=True, resolve_entities=False)
    ).getroot()
    return self._register(root)

  def write(self, element: int, path: str | PathLike, encoding: str | None = None) -> None:
    path = make_usable_path(path, mkdir=True)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    _element = self._get_elem(element)
    with et.xmlfile(path, encoding=encoding) as f:
      f.write_declaration()
      f.write(_element)

  def clear(self, element: int) -> None:
    _element = self._get_elem(element)
    _element.clear()

  def to_bytes(
    self, element: int, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    _element = self._get_elem(element)
    if not self_closing and _element.text is None:
      _element = copy(_element)
      _element.text = ""
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return et.tostring(_element, encoding=encoding, xml_declaration=False)

  def iterparse(
    self,
    path: str | PathLike,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Iterator[int]:
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    ctx = et.iterparse(path, events=("start", "end"))
    # need to ignore mypy error for same reason as in lxml backend
    for elem in self._iterparse(ctx, tag_set):  # type: ignore[arg-type]
      yield self._register(elem)

  def iterwrite(
    self,
    path: str | PathLike | BufferedIOBase,
    elements: Iterable[int],
    encoding: str | None = None,
    *,
    root_elem=None,
    max_number_of_elements_in_buffer=1000,
    write_xml_declaration=True,
    write_doctype=True,
  ):
    elements = (self._get_elem(self._register(element)) for element in elements)
    root_elem = self.create_element("tmx", attributes={"version": "1.4"})

    super().iterwrite(
      path,
      _elements,
      encoding,
      root_elem=_root_elem,
      max_number_of_elements_in_buffer=max_number_of_elements_in_buffer,
      write_xml_declaration=write_xml_declaration,
      write_doctype=write_doctype,
    )
