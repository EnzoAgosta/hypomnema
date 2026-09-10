"""Node shapes, unions, content grammars, and serializer contracts.

Scope is what ``models.py`` itself owns: per-node construction (required and
optional fields, defaults), the ``extra="forbid"`` attribute discipline, the
discriminated unions, the two inline content grammars, tuple-field ordering,
the JSON serializers, and the deprecated surfaces (``<ut>``, ``lang``).
Value-parser repertoires belong to ``test_validators.py`` and cross-field
contract rules to ``test_validation.py``; only the wiring of each alias into
a field is asserted here.

The models are a deliberately permissive IR: typing is enforced at
construction only -- assignment is unvalidated, so nothing here asserts on
field assignment.
"""

import warnings
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from hypomnema.errors import LanguageTagError, TmxWarning
from hypomnema.models import (
  Bpt,
  Ept,
  Header,
  Hi,
  InlineNode,
  It,
  LeafNode,
  Map,
  Note,
  Ph,
  Property,
  StructureNode,
  Sub,
  TmxModel,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,  # ty: ignore[deprecated]
)

# One minimal valid payload per element. Payloads carry ``element`` so the
# same dict serves direct class validation and union dispatch.
MINIMAL_PAYLOADS: dict[str, dict[str, Any]] = {
  "note": {"element": "note"},
  "prop": {"element": "prop", "type": "x-prop"},
  "map": {"element": "map", "unicode": "#x41"},
  "ude": {"element": "ude", "name": "u", "maps": [{"element": "map", "unicode": "#x41"}]},
  "sub": {"element": "sub"},
  "bpt": {"element": "bpt", "i": 1},
  "ept": {"element": "ept", "i": 1},
  "it": {"element": "it", "pos": "begin"},
  "ph": {"element": "ph"},
  "hi": {"element": "hi"},
  "ut": {"element": "ut"},
  "header": {
    "element": "header",
    "creationtool": "testtool",
    "creationtoolversion": "1.0",
    "segtype": "sentence",
    "o_tmf": "tmx",
    "adminlang": "en",
    "srclang": "*all*",
    "datatype": "txt",
  },
  "tuv": {"element": "tuv", "xml_lang": "en"},
  "tu": {"element": "tu", "srclang": "*all*", "variants": [{"element": "tuv", "xml_lang": "en"}]},
}

NODE_CLASSES: dict[str, type[TmxModel]] = {
  "note": Note,
  "prop": Property,
  "map": Map,
  "ude": Ude,
  "sub": Sub,
  "bpt": Bpt,
  "ept": Ept,
  "it": It,
  "ph": Ph,
  "hi": Hi,
  "ut": Ut,  # ty: ignore[deprecated]
  "header": Header,
  "tuv": TranslationUnitVariant,
  "tu": TranslationUnit,
}

# (element, required field): dropping the key from the minimal payload must
# be rejected with that field named.
REQUIRED_FIELDS = (
  ("prop", "type"),
  ("map", "unicode"),
  ("ude", "name"),
  ("ude", "maps"),
  ("bpt", "i"),
  ("ept", "i"),
  ("it", "pos"),
  ("header", "creationtool"),
  ("header", "creationtoolversion"),
  ("header", "segtype"),
  ("header", "o_tmf"),
  ("header", "adminlang"),
  ("header", "srclang"),
  ("header", "datatype"),
  ("tuv", "xml_lang"),
  ("tu", "variants"),
  ("tu", "srclang"),
)

# Elements whose ``content`` holds text plus ``<sub>`` only (SubOrStr), and
# one carrying the general inline grammar (InlineNodeOrStr).
SUB_CONTENT_ELEMENTS = ("bpt", "ept", "it", "ph", "ut")
SEG_CONTENT_ELEMENTS = ("tuv", "hi", "sub")

INLINE_ELEMENT_PAYLOADS = (
  {"element": "bpt", "i": 1},
  {"element": "ept", "i": 1},
  {"element": "it", "pos": "end"},
  {"element": "ph"},
  {"element": "hi"},
  {"element": "ut"},
)

