---
title: Tuv
---

# Tuv

Translation Unit Variant — text in a specific language.

## XML Element

```xml
<tuv xml:lang="en" creationid="john">
  <prop type="max-length">20</prop>
  <seg>Hello, <bpt i="1">&lt;b&gt;</bpt>world<ept i="1">&lt;/b&gt;</ept>!</seg>
</tuv>
```

## Python Class

```python
@dataclass(slots=True)
class Tuv:
    lang: str  # Required
    
    o_encoding: str | None = None
    datatype: str | None = None
    usagecount: int | None = None
    lastusagedate: datetime | None = None
    creationtool: str | None = None
    creationtoolversion: str | None = None
    creationdate: datetime | None = None
    creationid: str | None = None
    changedate: datetime | None = None
    changeid: str | None = None
    o_tmf: str | None = None
    
    props: list[Prop] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    content: list[str | Bpt | Ept | It | Ph | Hi] = field(default_factory=list)
```

## Required Attributes

| Python | XML | Type | Description |
|--------|-----|------|-------------|
| `lang` | `xml:lang` | `str` | Language code (BCP-47) |

## Optional Attributes

### Language & Encoding

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `lang` | `xml:lang` | `str` | required | Language code |
| `datatype` | `datatype` | `str \| None` | `None` | Data type |
| `o_tmf` | `o-tmf` | `str \| None` | `None` | Original TM format |
| `o_encoding` | `o-encoding` | `str \| None` | `None` | Original encoding |

### Tracking

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `usagecount` | `usagecount` | `int \| None` | `None` | Times accessed |
| `lastusagedate` | `lastusagedate` | `datetime \| None` | `None` | Last access time |

### Provenance

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `creationtool` | `creationtool` | `str \| None` | `None` | Creating tool |
| `creationtoolversion` | `creationtoolversion` | `str \| None` | `None` | Tool version |
| `creationdate` | `creationdate` | `datetime \| None` | `None` | Creation timestamp |
| `creationid` | `creationid` | `str \| None` | `None` | Creator ID |
| `changedate` | `changedate` | `datetime \| None` | `None` | Last modified |
| `changeid` | `changeid` | `str \| None` | `None` | Modifier ID |

### Children

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `content` | `<seg>` | `list[str \| InlineElement]` | `[]` | Segment content |
| `props` | `<prop>` | `list[Prop]` | `[]` | Properties |
| `notes` | `<note>` | `list[Note]` | `[]` | Notes |

## XML ↔ Python Mapping

| XML | Python | Notes |
|-----|--------|-------|
| `xml:lang="en"` | `lang="en"` | Namespace prefix omitted |
| `<seg>` content | `content` list | Mixed text and inline elements |
| `<prop>` before `<seg>` | `props` list | |

## The content Field

The `content` field holds the segment text, which can be:

1. **Plain strings**: Text segments
2. **Inline elements**: `Bpt`, `Ept`, `It`, `Ph`, `Hi`

```python
# Simple text
content=["Hello, world!"]

# Text with markup
content=[
    "Hello, ",
    Bpt(i=1, content=["<b>"]),
    "world",
    Ept(i=1, content=["</b>"]),
    "!",
]
```

## Language Codes

BCP-47 language codes. Not validated by hypomnema.

| Code | Description |
|------|-------------|
| `en` | English |
| `en-US` | American English |
| `en-GB` | British English |
| `fr` | French |
| `fr-CA` | Canadian French |
| `zh-Hans` | Simplified Chinese |
| `zh-Hant` | Traditional Chinese |

Case sensitivity: Language codes in TMX are case-insensitive, but hypomnema preserves the case you provide.

## Creation

```python
import hypomnema as hm

# Simple text
tuv = hm.helpers.create_tuv("en", content=["Hello, world!"])

# With inline markup
tuv = hm.helpers.create_tuv("en", content=[
    "Hello, ",
    hm.helpers.create_bpt(i=1, content=["<b>"]),
    "world",
    hm.helpers.create_ept(i=1, content=["</b>"]),
])

# With metadata
tuv = hm.helpers.create_tuv(
    "en",
    content=["Submit"],
    creationid="john",
    usagecount=42,
)

# Direct instantiation
from hypomnema import Tuv
tuv = Tuv(
    lang="en",
    content=["Hello, world!"],
)
```

## Extracting Text

```python
# Get plain text
text = hm.helpers.text(tuv)

# Iterate text segments
for segment in hm.helpers.iter_text(tuv):
    print(segment)
```

## Edge Cases

### Empty Content

A TUV with no `<seg>` element has an empty `content` list. Controlled by `missing_seg` policy.

### Multiple `<seg>` Elements

TMX 1.4b allows exactly one `<seg>`. If multiple are found, behavior is controlled by `multiple_seg` policy:
- `RAISE` — Raise exception (default)
- `KEEP_FIRST` — Use first segment
- `KEEP_LAST` — Use last segment

## See Also

- [Tu](/en/api/types/tu) — Parent element
- [Inline Elements](/en/api/types/inline/) — Bpt, Ept, It, Ph, Hi
- [Helpers: text](/en/api/helpers#text) — Extracting plain text
