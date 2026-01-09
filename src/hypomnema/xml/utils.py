from unicodedata import category
from pathlib import Path
from hypomnema.base.errors import XmlSerializationError, InvalidTagError
from hypomnema.xml.policy import SerializationPolicy, DeserializationPolicy
from codecs import lookup
from collections.abc import Mapping, Iterable
from logging import Logger
from typing import TypeIs, Any
from encodings import normalize_encoding as python_normalize_encoding
from os import PathLike


def normalize_encoding(encoding: str | None) -> str:
  """Normalize an encoding name to its canonical Python codec name.

  This function:
  - Defaults to ``"utf-8"`` if ``encoding`` is None.
  - Converts "unicode" to "utf-8".
  - Uses Python's codec normalization for alias resolution.
  - Validates the encoding is known to Python.

  Parameters
  ----------
  encoding : str | None
      The encoding name to normalize. Can be a codec name, alias, or None.

  Returns
  -------
  str
      The canonical encoding name (lowercase).

  Raises
  ------
  ValueError
      If the encoding is not recognized by Python's codec registry.

  """
  normalized_encoding = python_normalize_encoding(encoding or "utf-8").lower()
  if encoding == "unicode":
    normalized_encoding = "utf-8"
  try:
    codec = lookup(normalized_encoding)
    return codec.name
  except LookupError as e:
    raise ValueError(f"Unknown encoding: {normalized_encoding}") from e


def prep_tag_set(
  tags: str | QName | Iterable[str | QName] | None, nsmap: Mapping[str | None, str]
) -> set[str] | None:
  """Convert tag names to a set of fully qualified names.

  This function normalizes tag names and converts them to their fully
  qualified form (Clark notation) using the provided namespace map.

  Parameters
  ----------
  tags : str | Collection[str] | None
      A single tag name, a collection of tag names, or None.
      Tag names can be local names, prefixed names (``prefix:localname``),
      or fully qualified names (``{uri}localname``).
  nsmap : dict[str | None, str] | None, optional
      Namespace map from prefix to URI. Used to resolve prefixed names.
      Defaults to an empty dictionary.

  Returns
  -------
  set[str] | None
      A set of fully qualified tag names, or None if ``tags`` was None
      or empty.

  """
  _nsmap = dict() if nsmap is None else nsmap
  if not tags:
    return None
  if isinstance(tags, str):
    qname = QName(tags, _nsmap)
    return {qname.qualified_name}
  elif isinstance(tags, QName):
    return {tags.qualified_name}
  else:
    result = set()
    for tag in tags:
      if isinstance(tag, str):
        qname = QName(tag, _nsmap)
        result.add(qname.qualified_name)
      elif isinstance(tag, QName):
        result.add(tag.qualified_name)
      else:
        raise TypeError(f"Unexpected tag type: {type(tag)}")
    return result


def assert_object_type[ExpectedType](
  obj: Any, expected_type: type[ExpectedType], *, logger: Logger, policy: SerializationPolicy
) -> TypeIs[ExpectedType]:
  """Assert that an object is of the expected type.

  This function checks the type of an object against an expected type,
  logs a diagnostic message if mismatched, and optionally raises an
  exception based on the policy.

  Parameters
  ----------
  obj : Any
      The object to check.
  expected_type : type[ExpectedType]
      The expected type of the object.
  logger : Logger
      Logger instance for diagnostic messages.
  policy : SerializationPolicy
      Policy object controlling behavior when types mismatch.

  Returns
  -------
  TypeIs[ExpectedType]
      True if the object is of the expected type, False otherwise.

  Raises
  ------
  XmlSerializationError
      If ``policy.invalid_object_type.behavior`` is ``"raise"``.

  """
  if not isinstance(obj, expected_type):
    logger.log(
      policy.invalid_object_type.log_level,
      "object of type %r is not an instance of %r",
      obj.__class__.__name__,
      expected_type.__name__,
    )
    if policy.invalid_object_type.behavior == "raise":
      raise XmlSerializationError(
        f"object of type {obj.__class__.__name__!r} is not an instance of {expected_type.__name__!r}"
      )
    return False
  return True


