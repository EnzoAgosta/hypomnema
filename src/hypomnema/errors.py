"""TMX validation errors, grouped failures, and advisory records.

Field failures carry paths and rejected values. A validation pass combines
failures in TmxErrorGroup, which supports ``except*`` handlers by error type.
Advisories describe recommendations and deprecated constructs without making
validation fail.
"""

from collections.abc import Sequence
from dataclasses import dataclass


class TmxError(Exception):
  """Base exception for failures concerning TMX data."""


class TmxSpecError(TmxError):
  """Base exception for violations of the TMX data contract."""


class TmxWarning(UserWarning):
  """Warning category for TMX recommendations that do not fail validation.

  Validators collect advisories and do not emit warnings. Callers can choose
  to emit those advisories using Python's ``warnings`` module, which supports
  filtering and escalation by category.
  """


class TmxDeprecationWarning(TmxWarning):
  """Warning category for deprecated TMX constructs such as lang and ut.

  This TmxWarning subclass allows deprecation warnings to be filtered
  separately from other TMX recommendations.
  """


@dataclass(frozen=True, slots=True)
class TmxAdvisory:
  """An immutable advisory collected during a validation pass.

  Attributes:
      category: Warning category to use if the caller emits this advisory.
      message: Human-readable recommendation or deprecation message.
      path: Location relative to the node being validated.
  """

  category: type[TmxWarning]
  message: str
  path: NodePath


class LanguageTagError(ValueError):
  """A rejected language tag and its grammar failure reason.

  Inherits ValueError so Pydantic can wrap the failure in ValidationError.

  Attributes:
      tag: Rejected input string.
      reason: Description of the syntax failure.
  """

  def __init__(self, tag: str, reason: str) -> None:
    """Record the rejected tag and its syntax failure reason."""
    super().__init__(tag, reason)
    self.tag = tag
    self.reason = reason

  def __str__(self) -> str:
    """Return the rejected tag and reason in a diagnostic message."""
    return f"not a well-formed BCP 47 language tag {self.tag!r}: {self.reason}"


@dataclass(frozen=True, slots=True)
class NodePath:
  """An immutable path relative to the node being validated.

  Attributes:
      segments: Ordered field names and list indices. An empty tuple denotes
          the root. Append a segment with the division operator.

  Examples:
      >>> str(NodePath() / "metadata" / 2 / "maps" / 0 / "code")
      'metadata[2].maps[0].code'
  """

  segments: tuple[str | int, ...] = ()

  def __truediv__(self, segment: str | int) -> NodePath:
    """Return a new path with a field name or list index appended."""
    return NodePath((*self.segments, segment))

  def __str__(self) -> str:
    """Render dotted fields and bracketed indices, or ``(root)`` when empty."""
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
  """Return a representation capped at 80 characters, including any ellipsis."""
  text = repr(value)
  if len(text) <= _MAX_REPR_LENGTH:
    return text
  return f"{text[: _MAX_REPR_LENGTH - 3]}..."


def _type_names(expected: type | tuple[type, ...]) -> str:
  """Join expected type names with ``or`` for a diagnostic message."""
  if isinstance(expected, tuple):
    return " or ".join(kind.__name__ for kind in expected)
  return expected.__name__


class TmxFieldError(TmxSpecError):
  """One validation failure with the original rejected value and its path.

  Attributes:
      path: Field or item location relative to the node being validated.
      value: Rejected object itself, without copying or string conversion.
  """

  def __init__(self, path: NodePath, value: object, message: str) -> None:
    """Record a path, rejected value, and human-readable failure message."""
    super().__init__(message)
    self.path = path
    self.value = value

  def __reduce__(self) -> tuple[type, tuple[object, ...]]:
    """Preserve the path, value, and message when pickling this exception."""
    # The default __reduce__ reconstructs via cls(*args), which loses the
    # path and value (and crashes on the leaf __init__ signatures).
    return (self.__class__, (self.path, self.value, self.args[0]))

  def __str__(self) -> str:
    """Format the path and message with a truncated representation of the value."""
    return f"{self.path}: {self.args[0]} (value: {_truncated_repr(self.value)})"


class TmxFieldTypeError(TmxFieldError):
  """A field whose value has an unexpected runtime type.

  Attributes:
      expected: Accepted type or tuple of accepted types.
  """

  def __init__(self, path: NodePath, value: object, expected: type | tuple[type, ...]) -> None:
    """Record the rejected value and accepted runtime types at a path."""
    super().__init__(path, value, f"expected {_type_names(expected)}, got {type(value).__name__}")
    self.expected = expected

  def __reduce__(self) -> tuple[type, tuple[object, ...]]:
    """Preserve the path, value, and expected types when pickling."""
    return (self.__class__, (self.path, self.value, self.expected))


class TmxFieldValueError(TmxFieldError):
  """A correctly typed field whose value fails validation."""

  def __init__(self, path: NodePath, value: object, reason: str) -> None:
    """Record the path, rejected value, and reason for rejection."""
    super().__init__(path, value, reason)


class TmxContractError(TmxFieldError):
  """A violation of a TMX rule involving related fields or nodes."""

  def __init__(self, path: NodePath, value: object, requirement: str) -> None:
    """Record the path, rejected value, and unmet TMX requirement."""
    super().__init__(path, value, requirement)


class TmxErrorGroup(ExceptionGroup):
  """A nonempty group of validation failures with collected advisories.

  Supports ``except*`` selection of individual error types. Splitting or
  selecting a subgroup retains all advisories from the original group.
  This class inherits ExceptionGroup directly, not TmxError.

  Attributes:
      advisories: Immutable sequence of advisories from the same pass.
  """

  advisories: tuple[TmxAdvisory, ...]
  """Advisories gathered during the same pass, if the caller cares."""

  def __new__(
    cls,
    message: str,
    errors: Sequence[Exception],
    advisories: Sequence[TmxAdvisory] = (),
  ) -> "TmxErrorGroup":
    """Allocate an exception group from a nonempty sequence of exceptions.

    Raises:
        ValueError: The error sequence is empty.
        TypeError: A member is not an Exception instance.
    """
    return super().__new__(cls, message, list(errors))

  def __init__(
    self,
    message: str,
    errors: Sequence[Exception],
    advisories: Sequence[TmxAdvisory] = (),
  ) -> None:
    """Initialize grouped failures and snapshot their advisory sequence.

    Args:
        message: Description of the validation failure group.
        errors: Nonempty sequence of exceptions gathered during validation.
        advisories: Recommendations collected during the same pass.
    """
    super().__init__(message, errors)
    self.advisories = tuple(advisories)

  def derive(self, excs: Sequence[BaseException]) -> "TmxErrorGroup":
    """Create a subgroup while retaining this group's message and advisories.

    Args:
        excs: Exceptions selected by ExceptionGroup operations. Members that
            are not Exception instances are discarded.

    Returns:
        A group of the same concrete type containing the remaining exceptions.

    Raises:
        ValueError: No Exception instances remain.
    """
    return self.__class__(self.message, [exc for exc in excs if isinstance(exc, Exception)], self.advisories)
