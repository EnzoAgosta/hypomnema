import pytest
import logging
from datetime import datetime
from enum import StrEnum
from hypomnema.base.types import Prop, Header
from hypomnema.base.errors import AttributeSerializationError, XmlSerializationError
from hypomnema.xml.serialization.base import BaseElementSerializer
from hypomnema.xml.policy import SerializationPolicy, PolicyValue


class ConcreteSerializer(BaseElementSerializer):
  """A concrete implementation for testing abstract BaseElementSerializer."""

  def _serialize(self, obj):
    return self.backend.create_element("test")


class MockEnum(StrEnum):
  A = "a"
  B = "b"


class BaseSerializerTest:
  @pytest.fixture(autouse=True)
  def setup(self, mocker, backend):
    self.mocker = mocker
    self.backend = backend
    self.policy = SerializationPolicy()
    self.logger = logging.getLogger("test")
    self.serializer = ConcreteSerializer(backend, self.policy, self.logger)

    # Mock emit to return a simple element for children/content tests
    self.serializer._set_emit(lambda x: self.backend.create_element("child"))


class TestBaseSerializerHappy(BaseSerializerTest):
  """Happy path tests for BaseElementSerializer."""

  def test_emit_delegates(self):
    """Test that emit calls the provided callable."""
    mock_emit = self.mocker.Mock(return_value="result")
    self.serializer._set_emit(mock_emit)
    obj = Prop(text="t", type="k")
    assert self.serializer.emit(obj) == "result"
    mock_emit.assert_called_once_with(obj)

  def test_handle_missing_attribute_not_required(self):
    """Test missing optional attribute does nothing."""
    elem = self.backend.create_element("elem")
    self.serializer._handle_missing_attribute(elem, "attr", required=False)

  def test_set_datetime_attribute_valid(self):
    """Test setting a valid datetime attribute."""
    elem = self.backend.create_element("elem")
    dt = datetime(2023, 1, 1, 12, 0, 0)
    self.serializer._set_datetime_attribute(elem, dt, "date", required=True)
    assert self.backend.get_attribute(elem, "date") == dt.isoformat()

  def test_set_datetime_attribute_none_optional(self):
    """Test setting None for optional datetime."""
    elem = self.backend.create_element("elem")
    self.serializer._set_datetime_attribute(elem, None, "date", required=False)
    assert self.backend.get_attribute(elem, "date") is None

  def test_set_int_attribute_valid(self):
    elem = self.backend.create_element("elem")
    self.serializer._set_int_attribute(elem, 42, "count", required=True)
    assert self.backend.get_attribute(elem, "count") == "42"

  def test_set_enum_attribute_valid(self):
    elem = self.backend.create_element("elem")
    self.serializer._set_enum_attribute(elem, MockEnum.A, "type", MockEnum, required=True)
    assert self.backend.get_attribute(elem, "type") == "a"

  def test_set_str_attribute_valid(self):
    elem = self.backend.create_element("elem")
    self.serializer._set_str_attribute(elem, "val", "attr", required=True)
    assert self.backend.get_attribute(elem, "attr") == "val"

  def test_serialize_content_strings_only(self):
    """Test serializing a list of strings."""
    source = self.mocker.Mock()
    source.content = ["Hello", ", ", "World"]
    source.__class__.__name__ = "Source"

    target = self.backend.create_element("target")
    self.serializer._serialize_content_into(source, target, allowed=())

    assert self.backend.get_text(target) == "Hello, World"

  def test_serialize_content_mixed(self):
    """Test serializing mixed strings and elements."""
    source = self.mocker.Mock()
    source.content = ["Hello", Prop(text="p", type="t"), "World"]
    source.__class__.__name__ = "Source"

    target = self.backend.create_element("target")

    self.serializer._set_emit(lambda x: self.backend.create_element("prop"))
    self.serializer._serialize_content_into(source, target, allowed=(Prop,))

    children = list(self.backend.iter_children(target))
    assert len(children) == 1
    assert self.backend.get_tag(children[0]) == "prop"
    assert self.backend.get_text(target) == "Hello"
    assert self.backend.get_tail(children[0]) == "World"

  def test_serialize_children_valid(self):
    children = [Prop(text="p1", type="t"), Prop(text="p2", type="t")]
    target = self.backend.create_element("target")

    self.serializer._set_emit(lambda x: self.backend.create_element("prop"))
    self.serializer._serialize_children(children, target, Prop)

    assert len(list(self.backend.iter_children(target))) == 2

  def test_serialize_children_emit_returns_none(self):
    """Test that if emit returns None, nothing is appended."""
    children = [Prop(text="p1", type="t")]
    target = self.backend.create_element("target")

    self.serializer._set_emit(lambda x: None)
    self.serializer._serialize_children(children, target, Prop)

    assert len(list(self.backend.iter_children(target))) == 0


