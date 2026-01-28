import pytest
from hypothesis import given

from hypomnema.base.types import Tmx
from hypomnema.xml.backends.lxml import LxmlBackend
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.serialization.serializer import Serializer
from tests.hypothesis.strategies import tmx
from tests.strict_backend import StrictBackend


@pytest.fixture(
  scope="session",
  params=["StandardBackend", "LxmlBackend", "StrictBackend"],
  ids=["Standard", "Lxml", "Strict"],
)
def backend(request):
  match request.param:
    case "StandardBackend":
      yield StandardBackend()
    case "LxmlBackend":
      yield LxmlBackend()
    case "StrictBackend":
      yield StrictBackend()


@pytest.fixture(scope="session")
def serializer(backend):
  return Serializer(backend)


@pytest.fixture(scope="session")
def deserializer(backend):
  return Deserializer(backend)


@pytest.mark.hypothesis
@given(tmx())
def test_hypothesis_roundtrip_tmx(serializer: Serializer, deserializer: Deserializer, tmx: Tmx):
  element = serializer.serialize(tmx)
  assert element is not None
  result = deserializer.deserialize(element)
  assert isinstance(result, Tmx)

  assert result == tmx
