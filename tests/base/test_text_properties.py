from hypomnema.api.helpers import (
  create_bpt,
  create_ept,
  create_sub,
  create_tuv,
  create_hi,
  iter_text,
)
from hypomnema.base.types import Bpt, Sub


def test_text_property_simple():
  """Test .text property on a simple string element."""
  tuv = create_tuv("en", content="Hello world")
  assert tuv.text == "Hello world"


def test_text_property_mixed_content():
  """Test .text property with mixed content (text + inline elements)."""
  tuv = create_tuv("en", content=["Click ", create_hi(content="here"), " to start."])
  assert tuv.text == "Click  to start."


def test_iter_text_simple():
  """Test .text property with sub-flows and no recurse."""
  tuv = create_bpt(i=1, content=["Click ", create_sub(content=["here"]), " to start."])
  assert list(iter_text(tuv)) == ["Click ", "here", " to start."]


def test_iter_text_ignore():
  """Test iter_text can dive into sub-flows and code containers."""
  tuv = create_bpt(i=1, content=["Click ", create_sub(content=["here"]), " to start."])
  assert list(iter_text(tuv, ignore=[Sub])) == ["Click ", " to start."]


def test_iter_text_recurse_deeply_nested():
  """Test iter_text can dive into sub-flows and code containers."""
  tuv = create_tuv(
    "en",
    content=[
      "Outer Tuv string",
      create_hi(
        content=[
          "Inner Hi string",
          create_bpt(
            i=1,
            content=[
              "Inner Hi Inner Bpt string",
              create_sub(content="Inner Hi Inner Bpt Inner Sub string"),
              "Inner Hi Inner Bpt Second string",
            ],
          ),
          "Inner Hi Second string",
          create_ept(i=1, content="Inner Hi Ept string"),
        ]
      ),
      "Outer Tuv Second string",
    ],
  )
  assert list(iter_text(tuv, ignore=[Bpt, Sub])) == [
    "Outer Tuv string",
    "Inner Hi string",
    "Inner Hi Second string",
    "Inner Hi Ept string",
    "Outer Tuv Second string",
  ]
