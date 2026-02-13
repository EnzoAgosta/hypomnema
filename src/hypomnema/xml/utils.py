"""
XML name and RFC 3986 URI-reference validation utilities.

This module provides validators for:
    - NCName (Non-Colonized Name) per XML Namespaces §4
    - URI-references per RFC 3986 §4.1

All public validators return ``None`` on success and raise
``ValueError`` (or a subclass) on failure, with a message
identifying the exact check that failed.
"""

from unicodedata import category
import re


from codecs import lookup
from encodings import normalize_encoding as python_normalize_encoding
from os import PathLike
from pathlib import Path
from typing import Literal, Protocol, overload, runtime_checkable


from hypomnema.base.errors import InvalidNCNameError


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


def make_usable_path(path: str | PathLike, *, mkdir: bool = True) -> Path:
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
_NAME_START_CATEGORIES = {"Lu", "Ll", "Lt", "Lm", "Lo", "Nl"}
"""Unicode general categories accepted for the first character of
an XML Name, per XML 1.0 5th Edition §2.3 (excluding ``_`` and
``:``, which are tested explicitly)."""

_NAME_CHAR_CATEGORIES = _NAME_START_CATEGORIES | {"Nd", "Mc", "Mn", "Pc"}
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
      raise ValueError("NCName cannot be empty")
    _validate_nc_start_char(name[0])
    for ch in name[1:]:
      _validate_ncname_char(ch)
    return
  except ValueError as err:
    raise InvalidNCNameError(name) from err


# ── RFC 3986 regex building blocks ───────────────────────────────
#
# Each constant below is a *string* containing a regex fragment,
# built up compositionally from the ABNF in RFC 3986 §3.  They are
# compiled into ``re.Pattern`` objects (prefixed ``_RE_``) further
# below for use at match time.

# Atomic character classes
ALPHA = r"[ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz]"
"""``ALPHA`` from RFC 2234 §6.1."""

AMPERSAND = r"\&"
APOSTROPHE = r"\'"
AT_SIGN = r"\@"
COLON = r"\:"
COMMA = r"\,"
DIGIT = r"[0123456789]"
"""``DIGIT`` from RFC 2234 §6.1."""

DOLLAR_SIGN = r"\$"
DOUBLE_COLON = r"\:\:"
EQUAL_SIGN = r"\="
EXCLAMATION_MARK = r"\!"
FORWARD_SLASH = r"\/"
HASHTAG = r"\#"
HEXDIGITS = r"[0123456789abcdefABCDEF]"
"""``HEXDIG`` from RFC 2234 §6.1."""

HYPHEN = r"\-"
LEFT_BRACKET = r"\("
LEFT_SQUARE_BRACKET = r"\["
PERCENT_SIGN = r"\%"
PERIOD = r"\."
PLUS_SIGN = r"\+"
QUESTION_MARK = r"\?"
RIGHT_BRACKET = r"\)"
RIGHT_SQUARE_BRACKET = r"\]"
SEMI_COLON = r"\;"
STAR_SIGN = r"\*"
TILDE = r"\~"
UNDERSCORE = r"\_"

# Composite productions – RFC 3986 §2
UNRESERVED = (
  rf"({ALPHA}|{DIGIT}|{HYPHEN}|{PERIOD}"
  rf"|{UNDERSCORE}|{TILDE})"
)
"""``unreserved`` per RFC 3986 §2.3."""

SUB_DELIMS = (
  rf"({EXCLAMATION_MARK}|{DOLLAR_SIGN}|{AMPERSAND}"
  rf"|{APOSTROPHE}|{LEFT_BRACKET}|{RIGHT_BRACKET}"
  rf"|{STAR_SIGN}|{PLUS_SIGN}|{COMMA}|{SEMI_COLON}"
  rf"|{EQUAL_SIGN})"
)
"""``sub-delims`` per RFC 3986 §2.2."""

PCT_ENCODED = rf"{PERCENT_SIGN}{HEXDIGITS}{HEXDIGITS}"
"""``pct-encoded`` per RFC 3986 §2.1."""

DEC_OCTET = (
  rf"({DIGIT}|[1-9]{DIGIT}|1{DIGIT}{{2}}"
  rf"|2[01234]{DIGIT}|25[012345])"
)
"""``dec-octet`` per RFC 3986 §3.2.2 (0–255)."""

# §3.3 – Path components
REG_NAME = rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS})*"
"""``reg-name`` per RFC 3986 §3.2.2."""

