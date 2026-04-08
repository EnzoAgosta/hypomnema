"""Pure functions for XML namespace handling.

This module provides namespace registration, deregistration, resolution, and
formatting using Clark notation ({uri}local) as the internal representation.

Registration validates NCNames and URIs. Resolution and formatting are fast
hot paths that do not re-validate.
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
  """Look up a prefix in nsmap first, then global_nsmap. Returns None if not found."""
  if nsmap is not None and prefix in nsmap:
    return nsmap[prefix]
  if prefix in global_nsmap:
    return global_nsmap[prefix]
  return None


def _lookup_reverse_ns(
  uri: str, *, global_nsmap: Mapping[str, str], nsmap: Mapping[str, str] | None
) -> str | None:
  """Look up a URI in nsmap first, then global_nsmap. Returns the prefix or None."""
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
  """Look up the prefix for a URI with successive lookup and ambiguity checking.

  Searches nsmap first, then global_nsmap. Raises MultiplePrefixesError
  if multiple prefixes in the same map map to the URI. Raises
  UnregisteredURIError if the URI is not found in either map.
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
  """Parse a name string into (prefix, uri, localname) parts.

  Accepts Clark notation ({uri}local), prefixed (prefix:local), or bare local names.
  Returns (None, None, localname) for bare names.
  Returns (None, uri, localname) for Clark notation (prefix not yet resolved).
  Returns (prefix, None, localname) for prefixed names (uri not yet resolved).
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
  """Resolve a name into (prefix, uri, localname, clark) parts.

  Accepts: ``{uri}local``, ``prefix:local``, or bare ``local``.
  Looks up prefixes in *nsmap* first, then *global_nsmap*.
  Built-in: ``"xml"`` prefix always maps to ``XML_NS_URI``.

  Returns:
    A :class:`ResolveResult` named tuple.

  Raises:
    UnregisteredPrefixError: On unknown prefix.
    MultiplePrefixesError: On names with multiple colons.
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
  """Convert a resolved name or Clark notation string to requested output format.

  ``"qualified"`` → ``{uri}local`` or ``local`` (passthrough)
  ``"local"``     → ``local`` (strip namespace, even if namespaced)
  ``"prefixed"``  → ``prefix:local`` or ``local`` (raises
    :class:`UnregisteredURIError` if URI unknown, :class:`MultiplePrefixesError`
    if multiple prefixes map to the same URI in one map)

  For plain local names (no namespace), all three notations return the same string.

  Uses successive lookups: *nsmap* first, then *global_nsmap*.
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
