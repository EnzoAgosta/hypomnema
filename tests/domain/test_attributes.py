from hypomnema.domain.attributes import _verify_encoding, _verify_language_code


def test_verify_encoding_accepts_known_codec() -> None:
  assert _verify_encoding("utf-8") == "utf-8"


def test_verify_encoding_rejects_unknown_codec() -> None:
  try:
    _verify_encoding("definitely-not-a-real-codec")
  except LookupError:
    pass
  else:
    raise AssertionError("Expected LookupError for an unknown codec")


def test_verify_language_code_currently_returns_input_unchanged() -> None:
  assert _verify_language_code("not-validated-yet") == "not-validated-yet"
