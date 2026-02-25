"""Tests for inline element serializers.

Tests serialization of TMX inline markup elements:
- BptSerializer: Bpt dataclasses
- EptSerializer: Ept dataclasses
- ItSerializer: It dataclasses
- PhSerializer: Ph dataclasses
- HiSerializer: Hi dataclasses
- SubSerializer: Sub dataclasses
"""

from logging import WARNING, getLogger
from typing import cast

import pytest

from hypomnema.base.errors import InvalidAttributeTypeError, RequiredAttributeMissingError
from hypomnema.base.types import Assoc, Bpt, Ept, Hi, It, Ph, Pos, Prop, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import Behavior, RaiseIgnore, RaiseIgnoreForce, XmlSerializationPolicy
from hypomnema.xml.serialization import (
  BptSerializer,
  EptSerializer,
  HiSerializer,
  ItSerializer,
  PhSerializer,
  SubSerializer,
)


class TestBptSerializer:
  """Tests for BptSerializer."""

  def test_minimal_bpt(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_minimal")
    handler = BptSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Bpt(i=1, content=["code"])

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "bpt"
    assert backend.get_attribute(result, "i") == "1"
    assert backend.get_text(result) == "code"

  def test_bpt_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_all")
    handler = BptSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Bpt(i=1, x=2, type="bold", content=["code"])

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "i") == "1"
    assert backend.get_attribute(result, "x") == "2"
    assert backend.get_attribute(result, "type") == "bold"

  def test_bpt_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_sub")
    handler = BptSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      return backend.create_element("sub")

    handler._set_emit(mock_emit)
    obj = Bpt(i=1, content=["before ", Sub(content=["subflow"]), " after"])

    result = handler._serialize(obj)
    assert backend.get_text(result) == "before "
    children = list(backend.iter_children(result))
    assert len(children) == 1
    assert backend.get_tail(children[0]) == " after"

  def test_bpt_missing_i_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_missing_i")
    handler = BptSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Bpt, Bpt(i=1, content=[]))
    obj.i = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_bpt_invalid_i_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_bpt_invalid_i")
    handler = BptSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Bpt, Bpt(i=1, content=[]))
    obj.i = "not-an-int"  # type: ignore[assignment]

    with pytest.raises(InvalidAttributeTypeError):
      handler._serialize(obj)

  def test_bpt_wrong_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_bpt_wrong_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = BptSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._serialize(Ept(i=1, content=[]))  # type: ignore[arg-type]

    assert result is None


class TestEptSerializer:
  """Tests for EptSerializer."""

  def test_minimal_ept(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_minimal")
    handler = EptSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Ept(i=1, content=["code"])

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "ept"
    assert backend.get_attribute(result, "i") == "1"
    assert backend.get_text(result) == "code"

  def test_ept_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_sub")
    handler = EptSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      return backend.create_element("sub")

    handler._set_emit(mock_emit)
    obj = Ept(i=1, content=[Sub(content=[]), "tail"])

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 1
    assert backend.get_tail(children[0]) == "tail"

  def test_ept_missing_i_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_missing_i")
    handler = EptSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Ept, Ept(i=1, content=[]))
    obj.i = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_ept_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ept_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = EptSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None


class TestItSerializer:
  """Tests for ItSerializer."""

  def test_minimal_it(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_minimal")
    handler = ItSerializer(backend, XmlSerializationPolicy(), logger)
    obj = It(pos=Pos.BEGIN, content=["code"])

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "it"
    assert backend.get_attribute(result, "pos") == "begin"
    assert backend.get_text(result) == "code"

  def test_it_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_all")
    handler = ItSerializer(backend, XmlSerializationPolicy(), logger)
    obj = It(pos=Pos.END, x=2, type="link", content=["code"])

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "pos") == "end"
    assert backend.get_attribute(result, "x") == "2"
    assert backend.get_attribute(result, "type") == "link"

  def test_it_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_sub")
    handler = ItSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      return backend.create_element("sub")

    handler._set_emit(mock_emit)
    obj = It(pos=Pos.BEGIN, content=["text ", Sub(content=[]), " more"])

    result = handler._serialize(obj)
    assert backend.get_text(result) == "text "
    children = list(backend.iter_children(result))
    assert len(children) == 1
    assert backend.get_tail(children[0]) == " more"

  def test_it_missing_pos_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_missing_pos")
    handler = ItSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(It, It(pos=Pos.BEGIN, content=[]))
    obj.pos = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_it_invalid_x_type_ignored(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_invalid_x")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = ItSerializer(backend, policy, logger)
    obj = cast(It, It(pos=Pos.BEGIN, content=[]))
    obj.x = "not-an-int"  # type: ignore[assignment]

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "x") is None

  def test_it_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_it_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = ItSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None


