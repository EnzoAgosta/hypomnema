"""Direct element-to-model projection for all TMX node models.

Accepts already-parsed lxml elements, not bytes: parser configuration and
streaming belong to the Reader, not to these functions, so a consumer can
bring their own parsing. The domain is closed -- the DTD fixes every node
kind -- so the surface is one flat, self-contained function per element,
mirroring ``validation.py``'s per-node family: each function knows
everything about its own element, gates its own fragment on the DTD, and
is safe to call standalone from anywhere. ``from_element`` is a thin
tag-dispatching convenience on top for callers that hold a bare element.

Projection is the lax half. The DTD checks the fragment's structure
(required attributes, child patterns, unknown attributes) and pydantic
coerces or rejects bad values -- both raising ``TmxSpecError`` with the
offending element and line. The strict contract pass is deliberately NOT
run here: a projected node is not yet safe to output, and validation is
the Writer's (or a consumer's) explicit call. There are no standalone
models for tmx/body/seg; ``seg`` is a ``tuv`` content wrapper.
"""

from lxml import etree
from pydantic import ValidationError

from ..errors import TmxSpecError
from ..models import (
  Bpt,
  Ept,
  Header,
  Hi,
  It,
  Map,
  Note,
  Ph,
  Property,
  Sub,
  TmxModel,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)
from .content import child_elements, read_mixed_content, read_text
from .dtd import validate_fragment
from .names import NON_ATTRIBUTE_FIELDS, xml_attribute_name


def _element_qname(element: etree._Element) -> etree.QName:
  """The element's tag as a namespace-free ``QName``.

  lxml accepts tag types beyond plain names -- comments and processing
  instructions carry a callable tag -- and a namespaced element is not a
  TMX element at all. Anything but a plain namespace-free name is a
  ``TmxSpecError``."""
  try:
    qname = etree.QName(element)
  except ValueError as error:
    raise TmxSpecError(f"expected a namespace-free TMX element, got {element.tag!r}") from error
  if qname.namespace is not None:
    raise TmxSpecError(f"expected a namespace-free TMX element, got {element.tag!r}")
  return qname


def _attributes(element: etree._Element, model_type: type[TmxModel]) -> dict[str, str | None]:
  """Collect the element's attributes under their model-field names.

  Every field except the discriminator and the explicit child/content
  slots is an XML attribute. The DTD has already checked required
  attributes and rejected unknown ones, so whatever remains is
  model-visible.
  """
  return {
    field_name: element.get(xml_attribute_name(field_name))
    for field_name in model_type.model_fields
    if field_name not in NON_ATTRIBUTE_FIELDS
  }


def _project[ModelType: TmxModel](
  element: etree._Element, model_type: type[ModelType], fields: dict[str, object]
) -> ModelType:
  """The one projection body, shared by every ``*_from_element``:
  namespace and tag guard, DTD gate, attribute mapping plus the node's
  own fields, coercion. Keeping it here makes each per-node function
  safe to call standalone on any fragment."""
  qname = _element_qname(element)
  expected_tag = model_type.model_fields["element"].default
  if qname.localname != expected_tag:
    raise TmxSpecError(
      f"expected <{expected_tag}>, got <{qname.localname}> at line {element.sourceline}"
    )
  validate_fragment(element)
  try:
    return model_type.model_validate(_attributes(element, model_type) | fields)
  except ValidationError as error:
    raise TmxSpecError(f"<{qname.localname}> at line {element.sourceline}: {error}") from error


def note_from_element(element: etree._Element) -> Note:
  """A ``<note>``: its attributes plus its text."""
  return _project(element, Note, {"text": read_text(element)})


def prop_from_element(element: etree._Element) -> Property:
  """A ``<prop>``: its attributes plus its text."""
  return _project(element, Property, {"text": read_text(element)})


def map_from_element(element: etree._Element) -> Map:
  """A ``<map>``: attributes only, not even formatting whitespace."""
  return _project(element, Map, {})


def ude_from_element(element: etree._Element) -> Ude:
  """A ``<ude>``: its attributes plus its ``<map>`` children."""
  return _project(element, Ude, {"maps": [from_element(child) for child in child_elements(element)]})


