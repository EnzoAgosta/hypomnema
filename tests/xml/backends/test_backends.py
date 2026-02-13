"""Tests for backend abstract method implementations.

Tests all abstract methods through both StandardBackend and LxmlBackend
using the parametrized backend fixture.
"""

from logging import WARNING, getLogger
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hypomnema.base.errors import UnregisteredPrefixError
from hypomnema.xml.backends.base import NamespaceHandler, XmlBackend
from hypomnema.xml.backends.lxml import LxmlBackend
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.policy import Behavior, NamespacePolicy, RaiseIgnore


class TestGetTag:
  """Tests for get_tag method."""

  def test_local_notation_default(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_tag(elem)
    assert result == "tu"

  def test_local_notation_explicit(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_tag(elem, notation="local")
    assert result == "tu"

  def test_prefixed_notation_no_namespace(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_tag(elem, notation="prefixed")
    assert result == "tu"

  def test_prefixed_notation_with_namespace(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    elem = backend.create_element("{http://www.w3.org/2001/XMLSchema}element")
    result = backend.get_tag(elem, notation="prefixed")
    assert result == "xs:element"

  def test_qualified_notation_no_namespace(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_tag(elem, notation="qualified")
    assert result == "tu"

  def test_qualified_notation_with_namespace(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    elem = backend.create_element("{http://www.w3.org/2001/XMLSchema}element")
    result = backend.get_tag(elem, notation="qualified")
    assert result == "{http://www.w3.org/2001/XMLSchema}element"

  def test_invalid_notation_raises(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    with pytest.raises(ValueError, match="Invalid notation"):
      backend.get_tag(elem, notation="invalid")  # type: ignore[arg-type]


class TestCreateElement:
  """Tests for create_element method."""

  def test_simple_element(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    assert backend.get_tag(elem) == "tu"

  def test_element_with_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "1", "lang": "en"})
    assert backend.get_attribute(elem, "id") == "1"
    assert backend.get_attribute(elem, "lang") == "en"

  def test_element_with_namespace_prefixed(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    elem = backend.create_element("xs:element")
    tag = backend.get_tag(elem, notation="qualified")
    assert tag == "{http://www.w3.org/2001/XMLSchema}element"

  def test_element_with_clark_notation(self, backend: XmlBackend) -> None:
    backend.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    elem = backend.create_element("{http://www.w3.org/2001/XMLSchema}element")
    tag = backend.get_tag(elem, notation="qualified")
    assert tag == "{http://www.w3.org/2001/XMLSchema}element"

  def test_element_with_prefix_no_uri_raises(self, backend: XmlBackend) -> None:
    with pytest.raises((ValueError, UnregisteredPrefixError)):
      backend.create_element("xs:element")

  def test_element_with_unregistered_prefix_ignore_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    ns_handler = NamespaceHandler(
      policy=NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE, WARNING))
    )
    logger = getLogger("test_element_with_unregistered_prefix_ignore_policy")
    backend._namespace_handler = ns_handler
    backend.logger = logger
    with caplog.at_level(WARNING):
      elem = backend.create_element("xs:element")
      assert backend.get_tag(elem, "qualified") == "element"
      assert "Namespace prefix 'xs' is not registered" in caplog.text

  def test_element_with_unregistered_uri_ignore_policy(self, backend: XmlBackend) -> None:
    ns_handler = NamespaceHandler(
      policy=NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE))
    )
    logger = getLogger("test_element_with_unregistered_prefix_ignore_policy")
    backend._namespace_handler = ns_handler
    backend.logger = logger
    elem = backend.create_element("{http://www.example.com}element")
    assert backend.get_tag(elem, "qualified") == "{http://www.example.com}element"

  def test_element_with_no_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes=None)
    assert backend.get_attribute_map(elem) == {}

  def test_create_element_with_broken_qualify_name(self, backend: XmlBackend) -> None:
    mock_hanlder = MagicMock(spec=NamespaceHandler)
    mock_hanlder.nsmap = {"example": "http://www.example.com"}
    mock_hanlder.qualify_name.return_value = (None, None, None)
    backend._namespace_handler = mock_hanlder
    with pytest.raises(ValueError):
      backend.create_element("element", attributes={"id": "1"})


class TestAppendChild:
  """Tests for append_child method."""

  def test_append_single_child(self, backend: XmlBackend) -> None:
    parent = backend.create_element("tmx")
    child = backend.create_element("tu")
    backend.append_child(parent, child)
    children = list(backend.iter_children(parent))
    assert len(children) == 1
    assert backend.get_tag(children[0]) == "tu"

  def test_append_multiple_children(self, backend: XmlBackend) -> None:
    parent = backend.create_element("body")
    for i in range(3):
      child = backend.create_element("tu", attributes={"id": str(i)})
      backend.append_child(parent, child)
    children = list(backend.iter_children(parent))
    assert len(children) == 3


class TestGetAttribute:
  """Tests for get_attribute method."""

  def test_get_existing_attribute(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "123"})
    result = backend.get_attribute(elem, "id")
    assert result == "123"

  def test_get_nonexistent_attribute_returns_none(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_attribute(elem, "nonexistent")
    assert result is None

  def test_get_with_default_value(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_attribute(elem, "nonexistent", default="default")
    assert result == "default"

  def test_get_existing_ignores_default(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "123"})
    result = backend.get_attribute(elem, "id", default="default")
    assert result == "123"

  def test_get_attribute_with_none_default(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_attribute(elem, "nonexistent", default=None)
    assert result is None


class TestSetAttribute:
  """Tests for set_attribute method."""

  def test_set_new_attribute(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    backend.set_attribute(elem, "id", "123")
    assert backend.get_attribute(elem, "id") == "123"

  def test_overwrite_existing_attribute(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "old"})
    backend.set_attribute(elem, "id", "new")
    assert backend.get_attribute(elem, "id") == "new"

  def test_set_multiple_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    backend.set_attribute(elem, "id", "1")
    backend.set_attribute(elem, "lang", "en")
    assert backend.get_attribute(elem, "id") == "1"
    assert backend.get_attribute(elem, "lang") == "en"


class TestDeleteAttribute:
  """Tests for delete_attribute method."""

  def test_delete_existing_attribute(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "123"})
    backend.delete_attribute(elem, "id")
    assert backend.get_attribute(elem, "id") is None

  def test_delete_nonexistent_attribute_no_error(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    backend.delete_attribute(elem, "nonexistent")

  def test_delete_one_of_multiple_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "1", "lang": "en"})
    backend.delete_attribute(elem, "id")
    assert backend.get_attribute(elem, "id") is None
    assert backend.get_attribute(elem, "lang") == "en"


class TestGetAttributeMap:
  """Tests for get_attribute_map method."""

  def test_element_with_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "1", "lang": "en"})
    result = backend.get_attribute_map(elem)
    assert result == {"id": "1", "lang": "en"}

  def test_element_without_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.get_attribute_map(elem)
    assert result == {}

  def test_attribute_map_is_copy(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "1"})
    result = backend.get_attribute_map(elem)
    result["new"] = "value"
    assert backend.get_attribute(elem, "new") is None


