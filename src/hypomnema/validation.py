"""Explicit, user-invocable validation for rules spanning several nodes.

GAPS decision 11: cheap local constraints run automatically in the models;
these cross-node correctness checks never run automatically. A user calls
them at their own runtime cost, and the writer (once it exists) always
calls them before converting a model to XML -- successfully completed
output must be spec-compliant. Rejections are Pydantic ``ValidationError``
with the offending node's location; the writer will wrap them into
``TmxSpecError``.

Current checks (GAPS decisions 12-13):

- ``validate_translation_unit_variant``: ``bpt``/``ept`` pairing and
  ``bpt.i`` uniqueness per flow scope. Flows are the variant's segment
  content and each ``<sub>``'s content (the embedded segment's own flow);
  ``<hi>`` is transparent, so its inline elements join the enclosing
  flow. Matching is per-``i`` with ordering, deliberately not stack
  nesting: the spec permits overlapping native code pairs.
- ``validate_translation_unit``: the variant check for every variant,
  plus one ``TmxWarning`` when sibling variants disagree on their ``x``
  values -- the spec's cross-variant matching mechanism, advisory per
  decision 13.

Both checks also re-emit the cheap model-level advisories for the data
they walk (GAPS decision 8): mutating a child does not re-trigger its
parent's validator, so a stale tree would otherwise stop warning. The
re-emitted warnings are advisory only and never affect the outcome.
"""

from collections.abc import Iterable
from warnings import warn

from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError
from typing_extensions import LiteralString

from .errors import TmxWarning
from .models import (
  Bpt,
  Ept,
  Hi,
  It,
  Note,
  Ph,
  Property,
  SegContentItem,
  Sub,
  SubContentItem,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)
from .validators import warn_deprecated_lang, warn_deprecated_ut, warn_map_without_target

_PAIRING_ERROR_TYPE = "inline_tag_pairing"
_CYCLE_ERROR_TYPE = "cyclic_content"


def _node_error(loc: tuple[str | int, ...], error_type: LiteralString, message: str, node: object) -> InitErrorDetails:
  return {"type": PydanticCustomError(error_type, "{message}", {"message": message}), "loc": loc, "input": node}


def _pairing_error(loc: tuple[str | int, ...], message: str, node: object) -> InitErrorDetails:
  return _node_error(loc, _PAIRING_ERROR_TYPE, message, node)


def _cycle_error(loc: tuple[str | int, ...], node: TmxNode) -> InitErrorDetails:
  return _node_error(
    loc, _CYCLE_ERROR_TYPE, f"cyclic content: this <{node.element}> contains itself through its descendants", node
  )


def _walk_segment(
  items: tuple[SegContentItem, ...], loc: tuple[str | int, ...], errors: list[InitErrorDetails], path: set[int]
) -> None:
  """Walk one flow: fresh ``i`` namespaces, unmatched-bpt check at the end.

  ``path`` holds the ids of the content nodes on the current descent and
  turns re-entry into a cycle error. Only mutation can create a cycle
  (GAPS decision 7a), and detection is scoped to this walk's root, so
  subtrees legitimately shared between variants stay legal.
  """
  bpt_locations: dict[int, tuple[tuple[str | int, ...], Bpt]] = {}
  ept_seen: set[int] = set()
  _walk_items(items, loc, errors, bpt_locations, ept_seen, path)
  for i, (bpt_loc, bpt) in bpt_locations.items():
    if i not in ept_seen:
      errors.append(_pairing_error(bpt_loc, f"<bpt> i={i} has no subsequent corresponding <ept> within this flow", bpt))


def _walk_items(
  items: tuple[SegContentItem, ...],
  loc: tuple[str | int, ...],
  errors: list[InitErrorDetails],
  bpt_locations: dict[int, tuple[tuple[str | int, ...], Bpt]],
  ept_seen: set[int],
  path: set[int],
) -> None:
  """Walk one flow's items in document order, sharing the flow's state.

  ``<hi>`` recursion shares the caller's state (it is transparent);
  paired and placeholder tags open fresh flows for their ``<sub>``
  contents. ``path`` carries the ids on the current descent; a node
  already on it is a cycle, reported without descending into it again.
  """
  for index, node in enumerate(items):
    if isinstance(node, str):
      continue
    if id(node) in path:
      errors.append(_cycle_error((*loc, index), node))
      continue
    path.add(id(node))
    child_loc = (*loc, index, "content")
    if isinstance(node, Bpt):
      if node.i in bpt_locations:
        errors.append(
          _pairing_error(
            (*loc, index), f"duplicate <bpt> i={node.i} within one flow; i must be unique among <bpt> elements", node
          )
        )
      else:
        bpt_locations[node.i] = ((*loc, index), node)
      _walk_sub_flows(node.content, child_loc, errors, path)
    elif isinstance(node, Ept):
      if node.i in ept_seen:
        errors.append(
          _pairing_error(
            (*loc, index), f"duplicate <ept> i={node.i} within one flow; i must be unique among <ept> elements", node
          )
        )
      ept_seen.add(node.i)
      if node.i not in bpt_locations:
        errors.append(
          _pairing_error((*loc, index), f"<ept> i={node.i} has no corresponding <bpt> earlier in this flow", node)
        )
      _walk_sub_flows(node.content, child_loc, errors, path)
    elif isinstance(node, Ut):
      warn_deprecated_ut()
      _walk_sub_flows(node.content, child_loc, errors, path)
    elif isinstance(node, It | Ph):
      _walk_sub_flows(node.content, child_loc, errors, path)
    elif isinstance(node, Hi):
      _walk_items(node.content, child_loc, errors, bpt_locations, ept_seen, path)
    path.discard(id(node))


