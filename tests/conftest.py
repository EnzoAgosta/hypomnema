import logging
import xml.etree.ElementTree as std_et
from collections.abc import Generator, Iterable

import lxml.etree as lxml_et
import pytest

from hypomnema import Deserializer, Serializer, XmlBackend, XmlPolicy
from hypomnema.xml.backends.lxml import LxmlBackend
from hypomnema.xml.backends.standard import StandardBackend
from hypomnema.xml.qname import QNameLike
from tests.strict_backend import StrictBackend

TypeOfBackend = StandardBackend | LxmlBackend | StrictBackend


@pytest.fixture(
  params=["StandardBackend", "LxmlBackend", "StrictBackend"], ids=["Standard", "Lxml", "Strict"]
)
def backend(
  request: pytest.FixtureRequest, test_logger: logging.Logger
) -> Generator[TypeOfBackend]:
  match request.param:
    case "StandardBackend":
      yield StandardBackend(logger=test_logger)
    case "LxmlBackend":
      yield LxmlBackend(logger=test_logger)
    case "StrictBackend":
      yield StrictBackend(logger=test_logger)


@pytest.fixture(scope="session")
def test_logger():
  test_logger = logging.getLogger("test")
  test_logger.setLevel(1)
  return test_logger


def _make_elem[TypeOfBackend](
  backend: XmlBackend[TypeOfBackend],
  tag: str,
  text: str | None = None,
  tail: str | None = None,
  **attrs: str,
) -> TypeOfBackend:
  element = backend.create_element(tag, attributes=attrs)
  backend.set_text(element, text)
  backend.set_tail(element, tail)
  return element


def _append_child[TypeOfBackend](
  backend: XmlBackend[TypeOfBackend], parent: TypeOfBackend, child: TypeOfBackend
) -> None:
  backend.append_child(parent, child)


def xml_equal[TypeOfBackend](
  elem1: TypeOfBackend, elem2: TypeOfBackend, backend: XmlBackend[TypeOfBackend] | None = None
) -> bool:
  if isinstance(backend, StrictBackend):
    _elem1 = backend._get_elem(elem1)
    _elem2 = backend._get_elem(elem2)
  else:
    _elem1 = elem1
    _elem2 = elem2

  match _elem1:
    case lxml_et._Element():
      can_elem1 = lxml_et.tostring(_elem1, method="c14n")
    case std_et.Element():
      can_elem1 = std_et.canonicalize(std_et.tostring(_elem1))  # type: ignore[assignment]
    case _:
      raise TypeError("Unexpected type of elem1")
  match _elem2:
    case lxml_et._Element():
      can_elem2 = lxml_et.tostring(_elem2, method="c14n")
    case std_et.Element():
      can_elem2 = std_et.canonicalize(std_et.tostring(_elem2))  # type: ignore[assignment]
    case _:
      raise TypeError("Unexpected type of elem2")
  return can_elem1 == can_elem2


def _assert_attr[T](backend: XmlBackend, element: T, name: str, expected: str) -> None:
  assert backend.get_attribute(element, name) == expected


def _assert_tag[T](backend: XmlBackend, element: T, expected: str) -> None:
  assert backend.get_tag(element) == expected


def _assert_text[T](backend: XmlBackend, element: T, expected: str) -> None:
  assert backend.get_text(element) == expected


def _serializer(backend: XmlBackend) -> Serializer:
  return Serializer(backend, policy=XmlPolicy())


def _deserializer(backend: XmlBackend) -> Deserializer:
  return Deserializer(backend, policy=XmlPolicy())


def _assert_children[T](
  backend: XmlBackend,
  element: T,
  expected_count: int,
  tag_filter: Iterable[str | QNameLike] | QNameLike | None = None,
):
  children = list(backend.iter_children(element, tag_filter=tag_filter))
  assert len(children) == expected_count
  return children
