import importlib
from unittest.mock import patch

import pytest

import hypomnema.xml.backends


def test_lxml_unavailable_fallback():
  # Make any import of anything under "lxml" raise ImportError
  lxml_mocks = {"lxml": None, "lxml.etree": None, "hypomnema.xml.backends.lxml": None}

  with patch.dict("sys.modules", lxml_mocks):
    with pytest.warns(UserWarning, match="lxml not installed"):
      importlib.reload(hypomnema.xml.backends)

    assert hypomnema.xml.backends.LxmlBackend is None

  # Reload again to restore normal state for other tests
  importlib.reload(hypomnema.xml.backends)
