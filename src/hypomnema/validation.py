"""Validate runtime model fields and TMX relationships without coercion.

Public ``validate_*`` functions inspect the supplied node and its descendants.
They return an advisory tuple on success or raise TmxErrorGroup with path-bearing
TmxFieldTypeError, TmxFieldValueError, and TmxContractError leaves. Catch the
whole group with ``except TmxErrorGroup`` or select leaf kinds with ``except*``.
Validation never repairs or mutates the input. XML character and DTD checks
happen separately during XML conversion and writing.

Advisories cover deprecated constructs, unknown encoding names, missing map
targets, and cross-variant code mismatches. They are data attached to an error
group's ``advisories`` tuple on failure and returned directly on success.
Validators never emit Python warnings.

Paths are relative to the validated root. Checks visit parent fields before
children and stop value checks after a field's type fails. Unmatched beginning
codes are reported at the end of their flow, so failures are not path-sorted.

Pairing uses ordered segment flows. Each variant and embedded Sub owns a flow;
Hi contributes to its enclosing flow. Beginning codes need unique identifiers
and a later ending code with the same identifier. Overlapping pairs are allowed.
Private checkers append findings to a shared session instead of raising them.
"""

import codecs
from collections.abc import Callable
from datetime import datetime
from functools import cache
from typing import TypeGuard, get_args

from .bcp47 import validate_well_formed_language_tag
from .coercion import validate_ascii, validate_tuid, validate_unicode_scalar, validate_unsigned_integer
from .errors import (
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
from .models import (
  Association,
  Bpt,
  Ept,
  Header,
  Hi,
  It,
  Map,
  Note,
  Ph,
  Position,
  Property,
  SegType,
  Sub,
  TmxModel,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)

__all__ = [
  "validate_bpt",
  "validate_ept",
  "validate_header",
  "validate_hi",
  "validate_it",
  "validate_map",
  "validate_note",
  "validate_ph",
  "validate_property",
  "validate_sub",
  "validate_translation_unit",
  "validate_translation_unit_variant",
  "validate_ude",
  "validate_ut",
]


class _Session:
  """Collect findings and ancestor identities for one validation pass.

  Attributes:
      errors: Field failures in traversal order.
      warnings: Advisory records returned on success or attached to errors.
      ancestors: Object identities on the active content descent path.
      x_values: External identifiers collected in the current variant.
  """

  __slots__ = ("ancestors", "errors", "warnings", "x_values")

  def __init__(self) -> None:
    """Start a validation pass with no findings or active ancestors."""
    self.errors: list[TmxFieldError] = []
    self.warnings: list[TmxAdvisory] = []
    self.x_values: set[int] = set()
    # ``id()`` of the content nodes on the current descent path. A node
    # whose id is here while the walk is still inside it is its own
    # ancestor: a cycle. A node seen elsewhere in the tree is fine.
    self.ancestors: list[int] = []

  def error(self, error: TmxFieldError) -> None:
    """Append a field failure without interrupting traversal."""
    self.errors.append(error)

  def warn(self, advisory: TmxAdvisory) -> None:
    """Append advisory data without emitting a Python warning."""
    self.warnings.append(advisory)

  def descend(self, node: object) -> None:
    """Push a content node identity onto the active ancestor path."""
    self.ancestors.append(id(node))

  def ascend(self) -> None:
    """Pop the identity added by the matching descend call."""
    self.ancestors.pop()

  def finish(self, node_name: str) -> tuple[TmxAdvisory, ...]:
    """Raise collected failures with advisories, or return the advisory tuple.

    Args:
        node_name: Model name to include in the group message.

    Raises:
        TmxErrorGroup: At least one field or relationship failed validation.
    """
    if self.errors:
      raise TmxErrorGroup(f"failed to validate {node_name}", self.errors, self.warnings)
    return tuple(self.warnings)


type _FieldCheck = Callable[[_Session, NodePath, object], None]
"""What an optional-field check looks like: session, path, unknown value."""

type _Flow = list[tuple[object, NodePath]]
"""The inline elements of one flow, in order: the spec's <seg> scope.
A flow is owned by a ``<tuv>``'s segment or a ``<sub>``'s embedded
segment; ``<hi>`` is transparent, so its inline elements join the
enclosing flow."""

_SEGMENT_TYPES: tuple[str, ...] = get_args(SegType.__value__)
_POSITIONS: tuple[str, ...] = get_args(Position.__value__)
_ASSOCIATIONS: tuple[str, ...] = get_args(Association.__value__)
_MAX_CONTENT_NESTING = 64
"""The most nesting levels of inline content one pass will walk.

Each nesting level (e.g. ``<bpt>`` → ``<sub>`` → ``<hi>`` → ``<bpt>``)
adds exactly two ``NodePath`` segments; a legal document never gets near
this bound, and a pathological one is reported rather than walked into
a raw ``RecursionError``."""


# Predicates shared by checkers and cross-field rules. Field rules consult
# the *runtime* type directly rather than "is not None", so a wrongly typed
# value does not silently satisfy a contract rule.


def _is_string(value: object) -> bool:
  """Return whether a value can participate in string-based contract checks."""
  return isinstance(value, str)


def _is_integer(value: object) -> TypeGuard[int]:
  """Return whether a value is an integer, excluding booleans."""
  # bool is an int subclass; it is not a number here.
  return isinstance(value, int) and not isinstance(value, bool)


# Checkers. All take (session, path, value), never raise, never mutate:
# they append at most a few errors and advisories to the session. A checker
# reporting a wrong type returns without value-checking that value.


@cache
def _required_fields(model_type: type[TmxModel]) -> tuple[str, ...]:
  """Read constructor requirements once per model class."""
  return tuple(name for name, field in model_type.model_fields.items() if field.is_required())


def _check_model[ModelType: TmxModel](
  node: object, model_type: type[ModelType], session: _Session, path: NodePath
) -> TypeGuard[ModelType]:
  """Check node type, required fields, and its declared element discriminator."""
  if not isinstance(node, model_type):
    session.error(TmxFieldTypeError(path, node, model_type))
    return False
  missing = [name for name in _required_fields(model_type) if not hasattr(node, name)]
  for name in missing:
    session.error(TmxContractError(path / name, None, "required field is missing"))
  if missing:
    return False
  value: object = getattr(node, "element", None)
  literal: object = model_type.model_fields["element"].default
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path / "element", value, str))
  elif value != literal:
    session.error(TmxFieldValueError(path / "element", value, f"expected the literal {literal!r}"))
  return True