def header_from_element(element: etree._Element) -> Header:
  """A ``<header>``: its attributes plus its metadata children."""
  return _project(element, Header, {"metadata": [from_element(child) for child in child_elements(element)]})


def tu_from_element(element: etree._Element) -> TranslationUnit:
  """A ``<tu>``: its attributes, its metadata children, then its
  variants -- document order survives the split."""
  children = list(child_elements(element))
  return _project(
    element,
    TranslationUnit,
    {
      "metadata": [from_element(child) for child in children if child.tag in ("note", "prop")],
      "variants": [from_element(child) for child in children if child.tag == "tuv"],
    },
  )


def tuv_from_element(element: etree._Element) -> TranslationUnitVariant:
  """A ``<tuv>``: its attributes, its metadata children, and its
  content -- the DTD's single ``<seg>`` is the content wrapper."""
  qname = _element_qname(element)
  if qname.localname != "tuv":
    raise TmxSpecError(
      f"expected <tuv>, got <{qname.localname}> at line {element.sourceline}"
    )
  children = list(child_elements(element))
  segments = [child for child in children if child.tag == "seg"]
  if len(segments) != 1:
    raise TmxSpecError(
      f"<tuv> at line {element.sourceline}: expected exactly one <seg>, got {len(segments)}"
    )
  return _project(
    element,
    TranslationUnitVariant,
    {
      "metadata": [from_element(child) for child in children if child.tag in ("note", "prop")],
      "content": _parse_content(segments[0]),
    },
  )


def bpt_from_element(element: etree._Element) -> Bpt:
  """A ``<bpt>``: its attributes plus its mixed content."""
  return _project(element, Bpt, {"content": _parse_content(element)})


def ept_from_element(element: etree._Element) -> Ept:
  """An ``<ept>``: its attributes plus its mixed content."""
  return _project(element, Ept, {"content": _parse_content(element)})


def it_from_element(element: etree._Element) -> It:
  """An ``<it>``: its attributes plus its mixed content."""
  return _project(element, It, {"content": _parse_content(element)})


def ph_from_element(element: etree._Element) -> Ph:
  """A ``<ph>``: its attributes plus its mixed content."""
  return _project(element, Ph, {"content": _parse_content(element)})


def hi_from_element(element: etree._Element) -> Hi:
  """A ``<hi>``: its attributes plus its mixed content."""
  return _project(element, Hi, {"content": _parse_content(element)})


def ut_from_element(element: etree._Element) -> Ut:
  """A ``<ut>``: its attributes plus its mixed content."""
  return _project(element, Ut, {"content": _parse_content(element)})


def sub_from_element(element: etree._Element) -> Sub:
  """A ``<sub>``: its attributes plus its mixed content."""
  return _project(element, Sub, {"content": _parse_content(element)})


def from_element(element: etree._Element) -> TmxNode:
  """Project any TMX element, dispatching on its tag's local name.

  Convenience for callers that hold a bare element; the per-node
  functions each gate their own fragment on the DTD, so this dispatcher
  adds no checks of its own beyond the name guard.
  """
  qname = _element_qname(element)
  match qname.localname:
    case "header":
      return header_from_element(element)
    case "tu":
      return tu_from_element(element)
    case "tuv":
      return tuv_from_element(element)
    case "note":
      return note_from_element(element)
    case "prop":
      return prop_from_element(element)
    case "ude":
      return ude_from_element(element)
    case "map":
      return map_from_element(element)
    case "bpt":
      return bpt_from_element(element)
    case "ept":
      return ept_from_element(element)
    case "it":
      return it_from_element(element)
    case "ph":
      return ph_from_element(element)
    case "hi":
      return hi_from_element(element)
    case "ut":
      return ut_from_element(element)
    case "sub":
      return sub_from_element(element)
    case "seg" | "tmx" | "body":
      raise TmxSpecError(
        f"<{qname.localname}> has no standalone domain model: project a <tuv>, <header>, or <tu> fragment instead"
      )
    case _:
      raise TmxSpecError(f"<{qname.localname}> is not a TMX 1.4b element")


def _parse_content(element: etree._Element) -> list[str | TmxNode]:
  return [item if isinstance(item, str) else from_element(item) for item in read_mixed_content(element)]
