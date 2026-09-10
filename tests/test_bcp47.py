"""RFC 5646 section 2.1 ABNF, not registry validity (section 2.2.9).

Reference: https://www.rfc-editor.org/rfc/rfc5646.html
The examples and grandfathered literals below come from the RFC, independently
of the implementation's tables. No network access or registry data is needed.
"""

import string

import pytest

from hypomnema.bcp47 import is_well_formed_language_tag, validate_language_tag_is_well_formed

# Appendix A: all examples before "Some Invalid Tags".
RFC_EXAMPLES = (
  "de",
  "fr",
  "ja",
  "i-enochian",
  "zh-Hant",
  "zh-Hans",
  "sr-Cyrl",
  "sr-Latn",
  "zh-cmn-Hans-CN",
  "cmn-Hans-CN",
  "zh-yue-HK",
  "yue-HK",
  "zh-Hans-CN",
  "sr-Latn-RS",
  "sl-rozaj",
  "sl-rozaj-biske",
  "sl-nedis",
  "de-CH-1901",
  "sl-IT-nedis",
  "hy-Latn-IT-arevela",
  "de-DE",
  "en-US",
  "es-419",
  "de-CH-x-phonebk",
  "az-Arab-x-AZE-derbend",
  "x-whatever",
  "qaa-Qaaa-QM-x-southern",
  "de-Qaaa",
  "sr-Latn-QM",
  "sr-Qaaa-RS",
  "en-US-u-islamcal",
  "zh-CN-a-myext-x-private",
  "en-a-myext-b-another",
)

# Section 2.1: literal alternatives, not imported from bcp47.py.
IRREGULAR_TAGS = (
  "en-GB-oed",
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
  "sgn-BE-FR",
  "sgn-BE-NL",
  "sgn-CH-DE",
)
REGULAR_TAGS = (
  "art-lojban",
  "cel-gaulish",
  "no-bok",
  "no-nyn",
  "zh-guoyu",
  "zh-hakka",
  "zh-min",
  "zh-min-nan",
  "zh-xiang",
)


@pytest.mark.parametrize("tag", RFC_EXAMPLES)
def test_rfc_examples_are_accepted(tag: str) -> None:
  assert is_well_formed_language_tag(tag)
  assert validate_language_tag_is_well_formed(tag) == tag


@pytest.mark.parametrize("tag", IRREGULAR_TAGS + REGULAR_TAGS)
def test_grandfathered_tags_are_case_insensitive(tag: str) -> None:
  # Comparison runs on lowercased input, so a per-character inversion
  # (covering both case directions) is accepted, spelling preserved.
  spelling = tag.swapcase()
  assert is_well_formed_language_tag(spelling)
  assert validate_language_tag_is_well_formed(spelling) == spelling


@pytest.mark.parametrize("tag", IRREGULAR_TAGS)
def test_irregular_tags_cannot_be_extended(tag: str) -> None:
  # An irregular literal is a complete alternative, not a langtag prefix.
  assert not is_well_formed_language_tag(f"{tag}-x-private")


@pytest.mark.parametrize("tag", REGULAR_TAGS)
def test_regular_tag_spellings_can_also_follow_the_langtag_grammar(tag: str) -> None:
  # These spellings happen to fit langtag independently of the literal table.
  assert is_well_formed_language_tag(f"{tag}-x-private")