def _check_value[Value](session: _Session, path: NodePath, value: Value, check: Callable[[Value], object]) -> None:
  """Attach a path to a shared scalar rule's failure without coercing its input."""
  try:
    check(value)
  except ValueError as error:
    session.error(TmxFieldValueError(path, value, str(error)))


def _check_optional(session: _Session, path: NodePath, value: object, check: _FieldCheck) -> None:
  """Run the supplied field check only when the value is not None."""
  if value is not None:
    check(session, path, value)


def _check_str(session: _Session, path: NodePath, value: object) -> None:
  """Record a type failure unless the value is a string."""
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))


def _check_ascii_text(session: _Session, path: NodePath, value: object) -> None:
  """Record a failure for a non-string or text containing non-ASCII characters."""
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  _check_value(session, path, value, validate_ascii)


def _check_unsigned_integer(session: _Session, path: NodePath, value: object) -> None:
  """Record a failure for booleans, non-integers, or negative integers."""
  if isinstance(value, bool) or not isinstance(value, int):
    session.error(TmxFieldTypeError(path, value, int))
    return
  _check_value(session, path, value, validate_unsigned_integer)


def _check_unicode_scalar(session: _Session, path: NodePath, value: object) -> None:
  """Record a failure unless the value is an integer Unicode scalar."""
  if isinstance(value, bool) or not isinstance(value, int):
    session.error(TmxFieldTypeError(path, value, int))
    return
  _check_value(session, path, value, validate_unicode_scalar)


def _check_datetime(session: _Session, path: NodePath, value: object) -> None:
  """Require a datetime, allowing naive values that output treats as UTC."""
  # Naive values are allowed and documented as UTC; an explicit offset is
  # kept as-is. All further ISO 8601 well-formedness was settled at the
  # entry boundary by parse_datetime.
  if not isinstance(value, datetime):
    session.error(TmxFieldTypeError(path, value, datetime))


