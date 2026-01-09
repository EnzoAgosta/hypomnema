import logging
from tests.strict_backend import StrictBackend
import pytest
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.backends.lxml import LxmlBackend


@pytest.fixture(
  params=["StandardBackend", "LxmlBackend", "StrictBackend"], ids=["Standard", "Lxml", "Strict"]
)
def backend(request):
  """
  Parametrized fixture that yields a fresh instance of each backend.
  """
  test_logger = logging.getLogger("test")
  match request.param:
    case "StandardBackend":
      yield StandardBackend(logger=test_logger)
    case "LxmlBackend":
      yield LxmlBackend(logger=test_logger)
    case "StrictBackend":
      yield StrictBackend(logger=test_logger)
