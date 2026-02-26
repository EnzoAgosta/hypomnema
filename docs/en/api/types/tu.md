---
title: Tu
---

# Tu

Translation Unit — a group of aligned segments in different languages.

## XML Element

```xml
<tu tuid="msg-001" srclang="en">
  <prop type="context">UI|Buttons</prop>
  <note>Context: Login screen</note>
  <tuv xml:lang="en"><seg>Submit</seg></tuv>
  <tuv xml:lang="fr"><seg>Soumettre</seg></tuv>
</tu>
```

## Python Class

```python
@dataclass(slots=True)
class Tu:
    tuid: str | None = None
    o_encoding: str | None = None
    datatype: str | None = None
    usagecount: int | None = None
    lastusagedate: datetime | None = None
    creationtool: str | None = None
    creationtoolversion: str | None = None
    creationdate: datetime | None = None
    creationid: str | None = None
    changedate: datetime | None = None
    segtype: Segtype | None = None
    changeid: str | None = None
    o_tmf: str | None = None
    srclang: str | None = None
    
    props: list[Prop] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    variants: list[Tuv] = field(default_factory=list)
```

## Attributes

### Identification

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `tuid` | `tuid` | `str \| None` | `None` | Unique identifier |

### Language & Type

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `srclang` | `srclang` | `str \| None` | `None` | Source language override |
| `segtype` | `segtype` | `Segtype \| None` | `None` | Segmentation type override |
| `datatype` | `datatype` | `str \| None` | `None` | Data type |
| `o_tmf` | `o-tmf` | `str \| None` | `None` | Original TM format |
| `o_encoding` | `o-encoding` | `str \| None` | `None` | Original encoding |

### Tracking

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `usagecount` | `usagecount` | `int \| None` | `None` | Number of times used |
| `lastusagedate` | `lastusagedate` | `datetime \| None` | `None` | Last usage timestamp |

### Provenance

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `creationtool` | `creationtool` | `str \| None` | `None` | Creating tool |
| `creationtoolversion` | `creationtoolversion` | `str \| None` | `None` | Tool version |
| `creationdate` | `creationdate` | `datetime \| None` | `None` | Creation timestamp |
| `creationid` | `creationid` | `str \| None` | `None` | Creator identifier |
| `changedate` | `changedate` | `datetime \| None` | `None` | Last modified timestamp |
| `changeid` | `changeid` | `str \| None` | `None` | Last modifier identifier |

### Children

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `variants` | `<tuv>` | `list[Tuv]` | `[]` | Language variants |
| `props` | `<prop>` | `list[Prop]` | `[]` | Properties |
| `notes` | `<note>` | `list[Note]` | `[]` | Notes |

## Inheritance from Header

Attributes not specified on a TU inherit from the header:

- `srclang` — Uses header's if not set
- `segtype` — Uses header's if not set
- `datatype` — Uses header's if not set

## XML ↔ Python Mapping

| XML | Python | Notes |
|-----|--------|-------|
| `tuid="msg-001"` | `tuid="msg-001"` | Direct mapping |
| `srclang="en"` | `srclang="en"` | Direct mapping |
| `<tuv>` children | `variants` list | Order preserved |
| `<prop>` before `<tuv>` | `props` list | Can interleave in XML |

## Creation

```python
import hypomnema as hm

# Using helper
tu = hm.helpers.create_tu(
    tuid="msg-001",
    srclang="en",
    variants=[
        hm.helpers.create_tuv("en", content=["Submit"]),
        hm.helpers.create_tuv("fr", content=["Soumettre"]),
    ],
    notes=[
        hm.helpers.create_note("Context: Login screen button"),
    ],
)

# Direct instantiation
from hypomnema import Tu, Tuv
tu = Tu(
    tuid="msg-001",
    srclang="en",
    variants=[
        Tuv(lang="en", content=["Submit"]),
        Tuv(lang="fr", content=["Soumettre"]),
    ],
)
```

## Accessing Variants

```python
tu = hm.helpers.create_tu(...)

# Iterate all variants
for tuv in tu.variants:
    print(f"{tuv.lang}: {hm.helpers.text(tuv)}")

# Find specific language
en_tuv = next((tuv for tuv in tu.variants if tuv.lang == "en"), None)
```

## See Also

- [Tuv](/en/api/types/tuv) — Translation unit variant
- [Header](/en/api/types/header) — Default attribute values
- [Prop](/en/api/types/prop) — Property element
- [Note](/en/api/types/note) — Note element
