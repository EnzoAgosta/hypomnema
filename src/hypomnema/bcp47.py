"""Check BCP 47 language-tag syntax using the RFC 5646 grammar.

These checks establish well-formedness, not registry validity. They do not
check registered subtags, deprecation, suppress-script rules, or duplicate
extension singletons. Comparisons are case-insensitive and accepted tags
retain their original spelling. Parsing follows the grammar from left to
right without backtracking.
"""

from collections.abc import Sequence

from hypomnema.errors import LanguageTagError

__all__ = ["is_well_formed_language_tag", "validate_well_formed_language_tag"]


_IRREGULAR_TAGS = frozenset(
  (
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
  )
)
"""The ABNF's ``irregular`` production, verbatim (lowercased).

None of these match ``langtag``, so the set is load-bearing: the ``i-*`` tags
fail ``language = 2*8ALPHA``, and ``en-gb-oed`` / ``sgn-be-*`` dead-end on a
3ALPHA or 2ALPHA subtag after the region.

The ABNF's ``regular`` production is deliberately *not* listed: every tag in
it already matches ``langtag``, either as language + extlang ("no-bok",
"zh-min", "zh-min-nan") or as language + variant ("art-lojban",
"cel-gaulish", "zh-guoyu", "zh-hakka", "zh-xiang"). Listing it could not
change any answer here, and a lookup table that never fires is a place for
bugs to hide. See ``test_regular_grandfathered_tags_match_langtag``, which
pins that claim so it fails loudly if it ever stops holding.
"""


class _Malformed(ValueError):
  """Carry a grammar failure reason until the public API adds the tag."""


# Character classes. The length bound comes first: it short-circuits before
# the string scans, and it keeps each predicate a one-to-one match for an
# ABNF repetition like "2*8alphanum".
#
# The isascii() calls are redundant while the only caller is
# validate_well_formed_language_tag, which rejects non-ASCII input up front.
# They stay because these predicates are the module's grammar primitives and
# must hold on their own -- do not drop them "because the entry point already
# checked", and do not drop the entry-point check either (see U+212A below).


def _is_alpha(text: str, min_len: int, max_len: int) -> bool:
  """Return whether ASCII letters fill the inclusive length range."""
  return min_len <= len(text) <= max_len and text.isascii() and text.isalpha()


def _is_digits(text: str, min_len: int, max_len: int) -> bool:
  """Return whether ASCII digits fill the inclusive length range."""
  return min_len <= len(text) <= max_len and text.isascii() and text.isdigit()


def _is_alphanum(text: str, min_len: int, max_len: int) -> bool:
  """Return whether ASCII letters or digits fill the inclusive length range."""
  return min_len <= len(text) <= max_len and text.isascii() and text.isalnum()


def _is_script(subtag: str) -> bool:
  """Return whether a script subtag contains exactly four ASCII letters."""
  return _is_alpha(subtag, 4, 4)


def _is_region(subtag: str) -> bool:
  """Return whether a region contains two ASCII letters or three digits."""
  return _is_alpha(subtag, 2, 2) or _is_digits(subtag, 3, 3)


def _is_variant(subtag: str) -> bool:
  """Match five to eight alphanumerics, or a digit plus three alphanumerics."""
  return _is_alphanum(subtag, 5, 8) or (_is_alphanum(subtag, 4, 4) and _is_digits(subtag[0], 1, 1))


def _is_extension_singleton(subtag: str) -> bool:
  """Match one ASCII letter or digit other than the private-use marker x."""
  return _is_alphanum(subtag, 1, 1) and subtag not in ("x", "X")


def _parse_language(subtags: Sequence[str]) -> int:
  """Consume a language and up to three permitted extended-language subtags.

  Args:
      subtags: Nonempty sequence of hyphen-separated subtags.

  Returns:
      Index of the first subtag after the language and any extended languages.

  Raises:
      _Malformed: The first subtag is not two through eight ASCII letters.
  """
  language = subtags[0]
  if not _is_alpha(language, 2, 8):
    raise _Malformed(f"malformed language subtag {language!r}")
  index = 1
  if len(language) in (2, 3):
    # extlang = 3ALPHA *2("-" 3ALPHA) -- at most three
    extlangs = 0
    while extlangs < 3 and index < len(subtags) and _is_alpha(subtags[index], 3, 3):
      extlangs += 1
      index += 1
  return index


