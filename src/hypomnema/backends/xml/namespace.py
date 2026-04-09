"""Pure functions for XML namespace handling.

This module provides namespace registration, deregistration, resolution, and
formatting using Clark notation (``{uri}local``) as the internal representation.

The public API consists of:

- :func:`register_namespace` / :func:`deregister_prefix` / :func:`deregister_uri`
  for managing prefix↔URI mappings in a dict.
- :func:`resolve` for turning a prefixed or Clark-notation name into a
  :class:`ResolveResult` with all four components (prefix, uri, localname, clark).
- :func:`format_notation` for converting a resolved name or Clark string into
  ``"qualified"``, ``"local"``, or ``"prefixed"`` output.

All resolution and formatting functions perform successive lookups — the
per-call *nsmap* is consulted first, then the *global_nsmap* — rather than
merging dicts. The ``"xml"`` prefix is a built-in that always maps to
``XML_NS_URI`` regardless of the maps.

Registration validates NCNames and URIs via :func:`.validate_ncname` and
:func:`.validate_uri`. Resolution and formatting are fast hot paths that do
not re-validate.
"""

from collections.abc import Mapping
from typing import Literal, NamedTuple

from hypomnema.backends.xml.errors import (
  ExistingNamespaceError,
  MultiplePrefixesError,
  RestrictedPrefixError,
  RestrictedURIError,
  UnregisteredPrefixError,
  UnregisteredURIError,
)
from hypomnema.backends.xml.utils import validate_ncname, validate_uri

XML_NS_URI = "http://www.w3.org/XML/1998/namespace"
XML_NS_PREFIX = "xml"


class ResolveResult(NamedTuple):
  """Result of resolving an XML name via :func:`resolve`.

  Attributes:
      prefix: Namespace prefix, or ``None`` for bare/local names. ``""`` for
          the default namespace (``xmlns="..."``).
      uri: Namespace URI, or ``None`` for un-namespaced names.
      localname: The local part of the name (after any prefix or URI).
      clark: Clark notation form (``{uri}local`` or bare ``local``).
  """

  prefix: str | None
  uri: str | None
  localname: str
  clark: str


def register_namespace(nsmap: dict[str, str], prefix: str, uri: str) -> None:
  """Add a prefix-to-URI mapping to *nsmap* in-place.

  Validates the prefix as an NCName (with a special-case exception for the
  empty string, representing the default namespace) and the URI per RFC 3986.

  Raises:
    RestrictedPrefixError: If prefix is ``"xml"``.
    RestrictedURIError: If uri is the XML namespace URI.
    ExistingNamespaceError: If prefix already exists in nsmap.
    InvalidNCNameError: If prefix is not a valid NCName.
    ValueError: If uri is empty or invalid.
  """
  if prefix == XML_NS_PREFIX:
    raise RestrictedPrefixError(prefix)
  if uri == XML_NS_URI:
    raise RestrictedURIError(uri)
  if prefix in nsmap:
    raise ExistingNamespaceError(prefix, nsmap[prefix], uri, nsmap)
  if prefix != "":
    validate_ncname(prefix)
  validate_uri(uri)
  nsmap[prefix] = uri


def deregister_prefix(nsmap: dict[str, str], prefix: str) -> None:
  """Remove a prefix mapping from *nsmap* in-place.

  Raises:
    RestrictedPrefixError: If prefix is ``"xml"``.
    UnregisteredPrefixError: If prefix is not in nsmap.
  """
  if prefix == XML_NS_PREFIX:
    raise RestrictedPrefixError(prefix)
  if prefix not in nsmap:
    raise UnregisteredPrefixError(prefix, nsmap)
  del nsmap[prefix]


def deregister_uri(nsmap: dict[str, str], uri: str) -> None:
  """Remove all prefix mappings for *uri* from *nsmap* in-place.

  Raises:
    RestrictedURIError: If uri is the XML namespace URI.
    UnregisteredURIError: If uri is not found in nsmap values.
  """
  if uri == XML_NS_URI:
    raise RestrictedURIError(uri)
  prefixes_to_remove = [prefix for prefix, mapped_uri in nsmap.items() if mapped_uri == uri]
  if not prefixes_to_remove:
    raise UnregisteredURIError(uri, nsmap)
  for prefix in prefixes_to_remove:
    del nsmap[prefix]


