"""Unit tests for the per-node projection family in ``xml.parse``.

The golden corpus in ``conftest.py`` is the oracle: every field of every
model is asserted explicitly against a hand-written, attribute-complete
fragment. Message strings are asserted only where rendering is the
feature (the source-line prefixes of parse errors).
"""

from datetime import UTC, datetime

import pytest
from lxml import etree

from hypomnema.errors import TmxSpecError
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
  TranslationUnit,
  TranslationUnitVariant,
  Ude,
  Ut,
)
from hypomnema.xml.names import NON_ATTRIBUTE_FIELDS
from hypomnema.xml.parse import (
  bpt_from_element,
  ept_from_element,
  from_element,
  header_from_element,
  hi_from_element,
  it_from_element,
  map_from_element,
  note_from_element,
  ph_from_element,
  prop_from_element,
  sub_from_element,
  tu_from_element,
  tuv_from_element,
  ude_from_element,
  ut_from_element,
)

TAGS = ("bpt", "ept", "header", "hi", "it", "map", "note", "ph", "prop", "sub", "tu", "tuv", "ude", "ut")

FROM_FUNCTIONS = {
  "note": note_from_element,
  "prop": prop_from_element,
  "map": map_from_element,
  "ude": ude_from_element,
  "header": header_from_element,
  "tu": tu_from_element,
  "tuv": tuv_from_element,
  "bpt": bpt_from_element,
  "ept": ept_from_element,
  "it": it_from_element,
  "ph": ph_from_element,
  "hi": hi_from_element,
  "ut": ut_from_element,
  "sub": sub_from_element,
}

MODELS = {
  "note": Note,
  "prop": Property,
  "map": Map,
  "ude": Ude,
  "header": Header,
  "tu": TranslationUnit,
  "tuv": TranslationUnitVariant,
  "bpt": Bpt,
  "ept": Ept,
  "it": It,
  "ph": Ph,
  "hi": Hi,
  "ut": Ut,
  "sub": Sub,
}

# Every attribute field of every model, against the golden corpus:
# coerced values, defaults where the fragment omits the attribute. This
# table is the oracle that no field is silently dropped by the mapping.
EXPECTED_FIELDS = {
  "note": {"o_encoding": "utf-8", "xml_lang": "en", "lang": "en-GB"},
  "prop": {"type": "client", "xml_lang": "en", "o_encoding": "utf-8", "lang": "fr"},
  "map": {"unicode": 0xF8FF, "code": 0xF8FF, "ent": "&", "subst": "space"},
  "ude": {"name": "win", "base": "windows-1252"},
  "bpt": {"i": 1, "x": 2, "type": "bold"},
  "ept": {"i": 1},
  "it": {"pos": "begin", "x": 3, "type": "link"},
  "ph": {"x": 4, "assoc": "f", "type": "var"},
  "hi": {"x": 5, "type": "emph"},
  "ut": {"x": 6},
  "sub": {"datatype": "rtf", "type": "f"},
  "tuv": {
    "xml_lang": "en",
    "o_encoding": "utf-8",
    "datatype": "plaintext",
    "usagecount": 3,
    "lastusagedate": datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
    "creationtool": "tool",
    "creationtoolversion": "1.0",
    "creationdate": datetime(2024, 1, 1, tzinfo=UTC),
    "creationid": "creator",
    "changedate": datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
    "o_tmf": "tmf",
    "changeid": "changer",
    "lang": None,
  },
  "tu": {
    "tuid": "tu-1",
    "o_encoding": "utf-8",
    "datatype": "plaintext",
    "usagecount": 2,
    "lastusagedate": datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
    "creationtool": "tool",
    "creationtoolversion": "1.0",
    "creationdate": datetime(2024, 1, 1, tzinfo=UTC),
    "creationid": "c1",
    "changedate": datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
    "segtype": "paragraph",
    "changeid": "ch",
    "o_tmf": "tmf",
    "srclang": "en",
  },
  "header": {
    "creationtool": "tool",
    "creationtoolversion": "1.0",
    "segtype": "paragraph",
    "o_tmf": "tmf",
    "adminlang": "en",
    "srclang": "en",
    "datatype": "plaintext",
    "o_encoding": "utf-8",
    "creationdate": datetime(2024, 1, 1, tzinfo=UTC),
    "creationid": "c1",
    "changedate": datetime(2024, 6, 1, 12, 0, tzinfo=UTC),
    "changeid": "ch1",
  },
}


