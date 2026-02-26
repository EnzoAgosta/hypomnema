---
title: Hi
---

# Hi

Highlight — marks text with special meaning.

## XML Element

```xml
<hi type="term">hypomnema</hi> is a TMX library.
Please do not translate the <hi type="protected">brand name</hi>.
```

## Python Class

```python
@dataclass(slots=True)
class Hi:
    x: int | None = None
    type: str | None = None
    content: list[str | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `x` | `x` | `int \| None` | `None` | External matching ID |
| `type` | `type` | `str \| None` | `None` | Highlight type |
| `content` | (mixed) | `list[str \| InlineElement]` | `[]` | Text + inline elements |

## When to Use Hi

Highlights mark text with special meaning:

- **Terminology**: Mark terms for terminology management
- **Protected text**: Mark text that should not be translated
- **Emphasis**: Mark emphasized text
- **Quality issues**: Mark suspect text after QA checks

```xml
<hi type="term">translation memory</hi>
<hi type="protected">Acme Corp</hi>
<hi type="emphasis">important</hi>
<hi type="qa-error">suspect phrase</hi>
```

## The type Attribute

Common type values:

| Value | Description |
|-------|-------------|
| `term` | Terminological unit |
| `protected` | Do not translate |
| `emphasis` | Emphasized text |
| `qa-error` | Quality issue |
| `proper-noun` | Proper name |

## Nesting

Hi can contain any inline elements, including nested Hi:

```python
hi = hm.helpers.create_hi(
    type="term",
    content=[
        "translation ",
        hm.helpers.create_hi(type="emphasis", content=["memory"]),
    ],
)
```

## Creation

```python
import hypomnema as hm

# Simple highlight
hi = hm.helpers.create_hi(
    type="term",
    content=["translation memory"],
)

# With nested markup
hi = hm.helpers.create_hi(
    type="protected",
    content=[
        hm.helpers.create_bpt(i=1, content=["<b>"]),
        "Acme Corp",
        hm.helpers.create_ept(i=1, content=["</b>"]),
    ],
)

# With x attribute
hi = hm.helpers.create_hi(
    x=1,
    type="term",
    content=["hypomnema"],
)
```

## Example

```python
tuv = hm.helpers.create_tuv("en", content=[
    "The ",
    hm.helpers.create_hi(type="term", content=["hypomnema"]),
    " library handles ",
    hm.helpers.create_hi(type="protected", content=["TMX"]),
    " files.",
])
```

## See Also

- [Tutorial: Inline Markup](/en/tutorial/05-inline-markup)