PCHAR = (
  rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}"
  rf"|{COLON}|{AT_SIGN})"
)
"""``pchar`` per RFC 3986 §3.3."""

QUERY = FRAGMENT = rf"({PCHAR}|{FORWARD_SLASH}|{QUESTION_MARK})*"
"""``query`` and ``fragment`` per RFC 3986 §3.4 / §3.5."""

SEGMENT = rf"{PCHAR}*"
"""``segment`` per RFC 3986 §3.3."""

SEGMENT_NZ = rf"{PCHAR}+"
"""``segment-nz`` per RFC 3986 §3.3."""

SEGMENT_NZ_NC = rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|{AT_SIGN})+"
"""``segment-nz-nc`` per RFC 3986 §3.3 (no colon)."""

PATH_ABEMPTY = rf"({FORWARD_SLASH}{SEGMENT})*"
"""``path-abempty`` per RFC 3986 §3.3."""

PATH_ABSOLUTE = (
  rf"{FORWARD_SLASH}"
  rf"({SEGMENT_NZ}({FORWARD_SLASH}{SEGMENT})*)?"
)
"""``path-absolute`` per RFC 3986 §3.3."""

PATH_NOSCHEME = rf"{SEGMENT_NZ_NC}({FORWARD_SLASH}{SEGMENT})*"
"""``path-noscheme`` per RFC 3986 §3.3."""

PATH_ROOTLESS = rf"{SEGMENT_NZ}({FORWARD_SLASH}{SEGMENT})*"
"""``path-rootless`` per RFC 3986 §3.3."""

# §3.2.2 – IP addresses
IPV4ADDRESS = (
  rf"{DEC_OCTET}{PERIOD}{DEC_OCTET}"
  rf"{PERIOD}{DEC_OCTET}{PERIOD}{DEC_OCTET}"
)
"""``IPv4address`` per RFC 3986 §3.2.2."""

H16 = rf"{HEXDIGITS}{{1,4}}"
"""``h16`` per RFC 3986 §3.2.2 (1–4 hex digits)."""

LS32 = rf"({H16}{COLON}{H16}|{IPV4ADDRESS})"
"""``ls32`` per RFC 3986 §3.2.2."""

IPV6ADDRESS = (
  "("
  rf"({H16}{COLON}){{6}}{LS32}"
  "|"
  rf"{DOUBLE_COLON}({H16}{COLON}){{5}}{LS32}"
  "|"
  rf"{H16}?{DOUBLE_COLON}({H16}{COLON}){{4}}{LS32}"
  "|"
  rf"(({H16}{COLON})?{H16})?{DOUBLE_COLON}"
  rf"({H16}{COLON}){{3}}{LS32}"
  "|"
  rf"(({H16}{COLON}){{0,2}}{H16})?{DOUBLE_COLON}"
  rf"({H16}{COLON}){{2}}{LS32}"
  "|"
  rf"(({H16}{COLON}){{0,3}}{H16})?{DOUBLE_COLON}"
  rf"{H16}{COLON}{LS32}"
  "|"
  rf"(({H16}{COLON}){{0,4}}{H16})?{DOUBLE_COLON}{LS32}"
  "|"
  rf"(({H16}{COLON}){{0,5}}{H16})?{DOUBLE_COLON}{H16}"
  "|"
  rf"(({H16}{COLON}){{0,6}}{H16})?{DOUBLE_COLON}"
  ")"
)
"""``IPv6address`` per RFC 3986 §3.2.2."""

IPVFUTURE = (
  rf"v{HEXDIGITS}+{PERIOD}"
  rf"({UNRESERVED}|{SUB_DELIMS}|{COLON})+"
)
"""``IPvFuture`` per RFC 3986 §3.2.2."""

IPLITERAL = (
  rf"{LEFT_SQUARE_BRACKET}({IPV6ADDRESS}|{IPVFUTURE})"
  rf"{RIGHT_SQUARE_BRACKET}"
)
"""``IP-literal`` per RFC 3986 §3.2.2."""

# §3.2 – Authority
PORT = rf"{DIGIT}*"
"""``port`` per RFC 3986 §3.2.3."""

HOST = rf"({IPLITERAL}|{IPV4ADDRESS}|{REG_NAME})"
"""``host`` per RFC 3986 §3.2.2."""

USERINFO = rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|{COLON})*"
"""``userinfo`` per RFC 3986 §3.2.1."""

