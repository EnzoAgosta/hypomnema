from pathlib import Path

import pytest

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import UnknownInlineNode, UnknownNode
from hypomnema.dumpers.xml import UnknownInlineNodeDumper, UnknownNodeDumper


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def test_unknown_node_dumper_reconstructs_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  payload = backend.to_bytes(
    parse_xml(
      backend, tmp_path, "unknown-node.xml", '<extra-root source="external">keep me</extra-root>'
    ),
    strip_tail=True,
  )

  element = UnknownNodeDumper(backend).dump(UnknownNode(payload=payload))

  assert backend.get_tag(element) == "extra-root"


def test_unknown_inline_node_dumper_reconstructs_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  payload = backend.to_bytes(
    parse_xml(backend, tmp_path, "unknown-inline.xml", '<opaque alpha="1">unknown</opaque>'),
    strip_tail=True,
  )

  element = UnknownInlineNodeDumper(backend).dump(UnknownInlineNode(payload=payload))

  assert backend.get_tag(element) == "opaque"


def test_unknown_node_dumper_rejects_non_bytes_payload(backend: XmlBackend[object]) -> None:
  with pytest.raises(TypeError, match="UnknownNode payload must be bytes"):
    UnknownNodeDumper(backend).dump(UnknownNode(payload="not-bytes"))


def test_unknown_inline_node_dumper_rejects_non_bytes_payload(backend: XmlBackend[object]) -> None:
  with pytest.raises(TypeError, match="UnknownInlineNode payload must be bytes"):
    UnknownInlineNodeDumper(backend).dump(UnknownInlineNode(payload={"not": "bytes"}))
