from datetime import UTC, datetime
from pathlib import Path

from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import Hi, Ph, Sub, TranslationVariant, UnknownInlineNode
from hypomnema.dumpers.xml import TranslationVariantDumper
from hypomnema.loaders.xml import TranslationVariantLoader


def parse_xml[T](backend: XmlBackend[T], tmp_path: Path, filename: str, xml: str) -> T:
  path = tmp_path / filename
  path.write_text(xml, encoding="utf-8")
  return backend.parse(path)


def canonicalize[T](
  backend: XmlBackend[T], element: T
) -> tuple[str, tuple[tuple[str, str], ...], str | None, str | None, tuple[object, ...]]:
  return (
    backend.get_tag(element),
    tuple(sorted(backend.get_attribute_map(element).items())),
    backend.get_text(element),
    backend.get_tail(element),
    tuple(canonicalize(backend, child) for child in backend.iter_children(element)),
  )


def dump_and_reload_variant(
  backend: XmlBackend[object], tmp_path: Path, node: TranslationVariant, filename: str
) -> TranslationVariant:
  element = TranslationVariantDumper(backend).dump(node)
  payload = backend.to_bytes(element, strip_tail=True)
  path = tmp_path / filename
  path.write_bytes(payload)
  return TranslationVariantLoader(backend).load(backend.parse(path))


def make_unknown_inline(backend: XmlBackend[object], tmp_path: Path) -> UnknownInlineNode:
  payload_element = parse_xml(
    backend, tmp_path, "unknown-inline.xml", '<opaque alpha="1">unknown</opaque>'
  )
  return UnknownInlineNode(payload=backend.to_bytes(payload_element, strip_tail=True))


def test_variant_node_roundtrip_preserves_known_inline_semantics(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  node = TranslationVariant.create(
    language="en",
    original_encoding="utf-8",
    original_data_type="html",
    usage_count=3,
    last_used_at=datetime(2024, 3, 4, 5, 6, 7, tzinfo=UTC),
    creation_tool="tool",
    creation_tool_version="1.0",
    created_at=datetime(2024, 3, 1, 1, 2, 3, tzinfo=UTC),
    created_by="creator",
    last_modified_at=datetime(2024, 3, 5, 6, 7, 8, tzinfo=UTC),
    last_modified_by="modifier",
    original_tm_format="legacy",
    segment=[
      "lead",
      Ph.create(
        content=["inner", Sub.create(content=["sub"], original_data_type="xml"), "tail"],
        association="b",
        external_id=2,
        kind="fmt",
      ),
      "after",
      Hi.create(content=["deep"], external_id=7, kind="style"),
      "end",
    ],
  )

  assert dump_and_reload_variant(backend, tmp_path, node, "variant-known.xml") == node


def test_variant_xml_roundtrip_preserves_known_inline_structure(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  original = parse_xml(
    backend,
    tmp_path,
    "variant-structure.xml",
    (
      '<tuv xml:lang="en" o-encoding="utf-8" datatype="html" usagecount="3" '
      'lastusagedate="20240304T050607Z" creationtool="tool" creationtoolversion="1.0" '
      'creationdate="20240301T010203Z" creationid="creator" changedate="20240305T060708Z" '
      'changeid="modifier" o-tmf="legacy">'
      '<seg>lead<ph assoc="b" x="2" type="fmt">inner<sub datatype="xml">sub</sub>tail</ph>'
      'after<hi x="7" type="style">deep</hi>end</seg>'
      "</tuv>"
    ),
  )

  node = TranslationVariantLoader(backend).load(original)
  reparsed = parse_xml(
    backend,
    tmp_path,
    "variant-structure-reparsed.xml",
    backend.to_bytes(TranslationVariantDumper(backend).dump(node), strip_tail=True).decode("utf-8"),
  )

  assert canonicalize(backend, reparsed) == canonicalize(backend, original)


def test_variant_node_roundtrip_preserves_unknown_inline_payload(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  unknown = make_unknown_inline(backend, tmp_path)
  node = TranslationVariant.create(language="en", segment=["lead", unknown, "tail"])

  reloaded = dump_and_reload_variant(backend, tmp_path, node, "variant-unknown-inline.xml")

  assert isinstance(reloaded.segment[1], UnknownInlineNode)
  assert reloaded.segment[1].payload == unknown.payload


def test_variant_xml_roundtrip_preserves_unknown_inline_structure(
  backend: XmlBackend[object], tmp_path: Path
) -> None:
  original = parse_xml(
    backend,
    tmp_path,
    "variant-unknown-inline-structure.xml",
    '<tuv xml:lang="en"><seg>lead<opaque alpha="1">unknown</opaque>tail</seg></tuv>',
  )

  node = TranslationVariantLoader(backend).load(original)
  reparsed = parse_xml(
    backend,
    tmp_path,
    "variant-unknown-inline-structure-reparsed.xml",
    backend.to_bytes(TranslationVariantDumper(backend).dump(node), strip_tail=True).decode("utf-8"),
  )

  assert canonicalize(backend, reparsed) == canonicalize(backend, original)
