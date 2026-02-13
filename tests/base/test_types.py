"""Tests for base types, specifically TextMixin.text property."""

from hypomnema.base.types import Bpt, Ept, Hi, It, Ph, Sub, Tuv


class TestTextMixin:
  """Tests for the TextMixin.text property."""

  def test_text_with_only_strings(self) -> None:
    tuv = Tuv(lang="en", content=["Hello", " ", "World"])
    assert tuv.text == "Hello World"

  def test_text_with_mixed_content(self) -> None:
    tuv = Tuv(lang="en", content=["Hello ", Bpt(i=1, content=["code"]), " World"])
    assert tuv.text == "Hello  World"

  def test_text_with_nested_inline_elements(self) -> None:
    tuv = Tuv(
      lang="en",
      content=["Start ", Bpt(i=1, content=["code ", Sub(content=["subflow"]), " tail"]), " End"],
    )
    assert tuv.text == "Start  End"

  def test_text_empty_content(self) -> None:
    tuv = Tuv(lang="en", content=[])
    assert tuv.text == ""

  def test_text_with_only_inline_elements(self) -> None:
    tuv = Tuv(lang="en", content=[Bpt(i=1, content=[]), Ept(i=1, content=[])])
    assert tuv.text == ""

  def test_text_with_hi_element(self) -> None:
    tuv = Tuv(lang="en", content=["Hello ", Hi(content=["highlighted"]), " World"])
    assert tuv.text == "Hello  World"

  def test_text_with_it_element(self) -> None:
    from hypomnema.base.types import Pos

    tuv = Tuv(lang="en", content=["Start ", It(pos=Pos.BEGIN, content=[]), " End"])
    assert tuv.text == "Start  End"

  def test_text_with_ph_element(self) -> None:
    tuv = Tuv(lang="en", content=["Hello ", Ph(content=["placeholder"]), " World"])
    assert tuv.text == "Hello  World"

  def test_text_on_bpt(self) -> None:
    bpt = Bpt(i=1, content=["before ", Sub(content=["sub"]), " after"])
    assert bpt.text == "before  after"

  def test_text_on_ept(self) -> None:
    ept = Ept(i=1, content=["code data"])
    assert ept.text == "code data"

  def test_text_on_hi(self) -> None:
    hi = Hi(content=["text ", Bpt(i=1, content=[]), " more"])
    assert hi.text == "text  more"

  def test_text_on_sub(self) -> None:
    sub = Sub(content=["subflow text ", Bpt(i=1, content=[]), " more"])
    assert sub.text == "subflow text  more"
