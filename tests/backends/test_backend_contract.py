"""Parametrized contract tests for StandardBackend and LxmlBackend."""

from pathlib import Path

import pytest

from hypomnema.backends.xml.errors import (
  ExistingNamespaceError,
  RestrictedPrefixError,
  RestrictedURIError,
  UnregisteredPrefixError,
  UnregisteredURIError,
)


def _write_xml(tmp_path: Path, filename: str, xml: str) -> Path:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return path


# ── Namespace management ─────────────────────────────────────────


class TestNamespaceManagement:
  def test_register_namespace(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("ns", "http://example.com/ns")
    assert b.global_nsmap == {"ns": "http://example.com/ns"}

  def test_register_namespace_rejects_reserved_prefix(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    with pytest.raises(RestrictedPrefixError):
      b.register_namespace("xml", "http://example.com")

  def test_register_namespace_rejects_reserved_uri(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    with pytest.raises(RestrictedURIError):
      b.register_namespace("myns", "http://www.w3.org/XML/1998/namespace")

  def test_register_namespace_raises_on_duplicate(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("ns", "http://old.example.com")
    with pytest.raises(ExistingNamespaceError):
      b.register_namespace("ns", "http://new.example.com")

  def test_deregister_prefix(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("ns", "http://example.com/ns")
    b.deregister_prefix("ns")
    assert b.global_nsmap == {}

  def test_deregister_prefix_rejects_reserved(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    with pytest.raises(RestrictedPrefixError):
      b.deregister_prefix("xml")

  def test_deregister_prefix_raises_on_missing(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    with pytest.raises(UnregisteredPrefixError):
      b.deregister_prefix("missing")

  def test_deregister_uri(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("a", "http://example.com/ns")
    b.register_namespace("b", "http://example.com/ns")
    b.deregister_uri("http://example.com/ns")
    assert b.global_nsmap == {}

  def test_deregister_uri_rejects_reserved(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    with pytest.raises(RestrictedURIError):
      b.deregister_uri("http://www.w3.org/XML/1998/namespace")

  def test_deregister_uri_raises_on_missing(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    with pytest.raises(UnregisteredURIError):
      b.deregister_uri("http://missing.example.com")

  def test_global_nsmap_constructor(self) -> None:
    from hypomnema.backends.xml.lxml import LxmlBackend
    from hypomnema.backends.xml.standard import StandardBackend

    for cls in [StandardBackend, LxmlBackend]:
      b = cls(global_nsmap={"ns": "http://example.com/ns"})
      assert b.global_nsmap == {"ns": "http://example.com/ns"}


# ── Element creation and tag retrieval ────────────────────────────


class TestElementCreation:
  def test_create_element_returns_local_tag(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("ns", "https://example.com/ns")
    element = b.create_element("ns:item")
    assert b.get_tag(element) == "{https://example.com/ns}item"

  def test_create_element_prefixed_tag(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("ns", "https://example.com/ns")
    element = b.create_element("ns:item")
    assert b.get_tag(element, notation="prefixed") == "ns:item"

  def test_create_element_qualified_tag(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    b.register_namespace("ns", "https://example.com/ns")
    element = b.create_element("ns:item")
    assert b.get_tag(element, notation="qualified") == "{https://example.com/ns}item"

  def test_create_element_local_tag(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item")
    assert b.get_tag(element, notation="local") == "item"

  def test_create_element_unnamespaced_tag_returns_bare_name(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("header")
    assert b.get_tag(element) == "header"

  def test_create_element_with_attributes(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item", attributes={"alpha": "1"})
    assert b.get_attribute(element, "alpha") == "1"

  def test_create_element_with_bytes_tag(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element(b"item")
    assert b.get_tag(element, notation="local") == "item"


# ── Attribute operations ──────────────────────────────────────────


class TestAttributeOperations:
  def test_get_attribute_returns_existing_value(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item", attributes={"alpha": "1"})
    assert b.get_attribute(element, "alpha") == "1"

  def test_get_attribute_returns_none_for_missing(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item")
    assert b.get_attribute(element, "missing") is None

  def test_get_attribute_returns_default_for_missing(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item")
    assert b.get_attribute(element, "missing", default="fallback") == "fallback"

  def test_set_attribute_stores_value(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item")
    b.set_attribute(element, "beta", "2")
    assert b.get_attribute(element, "beta") == "2"

  def test_get_attribute_map_returns_qualified_by_default(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item")
    b.set_attribute(element, "alpha", "1")
    b.set_attribute(element, "xml:lang", "en")
    attr_map = b.get_attribute_map(element)
    assert "alpha" in attr_map
    assert attr_map["alpha"] == "1"

  def test_get_attribute_map_with_local_notation(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item")
    b.set_attribute(element, "alpha", "1")
    b.set_attribute(element, "xml:lang", "en")
    attr_map = b.get_attribute_map(element, notation="local")
    assert attr_map["lang"] == "en"

  def test_delete_attribute_removes_value(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("item", attributes={"alpha": "1", "beta": "2"})
    b.delete_attribute(element, "alpha")
    assert b.get_attribute(element, "alpha") is None


# ── Text and tail ────────────────────────────────────────────────


class TestTextAndTail:
  def test_set_text_stores_value(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("root")
    b.set_text(element, "lead")
    assert b.get_text(element) == "lead"

  def test_set_tail_stores_value(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    element = b.create_element("child")
    b.set_tail(element, "between")
    assert b.get_tail(element) == "between"


# ── Child iteration ──────────────────────────────────────────────


class TestIterChildren:
  def test_append_child_adds_child(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    parent = b.create_element("root")
    child = b.create_element("child")
    b.append_child(parent, child)
    assert [b.get_tag(item, notation="local") for item in b.iter_children(parent)] == ["child"]

  def test_iter_children_yields_in_order(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.create_element("root")
    b.append_child(root, b.create_element("first"))
    b.append_child(root, b.create_element("second"))
    assert [b.get_tag(child, notation="local") for child in b.iter_children(root)] == [
      "first",
      "second",
    ]

  def test_iter_children_filters_single_tag(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.create_element("root")
    b.append_child(root, b.create_element("first"))
    b.append_child(root, b.create_element("second"))
    assert [
      b.get_tag(child, notation="local") for child in b.iter_children(root, tag_filter="second")
    ] == ["second"]

  def test_iter_children_filters_multiple_tags(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.create_element("root")
    b.append_child(root, b.create_element("first"))
    b.append_child(root, b.create_element("second"))
    assert [
      b.get_tag(child, notation="local")
      for child in b.iter_children(root, tag_filter=["first", "second"])
    ] == ["first", "second"]


# ── Serialization ─────────────────────────────────────────────────


class TestSerialization:
  def test_to_bytes_includes_tail_by_default(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    child = b.create_element("child")
    b.set_text(child, "value")
    b.set_tail(child, "tail")
    assert b.to_bytes(child).endswith(b"tail")

  def test_to_bytes_can_strip_tail(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    child = b.create_element("child")
    b.set_text(child, "value")
    b.set_tail(child, "tail")
    assert b.to_bytes(child, strip_tail=True) == b"<child>value</child>"


# ── Parsing and writing ──────────────────────────────────────────


class TestParsingAndWriting:
  def test_parse_reads_root_tag(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = _write_xml(tmp_path, "payload.xml", '<root alpha="1"><child>value</child></root>')
    assert b.get_tag(b.parse(path), notation="local") == "root"

  def test_parse_reads_root_attribute(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = _write_xml(tmp_path, "payload.xml", '<root alpha="1"><child>value</child></root>')
    assert b.get_attribute(b.parse(path), "alpha") == "1"

  def test_parse_reads_child_text(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = _write_xml(tmp_path, "payload.xml", "<root><child>value</child></root>")
    parsed = b.parse(path)
    child = next(b.iter_children(parsed))
    assert b.get_text(child) == "value"

  def test_parse_reads_child_tail(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = _write_xml(tmp_path, "payload.xml", "<root><child>value</child>tail</root>")
    parsed = b.parse(path)
    child = next(b.iter_children(parsed))
    assert b.get_tail(child) == "tail"

  def test_write_writes_parseable_root(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.create_element("root")
    b.write(root, tmp_path / "written.xml")
    assert b.get_tag(b.parse(tmp_path / "written.xml"), notation="local") == "root"

  def test_write_preserves_child_text(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.create_element("root")
    child = b.create_element("child")
    b.set_text(child, "value")
    b.append_child(root, child)
    path = tmp_path / "written.xml"
    b.write(root, path)
    reparsed = b.parse(path)
    reparsed_child = next(b.iter_children(reparsed))
    assert b.get_text(reparsed_child) == "value"

  def test_from_string_accepts_string(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.from_string('<root attr="val"/>')
    assert b.get_tag(root, notation="local") == "root"
    assert b.get_attribute(root, "attr") == "val"

  def test_from_bytes_accepts_bytes(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    root = b.from_bytes(b'<root attr="val"/>')
    assert b.get_tag(root, notation="local") == "root"
    assert b.get_attribute(root, "attr") == "val"

  def test_from_bytes_populates_nsmap(self, backend: object) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    xml = '<root xmlns:ns="http://example.com/ns"><ns:item/></root>'
    b.from_string(xml, populate_nsmap=True)
    assert "ns" in b.global_nsmap
    assert b.global_nsmap["ns"] == "http://example.com/ns"


# ── Iterparse ─────────────────────────────────────────────────────


class TestIterparse:
  def test_iterparse_yields_matching_elements(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = _write_xml(
      tmp_path,
      "iterparse.xml",
      (
        '<tmx version="1.4">'
        '<header creationtool="hypomnema" creationtoolversion="1.0" segtype="sentence" '
        'o-tmf="tmx" adminlang="en" srclang="fr" datatype="plaintext" />'
        "<body>"
        '<tu tuid="one"><tuv lang="en"><seg>One</seg></tuv></tu>'
        '<tu tuid="two"><tuv lang="fr"><seg>Deux</seg></tuv></tu>'
        "</body>"
        "</tmx>"
      ),
    )
    yielded = [
      (b.get_tag(element, notation="local"), b.get_attribute(element, "tuid"))
      for element in b.iterparse(path, tag_filter="tu")
    ]
    assert yielded == [("tu", "one"), ("tu", "two")]

  def test_iterparse_populates_nsmap(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = _write_xml(
      tmp_path, "ns_iterparse.xml", '<root xmlns:ns="http://example.com/ns"><ns:item/></root>'
    )
    list(b.iterparse(path, populate_nsmap=True))
    assert "ns" in b.global_nsmap


# ── Iterwrite ──────────────────────────────────────────────────────


class TestIterwrite:
  def test_iterwrite_writes_xml_declaration(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = tmp_path / "iterwrite.xml"
    b.iterwrite(
      path, [b.create_element("tu")], root_elem=b.create_element("body"), write_xml_declaration=True
    )
    assert path.read_text(encoding="utf-8").startswith('<?xml version="1.0" encoding="utf-8"?>')

  def test_iterwrite_writes_doctype(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = tmp_path / "iterwrite.xml"
    b.iterwrite(
      path,
      [b.create_element("tu")],
      root_elem=b.create_element("body"),
      doctype='<!DOCTYPE tmx SYSTEM "tmx14.dtd">',
    )
    assert '<!DOCTYPE tmx SYSTEM "tmx14.dtd">' in path.read_text(encoding="utf-8")

  def test_iterwrite_writes_requested_root(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = tmp_path / "iterwrite.xml"
    b.iterwrite(path, [b.create_element("tu")], root_elem=b.create_element("body"))
    assert b.get_tag(b.parse(path), notation="local") == "body"

  def test_iterwrite_preserves_child_order(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    first = b.create_element("tu", attributes={"tuid": "one"})
    second = b.create_element("tu", attributes={"tuid": "two"})
    path = tmp_path / "iterwrite.xml"
    b.iterwrite(
      path, [first, second], root_elem=b.create_element("body"), max_number_of_elements_in_buffer=1
    )
    reparsed = b.parse(path)
    assert [b.get_attribute(child, "tuid") for child in b.iter_children(reparsed)] == ["one", "two"]

  def test_iterwrite_no_root(self, backend: object, tmp_path: Path) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = tmp_path / "iterwrite_noroot.xml"
    first = b.create_element("tu", attributes={"tuid": "one"})
    second = b.create_element("tu", attributes={"tuid": "two"})
    b.iterwrite(path, [first, second])
    content = path.read_text(encoding="utf-8")
    assert "tuid" in content

  def test_iterwrite_with_xml_declaration_and_no_root(
    self, backend: object, tmp_path: Path
  ) -> None:
    from hypomnema.backends.xml.base import XmlBackend

    b = backend
    assert isinstance(b, XmlBackend)
    path = tmp_path / "iterwrite_decl_noroot.xml"
    b.iterwrite(path, [b.create_element("tu")], write_xml_declaration=True)
    content = path.read_text(encoding="utf-8")
    assert content.startswith("<?xml")
