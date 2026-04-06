import pytest

from hypomnema.backends.xml.base import NamespaceHandler
from hypomnema.backends.xml.errors import (
  ExistingNamespaceError,
  RestrictedPrefixError,
  RestrictedURIError,
  UnregisteredPrefixError,
  UnregisteredURIError,
)
from hypomnema.backends.xml.policy import (
  Behavior,
  NamespacePolicy,
  RaiseIgnore,
  RaiseIgnoreOverwrite,
)


def test_namespace_handler_registers_namespace() -> None:
  handler = NamespaceHandler()

  handler.register_namespace("ns", "https://example.com/ns")

  assert handler.nsmap == {"ns": "https://example.com/ns"}


def test_namespace_handler_qualifies_prefixed_name() -> None:
  handler = NamespaceHandler()
  handler.register_namespace("ns", "https://example.com/ns")

  assert handler.qualify_name("ns:item", nsmap=handler.nsmap) == (
    "ns",
    "https://example.com/ns",
    "item",
  )


def test_namespace_handler_qualifies_clark_name() -> None:
  handler = NamespaceHandler()
  handler.register_namespace("ns", "https://example.com/ns")

  assert handler.qualify_name("{https://example.com/ns}item", nsmap=handler.nsmap) == (
    "ns",
    "https://example.com/ns",
    "item",
  )


def test_namespace_handler_qualifies_local_name() -> None:
  handler = NamespaceHandler()

  assert handler.qualify_name("item", nsmap=handler.nsmap) == (None, None, "item")


def test_namespace_handler_deregisters_namespace() -> None:
  handler = NamespaceHandler()
  handler.register_namespace("ns", "https://example.com/ns")

  handler.deregister_prefix("ns")

  assert handler.nsmap == {}


def test_namespace_handler_rejects_restricted_prefix() -> None:
  handler = NamespaceHandler()

  with pytest.raises(RestrictedPrefixError):
    handler.register_namespace("xml", "https://example.com/ns")


def test_namespace_handler_rejects_restricted_uri() -> None:
  handler = NamespaceHandler()

  with pytest.raises(RestrictedURIError):
    handler.register_namespace("ns", "http://www.w3.org/XML/1998/namespace")


def test_namespace_handler_raises_for_existing_namespace_by_default() -> None:
  handler = NamespaceHandler({"ns": "https://example.com/old"})

  with pytest.raises(ExistingNamespaceError):
    handler.register_namespace("ns", "https://example.com/new")


def test_namespace_handler_can_overwrite_existing_namespace_via_policy() -> None:
  handler = NamespaceHandler(
    {"ns": "https://example.com/old"},
    policy=NamespacePolicy(existing_namespace=Behavior(RaiseIgnoreOverwrite.OVERWRITE)),
  )

  handler.register_namespace("ns", "https://example.com/new")

  assert handler.nsmap == {"ns": "https://example.com/new"}


def test_namespace_handler_can_ignore_missing_prefix_via_policy() -> None:
  handler = NamespaceHandler(
    policy=NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE))
  )

  assert handler.qualify_name("missing:item", nsmap=handler.nsmap) == ("missing", None, "item")


def test_namespace_handler_can_ignore_missing_uri_via_policy() -> None:
  handler = NamespaceHandler(
    policy=NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE))
  )

  assert handler.qualify_name("{https://example.com/missing}item", nsmap=handler.nsmap) == (
    None,
    "https://example.com/missing",
    "item",
  )


def test_namespace_handler_raises_for_missing_prefix_by_default() -> None:
  handler = NamespaceHandler()

  with pytest.raises(UnregisteredPrefixError):
    handler.qualify_name("missing:item", nsmap=handler.nsmap)


def test_namespace_handler_raises_for_missing_uri_by_default() -> None:
  handler = NamespaceHandler()

  with pytest.raises(UnregisteredURIError):
    handler.qualify_name("{https://example.com/missing}item", nsmap=handler.nsmap)
