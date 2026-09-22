"""Shared test helpers."""

import pytest

from hypomnema.errors import TmxFieldError


@pytest.fixture
def leaf_errors():
  """A caught ``TmxErrorGroup``'s leaves as ``TmxFieldError`` objects.

  Asserts every leaf is a field error first, so nested groups or foreign
  exception types cannot slip past the structural assertions that use it.
  """

  def leaf_errors(group) -> list[TmxFieldError]:
    """Return field-error leaves after rejecting nested groups and foreign errors."""
    assert all(isinstance(error, TmxFieldError) for error in group.exceptions)
    return [error for error in group.exceptions if isinstance(error, TmxFieldError)]

  return leaf_errors
