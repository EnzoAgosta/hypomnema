from unittest.mock import Mock
import pytest
from hypomnema import (
  Tmx,
  Header,
  Tu,
  Segtype,
  XmlDeserializationError,
  LxmlBackend,
  XmlSerializationError,
  SerializationPolicy,
  PolicyValue,
)
from hypomnema.api import load, save
from hypomnema.api.helpers import create_tmx, create_header, create_tu, create_tuv


class TestLoadSaveHappy:
  @pytest.fixture(autouse=True)
  def setup(self, backend):
    self.backend = backend
    self.tmx = create_tmx(
      header=create_header(
        creationtool="test-tool",
        creationtoolversion="1.0",
        segtype=Segtype.SENTENCE,
        srclang="en",
        datatype="plainText",
      ),
      body=[
        create_tu(
          tuid="tu1",
          srclang="en",
          variants=[
            create_tuv(lang="en", content=["Hello"]),
            create_tuv(lang="fr", content=["Bonjour"]),
          ],
        ),
        create_tu(
          tuid="tu2",
          srclang="en",
          variants=[
            create_tuv(lang="en", content=["World"]),
            create_tuv(lang="de", content=["Welt"]),
          ],
        ),
      ],
    )

  def test_save_and_load_roundtrip(self, tmp_path):
    file = tmp_path / "test.tmx"
    save(self.tmx, file)

    loaded = load(file)
    assert isinstance(loaded, Tmx)
    assert loaded.header.creationtool == "test-tool"
    assert len(loaded.body) == 2
    assert loaded.body[0].tuid == "tu1"
    assert loaded.body[1].tuid == "tu2"

  def test_save_with_custom_encoding(self, tmp_path):
    file = tmp_path / "test.tmx"
    save(self.tmx, file, encoding="utf-8")

    loaded = load(file)
    assert isinstance(loaded, Tmx)
    assert len(loaded.body) == 2

  def test_load_filter_tu(self, tmp_path):
    file = tmp_path / "test.tmx"
    save(self.tmx, file)

    elements = list(load(file, filter="tu"))
    assert len(elements) == 2
    assert all(isinstance(e, Tu) for e in elements)

  def test_load_filter_multiple_tags(self, tmp_path):
    file = tmp_path / "test.tmx"
    save(self.tmx, file)

    elements = list(load(file, filter=["tu", "header"]))
    assert len(elements) == 3  # 2 TUs + 1 header
    headers = [e for e in elements if isinstance(e, Header)]
    tus = [e for e in elements if isinstance(e, Tu)]
    assert len(headers) == 1
    assert len(tus) == 2

  def test_load_filter_string(self, tmp_path):
    file = tmp_path / "test.tmx"
    save(self.tmx, file)

    elements = list(load(file, filter="tu"))
    assert len(elements) == 2

  def test_load_generator_is_lazy(self, tmp_path):
    file = tmp_path / "test.tmx"
    save(self.tmx, file)

    gen = load(file, filter="tu")
    assert hasattr(gen, "__next__") or hasattr(gen, "__iter__")

  def test_save_creates_parent_directories(self, tmp_path):
    tmx = create_tmx(header=create_header(creationtool="test", srclang="en", datatype="txt"))
    path = tmp_path / "nested" / "deep"
    save(tmx, path)
    assert path.exists()

  def test_save_with_lxml_backend(self):
    save(self.tmx, "/tmp/test.tmx", backend=LxmlBackend())

  def test_load_nonexistent_file_raises(self):
    with pytest.raises(FileNotFoundError):
      load("/nonexistent/path/file.tmx")

  def test_load_directory_raises(self):
    with pytest.raises(IsADirectoryError):
      load("/tmp")


class TestLoadSaveError:
  def test_save_invalid_type_raises(self):
    with pytest.raises(TypeError, match="Root element is not a Tmx"):
      save("not a tmx", "/tmp/test.tmx")  # type: ignore[arg-type]

  def test_save_serializer_returns_none_raises(self, tmp_path):
    tmx = Mock(spec=Tmx)
    file = tmp_path / "test.tmx"
    with pytest.raises(XmlSerializationError, match="serializer returned None"):
      save(tmx, file, policy=SerializationPolicy(missing_handler=PolicyValue("ignore", 10)))

  def test_load_invalid_root_element_raises(self, tmp_path):
    file = tmp_path / "test.tmx"
    file.write_text("<nope/>")
    with pytest.raises(XmlDeserializationError, match="Root element is not a tmx"):
      load(file)