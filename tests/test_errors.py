"""Tests for the error vocabulary in ``hypomnema.errors``.

Structural attributes (``path``, ``value``, ``expected``, ``category``) are
what consumers program against, so tests assert those; message strings are
asserted only where rendering itself is the feature (path formatting, value
truncation), so wording stays free to evolve.
"""

import dataclasses
import pickle
import warnings

import pytest

from hypomnema.errors import (
  LanguageTagError,
  NodePath,
  TmxAdvisory,
  TmxContractError,
  TmxDeprecationWarning,
  TmxError,
  TmxErrorGroup,
  TmxFieldError,
  TmxFieldTypeError,
  TmxFieldValueError,
  TmxSpecError,
  TmxWarning,
)


def test_nodepath_builds_with_slash_operator():
  """Append field names and indices in order with the slash operator."""
  path = NodePath() / "metadata" / 2 / "maps" / 0 / "code"
  assert path.segments == ("metadata", 2, "maps", 0, "code")


def test_nodepath_default_is_empty():
  """Start a node path with no field or index segments."""
  assert NodePath().segments == ()


def test_nodepath_renders_fields_and_indices():
  """Render nested fields with dots and list indices with brackets."""
  assert str(NodePath() / "metadata" / 2 / "maps" / 0 / "code") == "metadata[2].maps[0].code"


def test_nodepath_renders_single_field():
  """Render a single field without a leading separator."""
  assert str(NodePath() / "creationtool") == "creationtool"


def test_nodepath_renders_empty_path_as_root():
  """Display an empty path as the root location."""
  assert str(NodePath()) == "(root)"


def test_nodepath_is_immutable():
  # FrozenInstanceError subclasses AttributeError; asserting the specific
  # class pins the frozen-dataclass contract, not just immutability.
  """Reject reassignment of a frozen path's segments."""
  path = NodePath() / "creationtool"
  with pytest.raises(dataclasses.FrozenInstanceError):
    path.segments = ("other",)  # ty: ignore[invalid-assignment]


def test_nodepath_renders_leading_index():
  """Render an index at the root without a preceding field name."""
  assert str(NodePath() / 0 / "code") == "[0].code"


def test_type_error_names_expected_and_actual_types():
  """Retain the rejected value, field path, and expected type."""
  error = TmxFieldTypeError(NodePath() / "segtype", 5, str)
  assert error.path == NodePath() / "segtype"
  assert error.value == 5
  assert error.expected is str


def test_type_error_accepts_several_expected_types():
  """Retain a tuple of acceptable types in a field type error."""
  error = TmxFieldTypeError(NodePath() / "metadata" / 0, 7, (NodePath, TmxAdvisory))
  assert error.expected == (NodePath, TmxAdvisory)


def test_value_error_carries_reason():
  """Include the field path, rejected value, and reason in a value error."""
  error = TmxFieldValueError(NodePath() / "adminlang", "nope!", "not a language tag")
  assert error.path == NodePath() / "adminlang"
  assert error.value == "nope!"
  assert str(error) == "adminlang: not a language tag (value: 'nope!')"


def test_contract_error_carries_requirement():
  """Include the field path, value, and failed requirement in a contract error."""
  error = TmxContractError(NodePath() / "base", None, "required because maps[0].code is set")
  assert error.path == NodePath() / "base"
  assert error.value is None
  assert str(error) == "base: required because maps[0].code is set (value: None)"


def test_field_error_str_renders_path_message_and_value():
  """Render the location, expected and actual types, and rejected value."""
  error = TmxFieldTypeError(NodePath() / "segtype", 5, str)
  assert str(error) == "segtype: expected str, got int (value: 5)"


def test_field_error_str_renders_root_path():
  """Identify root-level type failures with the root marker."""
  error = TmxFieldTypeError(NodePath(), object(), TmxError)
  assert str(error).startswith("(root): expected TmxError, got object")


def test_field_error_str_renders_several_expected_types():
  """Join alternative expected type names with the word or."""
  error = TmxFieldTypeError(NodePath() / "metadata" / 0, 7, (NodePath, TmxAdvisory))
  assert str(error) == "metadata[0]: expected NodePath or TmxAdvisory, got int (value: 7)"