def _check_language_tag(session: _Session, path: NodePath, value: object) -> None:
  """Record type or BCP 47 grammar failures without normalizing the value."""
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  _check_value(session, path, value, validate_well_formed_language_tag)


def _check_deprecated_lang(session: _Session, path: NodePath, value: object) -> None:
  """Check a legacy language attribute and collect its deprecation advisory."""
  _check_language_tag(session, path, value)
  session.warn(
    TmxAdvisory(
      TmxDeprecationWarning,
      "the lang attribute is deprecated since TMX 1.3 in favor of xml_lang",
      path,
    )
  )


def _check_srclang(session: _Session, path: NodePath, value: object) -> None:
  """Require a language tag or the exact source-language sentinel ``*all*``."""
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  if value.lower() == "*all*":
    # The entry boundary normalizes to the canonical spelling; strict
    # output expects it normalized.
    if value != "*all*":
      session.error(TmxFieldValueError(path, value, "expected the normalized spelling '*all*'"))
    return
  _check_language_tag(session, path, value)


def _check_one_of(session: _Session, path: NodePath, value: object, allowed: tuple[str, ...]) -> None:
  """Record a failure unless a string matches one of the allowed literals."""
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  if value not in allowed:
    session.error(TmxFieldValueError(path, value, f"expected one of {', '.join(map(repr, allowed))}"))


def _check_segtype(session: _Session, path: NodePath, value: object) -> None:
  """Require one of the four TMX segmentation literals."""
  _check_one_of(session, path, value, _SEGMENT_TYPES)


def _check_position(session: _Session, path: NodePath, value: object) -> None:
  """Require the isolated-code position to be begin or end."""
  _check_one_of(session, path, value, _POSITIONS)


def _check_association(session: _Session, path: NodePath, value: object) -> None:
  """Require the placeholder association to be p, f, or b."""
  _check_one_of(session, path, value, _ASSOCIATIONS)


def _check_tuid(session: _Session, path: NodePath, value: object) -> None:
  """Require a string without whitespace, allowing the empty string."""
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  _check_value(session, path, value, validate_tuid)


def _check_bpt_ept_pairing(flow: _Flow, session: _Session) -> None:
  """Collect missing matches and duplicate beginning-code identifiers.

  Each ending code consumes one earlier beginning code with the same identifier.
  Identifiers cannot be reused by another beginning code in the flow, even after
  closure. Overlapping pairs are allowed. Nodes with invalid identifier types
  are left to field validation.

  Args:
      flow: Inline nodes and their paths in segment order.
      session: Destination for pairing failures.
  """
  seen_i: set[int] = set()
  open_bpts: dict[int, tuple[NodePath, object]] = {}
  for node, path in flow:
    if isinstance(node, Bpt) and _is_integer(getattr(node, "i", None)):
      if node.i in seen_i:
        session.error(
          TmxContractError(path, node, f"duplicate <bpt> i {node.i}: the i attribute must be unique within a flow")
        )
      else:
        seen_i.add(node.i)
        open_bpts[node.i] = (path, node)
    elif isinstance(node, Ept) and _is_integer(getattr(node, "i", None)):
      if node.i in open_bpts:
        del open_bpts[node.i]
      else:
        session.error(TmxContractError(path, node, f"no preceding <bpt> with i {node.i} in this flow"))
  for i, (path, node) in open_bpts.items():
    session.error(TmxContractError(path, node, f"no subsequent <ept> with i {i} in this flow"))


def _check_encoding_name(session: _Session, path: NodePath, value: object) -> None:
  """Require a string and collect an advisory for an unknown codec name.

  Python's codec registry supplies the lookup. An unrecognized name remains
  acceptable because TMX encoding names can describe user-defined encodings.
  """
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  try:
    codecs.lookup(value)
  except LookupError:
    session.warn(
      TmxAdvisory(
        TmxWarning,
        f"encoding {value!r} is not recognized by Python's codecs; the spec recommends IANA charset identifiers",
        path,
      )
    )


