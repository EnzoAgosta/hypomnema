"""Tests for XmlBackend abstract base class methods.

Tests the non-abstract methods of XmlBackend through concrete implementations.
Uses the parametrized backend fixture to test both StandardBackend and LxmlBackend.
"""

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.backends.lxml import LxmlBackend
from hypomnema.xml.backends.standard import StandardBackend


class TestPrepTagSet:
  """Tests for prep_tag_set method."""

  def test_single_string_tag(self, backend: XmlBackend) -> None:
    result = backend.prep_tag_set("tu")
    assert result == {"tu"}

  def test_list_of_strings(self, backend: XmlBackend) -> None:
    result = backend.prep_tag_set(["tu", "tuv"])
    assert result == {"tu", "tuv"}

  def test_nested_iterable(self, backend: XmlBackend) -> None:
    # technically supported, but not recommended and mypy actively rejects it
    result = backend.prep_tag_set([["tu", "tuv"], "seg"])  # type: ignore[list-item]
    assert result == {"tu", "tuv", "seg"}

  def test_bytes_input(self, backend: XmlBackend) -> None:
    result = backend.prep_tag_set(b"tu")
    assert result == {"tu"}

  def test_bytearray_input(self, backend: XmlBackend) -> None:
    result = backend.prep_tag_set(bytearray(b"tu"))
    assert result == {"tu"}

  def test_qname_like_input(self, backend: XmlBackend) -> None:
    class MockQName:
      @property
      def text(self) -> str:
        return "tu"

    result = backend.prep_tag_set(MockQName())
    assert result == {"tu"}

  def test_empty_input(self, backend: XmlBackend) -> None:
    result = backend.prep_tag_set([])
    assert result == set()

  def test_mixed_types(self, backend: XmlBackend) -> None:
    class MockQName:
      @property
      def text(self) -> str:
        return "seg"

    result = backend.prep_tag_set(["tu", b"tuv", MockQName()])
    assert result == {"tu", "tuv", "seg"}


class TestNormalizeTagName:
  """Tests for normalize_tag_name method."""

  def test_string_input(self, backend: XmlBackend) -> None:
    result = backend.normalize_tag_name("tu")
    assert result == "tu"

  def test_bytes_input(self, backend: XmlBackend) -> None:
    result = backend.normalize_tag_name(b"tu")
    assert result == "tu"

  def test_bytearray_input(self, backend: XmlBackend) -> None:
    result = backend.normalize_tag_name(bytearray(b"tu"))
    assert result == "tu"

  def test_qname_like_input(self, backend: XmlBackend) -> None:
    class MockQName:
      @property
      def text(self) -> str:
        return "tu"

    result = backend.normalize_tag_name(MockQName())
    assert result == "tu"

  def test_invalid_type_raises(self, backend: XmlBackend) -> None:
    with pytest.raises(TypeError, match="Unexpected tag type"):
      backend.normalize_tag_name(123)  # type: ignore[arg-type]

  def test_bytes_with_utf8_encoding(self, backend: XmlBackend) -> None:
    result = backend.normalize_tag_name("\u4e2d\u6587".encode("utf-8"))
    assert result == "\u4e2d\u6587"


