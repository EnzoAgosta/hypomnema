from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import Note, Prop
from hypomnema.dumpers.xml import NoteDumper, PropDumper


def test_note_dumper_emits_note_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(NoteDumper(backend).dump(Note.create(text="note"))) == "note"


def test_note_dumper_emits_text(backend: XmlBackend[object]) -> None:
  assert backend.get_text(NoteDumper(backend).dump(Note.create(text="note"))) == "note"


def test_note_dumper_emits_language_attribute(backend: XmlBackend[object]) -> None:
  element = NoteDumper(backend).dump(Note.create(text="note", language="en"))

  assert backend.get_attribute(element, "xml:lang") == "en"


def test_note_dumper_emits_original_encoding_attribute(backend: XmlBackend[object]) -> None:
  element = NoteDumper(backend).dump(Note.create(text="note", original_encoding="utf-8"))

  assert backend.get_attribute(element, "o-encoding") == "utf-8"


def test_prop_dumper_emits_prop_tag(backend: XmlBackend[object]) -> None:
  assert (
    backend.get_tag(PropDumper(backend).dump(Prop.create(text="finance", kind="domain"))) == "prop"
  )


def test_prop_dumper_emits_text(backend: XmlBackend[object]) -> None:
  assert (
    backend.get_text(PropDumper(backend).dump(Prop.create(text="finance", kind="domain")))
    == "finance"
  )


def test_prop_dumper_emits_type_attribute(backend: XmlBackend[object]) -> None:
  element = PropDumper(backend).dump(Prop.create(text="finance", kind="domain"))

  assert backend.get_attribute(element, "type") == "domain"


def test_prop_dumper_emits_language_attribute(backend: XmlBackend[object]) -> None:
  element = PropDumper(backend).dump(Prop.create(text="finance", kind="domain", language="fr"))

  assert backend.get_attribute(element, "xml:lang") == "fr"


def test_prop_dumper_emits_original_encoding_attribute(backend: XmlBackend[object]) -> None:
  element = PropDumper(backend).dump(
    Prop.create(text="finance", kind="domain", original_encoding="latin-1")
  )

  assert backend.get_attribute(element, "o-encoding") == "latin-1"
