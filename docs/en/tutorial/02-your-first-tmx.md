---
title: Your First TMX
---

# Your First TMX

Let's load a TMX file and explore its structure.

## Loading a File

```python
import hypomnema as hm

tmx = hm.load("translations.tmx")
```

The `load()` function reads the TMX file and returns a `Tmx` dataclass containing all the data.

## Exploring the Structure

A TMX file has a simple hierarchical structure:

```python
tmx = hm.load("translations.tmx")

# Access the header (metadata about the file)
print(tmx.header.creationtool)      # Tool that created the TMX
print(tmx.header.srclang)           # Source language (e.g., "en")
print(tmx.header.segtype)           # Segmentation type

# Access the body (list of translation units)
for tu in tmx.body:
    print(f"Translation unit: {tu.tuid}")
    for tuv in tu.variants:
        print(f"  {tuv.lang}: {hm.helpers.text(tuv)}")
```

## The Data Model

```
Tmx
├── header: Header (file metadata)
│   ├── props: list[Prop]
│   └── notes: list[Note]
└── body: list[Tu] (translation units)
    └── variants: list[Tuv] (language variants)
        └── content: list[str | InlineElement]
```

- **Tmx**: Root element containing everything
- **Header**: Metadata (creation tool, source language, etc.)
- **Tu**: Translation unit — a set of aligned segments across languages
- **Tuv**: Translation unit variant — the text in one specific language
- **content**: The actual translatable text, possibly mixed with inline markup

## Extracting Plain Text

The `content` field of a `Tuv` can contain strings mixed with inline elements (for formatting, placeholders, etc.). To get just the text:

```python
text = hm.helpers.text(tuv)  # Concatenates all string parts
```

## Next Steps

Now that you can load and explore TMX files, let's learn how to [create them from scratch](/en/tutorial/03-creating-tmx).
