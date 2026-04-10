from pathlib import Path

import pytest

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.attributes import Assoc
from hypomnema.domain.nodes import Hi, Ph, TranslationVariant, UnknownInlineNode, UnknownNode
from hypomnema.loaders.xml import TranslationVariantLoader


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def parse_payload[T](backend: XmlBackend[T], tmp_path: Path, filename: str, payload: object) -> T:
  path = tmp_path / filename
  assert isinstance(payload, bytes)
  path.write_bytes(payload)
  return backend.parse(path)


def load_minimal_variant(backend: XmlBackend[object], tmp_path: Path) -> TranslationVariant:
  element = parse_xml(
    backend, tmp_path, "variant-minimal.xml", '<tuv xml:lang="en"><seg>Hello world</seg></tuv>'
  )
  return TranslationVariantLoader(backend).load(element)


def load_rich_variant(backend: XmlBackend[object], tmp_path: Path) -> TranslationVariant:
  element = parse_xml(
    backend,
    tmp_path,
    "variant-rich.xml",
    (
      '<tuv xml:lang="de" o-encoding="utf-8" datatype="html" usagecount="7" '
      'lastusagedate="2024-03-04T05:06:07" creationtool="tool" '
      'creationtoolversion="2.0" creationdate="2024-03-01T01:02:03" '
      'creationid="creator" changedate="2024-03-05T06:07:08" '
      'changeid="modifier" o-tmf="legacy" custom="value">'
      '<note xml:lang="fr">note</note>'
      '<prop type="domain">billing</prop>'
      '<extra-top flag="1">keep me</extra-top>'
      '<seg>lead<ph assoc="b" x="2" type="fmt">inner<sub datatype="xml">sub</sub>tail</ph>'
      'after<hi x="7" type="style">deep</hi><extra-inline alpha="1">opaque</extra-inline>end</seg>'
      "</tuv>"
    ),
  )
  return TranslationVariantLoader(backend).load(element)


def test_variant_loader_sets_language_from_minimal_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_variant(backend, tmp_path).spec_attributes.language == "en"