AUTHORITY = rf"({USERINFO}{AT_SIGN})?{HOST}({COLON}{PORT})?"
"""``authority`` per RFC 3986 §3.2."""

# §3.1 – Scheme
SCHEME = (
  rf"{ALPHA}({ALPHA}|{DIGIT}|{PLUS_SIGN}"
  rf"|{HYPHEN}|{PERIOD})*"
)
"""``scheme`` per RFC 3986 §3.1."""

# §3 / §4 – Top-level productions
HIER_PART = (
  rf"({FORWARD_SLASH}{FORWARD_SLASH}{AUTHORITY}{PATH_ABEMPTY}"
  rf"|{PATH_ABSOLUTE}|{PATH_ROOTLESS})?"
)
"""``hier-part`` per RFC 3986 §3."""

RELATIVE_PART = (
  rf"({FORWARD_SLASH}{FORWARD_SLASH}{AUTHORITY}{PATH_ABEMPTY}"
  rf"|{PATH_ABSOLUTE}|{PATH_NOSCHEME})?"
)
"""``relative-part`` per RFC 3986 §4.2."""

RELATIVE_REF = (
  rf"{RELATIVE_PART}({QUESTION_MARK}{QUERY})?"
  rf"({HASHTAG}{FRAGMENT})?"
)
"""``relative-ref`` per RFC 3986 §4.2."""

URI = (
  rf"{SCHEME}{COLON}{HIER_PART}"
  rf"({QUESTION_MARK}{QUERY})?({HASHTAG}{FRAGMENT})?"
)
"""``URI`` per RFC 3986 §3."""

URI_REFERENCE = rf"({URI}|{RELATIVE_REF})"
"""``URI-reference`` per RFC 3986 §4.1."""

# ── Pre-compiled patterns ────────────────────────────────────────
_RE_URI_REFERENCE = re.compile(URI_REFERENCE)
_RE_URI_DECOMPOSE = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?$")
_RE_SCHEME = re.compile(SCHEME)
_RE_ALPHA = re.compile(ALPHA)
_RE_SCHEME_TAIL_BAD = re.compile(
  r"[^ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
  r"0123456789\+\-\.]"
)
_RE_FRAGMENT = re.compile(FRAGMENT)
_RE_QUERY = re.compile(QUERY)
_RE_AUTHORITY = re.compile(AUTHORITY)
_RE_USERINFO = re.compile(USERINFO)
_RE_HOST = re.compile(HOST)
_RE_PORT = re.compile(PORT)
_RE_PATH_ABEMPTY = re.compile(PATH_ABEMPTY)
_RE_PATH_ABSOLUTE = re.compile(PATH_ABSOLUTE)
_RE_PATH_ROOTLESS = re.compile(PATH_ROOTLESS)
_RE_PATH_NOSCHEME = re.compile(PATH_NOSCHEME)
_RE_IPV4_OVERRANGE = re.compile(
  rf"{DEC_OCTET}{PERIOD}{DEC_OCTET}{PERIOD}{DEC_OCTET}"
  rf"{PERIOD}\d+"
)
_RE_PCHAR_QF = re.compile(rf"({PCHAR}|{FORWARD_SLASH}|{QUESTION_MARK})")
_RE_USERINFO_CHAR = re.compile(rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS}|{COLON})")
_RE_REGNAME_CHAR = re.compile(rf"({UNRESERVED}|{PCT_ENCODED}|{SUB_DELIMS})")
_RE_PATH_CHAR = re.compile(rf"({PCHAR}|{FORWARD_SLASH})")

_FORBIDDEN_CHARS = frozenset('<>{}|\\`"')
"""ASCII characters that are not permitted unencoded in a URI."""

_HEX_CHARS = frozenset("0123456789abcdefABCDEF")
"""Valid hexadecimal digit characters for percent-encoding."""


# ── Internal helpers ─────────────────────────────────────────────


def _find_bad_char(component: str, pattern: re.Pattern) -> str:
  """Return the first character in *component* that does not
  match *pattern*.

  Percent-encoded triplets (``%XX``) are skipped as atomic units.

  Args:
      component: The URI component to scan.
      pattern: A compiled regex that matches a single valid
          character.

  Returns:
      The first invalid character, or ``"<unknown>"`` if none
      could be isolated.
  """
  i = 0
  while i < len(component):
    if component[i] == "%" and i + 2 < len(component):
      i += 3
      continue
    if not pattern.fullmatch(component[i]):
      return component[i]
    i += 1
  return "<unknown>"


