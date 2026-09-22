"""Load the trusted package DTD and validate an element subtree."""

from copy import deepcopy
from functools import cache
from importlib.resources import files

from lxml import etree

from ..errors import TmxSpecError


@cache
def load_dtd() -> etree.DTD:
  """Load and cache the trusted TMX 1.4b DTD bundled with the package.

  Returns:
      The shared DTD instance. Its error log reflects its latest validation.

  Raises:
      OSError: The packaged DTD cannot be read.
      etree.DTDParseError: The packaged DTD cannot be parsed.
  """
  resource = files("hypomnema").joinpath("resources", "tmx14.dtd")
  with resource.open("rb") as source:
    return etree.DTD(source)


def validate_fragment(element: etree._Element) -> None:
  """Validate a subtree against the packaged DTD without modifying it.

  Args:
      element: Root of the fragment. Its parent and tail are not validated.

  Raises:
      TmxSpecError: The fragment violates the DTD. The message includes its
          tag, source line, and the underlying validation failure.
  """
  # lxml's synthetic document for a non-root fragment can introduce an
  # xmlns:xml declaration that the DTD then rejects. Give validation an
  # independently owned tree; project the untouched original, not this copy.
  validation_root = element if element.getroottree().getroot() is element else deepcopy(element)
  try:
    load_dtd().assertValid(validation_root)
  except etree.DocumentInvalid as error:
    raise TmxSpecError(f"<{element.tag}> at line {element.sourceline}: {error}") from error
