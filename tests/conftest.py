import logging
from tests.strict_backend import StrictBackend
import pytest
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.backends.lxml import LxmlBackend


@pytest.fixture(
<<<<<<< HEAD
  params=["StandardBackend", "LxmlBackend", "StrictBackend"], ids=["Standard", "Lxml", "Strict"]
)
def backend(request, test_logger):
  """
  Parametrized fixture that yields a fresh instance of each backend.
  """
=======
  # params=[StandardBackend, LxmlBackend], ids=["Standard", "Lxml"]
  params=["StandardBackend", "LxmlBackend", "StrictBackend"],
  ids=["Standard", "Lxml", "Strict"],
)
def backend(request):
  """
  Parametrized fixture that yields a fresh instance of each backend.
  """
  test_logger = logging.getLogger("test")
  test_logger.setLevel(1)
>>>>>>> 7c25f28 (Add test infrastructure with StrictBackend for XML backend testing (#42))
  match request.param:
    case "StandardBackend":
      yield StandardBackend(logger=test_logger)
    case "LxmlBackend":
      yield LxmlBackend(logger=test_logger)
    case "StrictBackend":
<<<<<<< HEAD
      yield StrictBackend(logger=test_logger)


@pytest.fixture(scope="session")
def test_logger():
  """Test logger."""
  test_logger = logging.getLogger("test")
  test_logger.setLevel(1)
  return test_logger
=======
      yield StrictBackend(logger=test_logger)
>>>>>>> 7c25f28 (Add test infrastructure with StrictBackend for XML backend testing (#42))
