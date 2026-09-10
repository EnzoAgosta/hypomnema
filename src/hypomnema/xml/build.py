"""Direct model-to-element projection for all TMX node models.

One flat, self-contained builder per node, mirroring both
``validation.py`` and ``parse.py``: each ``*_to_element`` gates its node
through the matching ``validate_*`` first (the whole subtree, contract
rules and advisories included -- failures raise ``TmxErrorGroup``, whose
``advisories`` stay readable) and only then builds a detached element.
The tag-to-builder dispatch belongs to the Writer, which sees the node
type it is about to stream out; ``to_element`` is a thin type-dispatching
convenience on top for callers that hold a bare node.

This is projection, not pretty-printing, and there is no ``model_dump()``.
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
  """Gate the header through its strict validation, then build a
  detached element."""
  validate_header(header)
  return _to_element(header)


def tu_to_element(tu: TranslationUnit) -> etree._Element:
  """Gate the unit -- every variant, every inline element -- through its
  strict validation, then build a detached element."""
  validate_translation_unit(tu)
  return _to_element(tu)


def tuv_to_element(tuv: TranslationUnitVariant) -> etree._Element:
  """Gate the variant through its strict validation, then build a
  detached element."""
  validate_translation_unit_variant(tuv)
  return _to_element(tuv)


def note_to_element(note: Note) -> etree._Element:
  validate_note(note)
  return _to_element(note)


def prop_to_element(prop: Property) -> etree._Element:
  validate_property(prop)
  return _to_element(prop)


def ude_to_element(ude: Ude) -> etree._Element:
  validate_ude(ude)
  return _to_element(ude)


def map_to_element(mapping: Map) -> etree._Element:
  validate_map(mapping)
  return _to_element(mapping)


def bpt_to_element(bpt: Bpt) -> etree._Element:
  validate_bpt(bpt)
  return _to_element(bpt)


def ept_to_element(ept: Ept) -> etree._Element:
  validate_ept(ept)
  return _to_element(ept)


def it_to_element(it: It) -> etree._Element:
  validate_it(it)
  return _to_element(it)


def ph_to_element(ph: Ph) -> etree._Element:
  validate_ph(ph)
  return _to_element(ph)


def hi_to_element(hi: Hi) -> etree._Element:
  validate_hi(hi)
  return _to_element(hi)


def ut_to_element(ut: Ut) -> etree._Element:
  validate_ut(ut)
  return _to_element(ut)


def sub_to_element(sub: Sub) -> etree._Element:
  validate_sub(sub)
  return _to_element(sub)


def to_element(model: TmxNode) -> etree._Element:
  """Validate then build, dispatching on the model type. Convenience for
  callers that hold a bare node."""
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
  """Build a detached element without revalidating: the caller has run
  the boundary validation pass."""
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
  """Walk native fields, excluding the discriminator and explicit child slots."""
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
  # Finish recursion before interleaving, so each ancestor does not keep
  # write_mixed_content's frame on the stack while building its descendants.
  projected_items = [item if isinstance(item, str) else _to_element(item) for item in items]
  write_mixed_content(element, projected_items)
