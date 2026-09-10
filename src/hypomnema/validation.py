"""Strict, user-invocable validation: every field, every time (lax input,
strict output).

The models accept nearly anything at the entry boundary and coerce it.
These validators are the other half of the contract: they check the
*runtime* type and value of every single field of a node and of everything
reachable from it (metadata lists, nested nodes), so a node that passes
validation is safe to output. Nothing here mutates or coerces: a node
either passes as a whole, or fails as a whole.

The calling pattern is always the same: call a ``validate_*`` function
inside ``try``/``except*`` and catch the error kinds you want to react to
(``TmxFieldTypeError`` for wrong runtime types, ``TmxFieldValueError`` for
rejected values, ``TmxContractError`` for cross-field spec rules). Every
failure of one pass travels on a single ``TmxErrorGroup``, and the
advisories gathered during that same pass ride on the group's
``advisories`` attribute (legacy ``lang`` usage, unknown encoding names,
``<map>`` without a target) -- they are data, never ``warnings.warn``
emissions; the caller decides whether to escalate, filter, or emit them.
A pass that gathers only advisories raises nothing, so a document that is
valid but uses a deprecated construct everywhere stays quiet until a real
error is being reported anyway. Errors and advisories both carry a
``NodePath`` locating the field relative to the node being validated,
e.g. ``metadata[2].maps[0].code``.

Field checks stop at the first failure per field -- a wrong type is not
followed by value checks of that same value -- and untyped/foreign
children are reported once as ``TmxFieldTypeError`` rather than cascading
into their innards. Errors and advisories are reported in field
traversal order: top-level fields first, then children depth-first.

The variant and inline validators (``<tuv>``, ``<bpt>``, ``<ept>``,
``<it>``, ``<ph>``, ``<hi>``, ``<ut>``, ``<sub>``) currently check type
validity and structure only: the cross-field contract rules (bpt/ept
pairing, ``x`` matching) and the deprecation advisories for the legacy
``lang`` on ``<tuv>`` and for ``<ut>`` ride on the translation-unit pass.
"""

import codecs
from collections.abc import Callable
from datetime import datetime

from .bcp47 import validate_well_formed_language_tag
from .errors import (
  LanguageTagError,
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
from .models import Bpt, Ept, Header, Hi, It, Map, Note, Ph, Property, Sub, TranslationUnitVariant, Ude, Ut

__all__ = [
  "validate_bpt",
  "validate_ept",
  "validate_header",
  "validate_hi",
  "validate_it",
  "validate_note",
  "validate_ph",
  "validate_property",
  "validate_sub",
  "validate_translation_unit_variant",
  "validate_ude",
  "validate_ut",
]


class _Session:
  """Accumulates the errors and advisories of one validation pass.

  Checkers append; ``finish`` raises all errors at once as a
  ``TmxErrorGroup`` with the advisories attached -- or, with no errors,
  returns quietly, however many advisories were gathered.
  """

  __slots__ = ("ancestors", "errors", "warnings")

  def __init__(self) -> None:
    self.errors: list[TmxFieldError] = []
    self.warnings: list[TmxAdvisory] = []
    # ``id()`` of the content nodes on the current descent path. A node
    # whose id is here while the walk is still inside it is its own
    # ancestor: a cycle. A node seen elsewhere in the tree is fine.
    self.ancestors: list[int] = []

  def error(self, error: TmxFieldError) -> None:
    self.errors.append(error)

  def warn(self, advisory: TmxAdvisory) -> None:
    self.warnings.append(advisory)

  def descend(self, node: object) -> None:
    self.ancestors.append(id(node))

  def ascend(self) -> None:
    self.ancestors.pop()

  def finish(self, node_name: str) -> None:
    """Raise the group if errors were gathered, advisories attached;
    otherwise return quietly."""
    if self.errors:
      raise TmxErrorGroup(f"failed to validate {node_name}", self.errors, self.warnings)


type _FieldCheck = Callable[[_Session, NodePath, object], None]
"""What an optional-field check looks like: session, path, unknown value."""

_SEGMENT_TYPES = ("block", "paragraph", "sentence", "phrase")
_POSITIONS = ("begin", "end")
_ASSOCIATIONS = ("p", "f", "b")
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
  return isinstance(value, str)


def _is_integer(value: object) -> bool:
  # bool is an int subclass; it is not a number here.
  return isinstance(value, int) and not isinstance(value, bool)


# Checkers. All take (session, path, value), never raise, never mutate:
# they append at most a few errors and advisories to the session. A checker
# reporting a wrong type returns without value-checking that value.


def _check_element(session: _Session, path: NodePath, value: object, literal: str) -> None:
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  if value != literal:
    session.error(TmxFieldValueError(path, value, f"expected the literal {literal!r}"))


def _check_optional(session: _Session, path: NodePath, value: object, check: _FieldCheck) -> None:
  if value is not None:
    check(session, path, value)


def _check_str(session: _Session, path: NodePath, value: object) -> None:
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))


