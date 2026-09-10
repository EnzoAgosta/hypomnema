"""Error hierarchy.

Field-level validation failures travel as individual, path-carrying
exceptions so consumers can use ``except*`` to select by kind and read
``path`` and ``value`` for diagnostics. A whole validation pass raises its
failures as one ``TmxErrorGroup``.
"""

from collections.abc import Sequence
from dataclasses import dataclass


class TmxError(Exception):
  """Base class for errors concerning TMX data."""


class TmxSpecError(TmxError):
  """Data violates the TMX contract."""


class TmxWarning(UserWarning):
  """Soft advisory that does not violate the TMX contract.

  Emitted for spec recommendations we deliberately do not enforce; consumers
  can filter, escalate, or ignore via the standard ``warnings`` machinery.
  """


class TmxDeprecationWarning(TmxWarning):
  """Advisory about a deprecated TMX construct (legacy ``lang``, ``<ut>``).

  A ``TmxWarning`` subclass so consumers can silence deprecation advisories
  without muting contract advisories such as the cross-variant ``x``
  mismatch. Filtering by category also keeps callers and tests independent
  of advisory message wording.
  """


@dataclass(frozen=True, slots=True)
class TmxAdvisory:
  """A soft advisory a validator gathered instead of being emitted.

  Advisories never fail a validation pass; they travel on the raised
  ``TmxErrorGroup`` (its ``advisories`` attribute) for the caller to
  act on -- or not. ``category`` is the ``warnings`` category a caller
  would use if it chose to emit: ``TmxDeprecationWarning`` for
  deprecated constructs, ``TmxWarning`` for spec recommendations.
  """

  category: type[TmxWarning]
  message: str
  path: NodePath


class LanguageTagError(ValueError):
  """A language tag was rejected.

  Subclasses ``ValueError`` so pydantic-shaped callers and existing
  ``except ValueError`` handlers keep working.
  """

  def __init__(self, tag: str, reason: str) -> None:
    super().__init__(tag, reason)
    self.tag = tag
    self.reason = reason

  def __str__(self) -> str:
    return f"not a well-formed BCP 47 language tag {self.tag!r}: {self.reason}"


@dataclass(frozen=True, slots=True)
class NodePath:
  """A path to a field or item, relative to the node being validated.

  Segments alternate between field names (``str``) and item indices
  (``int``): ``"metadata"`` / ``2`` / ``"maps"`` / ``0`` / ``"code"``
  renders as ``metadata[2].maps[0].code``. Build paths with ``/``:

  >>> NodePath() / "metadata" / 2 / "maps" / 0 / "code"
  NodePath(segments=('metadata', 2, 'maps', 0, 'code'))
  """

  segments: tuple[str | int, ...] = ()

  def __truediv__(self, segment: str | int) -> "NodePath":
    return NodePath((*self.segments, segment))

  def __str__(self) -> str:
    text = ""
    for segment in self.segments:
      if isinstance(segment, int):
        text += f"[{segment}]"
      elif text:
        text += f".{segment}"
      else:
        text = segment
    return text or "(root)"


_MAX_REPR_LENGTH = 80


def _truncated_repr(value: object) -> str:
  """``repr(value)``, capped so a huge value cannot flood a diagnostic."""
  text = repr(value)
  if len(text) <= _MAX_REPR_LENGTH:
    return text
  return f"{text[: _MAX_REPR_LENGTH - 3]}..."


def _type_names(expected: type | tuple[type, ...]) -> str:
  if isinstance(expected, tuple):
    return " or ".join(kind.__name__ for kind in expected)
  return expected.__name__


class TmxFieldError(TmxSpecError):
  """One field-level validation failure: where, what, and the value itself.

  A leaf error of a ``TmxErrorGroup``. ``path`` locates the field relative
  to the node being validated; ``value`` is the offending object itself, so
  a handler can read (or re-set) it programmatically.
  """

  def __init__(self, path: NodePath, value: object, message: str) -> None:
    super().__init__(message)
    self.path = path
    self.value = value

  def __reduce__(self) -> tuple[type, tuple[object, ...]]:
    # The default __reduce__ reconstructs via cls(*args), which loses the
    # path and value (and crashes on the leaf __init__ signatures).
    return (self.__class__, (self.path, self.value, self.args[0]))

  def __str__(self) -> str:
    return f"{self.path}: {self.args[0]} (value: {_truncated_repr(self.value)})"


class TmxFieldTypeError(TmxFieldError):
  """A field holds a value of the wrong runtime type."""

  def __init__(self, path: NodePath, value: object, expected: type | tuple[type, ...]) -> None:
    super().__init__(path, value, f"expected {_type_names(expected)}, got {type(value).__name__}")
    self.expected = expected

  def __reduce__(self) -> tuple[type, tuple[object, ...]]:
    return (self.__class__, (self.path, self.value, self.expected))


class TmxFieldValueError(TmxFieldError):
  """A field's runtime type is right, but its value is rejected."""

  def __init__(self, path: NodePath, value: object, reason: str) -> None:
    super().__init__(path, value, reason)


class TmxContractError(TmxFieldError):
  """A field violates a spec rule that involves other fields or nodes.

  Unlike ``TmxFieldValueError`` the field itself may hold a perfectly typed
  value; the rule it breaks is cross-field, so the message names the
  requirement, not just the value.
  """

  def __init__(self, path: NodePath, value: object, requirement: str) -> None:
    super().__init__(path, value, requirement)


class TmxErrorGroup(ExceptionGroup):
  """The group of ``TmxFieldError`` failures raised by a validation pass.

  Subclasses ``ExceptionGroup`` so a whole pass is catchable as one object
  while ``except* TmxFieldTypeError`` and friends still filter individual
  leaves out of it. ``errors`` must be non-empty: ``ExceptionGroup``
  itself rejects empty groups, and a pass with no failures raises nothing,
  however many advisories it gathered.
  """

  advisories: tuple[TmxAdvisory, ...]
  """Advisories gathered during the same pass, if the caller cares."""

  def __new__(
    cls,
    message: str,
    errors: Sequence[Exception],
    advisories: Sequence[TmxAdvisory] = (),
  ) -> "TmxErrorGroup":
    return super().__new__(cls, message, list(errors))

  def __init__(
    self,
    message: str,
    errors: Sequence[Exception],
    advisories: Sequence[TmxAdvisory] = (),
  ) -> None:
    super().__init__(message, errors)
    self.advisories = tuple(advisories)

  def derive(self, excs: Sequence[BaseException]) -> "TmxErrorGroup":
    return self.__class__(self.message, [exc for exc in excs if isinstance(exc, Exception)], self.advisories)
