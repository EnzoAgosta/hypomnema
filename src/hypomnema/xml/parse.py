"""Direct element-to-model projection for all TMX node models.

Accepts already-parsed lxml elements, not bytes. Parser configuration and
document wrappers remain separate work. There are no standalone models for
tmx/body/seg; seg is a tuv content wrapper.

Every case dispatches on the element tag and owns its content/child shape
in code; the mechanical attribute-name mapping (models.py's field-naming
rule) is shared with the build direction through ``names.py``.
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
  Note,
  Map,
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
from ..validation import validate
from .content import child_elements, read_mixed_content, read_text
from .dtd import validate_fragment
from .names import NON_ATTRIBUTE_FIELDS, xml_attribute_name


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


def from_element(element: etree._Element) -> TmxNode:
  """DTD-check a fragment, project it, then validate it (GAPS decision 19).

  The DTD runs once over the whole fragment; recursion projects trusted
  structure; the boundary validation pass then applies every contract
  rule to the projected model. Typing errors surface with the nested
  element and line that caused them; contract errors from the validation
  pass surface with the fragment's root element and line, with
  model-relative error locations.
  """
  validate_fragment(element)
  node = _from_element(element)
  try:
    validate(node)
  except ValidationError as error:
    raise TmxSpecError(f"<{element.tag}> at line {element.sourceline}: {error}") from error
  return node


def _from_element(element: etree._Element) -> TmxNode:
  if not isinstance(element.tag, str) or element.tag.startswith("{"):
    raise TmxSpecError(f"expected a namespace-free TMX element, got {element.tag!r}")
  try:
    match element.tag:
      case "header":
        # The DTD has already checked the required attributes and the
        # (note|prop|ude)* child pattern.
        return Header.model_validate(
          _attributes(element, Header) | {"metadata": tuple(_from_element(child) for child in child_elements(element))}
        )
      case "tu":
        children = tuple(child_elements(element))
        # The DTD has already checked ((note|prop)*, tuv+): metadata first,
        # then the variants, so document order survives the split.
        return TranslationUnit.model_validate(
          _attributes(element, TranslationUnit)
          | {
            "metadata": tuple(_from_element(child) for child in children if child.tag in ("note", "prop")),
            "variants": tuple(_from_element(child) for child in children if child.tag == "tuv"),
          }
        )
      case "tuv":
        children = tuple(child_elements(element))
        # The DTD has already checked ((note|prop)*, seg), so the single
        # <seg> exists and follows the metadata.
        (segment,) = (child for child in children if child.tag == "seg")
        return TranslationUnitVariant.model_validate(
          _attributes(element, TranslationUnitVariant)
          | {
            "metadata": tuple(_from_element(child) for child in children if child.tag in ("note", "prop")),
            "content": _parse_content(segment),
          }
        )
      case "note":
        return Note.model_validate(_attributes(element, Note) | {"text": read_text(element)})
      case "prop":
        return Property.model_validate(_attributes(element, Property) | {"text": read_text(element)})
      case "ude":
        # The DTD has already checked map+.
        return Ude.model_validate(
          _attributes(element, Ude) | {"maps": tuple(_from_element(child) for child in child_elements(element))}
        )
      case "map":
        return Map.model_validate(_attributes(element, Map))
      case "seg" | "tmx" | "body":
        raise TmxSpecError(
          f"<{element.tag}> has no standalone domain model: project a <tuv>, <header>, or <tu> fragment instead"
        )
      case "bpt":
        return Bpt.model_validate(_attributes(element, Bpt) | {"content": _parse_content(element)})
      case "ept":
        return Ept.model_validate(_attributes(element, Ept) | {"content": _parse_content(element)})
      case "it":
        return It.model_validate(_attributes(element, It) | {"content": _parse_content(element)})
      case "ph":
        return Ph.model_validate(_attributes(element, Ph) | {"content": _parse_content(element)})
      case "hi":
        return Hi.model_validate(_attributes(element, Hi) | {"content": _parse_content(element)})
      case "ut":
        return Ut.model_validate(_attributes(element, Ut) | {"content": _parse_content(element)})
      case "sub":
        return Sub.model_validate(_attributes(element, Sub) | {"content": _parse_content(element)})
      case _:
        raise TmxSpecError(f"<{element.tag}> is not a TMX 1.4b element")
  except ValidationError as error:
    raise TmxSpecError(f"<{element.tag}> at line {element.sourceline}: {error}") from error


def _parse_content(element: etree._Element) -> tuple[str | TmxNode, ...]:
  return tuple(item if isinstance(item, str) else _from_element(item) for item in read_mixed_content(element))