def check_tag(tag: str, expected_tag: str, logger: Logger, policy: DeserializationPolicy) -> None:
  """Check if a tag matches the expected tag.

  This function compares a tag against an expected value, logs a
  diagnostic message if mismatched, and optionally raises an exception
  based on the policy.

  Parameters
  ----------
  tag : str
      The actual tag name found.
  expected_tag : str
      The expected tag name.
  logger : Logger
      Logger instance for diagnostic messages.
  policy : DeserializationPolicy
      Policy object controlling behavior when tags mismatch.

  Raises
  ------
  InvalidTagError
      If ``policy.invalid_tag.behavior`` is ``"raise"``.

  """
  if not tag == expected_tag:
    logger.log(
      policy.invalid_tag.log_level, "Incorrect tag: expected %s, got %s", expected_tag, tag
    )
    if policy.invalid_tag.behavior == "raise":
      raise InvalidTagError(f"Incorrect tag: expected {expected_tag}, got {tag}")


def make_usable_path(path: str | bytes | PathLike, *, mkdir: bool = True) -> Path:
  """Convert a path to a normalized, usable Path object.

  This function normalizes paths by:
  - Decoding bytes paths to strings.
  - Expanding user home directory shortcuts (``~``).
  - Resolving symbolic links to their actual path.
  - Optionally creating parent directories.

  Parameters
  ----------
  path : str | bytes | PathLike
      The path to normalize.
  mkdir : bool, optional
      If True (default), create any missing parent directories.
      If False, only return the normalized path without creating directories.

  Returns
  -------
  Path
      A normalized Path object ready for file operations.

  """
  path = path.decode() if isinstance(path, bytes) else path
  final_path = Path(path).expanduser()
  if final_path.is_symlink():
    final_path = final_path.resolve()
  if mkdir:
    final_path.parent.mkdir(parents=True, exist_ok=True)
  return final_path


_NAME_START_CATEGORIES = {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}
_NAME_CHAR_CATEGORIES = _NAME_START_CATEGORIES | {"Nd", "Mc", "Mn", "Pc"}


def _is_letter(char: str) -> bool:
  """True if char is an XML 1.0 Letter (Name-start)."""
  cat = category(char)
  if cat in _NAME_START_CATEGORIES:
    return True
  return char == "_"  # ASCII underscore is explicitly allowed


def _is_ncname_char(char: str) -> bool:
  """True if char is allowed anywhere in an NCName after the first char."""
  cat = category(char)
  if cat in _NAME_CHAR_CATEGORIES:
    return True
  return char in (".", "-", "_")


def is_ncname(name: str) -> bool:
  """Return True if *name* is a valid XML 1.0 NCName.

  An NCName (non-colonized name) is a name that cannot contain a colon.
  It must start with a letter or underscore, and subsequent characters
  can be letters, digits, underscores, hyphens, or periods.

  Parameters
  ----------
  name : str
      The name to validate.

  Returns
  -------
  bool
      True if the name is a valid NCName, False otherwise.

  Notes
  -----
  This implements the NCName production from XML Namespaces 1.0:
  NCName ::= NameStartChar (NameChar)*

  The ASCII underscore (``_``) is explicitly allowed as a NameStartChar
  even though it's not a Letter category in Unicode.

  See Also
  --------
  _is_letter : Check if a character is a valid XML NameStartChar.
  _is_ncname_char : Check if a character is a valid XML NameChar.

  """
  """Return True if *name* is a valid XML 1.0 NCName."""
  if not name:
    return False
  if not _is_letter(name[0]):
    return False
  return all(_is_ncname_char(ch) for ch in name[1:])


def _split_qualified_tag(
  tag: str, nsmap: Mapping[str | None, str]
) -> tuple[str | None, str | None, str]:
  uri, localname = tag[1:].split("}", 1)
  if not is_ncname(localname):
    raise ValueError(f"NCName {localname} is not a valid xml localname")
  for prefix, value in nsmap.items():
    if value == uri:
      return uri, prefix, localname
  return uri, None, localname


def _split_prefixed_tag(
  tag: str, nsmap: Mapping[str | None, str]
) -> tuple[str | None, str | None, str]:
  prefix, localname = tag.split(":", 1)
  if not is_ncname(localname):
    raise ValueError(f"NCName {localname} is not a valid xml localname")
  if not is_ncname(prefix):
    raise ValueError(f"NCName {prefix} is not a valid xml prefix")
  return nsmap.get(prefix), prefix, localname


