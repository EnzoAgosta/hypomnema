"""Tests for BaseElementSerializer shared methods.

Tests the base class functionality that all handlers inherit:
- Logging (_log)
- Emit function injection (_set_emit, emit)
- Error handlers for all policy-driven behaviors
- Attribute setting with type conversion
- Child serialization
- Mixed content serialization
"""

from datetime import UTC, datetime, timedelta, timezone
from logging import INFO, WARNING, getLogger
from typing import cast

import pytest

from hypomnema.base.errors import (
  InvalidAttributeTypeError,
  InvalidChildElementError,
  InvalidElementTypeError,
  InvalidPolicyActionError,
  MissingTextContentError,
  RequiredAttributeMissingError,
)
from hypomnema.base.types import Assoc, Bpt, BptLike, Pos, Prop, Segtype, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import (
  Behavior,
  RaiseIgnore,
  RaiseIgnoreDefault,
  RaiseIgnoreForce,
  XmlSerializationPolicy,
)
from hypomnema.xml.serialization.base import BaseElementSerializer


class MockSerializer(BaseElementSerializer):
  """Mock serializer for testing base class methods."""

  def _serialize(self, obj):
    return None


class TestLog:
  """Tests for _log method."""

  def test_log_with_log_level(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_log")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    behavior = Behavior(RaiseIgnore.RAISE, INFO)

    with caplog.at_level(INFO):
      handler._log(behavior, "Test message %s", "arg1")

    assert "Test message arg1" in caplog.text

  def test_log_without_log_level(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_log_no_level")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    behavior = Behavior(RaiseIgnore.RAISE, None)

    with caplog.at_level(INFO):
      handler._log(behavior, "Test message")

    assert caplog.text == ""


class TestSetEmitAndEmit:
  """Tests for _set_emit and emit methods."""

  def test_emit_returns_result(self, backend: XmlBackend) -> None:
    logger = getLogger("test_emit")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    expected = backend.create_element("test")

    def mock_emit(obj):
      return expected

    handler._set_emit(mock_emit)
    result = handler.emit(Sub(content=[]))
    assert result is expected

  def test_emit_raises_without_set_emit(self, backend: XmlBackend) -> None:
    logger = getLogger("test_emit_raises")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    with pytest.raises(AssertionError, match="emit\\(\\) called before set_emit"):
      handler.emit(Sub(content=[]))


class TestHandleInvalidElementType:
  """Tests for _handle_invalid_element_type method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_type_raise")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    with pytest.raises(InvalidElementTypeError):
      handler._handle_invalid_element_type("wrong", Prop)

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_type_ignore")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_element_type("wrong", Prop)

    assert result is None
    assert "Invalid element type" in caplog.text

  def test_force_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_invalid_type_force")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.FORCE, WARNING))
    handler = MockSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._handle_invalid_element_type("wrong", Prop)

    assert result == "wrong"

  def test_invalid_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action")
    policy = XmlSerializationPolicy(
      invalid_element_type=Behavior(cast(RaiseIgnoreForce, "invalid_action"), WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_element_type("wrong", Prop)


class TestHandleInvalidChildElementType:
  """Tests for _handle_invalid_child_element_type method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_child_type_raise")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    with pytest.raises(InvalidChildElementError):
      handler._handle_invalid_child_element_type(str, Prop)

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_child_type_ignore")
    policy = XmlSerializationPolicy(invalid_child_element=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_invalid_child_element_type(str, Prop)

    assert "Invalid child element" in caplog.text

  def test_invalid_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_child_type_invalid")
    policy = XmlSerializationPolicy(
      invalid_child_element=Behavior(cast(RaiseIgnore, "invalid_action"), WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_child_element_type(str, Prop)


class TestHandleMissingTextContent:
  """Tests for _handle_missing_text_content method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_missing_text_raise")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Prop, Prop(text="placeholder", type="test"))
    obj.text = None  # type: ignore[assignment]

    with pytest.raises(MissingTextContentError):
      handler._handle_missing_text_content(obj)

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_missing_text_ignore")
    policy = XmlSerializationPolicy(
      missing_text_content=Behavior(RaiseIgnoreDefault.IGNORE, WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    obj = cast(Prop, Prop(text="placeholder", type="test"))
    obj.text = None  # type: ignore[assignment]

    with caplog.at_level(WARNING):
      result = handler._handle_missing_text_content(obj)

    assert result is None
    assert "has no text content" in caplog.text

  def test_default_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_missing_text_default")
    policy = XmlSerializationPolicy(
      missing_text_content=Behavior(RaiseIgnoreDefault.DEFAULT, WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    obj = cast(Prop, Prop(text="placeholder", type="test"))
    obj.text = None  # type: ignore[assignment]

    with caplog.at_level(WARNING):
      result = handler._handle_missing_text_content(obj)

    assert result == ""

  def test_invalid_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_child_type_invalid")
    policy = XmlSerializationPolicy(
      missing_text_content=Behavior(cast(RaiseIgnoreDefault, "invalid_action"), WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    prop = Prop(text="placeholder", type="test")
    prop.text = None  # type: ignore[assignment]
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_missing_text_content(prop)


class TestHandleRequiredAttributeMissing:
  """Tests for _handle_required_attribute_missing method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_required_attr_raise")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    with pytest.raises(RequiredAttributeMissingError):
      handler._handle_required_attribute_missing("prop", "type")

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_required_attr_ignore")
    policy = XmlSerializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    handler = MockSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_required_attribute_missing("prop", "type")

    assert "Required attribute" in caplog.text

  def test_invalid_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_child_type_invalid")
    policy = XmlSerializationPolicy(
      required_attribute_missing=Behavior(cast(RaiseIgnore, "invalid_action"), WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    prop = Prop(text="placeholder", type="test")
    prop.text = None  # type: ignore[assignment]
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_required_attribute_missing("prop", "type")


class TestSetAttribute:
  """Tests for _set_attribute method."""

  def test_set_string_attribute(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_string")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    handler._set_attribute(elem, "tuid", "tu-001")
    assert backend.get_attribute(elem, "tuid") == "tu-001"

  def test_set_datetime_attribute(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_datetime")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")
    dt = datetime(2024, 1, 15, 10, 30, 0)

    for attr in ("creationdate", "changedate", "lastusagedate"):
      handler._set_attribute(elem, attr, dt)
      assert backend.get_attribute(elem, attr) == "20240115T103000Z"

  def test_set_datetime_attribute_converts_non_utc_timezone(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_datetime_tz")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")
    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))

    handler._set_attribute(elem, "creationdate", dt)
    assert backend.get_attribute(elem, "creationdate") == "20240115T083000Z"

  def test_set_datetime_attribute_keeps_utc_timezone(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_datetime_utc")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")
    dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

    handler._set_attribute(elem, "creationdate", dt)
    assert backend.get_attribute(elem, "creationdate") == "20240115T103000Z"

  def test_set_int_attribute(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_int")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    for attr in ("i", "x", "usagecount"):
      handler._set_attribute(elem, attr, 42)
      assert backend.get_attribute(elem, attr) == "42"

  def test_set_enum_pos_attribute(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_pos")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    handler._set_attribute(elem, "pos", Pos.BEGIN)
    assert backend.get_attribute(elem, "pos") == "begin"

    handler._set_attribute(elem, "assoc", Assoc.P)
    assert backend.get_attribute(elem, "assoc") == "p"

    handler._set_attribute(elem, "segtype", Segtype.SENTENCE)
    assert backend.get_attribute(elem, "segtype") == "sentence"

  def test_set_none_skips(self, backend: XmlBackend) -> None:
    logger = getLogger("test_set_none")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    handler._set_attribute(elem, "tuid", None)
    assert backend.get_attribute(elem, "tuid") is None

  def test_invalid_datetime_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_datetime")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    for attr in ("creationdate", "changedate", "lastusagedate"):
      with pytest.raises(InvalidAttributeTypeError):
        handler._set_attribute(elem, attr, "not-a-datetime")

  def test_invalid_datetime_ignore(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_datetime")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)
    elem = backend.create_element("test")

    for attr in ("creationdate", "changedate", "lastusagedate"):
      handler._set_attribute(elem, attr, "not-a-datetime")  # type: ignore[arg-type]
      assert backend.get_attribute(elem, attr) is None

  def test_invalid_int_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_int")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    for attr in ("i", "x", "usagecount"):
      with pytest.raises(InvalidAttributeTypeError):
        handler._set_attribute(elem, attr, "not-an-int")  # type: ignore[arg-type]

  def test_invalid_int_ignore(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_int")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)
    elem = backend.create_element("test")

    for attr in ("i", "x", "usagecount"):
      handler._set_attribute(elem, attr, "not-an-int")  # type: ignore[arg-type]
      assert backend.get_attribute(elem, attr) is None

  def test_invalid_enum_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_enum")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    with pytest.raises(InvalidAttributeTypeError):
      handler._set_attribute(elem, "pos", "not-a-pos")

    with pytest.raises(InvalidAttributeTypeError):
      handler._set_attribute(elem, "assoc", "not-a-assoc")

    with pytest.raises(InvalidAttributeTypeError):
      handler._set_attribute(elem, "segtype", "not-a-segtype")

  def test_invalid_enum_ignore(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_enum")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)
    elem = backend.create_element("test")

    for attr in ("pos", "assoc", "segtype"):
      handler._set_attribute(elem, attr, "not-a-pos")  # type: ignore[arg-type]
      assert backend.get_attribute(elem, attr) is None

  def test_invalid_string_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_string")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    with pytest.raises(InvalidAttributeTypeError):
      handler._set_attribute(elem, "tuid", 123)


class TestSetRequiredAttribute:
  """Tests for _set_required_attribute method."""

  def test_sets_value(self, backend: XmlBackend) -> None:
    logger = getLogger("test_req_set")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    handler._set_required_attribute(elem, "type", "category")
    assert backend.get_attribute(elem, "type") == "category"

  def test_none_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_req_none")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    elem = backend.create_element("test")

    with pytest.raises(RequiredAttributeMissingError):
      handler._set_required_attribute(elem, "type", None)


class TestSerializeChildrenInto:
  """Tests for _serialize_children_into method."""

  def test_serializes_children(self, backend: XmlBackend) -> None:
    logger = getLogger("test_children")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(obj):
      return backend.create_element("prop")

    handler._set_emit(mock_emit)
    elem = backend.create_element("header")
    children = [Prop(text="v1", type="t1"), Prop(text="v2", type="t2")]

    handler._serialize_children_into(elem, children, Prop)
    child_elems = list(backend.iter_children(elem))
    assert len(child_elems) == 2

  def test_invalid_child_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_children_invalid")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("test"))
    elem = backend.create_element("header")
    children = [Prop(text="v1", type="t1"), "not-a-prop"]

    with pytest.raises(InvalidChildElementError):
      handler._serialize_children_into(elem, children, Prop)

  def test_invalid_child_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_children_ignore")
    policy = XmlSerializationPolicy(invalid_child_element=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)
    handler._set_emit(lambda o: backend.create_element("test"))
    elem = backend.create_element("header")
    children = [Prop(text="v1", type="t1"), "not-a-prop"]

    handler._serialize_children_into(elem, children, Prop)
    assert len(list(backend.iter_children(elem))) == 1

  def test_emit_returning_none_skips_child(self, backend: XmlBackend) -> None:
    logger = getLogger("test_children_emit_none")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: None)
    elem = backend.create_element("header")

    handler._serialize_children_into(elem, [Prop(text="v1", type="t1")], Prop)
    assert len(list(backend.iter_children(elem))) == 0


class TestSerializeContentInto:
  """Tests for _serialize_content_into method."""

  def test_text_only(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_text")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("bpt"))
    elem = backend.create_element("seg")
    content = ["hello", " ", "world"]

    handler._serialize_content_into(elem, content)
    assert backend.get_text(elem) == "hello world"

  def test_elements_only(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_elem")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(obj):
      return backend.create_element("bpt")

    handler._set_emit(mock_emit)
    elem = backend.create_element("seg")
    content = [Bpt(i=1, content=[]), Bpt(i=2, content=[])]

    handler._serialize_content_into(elem, content, False)
    children = list(backend.iter_children(elem))
    assert len(children) == 2

  def test_mixed_content(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_mixed")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(obj):
      return backend.create_element("bpt")

    handler._set_emit(mock_emit)
    elem = backend.create_element("seg")
    content: list[str | BptLike] = ["before ", Bpt(i=1, content=[]), " after"]

    handler._serialize_content_into(elem, content, False)
    assert backend.get_text(elem) == "before "
    children = list(backend.iter_children(elem))
    assert len(children) == 1
    assert backend.get_tail(children[0]) == " after"

  def test_appends_to_existing_text(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_append")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("bpt"))
    elem = backend.create_element("seg")
    backend.set_text(elem, "existing ")

    handler._serialize_content_into(elem, ["more"])
    assert backend.get_text(elem) == "existing more"

  def test_appends_to_existing_tail(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_tail_append")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(obj):
      return backend.create_element("bpt")

    handler._set_emit(mock_emit)
    elem = backend.create_element("seg")
    bpt = backend.create_element("bpt")
    backend.append_child(elem, bpt)

    content: list[str | BptLike] = [Bpt(i=1, content=[]), "more ", "and more"]
    handler._serialize_content_into(elem, content, False)
    children = list(backend.iter_children(elem))
    assert backend.get_tail(children[-1]) == "more and more"

  def test_invalid_child_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_invalid")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("bpt"))
    elem = backend.create_element("seg")
    content = [Bpt(i=1, content=[]), Sub(content=[])]

    with pytest.raises(InvalidChildElementError):
      handler._serialize_content_into(elem, content)  # type: ignore[arg-type]

  def test_invalid_child_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_invalid_ignore")
    policy = XmlSerializationPolicy(invalid_child_element=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)
    handler._set_emit(lambda o: backend.create_element("bpt"))
    elem = backend.create_element("seg")
    content = [Bpt(i=1, content=[]), Sub(content=[]), "text"]

    handler._serialize_content_into(elem, content)  # type: ignore[arg-type]
    children = list(backend.iter_children(elem))
    assert len(children) == 1

  def test_emit_returning_none_skips_inline_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_emit_none")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: None)
    elem = backend.create_element("seg")

    handler._serialize_content_into(elem, [Bpt(i=1, content=[])], False)
    assert len(list(backend.iter_children(elem))) == 0

  def test_sub_element_rejected_when_sub_only_false(self, backend: XmlBackend) -> None:
    logger = getLogger("test_content_sub_rejected")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("sub"))
    elem = backend.create_element("seg")

    with pytest.raises(InvalidChildElementError):
      handler._serialize_content_into(elem, [Sub(content=[])], False)


class TestHandleInvalidAttributeType:
  """Tests for _handle_invalid_attribute_type method."""

  def test_raise_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_attr_type_raise")
    handler = MockSerializer(backend, XmlSerializationPolicy(), logger)

    with pytest.raises(InvalidAttributeTypeError):
      handler._handle_invalid_attribute_type("wrong", int)

  def test_ignore_action(self, backend: XmlBackend, caplog: pytest.LogCaptureFixture) -> None:
    logger = getLogger("test_attr_type_ignore")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = MockSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      handler._handle_invalid_attribute_type("wrong", int)

    assert "Invalid attribute type" in caplog.text

  def test_invalid_action(self, backend: XmlBackend) -> None:
    logger = getLogger("test_invalid_action")
    policy = XmlSerializationPolicy(
      invalid_attribute_type=Behavior(cast(RaiseIgnore, "invalid_action"), WARNING)
    )
    handler = MockSerializer(backend, policy, logger)
    with pytest.raises(InvalidPolicyActionError):
      handler._handle_invalid_attribute_type("wrong", int)