class TestPhSerializer:
  """Tests for PhSerializer."""

  def test_minimal_ph(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_minimal")
    handler = PhSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Ph(content=["placeholder"])

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "ph"
    assert backend.get_text(result) == "placeholder"

  def test_ph_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_all")
    handler = PhSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Ph(x=1, type="image", assoc=Assoc.P, content=["placeholder"])

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "x") == "1"
    assert backend.get_attribute(result, "type") == "image"
    assert backend.get_attribute(result, "assoc") == "p"

  def test_ph_with_sub_element(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_sub")
    handler = PhSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      return backend.create_element("sub")

    handler._set_emit(mock_emit)
    obj = Ph(content=[Sub(content=["subflow"])])

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 1

  def test_ph_all_assoc_values(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_assoc")
    handler = PhSerializer(backend, XmlSerializationPolicy(), logger)

    for assoc, expected in [(Assoc.P, "p"), (Assoc.F, "f"), (Assoc.B, "b")]:
      obj = Ph(assoc=assoc, content=[])
      result = handler._serialize(obj)
      assert backend.get_attribute(result, "assoc") == expected

  def test_ph_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_ph_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = PhSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None


class TestHiSerializer:
  """Tests for HiSerializer."""

  def test_minimal_hi(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_minimal")
    handler = HiSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Hi(content=["highlighted text"])

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "hi"
    assert backend.get_text(result) == "highlighted text"

  def test_hi_with_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_attrs")
    handler = HiSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Hi(x=1, type="term", content=["text"])

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "x") == "1"
    assert backend.get_attribute(result, "type") == "term"

  def test_hi_with_inline_elements(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_inline")
    handler = HiSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = Hi(content=["before ", Bpt(i=1, content=[]), " ", Ept(i=1, content=[]), " after"])

    result = handler._serialize(obj)
    assert backend.get_text(result) == "before "
    children = list(backend.iter_children(result))
    assert len(children) == 2
    assert backend.get_tail(children[0]) == " "
    assert backend.get_tail(children[1]) == " after"

  def test_hi_nested_hi(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_nested")
    handler = HiSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      return backend.create_element("hi")

    handler._set_emit(mock_emit)
    obj = Hi(content=[Hi(content=["nested"])])

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 1

  def test_hi_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_hi_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = HiSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None


class TestSubSerializer:
  """Tests for SubSerializer."""

  def test_minimal_sub(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_minimal")
    handler = SubSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Sub(content=["sub-flow text"])

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "sub"
    assert backend.get_text(result) == "sub-flow text"

  def test_sub_with_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_attrs")
    handler = SubSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Sub(type="footnote", datatype="plaintext", content=["text"])

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "type") == "footnote"
    assert backend.get_attribute(result, "datatype") == "plaintext"

  def test_sub_with_inline_elements(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_inline")
    handler = SubSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = Sub(content=["text ", Bpt(i=1, content=[]), " more"])

    result = handler._serialize(obj)
    assert backend.get_text(result) == "text "
    children = list(backend.iter_children(result))
    assert len(children) == 1
    assert backend.get_tail(children[0]) == " more"

  def test_sub_invalid_child_type_ignored(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_invalid_child")
    policy = XmlSerializationPolicy(invalid_child_element=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = SubSerializer(backend, policy, logger)
    handler._set_emit(lambda o: backend.create_element("test"))

    obj = cast(Sub, Sub(content=[Bpt(i=1, content=[]), Prop(text="invalid", type="test")]))  # type: ignore[list-item]

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 1

  def test_sub_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_sub_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = SubSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None
