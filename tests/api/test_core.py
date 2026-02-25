"""Tests for the high-level API (load/dump functions).

Tests the main entry points for loading and saving TMX files, including
both full document loading and streaming mode.
"""

from logging import getLogger
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hypomnema.api.core import dump, load
from hypomnema.api.helpers import (
  create_bpt,
  create_header,
  create_hi,
  create_ph,
  create_sub,
  create_tmx,
  create_tu,
  create_tuv,
  iter_text,
)
from hypomnema.base.types import Note, Segtype, Tmx, Tu, Tuv
from hypomnema.xml import deserialization, serialization
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.deserialization import Deserializer
from hypomnema.xml.policy import XmlDeserializationPolicy
from hypomnema.xml.serialization import Serializer


class TestLoad:
  """Tests for the load function."""

  def test_load_full_document(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    loaded = load(tmx_file, backend=backend)
    assert isinstance(loaded, Tmx)
    assert loaded.header.creationtool == "hypomnema"

  def test_load_with_encoding(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, encoding="utf-8", backend=backend)

    loaded = load(tmx_file, encoding="utf-8", backend=backend)
    assert isinstance(loaded, Tmx)

  def test_load_with_custom_deserializer(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    custom_deserializer = Deserializer(backend)
    loaded = load(tmx_file, backend=backend, deserializer=custom_deserializer)
    assert isinstance(loaded, Tmx)

  def test_load_with_custom_policy(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    policy = XmlDeserializationPolicy()
    loaded = load(tmx_file, backend=backend, deserializer_policy=policy)
    assert isinstance(loaded, Tmx)

  def test_load_with_custom_logger(
    self, backend: XmlBackend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    logger = getLogger("test_load")
    captured: dict[str, object] = {}
    original = deserialization.Deserializer

    class SpyDeserializer(original):  # type: ignore[valid-type, misc]
      def __init__(self, *args, **kwargs):
        captured["logger"] = kwargs.get("logger")
        super().__init__(*args, **kwargs)

    monkeypatch.setattr(deserialization, "Deserializer", SpyDeserializer)
    loaded = load(tmx_file, backend=backend, deserializer_logger=logger)
    assert isinstance(loaded, Tmx)
    assert captured["logger"] is logger

  def test_load_file_not_found(self, backend: XmlBackend) -> None:
    with pytest.raises(FileNotFoundError):
      load("/nonexistent/path.tmx", backend=backend)

  def test_load_is_directory(self, backend: XmlBackend, tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
      load(tmp_path, backend=backend)

  def test_load_non_tmx_root_raises(self, backend: XmlBackend, tmp_path: Path) -> None:
    non_tmx = tmp_path / "not_tmx.xml"
    root = backend.create_element("not_tmx")
    backend.write(root, non_tmx)

    with pytest.raises(ValueError, match="Root element is not a tmx"):
      load(non_tmx, backend=backend)

  def test_load_streaming_with_filter(self, backend: XmlBackend, tmp_path: Path) -> None:
    tu1 = create_tu(
      variants=[create_tuv("en", content="Hello"), create_tuv("fr", content="Bonjour")]
    )
    tu2 = create_tu(variants=[create_tuv("en", content="World"), create_tuv("fr", content="Monde")])
    tmx = create_tmx(body=[tu1, tu2])
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    loaded_tus = list(load(tmx_file, filter="tu", backend=backend))
    assert len(loaded_tus) == 2
    assert all(isinstance(tu, Tu) for tu in loaded_tus)

  def test_load_streaming_with_multiple_filters(self, backend: XmlBackend, tmp_path: Path) -> None:
    tu = create_tu(variants=[create_tuv("en", content="Hello")])
    tmx = create_tmx(body=[tu])
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    loaded = list(load(tmx_file, filter=["tu", "tuv"], backend=backend))
    assert len(loaded) == 2
    types = [type(item) for item in loaded]
    assert Tuv in types
    assert Tu in types

  def test_load_with_backend_logger(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    logger = getLogger("test_backend_logger")
    loaded = load(tmx_file, backend=backend, backend_logger=logger)
    assert isinstance(loaded, Tmx)


class TestDump:
  """Tests for the dump function."""

  def test_dump_creates_file(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "output.tmx"

    dump(tmx, tmx_file, backend=backend)
    assert tmx_file.exists()

  def test_dump_creates_parent_directories(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "subdir" / "nested" / "output.tmx"

    dump(tmx, tmx_file, backend=backend)
    assert tmx_file.exists()

  def test_dump_with_encoding(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "output.tmx"

    dump(tmx, tmx_file, encoding="utf-16", backend=backend)
    assert tmx_file.exists()

  def test_dump_non_tmx_raises(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx_file = tmp_path / "output.tmx"

    with pytest.raises(TypeError, match="Root element is not a Tmx"):
      dump("not a tmx", tmx_file, backend=backend)  # type: ignore[arg-type]

  def test_dump_with_custom_logger(
    self, backend: XmlBackend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "output.tmx"
    logger = getLogger("test_dump")
    captured: dict[str, object] = {}
    original = serialization.Serializer

    class SpySerializer(original):  # type: ignore[valid-type, misc]
      def __init__(self, *args, **kwargs):
        captured["logger"] = kwargs.get("logger")
        super().__init__(*args, **kwargs)

    monkeypatch.setattr(serialization, "Serializer", SpySerializer)

    dump(tmx, tmx_file, backend=backend, serializer_logger=logger)
    assert tmx_file.exists()
    assert captured["logger"] is logger

  def test_dump_with_custom_backend_logger(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "output.tmx"
    logger = getLogger("test_dump_backend")

    dump(tmx, tmx_file, backend=backend, backend_logger=logger)
    assert tmx_file.exists()

  def test_dump_and_load_roundtrip(self, backend: XmlBackend, tmp_path: Path) -> None:
    header = create_header(
      creationtool="test-tool",
      creationtoolversion="1.0",
      segtype=Segtype.SENTENCE,
      adminlang="en",
      srclang="en",
      datatype="html",
    )
    tu = create_tu(
      tuid="tu-001",
      variants=[create_tuv("en", content="Hello World"), create_tuv("fr", content="Bonjour Monde")],
    )
    tmx = create_tmx(header=header, body=[tu])
    tmx_file = tmp_path / "roundtrip.tmx"

    dump(tmx, tmx_file, backend=backend)
    loaded = load(tmx_file, backend=backend)

    assert loaded.header.creationtool == "test-tool"
    assert loaded.header.segtype == Segtype.SENTENCE
    assert len(loaded.body) == 1
    assert loaded.body[0].tuid == "tu-001"
    assert len(loaded.body[0].variants) == 2

  def test_dump_and_load_roundtrip_with_deep_inline_nesting(
    self, backend: XmlBackend, tmp_path: Path
  ) -> None:
    deep_inline = create_bpt(
      1,
      content=[
        "code ",
        create_sub(
          content=[
            "sub1 ",
            create_ph(
              content=["ph ", create_sub(content=["sub2 ", create_hi(content=["hi text"])])]
            ),
          ]
        ),
      ],
    )
    tu = create_tu(
      variants=[
        create_tuv("en", content=["A ", deep_inline, " Z"]),
        create_tuv("fr", content=["B"]),
      ]
    )
    tmx = create_tmx(body=[tu])
    tmx_file = tmp_path / "roundtrip-deep.tmx"

    dump(tmx, tmx_file, backend=backend)
    loaded = load(tmx_file, backend=backend)

    text_parts = list(iter_text(loaded.body[0].variants[0], recurse_inside_ignored=True))
    assert "sub2 " in text_parts
    assert "hi text" in text_parts

  def test_dump_serializer_returns_none(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "output.tmx"

    mock_serializer = MagicMock(spec=Serializer)
    mock_serializer.serialize.return_value = None

    with pytest.raises(ValueError, match="serializer returned None"):
      dump(tmx, tmx_file, backend=backend, serializer=mock_serializer)


class TestLoadEdgeCases:
  """Tests for edge cases in load function."""

  def test_load_root_deserializes_to_non_tmx(self, backend: XmlBackend, tmp_path: Path) -> None:
    tmx = create_tmx()
    tmx_file = tmp_path / "test.tmx"
    dump(tmx, tmx_file, backend=backend)

    mock_deserializer = MagicMock(spec=Deserializer)
    mock_deserializer.deserialize.return_value = Note(text="not a tmx")

    with pytest.raises(ValueError, match="root element did not deserialize to a Tmx"):
      load(tmx_file, backend=backend, deserializer=mock_deserializer)

  def test_load_streaming_skips_elements_deserialized_as_none(
    self, backend: XmlBackend, tmp_path: Path
  ) -> None:
    tmx = create_tmx(body=[create_tu(variants=[create_tuv("en", content="Hello")]), create_tu()])
    tmx_file = tmp_path / "skip_none.tmx"
    dump(tmx, tmx_file, backend=backend)

    first_tu = Tu(tuid="only")
    mock_deserializer = MagicMock(spec=Deserializer)
    mock_deserializer.deserialize.side_effect = [first_tu, None]

    streamed = list(load(tmx_file, filter="tu", backend=backend, deserializer=mock_deserializer))
    assert streamed == [first_tu]

  def test_load_streaming_unknown_filter_returns_empty(
    self, backend: XmlBackend, tmp_path: Path
  ) -> None:
    tmx = create_tmx(body=[create_tu(variants=[create_tuv("en", content="Hello")])])
    tmx_file = tmp_path / "unknown_filter.tmx"
    dump(tmx, tmx_file, backend=backend)

    streamed = list(load(tmx_file, filter="nonexistent-tag", backend=backend))
    assert streamed == []

  def test_load_streaming_zero_tu_file_returns_empty(
    self, backend: XmlBackend, tmp_path: Path
  ) -> None:
    tmx = create_tmx(body=[])
    tmx_file = tmp_path / "zero_tu.tmx"
    dump(tmx, tmx_file, backend=backend)

    streamed = list(load(tmx_file, filter="tu", backend=backend))
    assert streamed == []

  def test_load_streaming_large_file(self, backend: XmlBackend, tmp_path: Path) -> None:
    total = 1500
    body = [
      create_tu(tuid=f"tu-{i}", variants=[create_tuv("en", content=f"text-{i}")])
      for i in range(total)
    ]
    tmx = create_tmx(body=body)
    tmx_file = tmp_path / "large.tmx"
    dump(tmx, tmx_file, backend=backend)

    streamed = list(load(tmx_file, filter="tu", backend=backend))
    assert len(streamed) == total

  def test_load_empty_file_raises_parse_error(self, backend: XmlBackend, tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.tmx"
    empty_file.write_text("")
    with pytest.raises(Exception):
      load(empty_file, backend=backend)