def _parse_extensions(subtags: Sequence[str], index: int) -> int:
  """Consume extension sequences starting at an index.

  Duplicate singleton identifiers are accepted as grammatically well-formed.

  Args:
      subtags: Hyphen-separated language-tag components.
      index: Index of the next subtag to inspect.

  Returns:
      Index of the first subtag outside the extension sequences.

  Raises:
      _Malformed: An extension lacks a body or has a body subtag that is not
          two through eight ASCII alphanumeric characters.
  """
  while index < len(subtags) and _is_extension_singleton(subtags[index]):
    singleton = subtags[index]
    index += 1
    body_count = 0
    # A length-1 subtag ends this extension: it is the next singleton, the
    # private-use "x", or malformed -- the caller decides which.
    while index < len(subtags) and len(subtags[index]) != 1:
      if not _is_alphanum(subtags[index], 2, 8):
        raise _Malformed(f"malformed extension subtag {subtags[index]!r}")
      body_count += 1
      index += 1
    if body_count == 0:
      raise _Malformed(f"extension {singleton!r} without subtags")
  return index


def _parse_privateuse(subtags: Sequence[str], index: int) -> None:
  """Validate the remaining subtags after a private-use marker.

  Args:
      subtags: Hyphen-separated language-tag components.
      index: Index immediately after the private-use marker x.

  Raises:
      _Malformed: No subtags remain, or a remaining subtag is not one through
          eight ASCII alphanumeric characters.
  """
  if index >= len(subtags):
    raise _Malformed("private-use singleton without subtags")
  for subtag in subtags[index:]:
    if not _is_alphanum(subtag, 1, 8):
      raise _Malformed(f"malformed private-use subtag {subtag!r}")


def _parse_langtag(subtags: Sequence[str]) -> None:
  """Validate a nonempty sequence against the ordinary language-tag grammar.

  Consumes language, optional script and region, variants, extensions, and
  optional trailing private use. Raises _Malformed at the first grammar error.
  """
  index = _parse_language(subtags)
  if index < len(subtags) and _is_script(subtags[index]):
    index += 1
  if index < len(subtags) and _is_region(subtags[index]):
    index += 1
  while index < len(subtags) and _is_variant(subtags[index]):
    index += 1
  index = _parse_extensions(subtags, index)
  if index < len(subtags):
    # Only a trailing private-use sequence may follow the extensions.
    if subtags[index].lower() != "x":
      raise _Malformed(f"unexpected subtag {subtags[index]!r}")
    _parse_privateuse(subtags, index + 1)


def validate_well_formed_language_tag(tag: object) -> str:
  """Validate a BCP 47 language tag without consulting a subtag registry.

  Args:
      tag: String to check against the language-tag grammar, including
          private-use and grandfathered forms.

  Returns:
      The original string with its case unchanged.

  Raises:
      TypeError: The input is not a string.
      LanguageTagError: The string is not grammatically well-formed. The error
          retains the tag and the reason for rejection.
  """
  if not isinstance(tag, str):
    raise TypeError(f"expected a string, got {type(tag)!r}")
  try:
    # Check before lower(): non-ASCII U+212A (KELVIN SIGN) folds to ASCII "k".
    if not tag.isascii():
      raise _Malformed("non-ASCII characters")
    if tag.lower() in _IRREGULAR_TAGS:
      return tag
    subtags = tag.split("-")
    if subtags[0].lower() == "x":
      _parse_privateuse(subtags, 1)
    else:
      _parse_langtag(subtags)
  except _Malformed as exc:
    raise LanguageTagError(tag, str(exc)) from None
  return tag


def is_well_formed_language_tag(tag: object) -> bool:
  """Return whether an object is a grammatically well-formed BCP 47 tag.

  Args:
      tag: Candidate tag. Non-string objects return False.

  Returns:
      True for accepted syntax, regardless of registry membership. Use
      ``validate_well_formed_language_tag`` to obtain a rejection reason.
  """
  try:
    validate_well_formed_language_tag(tag)
  except LanguageTagError, TypeError:
    return False
  return True
