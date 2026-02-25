"""Tests for structure element serializers.

Tests serialization of TMX structural elements:
- HeaderSerializer: Header dataclasses
- TuvSerializer: Tuv dataclasses
- TuSerializer: Tu dataclasses
- TmxSerializer: Tmx dataclasses
"""

from datetime import datetime
from logging import WARNING, getLogger
from typing import cast

import pytest

from hypomnema.base.errors import InvalidAttributeTypeError, RequiredAttributeMissingError
from hypomnema.base.types import Bpt, Header, Note, Prop, Segtype, Tmx, Tu, Tuv
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.policy import Behavior, RaiseIgnore, RaiseIgnoreForce, XmlSerializationPolicy
from hypomnema.xml.serialization import HeaderSerializer, TmxSerializer, TuSerializer, TuvSerializer


class TestHeaderSerializer:
  """Tests for HeaderSerializer."""

  def _create_minimal_header(self) -> Header:
    return Header(
      creationtool="test-tool",
      creationtoolversion="1.0",
      segtype=Segtype.SENTENCE,
      o_tmf="tmx",
      adminlang="en",
      srclang="en",
      datatype="plaintext",
    )

  def test_minimal_header(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_minimal")
    handler = HeaderSerializer(backend, XmlSerializationPolicy(), logger)
    obj = self._create_minimal_header()

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "header"
    assert backend.get_attribute(result, "creationtool") == "test-tool"
    assert backend.get_attribute(result, "creationtoolversion") == "1.0"
    assert backend.get_attribute(result, "segtype") == "sentence"
    assert backend.get_attribute(result, "o-tmf") == "tmx"
    assert backend.get_attribute(result, "adminlang") == "en"
    assert backend.get_attribute(result, "srclang") == "en"
    assert backend.get_attribute(result, "datatype") == "plaintext"

  def test_header_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_all")
    handler = HeaderSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype=Segtype.SENTENCE,
      o_tmf="tmx",
      adminlang="en",
      srclang="en",
      datatype="plaintext",
      o_encoding="utf-8",
      creationdate=datetime(2024, 1, 15, 10, 30, 0),
      creationid="user1",
      changedate=datetime(2024, 1, 20, 15, 0, 0),
      changeid="user2",
    )

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "o-encoding") == "utf-8"
    assert backend.get_attribute(result, "creationdate") == "20240115T103000Z"
    assert backend.get_attribute(result, "creationid") == "user1"
    assert backend.get_attribute(result, "changedate") == "20240120T150000Z"
    assert backend.get_attribute(result, "changeid") == "user2"

  def test_header_with_props_and_notes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_children")
    handler = HeaderSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype=Segtype.SENTENCE,
      o_tmf="tmx",
      adminlang="en",
      srclang="en",
      datatype="plaintext",
      props=[Prop(text="v1", type="t1"), Prop(text="v2", type="t2")],
      notes=[Note(text="note")],
    )

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 3

  def test_header_missing_required_attribute_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_missing_attr")
    handler = HeaderSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Header, self._create_minimal_header())
    obj.creationtool = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_header_invalid_segtype_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_invalid_segtype")
    handler = HeaderSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Header, self._create_minimal_header())
    obj.segtype = "invalid"  # type: ignore[assignment]

    with pytest.raises(InvalidAttributeTypeError):
      handler._serialize(obj)

  def test_header_invalid_datetime_ignored(self, backend: XmlBackend) -> None:
    logger = getLogger("test_header_invalid_datetime")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = HeaderSerializer(backend, policy, logger)
    obj = cast(Header, self._create_minimal_header())
    obj.creationdate = "not-a-date"  # type: ignore[assignment]

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "creationdate") is None

  def test_header_wrong_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_header_wrong_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = HeaderSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._serialize(Note(text="not a header"))  # type: ignore[arg-type]

    assert result is None