def test_variant_loader_sets_segment_from_minimal_input(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_variant(backend, tmp_path).segment == ["Hello world"]


def test_variant_loader_defaults_notes_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_variant(backend, tmp_path).notes == []


def test_variant_loader_defaults_props_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_variant(backend, tmp_path).props == []


def test_variant_loader_defaults_extra_attributes_to_empty_dict(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_variant(backend, tmp_path).extra_attributes == {}


def test_variant_loader_defaults_extra_nodes_to_empty_list(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_minimal_variant(backend, tmp_path).extra_nodes == []


def test_variant_loader_sets_original_encoding(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.original_encoding == "utf-8"


def test_variant_loader_sets_original_data_type(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.original_data_type == "html"


def test_variant_loader_coerces_usage_count(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.usage_count == 7


def test_variant_loader_sets_creation_tool(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.creation_tool == "tool"


def test_variant_loader_sets_creation_tool_version(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.creation_tool_version == "2.0"


def test_variant_loader_sets_created_by(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.created_by == "creator"


def test_variant_loader_sets_last_modified_by(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.last_modified_by == "modifier"


def test_variant_loader_sets_original_tm_format(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).spec_attributes.original_tm_format == "legacy"


def test_variant_loader_preserves_extra_attributes(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).extra_attributes == {"custom": "value"}


def test_variant_loader_loads_note_children(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [note.text for note in load_rich_variant(backend, tmp_path).notes] == ["note"]


def test_variant_loader_loads_prop_children(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert [prop.text for prop in load_rich_variant(backend, tmp_path).props] == ["billing"]


def test_variant_loader_preserves_unknown_top_level_nodes(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  extra_nodes = load_rich_variant(backend, tmp_path).extra_nodes

  assert len(extra_nodes) == 1
  assert isinstance(extra_nodes[0], UnknownNode)


def test_variant_loader_preserves_unknown_top_level_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  payload = load_rich_variant(backend, tmp_path).extra_nodes[0].payload

  assert (
    backend.get_tag(parse_payload(backend, tmp_path, "variant-extra-top.xml", payload))
    == "extra-top"
  )


def test_variant_loader_preserves_segment_leading_text(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).segment[0] == "lead"


def test_variant_loader_loads_placeholder_inline_node(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert isinstance(load_rich_variant(backend, tmp_path).segment[1], Ph)


def test_variant_loader_sets_placeholder_association(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  placeholder = load_rich_variant(backend, tmp_path).segment[1]

  assert isinstance(placeholder, Ph)
  assert placeholder.spec_attributes.association is Assoc.B


def test_variant_loader_sets_placeholder_external_id(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  placeholder = load_rich_variant(backend, tmp_path).segment[1]

  assert isinstance(placeholder, Ph)
  assert placeholder.spec_attributes.external_id == 2


def test_variant_loader_preserves_placeholder_mixed_content(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  placeholder = load_rich_variant(backend, tmp_path).segment[1]

  assert isinstance(placeholder, Ph)
  assert placeholder.content == ["inner", placeholder.content[1], "tail"]


def test_variant_loader_preserves_text_after_placeholder(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).segment[2] == "after"


def test_variant_loader_loads_hi_inline_node(backend: XmlBackend[object], tmp_path: Path) -> None:
  assert isinstance(load_rich_variant(backend, tmp_path).segment[3], Hi)


def test_variant_loader_preserves_hi_content(backend: XmlBackend[object], tmp_path: Path) -> None:
  highlight = load_rich_variant(backend, tmp_path).segment[3]

  assert isinstance(highlight, Hi)
  assert highlight.content == ["deep"]


def test_variant_loader_preserves_unknown_inline_node(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert isinstance(load_rich_variant(backend, tmp_path).segment[4], UnknownInlineNode)


def test_variant_loader_preserves_unknown_inline_payload_tag(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  unknown_inline = load_rich_variant(backend, tmp_path).segment[4]

  assert isinstance(unknown_inline, UnknownInlineNode)
  payload = parse_payload(backend, tmp_path, "variant-extra-inline.xml", unknown_inline.payload)
  assert backend.get_tag(payload) == "extra-inline"


def test_variant_loader_preserves_text_after_unknown_inline(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  assert load_rich_variant(backend, tmp_path).segment[5] == "end"


def test_variant_loader_allows_whitespace_outside_seg(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  element = parse_xml(
    backend, tmp_path, "variant-whitespace.xml", '<tuv xml:lang="en">  <seg>Hello</seg></tuv>'
  )

  assert TranslationVariantLoader(backend).load(element).segment == ["Hello"]


def test_variant_loader_rejects_non_whitespace_text_outside_seg(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  element = parse_xml(
    backend, tmp_path, "variant-text.xml", '<tuv xml:lang="en">unexpected<seg>Hello</seg></tuv>'
  )

  with pytest.raises(ValueError, match="Text content for <tuv> element must be empty"):
    TranslationVariantLoader(backend).load(element)


def test_variant_loader_requires_lang(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(backend, tmp_path, "variant-missing-lang.xml", "<tuv><seg>Hello</seg></tuv>")

  with pytest.raises(ValueError, match="Missing attribute 'xml:lang'"):
    TranslationVariantLoader(backend).load(element)


def test_variant_loader_requires_seg(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(
    backend, tmp_path, "variant-missing-seg.xml", '<tuv xml:lang="en"><note>note</note></tuv>'
  )

  with pytest.raises(ValueError, match="Missing <seg> element"):
    TranslationVariantLoader(backend).load(element)


def test_variant_loader_rejects_multiple_seg_elements(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  element = parse_xml(
    backend,
    tmp_path,
    "variant-multiple-seg.xml",
    '<tuv xml:lang="en"><seg>one</seg><seg>two</seg></tuv>',
  )

  with pytest.raises(ValueError, match="Multiple <seg> elements"):
    TranslationVariantLoader(backend).load(element)


def test_variant_loader_rejects_wrong_tag(backend: XmlBackend[object], tmp_path: Path) -> None:
  element = parse_xml(backend, tmp_path, "variant-wrong-tag.xml", "<tu><seg>Hello</seg></tu>")

  with pytest.raises(ValueError, match="Expected <tuv> element"):
    TranslationVariantLoader(backend).load(element)
