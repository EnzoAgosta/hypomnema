"""
XML name and RFC 3986 URI-reference validation utilities.

This module provides validators for:
    - NCName (Non-Colonized Name) per XML Namespaces §4
    - URI-references per RFC 3986 §4.1

All public validators return ``None`` on success and raise
``ValueError`` (or a subclass) on failure, with a message
identifying the exact check that failed.
"""

from ipaddress import IPv4Address, IPv6Address
from unicodedata import category


from codecs import lookup
from encodings import normalize_encoding as python_normalize_encoding
from os import PathLike
from pathlib import Path
from typing import Literal, Protocol, overload, runtime_checkable

from hypomnema.backends.xml.errors import InvalidNCNameError


@overload
def normalize_encoding(encoding: Literal["unicode"] | None) -> Literal["utf-8"]: ...
@overload
def normalize_encoding(encoding: str) -> str: ...
def normalize_encoding(encoding: str | None) -> str:
  """Normalize character encoding name to standard form.

  Converts encoding names to their canonical form using the Python
  codec registry. Handles "unicode" as an alias for UTF-8.

  Args:
      encoding: Encoding name to normalize. None or "unicode" returns "utf-8".

  Returns:
      Canonical encoding name.

  Raises:
      ValueError: If the encoding is unknown.

  Example:
      >>> normalize_encoding("UTF-8")
      'utf-8'
      >>> normalize_encoding("unicode")
      'utf-8'
      >>> normalize_encoding(None)
      'utf-8'
  """
  if encoding == "unicode" or encoding is None:
    return "utf-8"
  normalized_encoding = python_normalize_encoding(encoding).lower()
  try:
    codec = lookup(normalized_encoding)
    return codec.name
  except LookupError as e:
    raise ValueError(f"Unknown encoding: {normalized_encoding}") from e


def make_usable_path(path: str | PathLike[str], *, mkdir: bool = True) -> Path:
  """Convert path string to resolved Path object.

  Expands user directories (~), resolves to absolute path,
  and optionally creates parent directories.

  Args:
      path: Path to process.
      mkdir: Whether to create parent directories (default: True).

  Returns:
      Resolved absolute Path object.
  """
  final_path = Path(path).expanduser()
  final_path = final_path.resolve()
  if mkdir:
    final_path.parent.mkdir(parents=True, exist_ok=True)
  return final_path


@runtime_checkable
class QNameLike(Protocol):
  """Protocol for qualified name-like objects.

  Objects implementing this protocol can be used where qualified
  names are expected (e.g., tag filters).

  Attributes:
      text: The qualified name as a string.
  """

  @property
  def text(self) -> str: ...


# ── NCName validation ────────────────────────────────────────────
_NAME_START_CATEGORIES = frozenset({"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"})
"""Unicode general categories accepted for the first character of
an XML Name, per XML 1.0 5th Edition §2.3 (excluding ``_`` and
``:``, which are tested explicitly)."""

_NAME_CHAR_CATEGORIES = _NAME_START_CATEGORIES | frozenset({"Nd", "Mc", "Mn", "Pc"})
"""Unicode general categories accepted for subsequent characters of
an XML Name, per XML 1.0 5th Edition §2.3 (excluding ``-``, ``.``,
and ``\\u00B7``, which are tested explicitly)."""

_NAME_EXTRA_CHARS = frozenset("\u200c\u200d")
"""Characters with Unicode category Cf that are nonetheless valid
in XML NameStartChar per XML 1.0 5th Edition §2.3:
U+200C ZERO WIDTH NON-JOINER and U+200D ZERO WIDTH JOINER."""


def _validate_nc_start_char(char: str) -> None:
  """Validate that a character is valid for NCName start.

  A valid NCName start character is ``_``, U+200C, U+200D, or any
  character whose Unicode general category is in
  ``_NAME_START_CATEGORIES``.

  Args:
      char: Single character to validate.

  Raises:
      ValueError: If the character is not a valid NCName start
          character.
  """
  if char == "_" or char in _NAME_EXTRA_CHARS or category(char) in _NAME_START_CATEGORIES:
    return
  raise ValueError(f"Character {char!r} is not a valid xml name start")


def _validate_ncname_char(char: str) -> None:
  """Validate that a character is valid within an NCName.

  A valid NCName character is any valid start character, plus
  ``-``, ``.``, U+00B7, or any character whose Unicode general
  category is in ``_NAME_CHAR_CATEGORIES``.

  Args:
      char: Single character to validate.

  Raises:
      ValueError: If the character is not a valid NCName
          character.
  """
  if (
    char in _NAME_EXTRA_CHARS
    or char in ("\u00b7", ".", "-")
    or category(char) in _NAME_CHAR_CATEGORIES
  ):
    return
  raise ValueError(f"Character {char!r} is not a valid xml name char")