class TestTuvSerializer:
  """Tests for TuvSerializer."""

  def _create_minimal_tuv(self) -> Tuv:
    return Tuv(lang="en", content=["text"])

  def test_minimal_tuv(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_minimal")
    handler = TuvSerializer(backend, XmlSerializationPolicy(), logger)
    obj = self._create_minimal_tuv()

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "tuv"
    assert backend.get_attribute(result, "{http://www.w3.org/XML/1998/namespace}lang") == "en"
    children = list(backend.iter_children(result))
    assert len(children) == 1
    assert backend.get_tag(children[0]) == "seg"
    assert backend.get_text(children[0]) == "text"

  def test_tuv_with_all_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_all")
    handler = TuvSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Tuv(
      lang="en",
      o_encoding="utf-8",
      datatype="html",
      usagecount=5,
      lastusagedate=datetime(2024, 1, 15, 10, 0, 0),
      creationtool="tool",
      creationtoolversion="1.0",
      creationdate=datetime(2024, 1, 1, 0, 0, 0),
      creationid="user",
      changedate=datetime(2024, 1, 10, 12, 0, 0),
      changeid="editor",
      o_tmf="tmx",
      content=["text"],
    )

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "o-encoding") == "utf-8"
    assert backend.get_attribute(result, "datatype") == "html"
    assert backend.get_attribute(result, "usagecount") == "5"
    assert backend.get_attribute(result, "lastusagedate") == "20240115T100000Z"
    assert backend.get_attribute(result, "creationtool") == "tool"
    assert backend.get_attribute(result, "creationtoolversion") == "1.0"
    assert backend.get_attribute(result, "creationdate") == "20240101T000000Z"
    assert backend.get_attribute(result, "creationid") == "user"
    assert backend.get_attribute(result, "changedate") == "20240110T120000Z"
    assert backend.get_attribute(result, "changeid") == "editor"
    assert backend.get_attribute(result, "o-tmf") == "tmx"

  def test_tuv_with_props_and_notes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_children")
    handler = TuvSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = Tuv(
      lang="en", props=[Prop(text="v1", type="t1")], notes=[Note(text="note")], content=["text"]
    )

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 3

  def test_tuv_with_inline_content(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_content")
    handler = TuvSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      return backend.create_element("bpt")

    handler._set_emit(mock_emit)
    obj = Tuv(lang="en", content=["text ", Bpt(i=1, content=[]), " more"])

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    seg = children[0]
    assert backend.get_tag(seg) == "seg"
    assert backend.get_text(seg) == "text "
    seg_children = list(backend.iter_children(seg))
    assert len(seg_children) == 1

  def test_tuv_missing_lang_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_missing_lang")
    handler = TuvSerializer(backend, XmlSerializationPolicy(), logger)
    obj = self._create_minimal_tuv()
    obj.lang = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_tuv_invalid_usagecount_ignored(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_invalid_usagecount")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = TuvSerializer(backend, policy, logger)
    obj = self._create_minimal_tuv()
    obj.usagecount = "not-an-int"  # type: ignore[assignment]

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "usagecount") is None

  def test_tuv_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tuv_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = TuvSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None


class TestTuSerializer:
  """Tests for TuSerializer."""

  def _create_minimal_tu(self) -> Tu:
    return Tu()

  def test_minimal_tu(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_minimal")
    handler = TuSerializer(backend, XmlSerializationPolicy(), logger)
    obj = self._create_minimal_tu()

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "tu"

  def test_tu_with_attributes(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_attrs")
    handler = TuSerializer(backend, XmlSerializationPolicy(), logger)
    obj = Tu(
      tuid="tu-001",
      o_encoding="utf-8",
      datatype="html",
      usagecount=10,
      lastusagedate=datetime(2024, 1, 15, 10, 0, 0),
      creationtool="tool",
      creationtoolversion="1.0",
      creationdate=datetime(2024, 1, 1, 0, 0, 0),
      creationid="user",
      changedate=datetime(2024, 1, 10, 12, 0, 0),
      segtype=Segtype.PARAGRAPH,
      changeid="editor",
      o_tmf="tmx",
      srclang="en",
    )

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "tuid") == "tu-001"
    assert backend.get_attribute(result, "o-encoding") == "utf-8"
    assert backend.get_attribute(result, "datatype") == "html"
    assert backend.get_attribute(result, "usagecount") == "10"
    assert backend.get_attribute(result, "lastusagedate") == "20240115T100000Z"
    assert backend.get_attribute(result, "creationtool") == "tool"
    assert backend.get_attribute(result, "creationtoolversion") == "1.0"
    assert backend.get_attribute(result, "creationdate") == "20240101T000000Z"
    assert backend.get_attribute(result, "creationid") == "user"
    assert backend.get_attribute(result, "changedate") == "20240110T120000Z"
    assert backend.get_attribute(result, "segtype") == "paragraph"
    assert backend.get_attribute(result, "changeid") == "editor"
    assert backend.get_attribute(result, "o-tmf") == "tmx"
    assert backend.get_attribute(result, "srclang") == "en"

  def test_tu_with_variants(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_variants")
    handler = TuSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = Tu(
      props=[Prop(text="v1", type="t1")],
      notes=[Note(text="note")],
      variants=[Tuv(lang="en", content=["text"]), Tuv(lang="fr", content=["texte"])],
    )

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    assert len(children) == 4

  def test_tu_invalid_segtype_ignored(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_invalid_segtype")
    policy = XmlSerializationPolicy(invalid_attribute_type=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = TuSerializer(backend, policy, logger)
    obj = cast(Tu, self._create_minimal_tu())
    obj.segtype = "invalid"  # type: ignore[assignment]

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "segtype") is None

  def test_tu_invalid_type_ignored_with_policy(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tu_invalid_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = TuSerializer(backend, policy, logger)
    obj = 12
    result = handler._serialize(obj)  # type: ignore[arg-type]
    assert result is None


class TestTmxSerializer:
  """Tests for TmxSerializer."""

  def _create_minimal_tmx(self) -> Tmx:
    return Tmx(
      header=Header(
        creationtool="tool",
        creationtoolversion="1.0",
        segtype=Segtype.SENTENCE,
        o_tmf="tmx",
        adminlang="en",
        srclang="en",
        datatype="plaintext",
      ),
      body=[],
    )

  def test_minimal_tmx(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_minimal")
    handler = TmxSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = self._create_minimal_tmx()

    result = handler._serialize(obj)
    assert backend.get_tag(result) == "tmx"
    assert backend.get_attribute(result, "version") == "1.4"
    children = list(backend.iter_children(result))
    assert len(children) == 2
    assert backend.get_tag(children[0]) == "header"
    assert backend.get_tag(children[1]) == "body"

  def test_tmx_with_tus(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_tus")
    handler = TmxSerializer(backend, XmlSerializationPolicy(), logger)

    def mock_emit(o):
      tag = type(o).__name__.lower()
      return backend.create_element(tag)

    handler._set_emit(mock_emit)
    obj = Tmx(
      header=Header(
        creationtool="tool",
        creationtoolversion="1.0",
        segtype=Segtype.SENTENCE,
        o_tmf="tmx",
        adminlang="en",
        srclang="en",
        datatype="plaintext",
      ),
      body=[Tu(), Tu()],
    )

    result = handler._serialize(obj)
    children = list(backend.iter_children(result))
    body = children[1]
    body_children = list(backend.iter_children(body))
    assert len(body_children) == 2

  def test_tmx_missing_version_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_version")
    handler = TmxSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("test"))
    obj = cast(Tmx, self._create_minimal_tmx())
    obj.version = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_tmx_missing_header_raises(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_missing_header")
    handler = TmxSerializer(backend, XmlSerializationPolicy(), logger)
    obj = cast(Tmx, self._create_minimal_tmx())
    obj.header = None  # type: ignore[assignment]

    with pytest.raises(RequiredAttributeMissingError):
      handler._serialize(obj)

  def test_tmx_missing_header_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_tmx_missing_header_ignore")
    policy = XmlSerializationPolicy(
      required_attribute_missing=Behavior(RaiseIgnore.IGNORE, WARNING)
    )
    handler = TmxSerializer(backend, policy, logger)
    handler._set_emit(lambda o: backend.create_element("test"))
    obj = cast(Tmx, self._create_minimal_tmx())
    obj.header = None  # type: ignore[assignment]

    with caplog.at_level(WARNING):
      result = handler._serialize(obj)

    assert result is not None
    assert "Required attribute" in caplog.text

  def test_tmx_wrong_type_ignored_with_policy(
    self, backend: XmlBackend, caplog: pytest.LogCaptureFixture
  ) -> None:
    logger = getLogger("test_tmx_wrong_type")
    policy = XmlSerializationPolicy(invalid_element_type=Behavior(RaiseIgnoreForce.IGNORE, WARNING))
    handler = TmxSerializer(backend, policy, logger)

    with caplog.at_level(WARNING):
      result = handler._serialize(Note(text="not a tmx"))  # type: ignore[arg-type]

    assert result is None

  def test_tmx_custom_version(self, backend: XmlBackend) -> None:
    logger = getLogger("test_tmx_custom_version")
    handler = TmxSerializer(backend, XmlSerializationPolicy(), logger)
    handler._set_emit(lambda o: backend.create_element("test"))
    obj = Tmx(
      version="1.5",
      header=Header(
        creationtool="tool",
        creationtoolversion="1.0",
        segtype=Segtype.SENTENCE,
        o_tmf="tmx",
        adminlang="en",
        srclang="en",
        datatype="plaintext",
      ),
    )

    result = handler._serialize(obj)
    assert backend.get_attribute(result, "version") == "1.5"
