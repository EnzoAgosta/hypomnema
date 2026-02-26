---
title: It
---

# It

Isolated tag — a tag without its pair in the segment.

## XML Element

```xml
<it pos="begin" x="1" type="bold">&lt;b&gt;</it>text continues...
...text ends here<it pos="end" type="bold">&lt;/b&gt;</it>
```

## Python Class

```python
@dataclass(slots=True)
class It:
    pos: Pos  # Required
    x: int | None = None
    type: str | None = None
    content: list[str | Sub] = field(default_factory=list)
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `pos` | `pos` | `Pos` | required | Position: `begin` or `end` |
| `x` | `x` | `int \| None` | `None` | External matching ID |
| `type` | `type` | `str \| None` | `None` | Tag type |
| `content` | (mixed) | `list[str \| Sub]` | `[]` | Native code + sub-flows |

## When to Use It

Isolated tags occur when segmentation breaks a paired tag across segment boundaries:

```
Original: <b>Hello world</b> how are you?

After sentence segmentation:
  Segment 1: <b>Hello world.    (opening tag here, closing tag in next segment)
  Segment 2: </b> How are you?  (closing tag here, opening tag was in previous)
```

```xml
<!-- Segment 1 -->
<tu>
  <tuv><seg><it pos="begin" type="bold">&lt;b&gt;</it>Hello world.</seg></tuv>
</tu>

<!-- Segment 2 -->
<tu>
  <tuv><seg><it pos="end" type="bold">&lt;/b&gt;</it> How are you?</seg></tuv>
</tu>
```

## The pos Attribute

| Value | Description |
|-------|-------------|
| `begin` | Isolated beginning tag (end is in another segment) |
| `end` | Isolated ending tag (beginning is in another segment) |

```python
from hypomnema import Pos

it = helpers.create_it(pos=Pos.BEGIN, content=["<b>"])
it = helpers.create_it(pos=Pos.END, content=["</b>"])
```

## Creation

```python
import hypomnema as hm

# Beginning isolated tag
it = hm.helpers.create_it(
    pos="begin",  # or Pos.BEGIN
    type="bold",
    content=["<b>"],
)

# Ending isolated tag
it = hm.helpers.create_it(
    pos="end",  # or Pos.END
    type="bold",
    content=["</b>"],
)

# With x attribute for cross-language matching
it = hm.helpers.create_it(
    pos="begin",
    x=1,
    content=["<a href='#'>"],
)
```

## Example

```python
tuv = hm.helpers.create_tuv("en", content=[
    hm.helpers.create_it(pos="begin", type="bold", content=["<b>"]),
    "This sentence started with bold in the previous segment.",
])
```

## See Also

- [Bpt](/en/api/types/inline/bpt) — Paired tags
- [Enums: Pos](/en/api/types/enums#pos) — Position values