# Language nodes carrying the deprecated ``lang`` attribute: constructing
# must stay silent, accessing the attribute must warn.
LANG_NODE_FACTORIES: tuple[tuple[str, Callable[[], TmxModel]], ...] = (
  ("note", lambda: Note(lang="fr")),
  ("prop", lambda: Property(type="x", lang="fr")),
  ("tuv", lambda: TranslationUnitVariant(xml_lang="en", lang="fr")),
)


def collect_exceptions(error: BaseException | None, error_type: type[Exception]) -> list[Exception]:
  """Flatten an exception (group) tree into the matching members."""
  if error is None:
    return []
  matches = [error] if isinstance(error, error_type) else []
  if isinstance(error, ExceptionGroup):
    for sub_exception in error.exceptions:
      matches.extend(collect_exceptions(sub_exception, error_type))
  return matches


def make_header(**overrides: Any) -> Header:
  """A valid ``Header`` from the minimal payload, with attribute overrides."""
  return Header.model_validate({**MINIMAL_PAYLOADS["header"], **overrides})


@pytest.mark.parametrize("element", MINIMAL_PAYLOADS)
def test_minimal_payload_is_accepted(element: str) -> None:
  node = NODE_CLASSES[element].model_validate(MINIMAL_PAYLOADS[element])
  assert node.element == element  # ty: ignore[unresolved-attribute]


@pytest.mark.parametrize(("element", "required_field"), REQUIRED_FIELDS)
def test_missing_required_field_is_rejected(element: str, required_field: str) -> None:
  payload = {key: value for key, value in MINIMAL_PAYLOADS[element].items() if key != required_field}
  with pytest.raises(ValidationError) as raised:
    NODE_CLASSES[element].model_validate(payload)
  assert raised.value.errors()[0]["loc"][-1] == required_field


def test_optional_fields_default_to_none_or_empty() -> None:
  note = Note()
  assert note.o_encoding is None
  assert note.xml_lang is None
  assert note.text is None
  # Even a None access is flagged, so read the deprecated attribute inside a
  # filter that keeps the warning out of pytest's summary.
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    assert note.lang is None
  bpt = Bpt(i=1)
  assert bpt.x is None
  assert bpt.type is None
  assert bpt.content == ()
  header = make_header()
  assert header.o_encoding is None
  assert header.creationdate is None
  assert header.metadata == ()
  mapping = Map(unicode="#x41")
  assert mapping.code is None
  assert mapping.ent is None
  assert mapping.subst is None
  variant = TranslationUnitVariant(xml_lang="en")
  assert variant.o_encoding is None
  assert variant.datatype is None
  assert variant.usagecount is None
  assert variant.creationtool is None
  assert variant.creationtoolversion is None
  assert variant.creationdate is None
  assert variant.creationid is None
  assert variant.changedate is None
  assert variant.o_tmf is None
  assert variant.changeid is None
  assert variant.metadata == ()
  assert variant.content == ()
  unit = TranslationUnit.model_validate(MINIMAL_PAYLOADS["tu"])
  assert unit.tuid is None
  assert unit.o_encoding is None
  assert unit.datatype is None
  assert unit.usagecount is None
  assert unit.lastusagedate is None
  assert unit.creationtool is None
  assert unit.creationtoolversion is None
  assert unit.creationdate is None
  assert unit.creationid is None
  assert unit.changedate is None
  assert unit.segtype is None
  assert unit.changeid is None
  assert unit.o_tmf is None
  assert unit.metadata == ()


@pytest.mark.parametrize("element", MINIMAL_PAYLOADS)
def test_unknown_attribute_is_rejected(element: str) -> None:
  payload = {**MINIMAL_PAYLOADS[element], "unknown_attribute": "value"}
  with pytest.raises(ValidationError) as raised:
    NODE_CLASSES[element].model_validate(payload)
  assert "unknown_attribute" in str(raised.value)


