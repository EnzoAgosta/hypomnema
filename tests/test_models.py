"""Model contracts from the review: explicit discrimination, the
metadata/variants split, nonempty required children, the two inline
grammars, language advisories, and the deprecation warnings.

Covers GAPS decisions 4, 5, 8, and 15, plus the assignment and tuple
policies of decisions 7 and 11. Field names are the settled ones:
``metadata``/``variants`` on the unit, ``metadata``/``content`` on the
variant, ``metadata`` on the header. Happy-path constructions pass tuples
(the stored form); deliberately list-typed or type-foreign inputs are
routed through ``as_runtime_input`` to bypass static checking, because
their rejection or conversion is the behavior under test.
"""

import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from hypomnema.models import (
  Bpt,
  Ept,
  Header,
  Hi,
  It,
  Map,
  Note,
  Ph,
  Property,
  Sub,
  TranslationUnit,
  TranslationUnitVariant,
  Ut,
  Ude,
)

with warnings.catch_warnings():
  warnings.simplefilter("ignore")  # the ut advisory is tested on its own
  SEG_NODES = (Bpt(i=1), Ept(i=1), It(pos="begin"), Ph(), Hi(), Ut())

type LangModelFactory = Callable[..., Note | Property | TranslationUnitVariant]


def as_runtime_input(value: object) -> Any:
  """A value ty must not static-check against a field's nominal type.

  Deliberately invalid or type-foreign inputs are the point of several
  tests: the aliases accept string forms at runtime, lists convert to
  tuples, and Pydantic rejects the rest -- exactly the behavior under
  test.
  """
  return value


def variant(xml_lang: str = "en", *content: Any) -> TranslationUnitVariant:
  """A legal variant with the given inline content."""
  return TranslationUnitVariant(xml_lang=xml_lang, content=content)


def header(**overrides: Any) -> Header:
  """A legal header with every required attribute."""
  attributes: dict[str, Any] = {
    "creationtool": "ct",
    "creationtoolversion": "1.0",
    "segtype": "sentence",
    "o_tmf": "tmf",
    "adminlang": "en",
    "srclang": "en",
    "datatype": "plaintext",
  }
  attributes.update(overrides)
  return Header(**attributes)


LANG_MODELS: dict[str, LangModelFactory] = {
  "note": lambda lang, xml_lang: Note(lang=lang, xml_lang=xml_lang),
  "prop": lambda lang, xml_lang: Property(type="t", lang=lang, xml_lang=xml_lang),
  "tuv": lambda lang, xml_lang: TranslationUnitVariant(xml_lang=xml_lang, lang=lang, content=("x",)),
}
# The tuv is missing from this one: for a variant, legacy lang without
# xml_lang is an error (xml_lang is required), not a warning.
LANG_OPTIONAL_MODELS: dict[str, LangModelFactory] = {"note": LANG_MODELS["note"], "prop": LANG_MODELS["prop"]}


# Structural constraints (GAPS decision 5): models reject incomplete
# construction instead of deferring it to the writer's DTD check.


def test_translation_unit_requires_at_least_one_variant() -> None:
  with pytest.raises(ValidationError):
    TranslationUnit.model_validate({})
  with pytest.raises(ValidationError):
    TranslationUnit(variants=as_runtime_input([]))


def test_ude_requires_at_least_one_map() -> None:
  with pytest.raises(ValidationError):
    Ude.model_validate({"name": "example"})


def test_empty_variants_are_rejected_on_assignment() -> None:
  tu = TranslationUnit(variants=(variant(),))
  with pytest.raises(ValidationError):
    tu.variants = ()
  with pytest.raises(ValidationError):
    tu.variants = as_runtime_input([])


def test_empty_maps_are_rejected_on_assignment() -> None:
  ude = Ude(name="u", maps=(Map(unicode=as_runtime_input("#x41"), ent="A"),))
  with pytest.raises(ValidationError):
    ude.maps = ()


def test_a_single_variant_is_legal() -> None:
  # DTD floor is tuv+; the "logically two" prose is a convention, not a rule.
  tu = TranslationUnit(variants=(variant(),))
  assert tu.variants == (variant(),)


def test_empty_segment_content_is_legal() -> None:
  assert variant().content == ()


def test_empty_string_content_items_are_accepted() -> None:
  # GAPS decision 9 leaves XML round-trip semantics open; this pins the
  # model-layer baseline the decision starts from.
  tuv = variant("en", "", "after")
  assert tuv.content == ("", "after")


def test_tuv_metadata_and_content_are_independent() -> None:
  tuv = TranslationUnitVariant(xml_lang="en", metadata=(Note(text="n"),), content=("seg text",))
  assert type(tuv.metadata[0]) is Note
  assert tuv.content == ("seg text",)


