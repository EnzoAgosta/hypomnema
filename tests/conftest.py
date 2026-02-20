import pytest

from hypomnema.xml.backends import LxmlBackend, StandardBackend


@pytest.fixture(params=[StandardBackend, LxmlBackend])
def backend(request: pytest.FixtureRequest) -> StandardBackend | LxmlBackend:
  """Returns both StandardBackend and LxmlBackend for every test.

  This fixture parametrizes all tests to run against both backend
  implementations, ensuring backend equivalence.
  """
  return request.param()