def _check_list(
  session: _Session,
  path: NodePath,
  value: object,
  item_check: Callable[[object, _Session, NodePath], None],
  *,
  minimum: int = 0,
) -> None:
  """Check a list's type and minimum length, then visit each item.

  Args:
      session: Destination for failures and advisories.
      path: Path of the list field relative to the validated root.
      value: Runtime field value, which may not be a list.
      item_check: Checker receiving each item, session, and indexed path.
      minimum: Minimum allowed number of items. A short list is still traversed.
  """
  if not isinstance(value, list):
    session.error(TmxFieldTypeError(path, value, list))
    return
  if len(value) < minimum:
    session.error(TmxContractError(path, value, f"expected at least {minimum} item(s), got {len(value)}"))
  for index, item in enumerate(value):
    item_check(item, session, path / index)


# Node validators share scalar and model checks, then apply explicit
# node-specific field and relationship rules before recursing into children.


def _validate_header(header: object, session: _Session, path: NodePath) -> None:
  """Collect header field failures and recursively check its metadata."""
  if not _check_model(header, Header, session, path):
    return
  _check_str(session, path / "creationtool", header.creationtool)
  _check_str(session, path / "creationtoolversion", header.creationtoolversion)
  _check_segtype(session, path / "segtype", header.segtype)
  _check_str(session, path / "o_tmf", header.o_tmf)
  _check_language_tag(session, path / "adminlang", header.adminlang)
  _check_srclang(session, path / "srclang", header.srclang)
  _check_str(session, path / "datatype", header.datatype)
  _check_optional(session, path / "o_encoding", header.o_encoding, _check_encoding_name)
  _check_optional(session, path / "creationdate", header.creationdate, _check_datetime)
  _check_optional(session, path / "creationid", header.creationid, _check_str)
  _check_optional(session, path / "changedate", header.changedate, _check_datetime)
  _check_optional(session, path / "changeid", header.changeid, _check_str)
  _check_list(session, path / "metadata", header.metadata, _validate_metadata_node)


def _validate_metadata_node(node: object, session: _Session, path: NodePath) -> None:
  """Dispatch header metadata, reporting foreign child types once."""
  match node:
    case Note():
      _validate_note(node, session, path)
    case Property():
      _validate_property(node, session, path)
    case Ude():
      _validate_ude(node, session, path)
    case _:
      session.error(TmxFieldTypeError(path, node, (Note, Property, Ude)))


def _validate_note(note: object, session: _Session, path: NodePath) -> None:
  """Collect note field failures and legacy-language advisories."""
  if not _check_model(note, Note, session, path):
    return
  _check_optional(session, path / "o_encoding", note.o_encoding, _check_encoding_name)
  _check_optional(session, path / "xml_lang", note.xml_lang, _check_language_tag)
  _check_optional(session, path / "lang", note.lang, _check_deprecated_lang)
  _check_optional(session, path / "text", note.text, _check_str)


def _validate_property(property_node: object, session: _Session, path: NodePath) -> None:
  """Collect property field failures and legacy-language advisories."""
  if not _check_model(property_node, Property, session, path):
    return
  _check_str(session, path / "type", property_node.type)
  _check_optional(session, path / "xml_lang", property_node.xml_lang, _check_language_tag)
  _check_optional(session, path / "o_encoding", property_node.o_encoding, _check_encoding_name)
  _check_optional(session, path / "lang", property_node.lang, _check_deprecated_lang)
  _check_optional(session, path / "text", property_node.text, _check_str)


def _validate_map(map_node: object, session: _Session, path: NodePath) -> None:
  """Check mapping fields; leave parent-dependent rules to UDE validation."""
  if not _check_model(map_node, Map, session, path):
    return
  _check_unicode_scalar(session, path / "unicode", map_node.unicode)
  _check_optional(session, path / "code", map_node.code, _check_unsigned_integer)
  _check_optional(session, path / "ent", map_node.ent, _check_ascii_text)
  _check_optional(session, path / "subst", map_node.subst, _check_ascii_text)


