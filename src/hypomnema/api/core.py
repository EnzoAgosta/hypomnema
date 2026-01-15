from pathlib import Path
from hypomnema.xml.utils import make_usable_path
from logging import Logger, getLogger
from hypomnema import (
  Tmx,
  BaseElement,
  DeserializationPolicy,
  XmlBackend,
  StandardBackend,
  Deserializer,
  SerializationPolicy,
  Serializer,
  XmlSerializationError,
  XmlDeserializationError,
)
from collections.abc import Collection, Generator
from typing import overload
from os import PathLike
from pathlib import Path
from typing import overload

from hypomnema.base.errors import (XmlDeserializationError,
                                   XmlSerializationError)
from hypomnema.base.types import BaseElement, Tmx
from hypomnema.xml.backends.base import XmlBackend
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.deserialization.deserializer import Deserializer
from hypomnema.xml.qname import QNameLike
from hypomnema.xml.serialization.serializer import Serializer
from hypomnema.xml.utils import (make_usable_path, normalize_encoding,
                                 prep_tag_set)

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
  filter: str | QNameLike | Iterable[str | QNameLike],
  encoding: str | None = None,
  *,
  backend: XmlBackend | None = None,
) -> Generator[BaseElement]: ...
def load(
  path: str | PathLike,
  filter: str | QNameLike | Iterable[str | QNameLike] | None = None,
  encoding: str | None = None,
  *,
  backend: XmlBackend | None = None,
) -> Tmx | Generator[BaseElement]:
  """Load a TMX file from disk.

  Parameters
  ----------
  path : str | PathLike
      Path to the TMX file to load.
  filter : str | QNameLike | Iterable[str | QNameLike]
      Optional tag filter for streaming parsing. Pass "tu" to yield
      translation units one at a time without loading entire file.
  encoding : str | None
      Character encoding for the file. Defaults to "utf-8".
  backend : XmlBackend | None
      XML backend to use for parsing. If None, uses StandardBackend.

  Returns
  -------
  Tmx | Generator[BaseElement]
      If filter is None, returns complete Tmx object.
      If filter is specified, returns generator yielding matching elements.

  Raises
  ------
  FileNotFoundError
      If the file does not exist.
  IsADirectoryError
      If the path is a directory.
  XmlDeserializationError
      If the root element is not a valid TMX element.

  Example
  -------
  .. code-block:: python
    from hypomnema import load

    tmx = load("translations.tmx")
    for tu in load("large.tmx", filter="tu"):
      print(tu.srclang)
  """

  def _load_filtered(
    _backend: XmlBackend, _path: Path, _filter: str | Collection[str], _deserializer: Deserializer
  ) -> Generator[BaseElement]:
    """Internal generator for filtered loading."""
    for element in _backend.iterparse(_path, tag_filter=_filter):
      yield _deserializer.deserialize(element)

  _backend = backend if backend is not None else StandardBackend(logger=logger)
  _logger = logger if logger is not None else getLogger("hypomnema.api.load")
  _policy = policy if policy is not None else DeserializationPolicy()

  _deserializer = Deserializer(_backend, policy=_policy, logger=_logger)

  _path = make_usable_path(path, mkdir=False)
  if not _path.exists():
    raise FileNotFoundError(f"File {_path} does not exist")
  if not _path.is_file():
    raise IsADirectoryError(f"Path {_path} is a directory")

  if filter is not None:
    return _load_filtered(_backend, _path, filter, _deserializer)
  root = _backend.parse(_path, encoding=encoding)
  if _backend.get_tag(root, as_qname=True).local_name != "tmx":
    raise XmlDeserializationError("Root element is not a tmx")
  tmx = _deserializer.deserialize(root)
  if not isinstance(tmx, Tmx):
    raise XmlDeserializationError(f"root element did not deserialize to a Tmx: {type(tmx)}")
  return tmx


def dump(
  tmx: Tmx, path: PathLike | str, encoding: str | None = None, *, backend: XmlBackend | None = None
) -> None:
  """Serialize a TMX object to a file.

  Parameters
  ----------
  tmx : Tmx
      The TMX object to serialize.
  path : PathLike | str
      Path where the TMX file will be written.
  encoding : str | None
      Character encoding for the output file. Defaults to "utf-8".
  backend : XmlBackend | None
      XML backend to use for serialization. If None, uses StandardBackend.

  Raises
  ------
  TypeError
      If tmx is not a Tmx instance.
  XmlSerializationError
      If serialization fails.

  Example
  -------
  .. code-block:: python
    from hypomnema import dump, load

    tmx = load("input.tmx")
    tmx.boby = [tu for tu in tmx.body if not tu.variants]
    dump(tmx, "output.tmx")
  """
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
