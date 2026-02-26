---
title: Creating TMX Files
---

# Creating TMX Files

Let's build a TMX document from scratch.

## Creating the Header

The header contains metadata about the TMX file:

```python
import hypomnema as hm

header = hm.helpers.create_header(
    srclang="en",
    adminlang="en",
    segtype="sentence",
)
```

Most attributes have sensible defaults:
- `creationtool`: "hypomnema"
- `creationtoolversion`: Current library version
- `creationdate`: Current timestamp

## Creating Translation Units

A translation unit (Tu) groups variants in different languages:

```python
tu = hm.helpers.create_tu(
    tuid="msg-001",
    srclang="en",
    variants=[
        hm.helpers.create_tuv("en", content=["Hello, world!"]),
        hm.helpers.create_tuv("fr", content=["Bonjour, le monde!"]),
        hm.helpers.create_tuv("es", content=["¡Hola, mundo!"]),
    ],
)
```

## Creating the TMX Root

Combine the header and body into a Tmx object:

```python
tmx = hm.helpers.create_tmx(
    header=header,
    body=[tu],
)
```

## Adding Metadata

You can attach properties and notes at various levels:

```python
# Header-level metadata
header = hm.helpers.create_header(
    srclang="en",
    props=[
        hm.helpers.create_prop("client-name", "Acme Corp"),
        hm.helpers.create_prop("project-id", "PRJ-123"),
    ],
    notes=[
        hm.helpers.create_note("Generated from source files on 2024-01-15"),
    ],
)

# TU-level metadata
tu = hm.helpers.create_tu(
    variants=[...],
    notes=[
        hm.helpers.create_note("Context: Login screen button"),
    ],
)

# TUV-level metadata
tuv = hm.helpers.create_tuv(
    "en",
    content=["Submit"],
    props=[
        hm.helpers.create_prop("max-length", "10"),
    ],
)
```

## Next Steps

Now you can create basic TMX files. Next, let's explore [working with variants](/en/tutorial/04-working-with-variants) in more detail.