def _validate_ude(ude: object, session: _Session, path: NodePath) -> None:
  """Check mappings, require a base for coded maps, and advise on missing targets."""
  if not _check_model(ude, Ude, session, path):
    return
  _check_str(session, path / "name", ude.name)
  _check_optional(session, path / "base", ude.base, _check_encoding_name)
  _check_list(session, path / "maps", ude.maps, _validate_map, minimum=1)
  # Cross-field rules consult only well-typed values, and skip a maps
  # field that is not even a list: garbage in speaks through its type
  # errors, the contract rules stay quiet.
  maps = ude.maps if isinstance(ude.maps, list) else ()
  if not _is_string(ude.base):
    for index, node in enumerate(maps):
      if isinstance(node, Map) and _is_integer(node.code):
        session.error(
          TmxContractError(
            path / "base",
            ude.base,
            f"required because maps[{index}].code is set",
          )
        )
        break
  for index, node in enumerate(maps):
    if not isinstance(node, Map):
      continue
    if not (_is_integer(node.code) or _is_string(node.ent) or _is_string(node.subst)):
      session.warn(
        TmxAdvisory(
          TmxWarning,
          "a <map> should specify at least one of code, ent, or subst",
          path / "maps" / index,
        )
      )


# Content-tree dispatchers. A content list mixes plain text with inline
# elements; each dispatcher validates one item and recurses into nodes.
# ``<hi>``, ``<sub>``, and ``<tuv>`` hold inline content (any inline
# element); the paired-content elements (text or ``<sub>``) are
# ``<bpt>``, ``<ept>``, ``<it>``, ``<ph>``, and ``<ut>``.


def _check_content_depth(session: _Session, path: NodePath, node: object) -> bool:
  """Record a contract failure when the content path reaches the depth limit.

  Each content nesting level adds a field name and list index to the path.
  The limit uses the full path length, including any enclosing variant indices.

  Returns:
      True if traversal may continue; False after recording a depth failure.
  """
  if len(path.segments) < 2 * _MAX_CONTENT_NESTING:
    return True
  session.error(TmxContractError(path, node, f"content nested deeper than {_MAX_CONTENT_NESTING} levels"))
  return False


def _check_content_acyclic(session: _Session, path: NodePath, node: object) -> bool:
  """Record a contract failure if this node is already an active ancestor.

  Sharing a node between separate branches is allowed. Only a reference back
  to an ancestor on the current descent path is a cycle.

  Returns:
      True if the node may be visited; False after recording a cycle failure.
  """
  if id(node) not in session.ancestors:
    return True
  session.error(TmxContractError(path, node, "cyclic content: this element is its own ancestor"))
  return False


def _validate_inline_content_node(node: object, session: _Session, path: NodePath, flow: _Flow) -> None:
  """Check one text or inline item and add inline nodes to the pairing flow.

  Args:
      node: Content item to check for type, depth, cycles, and field validity.
      session: Shared findings and ancestor state.
      path: Path of this content item.
      flow: Ordered enclosing segment flow, extended in place. Hi passes this
          same flow to its children; Sub content owns a separate flow.
  """
  if not _check_content_depth(session, path, node):
    return
  if isinstance(node, str):
    return
  if not _check_content_acyclic(session, path, node):
    return
  session.descend(node)
  if isinstance(node, Bpt | Ept | It | Ph | Hi | Ut):
    flow.append((node, path))
  if isinstance(node, Bpt | It | Ph | Hi) and _is_integer(node.x):
    session.x_values.add(node.x)
  match node:
    case Bpt():
      _validate_bpt(node, session, path)
    case Ept():
      _validate_ept(node, session, path)
    case It():
      _validate_it(node, session, path)
    case Ph():
      _validate_ph(node, session, path)
    case Hi():
      _validate_hi(node, session, path, flow)
    case Ut():
      _validate_ut(node, session, path)
    case _:
      session.error(TmxFieldTypeError(path, node, (str, Bpt, Ept, Ph, It, Hi, Ut)))
  session.ascend()


def _validate_sub_content_node(node: object, session: _Session, path: NodePath) -> None:
  """Check text or an embedded Sub, whose pairing flow is independent."""
  if not _check_content_depth(session, path, node):
    return
  if isinstance(node, str):
    return
  if not _check_content_acyclic(session, path, node):
    return
  session.descend(node)
  if isinstance(node, Sub):
    _validate_sub(node, session, path)
  else:
    session.error(TmxFieldTypeError(path, node, (str, Sub)))
  session.ascend()


