from unicodedata import category
from pathlib import Path
from hypomnema.base.errors import XmlSerializationError, InvalidTagError
from hypomnema.xml.policy import SerializationPolicy, DeserializationPolicy
from codecs import lookup
from collections.abc import Collection, Mapping
from logging import Logger
from typing import TypeIs, Any
from encodings import normalize_encoding as python_normalize_encoding
from os import PathLike


def normalize_tag(tag: Any) -> str:
  if isinstance(tag, str):
    return tag.split("}", 1)[1] if "}" in tag else tag
  elif isinstance(tag, (bytes, bytearray)):
    return normalize_tag(tag.decode("utf-8"))
  elif hasattr(tag, "localname"):
    return tag.localname
  elif hasattr(tag, "text"):
    return normalize_tag(tag.text)
  else:
    raise TypeError(f"Unexpected tag type: {type(tag)}")


def normalize_encoding(encoding: str | None) -> str:
  normalized_encoding = python_normalize_encoding(encoding or "utf-8").lower()
  if encoding == "unicode":
    normalized_encoding = "utf-8"
  try:
    codec = lookup(normalized_encoding)
    return codec.name
  except LookupError as e:
    raise ValueError(f"Unknown encoding: {normalized_encoding}") from e


def prep_tag_set(
  tags: str | Collection[str] | None, nsmap: dict[str | None, str] | None = None
) -> set[str] | None:
  _nsmap = dict() if nsmap is None else nsmap
  if not tags:
    return None
  if isinstance(tags, str):
    qname = QName(tags, _nsmap)
    return {qname.qualified_name}
  return {QName(tag, _nsmap).qualified_name for tag in tags}


def assert_object_type[ExpectedType](
  obj: Any, expected_type: type[ExpectedType], *, logger: Logger, policy: SerializationPolicy
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


def check_tag(tag: str, expected_tag: str, logger: Logger, policy: DeserializationPolicy) -> None:
  if not tag == expected_tag:
    logger.log(
      policy.invalid_tag.log_level, "Incorrect tag: expected %s, got %s", expected_tag, tag
    )
    if policy.invalid_tag.behavior == "raise":
      raise InvalidTagError(f"Incorrect tag: expected {expected_tag}, got {tag}")


def make_usable_path(path: str | bytes | PathLike, *, mkdir: bool = True) -> Path:
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
  return None, None, localname


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
  uri: str | None
  """The namespace URI."""
  prefix: str | None
  """The namespace prefix."""
  local_name: str
  """The local name."""

  def __init__(
    self, tag: str | bytes | bytearray, nsmap: Mapping[str | None, str], encoding: str = "utf-8"
  ) -> None:
    if isinstance(tag, str):
      tag = tag
    if isinstance(tag, (bytes, bytearray)):
      tag = tag.decode(encoding)
    else:
      raise TypeError(f"Unexpected tag type: {type(tag)}")

    if tag[0] == "{":
      self.uri, self.prefix, self.local_name = _split_qualified_tag(tag, nsmap)
    elif tag[0] == ":":
      self.uri, self.prefix, self.local_name = _split_prefixed_tag(tag, nsmap)
    else:
      self.uri, self.prefix, self.local_name = None, None, tag

  @property
  def qualified_name(self) -> str:
    """The fully qualified name."""
    if self.uri is None:
      return self.local_name
    return f"{{{self.uri}}}{self.local_name}"

  @property
  def prefixed_name(self) -> str:
    """The prefixed name."""
    if self.prefix is None:
      return self.local_name
    return f"{self.prefix}:{self.local_name}"
