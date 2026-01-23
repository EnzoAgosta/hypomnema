from collections.abc import Generator, Iterable
from os import PathLike
from pathlib import Path
from typing import overload

from hypomnema.base.errors import (XmlDeserializationError,
                                   XmlSerializationError)
from hypomnema.base.types import BaseElement, Tmx
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.xml.utils import make_usable_path, normalize_encoding

__all__ = ["load", "dump"]


@overload
def load(
  path: str | PathLike,
  filter: None = None,
  encoding: str | None = None,
  *,
  backend: XmlBackend | None = None,
) -> Tmx: ...
@overload
def load(
  path: str | PathLike,
  filter: str | Iterable[str],
  encoding: str | None = None,
  *,
  backend: XmlBackend | None = None,
) -> Generator[BaseElement]: ...
def load(
  path: str | PathLike,
  filter: str | Iterable[str] | None = None,
  encoding: str | None = None,
  *,
  backend: XmlBackend | None = None,
) -> Tmx | Generator[BaseElement]:
  def _load_filtered(
    _backend: XmlBackend, _path: Path, _filter: str | Iterable[str], _deserializer: Deserializer
  ) -> Generator[BaseElement]:
    for element in _backend.iterparse(_path, tag_filter=_filter):
      obj = _deserializer.deserialize(element)
      if obj is not None:
        yield obj

  _encoding = normalize_encoding(encoding) if encoding is not None else "utf-8"
  _backend = backend if backend is not None else StandardBackend(default_encoding=_encoding)
  _deserializer = Deserializer(_backend)

  _path = make_usable_path(path, mkdir=False)
  if not _path.exists():
    raise FileNotFoundError(f"File {_path} does not exist")
  if not _path.is_file():
    raise IsADirectoryError(f"Path {_path} is a directory")

  if filter is not None:
    return _load_filtered(_backend, _path, filter, _deserializer)
  root = _backend.parse(_path)
  if _backend.get_tag(root, as_qname=True).local_name != "tmx":
    raise XmlDeserializationError("Root element is not a tmx")
  tmx = _deserializer.deserialize(root)
  if not isinstance(tmx, Tmx):
    raise XmlDeserializationError(f"root element did not deserialize to a Tmx: {type(tmx)}")
  return tmx


def dump(
  tmx: Tmx, path: PathLike | str, encoding: str | None = None, *, backend: XmlBackend | None = None
) -> None:
  if not isinstance(tmx, Tmx):
    raise TypeError(f"Root element is not a Tmx: {type(tmx)}")

  _encoding = normalize_encoding(encoding) if encoding is not None else "utf-8"
  _backend = backend if backend is not None else StandardBackend(default_encoding=_encoding)
  _serializer = Serializer(_backend)

  _path = make_usable_path(path, mkdir=True)
  xml_element = _serializer.serialize(tmx)
  if xml_element is None:
    raise XmlSerializationError("serializer returned None")
  _backend.write(xml_element, _path, encoding=_encoding)