def _validate_note_or_property_node(node: object, session: _Session, path: NodePath) -> None:
  """Check unit or variant metadata, rejecting children other than Note or Property."""
  match node:
    case Note():
      _validate_note(node, session, path)
    case Property():
      _validate_property(node, session, path)
    case _:
      session.error(TmxFieldTypeError(path, node, (Note, Property)))


# The variant and inline nodes.


def _check_translation_attributes(
  node: TranslationUnit | TranslationUnitVariant, session: _Session, path: NodePath
) -> None:
  """Check the shared encoding, usage, and creation attributes in field order."""
  _check_optional(session, path / "o_encoding", node.o_encoding, _check_encoding_name)
  _check_optional(session, path / "datatype", node.datatype, _check_str)
  _check_optional(session, path / "usagecount", node.usagecount, _check_unsigned_integer)
  _check_optional(session, path / "lastusagedate", node.lastusagedate, _check_datetime)
  _check_optional(session, path / "creationtool", node.creationtool, _check_str)
  _check_optional(session, path / "creationtoolversion", node.creationtoolversion, _check_str)
  _check_optional(session, path / "creationdate", node.creationdate, _check_datetime)
  _check_optional(session, path / "creationid", node.creationid, _check_str)
  _check_optional(session, path / "changedate", node.changedate, _check_datetime)


def _validate_translation_unit_variant(tuv: object, session: _Session, path: NodePath) -> None:
  """Check variant fields, metadata, and paired codes within its segment flow."""
  if not _check_model(tuv, TranslationUnitVariant, session, path):
    return
  session.descend(tuv)
  _check_language_tag(session, path / "xml_lang", tuv.xml_lang)
  _check_translation_attributes(tuv, session, path)
  _check_optional(session, path / "o_tmf", tuv.o_tmf, _check_str)
  _check_optional(session, path / "changeid", tuv.changeid, _check_str)
  # The legacy-lang deprecation advisory rides on this pass.
  _check_optional(session, path / "lang", tuv.lang, _check_deprecated_lang)
  _check_list(session, path / "metadata", tuv.metadata, _validate_note_or_property_node)
  flow: _Flow = []
  _check_list(
    session,
    path / "content",
    tuv.content,
    lambda item, item_session, item_path: _validate_inline_content_node(item, item_session, item_path, flow),
  )
  _check_bpt_ept_pairing(flow, session)
  session.ascend()


def _validate_sub(sub: object, session: _Session, path: NodePath) -> None:
  """Check an embedded segment and match codes within its own flow."""
  if not _check_model(sub, Sub, session, path):
    return
  session.descend(sub)
  _check_optional(session, path / "datatype", sub.datatype, _check_str)
  _check_optional(session, path / "type", sub.type, _check_str)
  flow: _Flow = []
  _check_list(
    session,
    path / "content",
    sub.content,
    lambda item, item_session, item_path: _validate_inline_content_node(item, item_session, item_path, flow),
  )
  _check_bpt_ept_pairing(flow, session)
  session.ascend()


def _validate_bpt(bpt: object, session: _Session, path: NodePath) -> None:
  """Check a beginning code and embedded segments without matching its outer pair."""
  if not _check_model(bpt, Bpt, session, path):
    return
  session.descend(bpt)
  _check_unsigned_integer(session, path / "i", bpt.i)
  _check_optional(session, path / "x", bpt.x, _check_unsigned_integer)
  _check_optional(session, path / "type", bpt.type, _check_str)
  _check_list(session, path / "content", bpt.content, _validate_sub_content_node)
  session.ascend()


def _validate_ept(ept: object, session: _Session, path: NodePath) -> None:
  """Check an ending code and embedded segments without matching its outer pair."""
  if not _check_model(ept, Ept, session, path):
    return
  session.descend(ept)
  _check_unsigned_integer(session, path / "i", ept.i)
  _check_list(session, path / "content", ept.content, _validate_sub_content_node)
  session.ascend()


def _validate_it(it: object, session: _Session, path: NodePath) -> None:
  """Check an isolated code, its position, and any embedded segments."""
  if not _check_model(it, It, session, path):
    return
  session.descend(it)
  _check_position(session, path / "pos", it.pos)
  _check_optional(session, path / "x", it.x, _check_unsigned_integer)
  _check_optional(session, path / "type", it.type, _check_str)
  _check_list(session, path / "content", it.content, _validate_sub_content_node)
  session.ascend()


