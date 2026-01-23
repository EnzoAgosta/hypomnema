from warnings import warn

from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.backends.standard import StandardBackend

try:
  from hypomnema.xml.backends.lxml import LxmlBackend  # noqa: F401

except ImportError as e:
  warn(f"lxml not installed, Only StandardBackend will be available. Error: {e}")
  LxmlBackend = None  # type:ignore

__all__ = ["XmlBackend", "StandardBackend", "LxmlBackend"]
