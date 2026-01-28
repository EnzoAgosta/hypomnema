from codecs import lookup
from collections.abc import Iterable
from encodings import normalize_encoding as python_normalize_encoding
from logging import Logger
from os import PathLike
from pathlib import Path
from re import IGNORECASE, compile
from typing import TYPE_CHECKING, Any, Mapping, TypeIs
from unicodedata import category

from hypomnema.base.errors import InvalidTagError, XmlSerializationError
from hypomnema.xml.policy import XmlPolicy

if TYPE_CHECKING:
  from hypomnema.xml.qname import QNameLike

__all__ = [
  "prep_tag_set",
  "make_usable_path",
  "normalize_encoding",
  "is_ncname",
  "is_valid_uri",
  "check_tag",
]


def normalize_encoding(encoding: str) -> str:
  """Normalize and validate an encoding name.

  Converts the encoding name to a standard form and validates
  that it is a valid Python codec.

  Special case for "unicode", which gets converted to "utf-8".

  Parameters
  ----------
  encoding : str
      The encoding name to normalize.

  Returns
  -------
  str
      The normalized encoding name.

  Raises
  ------
  ValueError
      If the encoding is not recognized.

  Examples
  --------
  .. code-block:: python

      normalize_encoding("UTF-8")  # "utf-8"
      normalize_encoding("unicode")  # "utf-8"
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
  tags: str | QNameLike | Iterable[str | QNameLike],
  *,
  nsmap: Mapping[str | None, str] | None = None,
) -> set[str]:
  """Prepare a set of qualified tag names.

  Converts tags (strings or QNameLike objects) into their qualified
  form and returns as a set for efficient lookup.

  Parameters
  ----------
  tags : str | QNameLike | Iterable[str | QNameLike]
      Tag(s) to prepare. Can be a single tag or iterable of tags.
  nsmap : Mapping[str | None, str] | None
      Namespace prefix to URI mapping for resolving prefixes.

  Returns
  -------
  set[str]
      Set of qualified tag names.

  Examples
  --------
  .. code-block:: python

      nsmap = {"ns": "http://example.com"}
      tags = prep_tag_set(["ns:tag1", "ns:tag2"], nsmap=nsmap)
      # {\"{http://example.com}tag1\", \"{http://example.com}tag2\"}
  """
  from hypomnema.xml.qname import QName, QNameLike

  if isinstance(tags, str):
    qname = QName(tags, nsmap=nsmap)
    return {qname.qualified_name}
  elif isinstance(tags, QNameLike):
    return {QName(tags, nsmap=nsmap).text}
  else:
    result: set[str] = set()
    for tag in tags:
      result.update(prep_tag_set(tag, nsmap=nsmap))
    return result


def assert_object_type[ExpectedType](
  obj: Any, expected_type: type[ExpectedType], *, logger: Logger, policy: XmlPolicy
) -> TypeIs[ExpectedType]:
  """Assert that an object is of the expected type.

  Checks if an object is an instance of the expected type and
  handles the result according to the configured policy.

  Parameters
  ----------
  obj : Any
      The object to check.
  expected_type : type[ExpectedType]
      The expected type.
  logger : Logger
      Logger for error messages.
  policy : XmlPolicy
      Policy for handling type mismatches.

  Returns
  -------
  TypeIs[ExpectedType]
      True if obj is of expected_type, False otherwise.

  Raises
  ------
  XmlSerializationError
      If the object type is incorrect and policy is "raise".
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


def check_tag(tag: str | QNameLike, expected_tag: str, logger: Logger, policy: XmlPolicy) -> None:
  """Check if a tag matches the expected tag.

  Parameters
  ----------
  tag : str | QNameLike
      The tag to check.
  expected_tag : str
      The expected tag name.
  logger : Logger
      Logger for error messages.
  policy : XmlPolicy
      Policy for handling tag mismatches.

  Raises
  ------
  InvalidTagError
      If tags don't match and policy is "raise".
  """
  from hypomnema.xml.qname import QName, QNameLike

  tag = QName(tag).text if isinstance(tag, QNameLike) else tag
  if not tag == expected_tag:
    logger.log(
      policy.invalid_tag.log_level, "Incorrect tag: expected %s, got %s", expected_tag, tag
    )
    if policy.invalid_tag.behavior == "raise":
      raise InvalidTagError(f"Incorrect tag: expected {expected_tag}, got {tag}")


