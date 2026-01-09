from hypomnema.xml.utils import QName


def test_create_element(backend):
  """Verify element creation with tag and attributes."""
  # Simple tag
  el = backend.create_element("foo", {"bar": "baz"})
  assert backend.get_tag(el) == "foo"
  assert backend.get_attribute(el, "bar") == "baz"

  # Check attribute map
  attrs = backend.get_attribute_map(el)
  assert attrs == {"bar": "baz"}


def test_text_tail_handling(backend):
  """Verify text and tail manipulation."""
  el = backend.create_element("foo")

  # Initial state
  assert backend.get_text(el) is None
  assert backend.get_tail(el) is None

  # Set text
  backend.set_text(el, "Hello")
  assert backend.get_text(el) == "Hello"

  # Set tail
  backend.set_tail(el, "World")
  assert backend.get_tail(el) == "World"

  # Clear text
  backend.set_text(el, None)
  assert backend.get_text(el) is None
  # Tail should remain
  assert backend.get_tail(el) == "World"


def test_child_manipulation(backend):
  """Verify appending and iterating children."""
  parent = backend.create_element("parent")
  child1 = backend.create_element("child1")
  child2 = backend.create_element("child2")

  backend.append_child(parent, child1)
  backend.append_child(parent, child2)

  children = list(backend.iter_children(parent))
  assert len(children) == 2
  assert backend.get_tag(children[0]) == "child1"
  assert backend.get_tag(children[1]) == "child2"


def test_namespaces(backend):
  """Verify namespace handling in tags and attributes."""
  nsmap = {"ns": "http://example.com/ns"}
  backend.register_namespace("ns", "http://example.com/ns")

  # Create with prefixed tag
  el = backend.create_element("{http://example.com/ns}root", nsmap=nsmap)

  # Get tag as string (Clark notation)
  assert backend.get_tag(el) == "{http://example.com/ns}root"

  # Get tag as QName
  qname = backend.get_tag(el, as_qname=True)
  assert isinstance(qname, QName)
  assert qname.local_name == "root"
  assert qname.uri == "http://example.com/ns"

  # Attributes with namespace
  backend.set_attribute(el, "{http://example.com/ns}attr", "val")
  assert backend.get_attribute(el, "{http://example.com/ns}attr") == "val"


def test_iter_children_filter(backend):
  """Verify filtering children by tag."""
  parent = backend.create_element("root")
  c1 = backend.create_element("a")
  c2 = backend.create_element("b")
  c3 = backend.create_element("a")

  backend.append_child(parent, c1)
  backend.append_child(parent, c2)
  backend.append_child(parent, c3)

  # Filter 'a'
  matches = list(backend.iter_children(parent, tag_filter="a"))
  assert len(matches) == 2
  assert all(backend.get_tag(x) == "a" for x in matches)

  # Filter 'b'
  matches_b = list(backend.iter_children(parent, tag_filter={"b"}))
  assert len(matches_b) == 1
  assert backend.get_tag(matches_b[0]) == "b"


def test_to_bytes(backend):
  """Verify serialization to bytes."""
  el = backend.create_element("root")
  backend.set_text(el, "content")

  output = backend.to_bytes(el)
  assert b"<root>content</root>" in output


def test_clear(backend):
  """Verify clearing an element."""
  parent = backend.create_element("parent")
  child = backend.create_element("child")
  backend.append_child(parent, child)
  backend.set_text(parent, "text")
  backend.set_attribute(parent, "k", "v")

  backend.clear(parent)

  # Attributes should be gone
  assert backend.get_attribute_map(parent) == {}
  # Children should be gone
  assert list(backend.iter_children(parent)) == []
  assert backend.get_text(parent) is None
