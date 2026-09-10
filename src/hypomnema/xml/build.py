"""Direct model-to-element projection for all TMX node models."""

from datetime import datetime

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
from ..validators import format_datetime, format_hex_integer, format_integer
from ..validation import validate
from .content import write_mixed_content, write_text
from .names import NON_ATTRIBUTE_FIELDS, xml_attribute_name


def to_element(model: TmxNode) -> etree._Element:
  """Validate the model (GAPS decision 19), then build a detached element.

  The boundary validation pass applies every contract rule to the model's
  current state before anything is built; failures raise ``TmxSpecError``,
  and non-node input is rejected with ``TypeError`` by the same pass.
  This is projection, not pretty-printing, and no ``model_dump()``.
  """
  try:
    validate(model)
  except ValidationError as error:
    raise TmxSpecError(f"invalid {type(model).__name__}: {error}") from error
  return _to_element(model)


def _to_element(model: TmxNode) -> etree._Element:
  """Build a detached element without revalidating: the entry point has
  already run the boundary validation pass."""
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
        formatted = format_integer(field_value)
      case _:
        raise TypeError(f"unsupported attribute value for {type(model).__name__}.{field_name}")

    xml_name = xml_attribute_name(field_name)
    try:
      element.set(xml_name, formatted)
    except ValueError as error:
      raise TmxSpecError(f"XML-illegal attribute {xml_name!r} on <{element.tag}>: {error}") from error


def _build_content(element: etree._Element, items: tuple[str | TmxNode, ...]) -> None:
  # Finish recursion before interleaving, so each ancestor does not keep
  # write_mixed_content's frame on the stack while building its descendants.
  projected_items = tuple(item if isinstance(item, str) else _to_element(item) for item in items)
  write_mixed_content(element, projected_items)
