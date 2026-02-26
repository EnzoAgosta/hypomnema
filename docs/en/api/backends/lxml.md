---
title: Lxml Backend
---

# LxmlBackend

XML backend using the lxml library.

## Class

```python
class LxmlBackend(XmlBackend):
    def __init__(
        self,
        logger: Logger | None = None,
        default_encoding: str = "utf-8",
        namespace_handler: NamespaceHandler | None = None,
    ): ...
```

## Installation

```bash
pip install lxml>=6.0.2
```

## Features

- **3-5x faster**: Significant speedup on large files
- **Better namespace handling**: Full namespace support
- **Streaming support**: `iterparse()` for large files
- **Security**: `resolve_entities=False` by default

## Usage

```python
from hypomnema import load, backends

# Explicit use
tmx = load("file.tmx", backend=backends.LxmlBackend())

# Auto-selected if lxml is installed
tmx = load("file.tmx")  # Uses LxmlBackend automatically
```

## Performance

| File Size | StandardBackend | LxmlBackend |
|-----------|-----------------|-------------|
| 1 MB | 0.5s | 0.2s |
| 10 MB | 5s | 1.5s |
| 100 MB | 50s | 15s |

(Actual times vary by system)

## When to Use

- Processing files > 10 MB
- Batch processing many files
- Performance-critical applications

## See Also

- [Standard Backend](/en/api/backends/standard) — Zero-dependency alternative
- [Tutorial: Backends](/en/tutorial/09-backends)
