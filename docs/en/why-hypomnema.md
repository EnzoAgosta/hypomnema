---
title: Why Hypomnema
---

# Why Hypomnema

A comparison of hypomnema with other TMX libraries and when to use it.

## The Problem

Most Python TMX parsers are thin XML wrappers:

```python
# Typical approach
import xml.etree.ElementTree as ET

tree = ET.parse("file.tmx")
for tu in tree.findall(".//tu"):
    for tuv in tu.findall("tuv"):
        lang = tuv.get("{xml}lang")
        text = tuv.find("seg").text
```

This approach has issues:

- **No type safety**: Everything is strings and None
- **No validation**: Malformed files cause silent errors
- **No abstraction**: Code is coupled to XML structure
- **No configurability**: Error handling is hardcoded

## Hypomnema's Approach

### Type-Safe Dataclasses

```python
import hypomnema as hm

tmx = hm.load("file.tmx")
for tu in tmx.body:
    for tuv in tu.variants:
        print(f"{tuv.lang}: {hm.helpers.text(tuv)}")
```

- IDE autocomplete works
- Type checkers catch errors
- Dataclass semantics (equality, repr, etc.)

### Policy-Driven Error Handling

```python
from hypomnema import policy

lenient = policy.XmlDeserializationPolicy(
    missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE),
)

tmx = hm.load("messy.tmx", deserializer_policy=lenient)
```

Configure behavior per violation type.

### Backend Abstraction

```python
# Zero dependencies
tmx = hm.load("file.tmx", backend=backends.StandardBackend())

# Or faster
tmx = hm.load("file.tmx", backend=backends.LxmlBackend())
```

Switch backends without changing code.

---

## Comparison

### vs translate-toolkit

[translate-toolkit](https://github.com/translate/translate) includes TMX support:

| Feature | translate-toolkit | hypomnema |
|---------|-------------------|-----------|
| TMX version | 1.4 | 1.4b |
| Type safety | No | Yes (dataclasses) |
| Inline elements | Limited | Full support |
| Policy-driven errors | No | Yes |
| Zero dependencies | No | Yes |
| Streaming | No | Yes |

Use translate-toolkit if you need:
- Multiple format support (PO, XLIFF, etc.)
- Translation workflow tools

Use hypomnema if you need:
- Type-safe TMX processing
- Configurable error handling
- Modern Python (3.13+)

### vs lxml directly

```python
# lxml
from lxml import etree
tree = etree.parse("file.tmx")

# hypomnema
import hypomnema as hm
tmx = hm.load("file.tmx")
```

| Feature | lxml | hypomnema |
|---------|------|-----------|
| Type safety | No | Yes |
| TMX validation | No | Yes (via policies) |
| TMX-specific API | No | Yes |
| Zero dependencies | No | Yes (with StandardBackend) |

Use lxml directly if you need:
- Generic XML processing
- XPath/XSLT
- Schema validation

Use hypomnema if you need:
- TMX-specific operations
- Type safety
- Simpler API

### vs tmxpy

[tmxpy](https://pypi.org/project/tmxpy/) is another Python TMX library:

| Feature | tmxpy | hypomnema |
|---------|-------|-----------|
| TMX version | Basic | 1.4b (full) |
| Inline elements | No | Yes |
| Policy-driven errors | No | Yes |
| Duck typing | No | Yes |

---

## When to Use Hypomnema

### Good Fit

- Processing TMX files in Python applications
- Converting between TMX and other formats
- Extracting data from translation memories
- Validating TMX files
- Building CAT tool integrations
- Localization engineering workflows

### Not a Good Fit

- Generic XML processing (use lxml)
- Multiple format support (use translate-toolkit)
- Translation workflow management (use translation management systems)
- Browser-based applications (use JavaScript TMX libraries)

---

## Design Goals

1. **Zero runtime dependencies** — Install and use without external packages
2. **Type-safe** — Full type hints, dataclasses, protocols
3. **Configurable** — Policy-driven error handling
4. **Performant** — Streaming support, lxml optional
5. **Extensible** — Custom backends, handlers, and element classes
6. **Spec-compliant** — Full TMX 1.4b support

---

## Name

*Hypomnema* (Greek: ὑπόμνημα) means "commentary" or "memorial" — a written record meant to preserve knowledge. It reflects the library's purpose: working with translation memories that preserve linguistic knowledge.