@pytest.mark.parametrize(
  "tag",
  [
    # language: each length in 2*3ALPHA / 4ALPHA / 5*8ALPHA.
    "ab",
    "abc",
    "abcd",
    "abcde",
    "abcdef",
    "abcdefg",
    "abcdefgh",
    # extlang: zero to three 3ALPHA subtags, on 2- or 3-letter languages only.
    "ab-cde",
    "ab-cde-fgh",
    "ab-cde-fgh-ijk",
    "abc-def",
    "abc-def-ghi",
    "abc-def-ghi-jkl",
    # Each language branch may be followed by script / region / variants.
    "abcd-Latn-US-1901",
    "abcdefgh-Latn-419-abcde",
    # Optional script and region, including arbitrary syntactic values.
    "en-Abcd",
    "en-ZZ",
    "en-000",
    "en-Abcd-ZZ",
    "en-Abcd-999",
    # variant: DIGIT 3alphanum or 5*8alphanum.
    "en-0abc",
    "en-1234",
    "en-abcde",
    "en-abcdef",
    "en-abcdefg",
    "en-abcdefgh",
    "en-a1b2c",
    "en-12345678",
    "en-abcde-0abc-abcdefgh",
    # All positions present, at the extlang upper bound.
    "ab-cde-fgh-ijk-Latn-419-abcde-0abc-a-12-b-abcdefgh-x-a-12345678",
    # extension bodies: two to eight alphanumerics, one or more subtags.
    "en-a-12",
    "en-a-abc",
    "en-a-abcd",
    "en-a-abcde",
    "en-a-abcdef",
    "en-a-abcdefg",
    "en-a-abcdefgh",
    "en-a-12-abcdefgh-b-34",
    # Script/region-looking subtags after a singleton are extension data.
    "en-a-Latn-US-419",
    # privateuse: one to eight alphanumerics, one or more subtags.
    "x-a",
    "x-ab",
    "x-abc",
    "x-abcd",
    "x-abcde",
    "x-abcdef",
    "x-abcdefg",
    "x-abcdefgh",
    "x-0-a-12345678",
    "en-x-a",
    "en-a-bb-x-a",
    # Once private use starts, singleton-looking subtags are ordinary data.
    "x-x",
    "en-x-x",
    "en-x-a-b-x",
    "en-x-US-Latn-a",
    "en-a-bb-x-a-a",
  ],
)
def test_grammar_productions_accept_their_boundaries(tag: str) -> None:
  assert is_well_formed_language_tag(tag)
  assert validate_language_tag_is_well_formed(tag) == tag


@pytest.mark.parametrize("singleton", string.ascii_letters + string.digits)
def test_every_ascii_alphanumeric_can_introduce_a_sequence(singleton: str) -> None:
  # X/x introduce private use; every other character is an extension singleton.
  assert is_well_formed_language_tag(f"en-{singleton}-ab")


@pytest.mark.parametrize("singleton", string.ascii_letters + string.digits)
def test_only_private_use_allows_a_one_character_body(singleton: str) -> None:
  assert is_well_formed_language_tag(f"en-{singleton}-a") is (singleton in "xX")


@pytest.mark.parametrize(
  "tag",
  [
    # Appendix A calls the first example invalid, but section 2.2.9 makes
    # duplicate singletons/variants a validity rule, not an ABNF restriction.
    "ar-a-aaa-b-bbb-a-ccc",
    "en-a-bb-A-cc",
    "en-1901-1901",
    "sl-rozaj-ROZAJ",
    # No registry membership, extlang prefix, or variant prefix checks.
    "zzzzzzzz-Qwer-ZZ-abcde",
    "en-cmn",
    "en-biske",
    # No extension-specific semantics (the 'u' body is only checked as ABNF).
    "en-u-00",
  ],
)
def test_well_formedness_does_not_enforce_validity(tag: str) -> None:
  assert is_well_formed_language_tag(tag)
  assert validate_language_tag_is_well_formed(tag) == tag


