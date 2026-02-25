"""High-level API for loading and saving TMX files.

This module provides the main entry points for working with TMX files:
``load()`` to deserialize TMX files into Python objects, and ``dump()``
to serialize objects back to TMX format.

The API supports both full document loading and memory-efficient streaming
for processing large files.
"""

from collections.abc import Generator, Iterable, Mapping
from logging import Logger
from os import PathLike
from pathlib import Path
from typing import NotRequired, TypedDict, Unpack, overload
from hypomnema.base.types import BaseElement, Tmx, TmxLike
from hypomnema.xml import backends, deserialization, policy, serialization, utils

DEFAULT_BACKEND = (
  backends.LxmlBackend if backends.LxmlBackend is not None else backends.StandardBackend
)


class LoadOptions(TypedDict):
  """Options for configuring the load operation.

  Kept separate from main function signature to keep things clean
  """

  backend: NotRequired[backends.XmlBackend]
  backend_logger: NotRequired[Logger]
  nsmap: NotRequired[Mapping[str, str]]
  namespace_handler: NotRequired[backends.NamespaceHandler]
  namespace_handler_logger: NotRequired[Logger]
  namespace_handler_policy: NotRequired[policy.NamespacePolicy]
  deserializer: NotRequired[deserialization.Deserializer]
  deserializer_logger: NotRequired[Logger]
  deserializer_policy: NotRequired[policy.XmlDeserializationPolicy]
  deserializer_handlers: NotRequired[Mapping[str, deserialization.BaseElementDeserializer]]


@overload
def load(
  path: str | PathLike,
  filter: None = None,
  encoding: str | None = None,
  **kwargs: Unpack[LoadOptions],
) -> Tmx: ...
@overload
def load(
  path: str | PathLike,
  filter: str | utils.QNameLike | Iterable[str | utils.QNameLike],
  encoding: str | None = None,
  **kwargs: Unpack[LoadOptions],
) -> Generator[BaseElement]: ...
def load(
  path: str | PathLike,
  filter: str | utils.QNameLike | Iterable[str | utils.QNameLike] | None = None,
  encoding: str | None = None,
  **kwargs: Unpack[LoadOptions],
) -> Tmx | Generator[BaseElement]:
  """Load a TMX file from disk.

  Deserializes a TMX file into Python dataclass objects. Supports both
  full document loading and memory-efficient streaming.

  Args:
      path: Path to the TMX file.
      filter: Optional tag filter for streaming. If specified, yields elements
          matching the filter without loading the entire document.
          Common values: "tu" for translation units, "tuv" for variants.
      encoding: Character encoding (default: "utf-8").
      **kwargs: Additional configuration options (backend, policies, etc.).
      backend: Custom XML backend (defaults to LxmlBackend if available else StandardBackend).
      backend_logger: Logger to be used by the backend if backend is not provided.
      nsmap: Custom namespace prefix-to-URI mappings to be used by the backend if backend is not provided.
      namespace_handler: Custom namespace handler instance to be used by the backend if backend is not provided.
      namespace_handler_logger: Logger for namespace operations to be used by the namespace handler if namespace_handler is not provided.
      namespace_handler_policy: Policy for namespace handling to be used by the namespace handler if namespace_handler is not provided.
      deserializer: Custom deserializer instance. Uses whatever backend is given or created using previous options.
      deserializer_logger: Logger for deserialization operations to be used by the deserializer if deserializer is not provided.
      deserializer_policy: Policy for deserialization error handling to be used by the deserializer if deserializer is not provided.
      deserializer_handlers: Custom element handlers for deserialization to be used by the deserializer if deserializer is not provided.

  Returns:
      If filter is None, returns the complete Tmx object.
      If filter is specified, returns a generator yielding matching elements.

  Raises:
      FileNotFoundError: If the file does not exist.
      IsADirectoryError: If path points to a directory.
      ValueError: If root element is not <tmx> or deserialization fails.

  Example:
      >>> # Load entire file
      >>> tmx = load("translations.tmx")
      >>> len(tmx.body)
      1000

      >>> # Stream translation units (memory efficient)
      >>> for tu in load("large.tmx", filter="tu"):
      ...   process(tu)
  """

  def _load_filtered(
    _backend: backends.XmlBackend,
    _path: Path,
    _filter: set[str] | None,
    _deserializer: deserialization.Deserializer,
  ) -> Generator[BaseElement]:
    for element in _backend.iterparse(_path, tag_filter=_filter):
      obj = _deserializer.deserialize(element)
      if obj is not None:
        yield obj

  _encoding = utils.normalize_encoding(encoding) if encoding is not None else "utf-8"
  _backend = kwargs.get(
    "backend",
    DEFAULT_BACKEND(
      logger=kwargs.get("backend_logger"),
      default_encoding=_encoding,
      namespace_handler=kwargs.get(
        "namespace_handler",
        backends.NamespaceHandler(
          nsmap=kwargs.get("nsmap"),
          logger=kwargs.get("namespace_handler_logger"),
          policy=kwargs.get("namespace_handler_policy"),
        ),
      ),
    ),
  )
  _deserializer = kwargs.get(
    "deserializer",
    deserialization.Deserializer(
      backend=_backend,
      policy=kwargs.get("deserializer_policy"),
      logger=kwargs.get("deserializer_logger"),
      handlers=kwargs.get("deserializer_handlers"),
    ),
  )

  _path = utils.make_usable_path(path, mkdir=False)
  if not _path.exists():
    raise FileNotFoundError(f"File {_path} does not exist")
  if not _path.is_file():
    raise IsADirectoryError(f"Path {_path} is a directory")

  if filter is not None:
    filter = _backend.prep_tag_set(filter)
    return _load_filtered(_backend, _path, filter, _deserializer)
  root = _backend.parse(_path)
  if _backend.get_tag(root) != "tmx":
    raise ValueError("Root element is not a tmx")
  tmx = _deserializer.deserialize(root)
  if not isinstance(tmx, Tmx):
    raise ValueError(f"root element did not deserialize to a Tmx: {type(tmx)}")
  return tmx


