---
title: Types Overview
---

# Types

Dataclasses representing TMX 1.4b elements. All dataclasses use `slots=True` for memory efficiency.

## Type Aliases

```python
type BaseElement = Tmx | Header | Prop | Note | Tu | Tuv | Bpt | Ept | It | Ph | Hi | Sub
type InlineElement = Bpt | Ept | It | Ph | Hi | Sub
```

## Protocol Types (Duck Typing)

For type-safe duck typing, hypomnema provides protocol classes:

```python
from hypomnema.base.types import (
    TmxLike, HeaderLike, TuLike, TuvLike,
    PropLike, NoteLike,
    BptLike, EptLike, ItLike, PhLike, HiLike, SubLike,
)
```

See [Duck Typing](/en/advanced/duck-typing) for details.

## Element Hierarchy

```
Tmx
├── header: Header
│   ├── props: list[Prop]
│   └── notes: list[Note]
└── body: list[Tu]
    ├── props: list[Prop]
    ├── notes: list[Note]
    └── variants: list[Tuv]
        ├── props: list[Prop]
        ├── notes: list[Note]
        └── content: list[str | InlineElement]
```

## Pages

- [Tmx](/en/api/types/tmx) — Root element
- [Header](/en/api/types/header) — File metadata
- [Tu](/en/api/types/tu) — Translation unit
- [Tuv](/en/api/types/tuv) — Translation unit variant
- [Prop](/en/api/types/prop) — Property element
- [Note](/en/api/types/note) — Note element
- [Enums](/en/api/types/enums) — Segtype, Pos, Assoc
- [Inline Elements](/en/api/types/inline/) — Bpt, Ept, It, Ph, Hi, Sub
