---
title: Bpt
---

# Bpt

Begin paired tag — the opening half of a paired inline tag.

## XML Elements

```xml
<bpt i="1" x="1" type="bold">&lt;b&gt;</bpt>important text<ept i="1">&lt;/b&gt;</ept>
```

## Python Classes

```python
@dataclass(slots=True)
class Bpt:
    i: int  # Required
    x: int | None = None
    type: str | None = None
    content: list[str | Sub] = field(default_factory=list)


@dataclass(slots=True)
class Ept:
    i: int  # Required
    content: list[str | Sub] = field(default_factory=list)
```

## Bpt Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `i` | `i` | `int` | required | Internal matching ID |
| `x` | `x` | `int \| None` | `None` | External matching ID |
| `type` | `type` | `str \| None` | `None` | Tag type |
| `content` | (mixed) | `list[str \| Sub]` | `[]` | Native code + sub-flows |

## Ept Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `i` | `i` | `int` | required | Internal matching ID |
| `content` | (mixed) | `list[str \| Sub]` | `[]` | Native code + sub-flows |

## The i Attribute

Pairs a `<bpt>` with its corresponding `<ept>` within a segment:

```python
tuv = helpers.create_tuv("en", content=[
    "This is ",
    helpers.create_bpt(i=1, content=["<b>"]),
    "important",
    helpers.create_ept(i=1, content=["</b>"]),
    " text.",
])
```

Each `i` value must be unique within a segment.

## The x Attribute

Matches inline elements across language variants:

```python
# English
en_tuv = helpers.create_tuv("en", content=[
    helpers.create_bpt(i=1, x=1, content=["<a href='#'>"]),
    "click here",
    helpers.create_ept(i=1, content=["</a>"]),
])

# French
fr_tuv = helpers.create_tuv("fr", content=[
    helpers.create_bpt(i=1, x=1, content=["<a href='#'>"]),
    "cliquez ici",
    helpers.create_ept(i=1, content=["</a>"]),
])
```

Same `x` value indicates the tags correspond across languages.

## The type Attribute

Describes the tag type. Common values:

| Value | Description |
|-------|-------------|
| `bold` | Bold formatting |
| `italic` | Italic formatting |
| `underline` | Underlined text |
| `link` | Hyperlink |
| `font` | Font change |
| `color` | Color change |

This is informational; tools may use it for processing.

## Sub-flows

Tags can contain translatable sub-flow text:

```python
bpt = helpers.create_bpt(
    i=1,
    content=[
        '<a href="#" title="',
        helpers.create_sub(content=["Click for more info"]),
        '">',
    ],
)
```

## Creation

```python
import hypomnema as hm

# Basic paired tags
bpt = hm.helpers.create_bpt(i=1, type="bold", content=["<b>"])
ept = hm.helpers.create_ept(i=1, content=["</b>"])

# With x attribute
bpt = hm.helpers.create_bpt(i=1, x=1, type="link", content=["<a href='#'>"])

# With sub-flow
bpt = hm.helpers.create_bpt(
    i=1,
    content=[
        '<a title="',
        hm.helpers.create_sub(content=["Tooltip text"]),
        '">',
    ],
)
```

## Example: Full Segment

```python
tuv = hm.helpers.create_tuv("en", content=[
    "Click ",
    hm.helpers.create_bpt(i=1, x=1, type="link", content=["<a href='#'>"]),
    "here",
    hm.helpers.create_ept(i=1, content=["</a>"]),
    " to ",
    hm.helpers.create_bpt(i=2, type="bold", content=["<b>"]),
    "continue",
    hm.helpers.create_ept(i=2, content=["</b>"]),
    ".",
])
```

## See Also

- [It](/en/api/types/inline/it) — Isolated tags (unpaired)
- [Sub](/en/api/types/inline/sub) — Sub-flow content
- [Tutorial: Inline Markup](/en/tutorial/05-inline-markup)