class TestBaseSerializerError(BaseSerializerTest):
  """Error cases for BaseElementSerializer."""

  def test_emit_raises_if_not_set(self):
    """Test that emit raises AssertionError if _set_emit wasn't called."""
    fresh_serializer = ConcreteSerializer(self.backend, self.policy, self.logger)
    with pytest.raises(AssertionError, match=r"emit\(\) called before set_emit\(\)"):
      fresh_serializer.emit(Prop(text="t", type="k"))

  def test_handle_missing_attribute_required_raise(self):
    """Test missing required attribute raises error by default."""
    elem = self.backend.create_element("elem")
    with pytest.raises(AttributeSerializationError, match="Required attribute 'attr' is missing"):
      self.serializer._handle_missing_attribute(elem, "attr", required=True)

  def test_handle_missing_attribute_required_ignore(self):
    """Test missing required attribute is ignored if policy says so."""
    self.policy.required_attribute_missing = PolicyValue("ignore", logging.DEBUG)
    elem = self.backend.create_element("elem")
    # Should not raise
    self.serializer._handle_missing_attribute(elem, "attr", required=True)

  def test_set_datetime_attribute_none_required(self):
    """Test setting None for required datetime."""
    elem = self.backend.create_element("elem")
    with pytest.raises(AttributeSerializationError):
      self.serializer._set_datetime_attribute(elem, None, "date", required=True)

  def test_set_datetime_attribute_invalid_type_raise(self):
    """Test setting invalid type for datetime raises."""
    elem = self.backend.create_element("elem")
    with pytest.raises(AttributeSerializationError, match="not a datetime object"):
      self.serializer._set_datetime_attribute(elem, "not-a-date", "date", required=True)

  def test_set_datetime_attribute_invalid_type_ignore(self):
    """Test setting invalid type for datetime ignored."""
    self.policy.invalid_attribute_type = PolicyValue("ignore", logging.DEBUG)
    elem = self.backend.create_element("elem")
    self.serializer._set_datetime_attribute(elem, "not-a-date", "date", required=True)
    assert self.backend.get_attribute(elem, "date") is None

  def test_set_int_attribute_invalid_type(self):
    elem = self.backend.create_element("elem")
    with pytest.raises(AttributeSerializationError, match="not an int"):
      self.serializer._set_int_attribute(elem, "42", "count", required=True)

  def test_set_enum_attribute_invalid_member(self):
    elem = self.backend.create_element("elem")
    with pytest.raises(AttributeSerializationError, match="not a member of"):
      self.serializer._set_enum_attribute(elem, "c", "type", MockEnum, required=True)

  def test_set_str_attribute_invalid_type(self):
    elem = self.backend.create_element("elem")
    with pytest.raises(AttributeSerializationError, match="not a string"):
      self.serializer._set_str_attribute(elem, 123, "attr", required=True)

  def test_serialize_content_invalid_child(self):
    """Test serialization of disallowed child type."""
    source = self.mocker.Mock()
    source.content = [Prop(text="p", type="t")]
    source.__class__.__name__ = "Source"

    target = self.backend.create_element("target")

    with pytest.raises(XmlSerializationError, match="Incorrect child element"):
      self.serializer._serialize_content_into(source, target, allowed=(Header,))

  def test_serialize_content_invalid_child_ignore(self):
    """Test ignoring disallowed child type."""
    self.policy.invalid_content_type = PolicyValue("ignore", logging.DEBUG)

    source = self.mocker.Mock()
    source.content = [Prop(text="p", type="t")]
    source.__class__.__name__ = "Source"

    target = self.backend.create_element("target")
    self.serializer._serialize_content_into(source, target, allowed=(Header,))

    assert len(list(self.backend.iter_children(target))) == 0

  def test_serialize_children_invalid_type(self):
    children = [Prop(text="p1", type="t")]
    target = self.backend.create_element("target")

    with pytest.raises(XmlSerializationError, match="Invalid child element"):
      self.serializer._serialize_children(children, target, MockEnum)