class QName:
  """Represents a qualified XML name with namespace information.

  This class parses and stores the components of a qualified XML name,
  supporting both Clark notation (``{uri}localname``) and prefixed
  notation (``prefix:localname``).

  Attributes
  ----------
  uri : str | None
      The namespace URI, or None if no namespace is declared.
  prefix : str | None
      The namespace prefix, or None if using default namespace or no namespace.
  local_name : str
      The local (unqualified) name component.

  Notes
  -----
  When a tag is provided in prefixed form (``prefix:localname``), the class
  looks up the URI from the provided namespace map. If the prefix is not
  found in the map, the prefix is preserved as-is and URI remains None.

  Examples
  --------
  >>> nsmap = {"tmx": "http://www.lisa.org/TMX14"}
  >>> q = QName("{http://www.lisa.org/TMX14}header", nsmap)
  >>> q.uri
  'http://www.lisa.org/TMX14'
  >>> q.local_name
  'header'
  >>> q.qualified_name
  '{http://www.lisa.org/TMX14}header'

  >>> q2 = QName("tmx:header", nsmap)
  >>> q2.uri
  'http://www.lisa.org/TMX14'
  >>> q2.prefixed_name
  'tmx:header'

  """

  uri: str | None
  """The namespace URI."""
  prefix: str | None
  """The namespace prefix."""
  local_name: str
  """The local name."""

  def __init__(
    self, tag: str | bytes | bytearray | QName, nsmap: Mapping[str | None, str], encoding: str = "utf-8"
  ) -> None:
    """Initialize a QName from a tag string and namespace map.

    Parameters
    ----------
    tag : str | bytes | bytearray
        The tag name to parse. Can be in Clark notation (``{uri}localname``),
        prefixed notation (``prefix:localname``), or a plain local name.
    nsmap : Mapping[str | None, str]
        Namespace map from prefix to URI. Used to resolve prefixed names.
    encoding : str, optional
        Encoding to use when decoding bytes or bytearray tags.
        Defaults to ``"utf-8"``.

    Raises
    ------
    TypeError
        If ``tag`` is not a str, bytes, or bytearray.
    ValueError
        If the local name or prefix is not a valid NCName.

    """
    if isinstance(tag, str):
      tag = tag
    elif isinstance(tag, (bytes, bytearray)):
      tag = tag.decode(encoding)
    elif isinstance(tag, QName):
      self.uri, self.prefix, self.local_name = tag.uri, tag.prefix, tag.local_name
      return
    else:
      raise TypeError(f"Unexpected tag type: {type(tag)}")

    if tag[0] == "{":
      self.uri, self.prefix, self.local_name = _split_qualified_tag(tag, nsmap)
    elif ":" in tag:
      self.uri, self.prefix, self.local_name = _split_prefixed_tag(tag, nsmap)
    else:
      self.uri, self.prefix, self.local_name = None, None, tag

  @property
  def qualified_name(self) -> str:
    """The fully qualified name in Clark notation.

    Returns
    -------
    str
        If a namespace URI is set, returns ``{uri}local_name``.
        Otherwise, returns just the ``local_name``.

    Examples
    --------
    >>> nsmap = {"tmx": "http://www.lisa.org/TMX14"}
    >>> QName("{http://www.lisa.org/TMX14}header", nsmap).qualified_name
    '{http://www.lisa.org/TMX14}header'
    >>> QName("header", nsmap).qualified_name
    'header'

    """
    if self.uri is None:
      return self.local_name
    return f"{{{self.uri}}}{self.local_name}"

  @property
  def prefixed_name(self) -> str:
    """The prefixed name using the registered prefix.

    Returns
    -------
    str
        If a prefix is set, returns ``prefix:local_name``.
        Otherwise, returns just the ``local_name``.

    Notes
    -----
    This property uses the prefix that was looked up from the namespace
    map, not necessarily the prefix that was in the original tag string.

    Examples
    --------
    >>> nsmap = {"tmx": "http://www.lisa.org/TMX14"}
    >>> QName("{http://www.lisa.org/TMX14}header", nsmap).prefixed_name
    'tmx:header'
    >>> QName("header", nsmap).prefixed_name
    'header'

    """
    if self.prefix is None:
      return self.local_name
    return f"{self.prefix}:{self.local_name}"
