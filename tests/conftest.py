import logging
import xml.etree.ElementTree as std_et
from collections.abc import Generator, Iterable

import lxml.etree as lxml_et
import pytest

from hypomnema import Deserializer, Serializer, XmlBackend, XmlPolicy
from hypomnema.xml.backends.lxml import LxmlBackend
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.qname import QNameLike
from tests.strict_backend import StrictBackend

TypeOfBackend = StandardBackend | LxmlBackend | StrictBackend


@pytest.fixture(
  params=["StandardBackend", "LxmlBackend", "StrictBackend"], ids=["Standard", "Lxml", "Strict"]
)
def backend(request, test_logger):
  """
  Parametrized fixture that yields a fresh instance of each backend.
  """
  match request.param:
    case "StandardBackend":
      yield StandardBackend(logger=test_logger)
    case "LxmlBackend":
      yield LxmlBackend(logger=test_logger)
    case "StrictBackend":
      yield StrictBackend(logger=test_logger)


@pytest.fixture(scope="session")
def test_logger():
  """Test logger."""
  test_logger = logging.getLogger("test")
  test_logger.setLevel(1)
  return test_logger
