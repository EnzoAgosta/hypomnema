from hypothesis import strategies as st

from hypomnema.base.types import (
  Assoc,
  Bpt,
  Ept,
  Header,
  Hi,
  It,
  Note,
  Ph,
  Pos,
  Prop,
  Segtype,
  Tmx,
  Tu,
  Tuv,
)


def alternating_types(elements):
  last_type = None

  def not_same_type(x):
    nonlocal last_type
    t = type(x)
    if t == last_type:
      return None
    last_type = t
    return id(t)

  return st.lists(elements, min_size=2, max_size=5, unique_by=not_same_type)


def _inline_text():
  return st.text(
    st.characters(exclude_categories=["Cc", "Co", "Cf", "Cs", "Zp", "Zs", "Zl"]),
    min_size=5,
    max_size=25,
  )


def _any_inline():
  return st.one_of(
    st.builds(
      Ph,
      x=st.integers(),
      content=st.lists(_inline_text(), min_size=1, max_size=1),
      assoc=st.sampled_from(Assoc),
      type=_inline_text(),
    ),
    st.builds(
      It,
      pos=st.sampled_from(Pos),
      content=st.lists(_inline_text(), min_size=1, max_size=1),
      type=_inline_text(),
    ),
    st.builds(
      Bpt,
      i=st.integers(),
      x=st.integers(),
      type=_inline_text(),
      content=st.lists(_inline_text(), min_size=1, max_size=1),
    ),
    st.builds(Ept, i=st.integers(), content=st.lists(_inline_text(), min_size=1, max_size=1)),
    st.builds(
      Hi,
      x=st.integers(),
      type=_inline_text(),
      content=st.lists(_inline_text(), min_size=1, max_size=1),
    ),
  )


def notes():
  return st.lists(
    st.builds(Note, text=_inline_text(), lang=_inline_text(), o_encoding=_inline_text()), max_size=2
  )


def props():
  return st.lists(
    st.builds(
      Prop, text=_inline_text(), type=_inline_text(), lang=_inline_text(), o_encoding=_inline_text()
    ),
    max_size=2,
  )


def header():
  return st.builds(
    Header,
    creationtool=_inline_text(),
    creationtoolversion=_inline_text(),
    segtype=st.sampled_from(Segtype),
    o_tmf=_inline_text(),
    adminlang=_inline_text(),
    srclang=_inline_text(),
    datatype=_inline_text(),
    creationdate=st.datetimes(),
    creationid=_inline_text(),
    changedate=st.datetimes(),
    changeid=_inline_text(),
    notes=notes(),
    props=props(),
  )


def tuv():
  return st.builds(
    Tuv,
    lang=_inline_text(),
    o_encoding=_inline_text(),
    datatype=_inline_text(),
    usagecount=st.integers(),
    lastusagedate=st.datetimes(),
    creationtool=_inline_text(),
    creationtoolversion=_inline_text(),
    creationdate=st.datetimes(),
    creationid=_inline_text(),
    changedate=st.datetimes(),
    changeid=_inline_text(),
    o_tmf=_inline_text(),
    props=props(),
    notes=notes(),
    content=alternating_types(st.one_of(_any_inline(), _inline_text())),
  )


def tu():
  return st.builds(
    Tu,
    tuid=_inline_text(),
    o_encoding=_inline_text(),
    datatype=_inline_text(),
    usagecount=st.integers(),
    lastusagedate=st.datetimes(),
    creationtool=_inline_text(),
    creationtoolversion=_inline_text(),
    creationdate=st.datetimes(),
    creationid=_inline_text(),
    changedate=st.datetimes(),
    segtype=st.sampled_from(Segtype),
    changeid=_inline_text(),
    o_tmf=_inline_text(),
    srclang=_inline_text(),
    props=props(),
    notes=notes(),
    variants=st.lists(tuv(), min_size=1, max_size=2),
  )


def tmx():
  return st.builds(Tmx, header=header(), body=st.lists(tu(), min_size=1, max_size=10))