def _check_ascii_text(session: _Session, path: NodePath, value: object) -> None:
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  if not value.isascii():
    session.error(TmxFieldValueError(path, value, "expected ASCII text"))


def _check_unsigned_integer(session: _Session, path: NodePath, value: object) -> None:
  if isinstance(value, bool) or not isinstance(value, int):
    session.error(TmxFieldTypeError(path, value, int))
    return
  if value < 0:
    session.error(TmxFieldValueError(path, value, "expected an unsigned integer"))


def _check_unicode_scalar(session: _Session, path: NodePath, value: object) -> None:
  if isinstance(value, bool) or not isinstance(value, int):
    session.error(TmxFieldTypeError(path, value, int))
    return
  if not 0 <= value <= 0x10FFFF:
    session.error(TmxFieldValueError(path, value, "expected a Unicode scalar value in 0..0x10FFFF"))
  elif 0xD800 <= value <= 0xDFFF:
    session.error(TmxFieldValueError(path, value, "surrogate code points are not valid Unicode scalar values"))


def _check_datetime(session: _Session, path: NodePath, value: object) -> None:
  # Naive values are allowed and documented as UTC; an explicit offset is
  # kept as-is. All further ISO 8601 well-formedness was settled at the
  # entry boundary by parse_datetime.
  if not isinstance(value, datetime):
    session.error(TmxFieldTypeError(path, value, datetime))


def _check_language_tag(session: _Session, path: NodePath, value: object) -> None:
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  try:
    validate_well_formed_language_tag(value)
  except LanguageTagError as error:
    session.error(TmxFieldValueError(path, value, str(error)))


def _check_deprecated_lang(session: _Session, path: NodePath, value: object) -> None:
  """A legacy ``lang`` value: validated like any language tag, plus the
  deprecation advisory, since merely using the attribute is advisory-worthy
  even when its value is fine."""
  _check_language_tag(session, path, value)
  session.warn(
    TmxAdvisory(
      TmxDeprecationWarning,
      "the lang attribute is deprecated since TMX 1.3 in favor of xml_lang",
      path,
    )
  )


def _check_srclang(session: _Session, path: NodePath, value: object) -> None:
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
  if not isinstance(value, str):
    session.error(TmxFieldTypeError(path, value, str))
    return
  if value not in allowed:
    session.error(TmxFieldValueError(path, value, f"expected one of {', '.join(map(repr, allowed))}"))


def _check_segtype(session: _Session, path: NodePath, value: object) -> None:
  _check_one_of(session, path, value, _SEGMENT_TYPES)


def _check_position(session: _Session, path: NodePath, value: object) -> None:
  _check_one_of(session, path, value, _POSITIONS)


def _check_association(session: _Session, path: NodePath, value: object) -> None:
  _check_one_of(session, path, value, _ASSOCIATIONS)


def _check_encoding_name(session: _Session, path: NodePath, value: object) -> None:
  """An encoding name: typed as ``str``; unknown to Python's codecs is an
  advisory, not an error -- the spec recommends IANA charset identifiers
  but only as a soft "if possible"."""
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
  """A list field: the container itself, its length, then each item.
  Item well-formedness is the item validator's business -- each one
  starts with its own instance check and reports a foreign item as
  ``TmxFieldTypeError`` without descending into it."""
  if not isinstance(value, list):
    session.error(TmxFieldTypeError(path, value, list))
    return
  if len(value) < minimum:
    session.error(TmxContractError(path, value, f"expected at least {minimum} item(s), got {len(value)}"))
  for index, item in enumerate(value):
    item_check(item, session, path / index)


# Node validators. Each private validator reads every field of its node --
# so "every field is checked" is verifiable by reading the body -- and
# recurses into children with an extended path.


