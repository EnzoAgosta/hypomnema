from dataclasses import dataclass, field
from logging import DEBUG
from typing import Literal

__all__ = ["PolicyValue", "XmlPolicy"]


@dataclass(slots=True)
class PolicyValue[Behavior: str]:
  """
  Container for policy behavior and logging configuration.

  Parameters
  ----------
  behavior : Behavior
      The action to execute when a policy condition is met.
  log_level : int
      The logging level to use before executing the behavior.

  Attributes
  ----------
  behavior : Behavior
      The action to execute when a policy condition is met.
  log_level : int
      The logging level to use before executing the behavior.
  """

  behavior: Behavior
  log_level: int


def _default[DefaultBehavior: str](
  default_behavior: DefaultBehavior,
) -> PolicyValue[DefaultBehavior]:
  return field(default_factory=lambda: PolicyValue(default_behavior, DEBUG))


@dataclass(slots=True, kw_only=True)
class XmlPolicy:
  """
  Configuration policy for XML serialization and deserialization.
  """

  # Namespace related items
  existing_namespace: PolicyValue[Literal["raise", "ignore", "overwrite"]] = _default("raise")
  """Action trying to register a namespace that is already registered."""
  missing_namespace: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when trying to deregister a namespace that is not registered."""
  invalid_namespace: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when trying to register a namespace with an invalid URI or prefix."""

  # Deserialization items
  missing_deserialization_handler: PolicyValue[Literal["raise", "ignore", "default"]] = _default(
    "raise"
  )
  """Action when no handler is registered for a TMX element.
  `default` will attempt fallback to internal library handlers."""
  invalid_tag: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when an unexpected XML tag is encountered."""
  required_attribute_missing: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when a mandatory TMX attribute is absent or its value is None in the case of a dataclass."""
  invalid_attribute_value: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when an attribute value violates TMX specifications."""
  extra_text: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when unexpected non-whitespace text is found within elements."""
  invalid_child_element: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when a child element is not permitted or allowed in that context by the TMX spec."""
  multiple_headers: PolicyValue[Literal["raise", "keep_first", "keep_last"]] = _default("raise")
  """Action when more than one `<header>` element exists in `<tmx>`.
  `keep_first` and `keep_last` will keep the first or last header encountered respectively."""
  missing_header: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when the mandatory `<header>` element is missing."""
  missing_seg: PolicyValue[Literal["raise", "ignore", "empty"]] = _default("raise")
  """Action when a `<tuv>` is missing the required `<seg>` element.
  `empty` will default to an empty list instead of None."""
  multiple_seg: PolicyValue[Literal["raise", "keep_first", "keep_last"]] = _default("raise")
  """Action when a `<tuv>` contains more than one `<seg>` element.
  `keep_first` and `keep_last` will keep the first or last seg encountered respectively."""
  empty_content: PolicyValue[Literal["raise", "ignore", "empty"]] = _default("raise")
  """Action when an element has no text content.
  `empty` will fall back to an empty list instead of None."""

  # Serialization items
  missing_serialization_handler: PolicyValue[Literal["raise", "ignore", "default"]] = _default(
    "raise"
  )
  """Action when no handler is registered for a TMX element.
  `default` will attempt fallback to internal library handlers."""
  invalid_attribute_type: PolicyValue[Literal["raise", "ignore", "coerce"]] = _default("raise")
  """Action when a field type is incompatible with XML attribute standards.
  `coerce` will attempt to coerce the field to a correct type."""
  invalid_content_element: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when element text content is not a string."""
  invalid_object_type: PolicyValue[Literal["raise", "ignore"]] = _default("raise")
  """Action when a handler receives an unexpected object type."""
