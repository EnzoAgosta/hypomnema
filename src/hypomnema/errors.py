"""Error hierarchy."""


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
