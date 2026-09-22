"""Map model field names to TMX XML attribute names.

Hyphens in XML names become underscores in model fields. The ``xml_lang``
field maps to the expanded name for ``xml:lang`` in the XML namespace.
"""

XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
XML_LANG = f"{{{XML_NAMESPACE}}}lang"

NON_ATTRIBUTE_FIELDS = frozenset({"element", "metadata", "content", "text", "maps", "variants"})
"""Model fields that are not XML attributes: the discriminator and the explicit child/content slots."""


def xml_attribute_name(field_name: str) -> str:
  """Return the XML attribute name corresponding to a model field.

  Args:
      field_name: Attribute field name, excluding child and content fields.

  Returns:
      The expanded XML name for ``xml_lang``, or the name with underscores
      replaced by hyphens.
  """
  return XML_LANG if field_name == "xml_lang" else field_name.replace("_", "-")