# Attribute mapping: every declared field of every node, coerced.


@pytest.mark.parametrize("tag", TAGS)
def test_from_element_maps_every_declared_field(tag, corpus):
  """The corpus sets or deliberately omits each attribute field; every
  value must land in the model, coerced to its native type."""
  model = FROM_FUNCTIONS[tag](etree.fromstring(corpus[tag]))
  for field, expected in EXPECTED_FIELDS[tag].items():
    assert getattr(model, field) == expected


def test_expected_fields_table_covers_every_attribute_field():
  """The oracle cannot silently drop a field: every attribute field of
  every model must appear in the table, so adding a model field without
  updating the corpus and the table fails here."""
  for tag in TAGS:
    model_type = MODELS[tag]
    attribute_fields = {name for name in model_type.model_fields if name not in NON_ATTRIBUTE_FIELDS}
    assert attribute_fields == set(EXPECTED_FIELDS[tag]), tag


EXPECTED_CONTENT = {
  "note": [("text", "a note")],
  "prop": [("text", "acme")],
  "map": [],
  "ude": [("maps", [Map(unicode=0xF8FF, code=0xF8FF, ent="&", subst="space")])],
  "bpt": [("content", ["<b>"])],
  "ept": [("content", ["</b>"])],
  "it": [("content", ["<a>"])],
  "ph": [("content", ["placeholder"])],
  "hi": [("content", ["emphasized ", Bpt(i=1, content=["x"]), Ept(i=1, content=["y"])])],
  "ut": [("content", ["{percent}"])],
  "sub": [("content", ["embedded"])],
  "tuv": [
    ("metadata", [Note(text="variant note")]),
    ("content", ["The ", Bpt(i=1, x=1, content=["{b"]), "black", Ept(i=1, content=["}"]), " cat"]),
  ],
  "tu": [
    ("metadata", [Property(type="client", text="acme")]),
    (
      "variants",
      [
        TranslationUnitVariant(
          xml_lang="en",
          content=["The ", Bpt(i=1, x=1, content=["{b"]), "black", Ept(i=1, content=["}"]), " cat"],
        ),
        TranslationUnitVariant(xml_lang="fr", content=["Le chat"]),
      ],
    ),
  ],
  "header": [
    (
      "metadata",
      [
        Note(text="header note"),
        Property(type="client", text="acme"),
        Ude(name="win", base="windows-1252", maps=[Map(unicode=0xF8FF, ent="&", subst="space")]),
      ],
    )
  ],
}


@pytest.mark.parametrize("tag", TAGS)
def test_from_element_projects_the_content_slots(tag, corpus):
  """The corpus's content slots are part of the oracle: text, mixed
  content, metadata, and maps all come through with their shapes."""
  model = FROM_FUNCTIONS[tag](etree.fromstring(corpus[tag]))
  for slot, expected in EXPECTED_CONTENT[tag]:
    assert getattr(model, slot) == expected


# Text and content shapes.


def test_note_text_distinguishes_none_and_empty():
  """XML cannot express an empty-string body: lxml normalizes
  ``<note></note>`` to the same None text as ``<note/>``, so the
  distinction exists only on the model side (build can still emit it)."""
  assert note_from_element(etree.fromstring("<note/>")).text is None
  assert note_from_element(etree.fromstring("<note></note>")).text is None


