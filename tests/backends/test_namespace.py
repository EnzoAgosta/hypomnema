"""Tests for the namespace.py pure functions."""

import pytest

from hypomnema.backends.xml.errors import (
  ExistingNamespaceError,
  InvalidNCNameError,
  MultiplePrefixesError,
  RestrictedPrefixError,
  RestrictedURIError,
  UnregisteredPrefixError,
  UnregisteredURIError,
)
from hypomnema.backends.xml.namespace import (
  XML_NS_PREFIX,
  XML_NS_URI,
  deregister_prefix,
  deregister_uri,
  format_notation,
  register_namespace,
  resolve,
)


# ── register_namespace ──────────────────────────────────────────


class TestRegisterNamespace:
  def test_adds_mapping(self) -> None:
    nsmap: dict[str, str] = {}
    register_namespace(nsmap, "xs", "http://www.w3.org/2001/XMLSchema")
    assert nsmap == {"xs": "http://www.w3.org/2001/XMLSchema"}

  def test_rejects_reserved_prefix(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(RestrictedPrefixError):
      register_namespace(nsmap, XML_NS_PREFIX, "http://example.com")

  def test_rejects_reserved_uri(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(RestrictedURIError):
      register_namespace(nsmap, "myxml", XML_NS_URI)

  def test_raises_on_duplicate_prefix(self) -> None:
    nsmap: dict[str, str] = {}
    register_namespace(nsmap, "ns", "http://old.example.com")
    with pytest.raises(ExistingNamespaceError):
      register_namespace(nsmap, "ns", "http://new.example.com")

  def test_validates_prefix_as_ncname(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(InvalidNCNameError):
      register_namespace(nsmap, "1bad", "http://example.com")

  def test_validates_uri(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(ValueError):
      register_namespace(nsmap, "ns", "")

  def test_allows_empty_prefix(self) -> None:
    nsmap: dict[str, str] = {}
    register_namespace(nsmap, "", "http://example.com/default")
    assert nsmap == {"": "http://example.com/default"}


# ── deregister_prefix ──────────────────────────────────────────


class TestDeregisterPrefix:
  def test_removes_mapping(self) -> None:
    nsmap: dict[str, str] = {"ns": "http://example.com/ns"}
    deregister_prefix(nsmap, "ns")
    assert nsmap == {}

  def test_rejects_reserved(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(RestrictedPrefixError):
      deregister_prefix(nsmap, XML_NS_PREFIX)

  def test_raises_on_missing(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(UnregisteredPrefixError):
      deregister_prefix(nsmap, "missing")


# ── deregister_uri ──────────────────────────────────────────


class TestDeregisterUri:
  def test_removes_all_prefixes_for_uri(self) -> None:
    nsmap: dict[str, str] = {"a": "http://example.com/ns", "b": "http://example.com/ns"}
    deregister_uri(nsmap, "http://example.com/ns")
    assert nsmap == {}

  def test_rejects_reserved(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(RestrictedURIError):
      deregister_uri(nsmap, XML_NS_URI)

  def test_raises_on_missing(self) -> None:
    nsmap: dict[str, str] = {}
    with pytest.raises(UnregisteredURIError):
      deregister_uri(nsmap, "http://missing.example.com")


# ── resolve ──────────────────────────────────────────


class TestResolve:
  def test_prefixed_name_returns_clark(self) -> None:
    result = resolve("ns:item", global_nsmap={"ns": "http://example.com/ns"})
    assert result.clark == "{http://example.com/ns}item"

  def test_prefixed_name_returns_prefix_and_uri(self) -> None:
    result = resolve("ns:item", global_nsmap={"ns": "http://example.com/ns"})
    assert result.prefix == "ns"
    assert result.uri == "http://example.com/ns"
    assert result.localname == "item"

  def test_clark_notation_passthrough(self) -> None:
    result = resolve("{http://example.com/ns}item", global_nsmap={"ns": "http://example.com/ns"})
    assert result.clark == "{http://example.com/ns}item"
    assert result.uri == "http://example.com/ns"
    assert result.localname == "item"

  def test_clark_notation_resolves_prefix(self) -> None:
    result = resolve("{http://example.com/ns}item", global_nsmap={"ns": "http://example.com/ns"})
    assert result.prefix == "ns"

  def test_local_name(self) -> None:
    result = resolve("item", global_nsmap={})
    assert result.prefix is None
    assert result.uri is None
    assert result.localname == "item"
    assert result.clark == "item"

  def test_xml_prefix_builtin(self) -> None:
    result = resolve("xml:lang", global_nsmap={})
    assert result.clark == f"{{{XML_NS_URI}}}lang"

  def test_nsmap_overrides_global_nsmap(self) -> None:
    result = resolve(
      "ns:item",
      global_nsmap={"ns": "http://fallback.example.com"},
      nsmap={"ns": "http://override.example.com"},
    )
    assert result.clark == "{http://override.example.com}item"

  def test_raises_on_unknown_prefix(self) -> None:
    with pytest.raises(UnregisteredPrefixError):
      resolve("missing:item", global_nsmap={})

  def test_raises_on_multiple_colons(self) -> None:
    with pytest.raises(MultiplePrefixesError):
      resolve("a:b:c", global_nsmap={})

  def test_empty_prefix_default_namespace(self) -> None:
    result = resolve(":item", global_nsmap={"": "http://example.com/default"})
    assert result.clark == "{http://example.com/default}item"

  def test_clark_unknown_uri_no_prefix(self) -> None:
    result = resolve("{http://unknown.example.com}item", global_nsmap={})
    assert result.prefix is None
    assert result.uri == "http://unknown.example.com"
    assert result.localname == "item"


# ── format_notation ──────────────────────────────────────────


class TestFormatNotation:
  def test_qualified(self) -> None:
    assert (
      format_notation("{http://example.com/ns}item", "qualified", global_nsmap={})
      == "{http://example.com/ns}item"
    )

  def test_local(self) -> None:
    assert format_notation("{http://example.com/ns}item", "local", global_nsmap={}) == "item"

  def test_prefixed(self) -> None:
    assert (
      format_notation(
        "{http://example.com/ns}item", "prefixed", global_nsmap={"ns": "http://example.com/ns"}
      )
      == "ns:item"
    )

  def test_prefixed_raises_on_unknown_uri(self) -> None:
    with pytest.raises(UnregisteredURIError):
      format_notation("{http://unknown.example.com}item", "prefixed", global_nsmap={})

  def test_prefixed_raises_on_multiple_prefixes(self) -> None:
    nsmap = {"a": "http://example.com/ns", "b": "http://example.com/ns"}
    with pytest.raises(MultiplePrefixesError):
      format_notation("{http://example.com/ns}item", "prefixed", global_nsmap=nsmap)

  def test_plain_local_name_qualified(self) -> None:
    assert format_notation("header", "qualified", global_nsmap={}) == "header"

  def test_plain_local_name_local(self) -> None:
    assert format_notation("header", "local", global_nsmap={}) == "header"

  def test_plain_local_name_prefixed(self) -> None:
    assert format_notation("header", "prefixed", global_nsmap={}) == "header"

  def test_prefixed_uses_nsmap_first(self) -> None:
    assert (
      format_notation(
        "{http://example.com/ns}item",
        "prefixed",
        global_nsmap={"ns_global": "http://example.com/ns"},
        nsmap={"ns_local": "http://example.com/ns"},
      )
      == "ns_local:item"
    )

  def test_prefixed_uses_global_nsmap_if_not_in_nsmap(self) -> None:
    assert (
      format_notation(
        "{http://example.com/ns}item",
        "prefixed",
        global_nsmap={"ns_global": "http://example.com/ns"},
        nsmap={"other": "http://other.example.com"},
      )
      == "ns_global:item"
    )

  def test_resolve_result_qualified(self) -> None:
    result = resolve("ns:item", global_nsmap={"ns": "http://example.com/ns"})
    assert (
      format_notation(result, "qualified", global_nsmap={"ns": "http://example.com/ns"})
      == "{http://example.com/ns}item"
    )

  def test_resolve_result_local(self) -> None:
    result = resolve("ns:item", global_nsmap={"ns": "http://example.com/ns"})
    assert format_notation(result, "local", global_nsmap={"ns": "http://example.com/ns"}) == "item"

  def test_resolve_result_prefixed(self) -> None:
    result = resolve("ns:item", global_nsmap={"ns": "http://example.com/ns"})
    assert (
      format_notation(result, "prefixed", global_nsmap={"ns": "http://example.com/ns"}) == "ns:item"
    )
