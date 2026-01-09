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
    # We simulate a case where the handler was not in the initial map
    # but exists in default handlers.
    # Initialize serializer with empty handlers map
    serializer = Serializer(self.backend, handlers={})
    serializer.policy.missing_handler = PolicyValue("default", logging.DEBUG)

    prop = Prop(text="val", type="key")
    # Should fall back to default handler for Prop
    elem = serializer.serialize(prop)
    assert elem is not None
    assert self.backend.get_tag(elem) == "prop"

  def test_custom_handler(self):
    # Define a mock handler
    mock_handler = self.mocker.Mock()
    mock_handler._emit = None  # emulate BaseElementSerializer
    mock_handler._set_emit = self.mocker.Mock()

    # We need _serialize to return something valid for the backend
    # But since we mock everything, we can just return "mock_element"
    mock_handler._serialize.return_value = "mock_element"

    handlers = {UnknownType: mock_handler}
    serializer = Serializer(self.backend, handlers=handlers)  # type: ignore

    obj = UnknownType()
    result = serializer.serialize(obj)  # type: ignore

    assert result == "mock_element"
    mock_handler._serialize.assert_called_once_with(obj)

  def test_serialize_unknown_type_ignore(self):
    obj = UnknownType()
    self.serializer.policy.missing_handler = PolicyValue("ignore", logging.DEBUG)

    result = self.serializer.serialize(obj)  # type: ignore
    assert result is None


class TestSerializerError(BaseSerializerTest):
  def test_serialize_unknown_type_raise(self):
    obj = UnknownType()
    # Default policy is raise
    with pytest.raises(MissingHandlerError, match="Missing handler"):
      self.serializer.serialize(obj)  # type: ignore

  def test_serialize_unknown_type_default_fallback_fail(self):
    # Fallback requested but type is truly unknown
    self.serializer.policy.missing_handler = PolicyValue("default", logging.DEBUG)
    obj = UnknownType()
    with pytest.raises(MissingHandlerError, match="Missing handler"):
      self.serializer.serialize(obj)  # type: ignore