def _validate_header(header: object, session: _Session, path: NodePath) -> None:
  if not isinstance(header, Header):
    session.error(TmxFieldTypeError(path, header, Header))
    return
  if not _check_required_fields(
    session,
    path,
    header,
    ("creationtool", "creationtoolversion", "segtype", "o_tmf", "adminlang", "srclang", "datatype"),
  ):
    return
  _check_element(session, path / "element", header.element, "header")
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
  """Dispatches one header-metadata child to its validator; a foreign
  child is reported once as ``TmxFieldTypeError``."""
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
  if not isinstance(note, Note):
    session.error(TmxFieldTypeError(path, note, Note))
    return
  _check_element(session, path / "element", note.element, "note")
  _check_optional(session, path / "o_encoding", note.o_encoding, _check_encoding_name)
  _check_optional(session, path / "xml_lang", note.xml_lang, _check_language_tag)
  _check_optional(session, path / "lang", note.lang, _check_deprecated_lang)
  _check_optional(session, path / "text", note.text, _check_str)


def _validate_property(property_node: object, session: _Session, path: NodePath) -> None:
  if not isinstance(property_node, Property):
    session.error(TmxFieldTypeError(path, property_node, Property))
    return
  if not _check_required_fields(session, path, property_node, ("type",)):
    return
  _check_element(session, path / "element", property_node.element, "prop")
  _check_str(session, path / "type", property_node.type)
  _check_optional(session, path / "xml_lang", property_node.xml_lang, _check_language_tag)
  _check_optional(session, path / "o_encoding", property_node.o_encoding, _check_encoding_name)
  _check_optional(session, path / "lang", property_node.lang, _check_deprecated_lang)
  _check_optional(session, path / "text", property_node.text, _check_str)


def _validate_map(map_node: object, session: _Session, path: NodePath) -> None:
  if not isinstance(map_node, Map):
    session.error(TmxFieldTypeError(path, map_node, Map))
    return
  if not _check_required_fields(session, path, map_node, ("unicode",)):
    return
  _check_element(session, path / "element", map_node.element, "map")
  _check_unicode_scalar(session, path / "unicode", map_node.unicode)
  _check_optional(session, path / "code", map_node.code, _check_unsigned_integer)
  _check_optional(session, path / "ent", map_node.ent, _check_ascii_text)
  _check_optional(session, path / "subst", map_node.subst, _check_ascii_text)


def _validate_ude(ude: object, session: _Session, path: NodePath) -> None:
  if not isinstance(ude, Ude):
    session.error(TmxFieldTypeError(path, ude, Ude))
    return
  if not _check_required_fields(session, path, ude, ("name", "maps")):
    return
  _check_element(session, path / "element", ude.element, "ude")
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
  """Whether the walk may descend into this content item: cyclic content
  (a node containing itself, planted via ``model_construct``) would
  otherwise recurse until a raw ``RecursionError`` escapes the pass.
  Each nesting level adds exactly two ``NodePath`` segments."""
  if len(path.segments) < 2 * _MAX_CONTENT_NESTING:
    return True
  session.error(TmxContractError(path, node, f"content nested deeper than {_MAX_CONTENT_NESTING} levels"))
  return False


def _check_required_fields(session: _Session, path: NodePath, node: object, names: tuple[str, ...]) -> bool:
  """A node built through ``model_construct`` may lack required fields
  entirely (nothing injects their values); report each one instead of
  crashing the pass with a raw attribute error."""
  missing = [name for name in names if not hasattr(node, name)]
  for name in missing:
    session.error(
      TmxContractError(
        path / name,
        None,
        "required field is missing (the node was not built at the entry boundary)",
      )
    )
  return not missing


def _check_content_acyclic(session: _Session, path: NodePath, node: object) -> bool:
  """Whether the walk may descend into this content node: a node whose
  ``id()`` is on the current descent path is its own ancestor, a cycle
  that ``hi.content.append(hi)`` can plant through ``model_construct``
  (XML cannot express one). The walk breaks there instead of recursing
  into a raw ``RecursionError``. A node seen elsewhere in the tree is
  not a cycle and stays legal."""
  if id(node) not in session.ancestors:
    return True
  session.error(TmxContractError(path, node, "cyclic content: this element is its own ancestor"))
  return False


def _validate_inline_content_node(node: object, session: _Session, path: NodePath) -> None:
  """One item of a ``list[InlineNodeOrStr]``: text or any inline element."""
  if not _check_content_depth(session, path, node):
    return
  if isinstance(node, str):
    return
  if not _check_content_acyclic(session, path, node):
    return
  session.descend(node)
  try:
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
        _validate_hi(node, session, path)
      case Ut():
        _validate_ut(node, session, path)
      case _:
        session.error(TmxFieldTypeError(path, node, (str, Bpt, Ept, Ph, It, Hi, Ut)))
  finally:
    session.ascend()


