"""Validate TMX models and build detached lxml element trees.

Each public builder validates its complete model subtree, including strict
contract rules and advisories, before projection. Validation failures raise
``TmxErrorGroup`` with advisories attached. Builders preserve content order
and whitespace, format native attribute values, and do not mutate models.
DTD validation is a separate step performed by ``TmxWriter``.
"""

from collections.abc import Sequence
from datetime import datetime

from lxml import etree

from ..coercion import format_datetime, format_hex_integer
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
from ..validation import (
  validate_bpt,
  validate_ept,
  validate_header,
  validate_hi,
  validate_it,
  validate_map,
  validate_note,
  validate_ph,
  validate_property,
  validate_sub,
  validate_translation_unit,
  validate_translation_unit_variant,
  validate_ude,
  validate_ut,
)
from .content import write_mixed_content, write_text
from .names import NON_ATTRIBUTE_FIELDS, xml_attribute_name


def header_to_element(header: Header) -> etree._Element:
  """Validate a header and build its detached XML subtree.

  Args:
      header: Model to validate and project without modification.

  Returns:
      A new ``<header>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_header(header)
  return _to_element(header)


def tu_to_element(tu: TranslationUnit) -> etree._Element:
  """Validate a translation unit and build its detached XML subtree.

  Args:
      tu: Model to validate and project without modification.

  Returns:
      A new ``<tu>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_translation_unit(tu)
  return _to_element(tu)


def tuv_to_element(tuv: TranslationUnitVariant) -> etree._Element:
  """Validate a translation-unit variant and build its detached XML subtree.

  Args:
      tuv: Model to validate and project without modification.

  Returns:
      A new ``<tuv>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_translation_unit_variant(tuv)
  return _to_element(tuv)


def note_to_element(note: Note) -> etree._Element:
  """Validate a note and build its detached XML subtree.

  Args:
      note: Model to validate and project without modification.

  Returns:
      A new ``<note>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_note(note)
  return _to_element(note)


def prop_to_element(prop: Property) -> etree._Element:
  """Validate a property and build its detached XML subtree.

  Args:
      prop: Model to validate and project without modification.

  Returns:
      A new ``<prop>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_property(prop)
  return _to_element(prop)


def ude_to_element(ude: Ude) -> etree._Element:
  """Validate a user-defined encoding and build its detached XML subtree.

  Args:
      ude: Model to validate and project without modification.

  Returns:
      A new ``<ude>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_ude(ude)
  return _to_element(ude)


def map_to_element(mapping: Map) -> etree._Element:
  """Validate a character mapping and build its detached XML subtree.

  Args:
      mapping: Model to validate and project without modification.

  Returns:
      A new empty ``<map>`` element containing the model's attributes.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_map(mapping)
  return _to_element(mapping)


def bpt_to_element(bpt: Bpt) -> etree._Element:
  """Validate a paired-code opening and build its detached XML subtree.

  Matching with an outer closing code requires validation of the enclosing
  flow; this standalone builder cannot check that relationship.

  Args:
      bpt: Model to validate and project without modification.

  Returns:
      A new ``<bpt>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_bpt(bpt)
  return _to_element(bpt)


def ept_to_element(ept: Ept) -> etree._Element:
  """Validate a paired-code closing and build its detached XML subtree.

  Matching with an outer opening code requires validation of the enclosing
  flow; this standalone builder cannot check that relationship.

  Args:
      ept: Model to validate and project without modification.

  Returns:
      A new ``<ept>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_ept(ept)
  return _to_element(ept)


def it_to_element(it: It) -> etree._Element:
  """Validate an isolated code and build its detached XML subtree.

  Args:
      it: Model to validate and project without modification.

  Returns:
      A new ``<it>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_it(it)
  return _to_element(it)


def ph_to_element(ph: Ph) -> etree._Element:
  """Validate a placeholder and build its detached XML subtree.

  Args:
      ph: Model to validate and project without modification.

  Returns:
      A new ``<ph>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_ph(ph)
  return _to_element(ph)


def hi_to_element(hi: Hi) -> etree._Element:
  """Validate a highlighted span and build its detached XML subtree.

  The span is checked as a complete pairing flow. Build the enclosing
  variant instead when a code pair crosses the highlight boundary.

  Args:
      hi: Model to validate and project without modification.

  Returns:
      A new ``<hi>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_hi(hi)
  return _to_element(hi)