def validate_ncname(name: str) -> None:
  """Validate that a string is a valid NCName.

  NCName (Non-Colonized Name) is an XML identifier that cannot
  contain colons. Used for local parts of element names, attribute
  names, namespace prefixes, etc.

  Args:
      name: The candidate NCName string.

  Raises:
      InvalidNCNameError: If *name* is empty or contains
          characters that violate the NCName production.

  Example:
      >>> validate_ncname("validName")
      >>> validate_ncname("ns:name")  # Raises InvalidNCNameError
  """
  try:
    if not name:
      raise InvalidNCNameError("NCName cannot be empty")
    _validate_nc_start_char(name[0])
    for ch in name[1:]:
      _validate_ncname_char(ch)
    return
  except ValueError as err:
    raise InvalidNCNameError(name) from err


ALPHA = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
DIGIT = frozenset("0123456789")
HEXDIG = DIGIT | frozenset("ABCDEFabcdef")
UNRESERVED = ALPHA | DIGIT | frozenset("-._~")
SUB_DELIMS = frozenset("!$&'()*+,;=")
GEN_DELIMS = frozenset(":/?#[]@")
RESERVED = GEN_DELIMS | SUB_DELIMS
PCHAR = UNRESERVED | SUB_DELIMS | frozenset(":@")
SCHEME_CHARS = ALPHA | DIGIT | frozenset("+-.")
USERINFO_CHARS = UNRESERVED | SUB_DELIMS | frozenset(":")
REG_NAME_CHARS = UNRESERVED | SUB_DELIMS
QUERY_CHARS = PCHAR | frozenset("/?")
FRAGMENT_CHARS = PCHAR | frozenset("/?")

ALLOWED_IP_LITERAL = UNRESERVED | SUB_DELIMS | frozenset(":")


def _validate_chars(
  s: str, allowed: frozenset[str], component: str, start_position: int = 0
) -> None:
  """Validate a URI component against an allowed character set.

  This helper accepts RFC 3986 percent-encoded triplets inline and
  otherwise requires each character to be present in ``allowed``.

  Args:
      s: Component text to validate.
      allowed: Allowed non-percent-encoded characters.
      component: Component name for error reporting.
      start_position: Offset applied to reported character positions.

  Raises:
      ValueError: If the component contains an invalid character or an
          invalid percent-encoded sequence.
  """
  i = 0
  while i < len(s):
    char = s[i]
    position = start_position + i
    if char == "%":
      if i + 2 >= len(s):
        raise ValueError(f"Truncated percent-encoding at position {position} in {component}")
      first_hex = s[i + 1]
      if first_hex not in HEXDIG:
        raise ValueError(
          f"Invalid hex digit {first_hex!r} at position {position + 1} in {component}"
        )
      second_hex = s[i + 2]
      if second_hex not in HEXDIG:
        raise ValueError(
          f"Invalid hex digit {second_hex!r} at position {position + 2} in {component}"
        )
      i += 3
      continue
    if char not in allowed:
      raise ValueError(f"Invalid character {char!r} at position {position} in {component}")
    i += 1


def _validate_scheme(scheme: str) -> None:
  """Validate a URI scheme.

  The scheme must match RFC 3986 ``ALPHA *( ALPHA / DIGIT / "+" /
  "-" / "." )``. Percent-encoding is not allowed.

  Args:
      scheme: Scheme text without the trailing ``:`` delimiter.

  Raises:
      ValueError: If the scheme is empty or contains invalid
          characters.
  """
  if not scheme:
    raise ValueError("Scheme cannot be empty")
  if scheme[0] not in ALPHA:
    raise ValueError(f"Scheme must begin with a letter, got {scheme[0]!r}")
  for index in range(1, len(scheme)):
    char = scheme[index]
    if char not in SCHEME_CHARS:
      raise ValueError(f"Invalid character {char!r} at position {index} in scheme")


def _validate_userinfo(userinfo: str) -> None:
  """Validate the userinfo subcomponent of an authority.

  Args:
      userinfo: Userinfo text before ``@``.

  Raises:
      ValueError: If the userinfo contains invalid characters or an
          invalid percent-encoded sequence.
  """
  _validate_chars(userinfo, USERINFO_CHARS, "userinfo")


def _validate_ip_literal(content: str) -> None:
  """Validate bracketed host content as IPv6 or IPvFuture.

  Args:
      content: Text inside ``[`` and ``]``.

  Raises:
      ValueError: If the content is empty or is not a valid IPv6
          address or IPvFuture literal.
  """
  if not content:
    raise ValueError("Host IP literal cannot be empty")
  if content[0] == "v" or content[0] == "V":
    try:
      separator_index = content.index(".")
    except ValueError as err:
      raise ValueError("Invalid IPvFuture in host: missing '.' after version") from err
    version = content[1:separator_index]
    if not version:
      raise ValueError("Invalid IPvFuture in host: version is empty")
    for index, char in enumerate(version, start=1):
      if char not in HEXDIG:
        raise ValueError(f"Invalid hex digit {char!r} at position {index} in host IP literal")
    future = content[separator_index + 1 :]
    if not future:
      raise ValueError("Invalid IPvFuture in host: address part is empty")
    for index, char in enumerate(future, start=separator_index + 1):
      if char not in ALLOWED_IP_LITERAL:
        raise ValueError(f"Invalid character {char!r} at position {index} in host IP literal")
    return
  try:
    IPv6Address(content)
  except ValueError as err:
    raise ValueError(f"Invalid IPv6 address {content!r} in host") from err


