---
title: Tmx
---

# Tmx

Root element for TMX documents.

## XML Element

```xml
<tmx version="1.4">
  <header>...</header>
  <body>...</body>
</tmx>
```

## Python Class

```python
@dataclass(slots=True)
class Tmx:
    header: Header
    version: str = "1.4"
    body: list[Tu] = field(default_factory=list)
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `header` | `<header>` | `Header` | required | File metadata |
| `version` | `version` | `str` | `"1.4"` | TMX version |
| `body` | `<body>` | `list[Tu]` | `[]` | Translation units |

## XML ↔ Python Mapping

| XML | Python | Notes |
|-----|--------|-------|
| `<tmx>` element | `Tmx` class | |
| `version` attribute | `version` field | String, e.g., `"1.4"` |
| `<header>` child | `header` field | Exactly one required |
| `<body>` child | `body` field | Contains all `<tu>` elements |

## Constraints

- Exactly one `<header>` element (required)
- Exactly one `<body>` element (required, but can be empty)
- `version` format: `major.minor` (e.g., `"1.4"`)

## Creation

```python
import hypomnema as hm

# Using create_tmx
tmx = hm.helpers.create_tmx(
    header=hm.helpers.create_header(srclang="en"),
    body=[
        hm.helpers.create_tu(...),
    ],
)

# Direct instantiation
from hypomnema import Tmx, Header
tmx = Tmx(
    header=Header(
        creationtool="my-app",
        creationtoolversion="1.0",
        segtype=hm.Segtype.SENTENCE,
        o_tmf="tmx",
        adminlang="en",
        srclang="en",
        datatype="plaintext",
    ),
)
```

## Accessing Data

```python
tmx = hm.load("file.tmx")

# Header info
print(tmx.header.srclang)
print(tmx.header.creationtool)

# Translation units
for tu in tmx.body:
    for tuv in tu.variants:
        print(f"{tuv.lang}: {hm.helpers.text(tuv)}")
```

## See Also

- [Header](/en/api/types/header) — Metadata element
- [Tu](/en/api/types/tu) — Translation unit
- [Core API: load](/en/api/core#load) — Loading TMX files
