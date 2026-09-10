"""Tests for the strict validators in ``hypomnema.validation``.

Garbage can only enter a node through ``model_construct`` (the entry
boundary rejects it), so bad-value tests plant fields through the
``planted_*`` builders, which bypass validation; every clean-pass test
goes through the real constructor instead, pinning the soundness
contract: anything the entry boundary accepts must validate clean.

Following the same principle as ``test_errors.py``: assertions are
structural (``path``, ``value``, category), never advisory message text.
"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest

from hypomnema.errors import (
  NodePath,
  TmxAdvisory,
  TmxContractError,
  TmxDeprecationWarning,
  TmxErrorGroup,
  TmxFieldError,
  TmxFieldTypeError,
  TmxFieldValueError,
  TmxWarning,
)
from hypomnema.models import Header, Map, Note, Property, Ude
from hypomnema.validation import validate_header, validate_note, validate_property, validate_ude

# Builders. The ``planted_*`` constructors bypass the entry boundary via
# model_construct, so any field can hold any value; their defaults are a
# fully valid node. Fields defaulting to None (o_encoding, xml_lang, lang,
# the header optionals, the map targets) are therefore covered for "may be
# None" by the clean-pass tests alone.


def planted_note(**overrides: object) -> Note:
  fields: dict[str, Any] = dict(o_encoding=None, xml_lang=None, lang=None, text="note")
  fields.update(overrides)
  return Note.model_construct(**fields)


def planted_property(**overrides: object) -> Property:
  fields: dict[str, Any] = dict(
    element="prop", type="prop-type", xml_lang=None, o_encoding=None, lang=None, text="prop"
  )
  fields.update(overrides)
  return Property.model_construct(**fields)


def planted_map(**overrides: object) -> Map:
  fields: dict[str, Any] = dict(element="map", unicode=0xF8FF, code=None, ent=None, subst=None)
  fields.update(overrides)
  return Map.model_construct(**fields)


def planted_ude(**overrides: object) -> Ude:
  fields: dict[str, Any] = dict(element="ude", name="ude", base=None, maps=[planted_map(unicode=65, ent="&a;")])
  fields.update(overrides)
  return Ude.model_construct(**fields)


def planted_header(**overrides: object) -> Header:
  fields: dict[str, Any] = dict(
    element="header",
    creationtool="tool",
    creationtoolversion="1.0",
    segtype="paragraph",
    o_tmf="tmf",
    adminlang="en",
    srclang="en",
    datatype="plaintext",
    o_encoding=None,
    creationdate=None,
    creationid=None,
    changedate=None,
    changeid=None,
    metadata=[],
  )
  fields.update(overrides)
  return Header.model_construct(**fields)


def error_of(validate, node) -> TmxFieldError:
  """Runs ``validate(node)``, expecting exactly one field error."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(node)
  errors = excinfo.value.exceptions
  assert len(errors) == 1
  error = errors[0]
  assert isinstance(error, TmxFieldError)
  return error


