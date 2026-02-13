"""Tests for structure element deserializers.

Tests deserialization of TMX structural elements:
- HeaderDeserializer: <header> elements
- TuvDeserializer: <tuv> translation unit variants
- TuDeserializer: <tu> translation units
- TmxDeserializer: <tmx> root elements
"""

from datetime import datetime
from logging import WARNING, getLogger

import pytest

from hypomnema.base.errors import (
  DuplicateChildError,
  ExtraTextError,
  InvalidChildTagError,
  InvalidEnumValueError,
  InvalidPolicyActionError,
  MissingBodyError,
  MissingHeaderError,
  MissingSegError,
  RequiredAttributeMissingError,
)
from hypomnema.base.types import Bpt, Header, Note, Prop, Segtype, Tmx, Tu, Tuv
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization import (
  HeaderDeserializer,
  TmxDeserializer,
  TuDeserializer,
  TuvDeserializer,
)
from hypomnema.xml.policy import (
  Behavior,
  DuplicateChildAction,
  RaiseIgnore,
  RaiseIgnoreForce,
  RaiseNoneKeep,
  XmlDeserializationPolicy,
)


class TestHeaderDeserializer:
  """Tests for HeaderDeserializer."""

  def _create_minimal_header(self, backend: XmlBackend) -> object:
    elem = backend.create_element("header")
    backend.set_attribute(elem, "creationtool", "test-tool")
    backend.set_attribute(elem, "creationtoolversion", "1.0")
    backend.set_attribute(elem, "segtype", "sentence")
    backend.set_attribute(elem, "o-tmf", "tmx")
    backend.set_attribute(elem, "adminlang", "en")
    backend.set_attribute(elem, "srclang", "en")
    backend.set_attribute(elem, "datatype", "plaintext")
    return elem

  def test_minimal_header(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_minimal")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_header(backend)

    result = handler._deserialize(elem)
    assert isinstance(result, Header)
    assert result.creationtool == "test-tool"
    assert result.creationtoolversion == "1.0"
    assert result.segtype == Segtype.SENTENCE
    assert result.o_tmf == "tmx"
    assert result.adminlang == "en"
    assert result.srclang == "en"
    assert result.datatype == "plaintext"
    assert result.o_encoding is None
    assert result.creationdate is None
    assert result.props == []
    assert result.notes == []

  def test_header_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_all")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_header(backend)
    backend.set_attribute(elem, "o-encoding", "utf-8")
    backend.set_attribute(elem, "creationdate", "2024-01-15T10:30:00")
    backend.set_attribute(elem, "creationid", "user1")
    backend.set_attribute(elem, "changedate", "2024-01-20T15:00:00")
    backend.set_attribute(elem, "changeid", "user2")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.o_encoding == "utf-8"
    assert result.creationdate == datetime(2024, 1, 15, 10, 30, 0)
    assert result.creationid == "user1"
    assert result.changedate == datetime(2024, 1, 20, 15, 0, 0)
    assert result.changeid == "user2"

  def test_header_with_props_and_notes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_children")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "prop":
        return Prop(text="value", type="category")
      elif tag == "note":
        return Note(text="a note")
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_header(backend)

    prop1 = backend.create_element("prop")
    backend.append_child(elem, prop1)
    note1 = backend.create_element("note")
    backend.append_child(elem, note1)
    prop2 = backend.create_element("prop")
    backend.append_child(elem, prop2)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.props) == 2
    assert len(result.notes) == 1

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = HeaderDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def test_header_missing_required_attribute_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_missing_attr")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("header")
    backend.set_attribute(elem, "creationtool", "tool")

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_header_invalid_segtype_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_invalid_segtype")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = self._create_minimal_header(backend)
    backend.set_attribute(elem, "segtype", "invalid")

    with pytest.raises(InvalidEnumValueError):
      handler._deserialize(elem)

  def test_header_invalid_segtype_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_invalid_segtype_none")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = HeaderDeserializer(backend, policy, logger)
    elem = self._create_minimal_header(backend)
    backend.set_attribute(elem, "segtype", "invalid")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.segtype is None

  def test_header_invalid_datetime_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_invalid_datetime")
    policy = XmlDeserializationPolicy(invalid_datetime_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = HeaderDeserializer(backend, policy, logger)
    elem = self._create_minimal_header(backend)
    backend.set_attribute(elem, "creationdate", "not-a-date")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.creationdate is None

  def test_header_extra_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_extra_text")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_header(backend)
    backend.set_text(elem, "extra text")

    with pytest.raises(ExtraTextError):
      handler._deserialize(elem)

  def test_header_extra_text_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_header_extra_text_ignore")
    policy = XmlDeserializationPolicy(extra_text=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = HeaderDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_header(backend)
    backend.set_text(elem, "extra text")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert "extra text content" in caplog.text

  def test_header_whitespace_text_allowed(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_whitespace")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_header(backend)
    backend.set_text(elem, "   \n  ")

    result = handler._deserialize(elem)
    assert result is not None

  def test_header_invalid_child_tag_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_invalid_child")
    handler = HeaderDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_header(backend)
    invalid = backend.create_element("invalid")
    backend.append_child(elem, invalid)

    with pytest.raises(InvalidChildTagError):
      handler._deserialize(elem)


class TestTuvDeserializer:
  """Tests for TuvDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = TuvDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def _create_minimal_tuv(self, backend: XmlBackend) -> object:
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    seg = backend.create_element("seg")
    backend.set_text(seg, "text")
    backend.append_child(elem, seg)
    return elem

  def test_minimal_tuv(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_minimal")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tuv(backend)

    result = handler._deserialize(elem)
    assert isinstance(result, Tuv)
    assert result.lang == "en"
    assert result.content == ["text"]

  def test_tuv_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_all")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    backend.set_attribute(elem, "o-encoding", "utf-8")
    backend.set_attribute(elem, "datatype", "html")
    backend.set_attribute(elem, "usagecount", "5")
    backend.set_attribute(elem, "lastusagedate", "2024-01-15T10:00:00")
    backend.set_attribute(elem, "creationtool", "tool")
    backend.set_attribute(elem, "creationtoolversion", "1.0")
    backend.set_attribute(elem, "creationdate", "2024-01-01T00:00:00")
    backend.set_attribute(elem, "creationid", "user")
    backend.set_attribute(elem, "changedate", "2024-01-10T12:00:00")
    backend.set_attribute(elem, "changeid", "editor")
    backend.set_attribute(elem, "o-tmf", "tmx")
    seg = backend.create_element("seg")
    backend.set_text(seg, "text")
    backend.append_child(elem, seg)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.o_encoding == "utf-8"
    assert result.datatype == "html"
    assert result.usagecount == 5
    assert result.lastusagedate == datetime(2024, 1, 15, 10, 0, 0)
    assert result.creationtool == "tool"
    assert result.creationtoolversion == "1.0"
    assert result.creationdate == datetime(2024, 1, 1, 0, 0, 0)
    assert result.creationid == "user"
    assert result.changedate == datetime(2024, 1, 10, 12, 0, 0)
    assert result.changeid == "editor"
    assert result.o_tmf == "tmx"

  def test_tuv_with_props_and_notes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_children")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "prop":
        return Prop(text="value", type="type1")
      elif tag == "note":
        return Note(text="note")
      elif tag == "bpt":
        return Bpt(i=1, content=[])
      return None

    handler._set_emit(mock_emit)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")

    prop1 = backend.create_element("prop")
    backend.append_child(elem, prop1)
    note1 = backend.create_element("note")
    backend.append_child(elem, note1)

    seg = backend.create_element("seg")
    backend.set_text(seg, "text ")
    bpt = backend.create_element("bpt")
    backend.append_child(seg, bpt)
    backend.set_tail(bpt, " more")
    backend.append_child(elem, seg)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.props) == 1
    assert len(result.notes) == 1
    assert len(result.content) == 3

  def test_tuv_missing_lang_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_missing_lang")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    seg = backend.create_element("seg")
    backend.set_text(seg, "text")
    backend.append_child(elem, seg)

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_tuv_missing_seg_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_missing_seg")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")

    with pytest.raises(MissingSegError):
      handler._deserialize(elem)

  def test_tuv_missing_seg_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_tuv_missing_seg_ignore")
    policy = XmlDeserializationPolicy(missing_seg=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = TuvDeserializer(backend, policy, logger)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.content == []
    assert "Missing <seg>" in caplog.text

  def test_tuv_multiple_seg_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_multi_seg")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    seg1 = backend.create_element("seg")
    backend.set_text(seg1, "first")
    backend.append_child(elem, seg1)
    seg2 = backend.create_element("seg")
    backend.set_text(seg2, "second")
    backend.append_child(elem, seg2)

    with pytest.raises(DuplicateChildError):
      handler._deserialize(elem)

  def test_tuv_multiple_seg_keep_first(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_multi_first")
    policy = XmlDeserializationPolicy(multiple_seg=Behavior(DuplicateChildAction.KEEP_FIRST))
    handler = TuvDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    seg1 = backend.create_element("seg")
    backend.set_text(seg1, "first")
    backend.append_child(elem, seg1)
    seg2 = backend.create_element("seg")
    backend.set_text(seg2, "second")
    backend.append_child(elem, seg2)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.content == ["first"]

  def test_tuv_multiple_seg_keep_last(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_multi_last")
    policy = XmlDeserializationPolicy(multiple_seg=Behavior(DuplicateChildAction.KEEP_LAST))
    handler = TuvDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    seg1 = backend.create_element("seg")
    backend.set_text(seg1, "first")
    backend.append_child(elem, seg1)
    seg2 = backend.create_element("seg")
    backend.set_text(seg2, "second")
    backend.append_child(elem, seg2)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.content == ["second"]

  def test_tuv_multiple_seg_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_multi_seg")
    policy = XmlDeserializationPolicy(multiple_seg=Behavior("invalid_action", WARNING))  # type: ignore
    handler = TuvDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    seg1 = backend.create_element("seg")
    backend.set_text(seg1, "first")
    backend.append_child(elem, seg1)
    seg2 = backend.create_element("seg")
    backend.set_text(seg2, "second")
    backend.append_child(elem, seg2)

    with pytest.raises(InvalidPolicyActionError):
      handler._deserialize(elem)

  def test_tuv_extra_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_extra_text")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    backend.set_text(elem, "extra")
    seg = backend.create_element("seg")
    backend.set_text(seg, "text")
    backend.append_child(elem, seg)

    with pytest.raises(ExtraTextError):
      handler._deserialize(elem)

  def test_tuv_invalid_usagecount_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_invalid_usagecount")
    policy = XmlDeserializationPolicy(invalid_int_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = TuvDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    backend.set_attribute(elem, "usagecount", "not-an-int")
    seg = backend.create_element("seg")
    backend.set_text(seg, "text")
    backend.append_child(elem, seg)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.usagecount is None

  def test_tuv_empty_seg(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_empty_seg")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    seg = backend.create_element("seg")
    backend.append_child(elem, seg)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.content == []

  def test_tuv_invalid_child_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_invalid_child")
    handler = TuvDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    invalid = backend.create_element("invalid")
    backend.append_child(elem, invalid)
    with pytest.raises(InvalidChildTagError):
      handler._deserialize(elem)

  def test_tuv_missing_seg_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_missing_seg")
    policy = XmlDeserializationPolicy(missing_seg=Behavior("invalid_action", WARNING))  # type: ignore
    handler = TuvDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tuv")
    backend.set_attribute(elem, "{http://www.w3.org/XML/1998/namespace}lang", "en")
    with pytest.raises(InvalidPolicyActionError):
      handler._deserialize(elem)


class TestTuDeserializer:
  """Tests for TuDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = TuDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def _create_minimal_tu(self, backend: XmlBackend) -> object:
    elem = backend.create_element("tu")
    return elem

  def test_minimal_tu(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_minimal")
    handler = TuDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tu(backend)

    result = handler._deserialize(elem)
    assert isinstance(result, Tu)
    assert result.tuid is None
    assert result.variants == []

  def test_tu_with_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_attrs")
    handler = TuDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tu")
    backend.set_attribute(elem, "tuid", "tu-001")
    backend.set_attribute(elem, "o-encoding", "utf-8")
    backend.set_attribute(elem, "datatype", "html")
    backend.set_attribute(elem, "usagecount", "10")
    backend.set_attribute(elem, "lastusagedate", "2024-01-15T10:00:00")
    backend.set_attribute(elem, "creationtool", "tool")
    backend.set_attribute(elem, "creationtoolversion", "1.0")
    backend.set_attribute(elem, "creationdate", "2024-01-01T00:00:00")
    backend.set_attribute(elem, "creationid", "user")
    backend.set_attribute(elem, "changedate", "2024-01-10T12:00:00")
    backend.set_attribute(elem, "segtype", "paragraph")
    backend.set_attribute(elem, "changeid", "editor")
    backend.set_attribute(elem, "o-tmf", "tmx")
    backend.set_attribute(elem, "srclang", "en")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.tuid == "tu-001"
    assert result.o_encoding == "utf-8"
    assert result.datatype == "html"
    assert result.usagecount == 10
    assert result.lastusagedate == datetime(2024, 1, 15, 10, 0, 0)
    assert result.creationtool == "tool"
    assert result.creationtoolversion == "1.0"
    assert result.creationdate == datetime(2024, 1, 1, 0, 0, 0)
    assert result.creationid == "user"
    assert result.changedate == datetime(2024, 1, 10, 12, 0, 0)
    assert result.segtype == Segtype.PARAGRAPH
    assert result.changeid == "editor"
    assert result.o_tmf == "tmx"
    assert result.srclang == "en"

  def test_tu_with_variants(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_variants")
    handler = TuDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "tuv":
        return Tuv(lang="en", content=["text"])
      elif tag == "prop":
        return Prop(text="value", type="type1")
      elif tag == "note":
        return Note(text="note")
      return None

    handler._set_emit(mock_emit)
    elem = backend.create_element("tu")

    prop1 = backend.create_element("prop")
    backend.append_child(elem, prop1)
    tuv1 = backend.create_element("tuv")
    backend.append_child(elem, tuv1)
    note1 = backend.create_element("note")
    backend.append_child(elem, note1)
    tuv2 = backend.create_element("tuv")
    backend.append_child(elem, tuv2)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.props) == 1
    assert len(result.notes) == 1
    assert len(result.variants) == 2

  def test_tu_extra_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_extra_text")
    handler = TuDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tu(backend)
    backend.set_text(elem, "extra text")

    with pytest.raises(ExtraTextError):
      handler._deserialize(elem)

  def test_tu_extra_text_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_tu_extra_text_ignore")
    policy = XmlDeserializationPolicy(extra_text=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = TuDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tu(backend)
    backend.set_text(elem, "extra text")

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert "extra text content" in caplog.text

  def test_tu_invalid_segtype_none_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_invalid_segtype")
    policy = XmlDeserializationPolicy(invalid_enum_value=Behavior(RaiseNoneKeep.NONE, WARNING))
    handler = TuDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tu(backend)
    backend.set_attribute(elem, "segtype", "invalid")

    result = handler._deserialize(elem)
    assert result is not None
    assert result.segtype is None

  def test_tu_invalid_child_tag_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_invalid_child")
    handler = TuDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tu(backend)
    invalid = backend.create_element("invalid")
    backend.append_child(elem, invalid)

    with pytest.raises(InvalidChildTagError):
      handler._deserialize(elem)


class TestTmxDeserializer:
  """Tests for TmxDeserializer."""

  def test_wrong_tag_returns_none_if_wrong_tag_and_policy_ignore(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_wrong_tag")
    policy = XmlDeserializationPolicy(invalid_tag=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = TmxDeserializer(backend, policy, logger)
    elem = backend.create_element("wrong")
    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)
    assert result is None
    assert "Invalid tag" in caplog.text

  def _create_minimal_tmx(self, backend: XmlBackend) -> object:
    elem = backend.create_element("tmx")
    backend.set_attribute(elem, "version", "1.4")
    return elem

  def _create_header_elem(self, backend: XmlBackend) -> object:
    header = backend.create_element("header")
    backend.set_attribute(header, "creationtool", "tool")
    backend.set_attribute(header, "creationtoolversion", "1.0")
    backend.set_attribute(header, "segtype", "sentence")
    backend.set_attribute(header, "o-tmf", "tmx")
    backend.set_attribute(header, "adminlang", "en")
    backend.set_attribute(header, "srclang", "en")
    backend.set_attribute(header, "datatype", "plaintext")
    return header

  def _create_body_elem(self, backend: XmlBackend) -> object:
    return backend.create_element("body")

  def test_minimal_tmx(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_minimal")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    result = handler._deserialize(elem)
    assert isinstance(result, Tmx)
    assert result.version == "1.4"
    assert result.header is not None
    assert result.body == []

  def test_tmx_with_tus(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_tus")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      elif tag == "tu":
        return Tu()
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)
    body = self._create_body_elem(backend)
    tu1 = backend.create_element("tu")
    backend.append_child(body, tu1)
    tu2 = backend.create_element("tu")
    backend.append_child(body, tu2)
    backend.append_child(elem, body)

    result = handler._deserialize(elem)
    assert result is not None
    assert len(result.body) == 2

  def test_tmx_missing_version_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_version")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = backend.create_element("tmx")

    with pytest.raises(RequiredAttributeMissingError):
      handler._deserialize(elem)

  def test_tmx_missing_header_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_header")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    with pytest.raises(MissingHeaderError):
      handler._deserialize(elem)

  def test_tmx_missing_header_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_tmx_missing_header_ignore")
    policy = XmlDeserializationPolicy(missing_header=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = TmxDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.header is None
    assert "Missing <header>" in caplog.text

  def test_tmx_missing_body_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_body")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)

    with pytest.raises(MissingBodyError):
      handler._deserialize(elem)

  def test_tmx_missing_body_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_tmx_missing_body_ignore")
    policy = XmlDeserializationPolicy(missing_body=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = TmxDeserializer(backend, policy, logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)

    with caplog.at_level(WARNING):
      result = handler._deserialize(elem)

    assert result is not None
    assert result.body == []
    assert "Missing <body>" in caplog.text

  def test_tmx_multiple_headers_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_header")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    header1 = self._create_header_elem(backend)
    backend.append_child(elem, header1)
    header2 = backend.create_element("header")
    backend.append_child(elem, header2)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    with pytest.raises(DuplicateChildError):
      handler._deserialize(elem)

  def test_tmx_multiple_headers_keep_first(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_header_first")
    policy = XmlDeserializationPolicy(multiple_headers=Behavior(DuplicateChildAction.KEEP_FIRST))
    handler = TmxDeserializer(backend, policy, logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header1 = self._create_header_elem(backend)
    backend.append_child(elem, header1)
    header2 = backend.create_element("header")
    backend.append_child(elem, header2)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.header is not None
    assert result.header.creationtool == "tool"

  def test_tmx_multiple_headers_keep_last(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_header_last")
    policy = XmlDeserializationPolicy(multiple_headers=Behavior(DuplicateChildAction.KEEP_LAST))
    handler = TmxDeserializer(backend, policy, logger)

    call_count = [0]

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        call_count[0] += 1
        return Header(
          creationtool=f"tool{call_count[0]}",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header1 = self._create_header_elem(backend)
    backend.append_child(elem, header1)
    header2 = backend.create_element("header")
    backend.append_child(elem, header2)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    result = handler._deserialize(elem)
    assert result is not None
    assert result.header is not None
    assert result.header.creationtool == "tool2"

  def test_tmx_multiple_body_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_body")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)
    body1 = self._create_body_elem(backend)
    backend.append_child(elem, body1)
    body2 = self._create_body_elem(backend)
    backend.append_child(elem, body2)

    with pytest.raises(DuplicateChildError):
      handler._deserialize(elem)

  def test_tmx_multiple_body_keep_last(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_body_last")
    policy = XmlDeserializationPolicy(multiple_body=Behavior(DuplicateChildAction.KEEP_LAST))
    handler = TmxDeserializer(backend, policy, logger)
    first = Tu(tuid="first")
    second = Tu(tuid="second")
    first_yielded = False

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      elif tag == "tu":
        nonlocal first_yielded
        if not first_yielded:
          first_yielded = True
          return first
        return second
      return None

    handler._set_emit(mock_emit)
    tmx = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(tmx, header)
    body1 = self._create_body_elem(backend)
    tu1 = backend.create_element("tu")
    backend.append_child(body1, tu1)
    backend.append_child(tmx, body1)
    body2 = self._create_body_elem(backend)
    tu2 = backend.create_element("tu")
    backend.append_child(body2, tu2)
    backend.append_child(tmx, body2)

    result = handler._deserialize(tmx)
    assert result is not None
    assert len(result.body) == 1
    assert result.body[0] is second

  def test_tmx_multiple_body_keep_first(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_body_first")
    policy = XmlDeserializationPolicy(multiple_body=Behavior(DuplicateChildAction.KEEP_FIRST))
    handler = TmxDeserializer(backend, policy, logger)
    first = Tu(tuid="first")
    second = Tu(tuid="second")
    first_yielded = False

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      elif tag == "tu":
        nonlocal first_yielded
        if not first_yielded:
          first_yielded = True
          return first
        return second
      return None

    handler._set_emit(mock_emit)
    tmx = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(tmx, header)
    body1 = self._create_body_elem(backend)
    tu1 = backend.create_element("tu")
    backend.append_child(body1, tu1)
    backend.append_child(tmx, body1)
    body2 = self._create_body_elem(backend)
    tu2 = backend.create_element("tu")
    backend.append_child(body2, tu2)
    backend.append_child(tmx, body2)

    result = handler._deserialize(tmx)
    assert result is not None
    assert len(result.body) == 1
    assert result.body[0] is first

  def test_tmx_extra_text_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_extra_text")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    backend.set_text(elem, "extra text")

    with pytest.raises(ExtraTextError):
      handler._deserialize(elem)

  def test_tmx_invalid_child_in_body(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_invalid_body_child")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)

    def mock_emit(e):
      tag = backend.get_tag(e)
      if tag == "header":
        return Header(
          creationtool="tool",
          creationtoolversion="1.0",
          segtype=Segtype.SENTENCE,
          o_tmf="tmx",
          adminlang="en",
          srclang="en",
          datatype="plaintext",
        )
      return None

    handler._set_emit(mock_emit)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)
    body = self._create_body_elem(backend)
    invalid = backend.create_element("invalid")
    backend.append_child(body, invalid)
    backend.append_child(elem, body)

    with pytest.raises(InvalidChildTagError):
      handler._deserialize(elem)

  def test_tmx_invalid_child_tag_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_invalid_child")
    handler = TmxDeserializer(backend, XmlDeserializationPolicy(), logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    invalid = backend.create_element("invalid")
    backend.append_child(elem, invalid)

    with pytest.raises(InvalidChildTagError):
      handler._deserialize(elem)

  def test_tmx_multiple_header_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_header")
    policy = XmlDeserializationPolicy(multiple_headers=Behavior("invalid_action", WARNING))  # type: ignore
    handler = TmxDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    header1 = self._create_header_elem(backend)
    backend.append_child(elem, header1)
    header2 = backend.create_element("header")
    backend.append_child(elem, header2)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    with pytest.raises(InvalidPolicyActionError):
      handler._deserialize(elem)

  def test_tmx_multiple_body_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_multi_body")
    policy = XmlDeserializationPolicy(multiple_body=Behavior("invalid_action", WARNING))  # type: ignore
    handler = TmxDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)
    body1 = self._create_body_elem(backend)
    backend.append_child(elem, body1)
    body2 = self._create_body_elem(backend)
    backend.append_child(elem, body2)

    with pytest.raises(InvalidPolicyActionError):
      handler._deserialize(elem)

  def test_tmx_missing_header_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_header")
    policy = XmlDeserializationPolicy(missing_header=Behavior("invalid_action", WARNING))  # type: ignore
    handler = TmxDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    body = self._create_body_elem(backend)
    backend.append_child(elem, body)

    with pytest.raises(InvalidPolicyActionError):
      handler._deserialize(elem)

  def test_tmx_missing_body_invalid_action_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_body")
    policy = XmlDeserializationPolicy(missing_body=Behavior("invalid_action", WARNING))  # type: ignore
    handler = TmxDeserializer(backend, policy, logger)
    handler._set_emit(lambda e: None)
    elem = self._create_minimal_tmx(backend)
    header = self._create_header_elem(backend)
    backend.append_child(elem, header)

    with pytest.raises(InvalidPolicyActionError):
      handler._deserialize(elem)
