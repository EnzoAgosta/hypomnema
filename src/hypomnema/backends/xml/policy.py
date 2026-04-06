"""Policy configuration for deserialization and serialization.

This module provides policy-driven error handling for TMX parsing and generation.
Policies allow users to configure how the library responds to various error
conditions (raise exceptions, ignore, use defaults, etc.).

Each policy consists of an action (from an ActionEnum) and an optional log level.
Actions control the behavior, while log levels determine logging verbosity.

Available Actions:
    RAISE: Raise an exception (strictest behavior).
    IGNORE: Silently ignore the error and continue.
    NONE: Use None as the value.
    KEEP: Keep the original value as-is.
    DEFAULT: Use a default value.
    FORCE: Force the operation through.
    OVERWRITE: Overwrite existing values.
    DELETE: Delete the problematic element.

Example:
    >>> from hypomnema.xml.policy import XmlDeserializationPolicy, Behavior, RaiseIgnore
    >>> policy = XmlDeserializationPolicy(
    ...   missing_seg=Behavior(RaiseIgnore.IGNORE), extra_text=Behavior(RaiseIgnore.IGNORE)
    ... )
"""

from dataclasses import dataclass
from enum import Enum, auto
from logging import DEBUG


class ActionEnum:
  """Base class for policy action enums."""

  pass


class RaiseIgnore(ActionEnum, Enum):
  """Actions for raise-or-ignore policies."""

  RAISE = auto()
  """Raise an exception."""

  IGNORE = auto()
  """Silently ignore."""


class RaiseNoneKeep(ActionEnum, Enum):
  """Actions for raise-none-keep policies."""

  RAISE = auto()
  """Raise an exception."""

  NONE = auto()
  """Use None as the value."""

  KEEP = auto()
  """Keep the original string value."""


class RaiseIgnoreDefault(ActionEnum, Enum):
  """Actions for raise-ignore-default policies."""

  RAISE = auto()
  """Raise an exception."""

  IGNORE = auto()
  """Silently ignore."""

  DEFAULT = auto()
  """Use a default value."""


class DuplicateChildAction(ActionEnum, Enum):
  """Actions for handling duplicate child elements."""

  RAISE = auto()
  """Raise an exception."""

  KEEP_FIRST = auto()
  """Use the first occurrence."""

  KEEP_LAST = auto()
  """Use the last occurrence."""


class RaiseIgnoreOverwrite(ActionEnum, Enum):
  """Actions for raise-ignore-overwrite policies."""

  RAISE = auto()
  """Raise an exception."""

  IGNORE = auto()
  """Silently ignore."""

  OVERWRITE = auto()
  """Overwrite the existing value."""


class RaiseIgnoreDelete(ActionEnum, Enum):
  """Actions for raise-ignore-delete policies."""

  RAISE = auto()
  """Raise an exception."""

  IGNORE = auto()
  """Silently ignore."""

  DELETE = auto()
  """Delete the problematic element."""


class RaiseIgnoreForce(ActionEnum, Enum):
  """Actions for raise-ignore-force policies."""

  RAISE = auto()
  """Raise an exception."""

  IGNORE = auto()
  """Silently ignore."""

  FORCE = auto()
  """Force the operation through."""


@dataclass(frozen=True, slots=True)
class Behavior[T: ActionEnum]:
  """Policy behavior configuration.

  Combines an action with an optional log level.

  Example:
      >>> Behavior(RaiseIgnore.RAISE, DEBUG)
      Behavior(action=<RaiseIgnore.RAISE: 1>, log_level=10)
      >>> Behavior(RaiseIgnore.IGNORE)
      Behavior(action=<RaiseIgnore.IGNORE: 2>, log_level=None)
  """

  action: T
  """The action to take (from an ActionEnum)."""

  log_level: int | None = None
  """Logging level for this behavior (None disables logging)."""


@dataclass(slots=True, kw_only=True, frozen=True)
class XmlDeserializationPolicy:
  """Policy configuration for TMX deserialization.

  Controls error handling behavior during XML parsing and object construction.
  """

  invalid_child_tag: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for unexpected child elements."""

  missing_text_content: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for elements missing required text."""

  invalid_tag: Behavior[RaiseIgnoreForce] = Behavior(RaiseIgnoreForce.RAISE, DEBUG)
  """Action for unexpected element tags."""

  extra_text: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for unexpected text content."""

  required_attribute_missing: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for missing required attributes."""

  multiple_seg: Behavior[DuplicateChildAction] = Behavior(DuplicateChildAction.RAISE, DEBUG)
  """Action for multiple <seg> elements in <tuv>."""

  multiple_headers: Behavior[DuplicateChildAction] = Behavior(DuplicateChildAction.RAISE, DEBUG)
  """Action for multiple <header> elements."""

  invalid_datetime_value: Behavior[RaiseNoneKeep] = Behavior(RaiseNoneKeep.RAISE, DEBUG)
  """Action for unparsable datetime values."""

  invalid_enum_value: Behavior[RaiseNoneKeep] = Behavior(RaiseNoneKeep.RAISE, DEBUG)
  """Action for invalid enum values."""

  invalid_int_value: Behavior[RaiseNoneKeep] = Behavior(RaiseNoneKeep.RAISE, DEBUG)
  """Action for unparsable integer values."""

  missing_deserialization_handler: Behavior[RaiseIgnoreDefault] = Behavior(
    RaiseIgnoreDefault.RAISE, DEBUG
  )
  """Action for missing element handlers."""

  missing_seg: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for <tuv> elements without <seg>."""

  multiple_body: Behavior[DuplicateChildAction] = Behavior(DuplicateChildAction.RAISE, DEBUG)
  """Action for multiple <body> elements."""

  missing_header: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for <tmx> elements without <header>."""

  missing_body: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for <tmx> elements without <body>."""


@dataclass(slots=True, kw_only=True, frozen=True)
class XmlSerializationPolicy:
  """Policy configuration for TMX serialization.

  Controls error handling behavior during object-to-XML conversion.
  """

  invalid_element_type: Behavior[RaiseIgnoreForce] = Behavior(RaiseIgnoreForce.RAISE, DEBUG)
  """Action for unexpected object types."""

  missing_text_content: Behavior[RaiseIgnoreDefault] = Behavior(RaiseIgnoreDefault.RAISE, DEBUG)
  """Action for objects missing required text."""

  required_attribute_missing: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for missing required attributes."""

  invalid_child_element: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for invalid child element types."""

  invalid_attribute_type: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action for attributes with wrong types."""

  missing_serialization_handler: Behavior[RaiseIgnoreDefault] = Behavior(
    RaiseIgnoreDefault.RAISE, DEBUG
  )
  """Action for missing element handlers."""


@dataclass(slots=True, kw_only=True, frozen=True)
class NamespacePolicy:
  """Policy configuration for namespace handling.

  Controls behavior when registering or resolving namespace prefixes.
  """

  existing_namespace: Behavior[RaiseIgnoreOverwrite] = Behavior(RaiseIgnoreOverwrite.RAISE, DEBUG)
  """Action when registering an already-existing prefix."""

  inexistent_namespace: Behavior[RaiseIgnore] = Behavior(RaiseIgnore.RAISE, DEBUG)
  """Action when resolving an unregistered prefix."""
