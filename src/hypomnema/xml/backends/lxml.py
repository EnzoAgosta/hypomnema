from collections.abc import Generator, Iterable, Mapping
from copy import copy
from os import PathLike
from typing import Literal, overload
import lxml.etree as et

from hypomnema.xml.backends.base import TagLike, XmlBackend
from hypomnema.xml.utils import QNameLike, make_usable_path, normalize_encoding


class LxmlBackend(XmlBackend[et._Element]):
  __slots__: tuple[str, ...] = tuple()

  def __init__(self, logger=None, default_encoding=None, *, namespace_handler=None):
    super().__init__(logger, default_encoding, namespace_handler=namespace_handler)

  def get_tag(
    self, element: et._Element, notation: Literal["prefixed", "qualified", "local"] = "local"
  ) -> str:
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
    key = self.normalize_tag_name(attribute_name)
    return element.get(key, default)

  def set_attribute(
    self, element: et._Element, attribute_name: TagLike, attribute_value: str
  ) -> None:
    key = self.normalize_tag_name(attribute_name)
    element.set(key, attribute_value)

  def delete_attribute(self, element: et._Element, attribute_name: TagLike) -> None:
    key = self.normalize_tag_name(attribute_name)
    element.attrib.pop(key, None)

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
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[et._Element]:
    if not len(element):
      return
    tag_set = self.prep_tag_set(tag_filter) if tag_filter is not None else None
    for child in element:
      child_tag = self.get_tag(child)
      if tag_set is None or child_tag in tag_set:
        yield child

  def parse(self, path: str | PathLike, encoding: str | None = None) -> et._Element:
    encoding = normalize_encoding(encoding)
    source = make_usable_path(path, mkdir=False)
    return et.parse(
      source, parser=et.XMLParser(encoding=encoding, recover=True, resolve_entities=False)
    ).getroot()

  def write(self, element: et._Element, path: str | PathLike, encoding: str | None = None) -> None:
    encoding = normalize_encoding(encoding)
    source = make_usable_path(path, mkdir=True)
    with et.xmlfile(source, encoding=encoding) as f:
      f.write_declaration()
      f.write_doctype("<!DOCTYPE tmx SYSTEM 'tmx14.dtd'>")
      f.write(element)

  def clear(self, element: et._Element) -> None:
    element.clear()

  def to_bytes(
    self, element: et._Element, encoding: str | None = None, self_closing: bool = False
  ) -> bytes:
    encoding = normalize_encoding(encoding)
    if not self_closing:
      if element.text is None:
        element = copy(element)
        element.text = ""

    return et.tostring(element, encoding=encoding, xml_declaration=False)

  def iterparse(
    self,
    path: str | PathLike,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[et._Element]:
    source = make_usable_path(path, mkdir=False)
    ctx = et.iterparse(source, events=("start", "end"))
    _tag_set = self.prep_tag_set(tag_filter) if tag_filter is not None else None
    # Even though we restrict the events to "start" and "end" at runtime
    # lxml's typing doesn't narrow to only "start" and "end" events
    # and actually includes "comment" and "pi" in the return type.
    yield from self._iterparse(ctx, _tag_set)  # type: ignore[arg-type]
