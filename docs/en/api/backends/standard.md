---
title: Standard Backend
---

# StandardBackend

XML backend using Python's built-in `xml.etree.ElementTree`.

## Class

```python
class StandardBackend(XmlBackend):
    def __init__(
        self,
        logger: Logger | None = None,
        default_encoding: str = "utf-8",
        namespace_handler: NamespaceHandler | None = None,
    ): ...
```

## Features

- **Zero dependencies**: Uses only Python stdlib
- **Streaming support**: `iterparse()` for large files
- **Namespace handling**: Supports `xml:lang` and custom namespaces

## Usage

```python
from hypomnema import load, backends

# Explicit use
tmx = load("file.tmx", backend=backends.StandardBackend())

# With logger
import logging
logger = logging.getLogger("xml-backend")

tmx = load("file.tmx", backend=backends.StandardBackend(logger=logger))
```

## Performance

Suitable for files up to ~100 MB. For larger files, consider LxmlBackend.

## Security

StandardBackend is safe by default—it doesn't resolve external entities.

## See Also

- [Lxml Backend](/en/api/backends/lxml) — Faster alternative
- [Tutorial: Backends](/en/tutorial/09-backends)
