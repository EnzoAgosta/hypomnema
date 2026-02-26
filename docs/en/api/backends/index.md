---
title: Backends Overview
---

# Backends

XML parsing abstraction for hypomnema.

## Philosophy

Hypomnema uses a backend abstraction to handle XML parsing:

- **Zero dependencies**: StandardBackend uses only Python stdlib
- **Performance**: LxmlBackend is 3-5x faster on large files
- **Extensibility**: Implement XmlBackend for custom needs

## XmlBackend Interface

```python
class XmlBackend(ABC):
    def parse(self, path: Path) -> Element: ...
    def iterparse(self, path: Path, tag_filter: set[str] | None) -> Generator[Element]: ...
    def write(self, element: Element, path: Path, encoding: str) -> None: ...
    
    def get_tag(self, element: Element) -> str: ...
    def get_text(self, element: Element) -> str | None: ...
    def get_tail(self, element: Element) -> str | None: ...
    def get_attribute(self, element: Element, name: str) -> str | None: ...
    def iter_children(self, element: Element) -> Iterator[Element]: ...
    # ... more methods
```

## Available Backends

| Backend | Dependencies | Performance | Use Case |
|---------|--------------|-------------|----------|
| [StandardBackend](/en/api/backends/standard) | None | Baseline | Default, zero-dep |
| [LxmlBackend](/en/api/backends/lxml) | `lxml>=6.0.2` | 3-5x faster | Large files |

## Auto-Selection

Hypomnema auto-selects the best backend:

1. If lxml is installed → LxmlBackend
2. Otherwise → StandardBackend

```python
# Uses best available
tmx = load("file.tmx")

# Explicit selection
from hypomnema import backends
tmx = load("file.tmx", backend=backends.StandardBackend())
```

## Sections

- [Standard Backend](/en/api/backends/standard) — stdlib xml.etree
- [Lxml Backend](/en/api/backends/lxml) — Optional lxml
