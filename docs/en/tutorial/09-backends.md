---
title: Backends
---

# Backends

Hypomnema uses a backend abstraction to handle XML parsing. This lets you choose between the standard library (no dependencies) or lxml (faster).

## Why Backends?

- **Zero dependencies**: Use stdlib backend for maximum compatibility
- **Performance**: Use lxml backend for 3-5x faster parsing on large files
- **Extensibility**: Implement custom backends for specific needs

## Standard Backend

The default backend uses Python's built-in `xml.etree.ElementTree`:

```python
from hypomnema import load, backends

tmx = load("file.tmx", backend=backends.StandardBackend())
```

This is always available with no additional dependencies.

## Lxml Backend

When lxml is installed, it's used automatically. Or specify it explicitly:

```python
from hypomnema import load, backends

tmx = load("file.tmx", backend=backends.LxmlBackend())
```

### Installing lxml

```bash
pip install lxml>=6.0.2
```

### Performance Comparison

| File Size | Standard Backend | Lxml Backend |
|-----------|------------------|--------------|
| 1 MB | 0.5s | 0.2s |
| 10 MB | 5s | 1.5s |
| 100 MB | 50s | 15s |

(Actual times vary by system and file complexity)

## Auto-Selection

By default, hypomnema auto-selects the best available backend:

1. If lxml is installed → use LxmlBackend
2. Otherwise → use StandardBackend

```python
# Uses lxml if available, otherwise standard
tmx = load("file.tmx")
```

## Backend Features

Both backends support all hypomnema features:

| Feature | Standard | Lxml |
|---------|----------|------|
| Full document parsing | ✅ | ✅ |
| Streaming (iterparse) | ✅ | ✅ |
| Namespace handling | ✅ | ✅ |
| Custom encoding | ✅ | ✅ |

## When to Use Which

**Use StandardBackend when:**
- You want zero dependencies
- File size is small (< 10 MB)
- Compatibility is more important than speed

**Use LxmlBackend when:**
- Processing large files (> 10 MB)
- Batch processing many files
- Performance is critical

## Tutorial Complete!

You've learned all the core concepts of hypomnema:

- Loading and saving TMX files
- Creating documents from scratch
- Working with variants and inline markup
- Streaming large files
- Configuring error handling
- Choosing backends

Next, explore the [Cookbook](/en/cookbook/) for practical recipes, or dive into the [API Reference](/en/api/) for comprehensive documentation.
