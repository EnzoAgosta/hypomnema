"""XML names and the model-field/attribute mapping shared by parsing and
building.

Field naming is mechanical: the TMX attribute name with ``-`` and ``:``
replaced by ``_``, otherwise verbatim -- ``o_tmf``, ``xml_lang``, and
plain ``type`` (models.py states the rule; this module implements it once).
"""

XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
XML_LANG = f"{{{XML_NAMESPACE}}}lang"

NON_ATTRIBUTE_FIELDS = frozenset({"element", "metadata", "content", "text", "maps", "variants"})
"""Model fields that are not XML attributes: the discriminator and the explicit child/content slots."""


def xml_attribute_name(field_name: str) -> str:
  """The XML attribute name for a model field (the mechanical naming rule)."""
  return XML_LANG if field_name == "xml_lang" else field_name.replace("_", "-")
