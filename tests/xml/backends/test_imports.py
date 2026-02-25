import importlib
from unittest.mock import patch

import pytest

import hypomnema.xml.backends


def test_lxml_unavailable_fallback():
  lxml_mocks = {"lxml": None, "lxml.etree": None, "hypomnema.xml.backends.lxml": None}

  try:
    with (
      patch.dict("sys.modules", lxml_mocks),
      pytest.warns(UserWarning, match="lxml not installed"),
    ):
      importlib.reload(hypomnema.xml.backends)

    assert hypomnema.xml.backends.LxmlBackend is None
  finally:
    importlib.reload(hypomnema.xml.backends)
