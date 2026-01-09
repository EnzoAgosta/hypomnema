from warnings import warn

from .base import XmlBackend
from .standard import StandardBackend


try:
  from .lxml import LxmlBackend  # noqa: F401

except ImportError as e:
  warn(f"lxml not installed, Only StandardBackend will be available. Error: {e}")
  LxmlBackend = None  # type: ignore[assignment]

__all__ = ["XmlBackend", "StandardBackend", "LxmlBackend"]
