"""Tests for hypomnema.xml.utils module.

Tests cover:
- normalize_encoding: encoding name normalization
- make_usable_path: path resolution and directory creation
- QNameLike: protocol compliance
- validate_ncname: NCName validation (XML Namespaces §4)
"""

import tempfile
from pathlib import Path

import pytest

from hypomnema.base.errors import InvalidNCNameError
from hypomnema.xml.utils import (
  QNameLike,
  _validate_nc_start_char,
  _validate_ncname_char,
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


class TestValidateUri:
  """Tests for RFC 3986 URI validation."""

  @pytest.mark.parametrize(
    "uri",
    [
      "a:b",
      "http://example.com",
      "http://example.com/",
      "http://example.com/path",
      "http://example.com/path?query",
      "http://example.com/path?query#fragment",
      "http://example.com:8080/path",
      "http://user:password@example.com/path",
      "http://user@example.com/",
      "http://@example.com/",
      "http://example.com:",
      "http://example.com:/path",
      "http://[2001:db8::1]/path",
      "http://[2001:db8::1]:8080/path",
      "http://[v1.test]/path",
      "https://example.com/p%20ath",
      "https://example.com/path?a=1&b=2",
      "https://example.com/path#sec-1",
      "urn:isbn:0451450523",
      "urn:example:a123,z456",
      "file:///etc/passwd",
      "file://localhost/etc/passwd",
      "git+ssh://github.com/user/repo",
      "mailto:user@example.com",
      "foo://info.example.com?fred",
      "foo://:",
      "foo://@/",
      "http://example.com/path//double",
      "http://999.0.0.1/",
      "http://127.0.0.1/",
      "http://exa%20mple/",
      "http://[::1]:",
      "http:path",
      "http://example.com?",
      "http://example.com/?a/b?c",
      "http://example.com#",
      "http://example.com/#a/b?c",
      "http://example.com/?",
      "http://example.com/#",
      "urn:",
      "foo:/bar",
      "foo:?q",
      "foo:#frag",
      "foo:?#frag",
      "foo:a//b",
      "foo://",
    ],
  )
  def test_valid_uris(self, uri: str) -> None:
    validate_uri(uri)

  @pytest.mark.parametrize(
    "uri",
    [
      "",
      "not a uri",
      "1http://example.com",
      "ht%tp://example.com",
      "ht tp://example.com",
      "http ://example.com",
      "http://exam ple.com",
      "http://exa%mple/",
      "http://exa%2mple/",
      "http://example.com/path with spaces",
      "http://example.com/%GG",
      "http://example.com/%2",
      "http://example.com/%",
      "http://[invalid-ipv6]/path",
      "http://[]/path",
      "http://user@name@example.com/",
      "http://example.com:abc/",
      "http://[::1]:abc/",
      "http://a:b:c/",
      "//example.com/path",
      "http://example.com//a",
      "http://[2001:db8::1]suffix/path",
      "http://[2001:db8::1]x",
      "http://[::1:80/",
      "http://example.com:12a",
      "http://example.com/%2G",
      "http://example.com/?q=te st",
      "http://example.com/#frag ment",
      "http://example.com/[",
      "http://example.com/]",
      "foo://exa[mple.com",
      "foo://example.com/%",
      "foo://example.com/%ZZ",
    ],
  )
  def test_invalid_uris_raise(self, uri: str) -> None:
    with pytest.raises(ValueError):
      validate_uri(uri)