class DumpOptions(TypedDict):
  """Options for configuring the dump operation.

  Kept separate from main function signature to keep things clean
  """

  backend: NotRequired[backends.XmlBackend]
  backend_logger: NotRequired[Logger]
  nsmap: NotRequired[Mapping[str, str]]
  namespace_handler: NotRequired[backends.NamespaceHandler]
  namespace_handler_logger: NotRequired[Logger]
  namespace_handler_policy: NotRequired[policy.NamespacePolicy]
  serializer: NotRequired[serialization.Serializer]
  serializer_logger: NotRequired[Logger]
  serializer_policy: NotRequired[policy.XmlSerializationPolicy]
  serialization_handlers: NotRequired[Mapping[type, serialization.BaseElementSerializer]]


def dump(
  tmx: Tmx, path: PathLike | str, encoding: str | None = None, **kwargs: Unpack[DumpOptions]
) -> None:
  """Save a TMX object to disk.

  Serializes a Tmx dataclass to a TMX 1.4b XML file.

  Args:
      tmx: The TMX object to serialize.
      path: Output file path. Parent directories are created if needed.
      encoding: Character encoding (default: "utf-8").
      **kwargs: Additional configuration options (backend, policies, etc.).
      backend: Custom XML backend (defaults to LxmlBackend if available else StandardBackend).
      backend_logger: Logger to be used by the backend if backend is not provided.
      nsmap: Custom namespace prefix-to-URI mappings to be used by the backend if backend is not provided.
      namespace_handler: Custom namespace handler instance to be used by the backend if backend is not provided.
      namespace_handler_logger: Logger for namespace operations to be used by the namespace handler if namespace_handler is not provided.
      namespace_handler_policy: Policy for namespace handling to be used by the namespace handler if namespace_handler is not provided.
      serializer: Custom serializer instance. Uses whatever backend is given or created using previous options.
      serializer_logger: Logger for serialization operations to be used by the serializer if serializer is not provided.
      serializer_policy: Policy for serialization error handling to be used by the serializer if serializer is not provided.
      serializer_handlers: Custom element handlers for serialization to be used by the serializer if serializer is not provided.

  Raises:
      TypeError: If tmx is not a Tmx instance.
      ValueError: If serialization fails.

  Example:
      >>> tmx = create_tmx(header=header, body=translations)
      >>> dump(tmx, "output.tmx")
      >>> dump(tmx, "output.tmx", encoding="utf-16")
  """
  if not isinstance(tmx, TmxLike):
    raise TypeError(f"Root element is not a Tmx: {type(tmx)}")

  _encoding = utils.normalize_encoding(encoding) if encoding is not None else "utf-8"
  _backend = kwargs.get(
    "backend",
    DEFAULT_BACKEND(
      logger=kwargs.get("backend_logger"),
      default_encoding=_encoding,
      namespace_handler=kwargs.get(
        "namespace_handler",
        backends.NamespaceHandler(
          nsmap=kwargs.get("nsmap"),
          logger=kwargs.get("namespace_handler_logger"),
          policy=kwargs.get("namespace_handler_policy"),
        ),
      ),
    ),
  )
  _serializer = kwargs.get(
    "serializer",
    serialization.Serializer(
      backend=_backend,
      policy=kwargs.get("serializer_policy"),
      logger=kwargs.get("serializer_logger"),
    ),
  )

  _path = utils.make_usable_path(path, mkdir=True)
  xml_element = _serializer.serialize(tmx)
  if xml_element is None:
    raise ValueError("serializer returned None")
  _backend.write(xml_element, _path, encoding=_encoding)
