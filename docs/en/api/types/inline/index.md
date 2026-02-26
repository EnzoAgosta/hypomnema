---
title: Inline Elements Overview
---

# Inline Elements

Elements that appear inside segment content (`<seg>`) to represent formatting, placeholders, and other markup.

## Element Types

| Element | Purpose | Content Type |
|---------|---------|--------------|
| `<bpt>` | Begin paired tag | `str \| Sub` |
| `<ept>` | End paired tag | `str \| Sub` |
| `<it>` | Isolated tag | `str \| Sub` |
| `<ph>` | Placeholder | `str \| Sub` |
| `<hi>` | Highlight | `str \| InlineElement` |
| `<sub>` | Sub-flow | `str \| InlineElement` |

## Nesting Rules

```
bpt, ept, it, ph
└── sub
    └── bpt, ept, it, ph, hi
        └── (can nest further)

hi
└── bpt, ept, it, ph, hi
    └── (can nest further)
```

- `bpt`, `ept`, `it`, `ph` can only contain text and `sub`
- `hi` can contain text and any inline elements (including nested `hi`)
- `sub` can contain text and any inline elements

## Matching Attributes

### i (Internal Matching)

Pairs `<bpt>` with corresponding `<ept>` within a segment:

```xml
<bpt i="1"><b></bpt>text<ept i="1"></b></ept>
```

### x (External Matching)

Matches inline elements across languages in the same TU:

```xml
<!-- English TUV -->
<bpt i="1" x="1"><a href="#"></bpt>link<ept i="1"></a></ept>

<!-- French TUV -->
<bpt i="1" x="1"><a href="#"></bpt>lien<ept i="1"></a></ept>
```

## Pages

- [Bpt](/en/api/types/inline/bpt) — Begin paired tags
- [Ept](/en/api/types/inline/ept) — End paired tags
- [It](/en/api/types/inline/it) — Isolated tags
- [Ph](/en/api/types/inline/ph) — Placeholders
- [Hi](/en/api/types/inline/hi) — Highlights
- [Sub](/en/api/types/inline/sub) — Sub-flows