@pytest.mark.parametrize("value", ["nope", 42, {}, None, [42], (42,)])
def test_variants_reject_non_sequences_and_non_variant_elements(value: Any) -> None:
  with pytest.raises(ValidationError):
    TranslationUnit(variants=value)


def test_variants_reject_metadata_models() -> None:
  with pytest.raises(ValidationError):
    TranslationUnit(variants=as_runtime_input([Note()]))


# Tuple behavior (decision 7): lists are accepted, tuples are stored, and
# augmented rebinding revalidates.


def test_list_input_is_stored_as_tuple() -> None:
  tu = TranslationUnit(variants=as_runtime_input([variant(), variant("de")]))
  assert type(tu.variants) is tuple
  ude = Ude(name="u", maps=as_runtime_input([Map(unicode=as_runtime_input("#x41"), ent="A")]))
  assert type(ude.maps) is tuple


def test_tuple_input_is_accepted() -> None:
  tu = TranslationUnit(variants=(variant(),))
  assert type(tu.variants) is tuple


def test_augmented_rebind_revalidates() -> None:
  tu = TranslationUnit(variants=(variant(),))
  tu.variants += (variant("de"),)
  assert len(tu.variants) == 2
  with pytest.raises(ValidationError):
    tu.variants += as_runtime_input((42,))


def test_the_container_is_immutable() -> None:
  tu = TranslationUnit(variants=(variant(),))
  with pytest.raises(AttributeError):
    tu.variants.append(variant())  # ty: ignore[unresolved-attribute]


def test_child_mutation_does_not_revalidate_the_parent() -> None:
  # Decision 7: no parent tracking or cascading validation. The child
  # assignment validates locally and succeeds silently.
  tu = TranslationUnit(variants=(variant(),))
  tu.variants[0].xml_lang = "de"
  assert tu.variants[0].xml_lang == "de"


def test_failed_child_assignment_still_validates_locally() -> None:
  tuv = variant()
  with pytest.raises(ValidationError):
    tuv.xml_lang = "en US"  # not a well-formed tag


# Explicit discrimination (GAPS decision 4): node identity comes from the
# class or an explicit tag, never from field-shape guessing.

TAGGED_INLINE = (
  ({"element": "bpt", "i": 1}, Bpt),
  ({"element": "ept", "i": 1}, Ept),
  ({"element": "ph"}, Ph),
  ({"element": "it", "pos": "begin"}, It),
  ({"element": "hi"}, Hi),
  ({"element": "ut"}, Ut),
)


@pytest.mark.parametrize(("data", "expected"), TAGGED_INLINE)
def test_tagged_inline_dicts_select_their_model(data: Any, expected: type) -> None:
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")  # the ut advisory is tested on its own
    tuv = TranslationUnitVariant(xml_lang="en", content=(data,))
  assert type(tuv.content[0]) is expected


@pytest.mark.parametrize("data", [{"i": 1}, {"pos": "begin"}, {"x": 1}, {"content": ["x"]}])
def test_untagged_ambiguous_inline_dicts_are_rejected(data: Any) -> None:
  with pytest.raises(ValidationError):
    TranslationUnitVariant(xml_lang="en", content=(data,))


def test_unknown_inline_tags_are_rejected() -> None:
  with pytest.raises(ValidationError):
    TranslationUnitVariant(xml_lang="en", content=as_runtime_input([{"element": "bogus", "i": 1}]))


def test_instances_and_strings_mix_without_tags() -> None:
  tuv = TranslationUnitVariant(xml_lang="en", content=("a", Bpt(i=1), Hi(), "b"))
  assert [type(node).__name__ for node in tuv.content] == ["str", "Bpt", "Hi", "str"]


def test_metadata_dicts_need_their_tag() -> None:
  with pytest.raises(ValidationError):
    TranslationUnit(variants=(variant(),), metadata=as_runtime_input([{"text": "n"}]))
  with pytest.raises(ValidationError):
    TranslationUnit(variants=(variant(),), metadata=as_runtime_input([{"type": "x"}]))


def test_tagged_metadata_dicts_are_accepted_in_any_order() -> None:
  tu = TranslationUnit(
    variants=(variant(),),
    metadata=as_runtime_input(
      [{"element": "note", "text": "n1"}, {"element": "prop", "type": "a"}, {"element": "note", "text": "n2"}]
    ),
  )
  assert [type(item).__name__ for item in tu.metadata] == ["Note", "Property", "Note"]


def test_the_sub_branch_needs_no_tag() -> None:
  b = Bpt(i=1, content=as_runtime_input(["code ", {"content": ["inner"]}]))
  assert type(b.content[1]) is Sub
  assert type(Bpt(i=1, content=(Sub(),)).content[0]) is Sub


