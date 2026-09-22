"""Shared golden corpus for the xml projection tests.

One attribute-complete, valid fragment per node kind, written by hand:
an independent oracle for both projection directions. Attribute order
matches the models' field declaration order, so a rebuilt element
serializes verbatim -- the build-side tests lean on that.
"""

import pytest

CORPUS: dict[str, str] = {
  "note": '<note o-encoding="utf-8" xml:lang="en" lang="en-GB">a note</note>',
  "prop": '<prop type="client" xml:lang="en" o-encoding="utf-8" lang="fr">acme</prop>',
  "map": '<map unicode="#xF8FF" code="#xF8FF" ent="&amp;" subst="space"/>',
  "ude": '<ude name="win" base="windows-1252"><map unicode="#xF8FF" code="#xF8FF" ent="&amp;" subst="space"/></ude>',
  "bpt": '<bpt i="1" x="2" type="bold">&lt;b&gt;</bpt>',
  "ept": '<ept i="1">&lt;/b&gt;</ept>',
  "it": '<it pos="begin" x="3" type="link">&lt;a&gt;</it>',
  "ph": '<ph x="4" assoc="f" type="var">placeholder</ph>',
  "hi": '<hi x="5" type="emph">emphasized <bpt i="1">x</bpt><ept i="1">y</ept></hi>',
  "ut": '<ut x="6">{percent}</ut>',
  "sub": '<sub datatype="rtf" type="f">embedded</sub>',
  "tuv": '<tuv xml:lang="en" o-encoding="utf-8" datatype="plaintext" usagecount="3" lastusagedate="20240601T120000Z" creationtool="tool" creationtoolversion="1.0" creationdate="20240101T000000Z" creationid="creator" changedate="20240601T120000Z" o-tmf="tmf" changeid="changer"><note>variant note</note><seg>The <bpt i="1" x="1">{b</bpt>black<ept i="1">}</ept> cat</seg></tuv>',
  "tu": '<tu tuid="tu-1" o-encoding="utf-8" datatype="plaintext" usagecount="2" lastusagedate="20240601T120000Z" creationtool="tool" creationtoolversion="1.0" creationdate="20240101T000000Z" creationid="c1" changedate="20240601T120000Z" segtype="paragraph" changeid="ch" o-tmf="tmf" srclang="en"><prop type="client">acme</prop><tuv xml:lang="en"><seg>The <bpt i="1" x="1">{b</bpt>black<ept i="1">}</ept> cat</seg></tuv><tuv xml:lang="fr"><seg>Le chat</seg></tuv></tu>',
  "header": '<header creationtool="tool" creationtoolversion="1.0" segtype="paragraph" o-tmf="tmf" adminlang="en" srclang="en" datatype="plaintext" o-encoding="utf-8" creationdate="20240101T000000Z" creationid="c1" changedate="20240601T120000Z" changeid="ch1"><note>header note</note><prop type="client">acme</prop><ude name="win" base="windows-1252"><map unicode="#xF8FF" ent="&amp;" subst="space"/></ude></header>',
}

TAGS = tuple(sorted(CORPUS))


@pytest.fixture
def corpus() -> dict[str, str]:
  """Return the shared fragment dictionary for projection tests."""
  return CORPUS
