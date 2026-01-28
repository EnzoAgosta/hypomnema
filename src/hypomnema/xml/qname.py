from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from hypomnema.base.errors import NamespaceError
from hypomnema.xml.utils import is_ncname, is_valid_uri

__all__ = ["QName", "QNameLike"]


@runtime_checkable
class QNameLike(Protocol):
  """Protocol for objects that can be used as QNames.

  Any object with a `text` attribute can be used as a QNameLike.
  This allows QName to be constructed from other QName instances
  or compatible objects.

  Examples
  --------
  .. code-block:: python

      class MyQName:
        text = "{http://example.com}tag"


      qname = QName(MyQName())  # Works via protocol
  """

  @property
  def text(self) -> str: ...


class QName:
  """Represents an XML qualified name with namespace support.

  Parses and manages XML qualified names in various notations:
  - Clark notation: {http://example.com}tag
  - Prefixed notation: ns:tag
  - Simple names: tag

  Parameters
  ----------
  tag : str | QNameLike
      The tag name to parse. Can be Clark notation, prefixed,
      or a simple name.
      If prefixed or in Clark notation, nsmap is required to resolve
      prefixes and URIs.
  nsmap : Mapping[str | None, str] | None
      Namespace prefix to URI mapping for resolving prefixes.

  Attributes
  ----------
  uri : str | None
      The namespace URI, or None for unprefixed names.
  prefix : str | None
      The namespace prefix, or None for unprefixed names.
  local_name : str
      The local part of the name (without prefix/URI).

  Raises
  ------
  ValueError
      If the tag is empty or contains invalid characters.
  NamespaceError
      If nsmap is required but not provided or missing a prefix.

  Examples
  --------
  .. code-block:: python

      # Simple name
      qname = QName("tag")
      print(qname.local_name)  # "tag"

      # Clark notation
      qname = QName("{http://example.com}tag")
      print(qname.uri)  # "http://example.com"

      # With namespace map
      nsmap = {"ns": "http://example.com"}
      qname = QName("ns:tag", nsmap=nsmap)
      print(qname.prefix)  # "ns"
  """

  uri: str | None
  prefix: str | None
  local_name: str

  def __init__(
    self, tag: str | QNameLike, *, nsmap: Mapping[str | None, str] | None = None
  ) -> None:
    if isinstance(tag, QNameLike):
      tag = tag.text
    if not tag:
      raise ValueError("tag must not be empty")
    self.prefix = None
    self.uri = None

    # Clark notation {uri}localname
    if tag[0] == "{":
      ns, tag = tag[1:].split("}", 1)
      if not is_valid_uri(ns):
        raise ValueError(f"{ns} is not a valid xml uri")
      if not is_ncname(tag):
        raise ValueError(f"{tag} is not a valid xml localname")
      self.uri = ns
      self.local_name = tag
      if nsmap is not None:
        for prefix, uri in nsmap.items():
          if uri == ns:
            self.prefix = prefix
            break
        else:
          raise NamespaceError(f"{ns} is not registered")
      else:
        raise NamespaceError("nsmap is required to resolve uri tags")

    # Prefixed notation prefix:localname (usually never given by xml libraries)
    elif tag.count(":") == 1:
      prefix, localname = tag.split(":", 1)
      if not is_ncname(prefix):
        raise ValueError(f"NCName {prefix} is not a valid xml prefix")
      if not is_ncname(localname):
        raise ValueError(f"NCName {localname} is not a valid xml localname")
      self.prefix = prefix
      self.local_name = localname
      if nsmap is not None:
        for _prefix, uri in nsmap.items():
          if _prefix == prefix:
            self.uri = uri
            break
        else:
          raise NamespaceError(f"{prefix} is not registered")
      else:
        raise NamespaceError("nsmap is required to resolve prefixed tags")
    else:
      if not is_ncname(tag):
        raise ValueError(f"{tag} is not a valid xml tag")
      self.local_name = tag
      self.uri = None
      self.prefix = None

  @property
  def qualified_name(self) -> str:
    """The qualified name in Clark notation.

    Returns the name in {uri}localname format if a URI is present,
    otherwise returns just the local name.

    Returns
    -------
    str
      The qualified name.

    Examples
    --------
    .. code-block:: python

        qname = QName("{http://example.com}tag")
        print(qname.qualified_name)  # "{http://example.com}tag"

        qname = QName("tag")
        print(qname.qualified_name)  # "tag"
    """
    if self.uri is None:
      return self.local_name
    return "{" + self.uri + "}" + self.local_name

  @property
  def prefixed_name(self) -> str:
    """The qualified name in prefixed notation.

    Returns the name in prefix:localname format if a prefix is present,
    otherwise returns just the local name.

    Returns
    -------
    str
      The prefixed name.

    Examples
    --------
    .. code-block:: python

        nsmap = {"ns": "http://example.com"}
        qname = QName("ns:tag", nsmap=nsmap)
        print(qname.prefixed_name)  # "ns:tag"

        qname = QName("tag")
        print(qname.prefixed_name)  # "tag"
    """
    if self.prefix is None:
      return self.local_name
    return self.prefix + ":" + self.local_name

  @property
  def text(self) -> str:
    """The qualified name (same as qualified_name).

    This property exists to satisfy the QNameLike protocol.

    Returns
    -------
    str
      The qualified name.
    """
    return self.qualified_name

  def __str__(self) -> str:
    """Return the qualified name as a string."""
    return self.qualified_name

  def __repr__(self) -> str:
    """Return a string representation of the QName."""
    return f"QName({self.qualified_name!r})"