def test_the_element_literal_is_frozen_and_pins_identity() -> None:
  with pytest.raises(ValidationError):
    Bpt.model_validate({"element": "ept", "i": 1})
  b = Bpt(i=1)
  with pytest.raises(ValidationError):
    b.element = as_runtime_input("ept")


def test_unknown_fields_are_rejected() -> None:
  with pytest.raises(ValidationError):
    Note.model_validate({"bogus": "x"})


# The two inline grammars: seg/hi/sub take general inline content; the
# paired and placeholder tags take text plus <sub> only (GAPS decision 4).


def test_bpt_content_takes_text_and_sub_only() -> None:
  b = Bpt(i=1, content=("text", Sub()))
  assert b.content == ("text", Sub())


@pytest.mark.parametrize("node", SEG_NODES)
def test_bpt_content_rejects_seg_level_inline_nodes(node: Any) -> None:
  with pytest.raises(ValidationError):
    Bpt(i=1, content=(node,))


def test_seg_content_rejects_sub() -> None:
  with pytest.raises(ValidationError):
    TranslationUnitVariant(xml_lang="en", content=as_runtime_input([Sub()]))


def test_sub_content_takes_the_general_grammar() -> None:
  s = Sub(content=("x", Bpt(i=1), Hi()))
  assert type(s.content[1]) is Bpt
  assert type(s.content[2]) is Hi


def test_hi_content_rejects_sub() -> None:
  with pytest.raises(ValidationError):
    Hi(content=as_runtime_input([Sub()]))


def test_sub_is_reachable_through_bpt_inside_hi() -> None:
  inner_sub = Sub(content=("x",))
  inner_bpt = Bpt(i=1, content=(inner_sub,))
  outer = Hi(content=(inner_bpt,))
  paired = outer.content[0]
  assert isinstance(paired, Bpt)
  assert paired.content[0] is inner_sub
  assert paired.content[0].content == ("x",)


def test_sub_does_not_nest_directly() -> None:
  with pytest.raises(ValidationError):
    Sub(content=as_runtime_input([Sub()]))


def test_inline_nesting_recurses() -> None:
  innermost_highlight = Hi(content=("e",))
  embedded_flow = Sub(content=(innermost_highlight,))
  code_token = Bpt(i=2, content=(embedded_flow,))
  tuv = TranslationUnitVariant(
    xml_lang="en", content=(Hi(content=("a", Hi(content=("b", Bpt(i=1), "c")), "d")), code_token)
  )
  outer_highlight = tuv.content[0]
  assert isinstance(outer_highlight, Hi)
  inner_highlight = outer_highlight.content[1]
  assert isinstance(inner_highlight, Hi)
  paired = inner_highlight.content[1]
  assert isinstance(paired, Bpt)
  assert paired.i == 1
  code_token = tuv.content[1]
  assert isinstance(code_token, Bpt)
  embedded_flow = code_token.content[0]
  assert isinstance(embedded_flow, Sub)
  innermost_highlight = embedded_flow.content[0]
  assert isinstance(innermost_highlight, Hi)
  assert innermost_highlight.content == ("e",)


def test_header_metadata_preserves_ude_interleaving() -> None:
  h = header(
    metadata=(Note(text="n"), Ude(name="u", maps=(Map(unicode=as_runtime_input("#x41"), ent="A"),)), Property(type="p"))
  )
  assert [type(item).__name__ for item in h.metadata] == ["Note", "Ude", "Property"]


def test_header_metadata_is_optional() -> None:
  assert header().metadata == ()


def test_header_required_attributes_are_enforced() -> None:
  attributes = {
    "creationtool": "ct",
    "creationtoolversion": "1.0",
    "segtype": "sentence",
    "o_tmf": "tmf",
    "adminlang": "en",
    "srclang": "en",
    "datatype": "plaintext",
  }
  for missing in attributes:
    partial = {key: value for key, value in attributes.items() if key != missing}
    with pytest.raises(ValidationError):
      Header.model_validate(partial)


# Deprecated language attributes (GAPS decision 8): models are silent
# (GAPS decision 19); the advisories fire in the validation pass and are
# tested in test_validation.py.


def test_tuv_xml_lang_is_required() -> None:
  with pytest.raises(ValidationError):
    TranslationUnitVariant.model_validate({"content": ["x"]})


def test_legacy_lang_cannot_substitute_for_xml_lang() -> None:
  with pytest.raises(ValidationError):
    TranslationUnitVariant.model_validate({"lang": "en", "content": ["x"]})


def test_tuv_lang_is_validated_as_a_tag() -> None:
  with pytest.raises(ValidationError):
    TranslationUnitVariant(xml_lang="en", lang="en US")


