"""XML processing utilities.

Provides namespace handling, encoding normalization, URI validation,
and other XML-related utilities.
"""

from .policy import (
  ActionEnum,
  Behavior,
  DuplicateChildAction,
  NamespacePolicy,
  RaiseIgnore,
  RaiseIgnoreDefault,
  RaiseIgnoreDelete,
  RaiseIgnoreForce,
  RaiseIgnoreOverwrite,
  RaiseNoneKeep,
  XmlDeserializationPolicy,
  XmlSerializationPolicy,
)
from .utils import (
  QNameLike,
  make_usable_path,
  normalize_encoding,
  validate_ncname,
  validate_uri,
  fast_validate_uri,
)
