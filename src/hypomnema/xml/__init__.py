"""XML processing utilities.

Provides namespace handling, encoding normalization, URI validation,
and other XML-related utilities.
"""

from . import policy, utils, backends, serialization, deserialization

__all__ = ["policy", "utils", "backends", "serialization", "deserialization"]
