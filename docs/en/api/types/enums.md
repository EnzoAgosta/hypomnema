---
title: Enums
---

# Enums

Enumerated types used in TMX attributes.

## Segtype

Segmentation type indicator.

```python
class Segtype(StrEnum):
    BLOCK = "block"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    PHRASE = "phrase"
```

| Value | Description |
|-------|-------------|
| `block` | Segment doesn't correspond to standard levels (e.g., a chapter) |
| `paragraph` | Segmented at paragraph boundaries |
| `sentence` | Segmented at sentence boundaries (recommended for portability) |
| `phrase` | Segmented at phrase boundaries |

### Usage

```python
from hypomnema import Segtype

header = helpers.create_header(
    segtype=Segtype.SENTENCE,  # Enum
    # or
    segtype="sentence",  # String (converted to Enum)
)
```

### XML Mapping

```xml
<header segtype="sentence">
<tu segtype="phrase">
```

---

## Pos

Position indicator for isolated tags (`<it>`).

```python
class Pos(StrEnum):
    BEGIN = "begin"
    END = "end"
```

| Value | Description |
|-------|-------------|
| `begin` | Isolated tag is a beginning tag (pair is outside segment) |
| `end` | Isolated tag is an ending tag (pair is outside segment) |

### Usage

```python
from hypomnema import Pos

it = helpers.create_it(
    pos=Pos.BEGIN,  # Enum
    # or
    pos="begin",  # String (converted to Enum)
)
```

### XML Mapping

```xml
<it pos="begin">
<it pos="end">
```

---

## Assoc

Association attribute for placeholders (`<ph>`).

```python
class Assoc(StrEnum):
    P = "p"
    F = "f"
    B = "b"
```

| Value | Description |
|-------|-------------|
| `p` | Associated with text **preceding** the element |
| `f` | Associated with text **following** the element |
| `b` | Associated with text on **both** sides |

### Usage

```python
from hypomnema import Assoc

ph = helpers.create_ph(
    assoc=Assoc.B,  # Enum
    # or
    assoc="b",  # String (converted to Enum)
)
```

### XML Mapping

```xml
<ph assoc="p">
<ph assoc="f">
<ph assoc="b">
```

### When to Use

The `assoc` attribute helps during translation:

- `p` (preceding): Placeholder belongs to the text before it
  - Example: Trailing punctuation, end tags
- `f` (following): Placeholder belongs to the text after it
  - Example: Leading tags, opening brackets
- `b` (both): Placeholder is independent
  - Example: Standalone variables, images

## String Conversion

All enums inherit from `StrEnum`, so they can be used as strings:

```python
from hypomnema import Segtype

s = Segtype.SENTENCE
print(s)  # "sentence"
print(s == "sentence")  # True
```
