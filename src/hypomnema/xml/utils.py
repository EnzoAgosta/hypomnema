from hypomnema.xml.policy import XmlPolicy
from unicodedata import category
from pathlib import Path
from hypomnema.base.errors import XmlSerializationError, InvalidTagError
from codecs import lookup
from collections.abc import Iterable
from logging import Logger
from typing import TypeIs, Any, Mapping, TYPE_CHECKING
from encodings import normalize_encoding as python_normalize_encoding
from logging import Logger
from os import PathLike
import re

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
  from hypomnema.xml.qname import QName, QNameLike
  tag = QName(tag).text if isinstance(tag, QNameLike) else tag
  if not tag == expected_tag:
    logger.log(
      policy.invalid_tag.log_level, "Incorrect tag: expected %s, got %s", expected_tag, tag
    )
    if policy.invalid_tag.behavior == "raise":
      raise InvalidTagError(f"Incorrect tag: expected {expected_tag}, got {tag}")


def make_usable_path(path: str | PathLike, *, mkdir: bool = True) -> Path:
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
  if not name:
    return False
  if not _is_letter(name[0]):
    return False
  return all(_is_ncname_char(ch) for ch in name[1:])


# RFC 3986 URI regex pattern
# Adapted from Appendix B of RFC 3986 by Claude 4.5 Opus
URI_PATTERN = re.compile(
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
  re.IGNORECASE,
)


def is_valid_uri(uri: str) -> bool:
  if not uri or not isinstance(uri, str):
    return False

  return bool(URI_PATTERN.match(uri))
