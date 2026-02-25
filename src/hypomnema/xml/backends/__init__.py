"""XML backend implementations.

Provides abstract base class and concrete implementations for XML parsing.

Available Backends:
    XmlBackend: Abstract base class for all backends.
    StandardBackend: Implementation using xml.etree.ElementTree (always available).
    LxmlBackend: Implementation using lxml (optional, faster).
"""

from warnings import warn
from .base import XmlBackend, NamespaceHandler
from .standard import StandardBackend

try:
  from hypomnema.xml.backends.lxml import LxmlBackend

except ImportError:
  warn("lxml not installed, only StandardBackend will be available", stacklevel=2)
  LxmlBackend = None  # type:ignore

__all__ = ["XmlBackend", "StandardBackend", "LxmlBackend", "NamespaceHandler"]
