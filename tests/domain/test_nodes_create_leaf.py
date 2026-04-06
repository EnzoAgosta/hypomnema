from hypomnema.domain.nodes import Note, Prop, UnknownNode


def test_note_create_sets_text() -> None:
  assert Note.create(text="note text").text == "note text"


def test_note_create_sets_language() -> None:
  assert Note.create(text="note text", language="en-US").spec_attributes.language == "en-US"


def test_note_create_sets_original_encoding() -> None:
  assert (
    Note.create(text="note text", original_encoding="utf-8").spec_attributes.original_encoding
    == "utf-8"
  )


def test_note_create_copies_extra_attributes() -> None:
  extra_attributes = {"custom": object()}

  note = Note.create(text="note text", extra_attributes=extra_attributes)

  assert note.extra_attributes == extra_attributes
  assert note.extra_attributes is not extra_attributes


def test_note_create_copies_extra_nodes() -> None:
  extra_nodes = [UnknownNode(payload=b"<custom />")]

  note = Note.create(text="note text", extra_nodes=extra_nodes)

  assert note.extra_nodes == extra_nodes
  assert note.extra_nodes is not extra_nodes


def test_note_create_defaults_empty_extra_attributes() -> None:
  assert Note.create(text="note text").extra_attributes == {}


def test_note_create_defaults_empty_extra_nodes() -> None:
  assert Note.create(text="note text").extra_nodes == []


def test_note_create_rejects_invalid_encoding() -> None:
  try:
    Note.create(text="note text", original_encoding="not-a-real-codec")
  except LookupError:
    pass
  else:
    raise AssertionError("Expected LookupError for an invalid encoding")


def test_prop_create_sets_text() -> None:
  assert Prop.create(text="prop text", kind="domain").text == "prop text"


def test_prop_create_sets_kind() -> None:
  assert Prop.create(text="prop text", kind="domain").spec_attributes.kind == "domain"


def test_prop_create_sets_language() -> None:
  assert (
    Prop.create(text="prop text", kind="domain", language="fr").spec_attributes.language == "fr"
  )


def test_prop_create_sets_original_encoding() -> None:
  assert (
    Prop.create(
      text="prop text", kind="domain", original_encoding="latin-1"
    ).spec_attributes.original_encoding
    == "latin-1"
  )


def test_prop_create_copies_extra_attributes() -> None:
  extra_attributes = {"custom": "value"}

  prop = Prop.create(text="prop text", kind="domain", extra_attributes=extra_attributes)

  assert prop.extra_attributes == extra_attributes
  assert prop.extra_attributes is not extra_attributes


def test_prop_create_copies_extra_nodes() -> None:
  extra_nodes = [UnknownNode(payload=b"<custom />")]

  prop = Prop.create(text="prop text", kind="domain", extra_nodes=extra_nodes)

  assert prop.extra_nodes == extra_nodes
  assert prop.extra_nodes is not extra_nodes