def _validate_sub_content_node(node: object, session: _Session, path: NodePath) -> None:
  """One item of a ``list[SubOrStr]``: text or a ``<sub>`` element."""
  if not _check_content_depth(session, path, node):
    return
  if isinstance(node, str):
    return
  if not _check_content_acyclic(session, path, node):
    return
  session.descend(node)
  try:
    match node:
      case Sub():
        _validate_sub(node, session, path)
      case _:
        session.error(TmxFieldTypeError(path, node, (str, Sub)))
  finally:
    session.ascend()


def _validate_tuv_metadata_node(node: object, session: _Session, path: NodePath) -> None:
  """Dispatches one ``<tuv>`` metadata child: a ``<tuv>`` may not hold a
  ``<ude>``."""
  match node:
    case Note():
      _validate_note(node, session, path)
    case Property():
      _validate_property(node, session, path)
    case _:
      session.error(TmxFieldTypeError(path, node, (Note, Property)))


# The variant and inline nodes.


def _validate_translation_unit_variant(tuv: object, session: _Session, path: NodePath) -> None:
  if not isinstance(tuv, TranslationUnitVariant):
    session.error(TmxFieldTypeError(path, tuv, TranslationUnitVariant))
    return
  if not _check_required_fields(session, path, tuv, ("xml_lang",)):
    return
  _check_element(session, path / "element", tuv.element, "tuv")
  _check_language_tag(session, path / "xml_lang", tuv.xml_lang)
  _check_optional(session, path / "o_encoding", tuv.o_encoding, _check_encoding_name)
  _check_optional(session, path / "datatype", tuv.datatype, _check_str)
  _check_optional(session, path / "usagecount", tuv.usagecount, _check_unsigned_integer)
  _check_optional(session, path / "lastusagedate", tuv.lastusagedate, _check_datetime)
  _check_optional(session, path / "creationtool", tuv.creationtool, _check_str)
  _check_optional(session, path / "creationtoolversion", tuv.creationtoolversion, _check_str)
  _check_optional(session, path / "creationdate", tuv.creationdate, _check_datetime)
  _check_optional(session, path / "creationid", tuv.creationid, _check_str)
  _check_optional(session, path / "changedate", tuv.changedate, _check_datetime)
  _check_optional(session, path / "o_tmf", tuv.o_tmf, _check_str)
  _check_optional(session, path / "changeid", tuv.changeid, _check_str)
  # The legacy-lang deprecation advisory rides on the translation-unit
  # pass; the field itself is validated now.
  _check_optional(session, path / "lang", tuv.lang, _check_language_tag)
  _check_list(session, path / "metadata", tuv.metadata, _validate_tuv_metadata_node)
  _check_list(session, path / "content", tuv.content, _validate_inline_content_node)


def _validate_sub(sub: object, session: _Session, path: NodePath) -> None:
  if not isinstance(sub, Sub):
    session.error(TmxFieldTypeError(path, sub, Sub))
    return
  _check_element(session, path / "element", sub.element, "sub")
  _check_optional(session, path / "datatype", sub.datatype, _check_str)
  _check_optional(session, path / "type", sub.type, _check_str)
  _check_list(session, path / "content", sub.content, _validate_inline_content_node)


def _validate_bpt(bpt: object, session: _Session, path: NodePath) -> None:
  if not isinstance(bpt, Bpt):
    session.error(TmxFieldTypeError(path, bpt, Bpt))
    return
  if not _check_required_fields(session, path, bpt, ("i",)):
    return
  _check_element(session, path / "element", bpt.element, "bpt")
  _check_unsigned_integer(session, path / "i", bpt.i)
  _check_optional(session, path / "x", bpt.x, _check_unsigned_integer)
  _check_optional(session, path / "type", bpt.type, _check_str)
  _check_list(session, path / "content", bpt.content, _validate_sub_content_node)


def _validate_ept(ept: object, session: _Session, path: NodePath) -> None:
  if not isinstance(ept, Ept):
    session.error(TmxFieldTypeError(path, ept, Ept))
    return
  if not _check_required_fields(session, path, ept, ("i",)):
    return
  _check_element(session, path / "element", ept.element, "ept")
  _check_unsigned_integer(session, path / "i", ept.i)
  _check_list(session, path / "content", ept.content, _validate_sub_content_node)


def _validate_it(it: object, session: _Session, path: NodePath) -> None:
  if not isinstance(it, It):
    session.error(TmxFieldTypeError(path, it, It))
    return
  if not _check_required_fields(session, path, it, ("pos",)):
    return
  _check_element(session, path / "element", it.element, "it")
  _check_position(session, path / "pos", it.pos)
  _check_optional(session, path / "x", it.x, _check_unsigned_integer)
  _check_optional(session, path / "type", it.type, _check_str)
  _check_list(session, path / "content", it.content, _validate_sub_content_node)


