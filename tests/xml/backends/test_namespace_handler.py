"""Tests for NamespaceHandler class."""

from logging import DEBUG, WARNING
from typing import cast

import pytest

from hypomnema.base.errors import (
  ExistingNamespaceError,
  InvalidNCNameError,
  InvalidPolicyActionError,
  MultiplePrefixesError,
  RestrictedPrefixError,
  RestrictedURIError,
  UnregisteredPrefixError,
  UnregisteredURIError,
)
from hypomnema.xml.backends.base import NamespaceHandler
from hypomnema.xml.policy import Behavior, NamespacePolicy, RaiseIgnore, RaiseIgnoreOverwrite


class TestNamespaceHandlerInit:
  """Tests for NamespaceHandler initialization."""

  def test_default_initialization(self) -> None:
    handler = NamespaceHandler()
    assert handler.nsmap == {}
    assert handler.logger is not None
    assert handler.policy is not None

  def test_with_custom_policy(self) -> None:
    custom_policy = NamespacePolicy()
    handler = NamespaceHandler(policy=custom_policy)
    assert handler.policy is custom_policy

  def test_with_initial_nsmap(self) -> None:
    initial_nsmap = {"xs": "http://www.w3.org/2001/XMLSchema"}
    handler = NamespaceHandler(nsmap=initial_nsmap)
    assert handler.nsmap == initial_nsmap

  def test_with_multiple_initial_namespaces(self) -> None:
    initial_nsmap = {
      "xs": "http://www.w3.org/2001/XMLSchema",
      "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }
    handler = NamespaceHandler(nsmap=initial_nsmap)
    assert len(handler.nsmap) == 2


class TestNamespaceHandlerRegisterNamespace:
  """Tests for register_namespace method."""

  def test_register_new_namespace(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    assert "xs" in handler.nsmap
    assert handler.nsmap["xs"] == "http://www.w3.org/2001/XMLSchema"

  def test_register_empty_prefix_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError, match="prefix and uri cannot be empty"):
      handler.register_namespace("", "http://example.com")

  def test_register_empty_uri_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError, match="prefix and uri cannot be empty"):
      handler.register_namespace("xs", "")

  def test_register_xml_prefix_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(RestrictedPrefixError, match="xml"):
      handler.register_namespace("xml", "http://example.com")

  def test_register_xml_namespace_uri_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(RestrictedURIError, match="XML"):
      handler.register_namespace("myxml", "http://www.w3.org/XML/1998/namespace")

  def test_register_existing_prefix_raise_policy(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    with pytest.raises(ExistingNamespaceError):
      handler.register_namespace("xs", "http://example.com")

  def test_register_existing_prefix_ignore_policy(self, caplog: pytest.LogCaptureFixture) -> None:
    policy = NamespacePolicy(existing_namespace=Behavior(RaiseIgnoreOverwrite.IGNORE, WARNING))
    handler = NamespaceHandler(policy=policy)
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    with caplog.at_level(WARNING):
      handler.register_namespace("xs", "http://example.com")
    assert handler.nsmap["xs"] == "http://www.w3.org/2001/XMLSchema"
    assert len(caplog.records) == 1
    assert "already registered" in caplog.records[0].message

  def test_register_existing_prefix_overwrite_policy(
    self, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = NamespacePolicy(existing_namespace=Behavior(RaiseIgnoreOverwrite.OVERWRITE, WARNING))
    handler = NamespaceHandler(policy=policy)
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    with caplog.at_level(WARNING):
      handler.register_namespace("xs", "http://example.com")
    assert handler.nsmap["xs"] == "http://example.com"
    assert len(caplog.records) == 2
    assert "already registered" in caplog.records[0].message
    assert "Overwriting existing uri" in caplog.records[1].message

  def test_register_invalid_ncname_prefix_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(InvalidNCNameError):
      handler.register_namespace("123invalid", "http://example.com")

  def test_register_invalid_uri_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError):
      handler.register_namespace("xs", "not a valid uri")


class TestNamespaceHandlerDeregisterPrefix:
  """Tests for deregister_prefix method."""

  def test_deregister_existing_prefix(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    handler.deregister_prefix("xs")
    assert "xs" not in handler.nsmap

  def test_deregister_empty_prefix_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError, match="prefix cannot be empty"):
      handler.deregister_prefix("")

  def test_deregister_xml_prefix_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(RestrictedPrefixError, match="xml"):
      handler.deregister_prefix("xml")

  def test_deregister_nonexistent_prefix_raise_policy(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(UnregisteredPrefixError):
      handler.deregister_prefix("nonexistent")

  def test_deregister_nonexistent_prefix_ignore_policy(
    self, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = NamespaceHandler(policy=policy)
    with caplog.at_level(WARNING):
      handler.deregister_prefix("nonexistent")
    assert len(caplog.records) == 1
    assert "not registered" in caplog.records[0].message


class TestNamespaceHandlerQualifyName:
  """Tests for qualify_name method."""

  def test_qualify_simple_local_name(self) -> None:
    handler = NamespaceHandler()
    prefix, uri, localname = handler.qualify_name("element", nsmap={})
    assert prefix is None
    assert uri is None
    assert localname == "element"

  def test_qualify_prefixed_name_registered(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    prefix, uri, localname = handler.qualify_name("xs:element", nsmap=handler.nsmap)
    assert prefix == "xs"
    assert uri == "http://www.w3.org/2001/XMLSchema"
    assert localname == "element"

  def test_qualify_prefixed_name_unregistered_raise_policy(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(UnregisteredPrefixError):
      handler.qualify_name("xs:element", nsmap={})

  def test_qualify_prefixed_name_unregistered_ignore_policy(
    self, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = NamespaceHandler(policy=policy)
    with caplog.at_level(WARNING):
      prefix, uri, localname = handler.qualify_name("xs:element", nsmap={})
    assert prefix == "xs"
    assert uri is None
    assert localname == "element"
    assert len(caplog.records) == 1
    assert "not registered" in caplog.records[0].message

  def test_qualify_clark_notation_registered(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    prefix, uri, localname = handler.qualify_name(
      "{http://www.w3.org/2001/XMLSchema}element", nsmap=handler.nsmap
    )
    assert prefix == "xs"
    assert uri == "http://www.w3.org/2001/XMLSchema"
    assert localname == "element"

  def test_qualify_clark_notation_unregistered_raise_policy(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(UnregisteredURIError):
      handler.qualify_name("{http://example.com}element", nsmap={})

  def test_qualify_clark_notation_unregistered_ignore_policy(
    self, caplog: pytest.LogCaptureFixture
  ) -> None:
    policy = NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE, WARNING))
    handler = NamespaceHandler(policy=policy)
    with caplog.at_level(WARNING):
      prefix, uri, localname = handler.qualify_name("{http://example.com}element", nsmap={})
    assert prefix is None
    assert uri == "http://example.com"
    assert localname == "element"
    assert len(caplog.records) == 1
    assert "not registered" in caplog.records[0].message

  def test_qualify_qname_like_object(self) -> None:
    class MockQName:
      @property
      def text(self) -> str:
        return "element"

    handler = NamespaceHandler()
    prefix, uri, localname = handler.qualify_name(MockQName(), nsmap={})
    assert prefix is None
    assert uri is None
    assert localname == "element"

  def test_qualify_empty_tag_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError, match="Tag cannot be empty"):
      handler.qualify_name("", nsmap={})

  def test_qualify_malformed_clark_notation_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError, match="Malformed Clark notation"):
      handler.qualify_name("{http://example.comelement", nsmap={})

  def test_qualify_multiple_colons_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(MultiplePrefixesError):
      handler.qualify_name("a:b:c", nsmap={})

  def test_qualify_invalid_ncname_localname_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(InvalidNCNameError):
      handler.qualify_name("123invalid", nsmap={})

  def test_qualify_invalid_uri_in_clark_raises(self) -> None:
    handler = NamespaceHandler()
    with pytest.raises(ValueError):
      handler.qualify_name("{not a valid uri}element", nsmap={})


class TestNamespaceHandlerLogging:
  """Tests for logging behavior."""

  def test_log_with_none_log_level(self, caplog: pytest.LogCaptureFixture) -> None:
    policy = NamespacePolicy(existing_namespace=Behavior(RaiseIgnoreOverwrite.IGNORE, None))
    handler = NamespaceHandler(policy=policy)
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    with caplog.at_level(DEBUG):
      handler.register_namespace("xs", "http://example.com")
    assert len(caplog.records) == 0

  def test_log_with_valid_log_level(self, caplog: pytest.LogCaptureFixture) -> None:
    policy = NamespacePolicy(existing_namespace=Behavior(RaiseIgnoreOverwrite.IGNORE, DEBUG))
    handler = NamespaceHandler(policy=policy)
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    with caplog.at_level(DEBUG):
      handler.register_namespace("xs", "http://example.com")
    assert len(caplog.records) == 1
    assert "already registered" in caplog.records[0].message
    assert caplog.records[0].levelname == "DEBUG"


class TestNamespaceHandlerInvalidPolicyAction:
  """Tests for invalid policy action handling."""

  def test_handle_existing_namespace_invalid_action(self) -> None:
    behavior = Behavior(cast(RaiseIgnoreOverwrite, "invalid_action"), DEBUG)
    policy = NamespacePolicy(existing_namespace=behavior)
    handler = NamespaceHandler(policy=policy)
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    with pytest.raises(InvalidPolicyActionError, match="Invalid behavior"):
      handler.register_namespace("xs", "http://example.com")

  def test_handle_inexistent_prefix_invalid_action(self) -> None:
    behavior = Behavior(cast(RaiseIgnore, "invalid_action"), DEBUG)
    policy = NamespacePolicy(inexistent_namespace=behavior)
    handler = NamespaceHandler(policy=policy)
    with pytest.raises(InvalidPolicyActionError, match="Invalid behavior"):
      handler.deregister_prefix("nonexistent")

  def test_handle_inexistent_uri_invalid_action(self) -> None:
    behavior = Behavior(cast(RaiseIgnore, "invalid_action"), DEBUG)
    policy = NamespacePolicy(inexistent_namespace=behavior)
    handler = NamespaceHandler(policy=policy)
    with pytest.raises(InvalidPolicyActionError, match="Invalid behavior"):
      handler.qualify_name("{http://example.com}element", nsmap={})


class TestNamespaceHandlerEdgeCases:
  """Edge case tests for NamespaceHandler."""

  def test_nsmap_is_mutable(self) -> None:
    handler = NamespaceHandler()
    handler.nsmap["test"] = "http://example.com"
    assert "test" in handler.nsmap
    assert handler.nsmap["test"] == "http://example.com"

  def test_deregister_twice_raises(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("xs", "http://www.w3.org/2001/XMLSchema")
    handler.deregister_prefix("xs")
    with pytest.raises(UnregisteredPrefixError):
      handler.deregister_prefix("xs")

  def test_qualify_clark_notation_with_no_nsmap(self, caplog: pytest.LogCaptureFixture) -> None:
    policy = NamespacePolicy(inexistent_namespace=Behavior(RaiseIgnore.IGNORE, DEBUG))
    handler = NamespaceHandler(policy=policy)
    with caplog.at_level(DEBUG):
      prefix, uri, localname = handler.qualify_name("{http://example.com}element", nsmap={})
    assert prefix is None
    assert uri == "http://example.com"
    assert localname == "element"
    assert len(caplog.records) == 1

  def test_register_with_ascii_uri(self) -> None:
    handler = NamespaceHandler()
    handler.register_namespace("myns", "http://example.com/ns")
    assert "myns" in handler.nsmap

  def test_qualify_unicode_localname(self) -> None:
    handler = NamespaceHandler()
    prefix, uri, localname = handler.qualify_name("\u4e2d\u6587", nsmap={})
    assert localname == "\u4e2d\u6587"