@pytest.mark.parametrize("build", LANG_MODELS.values(), ids=LANG_MODELS.keys())
def test_lang_equal_ignoring_case_is_silent(build: LangModelFactory) -> None:
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    build("EN-us", "en-US")


@pytest.mark.parametrize("build", LANG_MODELS.values(), ids=LANG_MODELS.keys())
def test_xml_lang_only_is_silent_and_leaves_lang_none(build: LangModelFactory) -> None:
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    model = build(None, "en")
  assert model.lang is None


def test_lang_spelling_is_preserved() -> None:
  note = Note(lang="EN-us")
  assert note.lang == "EN-us"


# Deprecation and recommendation warnings (GAPS decision 15): models are
# silent (GAPS decision 19); the advisories fire in the validation pass
# and are tested in test_validation.py.


@pytest.mark.parametrize("attributes", [{"code": "#x9F"}, {"ent": "copy"}, {"subst": "(c)"}])
def test_map_with_any_target_is_silent(attributes: dict[str, Any]) -> None:
  with warnings.catch_warnings():
    warnings.simplefilter("error")
    Map(unicode=as_runtime_input("#xF8FF"), **attributes)


# Serialization: tagged JSON, native Python dumps, round trips.


def test_python_dump_keeps_native_values_and_tags() -> None:
  tuv = TranslationUnitVariant(
    xml_lang="en", content=("a", Bpt(i=7, x=3)), lastusagedate=as_runtime_input("20240101T120000Z")
  )
  dumped = tuv.model_dump()
  assert dumped["content"][1] == {"element": "bpt", "i": 7, "x": 3, "type": None, "content": ()}
  assert dumped["lastusagedate"] == datetime(2024, 1, 1, 12, tzinfo=UTC)


def test_json_dump_serializes_values_as_strings() -> None:
  tuv = TranslationUnitVariant(
    xml_lang="en", content=("a", Bpt(i=7, x=3)), lastusagedate=as_runtime_input("20240101T120000Z")
  )
  dumped = tuv.model_dump(mode="json")
  assert dumped["content"][1]["i"] == "7"
  assert dumped["lastusagedate"] == "20240101T120000Z"


def test_tagged_json_round_trip_preserves_node_identity() -> None:
  original = TranslationUnit(
    variants=(variant("en", Hi(content=("x", Bpt(i=1)))), variant("de", "plain", Ph(x=2))),
    metadata=(Note(text="n"), Property(type="p")),
  )
  revived = TranslationUnit.model_validate_json(original.model_dump_json())
  assert revived == original
  assert type(revived.variants[0].content[0]) is Hi
  assert type(revived.variants[0].content[0].content[1]) is Bpt
  assert type(revived.variants[1].content[1]) is Ph


def test_exclude_defaults_can_drop_the_tag() -> None:
  # Documented caveat: omitting defaulted fields removes the tag, so the
  # result is not the complete round-trip representation.
  dumped = Hi().model_dump(exclude_defaults=True)
  assert "element" not in dumped
  assert Hi.model_validate(dumped) == Hi()


# Instance-trust policy (decision 7, verified by tests as it demands):
# Pydantic trusts existing model instances; only a data round trip is a
# deep check.


def test_model_validate_of_an_instance_is_identity() -> None:
  tu = TranslationUnit(variants=(variant(),))
  assert TranslationUnit.model_validate(tu) is tu


def test_constructed_invalid_children_embed_silently() -> None:
  # model_construct and model_copy(update=...) bypass validation entirely.
  bad = TranslationUnitVariant.model_construct(xml_lang="NOT A TAG", content=("x",))
  assert TranslationUnit(variants=(bad,)).variants == (bad,)  # accepted at construction
  tu = TranslationUnit(variants=(variant(),))
  tu.variants = (bad,)  # accepted at assignment
  assert tu.variants == (bad,)
  forged = variant().model_copy(update={"lang": "NOT A TAG"})
  assert forged.lang == "NOT A TAG"


def test_only_a_data_round_trip_is_a_deep_check() -> None:
  bad = TranslationUnitVariant.model_construct(xml_lang="NOT A TAG", content=("x",))
  tu = TranslationUnit.model_construct(variants=(bad,))
  with pytest.raises(ValidationError):
    TranslationUnit.model_validate(tu.model_dump())
  with pytest.raises(ValidationError):
    TranslationUnit.model_validate_json(tu.model_dump_json())


def test_validation_error_causes_are_retained_through_models() -> None:
  with pytest.raises(ValidationError) as excinfo:
    Bpt(i=as_runtime_input("not-a-number"))
  cause = excinfo.value.__cause__
  assert isinstance(cause, ExceptionGroup)
  assert all(isinstance(error, ValueError) for error in cause.exceptions)
