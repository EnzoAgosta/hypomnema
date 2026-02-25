"""Tests for hypomnema.xml.utils module.

Tests cover:
- normalize_encoding: encoding name normalization
- make_usable_path: path resolution and directory creation
- QNameLike: protocol compliance
- validate_ncname: NCName validation (XML Namespaces §4)
- fast_validate_uri: fast URI-reference validation (RFC 3986 §4.1)
- validate_uri: detailed URI-reference validation with diagnostics
"""

import tempfile
from pathlib import Path

import pytest

from hypomnema.base.errors import InvalidNCNameError
from hypomnema.xml import utils
from hypomnema.xml.utils import (
  QNameLike,
  _check_characters,
  _check_percent_encoding,
  _find_bad_char,
  _find_bad_pchar_qf,
  _raise_path_error,
  _validate_authority_detail,
  _validate_nc_start_char,
  _validate_ncname_char,
  _validate_path,
  fast_validate_uri,
  make_usable_path,
  normalize_encoding,
  validate_ncname,
  validate_uri,
)


class TestNormalizeEncoding:
  """Tests for normalize_encoding function."""

  def test_none_returns_utf8(self) -> None:
    assert normalize_encoding(None) == "utf-8"

  def test_unicode_returns_utf8(self) -> None:
    assert normalize_encoding("unicode") == "utf-8"

  def test_utf8_normalized(self) -> None:
    assert normalize_encoding("UTF-8") == "utf-8"

  def test_utf8_lowercase(self) -> None:
    assert normalize_encoding("utf-8") == "utf-8"

  def test_latin1_normalized(self) -> None:
    assert normalize_encoding("latin-1") == "iso8859-1"

  def test_iso88591_normalized(self) -> None:
    assert normalize_encoding("ISO-8859-1") == "iso8859-1"

  def test_cp1252_normalized(self) -> None:
    assert normalize_encoding("CP1252") == "cp1252"

  def test_ascii_normalized(self) -> None:
    assert normalize_encoding("ASCII") == "ascii"

  def test_unknown_encoding_raises(self) -> None:
    with pytest.raises(ValueError, match="Unknown encoding"):
      normalize_encoding("invalid-encoding-xyz")

  def test_empty_string_raises(self) -> None:
    with pytest.raises(ValueError, match="Unknown encoding"):
      normalize_encoding("")

  def test_unicode_uppercase_not_special(self) -> None:
    with pytest.raises(ValueError, match="Unknown encoding"):
      normalize_encoding("UNICODE")

  def test_unicode_mixed_case_not_special(self) -> None:
    with pytest.raises(ValueError, match="Unknown encoding"):
      normalize_encoding("UnIcOdE")


