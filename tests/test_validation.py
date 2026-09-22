"""Test strict tree validation, error paths, and collected advisories.

The planted builders bypass constructor validation with model_construct so
individual invalid fields and relationships can be tested. Other cases use
normal construction or mutate existing models. Assertions inspect structured
paths, values, and categories rather than advisory message wording.
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
  Ude,
  Ut,
)
from hypomnema.validation import (
  validate_bpt,
  validate_ept,
  validate_header,
  validate_hi,
  validate_it,
  validate_note,
  validate_ph,
  validate_property,
  validate_sub,
  validate_translation_unit,
  validate_translation_unit_variant,
  validate_ude,
  validate_ut,
)

# Builders. The ``planted_*`` constructors bypass the entry boundary via
# model_construct, so any field can hold any value; their defaults are a
# fully valid node. Fields defaulting to None (o_encoding, xml_lang, lang,
# the header optionals, the map targets) are therefore covered for "may be
# None" by the clean-pass tests alone.


def planted_note(**overrides: object) -> Note:
  """Construct a valid note by default and inject overrides without validation."""
  fields: dict[str, Any] = dict(o_encoding=None, xml_lang=None, lang=None, text="note")
  fields.update(overrides)
  return Note.model_construct(**fields)


def planted_property(**overrides: object) -> Property:
  """Construct a default property and inject overrides without validation."""
  fields: dict[str, Any] = dict(
    element="prop", type="prop-type", xml_lang=None, o_encoding=None, lang=None, text="prop"
  )
  fields.update(overrides)
  return Property.model_construct(**fields)


def planted_map(**overrides: object) -> Map:
  """Construct a default character map and inject overrides without validation."""
  fields: dict[str, Any] = dict(element="map", unicode=0xF8FF, code=None, ent=None, subst=None)
  fields.update(overrides)
  return Map.model_construct(**fields)


def planted_ude(**overrides: object) -> Ude:
  """Construct an encoding with one valid map and inject unchecked overrides."""
  fields: dict[str, Any] = dict(element="ude", name="ude", base=None, maps=[planted_map(unicode=65, ent="&a;")])
  fields.update(overrides)
  return Ude.model_construct(**fields)


def planted_header(**overrides: object) -> Header:
  """Construct a minimal valid header and inject overrides without validation."""
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
  """Return the only field error raised by validating a test node.

  Args:
      validate: Validator expected to reject node.
      node: Model containing exactly one validation failure.

  Returns:
      The group's sole field error. The test fails if validation does not
      raise the expected group or its leaves are not exactly one field error.
  """
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(node)
  errors = excinfo.value.exceptions
  assert len(errors) == 1
  error = errors[0]
  assert isinstance(error, TmxFieldError)
  return error


def advisory_of(validate, node) -> TmxAdvisory:
  """Return the only advisory from a validation group containing one error.

  Args:
      validate: Validator expected to raise TmxErrorGroup for node.
      node: Model containing one invalid field and one advisory condition.

  Returns:
      The group's sole advisory. The test fails if validation does not raise
      the expected group or it contains another number of errors or advisories.
  """
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(node)
  assert len(excinfo.value.exceptions) == 1
  advisories = excinfo.value.advisories
  assert len(advisories) == 1
  return advisories[0]


def test_minimal_header_from_entry_boundary_validates_clean():
  """Accept a minimally constructed header with the all-languages wildcard."""
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
  """Accept a header with optional attributes and every allowed metadata kind."""
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
  """Accept minimal note, property, and user-defined encoding models."""
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
  """Allow a legacy language attribute when there are no validation errors."""
  validate_note(Note(text="note", lang="en"))


def test_legacy_header_without_errors_raises_nothing():
  """Allow legacy metadata language attributes on an otherwise valid header."""
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
  """Keep a missing-map-target advisory nonfatal without field errors."""
  validate_ude(planted_ude(base="windows-1252", maps=[planted_map(unicode=65)]))


def test_unknown_encoding_advisory_alone_raises_nothing():
  """Keep an unknown encoding name nonfatal without field errors."""
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
  """Treat code zero as a valid mapping when the base encoding is present."""
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
  """Report each invalid header field with the expected error kind and path."""
  error = error_of(validate_header, planted_header(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


def test_note_and_property_text_may_be_none():
  """Accept None as the text body of both notes and properties."""
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
  """Report each invalid note field with the expected error kind and path."""
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
  """Report each invalid property field with the expected error kind and path."""
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
  """Report invalid encoding fields and map-list contracts at their field paths."""
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
  """Locate invalid map values under their encoding's maps list."""
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
  """Report an incorrect node discriminator at the element field."""
  error = error_of(validate, plant(element=foreign))
  assert isinstance(error, TmxFieldValueError)
  assert error.path == NodePath() / "element"


def test_rejects_non_string_element():
  """The shared element check also type-guards before comparing."""
  error = error_of(validate_note, planted_note(element=42))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "element"