class TestGetSetText:
  """Tests for get_text and set_text methods."""

  def test_get_text_from_element_with_text(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    backend.set_text(elem, "Hello")
    assert backend.get_text(elem) == "Hello"

  def test_get_text_from_element_without_text(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    assert backend.get_text(elem) is None

  def test_set_text_overwrites(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    backend.set_text(elem, "First")
    backend.set_text(elem, "Second")
    assert backend.get_text(elem) == "Second"

  def test_set_text_to_none(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    backend.set_text(elem, "Hello")
    backend.set_text(elem, None)
    assert backend.get_text(elem) is None

  def test_set_empty_string(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    backend.set_text(elem, "")
    assert backend.get_text(elem) == ""


class TestGetSetTail:
  """Tests for get_tail and set_tail methods."""

  def test_get_tail_from_element_with_tail(self, backend: XmlBackend) -> None:
    parent = backend.create_element("parent")
    child = backend.create_element("child")
    backend.append_child(parent, child)
    backend.set_text(parent, "before")
    backend.set_tail(child, "after")
    assert backend.get_tail(child) == "after"

  def test_get_tail_from_element_without_tail(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    assert backend.get_tail(elem) is None

  def test_set_tail_overwrites(self, backend: XmlBackend) -> None:
    parent = backend.create_element("parent")
    child = backend.create_element("child")
    backend.append_child(parent, child)
    backend.set_tail(child, "first")
    backend.set_tail(child, "second")
    assert backend.get_tail(child) == "second"

  def test_set_tail_to_none(self, backend: XmlBackend) -> None:
    parent = backend.create_element("parent")
    child = backend.create_element("child")
    backend.append_child(parent, child)
    backend.set_tail(child, "after")
    backend.set_tail(child, None)
    assert backend.get_tail(child) is None


class TestIterChildren:
  """Tests for iter_children method."""

  def test_iterate_all_children(self, backend: XmlBackend) -> None:
    parent = backend.create_element("body")
    for i in range(3):
      child = backend.create_element("tu", attributes={"id": str(i)})
      backend.append_child(parent, child)
    children = list(backend.iter_children(parent))
    assert len(children) == 3

  def test_filter_by_single_tag(self, backend: XmlBackend) -> None:
    parent = backend.create_element("body")
    backend.append_child(parent, backend.create_element("tu"))
    backend.append_child(parent, backend.create_element("tuv"))
    backend.append_child(parent, backend.create_element("tu"))
    children = list(backend.iter_children(parent, tag_filter="tu"))
    assert len(children) == 2

  def test_filter_by_multiple_tags(self, backend: XmlBackend) -> None:
    parent = backend.create_element("body")
    backend.append_child(parent, backend.create_element("tu"))
    backend.append_child(parent, backend.create_element("tuv"))
    backend.append_child(parent, backend.create_element("seg"))
    children = list(backend.iter_children(parent, tag_filter=["tu", "tuv"]))
    assert len(children) == 2

  def test_element_with_no_children(self, backend: XmlBackend) -> None:
    parent = backend.create_element("body")
    children = list(backend.iter_children(parent))
    assert len(children) == 0

  def test_filter_no_matches(self, backend: XmlBackend) -> None:
    parent = backend.create_element("body")
    backend.append_child(parent, backend.create_element("tu"))
    children = list(backend.iter_children(parent, tag_filter="seg"))
    assert len(children) == 0


class TestParse:
  """Tests for parse method."""

  def test_parse_valid_xml(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b'<tmx version="1.4"><body></body></tmx>'
    xml_file = tmp_path / "test.tmx"
    xml_file.write_bytes(xml_content)
    root = backend.parse(xml_file)
    assert backend.get_tag(root) == "tmx"

  def test_parse_with_custom_encoding(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = '<?xml version="1.0" encoding="utf-8"?><root/>'.encode("utf-8")
    xml_file = tmp_path / "test.xml"
    xml_file.write_bytes(xml_content)
    root = backend.parse(xml_file, encoding="utf-8")
    assert backend.get_tag(root) == "root"

  def test_parse_nonexistent_file_raises(self, backend: XmlBackend, tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent.tmx"
    with pytest.raises((FileNotFoundError, OSError)):
      backend.parse(nonexistent)

  def test_parse_preserves_attributes(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b'<root attr1="value1" attr2="value2"/>'
    xml_file = tmp_path / "test.xml"
    xml_file.write_bytes(xml_content)
    root = backend.parse(xml_file)
    assert backend.get_attribute(root, "attr1") == "value1"
    assert backend.get_attribute(root, "attr2") == "value2"

  def test_parse_preserves_children(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b"<root><child1/><child2/></root>"
    xml_file = tmp_path / "test.xml"
    xml_file.write_bytes(xml_content)
    root = backend.parse(xml_file)
    children = list(backend.iter_children(root))
    assert len(children) == 2


class TestWrite:
  """Tests for write method."""

  def test_write_element_to_file(self, backend: XmlBackend, tmp_path: Path) -> None:
    elem = backend.create_element("tmx", attributes={"version": "1.4"})
    output = tmp_path / "output.tmx"
    backend.write(elem, output)
    assert output.exists()

  def test_write_with_custom_encoding(self, backend: XmlBackend, tmp_path: Path) -> None:
    elem = backend.create_element("root")
    output = tmp_path / "output.xml"
    backend.write(elem, output, encoding="utf-8")
    content = output.read_text()
    assert "<?xml" in content

  def test_write_creates_parent_directories(self, backend: XmlBackend, tmp_path: Path) -> None:
    elem = backend.create_element("root")
    output = tmp_path / "subdir" / "output.xml"
    backend.write(elem, output)
    assert output.exists()

  def test_write_includes_xml_declaration(self, backend: XmlBackend, tmp_path: Path) -> None:
    elem = backend.create_element("root")
    output = tmp_path / "output.xml"
    backend.write(elem, output)
    content = output.read_text()
    assert content.startswith("<?xml")

  def test_write_includes_doctype(self, backend: XmlBackend, tmp_path: Path) -> None:
    elem = backend.create_element("tmx")
    output = tmp_path / "output.tmx"
    backend.write(elem, output)
    content = output.read_text()
    assert "<!DOCTYPE" in content


class TestClear:
  """Tests for clear method."""

  def test_clear_removes_children(self, backend: XmlBackend) -> None:
    parent = backend.create_element("parent")
    backend.append_child(parent, backend.create_element("child"))
    backend.clear(parent)
    children = list(backend.iter_children(parent))
    assert len(children) == 0

  def test_clear_removes_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("elem", attributes={"id": "1"})
    backend.clear(elem)
    assert backend.get_attribute(elem, "id") is None

  def test_clear_removes_text(self, backend: XmlBackend) -> None:
    elem = backend.create_element("elem")
    backend.set_text(elem, "text")
    backend.clear(elem)
    assert backend.get_text(elem) is None


class TestToBytes:
  """Tests for to_bytes method."""

  def test_serialize_simple_element(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.to_bytes(elem)
    assert b"<tu" in result

  def test_serialize_with_attributes(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"id": "123"})
    result = backend.to_bytes(elem)
    assert b'id="123"' in result or b"id='123'" in result

  def test_serialize_with_children(self, backend: XmlBackend) -> None:
    parent = backend.create_element("parent")
    backend.append_child(parent, backend.create_element("child"))
    result = backend.to_bytes(parent)
    assert b"<child" in result

  def test_serialize_with_custom_encoding(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.to_bytes(elem, encoding="utf-16")
    assert isinstance(result, bytes)

  def test_serialize_self_closing_true(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.to_bytes(elem, self_closing=True)
    assert b"/>" in result or b"<tu/>" in result

  def test_serialize_self_closing_false(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    result = backend.to_bytes(elem, self_closing=False)
    assert b"</tu>" in result

  def test_serialize_with_text(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    backend.set_text(elem, "Hello World")
    result = backend.to_bytes(elem)
    assert b"Hello World" in result


class TestIterparse:
  """Tests for iterparse method."""

  def test_iterparse_yields_elements(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b'<root><tu id="1"/><tu id="2"/><tu id="3"/></root>'
    xml_file = tmp_path / "test.tmx"
    xml_file.write_bytes(xml_content)
    elements = list(backend.iterparse(xml_file, tag_filter="tu"))
    assert len(elements) == 3

  def test_iterparse_filter_by_tag(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b"<root><tu/><tuv/><tu/></root>"
    xml_file = tmp_path / "test.tmx"
    xml_file.write_bytes(xml_content)
    elements = list(backend.iterparse(xml_file, tag_filter="tu"))
    assert len(elements) == 2

  def test_iterparse_no_filter_yields_all(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b"<root><tu/><tuv/></root>"
    xml_file = tmp_path / "test.tmx"
    xml_file.write_bytes(xml_content)
    elements = list(backend.iterparse(xml_file))
    assert len(elements) >= 2

  def test_iterparse_nonexistent_file_raises(self, backend: XmlBackend, tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent.tmx"
    with pytest.raises((FileNotFoundError, OSError)):
      list(backend.iterparse(nonexistent))

  def test_iterparse_element_attributes_accessible(
    self, backend: XmlBackend, tmp_path: Path
  ) -> None:
    xml_content = b'<root><tu id="1"/><tu id="2"/></root>'
    xml_file = tmp_path / "test.tmx"
    xml_file.write_bytes(xml_content)
    ids = []
    for elem in backend.iterparse(xml_file, tag_filter="tu"):
      ids.append(backend.get_attribute(elem, "id"))
    assert ids == ["1", "2"]

  def test_iterparse_filter_by_multiple_tags(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b"<root><tu/><tuv/><seg/><tu/></root>"
    xml_file = tmp_path / "test.tmx"
    xml_file.write_bytes(xml_content)
    elements = list(backend.iterparse(xml_file, tag_filter=["tu", "tuv"]))
    assert len(elements) == 3


class TestMixedContent:
  """Tests for handling mixed content (text + elements)."""

  def test_element_with_text_and_children(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b"<root>text<child/>more text</root>"
    xml_file = tmp_path / "test.xml"
    xml_file.write_bytes(xml_content)
    root = backend.parse(xml_file)
    assert backend.get_text(root) == "text"
    children = list(backend.iter_children(root))
    assert len(children) == 1
    assert backend.get_tail(children[0]) == "more text"

  def test_nested_elements_with_tail(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = b"<root><a>text<b/>tail</a></root>"
    xml_file = tmp_path / "test.xml"
    xml_file.write_bytes(xml_content)
    root = backend.parse(xml_file)
    child_a = list(backend.iter_children(root))[0]
    child_b = list(backend.iter_children(child_a))[0]
    assert backend.get_tail(child_b) == "tail"


class TestRoundTrip:
  """Tests for parse/write round-trip equivalence."""

  def test_roundtrip_preserves_structure(self, backend: XmlBackend, tmp_path: Path) -> None:
    xml_content = (
      b'<tmx version="1.4"><body><tu id="1"><tuv lang="en"><seg>Hello</seg></tuv></tu></body></tmx>'
    )
    input_file = tmp_path / "input.tmx"
    output_file = tmp_path / "output.tmx"
    input_file.write_bytes(xml_content)
    root = backend.parse(input_file)
    backend.write(root, output_file)
    root2 = backend.parse(output_file)
    assert backend.get_tag(root2) == "tmx"
    assert backend.get_attribute(root2, "version") == "1.4"


class TestBackendEquivalence:
  """Tests ensuring both backends produce equivalent results."""

  def test_create_element_equivalence(self) -> None:
    std = StandardBackend()
    lxml = LxmlBackend()
    std_elem = std.create_element("tu", attributes={"id": "1"})
    lxml_elem = lxml.create_element("tu", attributes={"id": "1"})
    assert std.get_tag(std_elem) == lxml.get_tag(lxml_elem)
    assert std.get_attribute(std_elem, "id") == lxml.get_attribute(lxml_elem, "id")

  def test_serialization_equivalence(self) -> None:
    std = StandardBackend()
    lxml = LxmlBackend()
    std_elem = std.create_element("tu", attributes={"id": "1"})
    lxml_elem = lxml.create_element("tu", attributes={"id": "1"})
    std_bytes = std.to_bytes(std_elem)
    lxml_bytes = lxml.to_bytes(lxml_elem)
    assert b"<tu" in std_bytes and b"<tu" in lxml_bytes


class TestEdgeCases:
  """Edge case tests for backends."""

  def test_empty_element_name_raises(self, backend: XmlBackend) -> None:
    with pytest.raises(ValueError):
      backend.create_element("")

  def test_very_long_element_name(self, backend: XmlBackend) -> None:
    long_name = "a" * 1000
    elem = backend.create_element(long_name)
    assert backend.get_tag(elem) == long_name

  def test_element_with_special_attribute_chars(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu")
    backend.set_attribute(elem, "attr", "value with spaces & <special> chars")
    result = backend.to_bytes(elem)
    assert b"value with spaces" in result

  def test_unicode_in_text_content(self, backend: XmlBackend) -> None:
    elem = backend.create_element("seg")
    backend.set_text(elem, "\u4e2d\u6587\u65e5\u672c\u8a9e")
    result = backend.to_bytes(elem)
    assert "\u4e2d\u6587\u65e5\u672c\u8a9e".encode("utf-8") in result

  def test_unicode_in_attribute_value(self, backend: XmlBackend) -> None:
    elem = backend.create_element("tu", attributes={"note": "\u4e2d\u6587"})
    result = backend.to_bytes(elem)
    assert "\u4e2d\u6587".encode("utf-8") in result

  def test_deeply_nested_elements(self, backend: XmlBackend) -> None:
    root = backend.create_element("root")
    current = root
    for i in range(10):
      child = backend.create_element(f"level{i}")
      backend.append_child(current, child)
      current = child
    result = backend.to_bytes(root)
    assert b"<level9" in result

  def test_many_attributes(self, backend: XmlBackend) -> None:
    attrs = {f"attr{i}": f"value{i}" for i in range(50)}
    elem = backend.create_element("elem", attributes=attrs)
    for i in range(50):
      assert backend.get_attribute(elem, f"attr{i}") == f"value{i}"

  def test_many_children(self, backend: XmlBackend) -> None:
    parent = backend.create_element("parent")
    for i in range(100):
      backend.append_child(parent, backend.create_element("child"))
    children = list(backend.iter_children(parent))
    assert len(children) == 100