def _find_bad_pchar_qf(component: str) -> str:
  """Return the first character in *component* invalid in a query
  or fragment.

  Valid characters are ``pchar / "/" / "?"``.

  Args:
      component: The query or fragment string (without the
          leading ``?`` or ``#``).

  Returns:
      The first invalid character, or ``"<unknown>"`` if none
      could be isolated.
  """
  i = 0
  while i < len(component):
    if component[i] == "%" and i + 2 < len(component):
      i += 3
      continue
    if not _RE_PCHAR_QF.fullmatch(component[i]):
      return component[i]
    i += 1
  return "<unknown>"


def _validate_authority_detail(authority: str) -> None:
  """Decompose *authority* and raise ``ValueError`` pinpointing
  the first defective sub-component.

  The authority is split into userinfo, host, and port.  Each is
  validated individually so the error message identifies which
  part is at fault.

  Args:
      authority: The authority string (without the leading
          ``//``).

  Raises:
      ValueError: Always — either with a specific diagnostic or
          a generic message if no sub-component check triggers.
  """
  host_and_port = authority
  if "@" in authority:
    at_pos = authority.rfind("@")
    userinfo_part = authority[:at_pos]
    host_and_port = authority[at_pos + 1 :]
    if not _RE_USERINFO.fullmatch(userinfo_part):
      bad = _find_bad_char(userinfo_part, _RE_USERINFO_CHAR)
      raise ValueError(
        f"Userinfo {userinfo_part!r} contains invalid "
        f"character {bad!r}. Allowed: unreserved / "
        f"pct-encoded / sub-delims / ':'."
      )

  host_part = host_and_port
  port_part = None
  if host_and_port.startswith("["):
    bracket_end = host_and_port.find("]")
    if bracket_end == -1:
      raise ValueError("Authority contains an unclosed '['. IP-literal brackets must be balanced.")
    host_part = host_and_port[: bracket_end + 1]
    remainder = host_and_port[bracket_end + 1 :]
    if remainder.startswith(":"):
      port_part = remainder[1:]
    elif remainder:
      raise ValueError(f"Unexpected characters {remainder!r} after IP-literal in authority.")
  elif ":" in host_and_port:
    last_colon = host_and_port.rfind(":")
    possible_port = host_and_port[last_colon + 1 :]
    if _RE_PORT.fullmatch(possible_port):
      port_part = possible_port
      host_part = host_and_port[:last_colon]

  if not _RE_HOST.fullmatch(host_part):
    if host_part.startswith("["):
      inner = host_part[1:-1] if host_part.endswith("]") else host_part[1:]
      if inner[:1] in ("v", "V"):
        raise ValueError(
          f"IPvFuture address {host_part!r} is malformed. Expected format: [v<hex>.<chars>]."
        )
      raise ValueError(
        f"IPv6 address {host_part!r} is malformed. Ensure "
        f"the address inside the brackets is a valid IPv6 "
        f"representation per RFC 3986 §3.2.2."
      )
    if _RE_IPV4_OVERRANGE.fullmatch(host_part):
      # Defensive check, REG_NAME pattern matches any digit/period combination
      # so host validation should never reache this check
      raise ValueError(
        f"IPv4 address {host_part!r} has an octet out of the 0-255 range."
      )  # pragma: no cover
    bad = _find_bad_char(host_part, _RE_REGNAME_CHAR)
    raise ValueError(
      f"Host {host_part!r} contains invalid character "
      f"{bad!r}. A reg-name may only contain unreserved / "
      f"pct-encoded / sub-delims characters."
    )

  if port_part is not None and not _RE_PORT.fullmatch(port_part):
    raise ValueError(f"Port {port_part!r} is invalid. It must consist of digits only.")

  raise ValueError(f"Authority {authority!r} is invalid per RFC 3986 §3.2.")


def _raise_path_error(path: str, context: str) -> None:
  """Raise ``ValueError`` for a path that is invalid in *context*.

  Args:
      path: The path string that failed validation.
      context: A human-readable description of the URI form
          (e.g. ``"a URI without authority"``).

  Raises:
      ValueError: Always.
  """
  bad = _find_bad_char(path, _RE_PATH_CHAR)
  if bad != "<unknown>":
    raise ValueError(f"Path {path!r} contains invalid character {bad!r}.")
  raise ValueError(f"Path {path!r} does not conform to RFC 3986 for {context}.")


