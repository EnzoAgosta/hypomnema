"""Tests for the Serializer orchestrator.

Tests the orchestration layer that:
- Maintains handler registry
- Dispatches objects to appropriate handlers
- Handles missing handlers per policy
- Injects emit function for recursive serialization
"""

from logging import WARNING, getLogger

import pytest

from hypomnema.base.errors import MissingSerializationHandlerError
from hypomnema.base.types import Bpt, Header, Note, Prop, Segtype, Sub, Tmx, Tu, Tuv
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import Behavior, RaiseIgnoreDefault, XmlSerializationPolicy
from hypomnema.xml.serialization import NoteSerializer, Serializer
from hypomnema.xml.serialization.base import BaseElementSerializer


class CustomClass:
  """Custom class for testing missing handler."""

  pass


class TestSerializerInit:
  """Tests for Serializer initialization."""

  def test_init_with_defaults(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    assert serializer.backend is backend
    assert serializer.policy == XmlSerializationPolicy()
    assert Note in serializer.handlers
    assert Prop in serializer.handlers
    assert Tu in serializer.handlers

  def test_init_with_custom_policy(self, backend: XmlBackend) -> None:
    policy = XmlSerializationPolicy()
    serializer = Serializer(backend, policy=policy)
    assert serializer.policy is policy

  def test_init_with_custom_logger(self, backend: XmlBackend) -> None:
    logger = getLogger("test_logger")
    serializer = Serializer(backend, logger=logger)
    assert serializer.logger is logger

  def test_init_with_custom_handlers(self, backend: XmlBackend) -> None:
    logger = getLogger("test_custom_handlers")
    custom_handlers = {Note: NoteSerializer(backend, XmlSerializationPolicy(), logger)}
    serializer = Serializer(backend, handlers=custom_handlers)
    assert Note in serializer.handlers
    assert Prop not in serializer.handlers


class TestSerializerDefaultHandlers:
  """Tests for default handler registration."""

  def test_all_handlers_registered(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    expected_handlers = [Note, Prop, Header, Tu, Tuv, Bpt, Sub, Tmx]
    for obj_type in expected_handlers:
      assert obj_type in serializer.handlers, f"Handler for {obj_type} not registered"

  def test_handlers_have_emit_set(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    for obj_type, handler in serializer.handlers.items():
      assert handler._emit is not None, f"Handler for {obj_type} does not have emit set"

  def test_handlers_emit_calls_serialize(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    note_handler = serializer.handlers[Note]
    obj = Note(text="test note")

    result = note_handler.emit(obj)
    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "test note"


class TestSerializerSerialize:
  """Tests for serialize method."""

  def test_serialize_dispatches_correctly(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    note = Note(text="note text")
    result = serializer.serialize(note)
    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "note text"

    prop = Prop(text="prop value", type="category")
    result = serializer.serialize(prop)
    assert backend.get_tag(result) == "prop"
    assert backend.get_text(result) == "prop value"
    assert backend.get_attribute(result, "type") == "category"

  def test_serialize_with_explicit_handler(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    handler = NoteSerializer(backend, XmlSerializationPolicy(), serializer.logger)
    handler._set_emit(serializer.serialize)

    obj = Note(text="text")
    result = serializer.serialize(obj, handler=handler)
    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "text"

  def test_serialize_unknown_type_raises(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    obj = CustomClass()

    with pytest.raises(MissingSerializationHandlerError):
      serializer.serialize(obj)  # type: ignore[arg-type]

  def test_serialize_unknown_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = XmlSerializationPolicy(
      missing_serialization_handler=Behavior(RaiseIgnoreDefault.IGNORE, WARNING)
    )
    serializer = Serializer(backend, policy=policy)

    obj = CustomClass()

    with caplog.at_level(WARNING):
      result = serializer.serialize(obj)  # type: ignore[arg-type]

    assert result is None
    assert "Missing handler" in caplog.text

  def test_serialize_unknown_type_default_uses_builtin(self, backend: XmlBackend) -> None:
    policy = XmlSerializationPolicy(
      missing_serialization_handler=Behavior(RaiseIgnoreDefault.DEFAULT)
    )
    serializer = Serializer(backend, policy=policy)

    obj = Note(text="text")
    result = serializer.serialize(obj)
    assert backend.get_tag(result) == "note"


class TestSerializerResolveHandler:
  """Tests for _resolve_handler method."""

  def test_resolve_existing_handler(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    handler = serializer._resolve_handler(Note)
    assert handler is not None
    assert isinstance(handler, NoteSerializer)

  def test_resolve_missing_handler_raises(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)
    with pytest.raises(MissingSerializationHandlerError):
      serializer._resolve_handler(CustomClass)

  def test_resolve_missing_handler_ignore(self, backend: XmlBackend) -> None:
    policy = XmlSerializationPolicy(
      missing_serialization_handler=Behavior(RaiseIgnoreDefault.IGNORE)
    )
    serializer = Serializer(backend, policy=policy)
    handler = serializer._resolve_handler(CustomClass)
    assert handler is None

  def test_resolve_missing_handler_default_uses_builtin(self, backend: XmlBackend) -> None:
    policy = XmlSerializationPolicy(
      missing_serialization_handler=Behavior(RaiseIgnoreDefault.DEFAULT)
    )
    serializer = Serializer(backend, policy=policy)
    handler = serializer._resolve_handler(Note)
    assert handler is not None
    assert isinstance(handler, NoteSerializer)

  def test_resolve_missing_handler_default_raises_for_unknown(self, backend: XmlBackend) -> None:
    policy = XmlSerializationPolicy(
      missing_serialization_handler=Behavior(RaiseIgnoreDefault.DEFAULT)
    )
    serializer = Serializer(backend, policy=policy)
    with pytest.raises(MissingSerializationHandlerError):
      serializer._resolve_handler(CustomClass)


class TestSerializerEmitIntegration:
  """Tests for emit function integration between handlers."""

  def test_emit_allows_recursive_serialization(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    prop = Prop(text="value", type="category")
    result = serializer.serialize(prop)
    assert backend.get_tag(result) == "prop"

  def test_nested_elements_serialized_correctly(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    bpt = Bpt(i=1, content=["code before ", Sub(content=["subflow"]), " code after"])
    result = serializer.serialize(bpt)
    assert backend.get_tag(result) == "bpt"
    assert backend.get_text(result) == "code before "
    children = list(backend.iter_children(result))
    assert len(children) == 1
    assert backend.get_tag(children[0]) == "sub"
    assert backend.get_tail(children[0]) == " code after"

  def test_custom_handler_with_emit(self, backend: XmlBackend) -> None:
    logger = getLogger("test_custom_emit")
    custom_handler = NoteSerializer(backend, XmlSerializationPolicy(), logger)
    custom_handlers = {Note: custom_handler}
    serializer = Serializer(backend, handlers=custom_handlers)

    note = Note(text="custom note")
    result = serializer.serialize(note)
    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "custom note"


class TestSerializerCustomHandlersOverride:
  """Tests for custom handlers overriding default behavior."""

  def test_custom_handler_overrides_default(self, backend: XmlBackend) -> None:
    class CustomNoteSerializer(BaseElementSerializer):
      def _serialize(self, obj):
        elem = self.backend.create_element("note")
        self.backend.set_text(elem, "custom: " + obj.text)
        return elem

    custom_handler = CustomNoteSerializer(backend, XmlSerializationPolicy(), getLogger())
    custom_handlers = {Note: custom_handler}
    serializer = Serializer(backend, handlers=custom_handlers)

    note = Note(text="text")
    result = serializer.serialize(note)

    assert backend.get_text(result) == "custom: text"

  def test_custom_handlers_not_merged_with_defaults(self, backend: XmlBackend) -> None:
    custom_handlers = {Note: NoteSerializer(backend, XmlSerializationPolicy(), getLogger())}
    serializer = Serializer(backend, handlers=custom_handlers)

    assert Note in serializer.handlers
    assert Prop not in serializer.handlers


class TestSerializerPolicyPropagation:
  """Tests for policy propagation to handlers."""

  def test_handlers_use_same_policy(self, backend: XmlBackend) -> None:
    policy = XmlSerializationPolicy()
    serializer = Serializer(backend, policy=policy)

    for handler in serializer.handlers.values():
      assert handler.policy is policy


class TestSerializerLoggerPropagation:
  """Tests for logger propagation to handlers."""

  def test_handlers_use_same_logger(self, backend: XmlBackend) -> None:
    logger = getLogger("test_logger")
    serializer = Serializer(backend, logger=logger)

    for handler in serializer.handlers.values():
      assert handler.logger is logger

  def test_default_logger_used_when_not_provided(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    for handler in serializer.handlers.values():
      assert handler.logger is not None


class TestSerializerWithBackendEquivalence:
  """Tests ensuring consistent behavior across backends."""

  def test_serialize_note_produces_same_result(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    note = Note(text="A note", lang="en")
    result = serializer.serialize(note)

    assert backend.get_tag(result) == "note"
    assert backend.get_text(result) == "A note"
    assert backend.get_attribute(result, "{http://www.w3.org/XML/1998/namespace}lang") == "en"

  def test_serialize_prop_produces_same_result(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    prop = Prop(text="value", type="category", o_encoding="utf-8")
    result = serializer.serialize(prop)

    assert backend.get_tag(result) == "prop"
    assert backend.get_text(result) == "value"
    assert backend.get_attribute(result, "type") == "category"
    assert backend.get_attribute(result, "o-encoding") == "utf-8"

  def test_serialize_full_tmx_produces_same_result(self, backend: XmlBackend) -> None:
    serializer = Serializer(backend)

    tmx = Tmx(
      header=Header(
        creationtool="tool",
        creationtoolversion="1.0",
        segtype=Segtype.SENTENCE,
        o_tmf="tmx",
        adminlang="en",
        srclang="en",
        datatype="plaintext",
      ),
      body=[Tu(variants=[Tuv(lang="en", content=["Hello"]), Tuv(lang="fr", content=["Bonjour"])])],
    )

    result = serializer.serialize(tmx)
    assert backend.get_tag(result) == "tmx"
    assert backend.get_attribute(result, "version") == "1.4"

    children = list(backend.iter_children(result))
    assert len(children) == 2
    assert backend.get_tag(children[0]) == "header"
    assert backend.get_tag(children[1]) == "body"
