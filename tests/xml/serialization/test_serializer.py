import pytest
import logging
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.xml.policy import SerializationPolicy, PolicyValue
from hypomnema.base.errors import MissingHandlerError
from hypomnema.base.types import Prop


class UnknownType:
  pass


class BaseSerializerTest:
  @pytest.fixture(autouse=True)
  def setup(self, mocker, backend):
    self.mocker = mocker
    self.backend = backend
    self.serializer = Serializer(backend, policy=SerializationPolicy())


class TestSerializerHappy(BaseSerializerTest):
  def test_serialize_unknown_type_default_fallback_success(self):
    serializer = Serializer(self.backend, handlers={})
    serializer.policy.missing_handler = PolicyValue("default", logging.DEBUG)

    prop = Prop(text="val", type="key")

    elem = serializer.serialize(prop)
    assert elem is not None
    assert self.backend.get_tag(elem) == "prop"

  def test_custom_handler(self):
    mock_handler = self.mocker.Mock()
    mock_handler._emit = None
    mock_handler._set_emit = self.mocker.Mock()

    mock_handler._serialize.return_value = "mock_element"

    handlers = {UnknownType: mock_handler}
    serializer = Serializer(self.backend, handlers=handlers)

    obj = UnknownType()
    result = serializer.serialize(obj)

    assert result == "mock_element"
    mock_handler._serialize.assert_called_once_with(obj)

  def test_serialize_unknown_type_ignore(self):
    obj = UnknownType()
    self.serializer.policy.missing_handler = PolicyValue("ignore", logging.DEBUG)

    result = self.serializer.serialize(obj)
    assert result is None


class TestSerializerError(BaseSerializerTest):
  def test_serialize_unknown_type_raise(self):
    obj = UnknownType()

    with pytest.raises(MissingHandlerError, match="Missing handler"):
      self.serializer.serialize(obj)

  def test_serialize_unknown_type_default_fallback_fail(self):
    self.serializer.policy.missing_handler = PolicyValue("default", logging.DEBUG)
    obj = UnknownType()
    with pytest.raises(MissingHandlerError, match="Missing handler"):
      self.serializer.serialize(obj)