def _check_characters(uri: str) -> None:
  """Scan *uri* for characters that are never valid in a URI.

  Rejects non-ASCII (U+0080+), control characters (U+0000–U+001F
  and U+007F), unencoded spaces, and the characters
  ``< > {{ }} | \\\\ `` " ``.

  Args:
      uri: The candidate URI string.

  Raises:
      ValueError: On the first prohibited character found.
  """
  for pos, ch in enumerate(uri):
    code = ord(ch)
    if code > 127:
      raise ValueError(
        f"Non-ASCII character {ch!r} (U+{code:04X}) at "
        f"position {pos}. RFC 3986 URIs must consist of "
        f"ASCII characters only; use percent-encoding for "
        f"non-ASCII data."
      )
    if code <= 0x1F or code == 0x7F:
      raise ValueError(
        f"Control character U+{code:04X} at position {pos} is not permitted in a URI."
      )
    if ch == " ":
      raise ValueError(f"Unencoded space at position {pos}. Use '%20' instead.")
    if ch in _FORBIDDEN_CHARS:
      raise ValueError(
        f"Character {ch!r} at position {pos} is not permitted in a URI. It must be percent-encoded."
      )


def _check_percent_encoding(uri: str) -> None:
  """Verify that every ``%`` in *uri* is followed by exactly two
  hexadecimal digits.

  Args:
      uri: The candidate URI string.

  Raises:
      ValueError: On the first malformed percent-encoding found.
  """
  idx = 0
  while idx < len(uri):
    if uri[idx] == "%":
      if idx + 2 >= len(uri):
        raise ValueError(
          f"Incomplete percent-encoding at position "
          f"{idx}: '%' must be followed by exactly two "
          f"hexadecimal digits, but the string ends "
          f"prematurely."
        )
      h1, h2 = uri[idx + 1], uri[idx + 2]
      if h1 not in _HEX_CHARS or h2 not in _HEX_CHARS:
        raise ValueError(
          f"Invalid percent-encoding '%{h1}{h2}' at "
          f"position {idx}: the two characters after "
          f"'%' must both be hexadecimal digits "
          f"(0-9, a-f, A-F)."
        )
      idx += 3
    else:
      idx += 1


def _validate_path(path: str, *, has_scheme: bool, has_authority: bool) -> None:
  """Validate *path* in the context of the surrounding URI
  components.

  Enforces the constraints from RFC 3986 §3.3:
      - With authority present: ``path-abempty`` only.
      - With scheme, no authority: ``path-absolute`` or
        ``path-rootless``; must not start with ``//``.
      - No scheme, with authority: ``path-abempty`` only.
      - No scheme, no authority: ``path-absolute`` or
        ``path-noscheme``; must not start with ``//``; first
        segment must not contain ``:``.

  Args:
      path: The path component string.
      has_scheme: Whether the URI has a scheme component.
      has_authority: Whether the URI has an authority component.

  Raises:
      ValueError: If the path violates the applicable production.
  """
  if has_authority:
    if not _RE_PATH_ABEMPTY.fullmatch(path):
      raise ValueError(
        f"Path {path!r} is invalid when an authority is "
        f"present. It must be empty or begin with '/'."
      )
    return

  if path.startswith("//"):
    raise ValueError(
      f"Path {path!r} begins with '//' but no authority "
      f"is present. This is ambiguous per RFC 3986 §3.3."
    )

  if not path:
    return

  if has_scheme:
    if not (_RE_PATH_ABSOLUTE.fullmatch(path) or _RE_PATH_ROOTLESS.fullmatch(path)):
      _raise_path_error(path, "a URI without authority")
  else:
    if not (_RE_PATH_ABSOLUTE.fullmatch(path) or _RE_PATH_NOSCHEME.fullmatch(path)):
      first_seg = path.split("/")[0]
      if ":" in first_seg:
        raise ValueError(
          f"Path {path!r} is a relative-reference "
          f"whose first segment ({first_seg!r}) "
          f"contains a colon. This is forbidden by "
          f"RFC 3986 §4.2 because it would be "
          f"mistaken for a scheme."
        )
      _raise_path_error(path, "a relative-reference")


# ── Public API ───────────────────────────────────────────────────


