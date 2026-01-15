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

__all__ = ["load", "save"]


@overload
def load(
  path: PathLike | str,
  filter: None = None,
  *,
  encoding: str = "utf-8",
  policy: DeserializationPolicy | None = None,
  backend: XmlBackend | None = None,
  logger: Logger | None = None,
) -> Tmx: ...
@overload
def load(
  path: PathLike | str,
  filter: str | Collection[str],
  *,
  encoding: str = "utf-8",
  policy: DeserializationPolicy | None = None,
  backend: XmlBackend | None = None,
  logger: Logger | None = None,
) -> Generator[BaseElement]: ...
def load(
  path: PathLike | str,
  filter: str | Collection[str] | None = None,
  *,
  encoding: str = "utf-8",
  policy: DeserializationPolicy | None = None,
  backend: XmlBackend | None = None,
  logger: Logger | None = None,
) -> Tmx | Generator[BaseElement]:
  """
  Load a TMX file from disk.

  Parameters
  ----------
  path : PathLike | str
      Path to the TMX file to load.
  filter : str | Collection[str] | None
      Optional tag filter for streaming parsing. If None, loads entire file.
      If provided, only elements matching these tags are deserializedand yielded.
      Example: filter="tu" or filter=["tu", "header"]
      Note: When filter is provided, the file is parsed using iterparse
      for memory efficiency with large files.
  encoding : str
      File encoding. Defaults to "utf-8".
  policy : DeserializationPolicy | None
      Deserialization policy. Defaults to standard policy.
  backend : XmlBackend | None
      XML backend to use. Defaults to StandardBackend (stdlib).
  logger : Logger | None
      Logger instance. Defaults to module logger.

  Returns
  -------
  Tmx
      The loaded and deserialized TMX object.
  Generator[BaseElement]
      If filter is provided, yields deserialized elements matching the filter
      as they are parsed.

  Raises
  ------
  XmlDeserializationError
      If the root element is not a tmx when the filter is None.
  FileNotFoundError
      If the file does not exist.
  IsADirectoryError
      If the path is a directory.

  Examples
  --------
  >>> tmx = load("translations.tmx")
  >>> tmx = load("translations.tmx", encoding="latin-1")
  >>> for tu in load("large.tmx", filter="tu"):
  >>>     print(tu.srclang)
  >>> gen = load("file.tmx", filter=["tu", "header"])
  >>> for element in gen:
  >>>     if isinstance(element, Tu):
  >>>         print(element.srclang)
  >>>     elif isinstance(element, Header):
  >>>         print(element.creationtool)
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


def save(
  tmx: Tmx,
  path: PathLike | str,
  *,
  encoding: str = "utf-8",
  policy: SerializationPolicy | None = None,
  backend: XmlBackend | None = None,
  logger: Logger | None = None,
) -> None:
  """
  Save a TMX object to disk.

  Parameters
  ----------
  tmx : Tmx
      The TMX object to serialize and save.
  path : PathLike | str
      Destination path for the TMX file.
  encoding : str
      File encoding. Defaults to "utf-8".
  policy : SerializationPolicy | None
      Serialization policy. Defaults to standard policy.
  backend : XmlBackend | None
      XML backend to use. Defaults to StandardBackend (stdlib).
  logger : Logger | None
      Logger instance. Defaults to module logger.

  Raises
  ------
  XmlSerializationError
      If the serialization returns None for the given tmx object.
  TypeError
      If the given tmx object is not a Tmx object.

  Examples
  --------
  >>> save(tmx, "output.tmx")
  >>> save(tmx, "output.tmx", encoding="utf-16")
  >>> from hypomnema import LxmlBackend
  >>> save(tmx, "output.tmx", backend=LxmlBackend())
  """
  _backend = backend if backend is not None else StandardBackend(logger=logger)
  _logger = logger if logger is not None else getLogger("hypomnema.api.save")
  _policy = policy if policy is not None else SerializationPolicy()

  _serializer = Serializer(_backend, policy=_policy, logger=_logger)

  _path = make_usable_path(path, mkdir=True)

  if not isinstance(tmx, Tmx):
    raise TypeError(f"Root element is not a Tmx: {type(tmx)}")
  xml_element = _serializer.serialize(tmx)
  if xml_element is None:
    raise XmlSerializationError("serializer returned None")
  _backend.write(xml_element, _path, encoding=encoding)
