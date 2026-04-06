import pytest

from hypomnema.backends.xml.lxml import LxmlBackend
from hypomnema.backends.xml.standard import StandardBackend


@pytest.fixture(params=[StandardBackend, LxmlBackend])
def backend(request: pytest.FixtureRequest) -> StandardBackend | LxmlBackend:
  """Returns both StandardBackend and LxmlBackend for every test.

  This fixture parametrizes all tests to run against both backend
  implementations, ensuring backend equivalence.
  """
  return request.param()
