from hypomnema.domain.attributes import Assoc, Pos
from hypomnema.domain.nodes import Bpt, Ept, Hi, It, Ph, Sub, UnknownInlineNode


def test_bpt_create_coerces_internal_id() -> None:
  assert Bpt.create(content=[], internal_id="1").spec_attributes.internal_id == 1


def test_bpt_create_coerces_external_id() -> None:
  assert Bpt.create(content=[], internal_id=1, external_id=b"2").spec_attributes.external_id == 2


def test_bpt_create_sets_kind() -> None:
  assert Bpt.create(content=[], internal_id=1, kind="fmt").spec_attributes.kind == "fmt"


def test_bpt_create_copies_content() -> None:
  content = ["start", UnknownInlineNode(payload=b"<unknown />")]

  node = Bpt.create(content=content, internal_id=1)

  assert node.content == content
  assert node.content is not content


def test_bpt_create_copies_extra_attributes() -> None:
  extra_attributes = {"custom": "value"}

  node = Bpt.create(content=[], internal_id=1, extra_attributes=extra_attributes)

  assert node.extra_attributes == extra_attributes
  assert node.extra_attributes is not extra_attributes


def test_ept_create_coerces_internal_id() -> None:
  assert Ept.create(content=["end"], internal_id="3").spec_attributes.internal_id == 3


def test_ept_create_preserves_content() -> None:
  assert Ept.create(content=["end"], internal_id=3).content == ["end"]


def test_ept_create_rejects_non_int_internal_id() -> None:
  try:
    Ept.create(content=[], internal_id="not-an-int")
  except ValueError:
    pass
  else:
    raise AssertionError("Expected ValueError for a non-integer internal id")


def test_it_create_normalizes_position() -> None:
  assert It.create(content=[], position="begin").spec_attributes.position is Pos.BEGIN


def test_it_create_coerces_external_id() -> None:
  assert It.create(content=[], position="begin", external_id="4").spec_attributes.external_id == 4


def test_it_create_sets_kind() -> None:
  assert It.create(content=[], position="begin", kind="xref").spec_attributes.kind == "xref"


def test_ph_create_normalizes_association() -> None:
  assert Ph.create(content=[], association="b").spec_attributes.association is Assoc.B


def test_ph_create_coerces_external_id() -> None:
  assert Ph.create(content=[], external_id="5").spec_attributes.external_id == 5


def test_ph_create_sets_kind() -> None:
  assert Ph.create(content=[], kind="x").spec_attributes.kind == "x"


def test_hi_create_defaults_external_id_to_none() -> None:
  assert Hi.create(content=[]).spec_attributes.external_id is None


def test_hi_create_defaults_kind_to_none() -> None:
  assert Hi.create(content=[]).spec_attributes.kind is None


def test_hi_create_defaults_content_to_given_empty_list() -> None:
  assert Hi.create(content=[]).content == []


def test_hi_create_defaults_extra_attributes_to_empty_dict() -> None:
  assert Hi.create(content=[]).extra_attributes == {}


def test_sub_create_sets_original_data_type() -> None:
  assert (
    Sub.create(content=[], original_data_type="plaintext").spec_attributes.original_data_type
    == "plaintext"
  )


def test_sub_create_sets_kind() -> None:
  assert Sub.create(content=[], kind="annotation").spec_attributes.kind == "annotation"


def test_sub_create_copies_content() -> None:
  content = ["nested"]

  node = Sub.create(content=content)

  assert node.content == content
  assert node.content is not content


def test_sub_create_copies_extra_attributes() -> None:
  extra_attributes = {"custom": "value"}

  node = Sub.create(content=[], extra_attributes=extra_attributes)

  assert node.extra_attributes == extra_attributes
  assert node.extra_attributes is not extra_attributes
