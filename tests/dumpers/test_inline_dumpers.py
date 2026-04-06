from hypomnema.backends.xml.base import XmlBackend
from hypomnema.domain.nodes import Bpt, Hi, Ph, Sub
from hypomnema.dumpers.xml import BptDumper, HiDumper


def dump_bpt(backend: XmlBackend[object]) -> object:
  sub = Sub.create(content=["sub"], original_data_type="xml")
  return BptDumper(backend).dump(
    Bpt.create(content=["lead", sub, "tail"], internal_id=1, external_id=2, kind="fmt")
  )


def dump_hi(backend: XmlBackend[object]) -> object:
  placeholder = Ph.create(content=["ph"], kind="fmt")
  return HiDumper(backend).dump(
    Hi.create(content=["lead", placeholder, "tail"], external_id=9, kind="style")
  )


def test_bpt_dumper_emits_bpt_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(dump_bpt(backend)) == "bpt"


def test_bpt_dumper_emits_internal_id_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_bpt(backend), "i") == "1"


def test_bpt_dumper_emits_external_id_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_bpt(backend), "x") == "2"


def test_bpt_dumper_emits_kind_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_bpt(backend), "type") == "fmt"


def test_bpt_dumper_emits_leading_text(backend: XmlBackend[object]) -> None:
  assert backend.get_text(dump_bpt(backend)) == "lead"


def test_bpt_dumper_emits_nested_sub_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(next(backend.iter_children(dump_bpt(backend)))) == "sub"


def test_bpt_dumper_emits_nested_sub_text(backend: XmlBackend[object]) -> None:
  child = next(backend.iter_children(dump_bpt(backend)))

  assert backend.get_text(child) == "sub"


def test_bpt_dumper_emits_tail_after_nested_sub(backend: XmlBackend[object]) -> None:
  child = next(backend.iter_children(dump_bpt(backend)))

  assert backend.get_tail(child) == "tail"


def test_hi_dumper_emits_hi_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(dump_hi(backend)) == "hi"


def test_hi_dumper_emits_external_id_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_hi(backend), "x") == "9"


def test_hi_dumper_emits_kind_attribute(backend: XmlBackend[object]) -> None:
  assert backend.get_attribute(dump_hi(backend), "type") == "style"


def test_hi_dumper_emits_leading_text(backend: XmlBackend[object]) -> None:
  assert backend.get_text(dump_hi(backend)) == "lead"


def test_hi_dumper_emits_nested_ph_tag(backend: XmlBackend[object]) -> None:
  assert backend.get_tag(next(backend.iter_children(dump_hi(backend)))) == "ph"


def test_hi_dumper_emits_nested_ph_text(backend: XmlBackend[object]) -> None:
  child = next(backend.iter_children(dump_hi(backend)))

  assert backend.get_text(child) == "ph"


def test_hi_dumper_emits_tail_after_nested_ph(backend: XmlBackend[object]) -> None:
  child = next(backend.iter_children(dump_hi(backend)))

  assert backend.get_tail(child) == "tail"