class TestNamespaceMethods:
  """Tests for namespace registration methods."""

  def test_register_namespace(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    assert "xs" in backend.nsmap
    assert backend.nsmap["xs"] == "http://www.w3.org/2001/XMLSchema"

  def test_deregister_prefix(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    backend.deregister_prefix("xs")
    assert "xs" not in backend.nsmap

  def test_nsmap_is_copy(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    nsmap = backend.nsmap
    nsmap["test"] = "http://example.com"
    assert "test" not in backend.nsmap


class TestIterwrite:
  """Tests for iterwrite method."""

  def _make_non_empty_root(
    self, backend: XmlBackend, tag: str = "tmx", attributes: dict | None = None
  ) -> Any:
    root = backend.create_element(tag, attributes=attributes)
    backend.set_text(root, "")
    return root

  def test_iterwrite_with_none_root_elem(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [
      backend.create_element("tu", attributes={"id": "1"}),
      backend.create_element("tu", attributes={"id": "2"}),
    ]
    output_path = tmp_path / "output.tmx"
    backend.iterwrite(output_path, elements)
    assert output_path.exists()
    content = output_path.read_text()
    assert '<tmx version="1.4">' in content
    assert "</tmx>" in content

  def test_iterwrite_fails_with_incorrect_to_bytes(
    self, backend: XmlBackend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
    elements = [
      backend.create_element("tu", attributes={"id": "1"}),
      backend.create_element("tu", attributes={"id": "2"}),
    ]
    root = self._make_non_empty_root(backend, "tmx", {"version": "1.4"})
    output_path = tmp_path / "output.tmx"
    monkeypatch.setattr(type(backend), "to_bytes", lambda *x, **kwargs: str(x).encode("utf-8"))
    with pytest.raises(
      ValueError, match="implementation returned an incorrectly formatted root element"
    ):
      backend.iterwrite(output_path, elements, root_elem=root)

  def test_basic_iterwrite(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [
      backend.create_element("tu", attributes={"id": "1"}),
      backend.create_element("tu", attributes={"id": "2"}),
    ]
    root = self._make_non_empty_root(backend, "tmx", {"version": "1.4"})
    output_path = tmp_path / "output.tmx"
    backend.iterwrite(output_path, elements, root_elem=root)
    assert output_path.exists()
    content = output_path.read_text()
    assert "<tmx" in content
    assert "</tmx>" in content

  def test_iterwrite_with_custom_root(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [backend.create_element("item")]
    custom_root = self._make_non_empty_root(backend, "custom", {"version": "1.0"})
    output_path = tmp_path / "output.xml"
    backend.iterwrite(output_path, elements, root_elem=custom_root)
    content = output_path.read_text()
    assert "<custom" in content
    assert "</custom>" in content

  def test_iterwrite_with_xml_declaration(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [backend.create_element("tu")]
    root = self._make_non_empty_root(backend)
    output_path = tmp_path / "output.tmx"
    backend.iterwrite(output_path, elements, root_elem=root, write_xml_declaration=True)
    content = output_path.read_text()
    assert content.startswith("<?xml")

  def test_iterwrite_with_doctype(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [backend.create_element("tu")]
    root = self._make_non_empty_root(backend)
    output_path = tmp_path / "output.tmx"
    backend.iterwrite(output_path, elements, root_elem=root, write_doctype=True)
    content = output_path.read_text()
    assert "<!DOCTYPE tmx" in content

  def test_iterwrite_invalid_buffer_size(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [backend.create_element("tu")]
    root = self._make_non_empty_root(backend)
    output_path = tmp_path / "output.tmx"
    with pytest.raises(ValueError, match="buffer_size must be >= 1"):
      backend.iterwrite(output_path, elements, root_elem=root, max_number_of_elements_in_buffer=0)

  def test_iterwrite_to_bytesio(self, backend: XmlBackend) -> None:
    elements = [backend.create_element("tu")]
    root = self._make_non_empty_root(backend)
    buffer = BytesIO()
    backend.iterwrite(buffer, elements, root_elem=root)
    content = buffer.getvalue().decode("utf-8")
    assert "<tmx" in content
    assert "</tmx>" in content

  def test_iterwrite_buffer_flushing(self, backend: XmlBackend, tmp_path: Path) -> None:
    elements = [backend.create_element("tu", attributes={"id": str(i)}) for i in range(5)]
    root = self._make_non_empty_root(backend)
    output_path = tmp_path / "output.tmx"
    backend.iterwrite(output_path, elements, root_elem=root, max_number_of_elements_in_buffer=2)
    content = output_path.read_text()
    for i in range(5):
      assert f'id="{i}"' in content or f"id='{i}'" in content


class TestIterwriteErrors:
  """Tests for iterwrite error conditions."""

  def test_iterwrite_malformed_root_element(self, backend: XmlBackend, tmp_path: Path) -> None:
    class BadElement:
      pass

    bad_root = BadElement()
    output_path = tmp_path / "output.tmx"
    with pytest.raises(
      (TypeError, AttributeError)
    ):  # lxml raises AttributeError since .text is missing and StandardBackend raises TypeError
      backend.iterwrite(output_path, [], root_elem=bad_root)


class TestBackendInitialization:
  """Tests for backend initialization."""

  @pytest.mark.parametrize("backend_class", [StandardBackend, LxmlBackend])
  def test_default_initialization(self, backend_class: type[XmlBackend]) -> None:
    backend = backend_class()
    assert backend.logger is not None
    assert backend.default_encoding == "utf-8"

  @pytest.mark.parametrize("backend_class", [StandardBackend, LxmlBackend])
  def test_custom_encoding(self, backend_class: type[XmlBackend]) -> None:
    backend = backend_class(default_encoding="iso-8859-1")
    assert backend.default_encoding == "iso8859-1"

  @pytest.mark.parametrize("backend_class", [StandardBackend, LxmlBackend])
  def test_none_encoding_returns_utf8(self, backend_class: type[XmlBackend]) -> None:
    backend = backend_class(default_encoding=None)
    assert backend.default_encoding == "utf-8"

  @pytest.mark.parametrize("backend_class", [StandardBackend, LxmlBackend])
  def test_unicode_encoding_returns_utf8(self, backend_class: type[XmlBackend]) -> None:
    backend = backend_class(default_encoding="unicode")
    assert backend.default_encoding == "utf-8"