def _validate_host(host: str) -> None:
  """Validate a non-literal host as IPv4 or registered name.

  Args:
      host: Host text without userinfo, brackets, or port.

  Raises:
      ValueError: If the host is neither a valid IPv4 address nor a
          valid registered name.
  """
  try:
    IPv4Address(host)
    return
  except ValueError:
    _validate_chars(host, REG_NAME_CHARS, "host")


def _validate_port(port: str) -> None:
  """Validate a URI port.

  Args:
      port: Port text after ``:``. The empty string is valid.

  Raises:
      ValueError: If the port contains any non-digit character.
  """
  for index, char in enumerate(port):
    if char not in DIGIT:
      raise ValueError(f"Invalid character {char!r} at position {index} in port")


def _validate_authority(authority: str) -> None:
  """Validate an authority and its userinfo, host, and port parts.

  Args:
      authority: Raw authority text after ``//`` and before any path.

  Raises:
      ValueError: If authority splitting fails or any subcomponent is
          invalid.
  """
  if not authority:
    return

  if authority.count("@") > 1:
    raise ValueError("Multiple '@' characters in authority")

  host_and_port = authority
  if "@" in authority:
    userinfo, _, host_and_port = authority.partition("@")
    _validate_userinfo(userinfo)

  if host_and_port.startswith("["):
    try:
      bracket_index = host_and_port.index("]")
    except ValueError as err:
      raise ValueError("Unclosed '[' in host, IP literal missing closing ']'") from err

    host = host_and_port[1:bracket_index]
    port_suffix = host_and_port[bracket_index + 1 :]
    if port_suffix and not port_suffix.startswith(":"):
      raise ValueError("Unexpected characters after IP literal in host")

    _validate_ip_literal(host)

    if port_suffix.startswith(":"):
      _validate_port(port_suffix[1:])
    return

  separator_index = host_and_port.rfind(":")
  if separator_index == -1:
    _validate_host(host_and_port)
    return

  host = host_and_port[:separator_index]
  port = host_and_port[separator_index + 1 :]
  _validate_port(port)
  _validate_host(host)


def _validate_path(path: str, has_authority: bool) -> None:
  """Validate a URI path with authority-sensitive leading-slash rules.

  Args:
      path: Raw path component.
      has_authority: Whether the URI included an authority component.

  Raises:
      ValueError: If the path violates RFC 3986 structure rules or
          contains invalid characters.
  """
  if has_authority:
    if path and not path.startswith("/"):
      raise ValueError("Path must begin with '/' when authority is present")
    if path.startswith("//"):
      raise ValueError("Path cannot begin with '//' when authority is present")
  elif path.startswith("//"):
    raise ValueError("Path cannot begin with '//' when authority is not present")

  segment_start = 0
  for segment in path.split("/"):
    _validate_chars(segment, PCHAR, "path", segment_start)
    segment_start += len(segment) + 1


def _validate_query(query: str) -> None:
  """Validate a URI query component.

  Args:
      query: Query text after ``?``.

  Raises:
      ValueError: If the query contains invalid characters or an
          invalid percent-encoded sequence.
  """
  if not query:
    return
  _validate_chars(query, QUERY_CHARS, "query")


def _validate_fragment(fragment: str) -> None:
  """Validate a URI fragment component.

  Args:
      fragment: Fragment text after ``#``.

  Raises:
      ValueError: If the fragment contains invalid characters or an
          invalid percent-encoded sequence.
  """
  if not fragment:
    return
  _validate_chars(fragment, FRAGMENT_CHARS, "fragment")


def validate_uri(uri: str) -> None:
  """Validate that a string is a syntactically valid RFC 3986 URI.

  The validator performs purely syntactic checks. It does not verify
  scheme registration, host reachability, port ranges, or query
  semantics.

  Args:
      uri: URI string to validate.

  Raises:
      ValueError: If the URI is empty or any component is
          syntactically invalid.
  """
  if not uri:
    raise ValueError("URI cannot be empty")

  remainder, fragment_separator, fragment = uri.partition("#")
  has_fragment = fragment_separator == "#"

  remainder, query_separator, query = remainder.partition("?")
  has_query = query_separator == "?"

  try:
    scheme_separator = remainder.index(":")
  except ValueError as err:
    raise ValueError("Missing ':' delimiter after scheme") from err

  scheme = remainder[:scheme_separator]
  hier_part = remainder[scheme_separator + 1 :]

  _validate_scheme(scheme)

  has_authority = hier_part.startswith("//")
  if has_authority:
    authority_and_path = hier_part[2:]
    authority, path_separator, path_rest = authority_and_path.partition("/")
    path = f"/{path_rest}" if path_separator else ""
    _validate_authority(authority)
  else:
    path = hier_part

  _validate_path(path, has_authority)

  if has_query:
    _validate_query(query)
  if has_fragment:
    _validate_fragment(fragment)
