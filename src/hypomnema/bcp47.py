"""Well-formedness validation for BCP 47 language tags (RFC 5646).

Grammar-only, per RFC 5646 section 2.2.9: a tag is "well-formed" when it
matches the ABNF in section 2.1. The stricter "valid" class -- registry
membership, deprecation, suppress-script, singleton uniqueness (section
2.2.6 rule 3) -- is out of scope and belongs to a registry-backed layer.

Self-contained (stdlib only, no TMX or third-party dependency) so it can be
lifted out as a standalone package.

References to "RFC 5646" below are section 2.1 unless noted. Per RFC 5646
the ABNF is case-insensitive, so comparisons run on lowercased input while
the original spelling is preserved.
"""

_IRREGULAR_TAGS = frozenset(
  {
    "en-gb-oed",
    "i-ami",
    "i-bnn",
    "i-default",
    "i-enochian",
    "i-hak",
    "i-klingon",
    "i-lux",
    "i-mingo",
    "i-navajo",
    "i-pwn",
    "i-tao",
    "i-tay",
    "i-tsu",
    "sgn-be-fr",
    "sgn-be-nl",
    "sgn-ch-de",
  }
)
"""The ABNF's ``irregular`` production, verbatim (lowercased)."""

_REGULAR_TAGS = frozenset(
  {"art-lojban", "cel-gaulish", "no-bok", "no-nyn", "zh-guoyu", "zh-hakka", "zh-min", "zh-min-nan", "zh-xiang"}
)
"""The ABNF's ``regular`` production, verbatim (lowercased)."""

_GRANDFATHERED_TAGS = _IRREGULAR_TAGS | _REGULAR_TAGS


def _is_alpha(text: str) -> bool:
  """ALPHA: ASCII letters only."""
  return text.isascii() and text.isalpha()


def _is_digit(text: str) -> bool:
  """DIGIT: ASCII digits only."""
  return text.isascii() and text.isdigit()


def _is_alphanum(text: str, minimum: int = 1, maximum: int = 8) -> bool:
  """``alphanum``: ASCII letters or digits, within a length range."""
  return minimum <= len(text) <= maximum and text.isascii() and text.isalnum()


def _validate_privateuse(subtags: list[str], original: str) -> None:
  """``privateuse = "x" 1*("-" (1*8alphanum))`` -- at least one subtag."""
  if not subtags or not all(_is_alphanum(subtag) for subtag in subtags):
    raise ValueError(f"malformed private-use tag: {original!r}")


def _validate_langtag(subtags: list[str], original: str) -> None:
  """``langtag = language ["-" script] ["-" region] *("-" variant) *("-" extension) ["-" privateuse]``."""
  index = _validate_language(subtags, original)
  # script = 4ALPHA
  if index < len(subtags) and len(subtags[index]) == 4 and _is_alpha(subtags[index]):
    index += 1
  # region = 2ALPHA / 3DIGIT
  if index < len(subtags) and (
    (len(subtags[index]) == 2 and _is_alpha(subtags[index])) or (len(subtags[index]) == 3 and _is_digit(subtags[index]))
  ):
    index += 1
  # *("-" variant)
  while index < len(subtags) and _is_variant(subtags[index]):
    index += 1
  # *("-" extension) ["-" privateuse]
  # Duplicate singletons affect validity, not ABNF well-formedness (2.2.9).
  while index < len(subtags):
    singleton = subtags[index].lower()
    if len(singleton) != 1 or not _is_alphanum(singleton):
      raise ValueError(f"malformed subtag {subtags[index]!r}: {original!r}")
    index += 1
    if index == len(subtags):
      raise ValueError(f"singleton {singleton!r} without subtags: {original!r}")
    if singleton == "x":
      # trailing privateuse terminates the tag; subtags may be a single character
      _validate_privateuse(subtags[index:], original)
      return
    # extension = singleton 1*("-" (2*8alphanum)); the singleton production
    # for extensions excludes "x", which is private use
    body_count = 0
    while index < len(subtags) and len(subtags[index]) != 1:
      if not _is_alphanum(subtags[index], 2, 8):
        raise ValueError(f"malformed extension subtag {subtags[index]!r}: {original!r}")
      body_count += 1
      index += 1
    if body_count == 0:
      raise ValueError(f"extension {singleton!r} without subtags: {original!r}")


def _validate_language(subtags: list[str], original: str) -> int:
  """``language = 2*3ALPHA ["-" extlang] / 4ALPHA / 5*8ALPHA`` -- returns the
  index of the first subtag after the language.

  The three alternatives share ``ALPHA`` and together span lengths 2-8
  (4ALPHA is reserved for future use, 5*8ALPHA covers registered language
  subtags); only the 2-3 length branch admits extlangs."""
  language = subtags[0]
  if not (_is_alpha(language) and 2 <= len(language) <= 8):
    raise ValueError(f"malformed language subtag {language!r}: {original!r}")
  index = 1
  if len(language) in (2, 3):
    # extlang = 3ALPHA *2("-" 3ALPHA)
    extlang_count = 0
    while extlang_count < 3 and index < len(subtags) and len(subtags[index]) == 3 and _is_alpha(subtags[index]):
      extlang_count += 1
      index += 1
  return index


def _is_variant(subtag: str) -> bool:
  """``variant = 5*8alphanum / (DIGIT 3alphanum)``."""
  return _is_alphanum(subtag, 5, 8) or (len(subtag) == 4 and _is_digit(subtag[0]) and _is_alphanum(subtag[1:], 3, 3))


def is_well_formed_language_tag(tag: object) -> bool:
  """Whether ``tag`` is a well-formed BCP 47 language tag.

  ``language-tag = langtag / privateuse / grandfathered``. Non-string input
  returns ``False`` rather than raising, for pydantic-shaped callers;
  ``validate_language_tag`` raises ``TypeError`` instead.
  """
  # Check before lower(): non-ASCII U+212A (Kelvin sign) folds to ASCII 'k'.
  if not isinstance(tag, str) or not tag.isascii():
    return False
  lowered = tag.lower()
  if lowered in _GRANDFATHERED_TAGS:
    return True
  subtags = tag.split("-")
  try:
    if subtags[0].lower() == "x":
      _validate_privateuse(subtags[1:], tag)
    else:
      _validate_langtag(subtags, tag)
  except ValueError:
    return False
  return True


def validate_language_tag_is_well_formed(tag: object) -> str:
  """Validate a well-formed BCP 47 language tag and return it unchanged.

  Raises ``ValueError`` with a reason when the tag is not well-formed.
  Case is preserved: tags are case-insensitive, spelling is not.
  """
  if not isinstance(tag, str):
    raise TypeError(f"expected a string, got {type(tag)!r}")
  if not is_well_formed_language_tag(tag):
    raise ValueError(f"not a well-formed BCP 47 language tag: {tag!r}")
  return tag