def _lookup_ns(
  prefix: str, *, global_nsmap: Mapping[str, str], nsmap: Mapping[str, str] | None
) -> str | None:
  """Look up a prefix in *nsmap* first, then *global_nsmap*.

  Returns the URI string if found, or ``None`` if the prefix is not
  registered in either map.
  """
  if nsmap is not None and prefix in nsmap:
    return nsmap[prefix]
  if prefix in global_nsmap:
    return global_nsmap[prefix]
  return None


def _lookup_reverse_ns(
  uri: str, *, global_nsmap: Mapping[str, str], nsmap: Mapping[str, str] | None
) -> str | None:
  """Look up a URI in *nsmap* first, then *global_nsmap*.

  Returns the first matching prefix string, or ``None`` if the URI is
  not found in either map.
  """
  if nsmap is not None:
    for prefix, mapped_uri in nsmap.items():
      if mapped_uri == uri:
        return prefix
  for prefix, mapped_uri in global_nsmap.items():
    if mapped_uri == uri:
      return prefix
  return None


def _lookup_prefix_for_uri(
  uri: str, *, global_nsmap: Mapping[str, str], nsmap: Mapping[str, str] | None
) -> str:
  """Look up the prefix for a URI using successive lookup and ambiguity checking.

  Searches *nsmap* first. If not found there, searches *global_nsmap*.
  Within each map, raises :class:`MultiplePrefixesError` if more than
  one prefix maps to the same URI. Raises :class:`UnregisteredURIError`
  if the URI is not found in either map.
  """
  if nsmap is not None:
    prefixes = [prefix for prefix, mapped_uri in nsmap.items() if mapped_uri == uri]
    if len(prefixes) > 1:
      raise MultiplePrefixesError(f"{{{uri}}}")
    if len(prefixes) == 1:
      return prefixes[0]
  prefixes = [prefix for prefix, mapped_uri in global_nsmap.items() if mapped_uri == uri]
  if len(prefixes) > 1:
    raise MultiplePrefixesError(f"{{{uri}}}")
  if len(prefixes) == 1:
    return prefixes[0]

  raise UnregisteredURIError(uri, {**global_nsmap, **(nsmap or {})})


def _parse_name(name: str) -> tuple[str | None, str | None, str]:
  """Parse a name string into ``(prefix, uri, localname)`` parts.

  Accepts Clark notation (``{uri}local``), prefixed (``prefix:local``),
  default-namespace prefixed (``:local``), or bare local names.

  Returns:
      ``(None, None, localname)`` for bare names.
      ``(None, uri, localname)`` for Clark notation (prefix not yet resolved).
      ``(prefix, None, localname)`` for prefixed names (uri not yet resolved).
      ``("", None, localname)`` for default-namespace prefixed names.

  Raises:
      ValueError: On empty strings, malformed Clark notation, or empty
          localnames.
      MultiplePrefixesError: On names with more than one colon.
  """
  if not name:
    raise ValueError("Name cannot be empty")
  if name.startswith("{"):
    if "}" not in name[1:]:
      raise ValueError(f"Malformed Clark notation: missing }} in {name!r}")
    uri, localname = name[1:].split("}", 1)
    if not localname:
      raise ValueError(f"Malformed Clark notation: empty localname in {name!r}")
    return None, uri, localname

  match name.split(":"):
    case [prefix, localname] if not prefix:
      if not localname:
        raise ValueError(f"Malformed prefixed name: empty localname in {name!r}")
      return "", None, localname
    case [prefix, localname]:
      if not localname:
        raise ValueError(f"Malformed prefixed name: empty localname in {name!r}")
      return prefix, None, localname
    case [localname]:
      return None, None, localname
    case _:
      raise MultiplePrefixesError(name)


