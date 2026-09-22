"""Unit tests for the shared field/attribute name mapping."""

import pytest

from hypomnema.models import (
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
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)
from hypomnema.xml.names import NON_ATTRIBUTE_FIELDS, xml_attribute_name

ALL_MODELS = (Note, Property, Map, Ude, Header, TranslationUnit, TranslationUnitVariant, Bpt, Ept, It, Ph, Hi, Ut, Sub)


@pytest.mark.parametrize(
  ("field_name", "attribute_name"),
  [
    ("creationtool", "creationtool"),
    ("creationtoolversion", "creationtoolversion"),
    ("segtype", "segtype"),
    ("o_tmf", "o-tmf"),
    ("o_encoding", "o-encoding"),
    ("usagecount", "usagecount"),
    ("lastusagedate", "lastusagedate"),
    ("tuid", "tuid"),
    ("adminlang", "adminlang"),
    ("xml_lang", "{http://www.w3.org/XML/1998/namespace}lang"),
  ],
)
def test_field_names_map_mechanically(field_name: str, attribute_name: str) -> None:
  """Replace underscores with hyphens and qualify the xml_lang attribute."""
  assert xml_attribute_name(field_name) == attribute_name


def test_non_attribute_fields_are_the_explicit_slots() -> None:
  """Exclude only the discriminator and child or content slots from attributes."""
  assert NON_ATTRIBUTE_FIELDS == {"element", "metadata", "content", "text", "maps", "variants"}


@pytest.mark.parametrize("model_type", ALL_MODELS)
def test_every_attribute_field_follows_the_naming_rule(model_type) -> None:
  """Map every model attribute mechanically, with xml_lang namespace-qualified."""
  for field_name in model_type.model_fields:
    if field_name in NON_ATTRIBUTE_FIELDS:
      continue
    attribute_name = xml_attribute_name(field_name)
    if field_name == "xml_lang":
      assert attribute_name == "{http://www.w3.org/XML/1998/namespace}lang"
    else:
      assert attribute_name == field_name.replace("_", "-"), field_name
