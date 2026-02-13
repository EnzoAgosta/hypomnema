"""Tests for BaseElementDeserializer shared methods.

Tests the base class functionality that all handlers inherit:
- Logging (_log)
- Emit function injection (_set_emit, emit)
- Attribute parsing (_parse_required_attribute)
- Type conversion (try_convert_to_datetime, try_convert_to_int, try_convert_to_enum)
- Mixed content deserialization (_deserialize_content)
- Error handlers for all policy-driven behaviors
"""

from datetime import datetime, timezone
from enum import StrEnum
from logging import INFO, WARNING, getLogger

import pytest

from hypomnema.base.errors import (
  ExtraTextError,
  InvalidChildTagError,
  InvalidDatetimeValueError,
  InvalidEnumValueError,
  InvalidIntValueError,
  InvalidPolicyActionError,
  InvalidTagError,
  MissingTextContentError,
  RequiredAttributeMissingError,
)
from hypomnema.base.types import Bpt, Ept, Hi, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization.base import BaseElementDeserializer
from hypomnema.xml.policy import (
  Behavior,
  RaiseIgnore,
  RaiseIgnoreForce,
  RaiseNoneKeep,
  XmlDeserializationPolicy,
)


class MockEnum(StrEnum):
  VALUE_A = "value_a"
  VALUE_B = "value_b"


class MockDeserializer(BaseElementDeserializer):
  """Mock deserializer for testing base class methods."""

  def _deserialize(self, element):
    return None