def advisory_of(validate, node) -> TmxAdvisory:
  """Runs ``validate(node)``, asserting the group carries exactly one
  error and one advisory, and returning the advisory."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(node)
  assert len(excinfo.value.exceptions) == 1
  advisories = excinfo.value.advisories
  assert len(advisories) == 1
  return advisories[0]


def test_minimal_header_from_entry_boundary_validates_clean():
  validate_header(
    Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype="block",
      o_tmf="tmf",
      adminlang="en-GB",
      srclang="*all*",
      datatype="plaintext",
    )
  )


def test_full_header_from_entry_boundary_validates_clean():
  validate_header(
    Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype="paragraph",
      o_tmf="tmf",
      adminlang="en",
      srclang="fr",
      datatype="plaintext",
      o_encoding="utf-8",
      creationdate=datetime(2024, 1, 1, tzinfo=UTC),
      creationid="creator",
      changedate=datetime(2024, 6, 1, tzinfo=UTC),
      changeid="changer",
      metadata=[
        Note(text="note"),
        Property(type="client", text="acme"),
        Ude(name="win", base="windows-1252", maps=[Map(unicode=0xF8FF, code=0xF8FF, ent="&blob;")]),
      ],
    )
  )


def test_naive_datetimes_are_accepted():
  """Naive values are allowed and documented as UTC."""
  validate_header(
    Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype="paragraph",
      o_tmf="tmf",
      adminlang="en",
      srclang="en",
      datatype="plaintext",
      creationdate=datetime(2024, 1, 1),
    )
  )


def test_non_utc_offsets_are_accepted():
  """An explicit offset is kept as-is, not just UTC."""
  validate_header(
    Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype="paragraph",
      o_tmf="tmf",
      adminlang="en",
      srclang="en",
      datatype="plaintext",
      changedate=datetime(2024, 6, 1, tzinfo=timezone(timedelta(hours=5))),
    )
  )


def test_minimal_note_property_and_ude_validate_clean():
  validate_note(Note(text="note"))
  validate_property(Property(type="client"))
  validate_ude(Ude(name="ude", maps=[Map(unicode=65, ent="&a;")]))


def test_mutated_header_still_validates_clean():
  """The mutation workflow: append, change a child, re-validate."""
  header = Header(
    creationtool="tool",
    creationtoolversion="1.0",
    segtype="paragraph",
    o_tmf="tmf",
    adminlang="en",
    srclang="en",
    datatype="plaintext",
  )
  appended = Note(text="appended")
  header.metadata.append(appended)
  appended.text = "mutated"
  header.metadata.append(Note(lang="en", text="legacy"))
  validate_header(header)


def test_legacy_note_without_errors_raises_nothing():
  validate_note(Note(text="note", lang="en"))


def test_legacy_header_without_errors_raises_nothing():
  validate_header(
    Header(
      creationtool="tool",
      creationtoolversion="1.0",
      segtype="paragraph",
      o_tmf="tmf",
      adminlang="en",
      srclang="en",
      datatype="plaintext",
      metadata=[Note(lang="en", text="a"), Property(lang="fr", type="client")],
    )
  )


def test_map_target_advisory_alone_raises_nothing():
  validate_ude(planted_ude(base="windows-1252", maps=[planted_map(unicode=65)]))


def test_unknown_encoding_advisory_alone_raises_nothing():
  validate_note(planted_note(o_encoding="not-an-encoding"))


@pytest.mark.parametrize("segtype", ["block", "paragraph", "sentence", "phrase"])
def test_header_accepts_every_segment_type(segtype):
  """No member of the vocabulary may silently drop out of the check."""
  validate_header(planted_header(segtype=segtype))


@pytest.mark.parametrize("scalar", [0, 0xD7FF, 0xE000, 0x10FFFF])
def test_ude_accepts_unicode_scalar_boundaries(scalar):
  """Both range ends and both surrogate-range edges are scalar values."""
  validate_ude(planted_ude(base="windows-1252", maps=[planted_map(unicode=scalar, ent="&a;")]))


def test_ude_accepts_zero_code_with_base():
  validate_ude(planted_ude(base="windows-1252", maps=[planted_map(unicode=65, code=0)]))


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("creationtool", 42, TmxFieldTypeError),
    ("creationtoolversion", None, TmxFieldTypeError),
    ("segtype", 5, TmxFieldTypeError),
    ("segtype", "word", TmxFieldValueError),
    ("o_tmf", 42, TmxFieldTypeError),
    ("adminlang", 5, TmxFieldTypeError),
    ("adminlang", "not a tag!", TmxFieldValueError),
    ("srclang", 5, TmxFieldTypeError),
    ("srclang", "*ALL*", TmxFieldValueError),
    ("srclang", "not a tag!", TmxFieldValueError),
    ("datatype", 42, TmxFieldTypeError),
    ("o_encoding", 42, TmxFieldTypeError),
    ("creationdate", "2024-01-01T00:00:00", TmxFieldTypeError),
    ("creationid", 42, TmxFieldTypeError),
    ("changedate", 42, TmxFieldTypeError),
    ("changeid", 42, TmxFieldTypeError),
  ],
)
def test_header_rejects_bad_field_values(field, bad_value, expected_kind):
  error = error_of(validate_header, planted_header(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


def test_note_and_property_text_may_be_none():
  """The one optional field not already None in the builders' defaults;
  every other optional field is None by construction in the builders."""
  validate_note(planted_note(text=None))
  validate_property(planted_property(text=None))


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("o_encoding", 42, TmxFieldTypeError),
    ("xml_lang", 42, TmxFieldTypeError),
    ("xml_lang", "not a tag!", TmxFieldValueError),
    ("lang", 42, TmxFieldTypeError),
    ("lang", "not a tag!", TmxFieldValueError),
    ("text", 42, TmxFieldTypeError),
  ],
)
def test_note_rejects_bad_field_values(field, bad_value, expected_kind):
  error = error_of(validate_note, planted_note(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("type", None, TmxFieldTypeError),
    ("type", 42, TmxFieldTypeError),
    ("xml_lang", 42, TmxFieldTypeError),
    ("xml_lang", "not a tag!", TmxFieldValueError),
    ("o_encoding", 42, TmxFieldTypeError),
    ("lang", 42, TmxFieldTypeError),
    ("lang", "not a tag!", TmxFieldValueError),
    ("text", 42, TmxFieldTypeError),
  ],
)
def test_property_rejects_bad_field_values(field, bad_value, expected_kind):
  error = error_of(validate_property, planted_property(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("name", 42, TmxFieldTypeError),
    ("base", 42, TmxFieldTypeError),
    ("maps", 42, TmxFieldTypeError),
    ("maps", (planted_map(),), TmxFieldTypeError),
    ("maps", [], TmxContractError),
  ],
)
def test_ude_rejects_bad_field_values(field, bad_value, expected_kind):
  error = error_of(validate_ude, planted_ude(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("unicode", "x", TmxFieldTypeError),
    ("unicode", 0x110000, TmxFieldValueError),
    ("unicode", -1, TmxFieldValueError),
    ("unicode", 0xD800, TmxFieldValueError),
    ("unicode", True, TmxFieldTypeError),
    ("code", "5", TmxFieldTypeError),
    ("code", -1, TmxFieldValueError),
    ("code", True, TmxFieldTypeError),
    ("ent", 42, TmxFieldTypeError),
    ("ent", "café", TmxFieldValueError),
    ("subst", 42, TmxFieldTypeError),
    ("subst", "café", TmxFieldValueError),
  ],
)
def test_ude_rejects_bad_map_field_values(field, bad_value, expected_kind):
  # A valid base keeps the base-required contract rule out of the way:
  # the sweep tests one field at a time.
  error = error_of(validate_ude, planted_ude(base="windows-1252", maps=[planted_map(**{field: bad_value})]))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / "maps" / 0 / field


@pytest.mark.parametrize(
  ("validate", "plant", "foreign"),
  [
    (validate_header, planted_header, "ude"),
    (validate_note, planted_note, "prop"),
    (validate_property, planted_property, "note"),
    (validate_ude, planted_ude, "header"),
  ],
)
def test_rejects_foreign_element_literal(validate, plant, foreign):
  error = error_of(validate, plant(element=foreign))
  assert isinstance(error, TmxFieldValueError)
  assert error.path == NodePath() / "element"


def test_rejects_non_string_element():
  """The shared element check also type-guards before comparing."""
  error = error_of(validate_note, planted_note(element=42))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "element"


def test_header_rejects_foreign_metadata_item_without_cascading():
  error = error_of(validate_header, planted_header(metadata=["not a node"]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "metadata" / 0


def test_header_reports_wrong_metadata_container():
  error = error_of(validate_header, planted_header(metadata="not a list"))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "metadata"


def test_ude_reports_wrong_maps_container():
  error = error_of(validate_ude, planted_ude(maps="not a list"))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "maps"


def test_ude_reports_foreign_map_item_without_cascading():
  error = error_of(validate_ude, planted_ude(maps=["not a map", planted_map(unicode=65, ent="&a;")]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "maps" / 0


def test_ude_checks_the_siblings_of_a_foreign_map_item(leaf_errors):
  """The foreign item is reported once; its well-typed sibling is still
  descended into."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ude(planted_ude(maps=["not a map", planted_map(unicode=0xD800)]))
  paths = [error.path for error in leaf_errors(excinfo.value)]
  assert paths == [NodePath() / "maps" / 0, NodePath() / "maps" / 1 / "unicode"]


