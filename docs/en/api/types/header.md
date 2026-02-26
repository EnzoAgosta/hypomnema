---
title: Header
---

# Header

File-level metadata for a TMX document.

## XML Element

```xml
<header
  creationtool="hypomnema"
  creationtoolversion="1.0.0"
  segtype="sentence"
  o-tmf="tmx"
  adminlang="en"
  srclang="en"
  datatype="plaintext"
  creationdate="20240115T120000Z"
>
  <prop type="client">Acme Corp</prop>
  <note>Generated from source files</note>
</header>
```

## Python Class

```python
@dataclass(slots=True)
class Header:
    creationtool: str
    creationtoolversion: str
    segtype: Segtype
    o_tmf: str
    adminlang: str
    srclang: str
    datatype: str
    
    o_encoding: str | None = None
    creationdate: datetime | None = None
    creationid: str | None = None
    changedate: datetime | None = None
    changeid: str | None = None
    
    props: list[Prop] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
```

## Required Attributes

| Python | XML | Type | Description |
|--------|-----|------|-------------|
| `creationtool` | `creationtool` | `str` | Tool that created the TMX |
| `creationtoolversion` | `creationtoolversion` | `str` | Version of creating tool |
| `segtype` | `segtype` | `Segtype` | Segmentation type |
| `o_tmf` | `o-tmf` | `str` | Original TM format |
| `adminlang` | `adminlang` | `str` | Administrative language (BCP-47) |
| `srclang` | `srclang` | `str` | Source language (BCP-47 or `*all*`) |
| `datatype` | `datatype` | `str` | Data type (e.g., `plaintext`, `html`) |

## Optional Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `o_encoding` | `o-encoding` | `str \| None` | `None` | Original encoding |
| `creationdate` | `creationdate` | `datetime \| None` | `None` | Creation timestamp |
| `creationid` | `creationid` | `str \| None` | `None` | Creator identifier |
| `changedate` | `changedate` | `datetime \| None` | `None` | Last modified timestamp |
| `changeid` | `changeid` | `str \| None` | `None` | Last modifier identifier |
| `props` | `<prop>` | `list[Prop]` | `[]` | Tool-specific properties |
| `notes` | `<note>` | `list[Note]` | `[]` | Human-readable notes |

## XML ↔ Python Mapping

| XML | Python | Notes |
|-----|--------|-------|
| `o-tmf` | `o_tmf` | Hyphen → underscore |
| `o-encoding` | `o_encoding` | Hyphen → underscore |
| `segtype="sentence"` | `segtype=Segtype.SENTENCE` | String → Enum |
| `creationdate="20240115T120000Z"` | `datetime` object | ISO-8601 with Z suffix |
| `<prop>` children | `props` list | |
| `<note>` children | `notes` list | |

## Datetime Format

TMX uses ISO-8601 with 'Z' suffix (UTC):

```
YYYYMMDDThhmmssZ
```

Example: `20240115T143022Z`

Python's `datetime.isoformat()` does not append 'Z' automatically. Hypomnema handles this during serialization.

## Common datatype Values

| Value | Description |
|-------|-------------|
| `plaintext` | Plain text (default) |
| `html` | HTML content |
| `xml` | XML content |
| `rtf` | Rich Text Format |
| `unknown` | Unknown type |

## Creation

```python
import hypomnema as hm
from datetime import datetime, UTC

# Using helper with defaults
header = hm.helpers.create_header(
    srclang="en",
    adminlang="en",
    segtype="sentence",
)

# With all options
header = hm.helpers.create_header(
    creationtool="my-app",
    creationtoolversion="1.0",
    segtype=hm.Segtype.SENTENCE,
    o_tmf="tmx",
    adminlang="en",
    srclang="en",
    datatype="html",
    creationdate=datetime.now(UTC),
    props=[
        hm.helpers.create_prop("client", "Acme Corp"),
    ],
    notes=[
        hm.helpers.create_note("Generated from HTML files"),
    ],
)

# Direct instantiation
from hypomnema import Header, Segtype
header = Header(
    creationtool="my-app",
    creationtoolversion="1.0",
    segtype=Segtype.SENTENCE,
    o_tmf="tmx",
    adminlang="en",
    srclang="en",
    datatype="plaintext",
)
```

## See Also

- [Tmx](/en/api/types/tmx) — Parent element
- [Prop](/en/api/types/prop) — Property element
- [Note](/en/api/types/note) — Note element
- [Enums](/en/api/types/enums) — Segtype values