def test_field_error_leaves_repr_up_to_the_cap_untouched():
  """A repr of exactly the cap length (80) appears verbatim."""
  value = "x" * 78  # repr() adds the two quotes: exactly 80 characters
  error = TmxFieldValueError(NodePath() / "text", value, "rejected")
  assert f"(value: {value!r})" in str(error)


def test_field_error_truncates_repr_past_the_cap():
  """Cap rejected-value representations at 80 characters with a final ellipsis."""
  value = "x" * 79  # repr() is 81 characters (two quotes included): one over the cap
  error = TmxFieldValueError(NodePath() / "text", value, "rejected")
  assert f"(value: '{'x' * 76}...)" in str(error)


def test_error_hierarchy_slots_into_tmx_errors():
  """Keep all field errors catchable as specification and TMX errors."""
  assert issubclass(TmxFieldError, TmxSpecError)
  assert issubclass(TmxSpecError, TmxError)
  for kind in (TmxFieldTypeError, TmxFieldValueError, TmxContractError):
    assert issubclass(kind, TmxFieldError)


def test_warning_hierarchy_supports_category_filtering():
  """Keep deprecations under TmxWarning and preserve their emitted category."""
  assert issubclass(TmxDeprecationWarning, TmxWarning)
  assert issubclass(TmxWarning, UserWarning)
  with warnings.catch_warnings(record=True) as caught:
    warnings.warn("legacy lang", TmxDeprecationWarning)
  assert [warning.category for warning in caught] == [TmxDeprecationWarning]


@pytest.mark.parametrize(
  "error",
  [
    TmxFieldTypeError(NodePath() / "segtype", 5, str),
    TmxFieldValueError(NodePath() / "adminlang", "nope!", "not a language tag"),
    TmxContractError(NodePath() / "base", None, "required"),
  ],
  ids=["type", "value", "contract"],
)
def test_leaf_error_pickle_roundtrip_keeps_path_value_and_message(error: TmxFieldError):
  """Reconstruct each field-error kind with its original structured details."""
  clone = pickle.loads(pickle.dumps(error))
  assert isinstance(clone, type(error))
  assert clone.path == error.path
  assert clone.value == error.value
  assert clone.args[0] == error.args[0]


def test_type_error_pickle_roundtrip_keeps_expected():
  """Retain the expected type when a type error is pickled."""
  clone = pickle.loads(pickle.dumps(TmxFieldTypeError(NodePath(), 5, str)))
  assert clone.expected is str


def an_advisory(message: str = "advisory") -> TmxAdvisory:
  """Return a deprecation advisory for the legacy language field."""
  return TmxAdvisory(TmxDeprecationWarning, message, NodePath() / "lang")


def test_advisory_is_immutable():
  """Reject reassignment of a frozen advisory's message."""
  advisory = an_advisory()
  with pytest.raises(dataclasses.FrozenInstanceError):
    advisory.message = "changed"  # ty: ignore[invalid-assignment]


def two_errors() -> list[TmxFieldError]:
  """Fresh instances on every call: exceptions compare by identity."""
  return [
    TmxFieldTypeError(NodePath() / "segtype", 5, str),
    TmxFieldValueError(NodePath() / "adminlang", "nope!", "not a language tag"),
  ]


def test_error_group_holds_errors_and_advisories():
  """Store field errors and advisories separately in an error group."""
  errors = two_errors()
  advisory = an_advisory()
  group = TmxErrorGroup("failed to validate Header", errors, [advisory])
  assert group.message == "failed to validate Header"
  assert list(group.exceptions) == errors
  assert group.advisories == (advisory,)


def test_error_group_advisories_default_to_empty():
  """Use an empty advisory tuple when no advisories are supplied."""
  group = TmxErrorGroup("failed to validate Header", two_errors())
  assert group.advisories == ()


def test_error_group_rejects_empty():
  """Reject an error group without exception leaves."""
  with pytest.raises(ValueError):
    TmxErrorGroup("failed to validate Header", [])