def _validate_ph(ph: object, session: _Session, path: NodePath) -> None:
  if not isinstance(ph, Ph):
    session.error(TmxFieldTypeError(path, ph, Ph))
    return
  _check_element(session, path / "element", ph.element, "ph")
  _check_optional(session, path / "x", ph.x, _check_unsigned_integer)
  _check_optional(session, path / "assoc", ph.assoc, _check_association)
  _check_optional(session, path / "type", ph.type, _check_str)
  _check_list(session, path / "content", ph.content, _validate_sub_content_node)


def _validate_hi(hi: object, session: _Session, path: NodePath) -> None:
  if not isinstance(hi, Hi):
    session.error(TmxFieldTypeError(path, hi, Hi))
    return
  _check_element(session, path / "element", hi.element, "hi")
  _check_optional(session, path / "x", hi.x, _check_unsigned_integer)
  _check_optional(session, path / "type", hi.type, _check_str)
  _check_list(session, path / "content", hi.content, _validate_inline_content_node)


def _validate_ut(ut: object, session: _Session, path: NodePath) -> None:
  if not isinstance(ut, Ut):
    session.error(TmxFieldTypeError(path, ut, Ut))
    return
  _check_element(session, path / "element", ut.element, "ut")
  _check_optional(session, path / "x", ut.x, _check_unsigned_integer)
  _check_list(session, path / "content", ut.content, _validate_sub_content_node)


def validate_header(header: Header) -> None:
  """Validate a :class:`Header` and everything reachable from it.

  Raises ``TmxErrorGroup`` holding one ``TmxFieldError`` per failure and,
  on its ``advisories`` attribute, every advisory gathered along the way
  (legacy ``lang`` usage, unknown encoding names, ``<map>`` without a
  target). Returns without raising when no field fails, even if
  advisories were gathered; see the module docstring for the calling
  pattern.
  """
  session = _Session()
  _validate_header(header, session, NodePath())
  session.finish("Header")


def validate_note(note: Note) -> None:
  """Validate a :class:`Note`; see :func:`validate_header` for semantics."""
  session = _Session()
  _validate_note(note, session, NodePath())
  session.finish("Note")


def validate_property(property_node: Property) -> None:
  """Validate a :class:`Property`; see :func:`validate_header` for semantics."""
  session = _Session()
  _validate_property(property_node, session, NodePath())
  session.finish("Property")


def validate_ude(ude: Ude) -> None:
  """Validate a :class:`Ude`, including its maps and both contract rules
  (``base`` required when a map carries ``code``; the map-target
  advisory). See :func:`validate_header` for semantics."""
  session = _Session()
  _validate_ude(ude, session, NodePath())
  session.finish("Ude")


def validate_translation_unit_variant(tuv: TranslationUnitVariant) -> None:
  """Validate a :class:`TranslationUnitVariant` and its whole content
  tree. See :func:`validate_header` for semantics; the legacy-``lang``
  deprecation advisory rides on the translation-unit pass."""
  session = _Session()
  _validate_translation_unit_variant(tuv, session, NodePath())
  session.finish("TranslationUnitVariant")


def validate_bpt(bpt: Bpt) -> None:
  """Validate a :class:`Bpt` and its content tree; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_bpt(bpt, session, NodePath())
  session.finish("Bpt")


def validate_ept(ept: Ept) -> None:
  """Validate an :class:`Ept` and its content tree; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_ept(ept, session, NodePath())
  session.finish("Ept")


def validate_it(it: It) -> None:
  """Validate an :class:`It` and its content tree; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_it(it, session, NodePath())
  session.finish("It")


def validate_ph(ph: Ph) -> None:
  """Validate a :class:`Ph` and its content tree; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_ph(ph, session, NodePath())
  session.finish("Ph")


def validate_hi(hi: Hi) -> None:
  """Validate a :class:`Hi` and its content tree; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_hi(hi, session, NodePath())
  session.finish("Hi")


def validate_ut(ut: Ut) -> None:
  """Validate a :class:`Ut` and its content tree; the ``<ut>``
  deprecation advisory rides on the translation-unit pass; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_ut(ut, session, NodePath())
  session.finish("Ut")


def validate_sub(sub: Sub) -> None:
  """Validate a :class:`Sub` and its content tree; see
  :func:`validate_header` for semantics."""
  session = _Session()
  _validate_sub(sub, session, NodePath())
  session.finish("Sub")