def test_header_rejects_foreign_metadata_item_without_cascading():
  """Report one type error at an invalid header metadata item's index."""
  error = error_of(validate_header, planted_header(metadata=["not a node"]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "metadata" / 0


def test_header_reports_wrong_metadata_container():
  """Reject a non-list header metadata container at its field path."""
  error = error_of(validate_header, planted_header(metadata="not a list"))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "metadata"


def test_ude_reports_wrong_maps_container():
  """Reject a non-list map container at the maps field path."""
  error = error_of(validate_ude, planted_ude(maps="not a list"))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "maps"


def test_ude_reports_foreign_map_item_without_cascading():
  """Report one type error for a foreign object in the maps list."""
  error = error_of(validate_ude, planted_ude(maps=["not a map", planted_map(unicode=65, ent="&a;")]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "maps" / 0


def test_ude_checks_the_siblings_of_a_foreign_map_item(leaf_errors):
  """Report a foreign map item and continue checking its correctly typed sibling."""
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
    (validate_translation_unit_variant, lambda: planted_bpt()),
    (validate_bpt, lambda: planted_ept()),
    (validate_ept, lambda: planted_bpt()),
    (validate_it, lambda: planted_ph()),
    (validate_ph, lambda: planted_it()),
    (validate_hi, lambda: planted_ut()),
    (validate_ut, lambda: planted_hi()),
    (validate_sub, lambda: planted_bpt()),
  ],
)
def test_wrongly_typed_root_is_reported_at_root(validate, wrong_node, leaf_errors):
  """Locate an incorrect root node type at the empty path."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(wrong_node())  # the wrong node type, on purpose
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert errors[0].path == NodePath()


def test_note_lang_gathers_deprecation_advisory():
  """Attach a legacy-language deprecation advisory to a failing note validation."""
  advisory = advisory_of(validate_note, planted_note(lang="en-GB", text=42))
  assert advisory.category is TmxDeprecationWarning
  assert advisory.path == NodePath() / "lang"


def test_property_lang_gathers_deprecation_advisory():
  """Attach a legacy-language deprecation advisory to a failing property validation."""
  advisory = advisory_of(validate_property, planted_property(lang="en-GB", text=42))
  assert advisory.category is TmxDeprecationWarning
  assert advisory.path == NodePath() / "lang"


def test_absent_lang_gathers_no_advisory():
  """Omit legacy-language advisories when the language attribute is absent."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_note(planted_note(text=42))
  assert excinfo.value.advisories == ()


def test_note_unknown_encoding_gathers_advisory():
  """Attach an unknown-encoding advisory at the note's encoding field."""
  advisory = advisory_of(validate_note, planted_note(o_encoding="not-an-encoding", text=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "o_encoding"


def test_header_unknown_encoding_gathers_advisory():
  """Attach an unknown-encoding advisory at the header's encoding field."""
  advisory = advisory_of(validate_header, planted_header(o_encoding="not-an-encoding", creationtool=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "o_encoding"


def test_ude_unknown_base_encoding_gathers_advisory():
  """Attach an unknown-encoding advisory at the encoding definition's base field."""
  advisory = advisory_of(validate_ude, planted_ude(base="not-an-encoding", name=42))
  assert advisory.category is TmxWarning
  assert advisory.path == NodePath() / "base"


def test_ude_known_encoding_gathers_no_advisory():
  """The spec recommends IANA names; real codec names are fine."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ude(planted_ude(base="windows-1252", name=42))
  assert excinfo.value.advisories == ()


def test_map_without_target_gathers_advisory():
  """Attach a warning to a map without code, entity, or substitution targets."""
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
  """Report parent advisories before those from nested metadata."""
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
  """Require a base encoding when a mapping supplies a native code value."""
  error = error_of(validate_ude, planted_ude(base=None, maps=[planted_map(unicode=65, code=0xF8FF)]))
  assert isinstance(error, TmxContractError)
  assert error.path == NodePath() / "base"


def test_base_not_required_without_code():
  """Allow an entity-only mapping without a base encoding."""
  validate_ude(planted_ude(base=None, maps=[planted_map(unicode=65, ent="&a;")]))


def test_wrongly_typed_base_does_not_silently_satisfy_the_rule():
  """A non-string base must not count as present."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ude(planted_ude(base=5, maps=[planted_map(unicode=65, code=0xF8FF)]))
  kinds = [type(error) for error in excinfo.value.exceptions]
  assert kinds == [TmxFieldTypeError, TmxContractError]


def test_only_well_typed_maps_count_for_the_rule():
  """Report a noninteger map code without adding a missing-base contract error."""
  error = error_of(validate_ude, planted_ude(base=None, maps=[planted_map(unicode=65, code="5")]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "maps" / 0 / "code"


def test_all_failures_arrive_in_one_flat_group(leaf_errors):
  """Collect all field failures in one flat group in traversal order."""
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
  """Keep error leaves separate from nonfatal advisory records."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_note(planted_note(lang="en", text=42))
  assert [error.path for error in leaf_errors(excinfo.value)] == [NodePath() / "text"]
  assert [advisory.path for advisory in excinfo.value.advisories] == [NodePath() / "lang"]


# Builders for the variant and inline nodes. Only required fields are
# seeded; model_construct injects every default, which the clean-pass
# tests then pin.


def planted_tuv(**overrides: object) -> TranslationUnitVariant:
  """Construct an English variant and inject overrides without validation."""
  fields: dict[str, Any] = dict(xml_lang="en")
  fields.update(overrides)
  return TranslationUnitVariant.model_construct(**fields)


def planted_sub(**overrides: object) -> Sub:
  """Construct an empty subflow and inject overrides without validation."""
  fields: dict[str, Any] = dict()
  fields.update(overrides)
  return Sub.model_construct(**fields)


def planted_bpt(**overrides: object) -> Bpt:
  """Construct a begin code with pairing index 1 and inject unchecked overrides."""
  fields: dict[str, Any] = dict(i=1)
  fields.update(overrides)
  return Bpt.model_construct(**fields)


def planted_ept(**overrides: object) -> Ept:
  """Construct an end code with pairing index 1 and inject unchecked overrides."""
  fields: dict[str, Any] = dict(i=1)
  fields.update(overrides)
  return Ept.model_construct(**fields)


def planted_it(**overrides: object) -> It:
  """Construct a begin-position isolated code and inject unchecked overrides."""
  fields: dict[str, Any] = dict(pos="begin")
  fields.update(overrides)
  return It.model_construct(**fields)


def planted_ph(**overrides: object) -> Ph:
  """Construct an empty placeholder and inject overrides without validation."""
  fields: dict[str, Any] = dict()
  fields.update(overrides)
  return Ph.model_construct(**fields)


def planted_hi(**overrides: object) -> Hi:
  """Construct an empty highlight and inject overrides without validation."""
  fields: dict[str, Any] = dict()
  fields.update(overrides)
  return Hi.model_construct(**fields)


def planted_ut(**overrides: object) -> Ut:
  """Construct an empty legacy code and inject overrides without validation."""
  fields: dict[str, Any] = dict()
  fields.update(overrides)
  return Ut.model_construct(**fields)


# Soundness: a constructor-built content tree validates clean at every
# level, from the variant down to the innermost inline element.


def content_tree() -> tuple[TranslationUnitVariant, Bpt, Ept, It, Ph, Sub, Hi, Ut]:
  """Build a valid variant tree and return direct references to its child nodes.

  Returns:
      The variant, begin code, end code, isolated code, placeholder, subflow,
      highlight, and legacy code, in that order. Child references belong to
      the returned tree and can be mutated or validated independently.
  """
  hi = Hi(x=9)
  sub = Sub(datatype="rtf", content=[hi, "tail"])
  bpt = Bpt(i=1, x=2, content=["inside", sub])
  ept = Ept(i=1, content=[Sub(type="f", content=["x"])])
  it = It(pos="begin", content=["ok"])
  ph = Ph(x=3, assoc="f", content=["deep"])
  ut = Ut(x=4)
  tree = TranslationUnitVariant(
    xml_lang="en",
    metadata=[Note(text="n"), Property(type="client")],
    content=["before", bpt, ept, it, ph, Hi(content=[ut, "u"]), "after"],
  )
  return tree, bpt, ept, it, ph, sub, hi, ut


def test_content_tree_from_entry_boundary_validates_clean():
  """Validate a constructed content tree both as a variant and at each child root."""
  tree, bpt, ept, it, ph, sub, hi, ut = content_tree()
  validate_translation_unit_variant(tree)
  validate_bpt(bpt)
  validate_ept(ept)
  validate_it(it)
  validate_ph(ph)
  validate_sub(sub)
  validate_hi(hi)
  validate_ut(ut)


def test_mutated_content_tree_still_validates_clean():
  """Accept appended paired codes and text after model construction."""
  tree, bpt, *_ = content_tree()
  tree.content.append(Bpt(i=7))
  tree.content.append(Ept(i=7))
  bpt.content.append("appended")
  validate_translation_unit_variant(tree)


# Field sweeps: every field of every new node, wrong type and bad value.


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("xml_lang", 42, TmxFieldTypeError),
    ("xml_lang", "not a tag!", TmxFieldValueError),
    ("o_encoding", 42, TmxFieldTypeError),
    ("datatype", 42, TmxFieldTypeError),
    ("usagecount", "5", TmxFieldTypeError),
    ("usagecount", -1, TmxFieldValueError),
    ("usagecount", True, TmxFieldTypeError),
    ("lastusagedate", 42, TmxFieldTypeError),
    ("creationtool", 42, TmxFieldTypeError),
    ("creationtoolversion", 42, TmxFieldTypeError),
    ("creationdate", "2024-01-01T00:00:00", TmxFieldTypeError),
    ("creationid", 42, TmxFieldTypeError),
    ("changedate", 42, TmxFieldTypeError),
    ("o_tmf", 42, TmxFieldTypeError),
    ("changeid", 42, TmxFieldTypeError),
    ("lang", 42, TmxFieldTypeError),
    ("lang", "not a tag!", TmxFieldValueError),
    ("metadata", "not a list", TmxFieldTypeError),
    ("content", "not a list", TmxFieldTypeError),
  ],
)
def test_tuv_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid variant fields with the expected error kind and path."""
  error = error_of(validate_translation_unit_variant, planted_tuv(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("i", None, TmxFieldTypeError),
    ("i", -1, TmxFieldValueError),
    ("i", True, TmxFieldTypeError),
    ("x", "5", TmxFieldTypeError),
    ("x", -1, TmxFieldValueError),
    ("type", 42, TmxFieldTypeError),
    ("content", "not a list", TmxFieldTypeError),
  ],
)
def test_bpt_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid begin-code fields with the expected error kind and path."""
  error = error_of(validate_bpt, planted_bpt(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [("i", None, TmxFieldTypeError), ("i", True, TmxFieldTypeError), ("content", "not a list", TmxFieldTypeError)],
)
def test_ept_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid end-code fields with the expected error kind and path."""
  error = error_of(validate_ept, planted_ept(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


def test_tuv_metadata_children_are_field_validated(leaf_errors):
  """Report errors inside both note and property children of variant metadata."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(metadata=[planted_note(text=42), planted_property(type=42)]))
  errors = leaf_errors(excinfo.value)
  assert [error.path for error in errors] == [
    NodePath() / "metadata" / 0 / "text",
    NodePath() / "metadata" / 1 / "type",
  ]


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("pos", 42, TmxFieldTypeError),
    ("pos", "middle", TmxFieldValueError),
    ("x", "5", TmxFieldTypeError),
    ("type", 42, TmxFieldTypeError),
    ("content", "not a list", TmxFieldTypeError),
  ],
)
def test_it_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid isolated-code fields with the expected error kind and path."""
  error = error_of(validate_it, planted_it(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("x", "5", TmxFieldTypeError),
    ("assoc", "both", TmxFieldValueError),
    ("assoc", 42, TmxFieldTypeError),
    ("type", 42, TmxFieldTypeError),
    ("content", "not a list", TmxFieldTypeError),
  ],
)
def test_ph_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid placeholder fields with the expected error kind and path."""
  error = error_of(validate_ph, planted_ph(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("x", "5", TmxFieldTypeError),
    ("x", -1, TmxFieldValueError),
    ("type", 42, TmxFieldTypeError),
    ("content", "not a list", TmxFieldTypeError),
  ],
)
def test_hi_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid highlight fields with the expected error kind and path."""
  error = error_of(validate_hi, planted_hi(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [("x", "5", TmxFieldTypeError), ("x", -1, TmxFieldValueError), ("content", "not a list", TmxFieldTypeError)],
)
def test_ut_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid legacy-code fields with the expected error kind and path."""
  error = error_of(validate_ut, planted_ut(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [("datatype", 42, TmxFieldTypeError), ("type", 42, TmxFieldTypeError), ("content", "not a list", TmxFieldTypeError)],
)
def test_sub_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid subflow fields with the expected error kind and path."""
  error = error_of(validate_sub, planted_sub(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


# Element literals across the whole content vocabulary.


@pytest.mark.parametrize(
  ("validate", "plant", "foreign"),
  [
    (validate_translation_unit_variant, planted_tuv, "tu"),
    (validate_bpt, planted_bpt, "ept"),
    (validate_ept, planted_ept, "bpt"),
    (validate_it, planted_it, "ph"),
    (validate_ph, planted_ph, "it"),
    (validate_hi, planted_hi, "ut"),
    (validate_ut, planted_ut, "hi"),
    (validate_sub, planted_sub, "bpt"),
  ],
)
def test_content_node_rejects_foreign_element_literal(validate, plant, foreign):
  """Reject a content node whose discriminator names a different node kind."""
  error = error_of(validate, plant(element=foreign))
  assert isinstance(error, TmxFieldValueError)
  assert error.path == NodePath() / "element"


def test_content_node_rejects_non_string_element():
  """Report a discriminator type error before comparing its literal value."""
  error = error_of(validate_bpt, planted_bpt(element=42))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "element"


# Content dispatchers: each content list accepts exactly its declared
# union, foreign items are reported once, siblings are still checked.


@pytest.mark.parametrize(
  ("validate", "plant", "foreign", "expected_union"),
  [
    (validate_translation_unit_variant, planted_tuv, planted_sub(), (str, Bpt, Ept, Ph, It, Hi, Ut)),
    (validate_translation_unit_variant, planted_tuv, planted_note(), (str, Bpt, Ept, Ph, It, Hi, Ut)),
    (validate_bpt, planted_bpt, planted_hi(), (str, Sub)),
    (validate_ept, planted_ept, planted_hi(), (str, Sub)),
    (validate_it, planted_it, planted_bpt(), (str, Sub)),
    (validate_ph, planted_ph, planted_hi(), (str, Sub)),
    (validate_ut, planted_ut, planted_bpt(), (str, Sub)),
    (validate_hi, planted_hi, planted_sub(), (str, Bpt, Ept, Ph, It, Hi, Ut)),
    (validate_sub, planted_sub, planted_sub(), (str, Bpt, Ept, Ph, It, Hi, Ut)),
  ],
  ids=[
    "tuv-sub",
    "tuv-note",
    "bpt-hi",
    "ept-hi",
    "it-bpt",
    "ph-hi",
    "ut-bpt",
    "hi-sub",
    "sub-sub",
  ],
)
def test_content_rejects_foreign_items(validate, plant, foreign, expected_union, leaf_errors):
  """Report disallowed content once with the item's path and accepted type union."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(plant(content=[foreign]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxFieldTypeError)
  assert errors[0].path == NodePath() / "content" / 0
  assert errors[0].expected == expected_union


def test_tuv_metadata_rejects_ude():
  """A <tuv> may not hold a <ude> in its metadata, unlike a <header>."""
  error = error_of(validate_translation_unit_variant, planted_tuv(metadata=[planted_ude()]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "metadata" / 0


def test_content_checks_the_siblings_of_a_foreign_item(leaf_errors):
  """Continue validating nested siblings after an invalid content item."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_bpt(planted_bpt(content=[42, planted_sub(content=[42])]))
  assert [error.path for error in leaf_errors(excinfo.value)] == [
    NodePath() / "content" / 0,
    NodePath() / "content" / 1 / "content" / 0,
  ]


# Cyclic content: a node that is its own ancestor is reported once, at
# the first revisit; a shared subtree seen twice as siblings is legal.


def test_self_cycle_is_reported_once(leaf_errors):
  """Report a self-reference once at the first cyclic content item."""
  hi = planted_hi()
  hi.content.append(hi)
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_hi(hi)
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath() / "content" / 0


def test_whole_unit_reports_cyclic_content() -> None:
  """Keep external-identifier collection inside the cycle-protected walk."""
  hi = Hi(x=1)
  hi.content.append(hi)
  unit = TranslationUnit(variants=[TranslationUnitVariant(xml_lang="en", content=[hi])])
  with pytest.raises(TmxErrorGroup) as caught:
    validate_translation_unit(unit)
  assert len(caught.value.exceptions) == 1
  assert isinstance(caught.value.exceptions[0], TmxContractError)


def test_whole_unit_stops_at_content_depth_limit() -> None:
  """Reject very deep input without a second unbounded content traversal."""
  hi = deep_hi_chain(2000)
  unit = TranslationUnit(variants=[TranslationUnitVariant(xml_lang="en", content=[hi])])
  with pytest.raises(TmxErrorGroup) as caught:
    validate_translation_unit(unit)
  assert len(caught.value.exceptions) == 1
  assert isinstance(caught.value.exceptions[0], TmxContractError)


def test_three_node_cycle_is_reported_once(leaf_errors):
  """Report a cycle across begin code, subflow, and highlight at its first revisit."""
  bpt = planted_bpt()
  sub = planted_sub()
  hi = planted_hi()
  hi.content.append(bpt)
  sub.content.append(hi)
  bpt.content.append(sub)
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_bpt(bpt)
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath() / "content" / 0 / "content" / 0 / "content" / 0


def test_diamond_content_is_legal():
  """The same node referenced twice as siblings is not a cycle."""
  shared = planted_hi(content=["x"])
  validate_hi(planted_hi(content=[shared, shared, "tail"]))


def test_shared_node_across_branches_is_legal():
  """Allow the same node in separate branches without treating sharing as a cycle."""
  shared = planted_hi(content=["x"])
  tree = planted_hi(content=[shared, planted_hi(content=[shared])])
  validate_hi(tree)


# The depth bound: legitimate depth is walked, pathological depth is
# reported at the level where the walk stops.


def deep_hi_chain(height: int) -> Hi:
  """A chain of `height` <hi> elements, the innermost holding text."""
  node = planted_hi(content=["leaf"])
  for _ in range(height - 1):
    node = planted_hi(content=[node])
  return node


@pytest.mark.parametrize("height", [1, 63])
def test_deep_acyclic_content_validates_clean(height):
  """Accept highlight chains whose content remains below the depth limit."""
  validate_hi(deep_hi_chain(height))


@pytest.mark.parametrize("height", [64, 200])
def test_deeper_than_the_bound_is_reported(height, leaf_errors):
  """Stop overdeep traversal with one contract error at content depth 64."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_hi(deep_hi_chain(height))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  # The walk stops at the first item 64 levels down: 2 * 64 segments.
  assert errors[0].path == NodePath(("content", 0) * 64)


# Missing required fields (a node built past the entry boundary) are
# reported instead of crashing with an attribute error.


@pytest.mark.parametrize(
  ("validate", "empty", "required"),
  [
    (
      validate_header,
      Header.model_construct,
      ("creationtool", "creationtoolversion", "segtype", "o_tmf", "adminlang", "srclang", "datatype"),
    ),
    (validate_property, Property.model_construct, ("type",)),
    (validate_ude, Ude.model_construct, ("name", "maps")),
    (validate_translation_unit_variant, TranslationUnitVariant.model_construct, ("xml_lang",)),
    (validate_bpt, Bpt.model_construct, ("i",)),
    (validate_ept, Ept.model_construct, ("i",)),
    (validate_it, It.model_construct, ("pos",)),
    (validate_translation_unit, TranslationUnit.model_construct, ("variants",)),
  ],
)
def test_missing_required_fields_are_reported(validate, empty, required, leaf_errors):
  """Report each absent required field as a contract error in declaration order."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate(empty())
  errors = leaf_errors(excinfo.value)
  assert [type(error) for error in errors] == [TmxContractError] * len(required)
  assert [error.path for error in errors] == [NodePath() / name for name in required]


def test_missing_map_unicode_is_reported():
  """<map>'s own guard, reached through its <ude>."""
  error = error_of(validate_ude, planted_ude(maps=[Map.model_construct(element="map")]))
  assert isinstance(error, TmxContractError)
  assert error.path == NodePath() / "maps" / 0 / "unicode"


# Scope of this pass: the deprecation advisories ride on the translation
# unit pass, so a variant pass gathers none even for legacy `lang`.


def test_tuv_lang_gathers_deprecation_advisory():
  """Collect a variant's legacy-language advisory during variant validation."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(lang="en", xml_lang=42))
  assert len(excinfo.value.exceptions) == 1
  advisories = excinfo.value.advisories
  assert len(advisories) == 1
  assert advisories[0].category is TmxDeprecationWarning
  assert advisories[0].path == NodePath() / "lang"


def test_ut_gathers_deprecation_advisory():
  """The <ut> advisory rides on every pass that reaches one."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_ut(planted_ut(content=[42]))
  assert len(excinfo.value.exceptions) == 1
  advisories = excinfo.value.advisories
  assert len(advisories) == 1
  assert advisories[0].category is TmxDeprecationWarning
  assert advisories[0].path == NodePath()


@pytest.mark.parametrize(
  ("plant_item", "bad_path", "overrides"),
  [
    (planted_it, NodePath() / "content" / 0 / "pos", dict(pos="middle")),
    (planted_ph, NodePath() / "content" / 0 / "assoc", dict(assoc="both")),
    (planted_hi, NodePath() / "content" / 0 / "content" / 0, dict(content=[42])),
    (planted_ut, NodePath() / "content" / 0 / "content" / 0, dict(content=[42])),
  ],
)
def test_inline_nodes_in_content_are_field_validated(plant_item, bad_path, overrides, leaf_errors):
  """Locate invalid inline-node fields at their nested content paths."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[plant_item(**overrides)]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert errors[0].path == bad_path


def test_bpt_in_content_is_field_validated(leaf_errors):
  """Report both a begin-code field error and its missing matching end code."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[planted_bpt(type=42)]))
  errors = leaf_errors(excinfo.value)
  assert [error.path for error in errors] == [
    NodePath() / "content" / 0 / "type",
    NodePath() / "content" / 0,
  ]
  assert isinstance(errors[1], TmxContractError)


def test_ept_in_content_is_field_validated(leaf_errors):
  """Report both an end-code field error and its missing matching begin code."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[planted_ept(i=-1)]))
  errors = leaf_errors(excinfo.value)
  assert [error.path for error in errors] == [
    NodePath() / "content" / 0 / "i",
    NodePath() / "content" / 0,
  ]
  assert isinstance(errors[1], TmxContractError)


def test_sub_reached_through_content_is_field_validated(leaf_errors):
  """Locate an invalid subflow field reached through a begin code's content."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_bpt(planted_bpt(content=[planted_sub(datatype=42)]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert errors[0].path == NodePath() / "content" / 0 / "datatype"


def test_ut_content_items_are_checked(leaf_errors):
  """Accept text and subflows in legacy codes and locate foreign content items."""
  validate_ut(planted_ut(content=["text", planted_sub()]))
  error = error_of(validate_ut, planted_ut(content=[42]))
  assert error.path == NodePath() / "content" / 0


def test_depth_bound_applies_to_node_items(leaf_errors):
  """Report the offending node itself when the content depth limit is reached."""
  node = root = planted_hi()
  for _ in range(63):
    child = planted_hi()
    node.content.append(child)
    node = child
  innermost = planted_hi()
  node.content.append(innermost)
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_hi(root)
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath(("content", 0) * 64)
  assert errors[0].value is innermost


# Internal matching: bpt/ept pairing, per flow (the <seg> scope).


def test_pairing_matches_overlapping_ranges():
  """Allow overlapping begin/end ranges when their pairing indices match."""
  validate_translation_unit_variant(
    planted_tuv(
      content=[
        planted_bpt(i=1),
        planted_bpt(i=2),
        planted_ept(i=1),
        planted_ept(i=2),
      ]
    )
  )


def test_hi_is_transparent_for_pairing():
  """Pair a begin code with an end code inside a transparent highlight."""
  validate_translation_unit_variant(planted_tuv(content=[planted_bpt(i=1), planted_hi(content=[planted_ept(i=1)])]))


def test_sub_content_is_its_own_flow(leaf_errors):
  """Keep subflow end codes from closing begin codes in the enclosing flow."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(
      planted_tuv(
        content=[
          planted_bpt(i=1),
          planted_ph(content=[planted_sub(content=[planted_ept(i=1)])]),
        ]
      )
    )
  errors = leaf_errors(excinfo.value)
  assert [error.path for error in errors] == [
    NodePath() / "content" / 1 / "content" / 0 / "content" / 0,
    NodePath() / "content" / 0,
  ]


def test_duplicate_bpt_i_after_closure_is_reported(leaf_errors):
  """Report a reused begin-code index once, even after its earlier range closes."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[planted_bpt(i=1), planted_ept(i=1), planted_bpt(i=1)]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath() / "content" / 2


def test_duplicate_bpt_i_is_reported(leaf_errors):
  """<bpt> i must be unique within a flow."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[planted_bpt(i=1), planted_bpt(i=1), planted_ept(i=1)]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath() / "content" / 1


def test_bpt_without_subsequent_ept_is_reported(leaf_errors):
  """Report an unmatched begin code at its content position."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[planted_bpt(i=3)]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath() / "content" / 0


def test_ept_without_preceding_bpt_is_reported(leaf_errors):
  """Report an end code without an earlier matching begin code."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit_variant(planted_tuv(content=[planted_ept(i=3)]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxContractError)
  assert errors[0].path == NodePath() / "content" / 0


def test_only_well_typed_bpt_ept_participate_in_pairing(leaf_errors):
  """Report a noninteger pairing index without an additional unmatched-code error."""
  error = error_of(validate_translation_unit_variant, planted_tuv(content=[planted_bpt(i="x")]))
  assert error.path == NodePath() / "content" / 0 / "i"


# External matching: the cross-variant x advisory, riding on <tu>.


def planted_tu(**overrides: object) -> TranslationUnit:
  """Construct a unit with one English variant and inject unchecked overrides."""
  fields: dict[str, Any] = dict(srclang="en", variants=[planted_tuv()])
  fields.update(overrides)
  return TranslationUnit.model_construct(**fields)


def test_tu_from_entry_boundary_validates_clean():
  """Accept matching external identifiers in different orders across variants."""
  validate_translation_unit(
    TranslationUnit(
      srclang="en",
      variants=[
        TranslationUnitVariant(
          xml_lang="en",
          content=[
            "The ",
            Bpt(i=1, x=1, content=["{\\b "]),
            "black",
            Ept(i=1, content=["}"]),
            Bpt(i=2, x=2, content=["{\\i "]),
            "cat",
            Ept(i=2, content=["}"]),
          ],
        ),
        TranslationUnitVariant(
          xml_lang="fr",
          content=[
            "Le ",
            Bpt(i=1, x=2, content=["{\\i "]),
            "chat",
            Ept(i=1, content=["}"]),
            Bpt(i=2, x=1, content=["{\\b "]),
            "noir",
            Ept(i=2, content=["]"]),
          ],
        ),
      ],
    )
  )


def test_cross_variant_x_disagreement_gathers_advisory():
  """Warn at the variants list when external matching identifiers disagree."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(
        tuid="a b",  # one error so the advisory-bearing pass still raises
        variants=[
          planted_tuv(xml_lang="en", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
          planted_tuv(xml_lang="fr", content=[planted_bpt(i=1, x=2), planted_ept(i=1)]),
        ],
      )
    )
  assert len(excinfo.value.exceptions) == 1
  advisories = excinfo.value.advisories
  assert len(advisories) == 1
  assert advisories[0].category is TmxWarning
  assert advisories[0].path == NodePath() / "variants"


def test_cross_variant_x_agreement_gathers_no_advisory():
  """Avoid matching advisories when both variants use the same identifiers."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(
        tuid="a b",
        variants=[
          planted_tuv(xml_lang="en", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
          planted_tuv(xml_lang="fr", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
        ],
      )
    )
  assert excinfo.value.advisories == ()


def test_variant_without_x_does_not_participate():
  """A variant with no x-valued inline elements is not a disagreement."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(
        tuid="a b",
        variants=[
          planted_tuv(xml_lang="en", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
          planted_tuv(xml_lang="fr"),
        ],
      )
    )
  assert excinfo.value.advisories == ()


def test_x_inside_sub_content_participates(leaf_errors):
  """Include external identifiers inside embedded subflows in variant comparisons."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(
        tuid="a b",
        variants=[
          planted_tuv(xml_lang="en", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
          planted_tuv(
            xml_lang="fr",
            content=[
              planted_bpt(i=2, content=[planted_sub(content=[planted_hi(x=2)])]),
              planted_ept(i=2),
            ],
          ),
        ],
      )
    )
  assert [error.path for error in leaf_errors(excinfo.value)] == [NodePath() / "tuid"]
  assert [advisory.category for advisory in excinfo.value.advisories] == [TmxWarning]


def test_ut_x_is_excluded_from_external_matching():
  """Ignore legacy-code external identifiers while preserving their deprecation."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(
        tuid="a b",
        variants=[
          planted_tuv(xml_lang="en", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
          planted_tuv(xml_lang="fr", content=[planted_ut(x=5)]),
        ],
      )
    )
  assert [(advisory.category, advisory.path) for advisory in excinfo.value.advisories] == [
    (TmxDeprecationWarning, NodePath() / "variants" / 1 / "content" / 0)
  ]


def test_garbage_x_is_excluded_from_external_matching():
  """Exclude invalid external identifiers from cross-variant comparisons."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(
        tuid="a b",
        variants=[
          planted_tuv(xml_lang="en", content=[planted_bpt(i=1, x=1), planted_ept(i=1)]),
          planted_tuv(xml_lang="fr", content=[planted_bpt(i=2, x="junk"), planted_ept(i=2)]),
        ],
      )
    )
  assert excinfo.value.advisories == ()


# The <tu> node: fields, metadata, variants, and its wiring.


def test_tu_from_entry_boundary_minimal_validates_clean():
  """Accept a minimally constructed unit containing one English variant."""
  validate_translation_unit(TranslationUnit(variants=[TranslationUnitVariant(xml_lang="en")]))


@pytest.mark.parametrize(
  ("field", "bad_value", "expected_kind"),
  [
    ("tuid", "a b", TmxFieldValueError),
    ("tuid", 42, TmxFieldTypeError),
    ("o_encoding", 42, TmxFieldTypeError),
    ("datatype", 42, TmxFieldTypeError),
    ("usagecount", -1, TmxFieldValueError),
    ("lastusagedate", 42, TmxFieldTypeError),
    ("creationtool", 42, TmxFieldTypeError),
    ("creationtoolversion", 42, TmxFieldTypeError),
    ("creationdate", 42, TmxFieldTypeError),
    ("creationid", 42, TmxFieldTypeError),
    ("changedate", 42, TmxFieldTypeError),
    ("segtype", "word", TmxFieldValueError),
    ("changeid", 42, TmxFieldTypeError),
    ("o_tmf", 42, TmxFieldTypeError),
    ("srclang", 42, TmxFieldTypeError),
    ("srclang", "not a tag!", TmxFieldValueError),
    ("srclang", "*ALL*", TmxFieldValueError),
    ("metadata", "not a list", TmxFieldTypeError),
    ("variants", "not a list", TmxFieldTypeError),
    ("variants", 42, TmxFieldTypeError),
  ],
)
def test_tu_rejects_bad_field_values(field, bad_value, expected_kind):
  """Report invalid unit fields with the expected error kind and field path."""
  error = error_of(validate_translation_unit, planted_tu(**{field: bad_value}))
  assert isinstance(error, expected_kind)
  assert error.path == NodePath() / field


def test_tu_variants_minimum_is_reported(leaf_errors):
  """Report an empty variants list as a contract error."""
  error = error_of(validate_translation_unit, planted_tu(variants=[]))
  assert isinstance(error, TmxContractError)
  assert error.path == NodePath() / "variants"


def test_tu_metadata_rejects_ude(leaf_errors):
  """A <tu>'s metadata is <note>/<prop> only, like a <tuv>'s."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(planted_tu(metadata=[planted_ude()]))
  errors = leaf_errors(excinfo.value)
  assert len(errors) == 1
  assert isinstance(errors[0], TmxFieldTypeError)
  assert errors[0].path == NodePath() / "metadata" / 0
  assert errors[0].expected == (Note, Property)


def test_tu_metadata_lang_gathers_advisory():
  """Propagate metadata language deprecations through unit validation."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(planted_tu(tuid="a b", metadata=[planted_note(lang="en")]))
  assert len(excinfo.value.exceptions) == 1
  advisories = excinfo.value.advisories
  assert [advisory.path for advisory in advisories] == [NodePath() / "metadata" / 0 / "lang"]


def test_tu_validates_variants(leaf_errors):
  """Locate an invalid variant language under the parent unit's variants list."""
  error = error_of(validate_translation_unit, planted_tu(variants=[planted_tuv(xml_lang=42)]))
  assert isinstance(error, TmxFieldTypeError)
  assert error.path == NodePath() / "variants" / 0 / "xml_lang"


def test_ut_advisory_rides_on_every_pass_reaching_one(leaf_errors):
  """Collect a deeply nested legacy-code advisory during whole-unit validation."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    validate_translation_unit(
      planted_tu(tuid="a b", variants=[planted_tuv(content=[planted_hi(content=[planted_ut()])])])
    )
  assert [error.path for error in leaf_errors(excinfo.value)] == [NodePath() / "tuid"]
  advisories = excinfo.value.advisories
  assert [advisory.category for advisory in advisories] == [TmxDeprecationWarning]
  assert [advisory.path for advisory in advisories] == [NodePath() / "variants" / 0 / "content" / 0 / "content" / 0]