def test_element_defaults_to_the_tmx_element_name() -> None:
  assert Note().element == "note"
  assert Property(type="x").element == "prop"
  assert TranslationUnitVariant(xml_lang="en").element == "tuv"


def test_element_cannot_be_reassigned() -> None:
  node = Note()
  with pytest.raises(ValidationError):
    node.element = "prop"  # ty: ignore[invalid-assignment]


def test_element_mismatch_is_rejected() -> None:
  with pytest.raises(ValidationError):
    Note.model_validate({**MINIMAL_PAYLOADS["note"], "element": "prop"})


@pytest.mark.parametrize("element", MINIMAL_PAYLOADS)
def test_tmx_node_union_dispatches_every_element(element: str) -> None:
  node = TypeAdapter(TmxNode).validate_python(MINIMAL_PAYLOADS[element])
  assert type(node) is NODE_CLASSES[element]


@pytest.mark.parametrize("payload", INLINE_ELEMENT_PAYLOADS)
def test_inline_node_union_accepts_its_members(payload: dict[str, Any]) -> None:
  node = TypeAdapter(InlineNode).validate_python(payload)
  assert node.element == payload["element"]


@pytest.mark.parametrize(
  "payload",
  [
    MINIMAL_PAYLOADS["sub"],
    {"element": "note"},
    {"element": "prop", "type": "x"},
    {"element": "map", "unicode": "#x41"},
    MINIMAL_PAYLOADS["header"],
  ],
)
def test_inline_node_union_rejects_other_kinds(payload: dict[str, Any]) -> None:
  with pytest.raises(ValidationError):
    TypeAdapter(InlineNode).validate_python(payload)


@pytest.mark.parametrize(
  "payload",
  [{"element": "note"}, {"element": "prop", "type": "x"}, {"element": "map", "unicode": "#x41"}],
)
def test_leaf_node_union_accepts_its_members(payload: dict[str, Any]) -> None:
  node = TypeAdapter(LeafNode).validate_python(payload)
  assert node.element == payload["element"]


@pytest.mark.parametrize("payload", [{"element": "bpt", "i": 1}, MINIMAL_PAYLOADS["header"]])
def test_leaf_node_union_rejects_other_kinds(payload: dict[str, Any]) -> None:
  with pytest.raises(ValidationError):
    TypeAdapter(LeafNode).validate_python(payload)


@pytest.mark.parametrize(
  "payload",
  [MINIMAL_PAYLOADS["header"], MINIMAL_PAYLOADS["tu"], MINIMAL_PAYLOADS["tuv"], MINIMAL_PAYLOADS["ude"]],
)
def test_structure_node_union_accepts_its_members(payload: dict[str, Any]) -> None:
  node = TypeAdapter(StructureNode).validate_python(payload)
  assert node.element == payload["element"]


@pytest.mark.parametrize(
  "payload", [{"element": "note"}, {"element": "prop", "type": "x"}, {"element": "map", "unicode": "#x41"}]
)
def test_structure_node_union_rejects_other_kinds(payload: dict[str, Any]) -> None:
  with pytest.raises(ValidationError):
    TypeAdapter(StructureNode).validate_python(payload)


def test_unknown_element_name_is_rejected() -> None:
  with pytest.raises(ValidationError):
    TypeAdapter(TmxNode).validate_python({"element": "unknown"})


@pytest.mark.parametrize("element", SUB_CONTENT_ELEMENTS)
def test_sub_content_elements_take_text_and_sub_only(element: str) -> None:
  payload = {**MINIMAL_PAYLOADS[element], "content": ("leading text", {"element": "sub", "content": ("in",)})}
  node = NODE_CLASSES[element].model_validate(payload)
  assert node.content == ("leading text", Sub(content=("in",)))  # ty: ignore[unresolved-attribute]


