"""Shared construction scaffolding; XML/model expectations stay in the tests."""

from collections.abc import Callable

import pytest

from hypomnema.models import (
  Bpt,
  Ept,
  Header,
  Hi,
  It,
  Map,
  Note,
  Ph,
  Property,
  Sub,
  TmxNode,
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)


@pytest.fixture
def minimal_header() -> Header:
  return Header(
    creationtool="ct",
    creationtoolversion="1",
    segtype="sentence",
    o_tmf="g",
    adminlang="en",
    srclang="en",
    datatype="txt",
  )


@pytest.fixture(
  params=[
    pytest.param(Note, id="note"),
    pytest.param(Property, id="prop"),
    pytest.param(Map, id="map"),
    pytest.param(Ude, id="ude"),
    pytest.param(Bpt, id="bpt"),
    pytest.param(Ept, id="ept"),
    pytest.param(It, id="it"),
    pytest.param(Ph, id="ph"),
    pytest.param(Hi, id="hi"),
    pytest.param(Ut, id="ut"),
    pytest.param(Sub, id="sub"),
    pytest.param(Header, id="header"),
    pytest.param(TranslationUnit, id="tu"),
    pytest.param(TranslationUnitVariant, id="tuv"),
  ]
)
def minimal_node(request: pytest.FixtureRequest, minimal_header: Header) -> TmxNode:
  """A fresh node with required attributes/children only, and no text."""
  model_type: type[TmxNode] = request.param
  factories: dict[type[TmxNode], Callable[[], TmxNode]] = {
    Note: Note,
    Property: lambda: Property(type="p"),
    Map: lambda: Map(unicode=0xE9),
    Ude: lambda: Ude(name="u", maps=(Map(unicode=0xE9),)),
    Bpt: lambda: Bpt(i=1),
    Ept: lambda: Ept(i=1),
    It: lambda: It(pos="begin"),
    Ph: Ph,
    Hi: Hi,
    Ut: Ut,
    Sub: Sub,
    Header: lambda: minimal_header,
    TranslationUnit: lambda: TranslationUnit(variants=(TranslationUnitVariant(xml_lang="en"),)),
    TranslationUnitVariant: lambda: TranslationUnitVariant(xml_lang="en"),
  }
  return factories[model_type]()


@pytest.fixture
def valid_tmx_document() -> str:
  """Handwritten input for document-level DTD and wrapper-boundary checks."""
  return (
    '<tmx version="1.4">'
    '<header creationtool="t" creationtoolversion="1" segtype="phrase" o-tmf="ascii"'
    ' adminlang="en" srclang="en" datatype="txt"/>'
    '<body><tu><tuv xml:lang="en"><seg>hello</seg></tuv></tu></body>'
    "</tmx>"
  )
