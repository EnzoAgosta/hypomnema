"""`lxml.etree` implementation of the shared XML backend contract.

`LxmlBackend` provides the same public :class:`XmlBackend` interface as the
standard library backend while using `lxml`'s parser and serializer primitives
under the covers.

Parsing uses a single-pass ``iterparse`` with ``start`` and ``start-ns``
events, collecting namespace declarations as they are encountered. Name
resolution uses successive lookup — per-call ``nsmap`` first, then
``global_nsmap`` — via :func:`resolve` and :func:`format_notation`. Where
relevant, the element's own ``nsmap`` attribute is merged into a fresh dict
(non-mutating) so lxml-specific namespace declarations are visible to the
resolution layer.
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

  This backend keeps the same behavioral contract as :class:`StandardBackend`
  but uses `lxml`'s element type, parser configuration, and streaming writer.

  Where lxml exposes per-element namespace maps (``element.nsmap``), this
  backend merges them into a fresh dict alongside the caller-provided ``nsmap``
  so that prefix resolution sees in-scope declarations without mutating the
  caller's dict.

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
    """Return the element's tag in the requested notation.

    Merges ``element.nsmap`` into the resolution map so lxml-specific
    namespace declarations are visible.
    """
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
    """Create an ``lxml.etree._Element`` with names resolved to Clark notation.

    If the resolved tag carries a prefix and URI, an lxml ``nsmap`` is passed
    to the element constructor so lxml records the namespace declaration.
    """
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
    """Append *child* as a subelement of *parent*."""
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
    """Return the value of attribute *name*, or *default* if missing.

    Merges ``element.nsmap`` into the resolution map.
    """
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
    """Set attribute *name* to *value*, merging ``element.nsmap`` for resolution."""
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
    """Remove attribute *name* if it exists, merging ``element.nsmap`` for resolution."""
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
    """Return all attributes as ``{formatted_name: value}``, merging ``element.nsmap``."""
    element_nsmap = {k: v for k, v in element.nsmap.items() if k is not None}
    merged_nsmap: MutableMapping[str, str] = (
      {**nsmap, **element_nsmap} if nsmap is not None else element_nsmap
    )
    return {
      format_notation(key, notation, global_nsmap=self._global_nsmap, nsmap=merged_nsmap): value
      for key, value in element.attrib.items()
    }

  def get_text(self, element: et._Element) -> str | None:
    """Return the text content of *element*, or ``None``."""
    return element.text

  def set_text(self, element: et._Element, text: str | None) -> None:
    """Set the text content of *element*."""
    element.text = text

  def get_tail(self, element: et._Element) -> str | None:
    """Return the tail text of *element*, or ``None``."""
    return element.tail

  def set_tail(self, element: et._Element, tail: str | None) -> None:
    """Set the tail text of *element*."""
    element.tail = tail

  def iter_children(
    self,
    element: et._Element,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
  ) -> Generator[et._Element]:
    """Yield direct children of *element*, optionally filtered by *tag_filter*.

    When *tag_filter* is not None, ``element.nsmap`` is merged into the
    namespace resolution map so lxml-specific declarations are visible.
    """
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
    """Parse an XML document from *path* and return the root element.

    Uses a single-pass ``iterparse``. If *populate_nsmap* is True,
    encountered namespace declarations are registered into the backend's
    ``global_nsmap``.
    """
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
    """Parse an XML document from a ``bytes`` object via :meth:`parse`."""
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
    """Parse an XML document from a ``str`` via :meth:`parse`."""
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
    """Write *element* to *path* as an XML document via :meth:`iterwrite`."""
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
    """Remove all children, attributes, and text from *element*."""
    element.clear()

  def to_bytes(
    self,
    element: et.Element,
    encoding: str | None = None,
    *,
    self_closing: bool = False,
    strip_tail: bool = False,
  ) -> bytes:
    """Serialize *element* to bytes.

    Args:
        element: The element to serialize.
        encoding: Character encoding (defaults to ``default_encoding``).
        self_closing: If True, empty elements render as ``<tag/>``.
        strip_tail: If True, remove tail text before serializing.
    """
    enc = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    if strip_tail and element.tail is not None:
      element = copy(element)
      element.tail = None
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""
    return et.tostring(element, encoding=enc, xml_declaration=False, with_tail=not strip_tail)

  def to_string(
    self, element: et.Element, *, self_closing: bool = False, strip_tail: bool = False
  ) -> str:
    """Serialize *element* to a Unicode string (encoding ``"unicode"``).

    Args:
        element: The element to serialize.
        self_closing: If True, empty elements render as ``<tag/>``.
        strip_tail: If True, remove tail text before serializing.
    """
    if strip_tail and element.tail is not None:
      element = copy(element)
      element.tail = None
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""
    return cast(str, et.tostring(element, encoding="unicode", xml_declaration=False))

  def iterparse(
    self,
    path: str | PathLike[str] | PathLike[bytes] | BinaryIO,
    *,
    tag_filter: str | bytes | Iterable[str | bytes] | None = None,
    nsmap: MutableMapping[str, str] | None = None,
    populate_nsmap: bool = False,
  ) -> Generator[et.Element]:
    """Incrementally parse *path*, yielding elements matching *tag_filter*.

    Uses a single-pass ``iterparse`` with ``start``, ``end``, and
    ``start-ns`` events. Elements whose closing tag is reached while no
    ancestor is pending are cleared to keep memory bounded.

    If *populate_nsmap* is True, encountered namespace declarations are
    registered into the backend's ``global_nsmap``.
    """
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
    """Convert a tag filter specification to a set of Clark-notation tag names."""
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