def _validate_ph(ph: object, session: _Session, path: NodePath) -> None:
  """Check a placeholder, its association, and any embedded segments."""
  if not _check_model(ph, Ph, session, path):
    return
  session.descend(ph)
  _check_optional(session, path / "x", ph.x, _check_unsigned_integer)
  _check_optional(session, path / "assoc", ph.assoc, _check_association)
  _check_optional(session, path / "type", ph.type, _check_str)
  _check_list(session, path / "content", ph.content, _validate_sub_content_node)
  session.ascend()


def _validate_hi(hi: object, session: _Session, path: NodePath, flow: _Flow) -> None:
  """Check highlighted content and append its inline nodes to the enclosing flow."""
  if not _check_model(hi, Hi, session, path):
    return
  session.descend(hi)
  _check_optional(session, path / "x", hi.x, _check_unsigned_integer)
  _check_optional(session, path / "type", hi.type, _check_str)
  _check_list(
    session,
    path / "content",
    hi.content,
    lambda item, item_session, item_path: _validate_inline_content_node(item, item_session, item_path, flow),
  )
  session.ascend()


def _validate_ut(ut: object, session: _Session, path: NodePath) -> None:
  """Check a legacy code and embedded segments, collecting a deprecation advisory."""
  if not _check_model(ut, Ut, session, path):
    return
  session.warn(
    TmxAdvisory(
      TmxDeprecationWarning,
      "the <ut> element is deprecated, use <bpt>, <ept>, <it>, or <ph> instead",
      path,
    )
  )
  session.descend(ut)
  _check_optional(session, path / "x", ut.x, _check_unsigned_integer)
  _check_list(session, path / "content", ut.content, _validate_sub_content_node)
  session.ascend()


def _validate_translation_unit(tu: object, session: _Session, path: NodePath) -> None:
  """Check unit fields and variants, collecting cross-variant identifier advisories."""
  if not _check_model(tu, TranslationUnit, session, path):
    return
  session.descend(tu)
  _check_optional(session, path / "tuid", tu.tuid, _check_tuid)
  _check_translation_attributes(tu, session, path)
  _check_optional(session, path / "segtype", tu.segtype, _check_segtype)
  _check_optional(session, path / "changeid", tu.changeid, _check_str)
  _check_optional(session, path / "o_tmf", tu.o_tmf, _check_str)
  _check_optional(session, path / "srclang", tu.srclang, _check_srclang)
  _check_list(session, path / "metadata", tu.metadata, _validate_note_or_property_node)
  variant_x_sets: set[frozenset[int]] = set()

  def validate_variant(variant: object, variant_session: _Session, variant_path: NodePath) -> None:
    """Collect identifiers while checking this variant's protected content tree."""
    variant_session.x_values.clear()
    _validate_translation_unit_variant(variant, variant_session, variant_path)
    if variant_session.x_values:
      variant_x_sets.add(frozenset(variant_session.x_values))

  _check_list(session, path / "variants", tu.variants, validate_variant, minimum=1)
  if len(variant_x_sets) > 1:
    listing = " vs ".join(", ".join(map(str, sorted(x_set))) for x_set in sorted(variant_x_sets, key=sorted))
    session.warn(
      TmxAdvisory(
        TmxWarning,
        f"sibling variants disagree on their x values: {listing}",
        path / "variants",
      )
    )
  session.ascend()


def validate_header(header: Header) -> tuple[TmxAdvisory, ...]:
  """Validate a header and its metadata without modifying it.

  Checks required fields and all nested notes, properties, and UDE mappings.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      header: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_header(header, session, NodePath())
  return session.finish("Header")


def validate_map(map_node: Map) -> tuple[TmxAdvisory, ...]:
  """Validate a character mapping without modifying it.

  Parent-dependent base and missing-target checks run in validate_ude.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      map_node: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_map(map_node, session, NodePath())
  return session.finish("Map")