def test_note_text_whitespace_is_preserved():
  assert note_from_element(etree.fromstring("<note>  padded  </note>")).text == "  padded  "


def test_tu_metadata_and_variants_keep_document_order():
  """The DTD requires all metadata before the first variant; the split
  preserves the order within each group."""
  tu = tu_from_element(
    etree.fromstring(
      '<tu tuid="1" srclang="en">'
      '<note>first</note><prop type="client">second</prop><note>third</note>'
      '<tuv xml:lang="en"><seg>one</seg></tuv>'
      '<tuv xml:lang="fr"><seg>two</seg></tuv>'
      "</tu>"
    )
  )
  assert [type(node) for node in tu.metadata] == [Note, Property, Note]
  assert [node.text for node in tu.metadata] == ["first", "second", "third"]
  assert [variant.xml_lang for variant in tu.variants] == ["en", "fr"]


def test_tuv_metadata_comes_before_the_seg():
  tuv = tuv_from_element(etree.fromstring('<tuv xml:lang="en"><note>variant note</note><seg>content</seg></tuv>'))
  assert [note.text for note in tuv.metadata] == ["variant note"]
  assert tuv.content == ["content"]


def test_tuv_with_two_segs_is_reported():
  """The DTD rejects this first, but the projection must not crash on a
  planted double-<seg> fragment with an unpacking error."""
  with pytest.raises(TmxSpecError, match="expected exactly one <seg>, got 2"):
    tuv_from_element(etree.fromstring('<tuv xml:lang="en"><seg>a</seg><seg>b</seg></tuv>'))


@pytest.mark.parametrize(
  ("tag", "outer", "child_markup", "child_type"),
  [
    ("bpt", '<bpt i="1">before {child} after</bpt>', '<sub type="f">mid</sub>', Sub),
    ("ept", '<ept i="1">before {child} after</ept>', '<sub type="f">mid</sub>', Sub),
    ("it", '<it pos="begin">before {child} after</it>', '<sub type="f">mid</sub>', Sub),
    ("ph", '<ph x="4">before {child} after</ph>', '<sub type="f">mid</sub>', Sub),
    ("ut", '<ut x="6">before {child} after</ut>', '<sub type="f">mid</sub>', Sub),
    ("hi", "<hi>before {child} after</hi>", '<bpt i="1">mid</bpt>', Bpt),
    ("sub", "<sub>before {child} after</sub>", "<hi>mid</hi>", Hi),
  ],
)
def test_inline_content_interleaves_text_and_elements(tag, outer, child_markup, child_type):
  model = FROM_FUNCTIONS[tag](etree.fromstring(outer.format(child=child_markup)))
  assert isinstance(model, (Bpt, Ept, It, Ph, Hi, Ut, Sub))
  assert model.content[0] == "before "
  assert type(model.content[1]) is child_type
  assert model.content[2] == " after"


def test_ude_projects_its_maps():
  ude = ude_from_element(etree.fromstring(CORPUS_UDE))
  assert [mapping.unicode for mapping in ude.maps] == [0xF8FF]
  assert [mapping.ent for mapping in ude.maps] == ["&"]


# The gates: tag identity, DTD, names, no-model tags. Each per-node
# function gates its own fragment, so every one is tested standalone.


DTD_JUNK_FRAGMENTS = {
  "note": '<note junk="1" o-encoding="utf-8">x</note>',
  "prop": '<prop junk="1" type="client">x</prop>',
  "map": '<map junk="1" unicode="#x41"/>',
  "ude": '<ude junk="1" name="n"><map unicode="#x41"/></ude>',
  "bpt": '<bpt junk="1" i="1">x</bpt>',
  "ept": '<ept junk="1" i="1">x</ept>',
  "it": '<it junk="1" pos="begin">x</it>',
  "ph": '<ph junk="1" x="1">x</ph>',
  "hi": '<hi junk="1">x</hi>',
  "ut": '<ut junk="1" x="1">x</ut>',
  "sub": '<sub junk="1">x</sub>',
  "tuv": '<tuv junk="1" xml:lang="en"><seg>x</seg></tuv>',
  "tu": '<tu junk="1" srclang="en"><tuv xml:lang="en"><seg>x</seg></tuv></tu>',
  "header": '<header junk="1" creationtool="t" creationtoolversion="1" segtype="paragraph" o-tmf="x" adminlang="en" srclang="en" datatype="plain"/>',
}