class TestLog:
  """Tests for _log method."""

  def test_log_with_log_level(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_log")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)
    behavior = Behavior(RaiseIgnore.RAISE, INFO)

    with caplog.at_level(INFO):
      handler._log(behavior, "Test message %s", "arg1")

    assert "Test message arg1" in caplog.text

  def test_log_without_log_level(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_log_no_level")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)
    behavior = Behavior(RaiseIgnore.RAISE, None)

    with caplog.at_level(INFO):
      handler._log(behavior, "Test message")

    assert caplog.text == ""


class TestSetEmitAndEmit:
  """Tests for _set_emit and emit methods."""

  def test_emit_returns_result(self, backend: XmlBackend) -> None:
    logger = getLogger("test_emit")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)
    expected = Sub(content=[])

    def mock_emit(element):
      return expected

    handler._set_emit(mock_emit)
    result = handler.emit(backend.create_element("test"))
    assert result is expected

  def test_emit_raises_without_set_emit(self, backend: XmlBackend) -> None:
    logger = getLogger("test_emit_raises")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(AssertionError, match="emit\\(\\) called before set_emit"):
      handler.emit(backend.create_element("test"))


class TestParseRequiredAttribute:
  """Tests for _parse_required_attribute method."""

  def test_returns_value_when_present(self, backend: XmlBackend) -> None:
    logger = getLogger("test_parse_required")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("test", attributes={"attr": "value"})

    result = handler._parse_required_attribute(elem, "attr")
    assert result == "value"

  def test_raises_when_missing(self, backend: XmlBackend) -> None:
    logger = getLogger("test_parse_required_missing")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("test")

    with pytest.raises(RequiredAttributeMissingError):
      handler._parse_required_attribute(elem, "attr")

  def test_returns_none_when_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_parse_required_ignore")
    policy = XmlDeserializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    handler = MockDeserializer(backend, policy, logger)
    elem = backend.create_element("test")

    with caplog.at_level(WARNING):
      result = handler._parse_required_attribute(elem, "attr")

    assert result is None
    assert "Required attribute" in caplog.text


class TestTryConvertToDatetime:
  """Tests for try_convert_to_datetime method."""

  def test_valid_datetime(self, backend: XmlBackend) -> None:
    logger = getLogger("test_datetime")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    result = handler.try_convert_to_datetime("test", "2024-01-15T10:30:00", "attr")
    assert result == datetime(2024, 1, 15, 10, 30, 0)

  def test_valid_datetime_with_z_suffix(self, backend: XmlBackend) -> None:
    logger = getLogger("test_datetime_z")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    result = handler.try_convert_to_datetime("test", "2024-01-15T10:30:00Z", "attr")
    assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

  def test_invalid_datetime_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_datetime_invalid")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidDatetimeValueError):
      handler.try_convert_to_datetime("test", "not-a-date", "attr")

  def test_invalid_datetime_returns_none_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_datetime_none")
    policy = XmlDeserializationPolicy(invalid_datetime_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler.try_convert_to_datetime("test", "not-a-date", "attr")

    assert result is None
    assert "Invalid attribute" in caplog.text

  def test_invalid_datetime_keeps_value_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_datetime_keep")
    policy = XmlDeserializationPolicy(invalid_datetime_value=Behavior(RaiseNoneKeep.KEEP, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler.try_convert_to_datetime("test", "not-a-date", "attr")

    assert result == "not-a-date"


class TestTryConvertToInt:
  """Tests for try_convert_to_int method."""

  def test_valid_int(self, backend: XmlBackend) -> None:
    logger = getLogger("test_int")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    result = handler.try_convert_to_int("test", "42", "attr")
    assert result == 42

  def test_negative_int(self, backend: XmlBackend) -> None:
    logger = getLogger("test_int_neg")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    result = handler.try_convert_to_int("test", "-10", "attr")
    assert result == -10

  def test_invalid_int_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_int_invalid")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidIntValueError):
      handler.try_convert_to_int("test", "not-an-int", "attr")

  def test_invalid_int_returns_none_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_int_none")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler.try_convert_to_int("test", "not-an-int", "attr")

    assert result is None
    assert "Invalid attribute" in caplog.text

  def test_invalid_int_keeps_value_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_int_keep")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.KEEP, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler.try_convert_to_int("test", "not-an-int", "attr")

    assert result == "not-an-int"


class TestTryConvertToEnum:
  """Tests for try_convert_to_enum method."""

  def test_valid_enum_value(self, backend: XmlBackend) -> None:
    logger = getLogger("test_enum")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    result = handler.try_convert_to_enum("test", "value_a", "attr", MockEnum)
    assert result == MockEnum.VALUE_A

  def test_invalid_enum_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_enum_invalid")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidEnumValueError):
      handler.try_convert_to_enum("test", "invalid_value", "attr", MockEnum)

  def test_invalid_enum_returns_none_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_enum_none")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler.try_convert_to_enum("test", "invalid_value", "attr", MockEnum)

    assert result is None
    assert "Invalid attribute" in caplog.text

  def test_invalid_enum_keeps_value_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_enum_keep")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.KEEP, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler.try_convert_to_enum("test", "invalid_value", "attr", MockEnum)

    assert result == "invalid_value"


class TestDeserializeContent:
  """Tests for _deserialize_content method."""

  def test_text_only(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_text")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("test")
    backend.set_text(elem, "text content")

    result = handler._deserialize_content(elem, ("sub",))
    assert result == ["text content"]

  def test_element_only(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_elem")
    policy = XmlDeserializationPolicy()
    handler = MockDeserializer(backend, policy, logger)

    def mock_emit(element):
      return Sub(content=[])

    handler._set_emit(mock_emit)

    elem = backend.create_element("test")
    child = backend.create_element("sub")
    backend.append_child(elem, child)

    result = handler._deserialize_content(elem, ("sub",))
    assert len(result) == 1
    assert isinstance(result[0], Sub)

  def test_mixed_content(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_mixed")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(element):
      return Sub(content=[])

    handler._set_emit(mock_emit)

    elem = backend.create_element("test")
    backend.set_text(elem, "before ")
    child = backend.create_element("sub")
    backend.append_child(elem, child)
    backend.set_tail(child, " after")

    result = handler._deserialize_content(elem, ("sub",))
    assert result == ["before ", Sub(content=[]), " after"]

  def test_invalid_child_tag_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_invalid")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(element):
      return Sub(content=[])

    handler._set_emit(mock_emit)

    elem = backend.create_element("test")
    child = backend.create_element("invalid")
    backend.append_child(elem, child)

    with pytest.raises(InvalidChildTagError):
      handler._deserialize_content(elem, ("sub",))

  def test_invalid_child_tag_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_content_invalid_ignore")
    policy = XmlDeserializationPolicy(invalid_child_tag=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    def mock_emit(element):
      return Sub(content=[])

    handler._set_emit(mock_emit)

    elem = backend.create_element("test")
    child = backend.create_element("invalid")
    backend.append_child(elem, child)

    with caplog.at_level(WARNING):
      result = handler._deserialize_content(elem, ("sub",))

    assert result == []
    assert "Invalid child tag" in caplog.text

  def test_emit_returns_none_skipped(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_none")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(element):
      return None

    handler._set_emit(mock_emit)

    elem = backend.create_element("test")
    child = backend.create_element("sub")
    backend.append_child(elem, child)

    result = handler._deserialize_content(elem, ("sub",))
    assert result == []

  def test_inline_tags_allowed(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_inline")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    emitted = []

    def mock_emit(element):
      tag = backend.get_tag(element)
      emitted.append(tag)
      if tag == "bpt":
        return Bpt(i=1, content=[])
      elif tag == "ept":
        return Ept(i=1, content=[])
      elif tag == "hi":
        return Hi(content=[])
      return None

    handler._set_emit(mock_emit)

    elem = backend.create_element("test")
    backend.append_child(elem, backend.create_element("bpt"))
    backend.append_child(elem, backend.create_element("ept"))
    backend.append_child(elem, backend.create_element("hi"))

    result = handler._deserialize_content(elem, ("bpt", "ept", "it", "ph", "hi"))
    assert len(result) == 3
    assert isinstance(result[0], Bpt)
    assert isinstance(result[1], Ept)
    assert isinstance(result[2], Hi)


class TestHandleInvalidTag:
  """Tests for _handle_invalid_tag method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_tag_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidTagError):
      handler._handle_invalid_tag("wrong", "expected")

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_tag_ignore")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_tag("wrong", "expected")

    assert result is None
    assert "Invalid tag" in caplog.text

  def test_force_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_tag_force")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.FORCE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_tag("wrong", "expected")

    assert result == "wrong"

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_tag("wrong", "expected")


class TestHandleInvalidChildTag:
  """Tests for _handle_invalid_child_tag method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_child_tag_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidChildTagError):
      handler._handle_invalid_child_tag("parent", "wrong", ("expected",))

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_child_tag_ignore")
    policy = XmlDeserializationPolicy(invalid_child_tag=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_invalid_child_tag("parent", "wrong", ("expected",))

    assert "Invalid child tag" in caplog.text

  def test_expected_as_tuple(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_child_tag_tuple")
    policy = XmlDeserializationPolicy(invalid_child_tag=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_invalid_child_tag("parent", "wrong", ("a", "b", "c"))

    assert "Invalid child tag" in caplog.text

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(invalid_child_tag=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_child_tag("parent", "wrong", ("a", "b", "c"))


class TestHandleMissingTextContent:
  """Tests for _handle_missing_text_content method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_missing_text_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(MissingTextContentError):
      handler._handle_missing_text_content("note")

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_missing_text_ignore")
    policy = XmlDeserializationPolicy(missing_text_content=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_missing_text_content("note")

    assert result is None
    assert "has no text content" in caplog.text

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(missing_text_content=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_missing_text_content("note")


class TestHandleExtraText:
  """Tests for _handle_extra_text method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_extra_text_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(ExtraTextError):
      handler._handle_extra_text("tmx", "extra text")

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_extra_text_ignore")
    policy = XmlDeserializationPolicy(extra_text=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_extra_text("tmx", "extra text")

    assert "extra text content" in caplog.text

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(extra_text=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_extra_text("tmx", "extra text")


class TestHandleRequiredAttributeMissing:
  """Tests for _handle_required_attribute_missing method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_required_attr_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(RequiredAttributeMissingError):
      handler._handle_required_attribute_missing("tu", "tuid")

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_required_attr_ignore")
    policy = XmlDeserializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_required_attribute_missing("tu", "tuid")

    assert "Required attribute" in caplog.text

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(
      required_attribute_missing=Behavior("invalid_action", WARNING)  # type: ignore
    )
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_required_attribute_missing("tu", "tuid")


class TestHandleInvalidEnumValue:
  """Tests for _handle_invalid_enum_value method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_enum_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidEnumValueError):
      handler._handle_invalid_enum_value("test", "attr", "invalid", MockEnum)

  def test_none_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_enum_none")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_enum_value("test", "attr", "invalid", MockEnum)

    assert result is None
    assert "Invalid attribute" in caplog.text

  def test_keep_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_enum_keep")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.KEEP, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_enum_value("test", "attr", "invalid", MockEnum)

    assert result == "invalid"

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_enum_value("test", "attr", "invalid", MockEnum)


class TestHandleInvalidDatetimeValue:
  """Tests for _handle_invalid_datetime_value method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_datetime_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidDatetimeValueError):
      handler._handle_invalid_datetime_value("test", "attr", "not-a-date", datetime)

  def test_none_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_datetime_none")
    policy = XmlDeserializationPolicy(invalid_datetime_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_datetime_value("test", "attr", "not-a-date", datetime)

    assert result is None
    assert "Invalid attribute" in caplog.text

  def test_keep_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_datetime_keep")
    policy = XmlDeserializationPolicy(invalid_datetime_value=Behavior(RaiseNoneKeep.KEEP, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_datetime_value("test", "attr", "not-a-date", datetime)

    assert result == "not-a-date"

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(invalid_datetime_value=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_datetime_value("test", "attr", "not-a-date", datetime)


class TestHandleInvalidIntValue:
  """Tests for _handle_invalid_int_value method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_int_raise")
    handler = MockDeserializer(backend, XmlDeserializationPolicy(), logger)

    with pytest.raises(InvalidIntValueError):
      handler._handle_invalid_int_value("test", "attr", "not-an-int", int)

  def test_none_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_int_none")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_int_value("test", "attr", "not-an-int", int)

    assert result is None
    assert "Invalid attribute" in caplog.text

  def test_keep_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_int_keep")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.KEEP, WARNING))
    handler = MockDeserializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_int_value("test", "attr", "not-an-int", int)

    assert result == "not-an-int"

  def test_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action_raise")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior("invalid_action", WARNING))  # type: ignore
    handler = MockDeserializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_int_value("test", "attr", "not-an-int", int)
