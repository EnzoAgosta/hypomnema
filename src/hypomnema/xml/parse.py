"""Project existing lxml elements into TMX models.

Public parsers check fragment structure against the packaged DTD and coerce
attribute values through the models. They preserve content order and
whitespace without mutating the supplied tree. Strict semantic validation
is separate and must run before output. Configure XML parsing and entity
handling before passing elements here, or use ``TmxReader``.

There are no standalone models for ``tmx``, ``body``, or ``seg``. A ``seg``
provides its parent variant's content.
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
  """Return an element's QName or reject tags that cannot name a TMX node.

  Namespaced tags, comments, and processing instructions raise
  ``TmxSpecError``. The local name is checked by the caller.
  """
  try:
    qname = etree.QName(element)
  except ValueError as error:
    raise TmxSpecError(f"expected a namespace-free TMX element, got {element.tag!r}") from error
  if qname.namespace is not None:
    raise TmxSpecError(f"expected a namespace-free TMX element, got {element.tag!r}")
  return qname


def _attributes(element: etree._Element, model_type: type[TmxModel]) -> dict[str, str | None]:
  """Map XML attributes to model fields after DTD validation.

  Child and discriminator fields are excluded. Missing optional attributes
  remain ``None`` for model construction.
  """
  return {
    field_name: element.get(xml_attribute_name(field_name))
    for field_name in model_type.model_fields
    if field_name not in NON_ATTRIBUTE_FIELDS
  }


def _project[ModelType: TmxModel](
  element: etree._Element, model_type: type[ModelType], fields: dict[str, object]
) -> ModelType:
  """Check the tag and DTD, then construct a model from attributes and fields.

  Args:
      element: Fragment whose name and structure must match ``model_type``.
      model_type: Model class to construct.
      fields: Already projected content and children, merged over attributes.

  Returns:
      A model with coerced attribute values, without strict validation.

  Raises:
      TmxSpecError: The tag, DTD structure, or model field values are invalid.
  """
  qname = _element_qname(element)
  expected_tag = model_type.model_fields["element"].default
  if qname.localname != expected_tag:
    raise TmxSpecError(f"expected <{expected_tag}>, got <{qname.localname}> at line {element.sourceline}")
  validate_fragment(element)
  try:
    return model_type.model_validate(_attributes(element, model_type) | fields)
  except ValidationError as error:
    raise TmxSpecError(f"<{qname.localname}> at line {element.sourceline}: {error}") from error


def note_from_element(element: etree._Element) -> Note:
  """Parse a ``<note>`` fragment with its text and attributes.

  Args:
      element: Namespace-free ``<note>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Note, {"text": read_text(element)})


def prop_from_element(element: etree._Element) -> Property:
  """Parse a ``<prop>`` fragment with its text and attributes.

  Args:
      element: Namespace-free ``<prop>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Property, {"text": read_text(element)})


def map_from_element(element: etree._Element) -> Map:
  """Parse a ``<map>`` fragment with its attributes.

  Args:
      element: Namespace-free ``<map>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Map, {})


def ude_from_element(element: etree._Element) -> Ude:
  """Parse a ``<ude>`` fragment with its ordered character mappings.

  Args:
      element: Namespace-free ``<ude>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Ude, {"maps": [from_element(child) for child in child_elements(element)]})


def header_from_element(element: etree._Element) -> Header:
  """Parse a ``<header>`` fragment with its ordered metadata.

  Args:
      element: Namespace-free ``<header>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Header, {"metadata": [from_element(child) for child in child_elements(element)]})


def tu_from_element(element: etree._Element) -> TranslationUnit:
  """Parse a ``<tu>`` fragment with its ordered metadata and variants.

  Args:
      element: Namespace-free ``<tu>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
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
  """Parse a ``<tuv>`` fragment with its metadata and mixed content from its single segment.

  Args:
      element: Namespace-free ``<tuv>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  qname = _element_qname(element)
  if qname.localname != "tuv":
    raise TmxSpecError(f"expected <tuv>, got <{qname.localname}> at line {element.sourceline}")
  children = list(child_elements(element))
  segments = [child for child in children if child.tag == "seg"]
  if len(segments) != 1:
    raise TmxSpecError(f"<tuv> at line {element.sourceline}: expected exactly one <seg>, got {len(segments)}")
  return _project(
    element,
    TranslationUnitVariant,
    {
      "metadata": [from_element(child) for child in children if child.tag in ("note", "prop")],
      "content": _parse_content(segments[0]),
    },
  )


def bpt_from_element(element: etree._Element) -> Bpt:
  """Parse a ``<bpt>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<bpt>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Bpt, {"content": _parse_content(element)})


def ept_from_element(element: etree._Element) -> Ept:
  """Parse a ``<ept>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<ept>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Ept, {"content": _parse_content(element)})


def it_from_element(element: etree._Element) -> It:
  """Parse a ``<it>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<it>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, It, {"content": _parse_content(element)})


def ph_from_element(element: etree._Element) -> Ph:
  """Parse a ``<ph>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<ph>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Ph, {"content": _parse_content(element)})


def hi_from_element(element: etree._Element) -> Hi:
  """Parse a ``<hi>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<hi>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Hi, {"content": _parse_content(element)})


def ut_from_element(element: etree._Element) -> Ut:
  """Parse a ``<ut>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<ut>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Ut, {"content": _parse_content(element)})


def sub_from_element(element: etree._Element) -> Sub:
  """Parse a ``<sub>`` fragment with its attributes and mixed content.

  Args:
      element: Namespace-free ``<sub>`` element. The tree is not modified,
          and the element's own tail is excluded.

  Returns:
      A model with coerced attributes. Strict semantic validation is deferred.

  Raises:
      TmxSpecError: The tag, DTD structure, or projected field values are invalid.
  """
  return _project(element, Sub, {"content": _parse_content(element)})


def from_element(element: etree._Element) -> TmxNode:
  """Parse a supported TMX node by dispatching on its namespace-free tag.

  Args:
      element: Existing element to project without mutation. Wrapper elements
          ``tmx``, ``body``, and ``seg`` are not standalone nodes.

  Returns:
      A model with coerced attributes and projected children. Strict semantic
      validation has not been performed.

  Raises:
      TmxSpecError: The tag is unsupported or namespaced, the fragment fails
          DTD validation, or its content cannot be projected into a model.
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
  """Project mixed content into text and models while preserving their order."""
  return [item if isinstance(item, str) else from_element(item) for item in read_mixed_content(element)]