@pytest.mark.parametrize("tag", TAGS)
def test_dtd_gate_rejects_unknown_attributes(tag):
  """Each fragment is DTD-valid except for the junk attribute, so the
  attribute gate itself is what fails, not the child pattern."""
  with pytest.raises(TmxSpecError):
    FROM_FUNCTIONS[tag](etree.fromstring(DTD_JUNK_FRAGMENTS[tag]))


@pytest.mark.parametrize(
  ("function", "broken"),
  [
    # Header: creationtool is #REQUIRED.
    (
      header_from_element,
      '<header creationtoolversion="1.0" segtype="paragraph" o-tmf="tmf" adminlang="en" srclang="en" datatype="plaintext"/>',
    ),
    # tuv: xml:lang is #REQUIRED.
    (tuv_from_element, '<tuv o-encoding="utf-8"><seg>x</seg></tuv>'),
    # map: unicode is #REQUIRED.
    (map_from_element, '<map code="#xF8FF"/>'),
    # bpt/ept: i is #REQUIRED.
    (bpt_from_element, '<bpt x="2">x</bpt>'),
    (ept_from_element, "<ept>x</ept>"),
    # it: pos is #REQUIRED.
    (it_from_element, '<it x="3">x</it>'),
  ],
)
def test_dtd_gate_rejects_missing_required_attributes(function, broken):
  with pytest.raises(TmxSpecError):
    function(etree.fromstring(broken))


def test_tu_without_srclang_passes_the_dtd_but_not_the_entry_boundary():
  """The DTD declares srclang #IMPLIED on <tu>, but the model requires
  it: the entry boundary is stricter than the DTD, and a DTD-valid
  fragment still fails coercion, with the line attached."""
  with pytest.raises(TmxSpecError) as excinfo:
    tu_from_element(etree.fromstring('<tu tuid="1"><tuv xml:lang="en"><seg>x</seg></tuv></tu>'))
  assert "at line 1" in str(excinfo.value)


@pytest.mark.parametrize(
  ("function", "tag", "other_tag"),
  [
    (note_from_element, "note", "prop"),
    (prop_from_element, "prop", "note"),
    (tu_from_element, "tu", "tuv"),
    (tuv_from_element, "tuv", "tu"),
    (ude_from_element, "ude", "header"),
    (header_from_element, "header", "tu"),
    (map_from_element, "map", "note"),
    (bpt_from_element, "bpt", "ept"),
    (ept_from_element, "ept", "bpt"),
    (it_from_element, "it", "ph"),
    (ph_from_element, "ph", "it"),
    (hi_from_element, "hi", "ut"),
    (ut_from_element, "ut", "hi"),
    (sub_from_element, "sub", "bpt"),
  ],
)
def test_foreign_tags_are_rejected_by_tag_identity(function, tag, other_tag, corpus):
  """A <prop> is a valid TMX fragment but not a <note>: each per-node
  function projects exactly its own element."""
  with pytest.raises(TmxSpecError) as excinfo:
    function(etree.fromstring(corpus[other_tag]))
  assert f"expected <{tag}>, got <{other_tag}>" in str(excinfo.value)


def test_tuv_without_a_seg_is_reported_standalone():
  """The projection must not crash with an unpacking error on a
  fragment the DTD would reject: the <tuv> owns its shape."""
  with pytest.raises(TmxSpecError, match="expected exactly one <seg>, got 0"):
    tuv_from_element(etree.fromstring('<tuv xml:lang="en"><note>x</note></tuv>'))


