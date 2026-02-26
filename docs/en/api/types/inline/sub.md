---
title: Sub
---

# Sub

Sub-flow — translatable text inside native codes.

## XML Element

```xml
<bpt i="1">&lt;a href="#" title="<sub>Click for more info</sub>"&gt;</bpt>
link text<ept i="1">&lt;/a&gt;</ept>
```

## Python Class

```python
@dataclass(slots=True)
class Sub:
    datatype: str | None = None
    type: str | None = None
    content: list[str | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `datatype` | `datatype` | `str \| None` | `None` | Data type |
| `type` | `type` | `str \| None` | `None` | Sub-flow type |
| `content` | (mixed) | `list[str \| InlineElement]` | `[]` | Text + inline elements |

## When to Use Sub

Sub-flows represent translatable text nested inside codes:

- **Tooltips**: `title` attribute text in links
- **Footnotes**: Footnote definitions
- **Alt text**: Image alternative text
- **Index entries**: Index marker text

```xml
<bpt i="1">&lt;a title="<sub>Go to homepage</sub>"&gt;</bpt>Home<ept i="1">&lt;/a&gt;</ept>
<ph type="fnote">&lt;fnote&gt;<sub>This is the footnote text</sub>&lt;/fnote&gt;</ph>
```

## Sub-flow vs Main Segment

Sub-flows can cause interoperability issues:

- Tool A: Includes sub-flow in main segment
- Tool B: Extracts sub-flow as independent segment

When exchanging TMX files, be aware of how tools handle sub-flows.

## Creation

```python
import hypomnema as hm

# Tooltip in a link
bpt = hm.helpers.create_bpt(
    i=1,
    content=[
        '<a href="#" title="',
        hm.helpers.create_sub(content=["Click for more information"]),
        '">',
    ],
)

# With type
sub = hm.helpers.create_sub(
    type="tooltip",
    content=["Additional help text"],
)
```

## Example

```python
tuv = hm.helpers.create_tuv("en", content=[
    "For more info, see the ",
    hm.helpers.create_bpt(
        i=1,
        content=[
            '<a href="help.html" title="',
            hm.helpers.create_sub(content=["Open help documentation"]),
            '">',
        ],
    ),
    "documentation",
    hm.helpers.create_ept(i=1, content=["</a>"]),
    ".",
])
```

## See Also

- [Bpt](/en/api/types/inline/bpt) — Where sub often appears
- [Ph](/en/api/types/inline/ph) — Can also contain sub-flows