@pytest.mark.parametrize("foreign_payload", [{"element": "ph"}, {"element": "hi"}, {"element": "note", "text": "n"}])
@pytest.mark.parametrize("element", SUB_CONTENT_ELEMENTS)
def test_sub_content_elements_reject_inline_and_leaf_nodes(element: str, foreign_payload: dict[str, Any]) -> None:
  payload = {**MINIMAL_PAYLOADS[element], "content": (foreign_payload,)}
  with pytest.raises(ValidationError):
    NODE_CLASSES[element].model_validate(payload)


@pytest.mark.parametrize("element", SEG_CONTENT_ELEMENTS)
def test_seg_content_elements_take_the_full_inline_grammar(element: str) -> None:
  payload = {**MINIMAL_PAYLOADS[element], "content": ("text", *INLINE_ELEMENT_PAYLOADS)}
  node = NODE_CLASSES[element].model_validate(payload)
  assert node.content[0] == "text"  # ty: ignore[unresolved-attribute]
  assert [child.element for child in node.content[1:]] == ["bpt", "ept", "it", "ph", "hi", "ut"]  # ty: ignore[unresolved-attribute]


@pytest.mark.parametrize("element", SEG_CONTENT_ELEMENTS)
def test_seg_content_elements_reject_sub(element: str) -> None:
  payload = {**MINIMAL_PAYLOADS[element], "content": ({"element": "sub"},)}
  with pytest.raises(ValidationError):
    NODE_CLASSES[element].model_validate(payload)


def test_hi_recurses_into_hi() -> None:
  payload = {"element": "hi", "content": ({"element": "hi", "content": ("inner",)}, "outer")}
  node = Hi.model_validate(payload)
  assert node.content[0].content == ("inner",)  # ty: ignore[unresolved-attribute]
  assert node.content[1] == "outer"


@pytest.mark.parametrize(
  ("element", "field", "payloads", "expected_elements"),
  [
    (
      "header",
      "metadata",
      [{"element": "note"}, {"element": "prop", "type": "x"}, {"element": "note"}],
      ["note", "prop", "note"],
    ),
    (
      "header",
      "metadata",
      [
        {"element": "note"},
        {"element": "prop", "type": "x"},
        {"element": "ude", "name": "u", "maps": [{"element": "map", "unicode": "#x41"}]},
      ],
      ["note", "prop", "ude"],
    ),
    (
      "tu",
      "metadata",
      [{"element": "prop", "type": "x"}, {"element": "note"}, {"element": "prop", "type": "y"}],
      ["prop", "note", "prop"],
    ),
    (
      "tu",
      "variants",
      [{"element": "tuv", "xml_lang": "en"}, {"element": "tuv", "xml_lang": "de"}],
      ["tuv", "tuv"],
    ),
  ],
)
def test_tuple_fields_keep_document_order(
  element: str, field: str, payloads: list[dict[str, Any]], expected_elements: list[str]
) -> None:
  payload = {**MINIMAL_PAYLOADS[element], field: payloads}
  node = NODE_CLASSES[element].model_validate(payload)
  children = getattr(node, field)
  assert isinstance(children, tuple)
  assert [child.element for child in children] == expected_elements


def test_header_metadata_accepts_ude_but_tu_metadata_does_not() -> None:
  header = make_header(metadata=[MINIMAL_PAYLOADS["ude"]])
  assert header.metadata[0].element == "ude"
  payload = {**MINIMAL_PAYLOADS["tu"], "metadata": [MINIMAL_PAYLOADS["ude"]]}
  with pytest.raises(ValidationError) as raised:
    TranslationUnit.model_validate(payload)
  assert "ude" in str(raised.value)


@pytest.mark.parametrize(("element", "field"), [("tu", "variants"), ("ude", "maps")])
def test_nonempty_tuple_fields_reject_an_empty_list(element: str, field: str) -> None:
  payload = {**MINIMAL_PAYLOADS[element], field: []}
  with pytest.raises(ValidationError) as raised:
    NODE_CLASSES[element].model_validate(payload)
  assert raised.value.errors()[0]["type"] == "too_short"
  assert raised.value.errors()[0]["loc"] == (field,)


