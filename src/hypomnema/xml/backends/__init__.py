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

except ImportError as e:
  from warnings import warn

  warn(f"lxml not installed, Only StandardBackend will be available. Error: {e}")
  LxmlBackend = None  # type:ignore

__all__ = ["XmlBackend", "StandardBackend", "LxmlBackend"]
