"""XML backend implementations.

Provides abstract base class and concrete implementations for XML parsing.

Available Backends:
    XmlBackend: Abstract base class for all backends.
    StandardBackend: Implementation using xml.etree.ElementTree (always available).
    LxmlBackend: Implementation using lxml (optional, faster).
"""

from .base import XmlBackend
from .standard import StandardBackend

try:
  from hypomnema.xml.backends.lxml import LxmlBackend  # noqa: F401

# Below lines are excluded from coverage as they are tested
# via a subprocess in test_imports.py

except ImportError as e:  # pragma: no cover
  from warnings import warn  # pragma: no cover

  warn(
    f"lxml not installed, Only StandardBackend will be available. Error: {e}"
  )  # pragma: no cover
  LxmlBackend = None  # type:ignore # pragma: no cover

__all__ = ["XmlBackend", "StandardBackend", "LxmlBackend"]
