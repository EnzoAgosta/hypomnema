"""Tests for NoteSerializer and PropSerializer.

Tests the serialization of simple text-only elements with optional attributes:
- NoteSerializer: Note dataclasses
- PropSerializer: Prop dataclasses with required type attribute
"""

from logging import WARNING, getLogger
from typing import cast

import pytest

from hypomnema.base.errors import MissingTextContentError, RequiredAttributeMissingError
from hypomnema.base.types import Note, Prop
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import (
  Behavior,
  RaiseIgnore,
  RaiseIgnoreDefault,
  RaiseIgnoreForce,
  XmlSerializationPolicy,
)
from hypomnema.xml.serialization import NoteSerializer, PropSerializer


class TestPropSerializer:
  """Tests for PropSerializer."""

  def test_minimal_prop(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_minimal")
    handler = PropSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Prop(text="value", type="category")

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "prop"
    assert backend.get_text(result) == "value"
    assert backend.get_attribute(result, "type") == "category"

  def test_prop_with_lang(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_lang")
    handler = PropSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Prop(text="value", type="category", lang="en")

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "{http://www.w3.org/XML/1998/namespace}lang") == "en"

  def test_prop_with_o_encoding(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_encoding")
    handler = PropSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Prop(text="value", type="category", o_encoding="utf-8")

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "o-encoding") == "utf-8"

  def test_prop_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_all")
    handler = PropSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Prop(text="value", type="category", lang="en", o_encoding="utf-8")

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "prop"
    assert backend.get_text(result) == "value"
    assert backend.get_attribute(result, "type") == "category"
    assert backend.get_attribute(result, "{http://www.w3.org/XML/1998/namespace}lang") == "en"
    assert backend.get_attribute(result, "o-encoding") == "utf-8"

  def test_prop_missing_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_missing_text")
    handler = PropSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Prop, Prop(text="placeholder", type="category"))
    obj.text = None  # type: ignore[assignment]

    with pytest.raises(MissingTextContentError):
      handler._serialize(obj)

  def test_prop_missing_text_default_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_missing_text_default")
    policy = XmlSerializationPolicy(
      missing_text_content=Behavior(RaiseIgnoreDefault.DEFAULT, WARNING)
    )
    handler = PropSerializer(backend, policy, logger)
    obj = cast(Prop, Prop(text="placeholder", type="category"))
    obj.text = None  # type: ignore[assignment]

    result = handler._serialize(obj)
    assert backend.get_text(result) == ""

  def test_prop_missing_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_missing_type")
    handler = PropSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Prop, Prop(text="value", type="placeholder"))
    obj.type = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_prop_missing_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_prop_missing_type_ignore")
    policy = XmlSerializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    handler = PropSerializer(backend, policy, logger)
    obj = cast(Prop, Prop(text="value", type="placeholder"))
    obj.type = None  # type: ignore[assignment]

    with caplog.at_level(WARNING):
      result = handler._serialize(obj)

    assert result is not None
    assert "Required attribute" in caplog.text

  def test_prop_wrong_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_prop_wrong_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = PropSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._serialize(Note(text="not a prop"))  # type: ignore[arg-type]

    assert result is None
    assert "Invalid element type" in caplog.text


class TestNoteSerializer:
  """Tests for NoteSerializer."""

  def test_minimal_note(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_minimal")
    handler = NoteSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Note(text="A note")

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "A note"

  def test_note_with_lang(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_lang")
    handler = NoteSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Note(text="A note", lang="en")

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "{http://www.w3.org/XML/1998/namespace}lang") == "en"

  def test_note_with_o_encoding(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_encoding")
    handler = NoteSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Note(text="A note", o_encoding="utf-8")

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "o-encoding") == "utf-8"

  def test_note_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_all")
    handler = NoteSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Note(text="A note", lang="en", o_encoding="utf-8")

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "A note"
    assert backend.get_attribute(result, "{http://www.w3.org/XML/1998/namespace}lang") == "en"
    assert backend.get_attribute(result, "o-encoding") == "utf-8"

  def test_note_missing_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_missing_text")
    handler = NoteSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Note, Note(text="placeholder"))
    obj.text = None  # type: ignore[assignment]

    with pytest.raises(MissingTextContentError):
      handler._serialize(obj)

  def test_note_missing_text_default_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_missing_text_default")
    policy = XmlSerializationPolicy(
      missing_text_content=Behavior(RaiseIgnoreDefault.DEFAULT, WARNING)
    )
    handler = NoteSerializer(backend, policy, logger)
    obj = cast(Note, Note(text="placeholder"))
    obj.text = None  # type: ignore[assignment]

    result = handler._serialize(obj)
    assert backend.get_text(result) == ""

  def test_note_wrong_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_note_wrong_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = NoteSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._serialize(Prop(text="not a note", type="test"))  # type: ignore[arg-type]

    assert result is None
    assert "Invalid element type" in caplog.text
