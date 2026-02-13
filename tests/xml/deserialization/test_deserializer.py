"""Tests for the Deserializer orchestrator.

Tests the orchestration layer that:
- Maintains handler registry
- Dispatches elements to appropriate handlers
- Handles missing handlers per policy
- Injects emit function for recursive deserialization
"""

from logging import WARNING, getLogger

import pytest

from hypomnema.base.errors import MissingDeserializationHandlerError
from hypomnema.base.types import Bpt, Note, Prop, Sub
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization import Deserializer, NoteDeserializer
from hypomnema.xml.deserialization.base import BaseElementDeserializer
from hypomnema.xml.policy import Behavior, RaiseIgnore, RaiseIgnoreDefault, XmlDeserializationPolicy


class TestDeserializerInit:
  """Tests for Deserializer initialization."""

  def test_init_with_defaults(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    assert deserializer.backend is backend
    assert deserializer.policy == XmlDeserializationPolicy()
    assert "note" in deserializer.handlers
    assert "prop" in deserializer.handlers
    assert "tu" in deserializer.handlers

  def test_init_with_custom_policy(self, backend: XmlBackend) -> None:
    policy = XmlDeserializationPolicy()
    deserializer = Deserializer(backend, policy=policy)
    assert deserializer.policy is policy

  def test_init_with_custom_logger(self, backend: XmlBackend) -> None:
    logger = getLogger("test_logger")
    deserializer = Deserializer(backend, logger=logger)
    assert deserializer.logger is logger

  def test_init_with_custom_handlers(self, backend: XmlBackend) -> None:
    logger = getLogger("test_custom_handlers")
    custom_handlers = {"note": NoteDeserializer(backend, XmlDeserializationPolicy(), logger)}
    deserializer = Deserializer(backend, handlers=custom_handlers)
    assert "note" in deserializer.handlers
    assert "prop" not in deserializer.handlers


class TestDeserializerDefaultHandlers:
  """Tests for default handler registration."""

  def test_all_handlers_registered(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    expected_handlers = [
      "note",
      "prop",
      "header",
      "tu",
      "tuv",
      "bpt",
      "ept",
      "it",
      "ph",
      "sub",
      "hi",
      "tmx",
    ]
    for tag in expected_handlers:
      assert tag in deserializer.handlers, f"Handler for {tag} not registered"

  def test_handlers_have_emit_set(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    for tag, handler in deserializer.handlers.items():
      assert handler._emit is not None, f"Handler for {tag} does not have emit set"

  def test_handlers_emit_calls_deserialize(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    note_handler = deserializer.handlers["note"]
    elem = backend.create_element("note")
    backend.set_text(elem, "test note")

    result = note_handler.emit(elem)
    assert isinstance(result, Note)
    assert result.text == "test note"


class TestDeserializerDeserialize:
  """Tests for deserialize method."""

  def test_deserialize_dispatches_correctly(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)

    note_elem = backend.create_element("note")
    backend.set_text(note_elem, "note text")
    result = deserializer.deserialize(note_elem)
    assert isinstance(result, Note)
    assert result.text == "note text"

    prop_elem = backend.create_element("prop")
    backend.set_text(prop_elem, "prop value")
    backend.set_attribute(prop_elem, "type", "category")
    result = deserializer.deserialize(prop_elem)
    assert isinstance(result, Prop)
    assert result.text == "prop value"
    assert result.type == "category"

  def test_deserialize_with_explicit_handler(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    handler = NoteDeserializer(backend, XmlDeserializationPolicy(), deserializer.logger)
    handler._set_emit(deserializer.deserialize)

    elem = backend.create_element("note")
    backend.set_text(elem, "text")
    result = deserializer.deserialize(elem, handler=handler)
    assert isinstance(result, Note)
    assert result.text == "text"

  def test_deserialize_unknown_tag_raises(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    elem = backend.create_element("unknown")

    with pytest.raises(MissingDeserializationHandlerError):
      deserializer.deserialize(elem)

  def test_deserialize_unknown_tag_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = XmlDeserializationPolicy(
      missing_deserialization_handler=Behavior(RaiseIgnoreDefault.IGNORE, WARNING)
    )
    deserializer = Deserializer(backend, policy=policy)

    elem = backend.create_element("unknown")

    with caplog.at_level(WARNING):
      result = deserializer.deserialize(elem)

    assert result is None
    assert "Missing handler" in caplog.text

  def test_deserialize_unknown_tag_default_uses_builtin(self, backend: XmlBackend) -> None:
    policy = XmlDeserializationPolicy(
      missing_deserialization_handler=Behavior(RaiseIgnoreDefault.DEFAULT)
    )
    deserializer = Deserializer(backend, policy=policy)

    elem = backend.create_element("note")
    backend.set_text(elem, "text")
    result = deserializer.deserialize(elem)
    assert isinstance(result, Note)


class TestDeserializerResolveHandler:
  """Tests for _resolve_handler method."""

  def test_resolve_existing_handler(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    handler = deserializer._resolve_handler("note")
    assert handler is not None
    assert isinstance(handler, NoteDeserializer)

  def test_resolve_missing_handler_raises(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)
    with pytest.raises(MissingDeserializationHandlerError):
      deserializer._resolve_handler("unknown")

  def test_resolve_missing_handler_ignore(self, backend: XmlBackend) -> None:
    policy = XmlDeserializationPolicy(
      missing_deserialization_handler=Behavior(RaiseIgnoreDefault.IGNORE)
    )
    deserializer = Deserializer(backend, policy=policy)
    handler = deserializer._resolve_handler("unknown")
    assert handler is None

  def test_resolve_missing_handler_default_uses_builtin(self, backend: XmlBackend) -> None:
    policy = XmlDeserializationPolicy(
      missing_deserialization_handler=Behavior(RaiseIgnoreDefault.DEFAULT)
    )
    deserializer = Deserializer(backend, policy=policy)

    handler = deserializer._resolve_handler("note")
    assert handler is not None
    assert isinstance(handler, NoteDeserializer)

  def test_resolve_missing_handler_default_raises_for_unknown(self, backend: XmlBackend) -> None:
    policy = XmlDeserializationPolicy(
      missing_deserialization_handler=Behavior(RaiseIgnoreDefault.DEFAULT)
    )
    deserializer = Deserializer(backend, policy=policy)

    with pytest.raises(MissingDeserializationHandlerError):
      deserializer._resolve_handler("unknown")


class TestDeserializerEmitIntegration:
  """Tests for emit function integration between handlers."""

  def test_emit_allows_recursive_deserialization(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)

    prop_elem = backend.create_element("prop")
    backend.set_text(prop_elem, "value")
    backend.set_attribute(prop_elem, "type", "category")

    result = deserializer.deserialize(prop_elem)
    assert isinstance(result, Prop)

  def test_nested_elements_deserialized_correctly(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)

    bpt_elem = backend.create_element("bpt")
    backend.set_attribute(bpt_elem, "i", "1")
    backend.set_text(bpt_elem, "code before ")
    sub_elem = backend.create_element("sub")
    backend.set_text(sub_elem, "subflow")
    backend.append_child(bpt_elem, sub_elem)
    backend.set_tail(sub_elem, " code after")

    result = deserializer.deserialize(bpt_elem)
    assert isinstance(result, Bpt)
    assert len(result.content) == 3
    assert result.content[0] == "code before "
    assert isinstance(result.content[1], Sub)
    assert result.content[2] == " code after"

  def test_custom_handler_with_emit(self, backend: XmlBackend) -> None:
    logger = getLogger("test_custom_emit")
    custom_handler = NoteDeserializer(backend, XmlDeserializationPolicy(), logger)
    custom_handlers = {"note": custom_handler}
    deserializer = Deserializer(backend, handlers=custom_handlers)

    note_elem = backend.create_element("note")
    backend.set_text(note_elem, "custom note")
    result = deserializer.deserialize(note_elem)
    assert isinstance(result, Note)
    assert result.text == "custom note"


class TestDeserializerCustomHandlersOverride:
  """Tests for custom handlers overriding default behavior."""

  def test_custom_handler_overrides_default(self, backend: XmlBackend) -> None:
    class CustomNoteDeserializer(BaseElementDeserializer):
      def _deserialize(self, element):
        return Note(text="custom: " + (backend.get_text(element) or ""))

    custom_handler = CustomNoteDeserializer(backend, XmlDeserializationPolicy(), getLogger())
    custom_handlers = {"note": custom_handler}
    deserializer = Deserializer(backend, handlers=custom_handlers)

    note_elem = backend.create_element("note")
    backend.set_text(note_elem, "text")
    result = deserializer.deserialize(note_elem)

    assert isinstance(result, Note)
    assert result.text == "custom: text"

  def test_custom_handlers_not_merged_with_defaults(self, backend: XmlBackend) -> None:
    custom_handlers = {"note": NoteDeserializer(backend, XmlDeserializationPolicy(), getLogger())}
    deserializer = Deserializer(backend, handlers=custom_handlers)

    assert "note" in deserializer.handlers
    assert "prop" not in deserializer.handlers


class TestDeserializerPolicyPropagation:
  """Tests for policy propagation to handlers."""

  def test_handlers_use_same_policy(self, backend: XmlBackend) -> None:
    policy = XmlDeserializationPolicy()
    deserializer = Deserializer(backend, policy=policy)

    for handler in deserializer.handlers.values():
      assert handler.policy is policy

  def test_handler_uses_policy_for_error_handling(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = XmlDeserializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    deserializer = Deserializer(backend, policy=policy)

    prop_elem = backend.create_element("prop")
    backend.set_text(prop_elem, "value")

    with caplog.at_level(WARNING):
      result = deserializer.deserialize(prop_elem)

    assert isinstance(result, Prop)
    assert result.type is None


class TestDeserializerLoggerPropagation:
  """Tests for logger propagation to handlers."""

  def test_handlers_use_same_logger(self, backend: XmlBackend) -> None:
    logger = getLogger("test_logger")
    deserializer = Deserializer(backend, logger=logger)

    for handler in deserializer.handlers.values():
      assert handler.logger is logger

  def test_default_logger_used_when_not_provided(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)

    for handler in deserializer.handlers.values():
      assert handler.logger is not None


class TestDeserializerWithBackendEquivalence:
  """Tests ensuring consistent behavior across backends."""

  def test_deserialize_note_produces_same_result(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)

    note_elem = backend.create_element("note")
    backend.set_text(note_elem, "A note")
    backend.set_attribute(note_elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")

    result = deserializer.deserialize(note_elem)

    assert isinstance(result, Note)
    assert result.text == "A note"
    assert result.lang == "en"

  def test_deserialize_prop_produces_same_result(self, backend: XmlBackend) -> None:
    deserializer = Deserializer(backend)

    prop_elem = backend.create_element("prop")
    backend.set_text(prop_elem, "value")
    backend.set_attribute(prop_elem, "type", "category")
    backend.set_attribute(prop_elem, "o-encoding", "utf-8")

    result = deserializer.deserialize(prop_elem)

    assert isinstance(result, Prop)
    assert result.text == "value"
    assert result.type == "category"
    assert result.o_encoding == "utf-8"