def make_usable_path(path: str | PathLike, *, mkdir: bool = True) -> Path:
  """Convert a path to an absolute, usable Path object.

  Expands user directories, resolves to absolute path, and
  optionally creates parent directories.

  Parameters
  ----------
  path : str | PathLike
      The path to convert.
  mkdir : bool
      If True, create parent directories. Default True.

  Returns
  -------
  Path
      The usable Path object.

  Examples
  --------
  .. code-block:: python

      path = make_usable_path("~/documents/file.txt")
      # Returns: Path("/home/user/documents/file.txt")
  """
  final_path = Path(path).expanduser()
  final_path = final_path.resolve()
  if mkdir:
    final_path.parent.mkdir(parents=True, exist_ok=True)
  return final_path


_NAME_START_CATEGORIES = {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}
_NAME_CHAR_CATEGORIES = _NAME_START_CATEGORIES | {"Nd", "Mc", "Mn", "Pc"}


def _is_letter(char: str) -> bool:
  cat = category(char)
  if cat in _NAME_START_CATEGORIES:
    return True
  return char == "_"  # ASCII underscore is explicitly allowed


def _is_ncname_char(char: str) -> bool:
  cat = category(char)
  if cat in _NAME_CHAR_CATEGORIES:
    return True
  return char in (".", "-", "_")


def is_ncname(name: str) -> bool:
  """Check if a string is a valid NCName (non-colonized name).

  Validates that the name follows XML NCName rules:
  - Must start with a letter or underscore
  - Subsequent characters can be letters, digits, underscores,
    hyphens, periods, or combining characters

  Parameters
  ----------
  name : str
      The name to validate.

  Returns
  -------
  bool
      True if valid NCName, False otherwise.

  Examples
  --------
  .. code-block:: python

      is_ncname("validName")  # True
      is_ncname("invalid:name")  # False
      is_ncname("123name")  # False
  """
  if not name:
    return False
  if not _is_letter(name[0]):
    return False
  return all(_is_ncname_char(ch) for ch in name[1:])


# RFC 3986 URI regex pattern
# Adapted from Appendix B of RFC 3986 by Claude 4.5 Opus
URI_PATTERN = compile(
  r"^"
  r"(?:([a-zA-Z][a-zA-Z0-9+.-]*):"  # scheme (required)
  r"(?:"
  r"//(?:"  # authority (optional)
  r"(?:[a-zA-Z0-9._~%!$&'()*+,;=:-]*)@)?"  # userinfo
  r"(?:"  # host
  r"\[(?:[a-fA-F0-9:.]+)\]|"  # IPv6
  r"[a-zA-Z0-9._~%!$&'()*+,;=-]*"  # reg-name or IPv4
  r")"
  r"(?::[0-9]*)?"  # port
  r")?"
  r"([a-zA-Z0-9._~%!$&'()*+,;=:@/-]*)"  # path
  r"(?:\?([a-zA-Z0-9._~%!$&'()*+,;=:@/?-]*))?"  # query
  r"(?:#([a-zA-Z0-9._~%!$&'()*+,;=:@/?-]*))?"  # fragment
  r")$",
  IGNORECASE,
)


def is_valid_uri(uri: str) -> bool:
  """Check if a string is a valid URI according to RFC 3986.

  Validates that the string conforms to URI syntax rules
  including scheme, authority, path, query, and fragment.

  Parameters
  ----------
  uri : str
      The URI to validate.

  Returns
  -------
  bool
      True if valid URI, False otherwise.

  Examples
  --------
  .. code-block:: python

      is_valid_uri("http://example.com/path")  # True
      is_valid_uri("urn:isbn:0451450523")  # True
      is_valid_uri("not a uri")  # False
  """
  if not uri or not isinstance(uri, str):
    return False

  return bool(URI_PATTERN.match(uri))
