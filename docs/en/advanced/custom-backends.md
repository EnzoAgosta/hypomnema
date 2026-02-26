---
title: Custom Backends
---

# Custom Backends

Implement the `XmlBackend` interface for custom XML handling.

## When to Create a Custom Backend

- Use a different XML library (e.g., `defusedxml` for security)
- Add custom preprocessing/postprocessing
- Integrate with existing XML pipelines
- Support alternative storage formats

## XmlBackend Interface

```python
from abc import ABC, abstractmethod

class XmlBackend(ABC):
    @property
    @abstractmethod
    def Element(self) -> type: ...
    
    # Parsing
    @abstractmethod
    def parse(self, path: Path) -> Element: ...
    
    @abstractmethod
    def iterparse(
        self, path: Path, tag_filter: set[str] | None = None
    ) -> Generator[Element]: ...
    
    # Writing
    @abstractmethod
    def write(self, element: Element, path: Path, encoding: str = "utf-8") -> None: ...
    
    # Element access
    @abstractmethod
    def get_tag(self, element: Element) -> str: ...
    
    @abstractmethod
    def get_text(self, element: Element) -> str | None: ...
    
    @abstractmethod
    def get_tail(self, element: Element) -> str | None: ...
    
    @abstractmethod
    def get_attribute(self, element: Element, name: str) -> str | None: ...
    
    @abstractmethod
    def iter_children(self, element: Element) -> Iterator[Element]: ...
    
    # Element modification
    @abstractmethod
    def create_element(self, tag: str) -> Element: ...
    
    @abstractmethod
    def set_text(self, element: Element, text: str) -> None: ...
    
    @abstractmethod
    def set_tail(self, element: Element, tail: str) -> None: ...
    
    @abstractmethod
    def set_attribute(self, element: Element, name: str, value: str) -> None: ...
    
    @abstractmethod
    def append_child(self, parent: Element, child: Element) -> None: ...
    
    # Tag filtering
    @abstractmethod
    def prep_tag_set(
        self, tags: str | QNameLike | Iterable[str | QNameLike]
    ) -> set[str]: ...
```

## Example: Defusedxml Backend

For handling untrusted XML input:

```python
from defusedxml.ElementTree import parse as safe_parse, iterparse as safe_iterparse
from hypomnema.xml.backends.base import XmlBackend

class DefusedxmlBackend(XmlBackend):
    """Secure backend using defusedxml for untrusted input."""
    
    @property
    def Element(self) -> type:
        from xml.etree.ElementTree import Element
        return Element
    
    def parse(self, path: Path) -> Element:
        tree = safe_parse(path)
        return tree.getroot()
    
    def iterparse(self, path: Path, tag_filter: set[str] | None = None) -> Generator[Element]:
        for event, element in safe_iterparse(path, events=("end",)):
            if tag_filter is None or self.get_tag(element) in tag_filter:
                yield element
    
    # ... implement remaining methods
```

## Example: Dict-Based Backend

For testing or alternative storage:

```python
class DictBackend(XmlBackend):
    """Backend that stores XML as dictionaries."""
    
    @property
    def Element(self) -> type:
        return dict
    
    def create_element(self, tag: str) -> dict:
        return {"tag": tag, "attrs": {}, "text": None, "tail": None, "children": []}
    
    def get_tag(self, element: dict) -> str:
        return element["tag"]
    
    def get_text(self, element: dict) -> str | None:
        return element.get("text")
    
    def set_text(self, element: dict, text: str) -> None:
        element["text"] = text
    
    # ... implement remaining methods
```

## Using Custom Backends

```python
from hypomnema import load, dump

backend = DefusedxmlBackend()

tmx = load("untrusted.tmx", backend=backend)
dump(tmx, "output.tmx", backend=backend)
```

## Implementation Notes

### Namespace Handling

The backend must handle namespaced attributes:

```python
def get_attribute(self, element: Element, name: str) -> str | None:
    # Handle {namespace}localname format
    if name.startswith("{"):
        return element.get(name)
    
    # Handle xml:lang specially
    if name == "{xml}lang":
        return element.get("{http://www.w3.org/XML/1998/namespace}lang")
    
    return element.get(name)
```

### Tag Normalization

`get_tag()` should return local names without namespaces:

```python
def get_tag(self, element: Element) -> str:
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[1]  # Strip namespace
    return tag
```

### Streaming Cleanup

`iterparse()` should clean up elements after yielding:

```python
def iterparse(self, path: Path, tag_filter: set[str] | None) -> Generator[Element]:
    for event, element in ET.iterparse(path, events=("end",)):
        if tag_filter is None or self.get_tag(element) in tag_filter:
            yield element
            element.clear()  # Free memory
```

## See Also

- [Backends Overview](/en/api/backends/)
- [StandardBackend](/en/api/backends/standard) — Reference implementation
