---
title: API Reference
---

# API Reference

Complete reference for all hypomnema modules, classes, and functions.

## Module Organization

```
hypomnema/
├── load(), dump()         # Core API
├── helpers                 # Factory functions
├── types                   # Dataclasses (Tmx, Tu, Tuv, etc.)
├── policy                  # Error handling policies
├── backends                # XML parsing backends
├── serialization           # Object → XML conversion
├── deserialization         # XML → Object conversion
└── errors                  # Exception hierarchy
```

## Quick Import

```python
import hypomnema as hm

# Load and save
tmx = hm.load("file.tmx")
hm.dump(tmx, "output.tmx")

# Create elements
header = hm.helpers.create_header(srclang="en")
tu = hm.helpers.create_tu(variants=[...])

# Dataclasses
from hypomnema import Tmx, Tu, Tuv, Header, Prop, Note

# Inline elements
from hypomnema import Bpt, Ept, It, Ph, Hi, Sub

# Enums
from hypomnema import Segtype, Pos, Assoc
```

## Sections

- [Core](/en/api/core) — `load()` and `dump()` functions
- [Helpers](/en/api/helpers) — Factory functions for creating elements
- [Types](/en/api/types/) — All dataclasses and enums
- [Policy](/en/api/policy/) — Error handling configuration
- [Backends](/en/api/backends/) — XML parsing abstraction
- [Errors](/en/api/errors) — Exception hierarchy