def test_hex_integers_round_trip_through_json() -> None:
  mapping = Map.model_validate({"element": "map", "unicode": "#xF8FF", "code": "#x1F600"})
  assert mapping.unicode == 0xF8FF
  assert mapping.code == 0x1F600
  assert '"unicode":"#xF8FF","code":"#x1F600"' in mapping.model_dump_json()
  assert Map.model_validate_json(mapping.model_dump_json()) == mapping


@pytest.mark.parametrize("value", ["#xD800", "#x110000", "#x-1"])
def test_map_unicode_must_be_a_unicode_scalar_value(value: str) -> None:
  with pytest.raises(ValidationError):
    Map.model_validate({"element": "map", "unicode": value})


@pytest.mark.parametrize(("field", "value"), [("ent", "&nbsp;"), ("subst", "&amp;")])
def test_map_ent_and_subst_take_ascii_text(field: str, value: str) -> None:
  mapping = Map.model_validate({"element": "map", "unicode": "#x41", field: value})
  assert getattr(mapping, field) == value


@pytest.mark.parametrize(("field", "value"), [("ent", "café"), ("subst", "españa")])
def test_map_ent_and_subst_reject_non_ascii_text(field: str, value: str) -> None:
  with pytest.raises(ValidationError) as raised:
    Map.model_validate({"element": "map", "unicode": "#x41", field: value})
  assert raised.value.errors()[0]["loc"] == (field,)
  assert raised.value.errors()[0]["type"] == "value_error"


def test_tuid_takes_no_whitespace() -> None:
  assert TranslationUnit.model_validate({**MINIMAL_PAYLOADS["tu"], "tuid": "a-b"}).tuid == "a-b"
  with pytest.raises(ValidationError):
    TranslationUnit.model_validate({**MINIMAL_PAYLOADS["tu"], "tuid": "a b"})


def test_datetimes_keep_their_explicit_offset() -> None:
  header = make_header(creationdate="20240302T010203+0100")
  assert header.creationdate == datetime(2024, 3, 2, 1, 2, 3, tzinfo=timezone(timedelta(hours=1)))
  assert '"creationdate":"20240302T010203+0100"' in header.model_dump_json()


def test_integers_take_decimal_strings_and_serialize_as_strings() -> None:
  variant = TranslationUnitVariant.model_validate({**MINIMAL_PAYLOADS["tuv"], "usagecount": "3"})
  assert variant.usagecount == 3
  assert '"usagecount":"3"' in variant.model_dump_json()


def test_unknown_encoding_names_warn_but_are_kept() -> None:
  with pytest.warns(TmxWarning):
    header = make_header(o_encoding="x-unknown")
  assert header.o_encoding == "x-unknown"


@pytest.mark.parametrize("segtype", ["block", "paragraph", "sentence", "phrase"])
def test_segtype_takes_the_four_spec_values(segtype: str) -> None:
  assert make_header(segtype=segtype).segtype == segtype
  assert TranslationUnit.model_validate({**MINIMAL_PAYLOADS["tu"], "segtype": segtype}).segtype == segtype


@pytest.mark.parametrize("segtype", ["word", "SENTENCE", "", "sentence "])
def test_segtype_rejects_other_values(segtype: str) -> None:
  with pytest.raises(ValidationError):
    make_header(segtype=segtype)


@pytest.mark.parametrize("pos", ["begin", "end"])
def test_it_pos_takes_begin_and_end(pos: str) -> None:
  assert It.model_validate({**MINIMAL_PAYLOADS["it"], "pos": pos}).pos == pos


@pytest.mark.parametrize("pos", ["middle", "start", "", None])
def test_it_pos_rejects_other_values(pos: str | None) -> None:
  with pytest.raises(ValidationError):
    It.model_validate({**MINIMAL_PAYLOADS["it"], "pos": pos})


@pytest.mark.parametrize("assoc", ["p", "f", "b"])
def test_ph_assoc_takes_p_f_and_b(assoc: str) -> None:
  assert Ph.model_validate({**MINIMAL_PAYLOADS["ph"], "assoc": assoc}).assoc == assoc


