---
title: Note
---

# Note

Annotation element for human-readable comments.

## XML Element

```xml
<note xml:lang="en">Context: Login screen button</note>
<note>This translation was reviewed by the client</note>
```

## Python Class

```python
@dataclass(slots=True)
class Note:
    text: str  # Required
    
    lang: str | None = None
    o_encoding: str | None = None
```

## Attributes

| Python | XML | Type | Default | Description |
|--------|-----|------|---------|-------------|
| `text` | (text content) | `str` | required | Note content |
| `lang` | `xml:lang` | `str \| None` | `None` | Language code |
| `o_encoding` | `o-encoding` | `str \| None` | `None` | Original encoding |

## XML ↔ Python Mapping

| XML | Python | Notes |
|-----|--------|-------|
| Text content | `text` field | |
| `xml:lang="en"` | `lang="en"` | Namespace prefix omitted |

## Usage

Notes can appear on:
- `<header>` — Document-level comments
- `<tu>` — Translation unit comments
- `<tuv>` — Variant-level comments

## Note vs Prop

| Element | Purpose | Audience |
|---------|---------|----------|
| `<note>` | Human-readable comments | Translators, reviewers |
| `<prop>` | Tool-specific data | CAT tools, scripts |

Use `<note>` for comments that should be visible to humans. Use `<prop>` for machine-readable metadata.

## Creation

```python
import hypomnema as hm

note = hm.helpers.create_note(
    text="Context: Login screen button",
)

# With language
note = hm.helpers.create_note(
    text="Reviewed by client",
    lang="en",
)

# Direct instantiation
from hypomnema import Note
note = Note(
    text="Do not translate brand name",
    lang="en",
)
```

## Accessing Notes

```python
# Get all notes for a TU
for note in tu.notes:
    print(note.text)

# Filter by language
en_notes = [n for n in tu.notes if n.lang == "en"]
```

## See Also

- [Prop](/en/api/types/prop) — Tool-specific properties
- [Header](/en/api/types/header) — Document-level notes
- [Tu](/en/api/types/tu) — TU-level notes
