from collections.abc import Generator, Iterable, Iterator, Mapping
from copy import copy
from logging import Logger
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
  """XML backend using lxml for improved performance.

  This backend provides XML operations using the lxml library,
  which is significantly faster than the standard library for
  large files. Requires lxml to be installed.

  Parameters
  ----------
  nsmap : Mapping[str, str] | None
      Custom namespace prefix to URI mappings.
  logger : Logger | None
      Logger instance for debug and error messages.
  default_encoding : str | None
      Default encoding for XML operations. Defaults to "utf-8".
  policy : XmlPolicy | None
      Policy configuration for error handling behavior.

  Examples
  --------
  .. code-block:: python

      from hypomnema.xml.backends.lxml import LxmlBackend

      backend = LxmlBackend()
      root = backend.parse("input.xml")
      print(backend.get_tag(root))
  """

  __slots__: tuple[str, ...] = tuple()

  def __init__(
    self,
    nsmap: Mapping[str, str] | None = None,
    logger: Logger | None = None,
    default_encoding: str | None = None,
    policy: XmlPolicy | None = None,
  ):
    """Initialize the LxmlBackend.

    Parameters
    ----------
    nsmap : Mapping[str, str] | None
        Custom namespace prefix to URI mappings.
    logger : Logger | None
        Logger instance.
    default_encoding : str | None
        Default encoding for XML operations.
    policy : XmlPolicy | None
        Policy for error handling.
    """
    super().__init__(nsmap, logger, default_encoding, policy)

  @overload
  def get_tag(self, element: et._Element, *, as_qname: Literal[True]) -> QName: ...
  @overload
  def get_tag(self, element: et._Element, *, as_qname: Literal[False] = False) -> str: ...
  def get_tag(self, element: et._Element, *, as_qname: bool = False) -> str | QName:
    """Get the tag name of an element.

    Parameters
    ----------
    element : et._Element
        The XML element.
    as_qname : bool
        If True, return QName object. If False, return string.

    Returns
    -------
    str | QName
        The tag name of the element.
    """
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
    """Create a new XML element.

    Parameters
    ----------
    tag : str | QNameLike
        Tag name for the element.
    attributes : Mapping[str, str] | None
        Optional attribute name-value pairs.

    Returns
    -------
    et._Element
        The created element.
    """
    if attributes is None:
      attributes = {}
    _attributes = {QName(key, nsmap=self.nsmap).text: value for key, value in attributes.items()}
    _tag = QName(tag, nsmap=self.nsmap)
    return et.Element(_tag.qualified_name, attrib=_attributes)

  def append_child(self, parent: et._Element, child: et._Element) -> None:
    """Append a child element to a parent.

    Parameters
    ----------
    parent : et._Element
        Parent element.
    child : et._Element
        Child element to append.
    """
    parent.append(child)

  @overload
  def get_attribute(self, element: et._Element, attribute_name: str) -> str | None: ...
  @overload
  def get_attribute[TypeOfDefault](
    self, element: et._Element, attribute_name: str, *, default: TypeOfDefault
  ) -> str | TypeOfDefault: ...
  def get_attribute[TypeOfDefault](
    self, element: et._Element, attribute_name: str, *, default: TypeOfDefault | None = None
  ) -> str | TypeOfDefault | None:
    """Get an attribute value from an element.

    Parameters
    ----------
    element : et._Element
        The XML element.
    attribute_name : str
        Name of the attribute.
    default : TypeOfDefault | None
        Default value if attribute is not present.

    Returns
    -------
    str | TypeOfDefault | None
        The attribute value, or default if not found.
    """
    _key = QName(attribute_name, nsmap=self.nsmap)
    return element.get(_key.text, default)

  def set_attribute(
    self, element: et._Element, attribute_name: str | QNameLike, attribute_value: str
  ) -> None:
    """Set an attribute on an element.

    Parameters
    ----------
    element : et._Element
        The XML element.
    attribute_name : str | QNameLike
        Name of the attribute.
    attribute_value : str
        Value to set.
    """
    _key = QName(attribute_name, nsmap=self.nsmap)
    element.set(_key.text, attribute_value)

  def delete_attribute(self, element: et._Element, attribute_name: str | QNameLike) -> None:
    """Delete an attribute from an element.

    Parameters
    ----------
    element : et._Element
        The XML element.
    attribute_name : str | QNameLike
        Name of the attribute to delete.
    """
    _key = QName(attribute_name, nsmap=self.nsmap)
    element.attrib.pop(_key.text, None)

  def get_attribute_map(self, element: et._Element) -> dict[str, str]:
    """Get all attributes of an element as a dictionary.

    Parameters
    ----------
    element : et._Element
        The XML element.

    Returns
    -------
    dict[str, str]
        Mapping of attribute names to values.
    """
    return {k: v for k, v in element.attrib.items()}

  def get_text(self, element: et._Element) -> str | None:
    """Get text content of an element.

    Parameters
    ----------
    element : et._Element
        The XML element.

    Returns
    -------
    str | None
        Text content, or None if empty.
    """
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
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Generator[et._Element]:
    """Iterate over child elements.

    Parameters
    ----------
    element : et._Element
        Parent element.
    tag_filter : str | QNameLike | Iterable[str | QNameLike] | None
        Optional tag filter(s) to match.

    Returns
    -------
    Generator[et._Element]
        Generator yielding matching child elements.
    """
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    for child in element:
      if tag_set is None or child.tag in tag_set:
        yield child

  def parse(self, path: str | PathLike, encoding: str | None = None) -> et._Element:
    """Parse an XML file and return the root element.

    Uses a parser with recover=True and resolve_entities=False
    for security and robustness.

    Parameters
    ----------
    path : str | PathLike
        Path to the XML file.
    encoding : str | None
        Optional encoding override.

    Returns
    -------
    et._Element
        Root element of the parsed document.
    """
    path = make_usable_path(path, mkdir=False)
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    root = et.parse(
      path, parser=et.XMLParser(encoding=encoding, recover=True, resolve_entities=False)
    ).getroot()
    return root

  def write(self, element: et._Element, path: str | PathLike, encoding: str | None = None) -> None:
    """Write an element to a file.

    Parameters
    ----------
    element : et._Element
        Root element to write.
    path : str | PathLike
        Path to write the file.
    encoding : str | None
        Optional encoding override.
    """
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
    """Serialize an element to bytes.

    Parameters
    ----------
    element : et._Element
        Element to serialize.
    encoding : str | None
        Optional encoding override.
    self_closing : bool
        If True, output as self-closing tag if empty.

    Returns
    -------
    bytes
        Serialized XML as bytes.
    """
    if not self_closing and element.text is None:
      element = copy(element)
      element.text = ""
    encoding = normalize_encoding(encoding) if encoding is not None else self.default_encoding
    return et.tostring(element, encoding=encoding, xml_declaration=False)

  def iterparse(
    self,
    path: str | PathLike,
    tag_filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  ) -> Iterator[et._Element]:
    """Parse XML incrementally, yielding matching elements.

    Parameters
    ----------
    path : str | PathLike
        Path to the XML file.
    tag_filter : str | QNameLike | Iterable[str | QNameLike] | None
        Tag(s) to match and yield.

    Returns
    -------
    Iterator[et._Element]
        Iterator over matching elements.
    """
    tag_set = prep_tag_set(tag_filter, nsmap=self.nsmap) if tag_filter is not None else None
    ctx = et.iterparse(path, events=("start", "end"))
    # need to ignore mypy error here because lxml typing
    # doesn't narrow to only "start" and "end" events even
    # when setting events to ("start", "end")
    yield from self._iterparse(ctx, tag_set)  # type: ignore[arg-type]