MALFORMED_TAGS = (
  "",
  "-",
  "-en",
  "en-",
  "en--US",
  "en-a--bb",
  "en-x--a",
  "en_US",
  "en.US",
  "*",
  "*all*",
  # language: too short/long or not all letters.
  "a",
  "i",
  "a-DE",  # Appendix A.
  "abcdefghi",
  "12",
  "e1",
  "ab1",
  "abc1",
  "abcd1",
  # extlang: excess count, wrong language branch, or wrong position.
  "ab-cde-fgh-ijk-lmn",
  "abc-def-ghi-jkl-mno",
  "abcd-efg",
  "abcde-fgh",
  "abcdefgh-ijk",
  "en-Latn-cmn",
  "en-US-cmn",
  "en-abcde-cmn",
  # script/region: wrong length, repeated, or out of order.
  "en-A1cd",
  "en-Latn-Cyrl",
  "en-US-Latn",
  "en-12",
  "en-U1",
  "en-1US",
  "en-US-GB",
  "de-419-DE",  # Appendix A.
  "en-abcde-US",
  # variant: put it after a region to prevent script/extlang interpretations.
  "en-US-abc",
  "en-US-abcd",
  "en-US-abc1",
  "en-US-1ab",
  "en-US-abcdefghi",
  "en-US-123456789",
  # extension: missing body, too-long body, or invalid characters.
  "en-a",
  "en-a-b",
  "en-a-b-cc",
  "en-a-x-private",
  "en-a-abcdefghi",
  "en-a-bb-c",
  "en-a-bb-c-d",
  "en-a-bb-!",
  "en-!-bb",
  # privateuse: must have at least one body subtag, each at most eight.
  "x",
  "X",
  "x-",
  "x-abcdefghi",
  "x-a-abcdefghi",
  "en-x",
  "en-x-",
  "en-x-abcdefghi",
  "en-a-bb-x",
  "en-x-a-abcdefghi",
  # Grandfathered lookalikes are not additional literal alternatives.
  "i-am",
  "i-amis",
  "i-madeup",
  "en-GB-oe",
  "sgn-BE-GB",
  # No whitespace, controls, punctuation, or multiple tags in one input.
  " en-US",
  "en-US ",
  "en\tUS",
  "en\nUS",
  "en\n",
  "en\r\n",
  "en\x00",
  "en US",
  "en/US",
  "en,fr",
  "en-US;q=0.8",
)


@pytest.mark.parametrize("tag", MALFORMED_TAGS)
def test_predicate_rejects_malformed_tags(tag: str) -> None:
  assert not is_well_formed_language_tag(tag)


@pytest.mark.parametrize("tag", MALFORMED_TAGS)
def test_validator_raises_for_malformed_tags(tag: str) -> None:
  with pytest.raises(ValueError):
    validate_language_tag_is_well_formed(tag)


@pytest.mark.parametrize(
  "tag",
  [
    "én",
    "ｅｎ",
    "en-cmñ",
    "en-Latñ",
    "en-ÜS",
    "en-٤١٩",
    "en-１９０１",
    "en-1abé",
    "en-abcdé",
    "en-a-éé",
    "x-é",
    "en-x-é",
    "en\u2010US",  # Unicode hyphen, not U+002D.
    "en\u2011US",  # Non-breaking hyphen.
    "en\u200b-US",  # Zero-width space.
    "en\u00a0",  # Non-breaking space.
    "\ud800",  # A Python string need not be valid Unicode scalar text.
    # Regression: U+212A lowercases to ASCII 'k'. Validate before folding.
    "i-\u212alingon",
    "I-\u212aLINGON",
    "en-\u212a-ab",
    "en-a-bb-\u212a-cc",
    "x-\u212a",
    # Related Unicode case traps must not expand the ASCII repertoire.
    "\u0130-ami",  # Capital I with dot.
    "\u0131-ami",  # Dotless i.
    "\u017fgn-BE-FR",  # Long s.
  ],
)
def test_non_ascii_is_rejected_in_every_production(tag: str) -> None:
  assert not is_well_formed_language_tag(tag)
  with pytest.raises(ValueError):
    validate_language_tag_is_well_formed(tag)


@pytest.mark.parametrize(
  "tag", ["mn-Cyrl-MN", "MN-cYRL-mn", "mN-cYrL-Mn", "eN-a-AbCd-X-pRiVaTe", "X-aBc-123", "EN-GB-OED"]
)
def test_validation_preserves_spelling(tag: str) -> None:
  assert validate_language_tag_is_well_formed(tag) == tag


@pytest.mark.parametrize("value", [None, True, False, 42, 1.5, b"en", ["en"], ("en",), {"tag": "en"}])
def test_predicate_returns_false_for_non_strings(value: object) -> None:
  assert is_well_formed_language_tag(value) is False


@pytest.mark.parametrize("value", [None, True, False, 42, 1.5, b"en", ["en"], ("en",), {"tag": "en"}])
def test_validator_raises_type_error_for_non_strings(value: object) -> None:
  with pytest.raises(TypeError):
    validate_language_tag_is_well_formed(value)
