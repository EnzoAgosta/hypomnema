---
title: Ph
---

# Ph

Placeholder — a standalone code without explicit ending.

## XML Element

```xml
Hello <ph x="1" type="var" assoc="b">{name}</ph>, welcome!
```

## Python Class

```python
@dataclass(slots=True)
class Ph:
    x: int | None = None
    type: str | None = None
    assoc: Assoc | None = None
    content: list[str | Sub] = field(default_factory=list)
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `x` | `x` | `int \| None` | `None` | External matching ID |
| `type` | `type` | `str \| None` | `None` | Placeholder type |
| `assoc` | `assoc` | `Assoc \| None` | `None` | Text association |
| `content` | (mixed) | `list[str \| Sub]` | `[]` | Native code + sub-flows |

## When to Use Ph

Placeholders represent self-contained codes:

- Variable placeholders: `{name}`, `%s`, `{{variable}}`
- Images: `<img src="...">`
- Line breaks: `<br>`, `\n`
- Footnote references
- Cross-reference tokens

```xml
<ph type="image">&lt;img src="logo.png"&gt;</ph>
<ph type="var">{count}</ph>
<ph type="lb">&lt;br&gt;</ph>
```

## The type Attribute

Common type values:

| Value | Description |
|-------|-------------|
| `var` | Variable placeholder |
| `image` | Image reference |
| `lb` | Line break |
| `pb` | Page break |
| `cb` | Column break |
| `fnote` | Footnote reference |
| `enote` | End-note reference |
| `index` | Index marker |
| `date` | Date field |
| `time` | Time field |
| `alt` | Alternate text |

## The assoc Attribute

Indicates association with surrounding text:

| Value | Description |
|-------|-------------|
| `p` | Associated with preceding text |
| `f` | Associated with following text |
| `b` | Associated with both sides (independent) |

This helps translation tools decide where to place the placeholder.

```python
# Preceding: placeholder belongs to text before it
ph = helpers.create_ph(assoc="p", content=["."])  # Trailing punctuation

# Following: placeholder belongs to text after it
ph = helpers.create_ph(assoc="f", content=["<p>"])  # Opening tag

# Both: independent placeholder
ph = helpers.create_ph(assoc="b", content=["{name}"])  # Variable
```

## Creation

```python
import hypomnema as hm

# Variable placeholder
ph = hm.helpers.create_ph(
    type="var",
    assoc="b",
    content=["{name}"],
)

# Image
ph = hm.helpers.create_ph(
    type="image",
    content=['<img src="logo.png">'],
)

# With x attribute
ph = hm.helpers.create_ph(
    x=1,
    type="var",
    content=["{count}"],
)
```

## Example

```python
tuv = hm.helpers.create_tuv("en", content=[
    "Hello, ",
    hm.helpers.create_ph(type="var", assoc="b", content=["{name}"]),
    "! You have ",
    hm.helpers.create_ph(type="var", assoc="b", content=["{count}"]),
    " messages.",
])
```

## See Also

- [Enums: Assoc](/en/api/types/enums#assoc) — Association values
- [Sub](/en/api/types/inline/sub) — Sub-flow content