def validate_note(note: Note) -> tuple[TmxAdvisory, ...]:
  """Validate a note without modifying it.

  Legacy lang usage produces a deprecation advisory.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      note: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.

  Examples:
      Check a model built without Pydantic's input validation and inspect the
      affected field through the error group:

      >>> note = Note.model_construct(text=42)
      >>> try:
      ...   validate_note(note)
      ... except TmxErrorGroup as group:
      ...   print(group.exceptions[0].path)
      text
  """
  session = _Session()
  _validate_note(note, session, NodePath())
  return session.finish("Note")


def validate_property(property_node: Property) -> tuple[TmxAdvisory, ...]:
  """Validate a property without modifying it.

  Checks the property type, optional attributes, and plain text.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      property_node: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_property(property_node, session, NodePath())
  return session.finish("Property")


def validate_ude(ude: Ude) -> tuple[TmxAdvisory, ...]:
  """Validate a user-defined encoding and its maps without modifying it.

  Requires base if a map sets code. Maps without code, ent, or subst
  produce an advisory.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      ude: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_ude(ude, session, NodePath())
  return session.finish("Ude")


def validate_translation_unit_variant(tuv: TranslationUnitVariant) -> tuple[TmxAdvisory, ...]:
  """Validate a variant, metadata, and segment content without modifying it.

  Checks beginning/ending-code pairing in the segment and its embedded flows.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      tuv: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_translation_unit_variant(tuv, session, NodePath())
  return session.finish("TranslationUnitVariant")


def validate_translation_unit(tu: TranslationUnit) -> tuple[TmxAdvisory, ...]:
  """Validate a translation unit and all its variants without modifying it.

  Checks each segment flow and compares nonempty external-identifier sets
  across variants. Differing sets produce an advisory.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      tu: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_translation_unit(tu, session, NodePath())
  return session.finish("TranslationUnit")


def validate_bpt(bpt: Bpt) -> tuple[TmxAdvisory, ...]:
  """Validate a beginning code and its embedded segments without modifying it.

  The matching outer Ept is checked only when validating the enclosing flow.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      bpt: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_bpt(bpt, session, NodePath())
  return session.finish("Bpt")


def validate_ept(ept: Ept) -> tuple[TmxAdvisory, ...]:
  """Validate an ending code and its embedded segments without modifying it.

  The matching outer Bpt is checked only when validating the enclosing flow.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      ept: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_ept(ept, session, NodePath())
  return session.finish("Ept")


def validate_it(it: It) -> tuple[TmxAdvisory, ...]:
  """Validate an isolated code and its embedded segments without modifying it.

  Requires a begin or end position; no outer paired code is required.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      it: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_it(it, session, NodePath())
  return session.finish("It")


def validate_ph(ph: Ph) -> tuple[TmxAdvisory, ...]:
  """Validate a placeholder and its embedded segments without modifying it.

  Checks optional external identifiers and association with surrounding text.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      ph: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_ph(ph, session, NodePath())
  return session.finish("Ph")


def validate_hi(hi: Hi) -> tuple[TmxAdvisory, ...]:
  """Validate a highlight and its inline content without modifying it.

  Treats the highlight as a complete pairing flow. Validate its enclosing
  variant instead when a pair crosses the highlight boundary.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      hi: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  flow: _Flow = []
  _validate_hi(hi, session, NodePath(), flow)
  _check_bpt_ept_pairing(flow, session)
  return session.finish("Hi")


def validate_ut(ut: Ut) -> tuple[TmxAdvisory, ...]:
  """Validate a legacy code and its embedded segments without modifying it.

  Collects the Ut deprecation advisory during this pass.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      ut: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_ut(ut, session, NodePath())
  return session.finish("Ut")


def validate_sub(sub: Sub) -> tuple[TmxAdvisory, ...]:
  """Validate an embedded segment and its inline content without modifying it.

  Checks pairing within this embedded flow independently of its parent code.
  Advisories are returned on success and attached to the error group on failure.

  Args:
      sub: Model to inspect in its current runtime state.

  Returns:
      Immutable advisories in traversal order, or an empty tuple.

  Raises:
      TmxErrorGroup: Field or relationship failures, with relative paths and
          any advisories collected during the same pass.
  """
  session = _Session()
  _validate_sub(sub, session, NodePath())
  return session.finish("Sub")
