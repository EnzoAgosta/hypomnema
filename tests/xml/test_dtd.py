"""Unit tests for the package DTD gate."""

import pytest
from lxml import etree

from hypomnema.errors import TmxSpecError
from hypomnema.xml.dtd import load_dtd, validate_fragment

TAGS = ("bpt", "ept", "header", "hi", "it", "map", "note", "ph", "prop", "sub", "tu", "tuv", "ude", "ut")


def test_load_dtd_is_cached():
  """One parsed DTD serves every fragment."""
  assert load_dtd() is load_dtd()


@pytest.mark.parametrize("tag", TAGS)
def test_validate_fragment_accepts_every_corpus_fragment(tag, corpus):
  validate_fragment(etree.fromstring(corpus[tag]))


def test_validate_fragment_rejects_missing_required_attributes():
  with pytest.raises(TmxSpecError) as excinfo:
    validate_fragment(
      etree.fromstring(
        '<header creationtoolversion="1.0" segtype="paragraph" o-tmf="tmf"'
        ' adminlang="en" srclang="en" datatype="plaintext"/>'
      )
    )
  assert "at line 1" in str(excinfo.value)


def test_validate_fragment_rejects_unknown_elements():
  with pytest.raises(TmxSpecError):
    validate_fragment(etree.fromstring("<thing/>"))


def test_validate_fragment_rejects_unknown_attributes():
  with pytest.raises(TmxSpecError):
    validate_fragment(etree.fromstring('<note junk="1">x</note>'))


def test_validate_fragment_rejects_broken_child_patterns():
  """The DTD's ((note|prop)*, tuv+) ordering: metadata after a variant
  is invalid even though every child is legal."""
  with pytest.raises(TmxSpecError):
    validate_fragment(
      etree.fromstring('<tu tuid="1" srclang="en"><tuv xml:lang="en"><seg>x</seg></tuv><note>late</note></tu>')
    )


def test_validate_fragment_rejects_text_in_empty_elements():
  with pytest.raises(TmxSpecError):
    validate_fragment(etree.fromstring('<map unicode="#x41">text</map>'))


def test_non_root_fragment_is_validated_on_its_own_copy():
  """A fragment nested in a larger document is validated standalone --
  the deepcopy branch: lxml's synthetic document would introduce an
  ``xmlns:xml`` declaration the DTD rejects. The fragment's tail in its
  parent is validation's business only."""
  document = etree.fromstring(
    '<tu tuid="1" srclang="en"><note>x</note>tail in parent<tuv xml:lang="en"><seg>y</seg></tuv></tu>'
  )
  note_element = document.find("note")
  assert note_element is not None
  note_element.tail = "belongs to the parent"
  validate_fragment(note_element)
  tuv_element = document.find("tuv")
  assert tuv_element is not None
  # The tuv carries xml:lang: serialized standalone, lxml would emit an
  # xmlns:xml declaration; the copy keeps the gate honest either way.
  validate_fragment(tuv_element)
