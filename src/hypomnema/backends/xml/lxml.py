"""`lxml.etree` implementation of the shared XML backend contract.

`LxmlBackend` provides the same public `XmlBackend` interface as the standard
library backend while using `lxml`'s parser and serializer primitives under the
covers.
"""

from collections.abc import Generator, Iterable, Mapping, MutableMapping
from copy import copy
from io import BytesIO
from logging import Logger
from os import PathLike
from typing import BinaryIO, Literal, cast, overload
import lxml.etree as et

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.backends.xml.namespace import format_notation, resolve
from hypomnema.backends.xml.utils import normalize_encoding


class LxmlBackend(XmlBackend[et._Element]):
  """XML backend built on `lxml.etree`.

  This backend keeps the same behavioral contract as `StandardBackend` but uses
  `lxml`'s element type, parser configuration, and streaming writer.

  Args:
      default_encoding: Default character encoding.
      logger: Logger for backend operations.
      global_nsmap: Initial namespace mappings.
  """

  __slots__: tuple[str, ...] = tuple()

  def __init__(
    self,
    *,
    default_encoding: str | None = None,
    logger: Logger | None = None,
    global_nsmap: MutableMapping[str, str] | None = None,
  ) -> None:
    super().__init__(default_encoding=default_encoding, logger=logger, global_nsmap=global_nsmap)

  def get_tag(
    self,
    element: et._Element,
    *,
    notation: Literal["qualified", "local", "prefixed"] = "qualified",
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str:
    tag = str(element.tag)
    element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
    merged_nsmap: MutableMapping[str, str] = (
      {**nsmap, **element_nsmap} if nsmap is not None else element_nsmap
    )
    resolved = resolve(tag, global_nsmap=self._global_nsmap, nsmap=merged_nsmap)
    return format_notation(
      resolved.clark, notation, global_nsmap=self._global_nsmap, nsmap=merged_nsmap
    )

  def create_element(
    self,
    tag: str | bytes,
    attributes: Mapping[str, str] | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> et._Element:
    if isinstance(tag, bytes):
      tag = tag.decode(self.default_encoding)
    result = resolve(tag, global_nsmap=self._global_nsmap, nsmap=nsmap)

    resolved_attribs: dict[str, str] = {
      resolve(key, global_nsmap=self._global_nsmap, nsmap=nsmap).clark: value
      for key, value in (attributes or {}).items()
    }
    if result.prefix is not None and result.uri is not None:
      element_nsmap: dict[str, str] = {result.prefix: result.uri}
      return et.Element(result.clark, attrib=resolved_attribs, nsmap=element_nsmap)
    return et.Element(result.clark, attrib=resolved_attribs)

  def append_child(self, parent: et._Element, child: et._Element) -> None:
    parent.append(child)

  @overload
  def get_attribute(
    self, element: et._Element, name: str | bytes, *, nsmap: MutableMapping[str, str] | None = None
  ) -> str | None: ...
  @overload
  def get_attribute[D](
    self,
    element: et._Element,
    name: str | bytes,
    *,
    default: D,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str | D: ...
  def get_attribute[D](
    self,
    element: et._Element,
    name: str | bytes,
    *,
    default: D | None = None,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> str | D | None:
    if isinstance(name, bytes):
      name = name.decode(self.default_encoding)
    element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
    merged_nsmap: MutableMapping[str, str] = (
      {**nsmap, **element_nsmap} if nsmap is not None else element_nsmap
    )
    key = resolve(name, global_nsmap=self._global_nsmap, nsmap=merged_nsmap).clark
    return element.get(key, default)

  def set_attribute(
    self,
    element: et._Element,
    name: str | bytes,
    value: str,
    *,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> None:
    if isinstance(name, bytes):
      name = name.decode(self.default_encoding)
    element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
    merged_nsmap: MutableMapping[str, str] = (
      {**nsmap, **element_nsmap} if nsmap is not None else element_nsmap
    )
    key = resolve(name, global_nsmap=self._global_nsmap, nsmap=merged_nsmap).clark
    element.set(key, value)

  def delete_attribute(
    self, element: et._Element, name: str | bytes, *, nsmap: MutableMapping[str, str] | None = None
  ) -> None:
    if isinstance(name, bytes):
      name = name.decode(self.default_encoding)
    element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
    merged_nsmap: MutableMapping[str, str] = (
      {**nsmap, **element_nsmap} if nsmap is not None else element_nsmap
    )
    key = resolve(name, global_nsmap=self._global_nsmap, nsmap=merged_nsmap).clark
    element.attrib.pop(key, None)

  def get_attribute_map(
    self,
    element: et._Element,
    *,
    notation: Literal["qualified", "local", "prefixed"] = "qualified",
    nsmap: MutableMapping[str, str] | None = None,
  ) -> dict[str, str]:
    element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
    merged_nsmap: MutableMapping[str, str] = (
      {**nsmap, **element_nsmap} if nsmap is not None else element_nsmap
    )
    return {
      format_notation(key, notation, global_nsmap=self._global_nsmap, nsmap=merged_nsmap): value
      for key, value in element.attrib.items()
    }

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
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> Generator[et._Element]:
    if not len(element):
      return
    if tag_filter is not None:
      element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
      if nsmap is None:
        nsmap = {}
      nsmap.update(element_nsmap)
      tag_set = self._resolve_tag_filter(tag_filter, nsmap)
    else:
      tag_set = None
    for child in element:
      child_tag = str(child.tag)
      if tag_set is None or child_tag in tag_set:
        yield child

  def parse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    encoding: str | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> et.Element:
    collected_ns: dict[str, str] = {}
    root: et.Element | None = None
    events: tuple[Literal["start", "start-ns"], ...]
    events = ("start", "start-ns") if populate_nsmap else ("start",)
    for event, data in et.iterparse(path, events=events):
      match event:
        case "start":
          if root is None:
            assert isinstance(data, et.Element)
            root = data
        case "start-ns":
          assert isinstance(data, tuple)
          prefix, uri = data
          collected_ns[prefix] = uri
    assert root is not None
    if populate_nsmap:
      for prefix, uri in collected_ns.items():
        self.register_namespace(prefix, uri)
    return root

  def from_bytes(
    self,
    data: bytes,
    encoding: str | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> et.Element:
    enc = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    fake_file = BytesIO(data)
    return self.parse(fake_file, encoding=enc, nsmap=nsmap, populate_nsmap=populate_nsmap)

  def from_string(
    self,
    data: str,
    encoding: str | None = None,
    *,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> et.Element:
    enc = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return self.parse(
      BytesIO(data.encode(enc)), encoding=enc, nsmap=nsmap, populate_nsmap=populate_nsmap
    )

  def write(
    self,
    element: et.Element,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    encoding: str | None = None,
    doctype: str | None = "<!DOCTYPE tmx SYSTEM 'tmx14.dtd'>",
  ) -> None:
    enc = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    self.iterwrite(
      path,
      [element],
      encoding=enc,
      max_number_of_elements_in_buffer=1,
      write_xml_declaration=True,
      doctype=doctype,
    )

  def clear(self, element: et.Element) -> None:
    element.clear()

  def to_bytes(
    self,
    element: et.Element,
    encoding: str | None = None,
    *,
    self_closing: bool = False,
    strip_tail: bool = False,
  ) -> bytes:
    enc = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""
    return et.tostring(element, encoding=enc, xml_declaration=False, with_tail=not strip_tail)

  def to_string(
    self, element: et.Element, *, self_closing: bool = False, strip_tail: bool = False
  ) -> str:
    if strip_tail and element.tail is not None:
      element = copy(element)
      element.tail = None
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""
    # for some reason mypy thinks lxml returns bytes when it should return str if encoding="unicode"
    return cast(str, et.tostring(element, encoding="unicode", xml_declaration=False))

  def iterparse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> Generator[et.Element]:
    if tag_filter is not None:
      tag_set = self._resolve_tag_filter(tag_filter, nsmap)
    else:
      tag_set = None
    collected_ns: dict[str, str] = {}
    elements_pending_yield: list[et.Element] = []
    for event, data in et.iterparse(path, events=("start", "end", "start-ns")):
      match event:
        case "start-ns":
          assert isinstance(data, tuple)
          prefix, uri = data
          collected_ns[prefix] = uri
        case "start":
          assert isinstance(data, et.Element)
          elem = data
          if tag_set is None or elem.tag in tag_set:
            elements_pending_yield.append(elem)
        case "end":
          assert isinstance(data, et.Element)
          elem = data
          if not elements_pending_yield:
            elem.clear()
            continue
          if elem is elements_pending_yield[-1]:
            elements_pending_yield.pop()
            if populate_nsmap:
              for prefix, uri in collected_ns.items():
                if prefix not in self._global_nsmap:
                  self.register_namespace(prefix, uri)
            yield elem
            if not elements_pending_yield:
              elem.clear()

  def _resolve_tag_filter(
    self, tag_filter: str | bytes | Iterable[str | bytes], nsmap: MutableMapping[str, str] | None
  ) -> set[str]:
    result: set[str] = set()
    if isinstance(tag_filter, bytes):
      result.add(
        resolve(
          tag_filter.decode(self.default_encoding), global_nsmap=self._global_nsmap, nsmap=nsmap
        ).clark
      )
    elif isinstance(tag_filter, str):
      result.add(resolve(tag_filter, global_nsmap=self._global_nsmap, nsmap=nsmap).clark)
    else:
      for item in tag_filter:
        if isinstance(item, bytes):
          result.add(
            resolve(
              item.decode(self.default_encoding), global_nsmap=self._global_nsmap, nsmap=nsmap
            ).clark
          )
        else:
          result.add(resolve(item, global_nsmap=self._global_nsmap, nsmap=nsmap).clark)
    return result
