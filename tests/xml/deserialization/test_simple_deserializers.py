"""Tests for NoteDeserializer and PropDeserializer.

Tests the deserialization of simple text-only elements with optional attributes:
- NoteDeserializer: <note> elements
- PropDeserializer: <prop> elements with required type attribute
"""

from logging import WARNING, getLogger

import pytest

from hypomnema.base.errors import MissingTextContentError, RequiredAttributeMissingError
from hypomnema.base.types import Note, Prop
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization import NoteDeserializer, PropDeserializer
from hypomnema.xml.policy import Behavior, RaiseIgnore, RaiseIgnoreForce, XmlDeserializationPolicy


class TestNoteDeserializer:
  """Tests for NoteDeserializer."""

  def test_minimal_note(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_minimal")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")
    backend.set_text(elem, "A note")

    result = handler._deserialize(elem)
    assert isinstance(result, Note)
    assert result.text == "A note"
    assert result.lang is None
    assert result.o_encoding is None

  def test_note_with_lang(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_lang")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")
    backend.set_text(elem, "A note")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.lang == "en"

  def test_note_with_o_encoding(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_encoding")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")
    backend.set_text(elem, "A note")
    backend.set_attribute(elem, "o-encoding", "utf-8")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.o_encoding == "utf-8"

  def test_note_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_all")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")
    backend.set_text(elem, "A note")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    backend.set_attribute(elem, "o-encoding", "utf-8")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.text == "A note"
    assert result.lang == "en"
    assert result.o_encoding == "utf-8"

  def test_note_missing_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_missing_text")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")

    with pytest.raises(MissingTextContentError):
      handler._deserialize(elem)

  def test_note_missing_text_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_note_missing_text_ignore")
    policy = XmlDeserializationPolicy(missing_text_content=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = NoteDeserializer(backend, policy, logger)
    elem = backend.create_element("note")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.text is None
    assert "has no text content" in caplog.text

  def test_note_invalid_tag_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_invalid_tag")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("wrong")
    backend.set_text(elem, "text")

    with pytest.raises(Exception):
      handler._deserialize(elem)

  def test_note_invalid_tag_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_note_invalid_tag_ignore")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = NoteDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    backend.set_text(elem, "text")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is None
    assert "Invalid tag" in caplog.text

  def test_note_whitespace_only_text(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_whitespace")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")
    backend.set_text(elem, "   ")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.text == "   "

  def test_note_empty_string_is_valid_text(self, backend: XmlBackend) -> None:
    logger = getLogger("test_note_empty_string")
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("note")
    backend.set_text(elem, "")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.text == ""


class TestPropDeserializer:
  """Tests for PropDeserializer."""

  def test_minimal_prop(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_minimal")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "property value")
    backend.set_attribute(elem, "type", "category")

    result = handler._deserialize(elem)
    assert isinstance(result, Prop)
    assert result.text == "property value"
    assert result.type == "category"
    assert result.lang is None
    assert result.o_encoding is None

  def test_prop_with_lang(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_lang")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "value")
    backend.set_attribute(elem, "type", "type1")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.lang == "en"

  def test_prop_with_o_encoding(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_encoding")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "value")
    backend.set_attribute(elem, "type", "type1")
    backend.set_attribute(elem, "o-encoding", "iso-8859-1")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.o_encoding == "iso-8859-1"

  def test_prop_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_all")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "value")
    backend.set_attribute(elem, "type", "type1")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    backend.set_attribute(elem, "o-encoding", "utf-8")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.text == "value"
    assert result.type == "type1"
    assert result.lang == "en"
    assert result.o_encoding == "utf-8"

  def test_prop_missing_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_missing_text")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_attribute(elem, "type", "type1")

    with pytest.raises(MissingTextContentError):
      handler._deserialize(elem)

  def test_prop_missing_text_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_prop_missing_text_ignore")
    policy = XmlDeserializationPolicy(missing_text_content=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = PropDeserializer(backend, policy, logger)
    elem = backend.create_element("prop")
    backend.set_attribute(elem, "type", "type1")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.text is None
    assert "has no text content" in caplog.text

  def test_prop_missing_type_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_missing_type")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "value")

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_prop_missing_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_prop_missing_type_ignore")
    policy = XmlDeserializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    handler = PropDeserializer(backend, policy, logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "value")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.type is None
    assert "Required attribute" in caplog.text

  def test_prop_invalid_tag_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_invalid_tag")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("wrong")
    backend.set_text(elem, "value")
    backend.set_attribute(elem, "type", "type1")

    with pytest.raises(Exception):
      handler._deserialize(elem)

  def test_prop_invalid_tag_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_prop_invalid_tag_ignore")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = PropDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    backend.set_text(elem, "value")
    backend.set_attribute(elem, "type", "type1")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is None
    assert "Invalid tag" in caplog.text

  def test_prop_with_custom_type_prefix(self, backend: XmlBackend) -> None:
    logger = getLogger("test_prop_custom_type")
    handler = PropDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("prop")
    backend.set_text(elem, "value")
    backend.set_attribute(elem, "type", "x-custom-prop")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.type == "x-custom-prop"
