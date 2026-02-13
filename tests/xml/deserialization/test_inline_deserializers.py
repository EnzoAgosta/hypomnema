"""Tests for inline element deserializers.

Tests deserialization of TMX inline markup elements:
- BptDeserializer: <bpt> begin paired tags
- EptDeserializer: <ept> end paired tags
- ItDeserializer: <it> isolated tags
- PhDeserializer: <ph> placeholder tags
- HiDeserializer: <hi> highlight elements
- SubDeserializer: <sub> sub-flow elements
"""

from logging import WARNING, getLogger

import pytest

from hypomnema.base.errors import InvalidIntValueError, RequiredAttributeMissingError
from hypomnema.base.types import Assoc, Bpt, Ept, Hi, It, Ph, Pos, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization import (
  BptDeserializer,
  EptDeserializer,
  HiDeserializer,
  ItDeserializer,
  PhDeserializer,
  SubDeserializer,
)
from hypomnema.xml.policy import Behavior, RaiseIgnoreForce, RaiseNoneKeep, XmlDeserializationPolicy


class TestBptDeserializer:
  """Tests for BptDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = BptDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_minimal_bpt(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_minimal")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "1")
    backend.set_text(elem, "code")

    result = handler._deserialize(elem)
    assert isinstance(result, Bpt)
    assert result.i == 1
    assert result.x is None
    assert result.type is None
    assert result.content == ["code"]

  def test_bpt_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_all")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "1")
    backend.set_attribute(elem, "x", "2")
    backend.set_attribute(elem, "type", "bold")
    backend.set_text(elem, "code")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.i == 1
    assert result.x == 2
    assert result.type == "bold"

  def test_bpt_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_sub")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      return Sub(content=[])

    handler._set_emit(mock_emit)
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "1")
    backend.set_text(elem, "before")
    sub = backend.create_element("sub")
    backend.append_child(elem, sub)
    backend.set_tail(sub, "after")

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 3
    assert result.content[0] == "before"
    assert isinstance(result.content[1], Sub)
    assert result.content[2] == "after"

  def test_bpt_missing_i_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_missing_i")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("bpt")

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_bpt_invalid_i_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_invalid_i")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "not-an-int")

    with pytest.raises(InvalidIntValueError):
      handler._deserialize(elem)

  def test_bpt_invalid_i_none_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_bpt_invalid_i_none")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = BptDeserializer(backend, policy, logger)
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "not-an-int")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.i is None
    assert "Invalid attribute" in caplog.text

  def test_bpt_invalid_x_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_invalid_x_none")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = BptDeserializer(backend, policy, logger)
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "1")
    backend.set_attribute(elem, "x", "not-an-int")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.x is None

  def test_bpt_empty_content(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_empty")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "1")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.content == []

  def test_bpt_negative_i(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_negative")
    handler = BptDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("bpt")
    backend.set_attribute(elem, "i", "-1")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.i == -1


class TestEptDeserializer:
  """Tests for EptDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = EptDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_minimal_ept(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_minimal")
    handler = EptDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("ept")
    backend.set_attribute(elem, "i", "1")
    backend.set_text(elem, "code")

    result = handler._deserialize(elem)
    assert isinstance(result, Ept)
    assert result.i == 1
    assert result.content == ["code"]

  def test_ept_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_sub")
    handler = EptDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      return Sub(content=[])

    handler._set_emit(mock_emit)
    elem = backend.create_element("ept")
    backend.set_attribute(elem, "i", "1")
    sub = backend.create_element("sub")
    backend.append_child(elem, sub)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 1
    assert isinstance(result.content[0], Sub)

  def test_ept_missing_i_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_missing_i")
    handler = EptDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("ept")

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_ept_invalid_i_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_invalid_i")
    handler = EptDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("ept")
    backend.set_attribute(elem, "i", "not-an-int")

    with pytest.raises(InvalidIntValueError):
      handler._deserialize(elem)

  def test_ept_empty_content(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_empty")
    handler = EptDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("ept")
    backend.set_attribute(elem, "i", "1")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.content == []


class TestItDeserializer:
  """Tests for ItDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = ItDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_minimal_it(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_minimal")
    handler = ItDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("it")
    backend.set_attribute(elem, "pos", "begin")
    backend.set_text(elem, "code")

    result = handler._deserialize(elem)
    assert isinstance(result, It)
    assert result.pos == Pos.BEGIN
    assert result.x is None
    assert result.type is None
    assert result.content == ["code"]

  def test_it_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_all")
    handler = ItDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("it")
    backend.set_attribute(elem, "pos", "end")
    backend.set_attribute(elem, "x", "2")
    backend.set_attribute(elem, "type", "link")
    backend.set_text(elem, "code")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.pos == Pos.END
    assert result.x == 2
    assert result.type == "link"

  def test_it_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_sub")
    handler = ItDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      return Sub(content=[])

    handler._set_emit(mock_emit)
    elem = backend.create_element("it")
    backend.set_attribute(elem, "pos", "begin")
    sub = backend.create_element("sub")
    backend.append_child(elem, sub)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 1
    assert isinstance(result.content[0], Sub)

  def test_it_missing_pos_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_missing_pos")
    handler = ItDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("it")

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_it_invalid_pos_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_invalid_pos")
    handler = ItDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("it")
    backend.set_attribute(elem, "pos", "invalid")

    with pytest.raises(Exception):
      handler._deserialize(elem)

  def test_it_invalid_x_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_invalid_x")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = ItDeserializer(backend, policy, logger)
    elem = backend.create_element("it")
    backend.set_attribute(elem, "pos", "begin")
    backend.set_attribute(elem, "x", "not-an-int")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.x is None


class TestPhDeserializer:
  """Tests for PhDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = PhDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_minimal_ph(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_minimal")
    handler = PhDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("ph")
    backend.set_text(elem, "placeholder")

    result = handler._deserialize(elem)
    assert isinstance(result, Ph)
    assert result.x is None
    assert result.type is None
    assert result.assoc is None
    assert result.content == ["placeholder"]

  def test_ph_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_all")
    handler = PhDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("ph")
    backend.set_attribute(elem, "x", "1")
    backend.set_attribute(elem, "type", "image")
    backend.set_attribute(elem, "assoc", "p")
    backend.set_text(elem, "placeholder")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.x == 1
    assert result.type == "image"
    assert result.assoc == Assoc.P

  def test_ph_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_sub")
    handler = PhDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      return Sub(content=[])

    handler._set_emit(mock_emit)
    elem = backend.create_element("ph")
    sub = backend.create_element("sub")
    backend.append_child(elem, sub)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 1
    assert isinstance(result.content[0], Sub)

  def test_ph_all_assoc_values(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_assoc")
    handler = PhDeserializer(backend, XmlDeserializationPolicy(), logger)

    for assoc_val, expected in [("p", Assoc.P), ("f", Assoc.F), ("b", Assoc.B)]:
      elem = backend.create_element("ph")
      backend.set_attribute(elem, "assoc", assoc_val)
      result = handler._deserialize(elem)
      assert result is not None
      assert result.assoc == expected

  def test_ph_invalid_assoc_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_invalid_assoc")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = PhDeserializer(backend, policy, logger)
    elem = backend.create_element("ph")
    backend.set_attribute(elem, "assoc", "invalid")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.assoc is None

  def test_ph_invalid_x_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_invalid_x")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = PhDeserializer(backend, policy, logger)
    elem = backend.create_element("ph")
    backend.set_attribute(elem, "x", "not-an-int")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.x is None


class TestHiDeserializer:
  """Tests for HiDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = HiDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_minimal_hi(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_minimal")
    handler = HiDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Bpt(i=1, content=[]))
    elem = backend.create_element("hi")
    backend.set_text(elem, "highlighted text")

    result = handler._deserialize(elem)
    assert isinstance(result, Hi)
    assert result.x is None
    assert result.type is None
    assert result.content == ["highlighted text"]

  def test_hi_with_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_attrs")
    handler = HiDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Bpt(i=1, content=[]))
    elem = backend.create_element("hi")
    backend.set_attribute(elem, "x", "1")
    backend.set_attribute(elem, "type", "term")
    backend.set_text(elem, "text")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.x == 1
    assert result.type == "term"

  def test_hi_with_inline_elements(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_inline")
    handler = HiDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "bpt":
        return Bpt(i=1, content=[])
      elif tag == "ept":
        return Ept(i=1, content=[])
      return None

    handler._set_emit(mock_emit)
    elem = backend.create_element("hi")
    backend.set_text(elem, "before ")
    bpt = backend.create_element("bpt")
    backend.append_child(elem, bpt)
    backend.set_tail(bpt, " ")
    ept = backend.create_element("ept")
    backend.append_child(elem, ept)
    backend.set_tail(ept, " after")

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 5
    assert result.content[0] == "before "
    assert isinstance(result.content[1], Bpt)
    assert result.content[2] == " "
    assert isinstance(result.content[3], Ept)
    assert result.content[4] == " after"

  def test_hi_nested_hi(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_nested")
    handler = HiDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "hi":
        return Hi(content=[])
      return None

    handler._set_emit(mock_emit)
    elem = backend.create_element("hi")
    nested = backend.create_element("hi")
    backend.append_child(elem, nested)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 1
    assert isinstance(result.content[0], Hi)

  def test_hi_invalid_x_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_invalid_x")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = HiDeserializer(backend, policy, logger)
    elem = backend.create_element("hi")
    backend.set_attribute(elem, "x", "not-an-int")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.x is None


class TestSubDeserializer:
  """Tests for SubDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = SubDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_minimal_sub(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_minimal")
    handler = SubDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Bpt(i=1, content=[]))
    elem = backend.create_element("sub")
    backend.set_text(elem, "sub-flow text")

    result = handler._deserialize(elem)
    assert isinstance(result, Sub)
    assert result.type is None
    assert result.datatype is None
    assert result.content == ["sub-flow text"]

  def test_sub_with_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_attrs")
    handler = SubDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Bpt(i=1, content=[]))
    elem = backend.create_element("sub")
    backend.set_attribute(elem, "type", "footnote")
    backend.set_attribute(elem, "datatype", "plaintext")
    backend.set_text(elem, "text")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.type == "footnote"
    assert result.datatype == "plaintext"

  def test_sub_with_inline_elements(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_inline")
    handler = SubDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "bpt":
        return Bpt(i=1, content=[])
      elif tag == "ph":
        return Ph(content=[])
      return None

    handler._set_emit(mock_emit)
    elem = backend.create_element("sub")
    backend.set_text(elem, "text ")
    bpt = backend.create_element("bpt")
    backend.append_child(elem, bpt)
    backend.set_tail(bpt, " more")
    ph = backend.create_element("ph")
    backend.append_child(elem, ph)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.content) == 4
    assert result.content[0] == "text "
    assert isinstance(result.content[1], Bpt)
    assert result.content[2] == " more"
    assert isinstance(result.content[3], Ph)

  def test_sub_nested_sub_not_allowed(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_nested")
    handler = SubDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Sub(content=[]))
    elem = backend.create_element("sub")
    nested = backend.create_element("sub")
    backend.append_child(elem, nested)

    with pytest.raises(Exception):
      handler._deserialize(elem)

  def test_sub_empty_content(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_empty")
    handler = SubDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: Bpt(i=1, content=[]))
    elem = backend.create_element("sub")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.content == []
