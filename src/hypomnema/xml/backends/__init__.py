from warnings import warn

from .base import XmlBackend
from .standard import StandardBackend

__all__ = ["XmlBackend", "StandardBackend"]

try:
  from .lxml import LxmlBackend  # noqa: F401

  __all__.append("LxmlBackend")
except ImportError:
  warn("lxml not installed, Only StandardBackend will be available")
