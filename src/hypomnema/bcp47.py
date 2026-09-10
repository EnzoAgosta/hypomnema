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

The grammar is unambiguous at every decision point, so the single greedy
left-to-right pass below never needs to backtrack: after a 2*3ALPHA
language only extlang can be 3ALPHA; only script can be 4ALPHA; variant's
4-character branch requires a leading DIGIT, so it cannot collide with
script; region's 3DIGIT cannot collide with that variant branch.
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
  """Internal: carries the reason only; the offending tag is added at the
  public boundary, so the message format lives in exactly one place."""


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
  """``ALPHA``: ASCII letters only, within a length range."""
  return min_len <= len(text) <= max_len and text.isascii() and text.isalpha()


def _is_digits(text: str, min_len: int, max_len: int) -> bool:
  """``DIGIT``: ASCII digits only, within a length range."""
  return min_len <= len(text) <= max_len and text.isascii() and text.isdigit()


def _is_alphanum(text: str, min_len: int, max_len: int) -> bool:
  """``alphanum``: ASCII letters or digits, within a length range."""
  return min_len <= len(text) <= max_len and text.isascii() and text.isalnum()


def _is_script(subtag: str) -> bool:
  """``script = 4ALPHA``."""
  return _is_alpha(subtag, 4, 4)


def _is_region(subtag: str) -> bool:
  """``region = 2ALPHA / 3DIGIT``."""
  return _is_alpha(subtag, 2, 2) or _is_digits(subtag, 3, 3)


def _is_variant(subtag: str) -> bool:
  """``variant = 5*8alphanum / (DIGIT 3alphanum)``."""
  return _is_alphanum(subtag, 5, 8) or (_is_alphanum(subtag, 4, 4) and _is_digits(subtag[0], 1, 1))


def _is_extension_singleton(subtag: str) -> bool:
  """``singleton``: one alphanum, excluding "x"/"X", which starts private use.

  The membership test uses a tuple, not the string ``"xX"``: ``"" in "xX"`` is
  true, and an empty subtag reaches here from a doubled or trailing hyphen.
  """
  return _is_alphanum(subtag, 1, 1) and subtag not in ("x", "X")


def _parse_language(subtags: Sequence[str]) -> int:
  """``language = 2*3ALPHA ["-" extlang] / 4ALPHA / 5*8ALPHA``; returns the
  index of the first subtag after the language.

  The three alternatives share ``ALPHA`` and together span lengths 2-8
  (4ALPHA is reserved for future use, 5*8ALPHA covers registered language
  subtags); only the 2-3 length branch admits extlangs.

  ``subtags`` must be non-empty; every caller gets it from ``str.split``,
  which never returns an empty list.
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
  """``*("-" extension)`` where ``extension = singleton 1*("-" (2*8alphanum))``;
  returns the index of the first subtag that is not part of an extension.

  Duplicate singletons affect validity, not ABNF well-formedness (2.2.9).
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
  """``privateuse = "x" 1*("-" (1*8alphanum))``, with ``index`` pointing just
  past the "x". Private use terminates the tag, so this consumes the rest."""
  if index >= len(subtags):
    raise _Malformed("private-use singleton without subtags")
  for subtag in subtags[index:]:
    if not _is_alphanum(subtag, 1, 8):
      raise _Malformed(f"malformed private-use subtag {subtag!r}")


def _parse_langtag(subtags: Sequence[str]) -> None:
  """``langtag = language ["-" script] ["-" region] *("-" variant)
  *("-" extension) ["-" privateuse]``."""
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
  """Validate a well-formed BCP 47 language tag and return it unchanged.

  ``language-tag = langtag / privateuse / grandfathered``. Raises ``TypeError``
  for non-string input and ``ValueError``, with the specific reason, when the
  tag is not well-formed. Case is preserved: tags are case-insensitive,
  spelling is not.
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
  """Whether ``tag`` is a well-formed BCP 47 language tag.

  Non-string input returns ``False`` rather than raising, for pydantic-shaped
  callers; ``validate_well_formed_language_tag`` raises ``TypeError`` and
  reports *why* a string was rejected.
  """
  try:
    validate_well_formed_language_tag(tag)
  except LanguageTagError, TypeError:
    return False
  return True
