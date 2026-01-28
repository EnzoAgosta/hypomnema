from typing import Any, cast

import pytest

from hypomnema import XmlBackend
from hypomnema.base.errors import (AttributeDeserializationError,
                                   XmlDeserializationError)
from hypomnema.base.types import Ph, Segtype, Tuv
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.policy import XmlPolicy
from hypomnema.xml.serialization.serializer import Serializer
from tests.conftest import _append_child, _make_elem
from tests.strict_backend import StrictBackend


def test_backend_parity_serialize_deserialize_tuv(backend: XmlBackend):
  serializer = Serializer(backend, policy=XmlPolicy())
  deserializer = Deserializer(backend, policy=XmlPolicy())

  tuv = cast(Any, Tuv(lang="en", content=["Hello ", Ph(x=1, content=["text"]), "World"]))
  element = serializer.serialize(tuv)
  result = deserializer.deserialize(element)

  assert result == tuv


def test_strict_backend_missing_header(backend: XmlBackend):
  if not isinstance(backend, StrictBackend):
    pytest.skip("StrictBackend only")

  deserializer = Deserializer(backend, policy=XmlPolicy())

  tmx_elem = _make_elem(backend, "tmx", version="1.4")

  with pytest.raises(XmlDeserializationError, match="missing a <header>"):
    deserializer.deserialize(tmx_elem)


def test_strict_backend_missing_seg(backend: XmlBackend):
  if not isinstance(backend, StrictBackend):
    pytest.skip("StrictBackend only")

  deserializer = Deserializer(backend, policy=XmlPolicy())

  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})

  with pytest.raises(XmlDeserializationError, match="missing a <seg>"):
    deserializer.deserialize(tuv_elem)


def test_strict_backend_missing_required_attribute(backend: XmlBackend):
  if not isinstance(backend, StrictBackend):
    pytest.skip("StrictBackend only")

  deserializer = Deserializer(backend, policy=XmlPolicy())

  prop_elem = _make_elem(backend, "prop", text="value")

  with pytest.raises(AttributeDeserializationError, match="Required attribute"):
    deserializer.deserialize(prop_elem)


def test_strict_backend_invalid_attribute_value(backend: XmlBackend):
  if not isinstance(backend, StrictBackend):
    pytest.skip("StrictBackend only")

  deserializer = Deserializer(backend, policy=XmlPolicy())

  header_elem = _make_elem(
    backend,
    "header",
    creationtool="tool",
    creationtoolversion="1",
    segtype="not-valid",
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )

  with pytest.raises(AttributeDeserializationError, match="not a valid enum"):
    deserializer.deserialize(header_elem)


def test_strict_backend_invalid_child(backend: XmlBackend):
  if not isinstance(backend, StrictBackend):
    pytest.skip("StrictBackend only")

  deserializer = Deserializer(backend, policy=XmlPolicy())

  header_elem = _make_elem(
    backend,
    "header",
    creationtool="tool",
    creationtoolversion="1",
    segtype=Segtype.BLOCK.value,
    **{"o-tmf": "tmf", "adminlang": "en", "srclang": "en", "datatype": "plain"},
  )
  _append_child(backend, header_elem, _make_elem(backend, "bad"))

  with pytest.raises(XmlDeserializationError, match="Invalid child element"):
    deserializer.deserialize(header_elem)


def test_strict_backend_invalid_inline_child(backend: XmlBackend):
  if not isinstance(backend, StrictBackend):
    pytest.skip("StrictBackend only")

  deserializer = Deserializer(backend, policy=XmlPolicy())

  seg_elem = _make_elem(backend, "seg", text="text")
  _append_child(backend, seg_elem, _make_elem(backend, "prop", text="bad", type="t"))
  tuv_elem = _make_elem(backend, "tuv", **{"xml:lang": "en"})
  _append_child(backend, tuv_elem, seg_elem)

  with pytest.raises(XmlDeserializationError, match="Incorrect child element"):
    deserializer.deserialize(tuv_elem)
