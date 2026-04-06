from pathlib import Path

from hypomnema.backends.xml.base import XmlBackend


def _write_xml(tmp_path: Path, filename: str, xml: str) -> Path:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return path


def test_backend_create_element_returns_local_tag(backend: XmlBackend[object]) -> None:
  backend.register_namespace("ns", "https://example.com/ns")

  element = backend.create_element("ns:item")

  assert backend.get_tag(element) == "item"


def test_backend_get_tag_returns_prefixed_name(backend: XmlBackend[object]) -> None:
  backend.register_namespace("ns", "https://example.com/ns")

  element = backend.create_element("ns:item")

  assert backend.get_tag(element, notation="prefixed") == "ns:item"


def test_backend_get_tag_returns_qualified_name(backend: XmlBackend[object]) -> None:
  backend.register_namespace("ns", "https://example.com/ns")

  element = backend.create_element("ns:item")

  assert backend.get_tag(element, notation="qualified") == "{https://example.com/ns}item"


def test_backend_get_attribute_returns_existing_value(backend: XmlBackend[object]) -> None:
  element = backend.create_element("item", attributes={"alpha": "1"})

  assert backend.get_attribute(element, "alpha") == "1"


def test_backend_get_attribute_returns_none_for_missing_value(backend: XmlBackend[object]) -> None:
  element = backend.create_element("item")

  assert backend.get_attribute(element, "missing") is None


def test_backend_get_attribute_returns_default_for_missing_value(
  backend: XmlBackend[object],
) -> None:
  element = backend.create_element("item")

  assert backend.get_attribute(element, "missing", default="fallback") == "fallback"


def test_backend_set_attribute_stores_value(backend: XmlBackend[object]) -> None:
  element = backend.create_element("item")

  backend.set_attribute(element, "beta", "2")

  assert backend.get_attribute(element, "beta") == "2"


def test_backend_get_attribute_map_returns_local_names(backend: XmlBackend[object]) -> None:
  element = backend.create_element("item")
  backend.set_attribute(element, "alpha", "1")
  backend.set_attribute(element, "xml:lang", "en")

  assert backend.get_attribute_map(element) == {"alpha": "1", "lang": "en"}


def test_backend_delete_attribute_removes_value(backend: XmlBackend[object]) -> None:
  element = backend.create_element("item", attributes={"alpha": "1", "beta": "2"})

  backend.delete_attribute(element, "alpha")

  assert backend.get_attribute(element, "alpha") is None


def test_backend_deregister_prefix_removes_registered_namespace(
  backend: XmlBackend[object],
) -> None:
  backend.register_namespace("ns", "https://example.com/ns")

  backend.deregister_prefix("ns")

  assert backend.nsmap == {}


def test_backend_set_text_stores_value(backend: XmlBackend[object]) -> None:
  element = backend.create_element("root")

  backend.set_text(element, "lead")

  assert backend.get_text(element) == "lead"


def test_backend_set_tail_stores_value(backend: XmlBackend[object]) -> None:
  element = backend.create_element("child")

  backend.set_tail(element, "between")

  assert backend.get_tail(element) == "between"


def test_backend_append_child_adds_child(backend: XmlBackend[object]) -> None:
  parent = backend.create_element("root")
  child = backend.create_element("child")

  backend.append_child(parent, child)

  assert [backend.get_tag(item) for item in backend.iter_children(parent)] == ["child"]


def test_backend_iter_children_yields_children_in_order(backend: XmlBackend[object]) -> None:
  root = backend.create_element("root")
  backend.append_child(root, backend.create_element("first"))
  backend.append_child(root, backend.create_element("second"))

  assert [backend.get_tag(child) for child in backend.iter_children(root)] == ["first", "second"]


def test_backend_iter_children_filters_single_tag(backend: XmlBackend[object]) -> None:
  root = backend.create_element("root")
  backend.append_child(root, backend.create_element("first"))
  backend.append_child(root, backend.create_element("second"))

  assert [backend.get_tag(child) for child in backend.iter_children(root, tag_filter="second")] == [
    "second"
  ]


def test_backend_iter_children_filters_multiple_tags(backend: XmlBackend[object]) -> None:
  root = backend.create_element("root")
  backend.append_child(root, backend.create_element("first"))
  backend.append_child(root, backend.create_element("second"))

  assert [
    backend.get_tag(child) for child in backend.iter_children(root, tag_filter=["first", "second"])
  ] == ["first", "second"]


