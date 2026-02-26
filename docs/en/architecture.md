---
title: Architecture
---

# Architecture

How hypomnema is designed and built.

## Design Philosophy

### Zero Dependencies

Hypomnema has no runtime dependencies by default:

- Uses Python stdlib `xml.etree.ElementTree`
- Optional `lxml` for performance
- No external packages required for basic use

This makes hypomnema:
- Easy to install and deploy
- Suitable for constrained environments
- Free from supply chain vulnerabilities

### Type-Safe

All public APIs have complete type hints:

```python
def load(
    path: str | PathLike,
    filter: str | None = None,
    **kwargs: Unpack[LoadOptions],
) -> Tmx | Generator[BaseElement]:
```

Works with:
- Static type checkers (mypy, pyright)
- IDE autocomplete
- Runtime protocol checking

### Policy-Driven

Error handling is configurable, not hardcoded:

```python
policy = XmlDeserializationPolicy(
    missing_seg=Behavior(RaiseIgnore.IGNORE),
    invalid_datetime=Behavior(RaiseNoneKeep.NONE),
)
```

This allows:
- Strict validation for critical workflows
- Lenient handling for legacy files
- Custom error responses per violation type

---

## Core Patterns

### Backend Abstraction

All XML operations go through `XmlBackend`:

```
User Code
    ↓
load() / dump()
    ↓
Deserializer / Serializer
    ↓
XmlBackend (interface)
    ↓
┌─────────────────┬─────────────────┐
│ StandardBackend │ LxmlBackend     │
│ (stdlib)        │ (optional)      │
└─────────────────┴─────────────────┘
```

Code outside `xml/backends/` never touches raw XML objects.

### Handler Pattern

Each TMX element has dedicated handlers:

```python
TmxDeserializer    → TmxSerializer
HeaderDeserializer → HeaderSerializer
TuDeserializer     → TuSerializer
TuvDeserializer    → TuvSerializer
# ... etc.
```

Handlers:
- Are single-responsibility
- Call `emit()` for nested elements (orchestrator dispatches)
- Respect policies for error handling

### Orchestrator Pattern

`Deserializer` and `Serializer` are orchestrators:

```python
class Deserializer:
    def __init__(self, backend, handlers: Mapping[str, BaseElementDeserializer]):
        self._handlers = handlers
        # Inject emit() into handlers
        for handler in handlers.values():
            handler.emit = self.deserialize
    
    def deserialize(self, element: Element) -> BaseElement | None:
        tag = self.backend.get_tag(element)
        handler = self._handlers.get(tag)
        return handler._deserialize(element) if handler else None
```

This enables:
- Handler replacement via `handlers=` parameter
- Recursive dispatch via `emit()`
- Clean separation of concerns

---

## Data Flow

### Deserialization

```
TMX File (disk)
    ↓
Backend.parse()
    ↓
XML Element Tree
    ↓
Deserializer.deserialize()
    ↓
Handler dispatch by tag
    ↓
TmxDeserializer → HeaderDeserializer → PropDeserializer
                              ↓
                TuDeserializer → TuvDeserializer → InlineElementDeserializers
    ↓
Tmx dataclass
```

### Serialization

```
Tmx dataclass
    ↓
Serializer.serialize()
    ↓
Handler dispatch by type
    ↓
TmxSerializer → HeaderSerializer → PropSerializer
                            ↓
              TuSerializer → TuvSerializer → InlineElementSerializers
    ↓
XML Element Tree
    ↓
Backend.write()
    ↓
TMX File (disk)
```

---

## Directory Structure

```
src/hypomnema/
├── __init__.py           # Public API exports
├── api/
│   ├── core.py           # load(), dump()
│   └── helpers.py        # create_* functions
├── base/
│   ├── types.py          # Dataclasses (Tmx, Tu, Tuv, etc.)
│   └── errors.py         # Exception hierarchy
└── xml/
    ├── backends/
    │   ├── base.py       # XmlBackend abstract class
    │   ├── standard.py   # stdlib implementation
    │   └── lxml.py       # lxml implementation
    ├── deserialization/
    │   ├── base.py       # BaseElementDeserializer
    │   ├── _handlers.py  # Concrete handlers
    │   └── deserializer.py  # Orchestrator
    ├── serialization/
    │   ├── base.py       # BaseElementSerializer
    │   ├── _handlers.py  # Concrete handlers
    │   └── serializer.py # Orchestrator
    ├── policy.py         # Policy classes
    └── utils.py          # Helpers (path, encoding, tags)
```

---

## Key Constraints

### No Direct XML Access

Code outside `xml/backends/` must use backend methods:

```python
# Wrong
tag = element.tag

# Right
tag = self.backend.get_tag(element)
```

### Dataclasses with slots

All dataclasses use `slots=True`:

```python
@dataclass(slots=True)
class Tu:
    ...
```

Reduces memory by ~40% for large files.

### Mutable Defaults

Use `field(default_factory=...)`:

```python
# Wrong
variants: list[Tuv] = []

# Right
variants: list[Tuv] = field(default_factory=list)
```

---

## Extension Points

| What | How |
|------|-----|
| Custom XML library | Implement `XmlBackend` |
| Custom (de)serialization | Implement handlers, pass via `handlers=` |
| Custom element classes | Implement `*Like` protocols |
| Custom error handling | Configure policies |
| Custom namespaces | Use `NamespaceHandler` |
