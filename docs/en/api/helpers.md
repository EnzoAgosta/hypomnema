---
title: Helpers
---

# Helpers

Factory functions for creating TMX elements. These handle common defaults and type conversions.

## Module

```python
from hypomnema import helpers
# or
from hypomnema.helpers import create_tu, create_tuv, ...
```

---

## Text Extraction

### text()

Extract plain text from mixed content.

```python
def text(source: Tuv | Bpt | Ept | It | Ph | Hi | Sub) -> str
```

Concatenates all string items in `content`, skipping inline elements.

```python
tuv = helpers.create_tuv("en", content=[
    "Hello, ",
    helpers.create_bpt(i=1),
    "world",
    helpers.create_ept(i=1),
    "!",
])

text = helpers.text(tuv)  # "Hello, world!"
```

### iter_text()

Iterate over text segments with optional filtering.

```python
def iter_text(
    source: Tuv | Bpt | Ept | It | Ph | Hi | Sub,
    *,
    ignore: type | Iterable[type] | None = None,
    recurse_inside_ignored: bool = False,
) -> Generator[str]
```

```python
# Get all text
list(helpers.iter_text(tuv))

# Skip placeholders
list(helpers.iter_text(tuv, ignore=Ph))

# Skip multiple types
list(helpers.iter_text(tuv, ignore=[Ph, It]))
```

---

## Root Elements

### create_tmx()

Create a TMX root element.

```python
def create_tmx(
    *,
    header: Header | None = None,
    body: Iterable[Tu] | None = None,
    version: str = "1.4",
) -> Tmx
```

```python
tmx = helpers.create_tmx(
    header=helpers.create_header(srclang="en"),
    body=[
        helpers.create_tu(...),
        helpers.create_tu(...),
    ],
)
```

### create_header()

Create a TMX header element.

```python
def create_header(
    *,
    creationtool: str = "hypomnema",
    creationtoolversion: str = ...,  # Current version
    segtype: Segtype | str = Segtype.BLOCK,
    o_tmf: str = "tmx",
    adminlang: str = "en",
    srclang: str = "en",
    datatype: str = "plaintext",
    o_encoding: str | None = None,
    creationdate: datetime | None = None,  # Defaults to now
    creationid: str | None = None,
    changedate: datetime | None = None,
    changeid: str | None = None,
    notes: Iterable[Note] | None = None,
    props: Iterable[Prop] | None = None,
) -> Header
```

```python
header = helpers.create_header(
    srclang="en",
    adminlang="en",
    segtype="sentence",
    notes=[
        helpers.create_note("Generated from source files"),
    ],
)
```

---

## Translation Units

### create_tu()

Create a translation unit.

```python
def create_tu(
    *,
    tuid: str | None = None,
    srclang: str | None = None,
    segtype: Segtype | str | None = None,
    variants: Iterable[Tuv] | None = None,
    # ... plus all optional metadata attributes
) -> Tu
```

```python
tu = helpers.create_tu(
    tuid="msg-001",
    srclang="en",
    variants=[
        helpers.create_tuv("en", content=["Hello"]),
        helpers.create_tuv("fr", content=["Bonjour"]),
    ],
)
```

### create_tuv()

Create a translation unit variant.

```python
def create_tuv(
    lang: str,
    *,
    content: str | Iterable[str | InlineElement] | None = None,
    # ... plus all optional metadata attributes
) -> Tuv
```

```python
# Simple text
tuv = helpers.create_tuv("en", content=["Hello, world!"])

# Text with inline markup
tuv = helpers.create_tuv("en", content=[
    "Hello, ",
    helpers.create_bpt(i=1, content=["<b>"]),
    "world",
    helpers.create_ept(i=1, content=["</b>"]),
])

# String shorthand (converted to list internally)
tuv = helpers.create_tuv("en", content="Simple text")
```

---

## Metadata Elements

### create_prop()

Create a property element.

```python
def create_prop(
    text: str,
    type: str,
    *,
    lang: str | None = None,
    o_encoding: str | None = None,
) -> Prop
```

```python
prop = helpers.create_prop(
    text="Acme Corp",
    type="client",
)
```

### create_note()

Create a note element.

```python
def create_note(
    text: str,
    *,
    lang: str | None = None,
    o_encoding: str | None = None,
) -> Note
```

```python
note = helpers.create_note(
    text="Context: Login screen",
    lang="en",
)
```

---

## Inline Elements

### create_bpt()

Create a begin paired tag.

```python
def create_bpt(
    i: int,
    *,
    content: str | Iterable[str | Sub] | None = None,
    x: int | None = None,
    type: str | None = None,
) -> Bpt
```

```python
bpt = helpers.create_bpt(i=1, type="bold", content=["<b>"])
```

### create_ept()

Create an end paired tag.

```python
def create_ept(
    i: int,
    *,
    content: str | Iterable[str | Sub] | None = None,
) -> Ept
```

```python
ept = helpers.create_ept(i=1, content=["</b>"])
```

### create_it()

Create an isolated tag.

```python
def create_it(
    pos: Pos | Literal["begin", "end"],
    *,
    content: str | Iterable[str | Sub] | None = None,
    x: int | None = None,
    type: str | None = None,
) -> It
```

```python
it = helpers.create_it(pos="begin", type="bold", content=["<b>"])
```

### create_ph()

Create a placeholder.

```python
def create_ph(
    *,
    content: str | Iterable[str | Sub] | None = None,
    x: int | None = None,
    assoc: Assoc | Literal["p", "f", "b"] | None = None,
    type: str | None = None,
) -> Ph
```

```python
ph = helpers.create_ph(type="var", content=["{name}"])
```

### create_hi()

Create a highlight.

```python
def create_hi(
    *,
    content: str | Iterable[str | InlineElement] | None = None,
    x: int | None = None,
    type: str | None = None,
) -> Hi
```

```python
hi = helpers.create_hi(type="term", content=["hypomnema"])
```

### create_sub()

Create a sub-flow.

```python
def create_sub(
    *,
    content: str | Iterable[str | InlineElement] | None = None,
    datatype: str | None = None,
    type: str | None = None,
) -> Sub
```

```python
sub = helpers.create_sub(content=["Click for more info"])
```

## See Also

- [Types](/en/api/types/) — Dataclass definitions
- [Tutorial: Creating TMX](/en/tutorial/03-creating-tmx)
