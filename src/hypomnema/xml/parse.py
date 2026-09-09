"""Direct element-to-model projection for all TMX node models.

Accepts already-parsed lxml elements, not bytes. Parser configuration and
document wrappers remain separate work. There are no standalone models for
tmx/body/seg; seg is a tuv content wrapper.
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
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)
from ..validation import validate
from .content import child_elements, read_mixed_content, read_text
from .dtd import validate_fragment
from .names import XML_LANG


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
          {
            "creationtool": element.get("creationtool"),
            "creationtoolversion": element.get("creationtoolversion"),
            "segtype": element.get("segtype"),
            "o_tmf": element.get("o-tmf"),
            "adminlang": element.get("adminlang"),
            "srclang": element.get("srclang"),
            "datatype": element.get("datatype"),
            "o_encoding": element.get("o-encoding"),
            "creationdate": element.get("creationdate"),
            "creationid": element.get("creationid"),
            "changedate": element.get("changedate"),
            "changeid": element.get("changeid"),
            "metadata": tuple(_from_element(child) for child in child_elements(element)),
          }
        )
      case "tu":
        children = tuple(child_elements(element))
        # The DTD has already checked ((note|prop)*, tuv+): metadata first,
        # then the variants, so document order survives the split.
        return TranslationUnit.model_validate(
          {
            "tuid": element.get("tuid"),
            "o_encoding": element.get("o-encoding"),
            "datatype": element.get("datatype"),
            "usagecount": element.get("usagecount"),
            "lastusagedate": element.get("lastusagedate"),
            "creationtool": element.get("creationtool"),
            "creationtoolversion": element.get("creationtoolversion"),
            "creationdate": element.get("creationdate"),
            "creationid": element.get("creationid"),
            "changedate": element.get("changedate"),
            "segtype": element.get("segtype"),
            "changeid": element.get("changeid"),
            "o_tmf": element.get("o-tmf"),
            "srclang": element.get("srclang"),
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
          {
            "xml_lang": element.get(XML_LANG),
            "o_encoding": element.get("o-encoding"),
            "datatype": element.get("datatype"),
            "usagecount": element.get("usagecount"),
            "lastusagedate": element.get("lastusagedate"),
            "creationtool": element.get("creationtool"),
            "creationtoolversion": element.get("creationtoolversion"),
            "creationdate": element.get("creationdate"),
            "creationid": element.get("creationid"),
            "changedate": element.get("changedate"),
            "o_tmf": element.get("o-tmf"),
            "changeid": element.get("changeid"),
            "lang": element.get("lang"),
            "metadata": tuple(_from_element(child) for child in children if child.tag in ("note", "prop")),
            "content": _parse_content(segment),
          }
        )
      case "note":
        return Note.model_validate(
          {
            "o_encoding": element.get("o-encoding"),
            "xml_lang": element.get(XML_LANG),
            "lang": element.get("lang"),
            "text": read_text(element),
          }
        )
      case "prop":
        return Property.model_validate(
          {
            "type": element.get("type"),
            "xml_lang": element.get(XML_LANG),
            "o_encoding": element.get("o-encoding"),
            "lang": element.get("lang"),
            "text": read_text(element),
          }
        )
      case "ude":
        # The DTD has already checked map+.
        return Ude.model_validate(
          {
            "name": element.get("name"),
            "base": element.get("base"),
            "maps": tuple(_from_element(child) for child in child_elements(element)),
          }
        )
      case "map":
        return Map.model_validate(
          {
            "unicode": element.get("unicode"),
            "code": element.get("code"),
            "ent": element.get("ent"),
            "subst": element.get("subst"),
          }
        )
      case "seg" | "tmx" | "body":
        raise TmxSpecError(
          f"<{element.tag}> has no standalone domain model: project a <tuv>, <header>, or <tu> fragment instead"
        )
      case "bpt":
        return Bpt.model_validate(
          {
            "i": element.get("i"),
            "x": element.get("x"),
            "type": element.get("type"),
            "content": _parse_content(element),
          }
        )
      case "ept":
        return Ept.model_validate({"i": element.get("i"), "content": _parse_content(element)})
      case "it":
        return It.model_validate(
          {
            "pos": element.get("pos"),
            "x": element.get("x"),
            "type": element.get("type"),
            "content": _parse_content(element),
          }
        )
      case "ph":
        return Ph.model_validate(
          {
            "x": element.get("x"),
            "assoc": element.get("assoc"),
            "type": element.get("type"),
            "content": _parse_content(element),
          }
        )
      case "hi":
        return Hi.model_validate(
          {"x": element.get("x"), "type": element.get("type"), "content": _parse_content(element)}
        )
      case "ut":
        return Ut.model_validate({"x": element.get("x"), "content": _parse_content(element)})
      case "sub":
        return Sub.model_validate(
          {"datatype": element.get("datatype"), "type": element.get("type"), "content": _parse_content(element)}
        )
      case _:
        raise TmxSpecError(f"<{element.tag}> is not a TMX 1.4b element")
  except ValidationError as error:
    raise TmxSpecError(f"<{element.tag}> at line {element.sourceline}: {error}") from error


def _parse_content(element: etree._Element) -> tuple[str | TmxNode, ...]:
  return tuple(item if isinstance(item, str) else _from_element(item) for item in read_mixed_content(element))
