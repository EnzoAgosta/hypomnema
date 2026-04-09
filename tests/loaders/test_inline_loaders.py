from pathlib import Path

import pytest

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.attributes import Assoc, Pos
from hypomnema.domain.nodes import Bpt, Hi, It, Ph, Sub, UnknownInlineNode
from hypomnema.loaders.xml import BptLoader, EptLoader, HiLoader, ItLoader, PhLoader, SubLoader


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def parse_payload[T](backend: XmlBackend[T], tmp_path: Path, filename: str, payload: object) -> T:
  path = tmp_path / filename
  assert isinstance(payload, bytes)
  path.write_bytes(payload)
  return backend.parse(path)


def load_bpt(backend: XmlBackend[object], tmp_path: Path) -> Bpt:
  element = parse_xml(
    backend,
    tmp_path,
    "bpt.xml",
    '<bpt i="1" x="2" type="fmt" custom="value">lead<sub datatype="xml">sub</sub>tail</bpt>',
  )
  return BptLoader(backend).load(element)


def load_it(backend: XmlBackend[object], tmp_path: Path) -> It:
  element = parse_xml(
    backend,
    tmp_path,
    "it.xml",
    '<it pos="begin" x="5" type="fmt">lead<sub datatype="xml">sub</sub>tail</it>',
  )
  return ItLoader(backend).load(element)


def load_ph(backend: XmlBackend[object], tmp_path: Path) -> Ph:
  element = parse_xml(
    backend,
    tmp_path,
    "ph.xml",
    '<ph assoc="f" x="7" type="fmt">lead<opaque alpha="1">unknown</opaque>tail</ph>',
  )
  return PhLoader(backend).load(element)


def load_hi(backend: XmlBackend[object], tmp_path: Path) -> Hi:
  element = parse_xml(
    backend,
    tmp_path,
    "hi.xml",
    (
      '<hi x="9" type="style" custom="value">lead'
      '<ph type="fmt">ph</ph>'
      "<hi>nested</hi>"
      "<opaque>unknown</opaque>"
      "tail</hi>"
    ),
  )
  return HiLoader(backend).load(element)


def load_sub(backend: XmlBackend[object], tmp_path: Path) -> Sub:
  element = parse_xml(
    backend,
    tmp_path,
    "sub.xml",
    '<sub datatype="xml" type="annotation" custom="value">lead<hi>known</hi><opaque>unknown</opaque>tail</sub>',
  )
  return SubLoader(backend).load(element)


def test_bpt_loader_sets_internal_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_bpt(backend, tmp_path).spec_attributes.internal_id == 1


def test_bpt_loader_sets_external_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_bpt(backend, tmp_path).spec_attributes.external_id == 2


def test_bpt_loader_sets_kind(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_bpt(backend, tmp_path).spec_attributes.kind == "fmt"


def test_bpt_loader_preserves_extra_attributes(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_bpt(backend, tmp_path).extra_attributes == {"custom": "value"}


def test_bpt_loader_preserves_mixed_content(backend: XmlBackend[object], tmp_path: Path) -> None:
  node = load_bpt(backend, tmp_path)

  assert node.content == ["lead", node.content[1], "tail"]


def test_bpt_loader_loads_nested_sub_node(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert isinstance(load_bpt(backend, tmp_path).content[1], Sub)


def test_bpt_loader_preserves_nested_sub_content(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  child = load_bpt(backend, tmp_path).content[1]

  assert isinstance(child, Sub)
  assert child.content == ["sub"]


def test_ept_loader_requires_internal_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(backend, tmp_path, "ept-missing-i.xml", "<ept>text</ept>")

  with pytest.raises(ValueError, match="Missing attribute 'i'"):
    EptLoader(backend).load(element)


def test_it_loader_sets_position(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_it(backend, tmp_path).spec_attributes.position is Pos.BEGIN


def test_it_loader_sets_external_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_it(backend, tmp_path).spec_attributes.external_id == 5


def test_it_loader_sets_kind(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_it(backend, tmp_path).spec_attributes.kind == "fmt"


def test_it_loader_preserves_tail_after_sub_elements(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_it(backend, tmp_path).content == [
    "lead",
    load_it(backend, tmp_path).content[1],
    "tail",
  ]


def test_ph_loader_sets_association(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_ph(backend, tmp_path).spec_attributes.association is Assoc.F


def test_ph_loader_sets_external_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_ph(backend, tmp_path).spec_attributes.external_id == 7


def test_ph_loader_sets_kind(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_ph(backend, tmp_path).spec_attributes.kind == "fmt"


def test_ph_loader_preserves_unknown_inline_node(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert isinstance(load_ph(backend, tmp_path).content[1], UnknownInlineNode)


def test_ph_loader_preserves_unknown_inline_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  unknown = load_ph(backend, tmp_path).content[1]

  assert isinstance(unknown, UnknownInlineNode)
  assert (
    backend.get_tag(parse_payload(backend, tmp_path, "ph-opaque.xml", unknown.payload)) == "opaque"
  )


def test_hi_loader_sets_external_id(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_hi(backend, tmp_path).spec_attributes.external_id == 9


def test_hi_loader_sets_kind(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_hi(backend, tmp_path).spec_attributes.kind == "style"


def test_hi_loader_preserves_extra_attributes(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_hi(backend, tmp_path).extra_attributes == {"custom": "value"}


def test_hi_loader_preserves_content_order(backend: XmlBackend[object], tmp_path: Path) -> None:
  node = load_hi(backend, tmp_path)

  assert node.content == ["lead", node.content[1], node.content[2], node.content[3], "tail"]


def test_hi_loader_loads_known_inline_child(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert isinstance(load_hi(backend, tmp_path).content[1], Ph)


def test_hi_loader_loads_nested_hi_child(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert isinstance(load_hi(backend, tmp_path).content[2], Hi)


def test_hi_loader_preserves_unknown_inline_child(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert isinstance(load_hi(backend, tmp_path).content[3], UnknownInlineNode)


def test_sub_loader_sets_original_data_type(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_sub(backend, tmp_path).spec_attributes.original_data_type == "xml"


def test_sub_loader_sets_kind(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_sub(backend, tmp_path).spec_attributes.kind == "annotation"


def test_sub_loader_preserves_extra_attributes(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_sub(backend, tmp_path).extra_attributes == {"custom": "value"}


def test_sub_loader_preserves_content_order(backend: XmlBackend[object], tmp_path: Path) -> None:
  node = load_sub(backend, tmp_path)

  assert node.content == ["lead", node.content[1], node.content[2], "tail"]


def test_sub_loader_loads_known_inline_child(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert isinstance(load_sub(backend, tmp_path).content[1], Hi)


def test_sub_loader_preserves_unknown_inline_child(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert isinstance(load_sub(backend, tmp_path).content[2], UnknownInlineNode)


def test_ept_loader_rejects_wrong_tag(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(backend, tmp_path, "wrong-ept.xml", "<ph>text</ph>")

  with pytest.raises(ValueError, match="Expected <ept> element"):
    EptLoader(backend).load(element)


def test_hi_loader_rejects_wrong_tag(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(backend, tmp_path, "wrong-hi.xml", "<sub>text</sub>")

  with pytest.raises(ValueError, match="Expected <hi> element"):
    HiLoader(backend).load(element)