@pytest.mark.parametrize("assoc", ["x", "prev", ""])
def test_ph_assoc_rejects_other_values(assoc: str | None) -> None:
  with pytest.raises(ValidationError):
    Ph.model_validate({**MINIMAL_PAYLOADS["ph"], "assoc": assoc})


def test_srclang_takes_the_all_literal() -> None:
  assert make_header().srclang == "*all*"
  assert TranslationUnit.model_validate(MINIMAL_PAYLOADS["tu"]).srclang == "*all*"


def test_srclang_is_normalized_to_lowercase() -> None:
  assert make_header(srclang="EN-US").srclang == "en-us"


def test_srclang_all_literal_is_case_insensitive() -> None:
  assert make_header(srclang="*ALL*").srclang == "*all*"


def test_model_dump_keeps_native_python_values() -> None:
  header = make_header(creationdate="20240302T010203Z", metadata=[{"element": "note", "text": "n"}])
  dumped = header.model_dump()
  assert type(dumped["creationdate"]) is datetime
  assert isinstance(dumped["metadata"], tuple)
  assert dumped["metadata"][0]["text"] == "n"


def test_json_output_uses_the_spec_prescribed_forms() -> None:
  mapping = Map.model_validate({"element": "map", "unicode": "#x41", "code": "#x1F600", "ent": "&nbsp;"})
  assert mapping.model_dump_json() == (
    '{"element":"map","unicode":"#x41","code":"#x1F600","ent":"&nbsp;","subst":null}'
  )
  bpt = Bpt.model_validate({"element": "bpt", "i": 1, "content": ("text", {"element": "sub"})})
  assert bpt.model_dump_json() == (
    '{"element":"bpt","i":"1","x":null,"type":null,"content":'
    '["text",{"element":"sub","datatype":null,"type":null,"content":[]}]}'
  )


def test_json_round_trip_is_value_stable() -> None:
  header = make_header(
    creationdate="20240302T010203+0100",
    o_encoding="iso-8859-1",
    metadata=[{"element": "note", "text": "n"}, {"element": "prop", "type": "x"}],
  )
  assert Header.model_validate_json(header.model_dump_json()) == header
  unit = TranslationUnit.model_validate({**MINIMAL_PAYLOADS["tu"], "tuid": "a-b"})
  assert TranslationUnit.model_validate_json(unit.model_dump_json()) == unit


def test_ut_instantiation_warns() -> None:
  with pytest.warns(DeprecationWarning, match="<ut>"):
    node = Ut()  # ty: ignore[deprecated]
  assert node.element == "ut"


@pytest.mark.parametrize(("element", "factory"), LANG_NODE_FACTORIES)
def test_lang_access_warns_but_construction_stays_silent(element: str, factory: Callable[[], TmxModel]) -> None:
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    node = factory()
  with pytest.warns(DeprecationWarning):
    _ = node.lang  # ty: ignore[unresolved-attribute]


@pytest.mark.parametrize("schema_class", [Note, Property, TranslationUnitVariant], ids=["note", "prop", "tuv"])
def test_lang_is_marked_deprecated_in_the_json_schema(schema_class: type[TmxModel]) -> None:
  assert schema_class.model_json_schema()["properties"]["lang"]["deprecated"] is True


def test_ut_is_marked_deprecated_in_the_json_schema() -> None:
  definition = Ut.model_json_schema()["$defs"]["Ut"]  # ty: ignore[deprecated]
  assert definition["deprecated"] is True
  assert "deprecated" in definition["description"]


def test_validation_error_cause_keeps_the_raised_error() -> None:
  with pytest.raises(ValidationError) as raised:
    Note.model_validate({"element": "note", "xml_lang": "zzz bogus"})
  causes = collect_exceptions(raised.value.__cause__, LanguageTagError)
  assert causes, "LanguageTagError expected somewhere in the cause chain"
  assert "zzz bogus" in str(causes[0])
