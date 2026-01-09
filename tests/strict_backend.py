from hypomnema import XmlBackend
import xml.etree.ElementTree as et
from hypomnema.xml.utils import normalize_encoding, prep_tag_set, QName


class StrictBackend(XmlBackend[int]):
  """
  A test-only backend that passes integers (IDs) to handlers instead of objects.
  This guarantees handlers NEVER access underlying XML objects directly.
  It uses lxml.etree internally for storage.
  """

  def __init__(self, logger, nsmap=None) -> None:
    self._global_nsmap = {"xml": "http://www.w3.org/XML/1998/namespace"}
    if nsmap is not None:
      self._global_nsmap.update(nsmap)
    self.logger = logger
    # Maps handle (id) -> Element
    self._store = {}

  def _register(self, element):
    """Register an internal element and return a handle."""
    obj_id = id(element)
    if obj_id not in self._store:
      self._store[obj_id] = element
    return obj_id

  def _get_elem(self, handle):
    """Retrieve the internal element from a handle."""
    return self._store[handle]

  def get_tag(self, element, *, as_qname=False, nsmap=None):
    elem = self._get_elem(element)
    tag = elem.tag
    if as_qname:
      return QName(tag, nsmap if nsmap is not None else self._global_nsmap)
    return tag

  def create_element(self, tag, attributes=None, *, nsmap=None):
    if isinstance(tag, QName):
      tag_name = tag.text
    else:
      tag_name = tag

    elem = et.Element(tag_name, attrib=attributes or {})
    return self._register(elem)

  def append_child(self, parent, child):
    p_elem = self._get_elem(parent)
    c_elem = self._get_elem(child)
    p_elem.append(c_elem)

  def get_attribute(self, element, attribute_name, default=None, *, nsmap=None):
    elem = self._get_elem(element)
    _nsmap = nsmap if nsmap is not None else self._global_nsmap
    if attribute_name[0] == "{" or ":" in attribute_name:
      attribute_name = QName(attribute_name, _nsmap).qualified_name

    return elem.get(attribute_name, default)

  def set_attribute(self, element, attribute_name, attribute_value, *, nsmap=None, unsafe=False):
    elem = self._get_elem(element)

    _nsmap = nsmap if nsmap is not None else self._global_nsmap
    attribute_name = attribute_name if unsafe else QName(attribute_name, _nsmap).qualified_name

    if attribute_value is None:
      if attribute_name in elem.attrib:
        elem.attrib.pop(attribute_name)
    else:
      elem.attrib[attribute_name] = attribute_value

  def get_attribute_map(self, element):
    elem = self._get_elem(element)
    return dict(elem.attrib)

  def get_text(self, element):
    elem = self._get_elem(element)
    return elem.text

  def set_text(self, element, text):
    elem = self._get_elem(element)
    elem.text = text

  def get_tail(self, element):
    elem = self._get_elem(element)
    return elem.tail

  def set_tail(self, element, tail):
    elem = self._get_elem(element)
    elem.tail = tail

  def iter_children(self, element, tag_filter=None, *, nsmap=None):
    elem = self._get_elem(element)

    tags = prep_tag_set(tag_filter, nsmap if nsmap is not None else self._global_nsmap)

    for child in elem:
      if tags is None or child.tag in tags:
        yield self._register(child)

  def parse(self, path, encoding="utf-8"):
    tree = et.parse(path)
    return self._register(tree.getroot())

  def write(self, element, path, encoding="utf-8"):
    elem = self._get_elem(element)
    tree = et.ElementTree(elem)
    tree.write(
      path, encoding=normalize_encoding(encoding), xml_declaration=True, short_empty_elements=False
    )

  def clear(self, element):
    elem = self._get_elem(element)
    elem.clear()

  def to_bytes(self, element, encoding="utf-8", self_closing=False):
    elem = self._get_elem(element)
    return et.tostring(
      elem, encoding=normalize_encoding(encoding), xml_declaration=False, short_empty_elements=False
    )

  def iterparse(self, path, tag_filter=None, *, nsmap=None):
    tags = prep_tag_set(tag_filter, nsmap if nsmap is not None else self._global_nsmap)
    context = et.iterparse(path, events=("start", "end"))
    pending_yield_stack = []

    for event, elem in context:
      if event == "start":
        if tags is None or elem.tag in tags:
          pending_yield_stack.append(elem)
        continue

      if not pending_yield_stack:
        elem.clear()
        continue

      if elem is pending_yield_stack[-1]:
        pending_yield_stack.pop()
        yield self._register(elem)

      if not pending_yield_stack:
        self.clear(elem)
      pass

  def iterwrite(
    self,
    path,
    elements,
    encoding="utf-8",
    *,
    root_elem=None,
    max_number_of_elements_in_buffer=1000,
    write_xml_declaration=True,
    write_doctype=True,
  ):
    elements = (self._get_elem(self._register(element)) for element in elements)
    root_elem = self.create_element("tmx", attributes={"version": "1.4"})

    return super().iterwrite(
      path,
      elements,
      encoding,
      root_elem=root_elem,
      max_number_of_elements_in_buffer=max_number_of_elements_in_buffer,
      write_xml_declaration=write_xml_declaration,
      write_doctype=write_doctype,
    )