def test_error_group_rejects_base_exception_leaves():
  """Reject BaseException leaves that are not ordinary Exceptions."""
  with pytest.raises(TypeError):
    TmxErrorGroup("failed", [KeyboardInterrupt()])  # ty: ignore[invalid-argument-type]


def test_error_group_derive_preserves_message_and_advisories():
  """Keep message and advisories when deriving a group of ordinary exceptions."""
  advisory = an_advisory()
  error = two_errors()[0]
  group = TmxErrorGroup("failed to validate Header", [error], [advisory])
  derived = group.derive([KeyboardInterrupt(), error])
  assert isinstance(derived, TmxErrorGroup)
  assert derived.message == group.message
  assert list(derived.exceptions) == [error]
  assert derived.advisories == (advisory,)


def test_error_group_split_returns_typed_groups_with_advisories():
  """Preserve the group type and advisories on both sides of a split."""
  errors = two_errors()
  advisory = an_advisory()
  group = TmxErrorGroup("failed", errors, [advisory])
  matched, rest = group.split(TmxFieldTypeError)
  assert isinstance(matched, TmxErrorGroup)
  assert list(matched.exceptions) == [errors[0]]
  assert matched.advisories == (advisory,)
  assert isinstance(rest, TmxErrorGroup)
  assert list(rest.exceptions) == [errors[1]]
  assert rest.advisories == (advisory,)


def test_error_group_pickle_roundtrip():
  """Pickling reconstructs fresh leaf instances, so compare structure."""
  group = TmxErrorGroup("failed to validate Header", two_errors(), [an_advisory()])
  clone = pickle.loads(pickle.dumps(group))
  assert isinstance(clone, TmxErrorGroup)
  assert clone.message == group.message
  assert [(error.path, error.value, error.args[0]) for error in leaf_errors(clone)] == [
    (error.path, error.value, error.args[0]) for error in leaf_errors(group)
  ]
  assert clone.advisories == group.advisories


def leaf_errors(group: BaseExceptionGroup) -> list[TmxFieldError]:
  """Return a group's leaves after asserting that every leaf is a field error."""
  assert all(isinstance(error, TmxFieldError) for error in group.exceptions)
  return [error for error in group.exceptions if isinstance(error, TmxFieldError)]


def test_except_star_filters_leaves_by_kind():
  """Handle each field-error kind separately without leaving an unhandled group."""
  try:
    raise TmxErrorGroup("failed", two_errors(), [an_advisory()])
  except* TmxFieldTypeError as field_type_errors:
    assert [error.path for error in leaf_errors(field_type_errors)] == [NodePath() / "segtype"]
  except* TmxFieldValueError as field_value_errors:
    assert [error.path for error in leaf_errors(field_value_errors)] == [NodePath() / "adminlang"]


def test_plain_except_catches_the_whole_group():
  """Catch all leaves and advisories together through a plain except clause."""
  with pytest.raises(TmxErrorGroup) as excinfo:
    raise TmxErrorGroup("failed", two_errors(), [an_advisory()])
  assert [error.path for error in leaf_errors(excinfo.value)] == [
    NodePath() / "segtype",
    NodePath() / "adminlang",
  ]
  assert excinfo.value.advisories == (an_advisory(),)


def test_unhandled_leaves_propagate_as_a_group():
  """Propagate unmatched leaves with their advisories after partial except* handling."""
  advisory = an_advisory()
  with pytest.raises(TmxErrorGroup) as excinfo:
    try:
      raise TmxErrorGroup("failed", two_errors(), [advisory])
    except* TmxFieldTypeError:
      pass
  assert [error.path for error in leaf_errors(excinfo.value)] == [NodePath() / "adminlang"]
  assert excinfo.value.advisories == (advisory,)


def test_language_tag_error_keeps_value_subclassing():
  """Expose language-tag details while remaining a ValueError."""
  error = LanguageTagError("nope!", "bad subtag")
  assert (error.tag, error.reason) == ("nope!", "bad subtag")
  assert str(error) == "not a well-formed BCP 47 language tag 'nope!': bad subtag"
  assert isinstance(error, ValueError)
