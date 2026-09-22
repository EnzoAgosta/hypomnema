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


def _parse[ModelType: TmxModel](element: etree._Element, model_type: type[ModelType]) -> ModelType:
  """Validate a public fragment once before recursively projecting its nodes."""
  qname = _element_qname(element)
  expected_tag = model_type.model_fields["element"].default
  if qname.localname != expected_tag:
    raise TmxSpecError(f"expected <{expected_tag}>, got <{qname.localname}> at line {element.sourceline}")
  validate_fragment(element)
  return _project(element, model_type)


def _project[ModelType: TmxModel](element: etree._Element, model_type: type[ModelType]) -> ModelType:
  """Coerce a node from a subtree that already passed the public DTD gate."""
  fields: dict[str, object] = {}
  match element.tag:
    case "note" | "prop":
      fields["text"] = read_text(element)
    case "header":
      fields["metadata"] = [_project_child(child) for child in child_elements(element)]
    case "ude":
      fields["maps"] = [_project_child(child) for child in child_elements(element)]
    case "tu":
      metadata: list[TmxNode] = []
      variants: list[TmxNode] = []
      for child in child_elements(element):
        (variants if child.tag == "tuv" else metadata).append(_project_child(child))
      fields.update(metadata=metadata, variants=variants)
    case "tuv":
      metadata = []
      for child in child_elements(element):
        if child.tag == "seg":
          fields["content"] = _parse_content(child)
        else:
          metadata.append(_project_child(child))
      fields["metadata"] = metadata
    case "map":
      pass
    case _:
      fields["content"] = _parse_content(element)
  try:
    return model_type.model_validate(_attributes(element, model_type) | fields)
  except ValidationError as error:
    raise TmxSpecError(f"<{element.tag}> at line {element.sourceline}: {error}") from error


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
  return _parse(element, Note)


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
  return _parse(element, Property)


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
  return _parse(element, Map)


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
  return _parse(element, Ude)


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
  return _parse(element, Header)


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
  return _parse(element, TranslationUnit)


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
  return _parse(element, TranslationUnitVariant)


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
  return _parse(element, Bpt)


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
  return _parse(element, Ept)


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
  return _parse(element, It)


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
  return _parse(element, Ph)


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
  return _parse(element, Hi)


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
  return _parse(element, Ut)


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
  return _parse(element, Sub)


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
  return _parse(element, _model_type(element))


_MODEL_TYPES: dict[str, type[TmxNode]] = {
  "note": Note,
  "prop": Property,
  "map": Map,
  "ude": Ude,
  "header": Header,
  "tu": TranslationUnit,
  "tuv": TranslationUnitVariant,
  "bpt": Bpt,
  "ept": Ept,
  "it": It,
  "ph": Ph,
  "hi": Hi,
  "ut": Ut,
  "sub": Sub,
}


def _model_type(element: etree._Element) -> type[TmxNode]:
  """Resolve a namespace-free tag to its domain model."""
  tag = _element_qname(element).localname
  if tag in ("seg", "tmx", "body"):
    raise TmxSpecError(f"<{tag}> has no standalone domain model: project a <tuv>, <header>, or <tu> fragment instead")
  try:
    return _MODEL_TYPES[tag]
  except KeyError:
    raise TmxSpecError(f"<{tag}> is not a TMX 1.4b element") from None


def _project_child(element: etree._Element) -> TmxNode:
  """Project a descendant without repeating its ancestor's DTD validation."""
  return _project(element, _model_type(element))


def _parse_content(element: etree._Element) -> list[str | TmxNode]:
  """Project mixed content into text and models while preserving their order."""
  return [item if isinstance(item, str) else _project_child(item) for item in read_mixed_content(element)]
