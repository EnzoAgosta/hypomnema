---
title: Inline Markup
---

# Inline Markup

TMX uses inline elements to represent formatting, placeholders, and other markup within translatable text.

## Why Inline Elements?

When you translate formatted text, the formatting tags shouldn't be translated:

```xml
<tu>
  <tuv xml:lang="en"><seg>Click <b>here</b> to continue</seg></tuv>
  <tuv xml:lang="fr"><seg>Cliquez <b>ici</b> pour continuer</seg></tuv>
</tu>
```

TMX inline elements let you represent this structure in a tool-agnostic way.

## Inline Element Types

| Element | Purpose |
|---------|---------|
| `<bpt>` / `<ept>` | Paired tags (opening/closing) |
| `<it>` | Isolated tag (no pair in segment) |
| `<ph>` | Placeholder (image, variable, etc.) |
| `<hi>` | Highlight (emphasis, terminology) |
| `<sub>` | Sub-flow (footnote text, tooltip) |

## Paired Tags: bpt and ept

Use `bpt` (begin paired tag) and `ept` (end paired tag) for formatting that wraps text:

```python
import hypomnema as hm

tuv = hm.helpers.create_tuv("en", content=[
    "Click ",
    hm.helpers.create_bpt(i=1, type="link", content=["<a href='#'>"]),
    "here",
    hm.helpers.create_ept(i=1, content=["</a>"]),
    " to continue.",
])
```

The `i` attribute pairs bpt with its corresponding ept.

## Placeholders: ph

Use `ph` for self-contained codes like images, variables, or line breaks:

```python
tuv = hm.helpers.create_tuv("en", content=[
    "Hello, ",
    hm.helpers.create_ph(type="var", content=["{name}"]),
    "!",
])
```

## Isolated Tags: it

Use `it` when a tag's pair is outside the segment (broken by segmentation):

```python
tuv = hm.helpers.create_tuv("en", content=[
    hm.helpers.create_it(pos="begin", type="bold", content=["<b>"]),
    "Important text",
])
```

## Highlights: hi

Use `hi` to mark text with special meaning (terminology, do-not-translate):

```python
tuv = hm.helpers.create_tuv("en", content=[
    "The ",
    hm.helpers.create_hi(type="term", content=[
        "hypomnema",
    ]),
    " library processes TMX files.",
])
```

## Sub-flows: sub

Use `sub` for translatable content inside markup (footnotes, tooltips):

```python
tuv = hm.helpers.create_tuv("en", content=[
    hm.helpers.create_bpt(i=1, content=[
        "<a href='#' title='",
        hm.helpers.create_sub(content=["Click for more info"]),
        "'>",
    ]),
    "Learn more",
    hm.helpers.create_ept(i=1, content=["</a>"]),
])
```

## Nesting Rules

Inline elements can nest:

- `bpt`, `ept`, `it`, `ph` can contain `sub`
- `hi` can contain any inline elements (including nested `hi`)
- `sub` can contain any inline elements

This allows representing complex markup structures.

## Next Steps

Now that you understand inline markup, let's learn about [saving files](/en/tutorial/06-saving-files).