def ut_to_element(ut: Ut) -> etree._Element:
  """Validate an unknown code and build its detached XML subtree.

  Args:
      ut: Model to validate and project without modification.

  Returns:
      A new ``<ut>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_ut(ut)
  return _to_element(ut)


def sub_to_element(sub: Sub) -> etree._Element:
  """Validate a subflow and build its detached XML subtree.

  Args:
      sub: Model to validate and project without modification.

  Returns:
      A new ``<sub>`` element containing the model's attributes and content.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  validate_sub(sub)
  return _to_element(sub)


def to_element(model: TmxNode) -> etree._Element:
  """Validate a TMX node and build its XML subtree by model type.

  Args:
      model: Any supported TMX node model. The entire subtree is validated.

  Returns:
      A new detached element, with child order and whitespace preserved.

  Raises:
      TmxErrorGroup: Strict model validation fails.
      TmxSpecError: An attribute or text value cannot be represented in XML.
  """
  match model:
    case Header():
      return header_to_element(model)
    case TranslationUnit():
      return tu_to_element(model)
    case TranslationUnitVariant():
      return tuv_to_element(model)
    case Ude():
      return ude_to_element(model)
    case Map():
      return map_to_element(model)
    case Note():
      return note_to_element(model)
    case Property():
      return prop_to_element(model)
    case Bpt():
      return bpt_to_element(model)
    case Ept():
      return ept_to_element(model)
    case It():
      return it_to_element(model)
    case Ph():
      return ph_to_element(model)
    case Hi():
      return hi_to_element(model)
    case Ut():
      return ut_to_element(model)
    case Sub():
      return sub_to_element(model)


def _to_element(model: TmxNode) -> etree._Element:
  """Build a detached subtree from a model that has already passed validation."""
  element = etree.Element(model.element)
  _write_attributes(element, model)

  match model:
    case Note() | Property():
      write_text(element, model.text)
    case Header():
      element.extend(_to_element(child) for child in model.metadata)
    case TranslationUnit():
      element.extend(_to_element(child) for child in model.metadata)
      element.extend(_to_element(variant) for variant in model.variants)
    case TranslationUnitVariant():
      element.extend(_to_element(child) for child in model.metadata)
      segment = etree.SubElement(element, "seg")
      _build_content(segment, model.content)
    case Ude():
      element.extend(_to_element(mapping) for mapping in model.maps)
    case Map():
      pass  # EMPTY: attributes only, not even formatting whitespace.
    case Bpt() | Ept() | It() | Ph() | Hi() | Ut() | Sub():
      _build_content(element, model.content)
  return element


def _write_attributes(element: etree._Element, model: TmxModel) -> None:
  """Set XML attributes from native model fields, omitting absent values.

  Dates use basic ISO notation with their offsets preserved; integer map
  attributes use hexadecimal.
  Child fields and the element discriminator are excluded. Unsupported
  value types raise ``TypeError``; XML-illegal values raise ``TmxSpecError``.
  """
  field_value: object
  for field_name, field_value in model:
    if field_name in NON_ATTRIBUTE_FIELDS or field_value is None:
      continue

    match field_value:
      case str():
        formatted = field_value
      case datetime():
        formatted = format_datetime(field_value)
      # Every int attribute of a <map> is a #x-hex value (unicode, code).
      case int() if isinstance(model, Map):
        formatted = format_hex_integer(field_value)
      case int():
        formatted = str(field_value)
      case _:
        raise TypeError(f"unsupported attribute value for {type(model).__name__}.{field_name}")

    xml_name = xml_attribute_name(field_name)
    try:
      element.set(xml_name, formatted)
    except ValueError as error:
      raise TmxSpecError(f"XML-illegal attribute {xml_name!r} on <{element.tag}>: {error}") from error


def _build_content(element: etree._Element, items: Sequence[str | TmxNode]) -> None:
  """Project child models, then append text and children in their original order."""
  # Finish recursion before interleaving, so each ancestor does not keep
  # write_mixed_content's frame on the stack while building its descendants.
  projected_items = [item if isinstance(item, str) else _to_element(item) for item in items]
  write_mixed_content(element, projected_items)
