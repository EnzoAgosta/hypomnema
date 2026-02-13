import subprocess
import sys
import textwrap
import pytest


@pytest.mark.skipif(
  sys.platform == "win32", reason="Subprocess isolation test; shell behavior differs on Windows"
)
def test_lxml_missing_fallback():
  """
  Test that LxmlBackend is set to None and a warning is raised if lxml
  cannot be imported.

  Note: This runs in a subprocess to safely manipulate sys.modules.
  Coverage is intentionally skipped for this test due to subprocess isolation.
  """
  code = textwrap.dedent("""
        import sys
        import warnings

        # Simulate lxml absence
        sys.modules['lxml'] = None

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import hypomnema.xml.backends as backends

            assert len(w) == 1
            assert "lxml not installed" in str(w[0].message)
            assert backends.LxmlBackend is None
    """)

  result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

  assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
