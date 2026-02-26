---
title: Working with Variants
---

# Working with Variants

A translation unit variant (Tuv) represents the text in one specific language.

## The Tuv Structure

```python
from hypomnema import Tuv

tuv = Tuv(
    lang="en",                        # Required: BCP-47 language code
    content=["Hello, world!"],        # The translatable text
    creationid="translator-1",        # Optional: who created it
    changedate=datetime.now(UTC),     # Optional: when last modified
    usagecount=42,                    # Optional: how many times used
    props=[],                         # Optional: tool-specific metadata
    notes=[],                         # Optional: human-readable notes
)
```

## Creating Variants

Using the helper function:

```python
import hypomnema as hm

tuv = hm.helpers.create_tuv(
    "en",
    content=["Hello, world!"],
    creationid="john",
)
```

## The Content Field

The `content` field is a list that can contain:

1. **Strings**: Plain text segments
2. **Inline elements**: Markup for formatting, placeholders, etc.

```python
# Simple text
tuv = hm.helpers.create_tuv("en", content=["Hello, world!"])

# Text with inline markup
tuv = hm.helpers.create_tuv("en", content=[
    "Hello, ",
    hm.helpers.create_bpt(i=1, content=["<b>"]),
    "world",
    hm.helpers.create_ept(i=1, content=["</b>"]),
    "!",
])
```

## Extracting Text

To get plain text without markup:

```python
text = hm.helpers.text(tuv)  # "Hello, world!"
```

To iterate over text segments:

```python
for segment in hm.helpers.iter_text(tuv):
    print(segment)
```

## Language Codes

Language codes follow [BCP-47](https://tools.ietf.org/html/bcp47):

- `"en"` — English
- `"en-US"` — American English
- `"fr-CA"` — Canadian French
- `"zh-Hans"` — Simplified Chinese

Hypomnema does not validate language codes—it trusts your input.

## Multiple Variants per TU

A complete translation unit typically has at least two variants:

```python
tu = hm.helpers.create_tu(
    srclang="en",
    variants=[
        hm.helpers.create_tuv("en", content=["Click here"]),
        hm.helpers.create_tuv("fr", content=["Cliquez ici"]),
        hm.helpers.create_tuv("de", content=["Hier klicken"]),
    ],
)
```

## Next Steps

Now let's learn about [inline markup](/en/tutorial/05-inline-markup) for handling formatting and placeholders.