def test_backend_to_bytes_includes_tail_by_default(backend: XmlBackend[object]) -> None:
  child = backend.create_element("child")
  backend.set_text(child, "value")
  backend.set_tail(child, "tail")

  assert backend.to_bytes(child).endswith(b"tail")


def test_backend_to_bytes_can_strip_tail(backend: XmlBackend[object]) -> None:
  child = backend.create_element("child")
  backend.set_text(child, "value")
  backend.set_tail(child, "tail")

  assert backend.to_bytes(child, strip_tail=True) == b"<child>value</child>"


def test_backend_parse_reads_root_tag(backend: XmlBackend[object], tmp_path: Path) -> None:
  path = _write_xml(tmp_path, "payload.xml", '<root alpha="1"><child>value</child></root>')

  assert backend.get_tag(backend.parse(path)) == "root"


def test_backend_parse_reads_root_attribute(backend: XmlBackend[object], tmp_path: Path) -> None:
  path = _write_xml(tmp_path, "payload.xml", '<root alpha="1"><child>value</child></root>')

  assert backend.get_attribute(backend.parse(path), "alpha") == "1"


def test_backend_parse_reads_child_text(backend: XmlBackend[object], tmp_path: Path) -> None:
  path = _write_xml(tmp_path, "payload.xml", "<root><child>value</child></root>")
  parsed = backend.parse(path)
  child = next(backend.iter_children(parsed))

  assert backend.get_text(child) == "value"


def test_backend_parse_reads_child_tail(backend: XmlBackend[object], tmp_path: Path) -> None:
  path = _write_xml(tmp_path, "payload.xml", "<root><child>value</child>tail</root>")
  parsed = backend.parse(path)
  child = next(backend.iter_children(parsed))

  assert backend.get_tail(child) == "tail"


def test_backend_write_writes_parseable_root(backend: XmlBackend[object], tmp_path: Path) -> None:
  root = backend.create_element("root")

  backend.write(root, tmp_path / "written.xml")

  assert backend.get_tag(backend.parse(tmp_path / "written.xml")) == "root"


def test_backend_write_preserves_child_text(backend: XmlBackend[object], tmp_path: Path) -> None:
  root = backend.create_element("root")
  child = backend.create_element("child")
  backend.set_text(child, "value")
  backend.append_child(root, child)
  path = tmp_path / "written.xml"

  backend.write(root, path)

  reparsed = backend.parse(path)
  reparsed_child = next(backend.iter_children(reparsed))
  assert backend.get_text(reparsed_child) == "value"


def test_backend_iterparse_yields_matching_elements(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
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
    (backend.get_tag(element), backend.get_attribute(element, "tuid"))
    for element in backend.iterparse(path, tag_filter="tu")
  ]

  assert yielded == [("tu", "one"), ("tu", "two")]


def test_backend_iterwrite_writes_xml_declaration(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  path = tmp_path / "iterwrite.xml"

  backend.iterwrite(
    path,
    [backend.create_element("tu")],
    root_elem=backend.create_element("body"),
    write_xml_declaration=True,
  )

  assert path.read_text(encoding="utf-8").startswith('<?xml version="1.0" encoding="utf-8"?>')


def test_backend_iterwrite_writes_doctype(backend: XmlBackend[object], tmp_path: Path) -> None:
  path = tmp_path / "iterwrite.xml"

  backend.iterwrite(
    path,
    [backend.create_element("tu")],
    root_elem=backend.create_element("body"),
    write_doctype=True,
  )

  assert '<!DOCTYPE tmx SYSTEM "tmx14.dtd">' in path.read_text(encoding="utf-8")


def test_backend_iterwrite_writes_requested_root(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  path = tmp_path / "iterwrite.xml"

  backend.iterwrite(path, [backend.create_element("tu")], root_elem=backend.create_element("body"))

  assert backend.get_tag(backend.parse(path)) == "body"


def test_backend_iterwrite_preserves_child_order(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  first = backend.create_element("tu", attributes={"tuid": "one"})
  second = backend.create_element("tu", attributes={"tuid": "two"})
  path = tmp_path / "iterwrite.xml"

  backend.iterwrite(
    path,
    [first, second],
    root_elem=backend.create_element("body"),
    max_number_of_elements_in_buffer=1,
  )

  reparsed = backend.parse(path)
  assert [backend.get_attribute(child, "tuid") for child in backend.iter_children(reparsed)] == [
    "one",
    "two",
  ]