@pytest.mark.parametrize(
  ("validate", "wrong_node"),
  [
    (validate_header, lambda: planted_ude()),
    (validate_note, planted_header),
    (validate_property, planted_note),
    (validate_ude, planted_header),
  ],
)
def test_wrongly_typed_root_is_reported_at_root(validate, wrong_node, leaf_errors):
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(wrong_node())  # the wrong node type, on purpose
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert errors[0].path == NodePath()


def test_note_lang_gathers_deprecation_advisory():
  advisory = advisory_of(validate_note, planted_note(lang="en-GB", text=42))
  assert advisory.category is TmxDeprecationWarning
  assert advisory.path == NodePath() / "lang"


def test_property_lang_gathers_deprecation_advisory():
  advisory = advisory_of(validate_property, planted_property(lang="en-GB", text=42))
  assert advisory.category is TmxDeprecationWarning
  assert advisory.path == NodePath() / "lang"


def test_absent_lang_gathers_no_advisory():
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_note(planted_note(text=42))
  assert excinfo.value.advisories == ()


def test_note_unknown_encoding_gathers_advisory():
  advisory = advisory_of(validate_note, planted_note(o_encoding="not-an-encoding", text=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "o_encoding"


def test_header_unknown_encoding_gathers_advisory():
  advisory = advisory_of(validate_header, planted_header(o_encoding="not-an-encoding", creationtool=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "o_encoding"


def test_ude_unknown_base_encoding_gathers_advisory():
  advisory = advisory_of(validate_ude, planted_ude(base="not-an-encoding", name=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "base"


def test_ude_known_encoding_gathers_no_advisory():
  """The spec recommends IANA names; real codec names are fine."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ude(planted_ude(base="windows-1252", name=42))
  assert excinfo.value.advisories == ()


def test_map_without_target_gathers_advisory():
  advisory = advisory_of(validate_ude, planted_ude(maps=[planted_map(unicode=65)], name=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "maps" / 0


@pytest.mark.parametrize(
  "target",
  [dict(code=0), dict(ent="&a;"), dict(subst="x")],
  ids=["code", "ent", "subst"],
)
def test_map_with_target_gathers_no_advisory(target):
  """Each of code, ent, and subst alone satisfies the target rule."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ude(planted_ude(name=42, base="windows-1252", maps=[planted_map(unicode=65, **target)]))
  assert excinfo.value.advisories == ()


def test_advisories_arrive_in_traversal_order():
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_header(
      planted_header(
        creationtool=42,
        o_encoding="not-an-encoding",
        metadata=[planted_note(lang="en")],
      )
    )
  assert [advisory.path for advisory in excinfo.value.advisories] == [
    NodePath() / "o_encoding",
    NodePath() / "metadata" / 0 / "lang",
  ]


def test_base_required_when_a_map_carries_code():
  error = error_of(validate_ude, planted_ude(base=None, maps=[planted_map(unicode=65, code=0xF8FF)]))
  assert isinstance(error, TmxContractError)
  assert error.path == NodePath() / "base"


def test_base_not_required_without_code():
  validate_ude(planted_ude(base=None, maps=[planted_map(unicode=65, ent="&a;")]))


def test_wrongly_typed_base_does_not_silently_satisfy_the_rule():
  """A non-string base must not count as present."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ude(planted_ude(base=5, maps=[planted_map(unicode=65, code=0xF8FF)]))
  kinds = [type(error) for error in excinfo.value.exceptions]
  assert kinds == [TmxFieldTypeError, TmxContractError]


def test_only_well_typed_maps_count_for_the_rule():
  """A map whose code is not an integer is reported for its type; the
  base rule stays quiet about it."""
  error = error_of(validate_ude, planted_ude(base=None, maps=[planted_map(unicode=65, code="5")]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "maps" / 0 / "code"


def test_all_failures_arrive_in_one_flat_group(leaf_errors):
  """Every failure is a leaf of the single group: no nested groups, and
  paths follow the documented traversal order."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_header(
      planted_header(
        creationtool=42,
        segtype="word",
        metadata=["foreign", planted_note(text=42)],
      )
    )
  assert [error.path for error in leaf_errors(excinfo.value)] == [
    NodePath() / "creationtool",
    NodePath() / "segtype",
    NodePath() / "metadata" / 0,
    NodePath() / "metadata" / 1 / "text",
  ]


def test_errors_and_advisories_travel_separately(leaf_errors):
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_note(planted_note(lang="en", text=42))
  assert [error.path for error in leaf_errors(excinfo.value)] == [NodePath() / "text"]
  assert [advisory.path for advisory in excinfo.value.advisories] == [NodePath() / "lang"]