def resolve(
  name: str, *, global_nsmap: Mapping[str, str], nsmap: Mapping[str, str] | None = None
) -> ResolveResult:
  """Resolve an XML name into its component parts.

  Accepts Clark notation (``{uri}local``), prefixed names (``prefix:local``),
  default-namespace names (``:local``), and bare local names (``local``).

  For prefixed names, the prefix is looked up in *nsmap* first, then
  *global_nsmap*. For Clark notation, the URI is reverse-resolved to a
  prefix via the same successive lookup. The ``"xml"`` prefix is a
  built-in that always maps to ``http://www.w3.org/XML/1998/namespace``
  regardless of the current namespace map.

  Args:
      name: The name to resolve.
      global_nsmap: The global (fallback) namespace prefix→URI map.
      nsmap: An optional per-call namespace map, consulted before
          *global_nsmap*.

  Returns:
      A :class:`ResolveResult` named tuple.

  Raises:
      UnregisteredPrefixError: On unknown prefix (including empty prefix
          for the default namespace when ``""`` is not in any map).
      MultiplePrefixesError: On names with more than one colon.
      ValueError: On malformed names.
  """
  prefix, uri, localname = _parse_name(name)

  match (prefix, uri, localname):
    case (None, None, localname):
      return ResolveResult(None, None, localname, localname)

    case ("", None, localname):
      default_uri = _lookup_ns("", global_nsmap=global_nsmap, nsmap=nsmap)
      if default_uri is None:
        raise UnregisteredPrefixError("", {**global_nsmap, **(nsmap or {})})
      clark = f"{{{default_uri}}}{localname}"
      return ResolveResult("", default_uri, localname, clark)

    case (str(), None, localname):
      if prefix == XML_NS_PREFIX:
        clark = f"{{{XML_NS_URI}}}{localname}"
        return ResolveResult(XML_NS_PREFIX, XML_NS_URI, localname, clark)
      uri = _lookup_ns(prefix, global_nsmap=global_nsmap, nsmap=nsmap)
      if uri is None:
        raise UnregisteredPrefixError(prefix, {**global_nsmap, **(nsmap or {})})
      clark = f"{{{uri}}}{localname}"
      return ResolveResult(prefix, uri, localname, clark)

    case (None, str(), localname):
      prefix = _lookup_reverse_ns(uri, global_nsmap=global_nsmap, nsmap=nsmap)
      clark = f"{{{uri}}}{localname}"
      return ResolveResult(prefix, uri, localname, clark)
    case _:
      raise MultiplePrefixesError(name)


def format_notation(
  result: ResolveResult | str,
  notation: Literal["qualified", "local", "prefixed"],
  *,
  global_nsmap: Mapping[str, str],
  nsmap: Mapping[str, str] | None = None,
) -> str:
  """Convert a resolved name or Clark notation string to the requested format.

  If *result* is a string, it is first resolved via :func:`resolve`.

  Notations:

      ``"qualified"`` → ``{uri}local`` or bare ``local`` (passthrough).
      ``"local"``     → ``local`` (strip namespace, even if namespaced).
      ``"prefixed"``  → ``prefix:local``. Uses successive lookup
          (*nsmap* first, then *global_nsmap*) and raises
          :class:`UnregisteredURIError` if the URI is not found, or
          :class:`MultiplePrefixesError` if multiple prefixes in the same
          map map to the URI. For plain local names (no namespace), returns
          the localname without a colon.

  For plain local names (no namespace), all three notations return the
  same string.

  Args:
      result: A :class:`ResolveResult` or a Clark notation string.
      notation: The desired output format.
      global_nsmap: The global (fallback) namespace prefix→URI map.
      nsmap: An optional per-call namespace map, consulted before
          *global_nsmap*.

  Raises:
      UnregisteredURIError: On ``"prefixed"`` notation when the URI is
          not in any map.
      MultiplePrefixesError: On ``"prefixed"`` notation when multiple
          prefixes in the same map map to the URI.
  """
  if isinstance(result, str):
    result = resolve(result, global_nsmap=global_nsmap, nsmap=nsmap)
  if result.uri is None:
    return result.localname
  match notation:
    case "qualified":
      return result.clark
    case "local":
      return result.localname
    case "prefixed":
      prefix = _lookup_prefix_for_uri(result.uri, global_nsmap=global_nsmap, nsmap=nsmap)
      return f"{prefix}:{result.localname}"
