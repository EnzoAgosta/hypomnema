"""Tests for DTD loading and fragment validation (src/hypomnema/xml/dtd.py).

``validate_fragment`` checks one element subtree against the packaged TMX
1.4b DTD. The validated scope is the fragment alone: its parent, siblings,
and tail are out of scope, and the original tree is never touched.
"""

import pathlib
import subprocess
import sys

import pytest
from lxml import etree

from hypomnema.errors import TmxSpecError
from hypomnema.xml.dtd import load_dtd, validate_fragment


def test_dtd_loads_and_validates_regardless_of_working_directory(
  tmp_path: pathlib.Path, valid_tmx_document: str
) -> None:
  # A fresh interpreter guarantees a cold resource load without coupling this
  # test to the loader's caching implementation or the suite's execution order.
  result = subprocess.run(
    [
      sys.executable,
      "-c",
      "from lxml import etree; from hypomnema.xml.dtd import validate_fragment; "
      f"validate_fragment(etree.fromstring({valid_tmx_document!r}))",
    ],
    cwd=tmp_path,
    capture_output=True,
    text=True,
  )
  assert result.returncode == 0, result.stderr


# --- whole-document (root) validation ---------------------------------------


def test_a_conforming_document_validates(valid_tmx_document: str) -> None:
  validate_fragment(etree.fromstring(valid_tmx_document))


def test_a_nonconforming_document_is_rejected_with_element_and_line() -> None:
  document = etree.fromstring(
    "<tmx version='1.4'>"
    "<header creationtool='t' creationtoolversion='1' segtype='phrase' o-tmf='ascii'"
    " adminlang='en' srclang='en'/>"  # datatype missing
    "<body/>"
    "</tmx>"
  )
  with pytest.raises(TmxSpecError, match="<tmx> at line 1"):
    validate_fragment(document)


# --- attached fragment validation -------------------------------------------


def test_attached_fragment_with_xml_lang_validates() -> None:
  # Regression guard: xml:lang on a non-root fragment must not trip over a
  # synthetic xmlns:xml declaration; the fragment is validated as its own tree.
  body = etree.fromstring("<body><tu><tuv xml:lang='en'><seg>hi</seg></tuv></tu></body>")
  validate_fragment(body[0])


def test_fragment_with_inline_content_validates() -> None:
  body = etree.fromstring("<body><tu><tuv xml:lang='en'><seg>a<bpt i='1'/>b</seg></tuv></tu></body>")
  validate_fragment(body[0][0][0])


# --- EMPTY content: <map> ---------------------------------------------------


@pytest.mark.parametrize("xml", ["<map unicode='#x41'/>", "<map unicode='#x41' code='#x0041' ent='A' subst='A'/>"])
def test_map_with_empty_content_validates(xml: str) -> None:
  validate_fragment(etree.fromstring(xml))


def test_map_inside_its_ude_context_validates() -> None:
  # The base-required-with-code rule belongs to explicit domain validation
  # (validate_ude, tested in test_validation.py), not the DTD.
  validate_fragment(etree.fromstring("<ude name='custom'><map unicode='#x41' code='#x0041'/></ude>"))


@pytest.mark.parametrize(
  "xml",
  ["<map unicode='#x41'>junk</map>", "<map unicode='#x41'> </map>", "<map unicode='#x41'>\n\t</map>", "<map/>"],
  ids=["text", "space", "line-break-and-tab", "missing-unicode"],
)
def test_nonconforming_map_is_rejected(xml: str) -> None:
  with pytest.raises(TmxSpecError, match="map") as excinfo:
    validate_fragment(etree.fromstring(xml))
  assert isinstance(excinfo.value.__cause__, etree.DocumentInvalid)


# --- rejection of invalid fragments -----------------------------------------


@pytest.mark.parametrize(
  "xml, tag, fragment_line, offending_line",
  [
    ("<body>\n  <tu>\n    <tuv>\n      <seg>x</seg>\n    </tuv>\n  </tu>\n</body>", "tuv", 3, 3),
    ('<tuv xml:lang="en">\n  <seg>\n    text\n    <bogus/>\n  </seg>\n</tuv>', "seg", 2, 4),
  ],
  ids=["missing-required-attribute", "undeclared-descendant"],
)
def test_invalid_fragment_names_the_element_and_line(
  xml: str, tag: str, fragment_line: int, offending_line: int
) -> None:
  document = etree.fromstring(xml)
  fragment = document.find(f".//{tag}")
  assert fragment is not None
  with pytest.raises(TmxSpecError, match=f"<{tag}> at line {fragment_line}:") as excinfo:
    validate_fragment(fragment)
  cause = excinfo.value.__cause__
  assert isinstance(cause, etree.DocumentInvalid)
  assert any(entry.line == offending_line for entry in cause.error_log)


# --- validation scope excludes the surrounding tree --------------------------


def test_validation_ignores_an_invalid_parent_and_sibling() -> None:
  # <evil>, <alsobad> are undeclared and the <tu> content model is violated;
  # none of that may fail the valid <tuv> inside.
  body = etree.fromstring("<body><tu><evil/><tuv xml:lang='en'><seg>x</seg></tuv></tu><alsobad/></body>")
  validate_fragment(body[0][1])


def test_validation_ignores_the_fragment_tail() -> None:
  # 'stray' is tail text of the validated <tuv>; body's (tu*) model forbids
  # text, so including the tail would fail a whole-tree check.
  body = etree.fromstring(
    "<body><tu><tuv xml:lang='en'><seg>x</seg></tuv></tu><tuv xml:lang='fr'><seg>y</seg></tuv>stray</body>"
  )
  validate_fragment(body[1])


# --- input nonmutation -------------------------------------------------------


def test_validation_does_not_mutate_a_valid_fragment() -> None:
  # The trailing <tu/> is an invalid sibling, excluded from the check.
  body = etree.fromstring("<body><tu><note>n</note><tuv xml:lang='en'><seg>a<bpt i='1'/>b</seg></tuv></tu><tu/></body>")
  snapshot = etree.tostring(body)
  validate_fragment(body[0][1])
  assert etree.tostring(body) == snapshot


def test_validation_does_not_mutate_an_invalid_fragment() -> None:
  body = etree.fromstring("<body><tu><tuv><seg>x</seg></tuv></tu></body>")
  snapshot = etree.tostring(body)
  with pytest.raises(TmxSpecError):
    validate_fragment(body[0][0])
  assert etree.tostring(body) == snapshot


def test_load_dtd_returns_a_dtd_bound_to_the_tmx_vocabulary() -> None:
  # Behavioral sanity check on the loaded resource, not its cache identity.
  dtd = load_dtd()
  declarations = {declaration.name: declaration for declaration in dtd.iterelements()}
  assert declarations["map"].type == "empty"
  assert {attribute.name for attribute in declarations["map"].iterattributes()} == {"unicode", "code", "ent", "subst"}
