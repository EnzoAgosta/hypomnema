"""Exercise the built distribution independently of the source checkout."""

import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


def test_wheel_can_read_and_write_tmx(tmp_path: Path) -> None:
  """Include the DTD and use it from an unpacked wheel in an isolated process."""
  repository = Path(__file__).resolve().parents[1]
  project = tmp_path / "project"
  project.mkdir()
  for name in ("pyproject.toml", "README.md", "LICENSE"):
    shutil.copy2(repository / name, project / name)
  shutil.copytree(repository / "src", project / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
  subprocess.run(["uv", "build", "--wheel", "--directory", str(project)], check=True, capture_output=True, text=True)
  installed = tmp_path / "installed"
  with ZipFile(next((project / "dist").glob("*.whl"))) as wheel:
    assert "hypomnema/resources/tmx14.dtd" in wheel.namelist()
    wheel.extractall(installed)
  subprocess.run(
    [
      sys.executable,
      "-I",
      "-c",
      """
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import hypomnema
from hypomnema.io import TmxReader, TmxWriter
from hypomnema.models import Header, TranslationUnit, TranslationUnitVariant

assert Path(hypomnema.__file__).is_relative_to(sys.argv[1])
header = Header(creationtool="test", creationtoolversion="1", segtype="sentence",
                o_tmf="test", adminlang="en", srclang="en", datatype="plaintext")
unit = TranslationUnit(variants=[TranslationUnitVariant(xml_lang="en", content=["hello"])])
output = BytesIO()
with TmxWriter(output, header=header) as writer:
    writer.write(unit)
output.seek(0)
with TmxReader(output) as reader:
    assert reader.read_header() == header
    assert list(reader) == [unit]
""",
      str(installed),
    ],
    check=True,
    capture_output=True,
    text=True,
    cwd=tmp_path,
  )