class TestMakeUsablePath:
  """Tests for make_usable_path function."""

  def test_string_path_resolves(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      path = make_usable_path(tmpdir, mkdir=False)
      assert path.is_absolute()
      assert path == Path(tmpdir).resolve()

  def test_pathlike_resolves(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      path = make_usable_path(Path(tmpdir), mkdir=False)
      assert path.is_absolute()

  def test_creates_parent_directories(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      target = Path(tmpdir) / "subdir" / "file.txt"
      path = make_usable_path(str(target), mkdir=True)
      assert path.parent.exists()

  def test_mkdir_false_no_create(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      target = Path(tmpdir) / "nonexistent" / "file.txt"
      path = make_usable_path(str(target), mkdir=False)
      assert not path.parent.exists()

  def test_expands_user_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/tmp/testhome")
    path = make_usable_path("~/test", mkdir=False)
    assert "~" not in str(path)

  def test_default_mkdir_true(self) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
      target = Path(tmpdir) / "subdir2" / "file.txt"
      path = make_usable_path(str(target))
      assert path.parent.exists()


class TestQNameLike:
  """Tests for QNameLike protocol."""

  def test_object_with_text_property(self) -> None:
    class MockQName:
      @property
      def text(self) -> str:
        return "test:name"

    obj = MockQName()
    assert isinstance(obj, QNameLike)

  def test_object_without_text_property(self) -> None:
    class NotQName:
      pass

    obj = NotQName()
    assert not isinstance(obj, QNameLike)

  def test_object_with_text_method_not_property(self) -> None:
    class NotProperty:
      def text(self) -> str:
        return "test"

    obj = NotProperty()
    assert isinstance(obj, QNameLike)


class TestValidateNcStartChar:
  """Tests for _validate_nc_start_char internal function."""

  def test_underscore_valid(self) -> None:
    _validate_nc_start_char("_")

  def test_letter_valid(self) -> None:
    _validate_nc_start_char("a")
    _validate_nc_start_char("Z")

  def test_digit_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name start"):
      _validate_nc_start_char("1")

  def test_hyphen_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name start"):
      _validate_nc_start_char("-")

  def test_period_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name start"):
      _validate_nc_start_char(".")

  def test_colon_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name start"):
      _validate_nc_start_char(":")

  def test_zero_width_non_joiner_valid(self) -> None:
    _validate_nc_start_char("\u200c")

  def test_zero_width_joiner_valid(self) -> None:
    _validate_nc_start_char("\u200d")

  def test_space_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name start"):
      _validate_nc_start_char(" ")

  def test_unicode_letter_valid(self) -> None:
    _validate_nc_start_char("\u03b1")


class TestValidateNcnameChar:
  """Tests for _validate_ncname_char internal function."""

  def test_digit_valid(self) -> None:
    _validate_ncname_char("0")
    _validate_ncname_char("9")

  def test_hyphen_valid(self) -> None:
    _validate_ncname_char("-")

  def test_period_valid(self) -> None:
    _validate_ncname_char(".")

  def test_middle_dot_valid(self) -> None:
    _validate_ncname_char("\u00b7")

  def test_colon_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name char"):
      _validate_ncname_char(":")

  def test_space_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name char"):
      _validate_ncname_char(" ")

  def test_letter_valid(self) -> None:
    _validate_ncname_char("a")
    _validate_ncname_char("Z")

  def test_underscore_valid(self) -> None:
    _validate_ncname_char("_")

  def test_at_sign_invalid(self) -> None:
    with pytest.raises(ValueError, match="not a valid xml name char"):
      _validate_ncname_char("@")


class TestValidateNcname:
  """Tests for validate_ncname public function."""

  def test_valid_simple_name(self) -> None:
    validate_ncname("validName")

  def test_valid_underscore_start(self) -> None:
    validate_ncname("_private")

  def test_valid_with_hyphen(self) -> None:
    validate_ncname("my-element")

  def test_valid_with_period(self) -> None:
    validate_ncname("my.element")

  def test_valid_with_digits(self) -> None:
    validate_ncname("name123")

  def test_valid_unicode_name(self) -> None:
    validate_ncname("\u03b1\u03b2\u03b3")

  def test_empty_string_raises(self) -> None:
    with pytest.raises(InvalidNCNameError, match="is not a valid NCName"):
      validate_ncname("")

  def test_starts_with_digit_raises(self) -> None:
    with pytest.raises(InvalidNCNameError):
      validate_ncname("1invalid")

  def test_starts_with_hyphen_raises(self) -> None:
    with pytest.raises(InvalidNCNameError):
      validate_ncname("-invalid")

  def test_starts_with_period_raises(self) -> None:
    with pytest.raises(InvalidNCNameError):
      validate_ncname(".invalid")

  def test_contains_colon_raises(self) -> None:
    with pytest.raises(InvalidNCNameError):
      validate_ncname("prefix:local")

  def test_contains_space_raises(self) -> None:
    with pytest.raises(InvalidNCNameError):
      validate_ncname("my name")

  def test_single_underscore_valid(self) -> None:
    validate_ncname("_")

  def test_single_letter_valid(self) -> None:
    validate_ncname("a")


class TestCheckCharacters:
  """Tests for _check_characters internal function."""

  def test_valid_ascii_passes(self) -> None:
    _check_characters("http://example.com/path?query=value#fragment")

  def test_non_ascii_raises(self) -> None:
    with pytest.raises(ValueError, match="Non-ASCII character"):
      _check_characters("http://example.com/\u00e9")

  def test_control_char_raises(self) -> None:
    with pytest.raises(ValueError, match="Control character"):
      _check_characters("http://example.com/\x00")

  def test_tab_control_char_raises(self) -> None:
    with pytest.raises(ValueError, match="Control character"):
      _check_characters("http://example.com/\t")

  def test_unencoded_space_raises(self) -> None:
    with pytest.raises(ValueError, match="Unencoded space"):
      _check_characters("http://example.com/path with space")

  def test_forbidden_char_angle_bracket_raises(self) -> None:
    with pytest.raises(ValueError, match="not permitted in a URI"):
      _check_characters("http://example.com/<script>")

  def test_forbidden_char_backslash_raises(self) -> None:
    with pytest.raises(ValueError, match="not permitted in a URI"):
      _check_characters("http://example.com\\path")

  def test_forbidden_char_double_quote_raises(self) -> None:
    with pytest.raises(ValueError, match="not permitted in a URI"):
      _check_characters('http://example.com/"test"')

  def test_forbidden_char_pipe_raises(self) -> None:
    with pytest.raises(ValueError, match="not permitted in a URI"):
      _check_characters("http://example.com|path")

  def test_forbidden_char_brace_raises(self) -> None:
    with pytest.raises(ValueError, match="not permitted in a URI"):
      _check_characters("http://example.com/{var}")

  def test_del_char_control_raises(self) -> None:
    with pytest.raises(ValueError, match="Control character"):
      _check_characters("http://example.com/\x7f")


class TestCheckPercentEncoding:
  """Tests for _check_percent_encoding internal function."""

  def test_no_percent_encoding_passes(self) -> None:
    _check_percent_encoding("http://example.com/path")

  def test_valid_percent_encoding_passes(self) -> None:
    _check_percent_encoding("http://example.com/%20space")
    _check_percent_encoding("http://example.com/%3Fquestion")

  def test_lowercase_hex_valid(self) -> None:
    _check_percent_encoding("http://example.com/%2f")

  def test_incomplete_percent_at_end_raises(self) -> None:
    with pytest.raises(ValueError, match="Incomplete percent-encoding"):
      _check_percent_encoding("http://example.com/%2")

  def test_percent_only_at_end_raises(self) -> None:
    with pytest.raises(ValueError, match="Incomplete percent-encoding"):
      _check_percent_encoding("http://example.com/%")

  def test_invalid_hex_digits_raises(self) -> None:
    with pytest.raises(ValueError, match="Invalid percent-encoding"):
      _check_percent_encoding("http://example.com/%GG")

  def test_percent_without_hex_raises(self) -> None:
    with pytest.raises(ValueError, match="Invalid percent-encoding"):
      _check_percent_encoding("http://example.com/%ZZ")

  def test_multiple_valid_percent_encodings(self) -> None:
    _check_percent_encoding("http://example.com/%20%3F%2F")


class TestFindBadChar:
  """Tests for _find_bad_char internal function."""

  def test_no_bad_char_returns_unknown(self) -> None:
    import re

    result = _find_bad_char("abc", re.compile(r"[a-z]"))
    assert result == "<unknown>"

  def test_finds_first_bad_char(self) -> None:
    import re

    result = _find_bad_char("ab!c", re.compile(r"[a-z]"))
    assert result == "!"

  def test_skips_percent_encoding(self) -> None:
    import re

    result = _find_bad_char("a%20b!c", re.compile(r"[a-z]"))
    assert result == "!"

  def test_empty_string_returns_unknown(self) -> None:
    import re

    result = _find_bad_char("", re.compile(r"[a-z]"))
    assert result == "<unknown>"


class TestFindBadPcharQf:
  """Tests for _find_bad_pchar_qf internal function."""

  def test_valid_pchar_returns_unknown(self) -> None:
    result = _find_bad_pchar_qf("abc123")
    assert result == "<unknown>"

  def test_finds_invalid_char(self) -> None:
    result = _find_bad_pchar_qf("abc<def")
    assert result == "<"

  def test_slash_valid(self) -> None:
    result = _find_bad_pchar_qf("a/b/c")
    assert result == "<unknown>"

  def test_question_mark_valid(self) -> None:
    result = _find_bad_pchar_qf("a?b")
    assert result == "<unknown>"

  def test_percent_encoded_skipped(self) -> None:
    result = _find_bad_pchar_qf("%20%3F")
    assert result == "<unknown>"


class TestValidateAuthorityDetail:
  """Tests for _validate_authority_detail internal function."""

  def test_simple_host(self) -> None:
    with pytest.raises(ValueError, match="is invalid per RFC 3986"):
      _validate_authority_detail("example.com")

  def test_host_with_port(self) -> None:
    with pytest.raises(ValueError, match="is invalid per RFC 3986"):
      _validate_authority_detail("example.com:8080")

  def test_userinfo_and_host(self) -> None:
    with pytest.raises(ValueError, match="is invalid per RFC 3986"):
      _validate_authority_detail("user@example.com")

  def test_invalid_userinfo_char(self) -> None:
    with pytest.raises(ValueError, match="Userinfo.*contains invalid character"):
      _validate_authority_detail("user<name>@example.com")

  def test_unclosed_bracket_in_ip_literal(self) -> None:
    with pytest.raises(ValueError, match="unclosed '\\['"):
      _validate_authority_detail("[::1")

  def test_unexpected_chars_after_ip_literal(self) -> None:
    with pytest.raises(ValueError, match="Unexpected characters"):
      _validate_authority_detail("[::1]extra")

  def test_invalid_port(self) -> None:
    with pytest.raises(ValueError, match="Host.*contains invalid character"):
      _validate_authority_detail("example.com:abc")

  def test_ipv6_malformed(self) -> None:
    with pytest.raises(ValueError, match="IPv6 address.*is malformed"):
      _validate_authority_detail("[invalid]")

  def test_ipvfuture_malformed(self) -> None:
    with pytest.raises(ValueError, match="is invalid per RFC 3986"):
      _validate_authority_detail("[v1.invalid]")

  def test_port_after_ip_literal(self) -> None:
    with pytest.raises(ValueError, match="is invalid per RFC 3986"):
      _validate_authority_detail("[::1]:8080")

  def test_invalid_port_after_ip_literal(self) -> None:
    with pytest.raises(ValueError, match="Port.*is invalid"):
      _validate_authority_detail("[::1]:abc")

  def test_ipvfuture_starting_with_v_raises_malformed_error(self) -> None:
    with pytest.raises(ValueError, match="IPvFuture address.*is malformed"):
      _validate_authority_detail("[vx]")


class TestRaisePathError:
  """Tests for _raise_path_error internal function."""

  def test_always_raises(self) -> None:
    with pytest.raises(ValueError):
      _raise_path_error("/invalid/path", "test context")

  def test_message_contains_path(self) -> None:
    with pytest.raises(ValueError, match="/invalid/path"):
      _raise_path_error("/invalid/path", "test context")


class TestValidatePath:
  """Tests for _validate_path internal function."""

  def test_empty_path_valid(self) -> None:
    _validate_path("", has_scheme=False, has_authority=False)

  def test_path_with_authority_abempty(self) -> None:
    _validate_path("/segment/subsegment", has_scheme=True, has_authority=True)

  def test_empty_path_with_authority(self) -> None:
    _validate_path("", has_scheme=True, has_authority=True)

  def test_path_starts_with_double_slash_no_authority_raises(self) -> None:
    with pytest.raises(ValueError, match="begins with '//'"):
      _validate_path("//path", has_scheme=False, has_authority=False)

  def test_path_starts_with_double_slash_with_scheme_no_authority_raises(self) -> None:
    with pytest.raises(ValueError, match="begins with '//'"):
      _validate_path("//path", has_scheme=True, has_authority=False)

  def test_relative_path_first_segment_with_colon_raises(self) -> None:
    with pytest.raises(ValueError, match="first segment.*contains a colon"):
      _validate_path("seg:ment/path", has_scheme=False, has_authority=False)

  def test_absolute_path_valid_no_scheme(self) -> None:
    _validate_path("/path/to/resource", has_scheme=False, has_authority=False)

  def test_rootless_path_with_scheme(self) -> None:
    _validate_path("path/to/resource", has_scheme=True, has_authority=False)

  def test_path_with_authority_invalid_raises(self) -> None:
    with pytest.raises(ValueError, match="Path.*is invalid when an authority is present"):
      _validate_path("invalid", has_scheme=True, has_authority=True)

  def test_path_invalid_for_uri_without_authority(self) -> None:
    with pytest.raises(ValueError, match="Path.*contains invalid character"):
      _validate_path("path^invalid", has_scheme=True, has_authority=False)

  def test_path_invalid_for_relative_reference(self) -> None:
    with pytest.raises(ValueError, match="Path.*contains invalid character"):
      _validate_path("path^invalid", has_scheme=False, has_authority=False)


class TestFastValidateUri:
  """Tests for fast_validate_uri function."""

  def test_valid_http_uri(self) -> None:
    fast_validate_uri("http://example.com/path")

  def test_valid_https_uri(self) -> None:
    fast_validate_uri("https://example.com/path")

  def test_valid_relative_ref(self) -> None:
    fast_validate_uri("/path/to/resource")

  def test_valid_uri_with_query(self) -> None:
    fast_validate_uri("http://example.com/path?query=value")

  def test_valid_uri_with_fragment(self) -> None:
    fast_validate_uri("http://example.com/path#fragment")

  def test_valid_uri_with_query_and_fragment(self) -> None:
    fast_validate_uri("http://example.com/path?query=value#fragment")

  def test_valid_relative_ref_noscheme(self) -> None:
    fast_validate_uri("path/to/resource")

  def test_non_string_raises(self) -> None:
    with pytest.raises(ValueError, match="Expected str"):
      fast_validate_uri(123)  # type: ignore[arg-type]

  def test_non_string_none_raises(self) -> None:
    with pytest.raises(ValueError, match="Expected str"):
      fast_validate_uri(None)  # type: ignore[arg-type]

  def test_invalid_uri_raises(self) -> None:
    with pytest.raises(ValueError, match="Invalid URI-reference"):
      fast_validate_uri("http://[invalid")


class TestValidateUri:
  """Tests for validate_uri function (detailed validation)."""

  def test_valid_http_uri(self) -> None:
    validate_uri("http://example.com/path")

  def test_valid_https_uri(self) -> None:
    validate_uri("https://example.com/path")

  def test_valid_uri_with_port(self) -> None:
    validate_uri("http://example.com:8080/path")

  def test_valid_uri_with_userinfo(self) -> None:
    validate_uri("http://user@example.com/path")

  def test_valid_uri_with_userinfo_and_password(self) -> None:
    validate_uri("http://user:pass@example.com/path")

  def test_valid_uri_with_query(self) -> None:
    validate_uri("http://example.com/path?query=value")

  def test_valid_uri_with_fragment(self) -> None:
    validate_uri("http://example.com/path#fragment")

  def test_valid_relative_ref(self) -> None:
    validate_uri("/path/to/resource")

  def test_valid_relative_ref_with_query(self) -> None:
    validate_uri("/path?query=value")

  def test_valid_relative_ref_with_fragment(self) -> None:
    validate_uri("/path#fragment")

  def test_valid_relative_ref_noscheme(self) -> None:
    validate_uri("path/to/resource")

  def test_valid_ipv4_uri(self) -> None:
    validate_uri("http://192.168.1.1/path")

  def test_valid_ipv6_uri(self) -> None:
    validate_uri("http://[::1]/path")

  def test_valid_ipv6_full_uri(self) -> None:
    validate_uri("http://[2001:db8::1]/path")

  def test_valid_empty_query(self) -> None:
    validate_uri("http://example.com/path?")

  def test_valid_empty_fragment(self) -> None:
    validate_uri("http://example.com/path#")

  def test_non_string_raises(self) -> None:
    with pytest.raises(ValueError, match="Expected str"):
      validate_uri(123)  # type: ignore[arg-type]

  def test_scheme_invalid_start_raises(self) -> None:
    with pytest.raises(ValueError, match="Scheme.*must start with a letter"):
      validate_uri("1scheme://example.com")

  def test_scheme_invalid_char_raises(self) -> None:
    with pytest.raises(ValueError, match="Scheme.*contains invalid character"):
      validate_uri("sch_eme://example.com")

  def test_fragment_invalid_char_raises(self) -> None:
    with pytest.raises(ValueError, match="Fragment.*contains invalid character"):
      validate_uri("http://example.com/path#frag[ment")

  def test_query_invalid_char_raises(self) -> None:
    with pytest.raises(ValueError, match="Query.*contains invalid character"):
      validate_uri("http://example.com/path?query^value")

  def test_empty_string_valid(self) -> None:
    validate_uri("")

  def test_path_only(self) -> None:
    validate_uri("/path/to/resource")

  def test_scheme_only(self) -> None:
    validate_uri("http:")

  def test_scheme_with_double_slash_only(self) -> None:
    validate_uri("http://")

  def test_percent_encoded_path(self) -> None:
    validate_uri("http://example.com/path%20with%20spaces")

  def test_percent_encoded_query(self) -> None:
    validate_uri("http://example.com/path?query=%3Cvalue%3E")

  def test_authority_with_unclosed_bracket_raises(self) -> None:
    with pytest.raises(ValueError, match="unclosed '\\['"):
      validate_uri("http://[::1/path")


class TestValidateUriEdgeCases:
  """Additional edge case tests for validate_uri."""

  def test_ipvfuture_valid(self) -> None:
    validate_uri("http://[v1.example]/path")

  def test_reg_name_with_sub_delims(self) -> None:
    validate_uri("http://example-test.com/path")

  def test_empty_path_with_scheme_and_authority(self) -> None:
    validate_uri("http://example.com")

  def test_double_slash_in_path(self) -> None:
    validate_uri("http://example.com//double//slash")

  def test_trailing_slash(self) -> None:
    validate_uri("http://example.com/path/")

  def test_leading_slash_no_scheme(self) -> None:
    validate_uri("/path")

  def test_no_leading_slash_no_scheme_valid(self) -> None:
    validate_uri("path/to/resource")


class TestRfc3986Compliance:
  """Tests specifically targeting RFC 3986 compliance."""

  def test_unreserved_chars_in_path(self) -> None:
    validate_uri("http://example.com/a-zA-Z0-9-._~")

  def test_sub_delims_in_query(self) -> None:
    validate_uri("http://example.com/path?!$&'()*+,;=")

  def test_colon_in_query(self) -> None:
    validate_uri("http://example.com/path?key:value")

  def test_at_in_query(self) -> None:
    validate_uri("http://example.com/path?user@host")

  def test_slash_in_query(self) -> None:
    validate_uri("http://example.com/path?a/b/c")

  def test_question_in_query(self) -> None:
    validate_uri("http://example.com/path?a?b?c")

  def test_port_empty_valid(self) -> None:
    validate_uri("http://example.com:")

  def test_port_numeric_valid(self) -> None:
    validate_uri("http://example.com:80")

  def test_port_large_numeric_valid(self) -> None:
    validate_uri("http://example.com:65535")


class TestUriValidationErrorMessages:
  """Tests for error message clarity in URI validation."""

  def test_non_ascii_error_position(self) -> None:
    with pytest.raises(ValueError, match="position 0"):
      validate_uri("\u00e9xample.com")

  def test_space_error_suggests_encoding(self) -> None:
    with pytest.raises(ValueError, match="'%20'"):
      validate_uri("http://example.com/path with space")

  def test_percent_encoding_error_hex_digits(self) -> None:
    with pytest.raises(ValueError, match="hexadecimal digits"):
      validate_uri("http://example.com/%GG")

  def test_authority_error_identifies_component(self) -> None:
    with pytest.raises(ValueError):
      validate_uri("http://user<>@example.com/")


class TestModuleConstants:
  """Tests for module-level constants."""

  def test_alpha_pattern(self) -> None:
    import re

    assert re.fullmatch(utils.ALPHA, "a")
    assert re.fullmatch(utils.ALPHA, "Z")
    assert not re.fullmatch(utils.ALPHA, "1")

  def test_digit_pattern(self) -> None:
    import re

    assert re.fullmatch(utils.DIGIT, "0")
    assert re.fullmatch(utils.DIGIT, "9")
    assert not re.fullmatch(utils.DIGIT, "a")

  def test_hexdigit_pattern(self) -> None:
    import re

    assert re.fullmatch(utils.HEXDIGITS, "a")
    assert re.fullmatch(utils.HEXDIGITS, "F")
    assert re.fullmatch(utils.HEXDIGITS, "9")
    assert not re.fullmatch(utils.HEXDIGITS, "g")

  def test_unreserved_pattern(self) -> None:
    import re

    pattern = re.compile(utils.UNRESERVED)
    assert pattern.fullmatch("a")
    assert pattern.fullmatch("Z")
    assert pattern.fullmatch("0")
    assert pattern.fullmatch("-")
    assert pattern.fullmatch(".")
    assert pattern.fullmatch("_")
    assert pattern.fullmatch("~")

  def test_sub_delims_pattern(self) -> None:
    import re

    pattern = re.compile(utils.SUB_DELIMS)
    assert pattern.fullmatch("!")
    assert pattern.fullmatch("$")
    assert pattern.fullmatch("&")
    assert pattern.fullmatch("'")
    assert pattern.fullmatch("(")
    assert pattern.fullmatch(")")
    assert pattern.fullmatch("*")
    assert pattern.fullmatch("+")
    assert pattern.fullmatch(",")
    assert pattern.fullmatch(";")
    assert pattern.fullmatch("=")

  def test_forbidden_chars_set(self) -> None:
    assert "<" in utils._FORBIDDEN_CHARS
    assert ">" in utils._FORBIDDEN_CHARS
    assert '"' in utils._FORBIDDEN_CHARS
    assert "{" in utils._FORBIDDEN_CHARS
    assert "}" in utils._FORBIDDEN_CHARS
    assert "|" in utils._FORBIDDEN_CHARS
    assert "\\" in utils._FORBIDDEN_CHARS
    assert "`" in utils._FORBIDDEN_CHARS

  def test_hex_chars_set(self) -> None:
    assert "0" in utils._HEX_CHARS
    assert "9" in utils._HEX_CHARS
    assert "a" in utils._HEX_CHARS
    assert "F" in utils._HEX_CHARS
    assert "g" not in utils._HEX_CHARS
