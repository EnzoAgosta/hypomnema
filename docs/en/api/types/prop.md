---
title: Prop
---

# Prop

Property element for tool-specific metadata.

## XML Element

```xml
<prop type="client">Acme Corp</prop>
<prop type="project-id" xml:lang="en">PRJ-123</prop>
```

## Python Class

```python
@dataclass(slots=True)
class Prop:
    text: str      # Required
    type: str      # Required
    
    lang: str | None = None
    o_encoding: str | None = None
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `text` | (text content) | `str` | required | Property value |
| `type` | `type` | `str` | required | Property type/key |
| `lang` | `xml:lang` | `str \| None` | `None` | Language code |
| `o_encoding` | `o-encoding` | `str \| None` | `None` | Original encoding |

## XML ↔ Python Mapping

| XML | Python | Notes |
|-----|--------|-------|
| `type="client"` | `type="client"` | Direct mapping |
| Text content | `text` field | |
| `xml:lang="en"` | `lang="en"` | Namespace prefix omitted |

## Usage

Properties can appear on:
- `<header>` — Document-level metadata
- `<tu>` — Translation unit metadata
- `<tuv>` — Variant-level metadata

## Property Type Conventions

TMX doesn't standardize property types. Common conventions:

| Type | Description |
|------|-------------|
| `client` | Client name |
| `project` | Project identifier |
| `domain` | Subject domain |
| `x-*` | Tool-specific (prefix with `x-`) |

Tool providers should publish their property types. Custom types should start with `x-`.

## Creation

```python
import hypomnema as hm

prop = hm.helpers.create_prop(
    text="Acme Corp",
    type="client",
)

# With language
prop = hm.helpers.create_prop(
    text="Software localization",
    type="domain",
    lang="en",
)

# Direct instantiation
from hypomnema import Prop
prop = Prop(
    text="PRJ-123",
    type="project-id",
)
```

## Accessing Properties

```python
# Find property by type
client = next(
    (p.text for p in tu.props if p.type == "client"),
    None,
)

# Get all properties as dict
props_dict = {p.type: p.text for p in tmx.header.props}
```

## See Also

- [Note](/en/api/types/note) — Human-readable annotations
- [Header](/en/api/types/header) — Document-level props
- [Tu](/en/api/types/tu) — TU-level props