def fast_validate_uri(uri: str) -> None:
  """Fast URI-reference validation per RFC 3986 §4.1.

  Performs a character-level scan, percent-encoding integrity
  check, and a single fullmatch against the ``URI-reference``
  production.  Errors identify the offending character or
  percent-encoding but do not decompose the URI into components.

  Args:
      uri: The candidate URI-reference string.

  Raises:
      ValueError: If *uri* is not a string or is not a valid
          URI-reference.
  """
  if not isinstance(uri, str):
    raise ValueError(f"Expected str, got {type(uri).__name__}.")
  _check_characters(uri)
  _check_percent_encoding(uri)
  if _RE_URI_REFERENCE.fullmatch(uri):
    return None
  raise ValueError(f"Invalid URI-reference: {uri!r}")


def validate_uri(uri: str) -> None:
  """Validate a URI-reference per RFC 3986 §4.1 with detailed
  diagnostics.

  Decomposes the URI into scheme, authority, path, query, and
  fragment using RFC 3986 Appendix B and validates each component
  individually.  The raised ``ValueError`` identifies exactly
  which component and character is at fault.

  Suitable for use with any URI found in an XML document: by the
  time an XML parser delivers an attribute value, character- and
  entity-references are already resolved, so this function
  validates the resolved string as a plain RFC 3986
  URI-reference.

  Args:
      uri: The candidate URI-reference string.

  Raises:
      ValueError: If *uri* is not a string or is not a valid
          URI-reference.  The message identifies the specific
          component and character that failed.
  """
  if not isinstance(uri, str):
    raise ValueError(f"Expected str, got {type(uri).__name__}.")

  _check_characters(uri)
  _check_percent_encoding(uri)

  # ── Decompose (RFC 3986 Appendix B) ──────────────────────────
  m = _RE_URI_DECOMPOSE.match(uri)
  if not m:
    # Defensive check, URI pattern matches any string
    raise ValueError(f"URI {uri!r} could not be decomposed into components.")  # pragma: no cover

  scheme = m.group(2)
  authority = m.group(4)
  path = m.group(5)
  query = m.group(7)
  fragment = m.group(9)

  has_scheme = scheme is not None
  has_authority = authority is not None

  # ── Scheme ───────────────────────────────────────────────────
  if has_scheme and not _RE_SCHEME.fullmatch(scheme):
    if not scheme:
      # Defensive check, The decomposition regex requires at least
      # one char before : for scheme to be captured
      raise ValueError(
        "Scheme component is empty. A scheme must start with a letter."  # pragma: no cover
      )
    if not _RE_ALPHA.fullmatch(scheme[0]):
      raise ValueError(
        f"Scheme {scheme!r} must start with a letter (a-z, A-Z), but starts with {scheme[0]!r}."
      )
    bad = _RE_SCHEME_TAIL_BAD.search(scheme[1:])
    if bad:
      raise ValueError(
        f"Scheme {scheme!r} contains invalid character "
        f"{bad.group()!r} at offset {bad.start() + 1}. "
        f"Only letters, digits, '+', '-', and '.' are "
        f"allowed after the initial letter."
      )
    # Defensive check, Specific checks (empty, first char alpha, bad tail char) cover all failure cases
    raise ValueError(f"Scheme {scheme!r} is invalid per RFC 3986.")  # pragma: no cover

  # ── Fragment ─────────────────────────────────────────────────
  if fragment is not None and not _RE_FRAGMENT.fullmatch(fragment):
    bad_fragment_char = _find_bad_pchar_qf(fragment)
    raise ValueError(
      f"Fragment component {fragment!r} contains invalid "
      f"character {bad_fragment_char!r}. Allowed: unreserved / "
      f"pct-encoded / sub-delims / ':' / '@' / '/' / '?'."
    )

  # ── Query ────────────────────────────────────────────────────
  if query is not None and not _RE_QUERY.fullmatch(query):
    bad_query_char = _find_bad_pchar_qf(query)
    raise ValueError(
      f"Query component {query!r} contains invalid "
      f"character {bad_query_char!r}. Allowed: unreserved / "
      f"pct-encoded / sub-delims / ':' / '@' / '/' / '?'."
    )

  # ── Authority ────────────────────────────────────────────────
  if has_authority and not _RE_AUTHORITY.fullmatch(authority):
    _validate_authority_detail(authority)

  # ── Path ─────────────────────────────────────────────────────
  _validate_path(path, has_scheme=has_scheme, has_authority=has_authority)

  return None