def _walk_sub_flows(
  items: tuple[SubContentItem, ...], loc: tuple[str | int, ...], errors: list[InitErrorDetails], path: set[int]
) -> None:
  """Walk the content of a paired or placeholder tag: text plus ``<sub>``
  nodes, each ``<sub>`` its own flow."""
  for index, node in enumerate(items):
    if isinstance(node, Sub):
      if id(node) in path:
        errors.append(_cycle_error((*loc, index), node))
        continue
      path.add(id(node))
      _walk_segment(node.content, (*loc, index, "content"), errors, path)
      path.discard(id(node))


def _rewarn_metadata_advisories(metadata: Iterable[Note | Property | Ude]) -> None:
  """Re-emit the metadata children's cheap model-level advisories.

  Advisories fire at construction and assignment, but mutating a child
  never re-triggers its parent's validator (GAPS decision 7). The
  explicit checks re-run them so a stale tree still gets its warnings
  (decision 8); duplicates across layers are acceptable, the standard
  warning filters deduplicate.
  """
  for node in metadata:
    match node:
      case Note() | Property():
        warn_deprecated_lang(node.lang, node.xml_lang)
      case Ude():
        for mapping in node.maps:
          warn_map_without_target(mapping.code, mapping.ent, mapping.subst)


def validate_translation_unit_variant(tuv: TranslationUnitVariant) -> None:
  """Check ``bpt``/``ept`` pairing and ``i`` uniqueness in every flow.

  Per GAPS decision 12: every ``bpt`` needs a subsequent corresponding
  ``ept`` and every ``ept`` a preceding ``bpt``, within one flow; ``i``
  is unique among ``bpt`` elements and among ``ept`` elements of a flow.
  Raises ``ValidationError`` with the offending node's location. Also
  detects cyclic content -- a node containing itself through its
  descendants, reachable only through mutation (GAPS decision 7a).

  Re-emits the variant metadata's advisories, so a tree mutated after
  construction still warns (GAPS decision 8).
  """
  errors: list[InitErrorDetails] = []
  _walk_segment(tuv.content, ("content",), errors, set())
  if errors:
    raise ValidationError.from_exception_data("TranslationUnitVariant", errors)
  _rewarn_metadata_advisories(tuv.metadata)


def _collect_x_values(node: SegContentItem | SubContentItem, into: set[int]) -> None:
  """Collect the ``x`` values of the inline elements the spec matches
  across variants (``bpt``, ``it``, ``ph``, ``hi``), including nested
  content."""
  if isinstance(node, str):
    return
  if isinstance(node, Bpt | It | Ph | Hi) and node.x is not None:
    into.add(node.x)
  for child in node.content:
    _collect_x_values(child, into)


def validate_translation_unit(tu: TranslationUnit) -> None:
  """Validate the whole translation unit.

  Runs ``validate_translation_unit_variant`` on every variant (raising on
  the first batch of structural errors, including cyclic content), then
  emits one ``TmxWarning`` if the variants disagree on their inline ``x``
  values (GAPS decision 13). Re-emits the advisories of the unit's and
  the variants' metadata, so a tree mutated after construction still
  warns (GAPS decision 8).
  """
  errors: list[InitErrorDetails] = []
  for index, tuv in enumerate(tu.variants):
    variant_errors: list[InitErrorDetails] = []
    _walk_segment(tuv.content, ("content",), variant_errors, set())
    for error in variant_errors:
      error["loc"] = ("variants", index, *error["loc"])
    errors.extend(variant_errors)
  if errors:
    raise ValidationError.from_exception_data("TranslationUnit", errors)
  x_sets = []
  for tuv in tu.variants:
    values: set[int] = set()
    for node in tuv.content:
      _collect_x_values(node, values)
    x_sets.append(frozenset(values))
  if len(set(x_sets)) > 1:
    all_values = sorted(set().union(*x_sets))
    warn(
      f"the variants of this <tu> use different inline x values {all_values};"
      " the x attribute matches inline tags between variants",
      TmxWarning,
    )
  _rewarn_metadata_advisories(tu.metadata)
  for tuv in tu.variants:
    _rewarn_metadata_advisories(tuv.metadata)
