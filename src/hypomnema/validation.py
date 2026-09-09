"""Pure, user-invocable validation for TMX contract rules (GAPS decision 19).

Models are a typed, permissive IR: typing (strict values, tuples, the
nonempty ``variants``/``maps``) is enforced automatically in the models, but
TMX *contract* rules -- cross-field rules, prose pairing, and advisories --
live here as side-effect-free functions that raise Pydantic
``ValidationError`` and emit ``TmxWarning`` advisories. Projection and the
future reader/writer invoke the relevant function at every XML-IR boundary
crossing; users should call them mid-pipeline for early error locality.
Between boundaries, no check runs automatically.

Current checks (GAPS decisions 12-13, 19):

- ``validate_ude``: ``<ude base>`` required when any ``<map>`` carries
  ``code``, plus the map-target advisory.
- ``validate_header``: the ``validate_ude`` check for every ``<ude>`` in the
  header's metadata, plus the legacy-``lang`` advisories for its notes and
  properties.
- ``validate_translation_unit_variant``: ``bpt``/``ept`` pairing and
  ``bpt.i`` uniqueness per flow scope, plus the variant metadata's
  legacy-``lang`` advisories. Flows are the variant's segment content and
  each ``<sub>``'s content (the embedded segment's own flow); ``<hi>`` is
  transparent, so its inline elements join the enclosing flow. Matching is
  per-``i`` with ordering, deliberately not stack nesting: the spec permits
  overlapping native code pairs.
- ``validate_translation_unit``: the variant walk for every variant, the
  unit metadata's advisories, plus one ``TmxWarning`` when sibling variants
  disagree on their ``x`` values -- the spec's cross-variant matching
  mechanism, advisory per decision 13.

The deprecated ``<ut>`` advisory is emitted inside the content walk, since
that is the pass that visits inline content.
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
  Header,
  Hi,
  It,
  Map,
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
_UDE_ERROR_TYPE = "ude_base_required"


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


def _warn_metadata_advisories(metadata: Iterable[Note | Property | Ude]) -> None:
  """Emit the metadata children's advisories (GAPS decision 19).

  Models no longer warn; the validation pass is the one place advisories
  fire, so this is primary emission, not a re-walk. Duplicates across
  separate validation passes are acceptable; the standard warning filters
  deduplicate.
  """
  for node in metadata:
    match node:
      case Note() | Property():
        warn_deprecated_lang(node.lang, node.xml_lang)
      case Ude():
        for mapping in node.maps:
          warn_map_without_target(mapping.code, mapping.ent, mapping.subst)


def _ude_errors(ude: Ude, loc: tuple[str | int, ...]) -> list[InitErrorDetails]:
  """``<ude base>`` is required when any ``<map>`` carries ``code``.

  One error per offending map, located under ``loc`` so header-level
  validation can prefix the metadata position.
  """
  if ude.base is not None:
    return []
  return [
    _node_error(
      (*loc, index),
      _UDE_ERROR_TYPE,
      f"<map> at index {index} carries code; <ude> requires base when any map carries code",
      mapping,
    )
    for index, mapping in enumerate(ude.maps)
    if mapping.code is not None
  ]


def validate_ude(ude: Ude) -> None:
  """Validate one ``<ude>``.

  Enforces the spec's cross-field rule: ``base`` is required when any
  ``<map>`` carries ``code`` (one error per offending map). Emits the
  map-target advisory for each map. Raises ``ValidationError``.
  """
  errors = _ude_errors(ude, ())
  if errors:
    raise ValidationError.from_exception_data("Ude", errors)
  for mapping in ude.maps:
    warn_map_without_target(mapping.code, mapping.ent, mapping.subst)


def validate_header(header: Header) -> None:
  """Validate a complete ``<header>``.

  Runs the ``validate_ude`` check on every ``<ude>`` in the metadata
  (error locations prefixed with the metadata position), and emits the
  legacy-``lang`` advisories for the header's notes and properties.
  Raises ``ValidationError`` if any ``<ude>`` violates its rule.
  """
  errors: list[InitErrorDetails] = []
  for index, node in enumerate(header.metadata):
    match node:
      case Note() | Property():
        warn_deprecated_lang(node.lang, node.xml_lang)
      case Ude():
        errors.extend(_ude_errors(node, ("metadata", index)))
        for mapping in node.maps:
          warn_map_without_target(mapping.code, mapping.ent, mapping.subst)
  if errors:
    raise ValidationError.from_exception_data("Header", errors)


def validate(node: TmxNode) -> None:
  """Validate any TMX node with the checks that apply to it.

  The projection boundary's dispatcher, and the one-call convenience for
  users. Header/unit/unit-variant/ude nodes run their full checks; leaf
  nodes emit their advisory (legacy ``lang``, map target, deprecated
  ``<ut>``); inline nodes carry nothing checkable outside a flow scope --
  pairing rules apply when a ``<tuv>`` or ``<tu>`` is validated.
  Raises ``ValidationError``; emits ``TmxWarning`` advisories.
  """
  match node:
    case Header():
      validate_header(node)
    case Ude():
      validate_ude(node)
    case TranslationUnit():
      validate_translation_unit(node)
    case TranslationUnitVariant():
      validate_translation_unit_variant(node)
    case Note() | Property():
      warn_deprecated_lang(node.lang, node.xml_lang)
    case Map():
      warn_map_without_target(node.code, node.ent, node.subst)
    case Ut():
      warn_deprecated_ut()
    case Bpt() | Ept() | It() | Ph() | Hi() | Sub():
      pass


def validate_translation_unit_variant(tuv: TranslationUnitVariant) -> None:
  """Check ``bpt``/``ept`` pairing and ``i`` uniqueness in every flow.

  Per GAPS decision 12: every ``bpt`` needs a subsequent corresponding
  ``ept`` and every ``ept`` a preceding ``bpt``, within one flow; ``i``
  is unique among ``bpt`` elements and among ``ept`` elements of a flow.
  Raises ``ValidationError`` with the offending node's location. Also
  detects cyclic content -- a node containing itself through its
  descendants, reachable only through mutation (GAPS decision 7a). Emits
  the variant metadata's legacy-``lang`` advisories (GAPS decision 19).
  """
  errors: list[InitErrorDetails] = []
  _walk_segment(tuv.content, ("content",), errors, set())
  if errors:
    raise ValidationError.from_exception_data("TranslationUnitVariant", errors)
  _warn_metadata_advisories(tuv.metadata)


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

  Runs the variant walk on every variant (raising on the first batch of
  structural errors, including cyclic content), emits the unit's and the
  variants' metadata advisories, then emits one ``TmxWarning`` if the
  variants disagree on their inline ``x`` values (GAPS decision 13).
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
  _warn_metadata_advisories(tu.metadata)
  for tuv in tu.variants:
    _warn_metadata_advisories(tuv.metadata)
