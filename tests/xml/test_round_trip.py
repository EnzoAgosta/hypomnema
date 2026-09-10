"""Round-trip property for the two projection directions.

For every corpus fragment: parse, build, reparse -- the model must come
back equal. This is the test that catches parse/build asymmetry (the two
walkers disagreeing) and any drift between the XML shapes and the models.
"""

from typing import cast

import pytest
from lxml import etree

from hypomnema.models import Bpt, Hi, It, Map, Note, Sub, TranslationUnit, TranslationUnitVariant
from hypomnema.xml.build import to_element
from hypomnema.xml.parse import from_element

TAGS = ("bpt", "ept", "header", "hi", "it", "map", "note", "ph", "prop", "sub", "tu", "tuv", "ude", "ut")


@pytest.mark.parametrize("tag", TAGS)
def test_corpus_round_trips_to_an_equal_model(tag, corpus):
  model = from_element(etree.fromstring(corpus[tag]))
  assert from_element(to_element(model)) == model


def test_empty_string_note_text_round_trip():
  """The empty-string note text survives an in-memory element round
  trip (to_element keeps ``text=""`` on the element, and the object
  round trip preserves it); only through actual XML text does the
  distinction collapse, because XML cannot express an empty-string
  body."""
  note = Note(text="")
  rebuilt = cast(Note, from_element(to_element(note)))
  assert rebuilt.text == ""
  xml = etree.tostring(to_element(note)).decode()
  assert xml == "<note></note>"
  assert cast(Note, from_element(etree.fromstring(xml))).text is None


def test_minimal_models_round_trip_to_an_equal_model():
  """Self-closing shapes and empty slots: the None-omission and
  empty-content build paths, end to end."""
  for model in (
    Note(),
    Bpt(i=1),
    Map(unicode=0x41),
    It(pos="begin"),
    TranslationUnitVariant(xml_lang="en"),
  ):
    assert from_element(to_element(model)) == model


def test_full_unit_round_trips_with_nested_content():
  """One integration unit: metadata, paired inline codes with an
  embedded ``<sub>`` holding transparent ``<hi>``/``<ph>``, a second
  variant, and the writer gate's full validation on the way out."""
  XML = (
    '<tu tuid="1" srclang="en">'
    "<note>unit note</note>"
    '<tuv xml:lang="en">'
    '<seg>before <bpt i="1" x="1">&lt;b&gt;<sub type="f">embedded <hi>high</hi></sub></bpt>'
    ' mid <ept i="1">&lt;/b&gt;</ept> <hi>plain <ph x="2">standalone</ph></hi> after</seg>'
    "</tuv>"
    '<tuv xml:lang="fr"><seg>Le chat</seg></tuv>'
    "</tu>"
  )
  tu = from_element(etree.fromstring(XML))
  rebuilt = cast(TranslationUnit, from_element(to_element(tu)))
  assert rebuilt == tu
  bpt = rebuilt.variants[0].content[1]
  assert isinstance(bpt, Bpt)
  embedded = bpt.content[1]
  assert isinstance(embedded, Sub)
  assert embedded.content[0] == "embedded "
  high = embedded.content[1]
  assert isinstance(high, Hi)
  assert high.content == ["high"]