def test_namespaced_elements_are_rejected():
  with pytest.raises(TmxSpecError, match="namespace-free"):
    from_element(etree.fromstring('<tmx:tu xmlns:tmx="urn:x" tuid="1" srclang="en"/>'))
  with pytest.raises(TmxSpecError, match="namespace-free"):
    note_from_element(etree.fromstring('<note xmlns="urn:x">x</note>'))


def test_comment_and_pi_tags_are_rejected():
  with pytest.raises(TmxSpecError, match="namespace-free"):
    note_from_element(etree.Comment("junk"))
  with pytest.raises(TmxSpecError, match="namespace-free"):
    note_from_element(etree.ProcessingInstruction("junk"))


@pytest.mark.parametrize("tag", ["seg", "tmx", "body"])
def test_modelless_tags_are_rejected(tag):
  """These are TMX elements without a standalone domain model."""
  with pytest.raises(TmxSpecError, match="no standalone domain model"):
    from_element(etree.fromstring(f"<{tag}/>"))


@pytest.mark.parametrize("tag", ["thing", "TUV"])
def test_unknown_tags_are_rejected(tag):
  with pytest.raises(TmxSpecError, match="is not a TMX 1.4b element"):
    from_element(etree.fromstring(f"<{tag}/>"))


def test_coercion_gate_reports_the_source_line():
  with pytest.raises(TmxSpecError) as excinfo:
    header_from_element(
      etree.fromstring(
        '<header creationtool="tool" creationtoolversion="1.0" segtype="paragraph"'
        ' o-tmf="tmf" adminlang="en" srclang="en" datatype="plaintext"'
        ' creationdate="nonsense"/>'
      )
    )
  assert "at line 1" in str(excinfo.value)


def test_coercion_gate_surfaces_the_field():
  with pytest.raises(TmxSpecError) as excinfo:
    map_from_element(etree.fromstring('<map unicode="junk"/>'))
  assert "unicode" in str(excinfo.value)


# The generic dispatcher: every arm routes to the right model.


@pytest.mark.parametrize("tag", TAGS)
def test_from_element_dispatches_every_tag(tag, corpus):
  model = from_element(etree.fromstring(corpus[tag]))
  assert type(model) is MODELS[tag]


CORPUS_UDE = '<ude name="win" base="windows-1252"><map unicode="#xF8FF" ent="&amp;" subst="space"/></ude>'


# Ordering and reach of the eager projection arguments: field arguments
# are computed before _project's gates, so some failures surface from a
# child's gate first. The order is pinned here as deliberate.


def test_text_gate_runs_before_the_dtd_gate():
  with pytest.raises(TmxSpecError, match="expected text only"):
    note_from_element(etree.fromstring("<note><b>x</b></note>"))


def test_child_dispatch_runs_before_the_parent_dtd_gate():
  with pytest.raises(TmxSpecError, match="is not a TMX 1.4b element"):
    header_from_element(
      etree.fromstring(
        '<header creationtool="t" creationtoolversion="1" segtype="paragraph"'
        ' o-tmf="x" adminlang="en" srclang="en" datatype="plain"><junk/></header>'
      )
    )


def test_non_root_fragment_is_gated_standalone():
  """A fragment nested in a larger document is DTD-gated on its own
  deepcopy, not against its parents."""
  document = etree.fromstring('<tu tuid="1" srclang="en"><note>hi</note><tuv xml:lang="en"><seg>x</seg></tuv></tu>')
  note_element = document.find("note")
  assert note_element is not None
  assert note_from_element(note_element).text == "hi"


def test_unresolved_entity_in_content_is_reported():
  parser = etree.XMLParser(resolve_entities=False)
  element = etree.fromstring('<!DOCTYPE note [<!ENTITY e "text">]><note>&e;</note>', parser)
  with pytest.raises(TmxSpecError, match="unresolved entity"):
    note_from_element(element)
