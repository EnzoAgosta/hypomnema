# AI Pair Programmer Context: hypomnema

**Python TMX 1.4b library | Zero runtime deps | Backend-agnostic | Policy-driven error handling**

## Important Directives
- **Scope**: All TMX 1.4b elements are implemented. **Do not add new elements** unless specifically requested.
- **Backend Abstraction**: **ALWAYS** use the `XmlBackend` abstraction. **NEVER** assume you are working with a real XML element object or import `xml.etree`/`lxml` directly in handlers.
- **Testing**: Always include test plan in PLAN.md, write tests after approval.
- **Documentation**: Write docstrings **last**. Do not document incomplete code.
- **Planning Required**: All changes require a plan document (PLAN.md or feature-specific name) reviewed by human before implementation, unless explicitly instructed to skip planning phase.

## Working Style
- **Response style**: Terse, to the point, maximal clarity
- **Code review priority**: Correctness → Readability → Performance → Documentation (last)
- **When uncertain**: Ask first
- **Planning**: Output plan → await approval → implement

---

## 1. Project Overview

### Problem Domain
TMX (Translation Memory eXchange) is an XML standard for sharing translation memories. Most Python parsers are thin XML wrappers. hypomnema provides:
- Full TMX 1.4b Level 2 compliance (arbitrary inline nesting depth)
- Type-safe dataclasses (not raw XML nodes)
- Policy-driven error handling (configure behavior for malformed data)
- Backend abstraction (stdlib xml.etree or lxml)

### Core Constraint
**No runtime dependencies** — stdlib backend is default, lxml is optional for performance.

### Domain Concepts
See `TERMINOLOGY.md` for quick reference. Key terms:
- **TU** (Translation Unit): Container for translations across languages
- **TUV** (Translation Unit Variant): One language version of a TU
- **Inline elements**: `<bpt>`, `<ept>`, `<it>`, `<ph>`, `<hi>`, `<sub>` — handle formatting/placeholders in translatable text
- **Seg**: The actual translatable content segment within a TUV (represented as `content` field in code)

---

## 2. Architecture Map

### Directory Structure
```
src/hypomnema/
├── __init__.py           # Public API exports
├── base/
│   ├── types.py          # TMX dataclasses (Tmx, Tu, Tuv, Bpt, etc.)
│   └── errors.py         # Exception hierarchy
├── xml/
│   ├── backends/
│   │   ├── base.py       # XmlBackend abstract class
│   │   ├── standard.py   # stdlib xml.etree backend
│   │   └── lxml.py       # lxml backend (optional dependency)
│   ├── deserialization/
│   │   ├── base.py       # BaseElementDeserializer
│   │   ├── _handlers.py  # TmxDeserializer, TuDeserializer, etc.
│   │   └── deserializer.py  # Orchestrator
│   ├── serialization/
│   │   ├── base.py       # BaseElementSerializer
│   │   ├── _handlers.py  # TmxSerializer, TuSerializer, etc.
│   │   └── serializer.py    # Orchestrator
│   ├── policy.py         # Policy configuration (DeserializationPolicy, SerializationPolicy)
│   └── utils.py          # Tag checking, path normalization
└── api/
    └── core.py           # load(), save()
    └── utils.py          # create_* helpers 
```

### Data Flow
```
Input: TMX file on disk
  ↓
Backend.parse() → XML Element tree
  ↓
Deserializer.deserialize() → dispatches to handlers
  ↓
Handlers (TmxDeserializer, TuDeserializer, etc.) → recursively build dataclasses
  ↓
Output: Tmx dataclass with nested Tu/Tuv/inline elements

Reverse for serialization (Tmx → handlers → Backend → disk)
```

### Backend Selection Logic
The `load()` function auto-detects available backends:
1. If `lxml` is installed and no backend specified → use LxmlBackend
2. Otherwise → use StandardBackend
3. User can override: `load(path, backend=StandardBackend())`

### Dependencies

| Scenario | lxml Required? |
|----------|----------------|
| Run tests | Yes (always available in dev environment) |
| Use library (basic) | No (stdlib backend sufficient) |
| Use library (streaming) | No (both backends support streaming) |
| Performance optimization | Optional (lxml is 3-5x faster on large files) |

**Runtime**:
- **Core**: None (uses stdlib xml.etree)
- **Optional**: `lxml>=6.0.2` (faster parsing, better namespace handling)

**Development/Testing**:
- `lxml` is **required** and assumed to be present in dev environment

### Key Design Patterns
1. **Strict Backend Abstraction**: Code outside of `xml/backends/` must **never** touch raw XML objects. It must operate solely through the `XmlBackend` interface. **Never import `xml.etree` or `lxml` outside of `xml/backends/`.**
2. **Handler Pattern**: Each TMX element type has a dedicated deserializer/serializer class
3. **Policy-Driven Validation**: Instead of raising exceptions unconditionally, policies let users configure behavior (raise/ignore/fallback)
4. **Recursive Dispatch**: `emit()` method delegates to orchestrator for nested elements

---

## 3. Code Conventions

### Naming
| Type | Convention | Example |
|------|-----------|---------|
| Files | snake_case | `deserialization/base.py` |
| Classes | PascalCase | `TuvDeserializer`, `XmlBackend` |
| Functions/methods | snake_case | `deserialize()`, `parse_attribute_as_int()` |
| Private methods | `_prefix` | `_deserialize()`, `_set_emit()` |
| Variables | snake_case | `backend`, `source_tuv` |
| Constants | UPPER_SNAKE | (rare, enums used instead) |
| Generics | TypeVar descriptive | `TypeOfElement`, `IterableOfProps` |

### Type Hints
**Strict typing enforced.** All public APIs, methods, and internal functions have full annotations.

```python
# dataclasses use field annotations
@dataclass(slots=True)
class Prop:
  text: str
  type: str
  lang: str | None = None

# Methods always annotated
def deserialize(self, element: TypeOfBackendElement) -> BaseElement | None:
  ...

# Generic type parameters
class BaseElementDeserializer[TypeOfBackendElement, TypeOfTmxElement: BaseElement](ABC):
  ...
```

**Type aliases** (in `base/types.py`):

| Alias | Expands To |
|-------|------------|
| `BaseElement` | `Tmx \| Header \| Prop \| Note \| Tu \| Tuv \| Bpt \| Ept \| It \| Ph \| Hi \| Sub` |
| `InlineElement` | `Bpt \| Ept \| It \| Ph \| Hi \| Sub` |

### Error Handling
**Policy-driven, not exception-driven.** Handlers check policies before raising:

```python
# Pattern: check policy, log, conditionally raise
if value is None:
  if self.logger:
    self.logger.log(self.policy.required_attribute_missing.log_level, "Missing attr %s", attr)
  if self.policy.required_attribute_missing.behavior == "raise":
    raise AttributeDeserializationError(f"Missing {attr}")
  return None  # or fallback value
```

Default behavior: strict (raise on any violation). Users can configure:
```python
policy = DeserializationPolicy(
  missing_seg=PolicyValue("ignore", logging.WARNING),
  extra_text=PolicyValue("ignore", logging.INFO),
)
```

**Error Message Format**: Include element tag and attribute/child name. Line numbers when available from backend.

### Logger Handling
All handlers accept optional logger. Pattern:
```python
if self.logger:
  self.logger.log(level, message, *args)
```
Never assume logger is present.

### Docstrings
**Lowest priority.** Only add after implementation is verified complete and only when explicitly requested.
**NumPy-style docstrings** for public APIs.

```python
def load(
  path: PathLike | str,
  filter: str | Collection[str] | None = None,
  *,
  encoding: str = "utf-8",
  policy: DeserializationPolicy | None = None,
  backend: XmlBackend | None = None,
  logger: Logger | None = None,
) -> Tmx | Generator[BaseElement]:
  """
  Load a TMX file from disk.

  Parameters
  ----------
  path : PathLike | str
      Path to the TMX file to load.
  filter : str | Collection[str] | None
      Optional tag filter for streaming parsing. Pass "tu" to yield
      translation units one at a time without loading entire file.

  Returns
  -------
  Tmx | Generator[BaseElement]
      If filter is None, returns complete Tmx object.
      If filter is specified, returns generator yielding matching elements.

  Examples
  --------
  >>> tmx = load("translations.tmx")
  >>> for tu in load("large.tmx", filter="tu"):
  >>>     print(tu.srclang)
  """
```

### Module Exports
Only export user-facing classes and functions via `__all__`. Internal helpers, base classes, and implementation details remain private.

```python
# Public API modules
__all__ = ["load", "save", "create_tu", "create_tuv"]

# Internal modules (handlers, backends)
# No __all__ or minimal exports for testing
```

### Import Organization
```python
# 1. Standard library
from dataclasses import dataclass, field
from datetime import datetime

# 2. Third-party (if any)
# (lxml only imported in backends/lxml.py)

# 3. Local relative imports
from hypomnema.base.types import Tmx, Tu
from hypomnema.xml.backends.base import XmlBackend

# __all__ at module top (after imports)
__all__ = ["Deserializer", "Serializer"]
```

---

## 4. Development Workflow

### Planning Process

**All code changes require a plan document before implementation** unless explicitly instructed to skip planning phase.

**Plan Document Requirements**:
- **Filename**: `PLAN.md` or feature-specific name (e.g., `PLAN_streaming_api.md`)
- **Location**: Project root or feature-specific subdirectory
- **Format**: Freeform markdown, structured for clarity
- **Content**: Describe problem, approach, files affected, edge cases, risks
- **Code**: Use snippets only when description is insufficient or when requested
- **Testing**: Always include test strategy and cases to cover

**Plan Scope**:
- New features/handlers → Plan required
- Breaking changes → Plan required
- Refactoring existing code → Plan required
- Bug fixes → Plan required
- Documentation updates → Plan not required

**Workflow**:
1. User requests change
2. AI outputs plan to PLAN.md
3. User reviews and approves/modifies plan
4. AI implements approved plan
5. AI writes tests per approved test strategy
6. User reviews implementation

**When Plan is Skipped**:
User explicitly instructs: "Skip planning, implement directly" or similar directive.

### Implementation Rules
- **No New Elements**: The spec implementation is complete. Do not create new dataclasses/handlers unless explicitly asked.
- **Backend Purity**: Any code interacting with XML must use `self.backend.method(element)`, never `element.method()`.
- **Dataclass Optimization**: All dataclasses must use `slots=True` for memory efficiency (significant for large TMX files with thousands of TUs).

### Adding a New TMX Element Handler
*(Only if explicitly requested. Consult existing handlers in `_handlers.py` as reference.)*

**Requirements**:
1. Dataclass in `base/types.py`
2. Deserializer in `xml/deserialization/_handlers.py`
3. Serializer in `xml/serialization/_handlers.py`
4. Registration in both orchestrators
5. Roundtrip tests
6. Policy handling for validation

### Testing Approach
- **Environment**: Virtual environment is active. `lxml` is always present.
- **Roundtrip tests**: `tests/xml/serialization/test_roundtrip.py`, `tests/xml/deserialization/test_roundtrip.py`
- **Handler tests**: `tests/xml/serialization/test_handlers.py`, `tests/xml/deserialization/test_handlers.py`
- **Fixtures**: `tests/conftest.py` provides sample TMX objects

Run tests:
```bash
pytest
pytest --cov=src/hypomnema --cov-report=term-missing
```

### Configuration Management
**No config files.** All configuration via constructor parameters:
```python
backend = StandardBackend(logger=custom_logger)
policy = DeserializationPolicy(missing_seg=PolicyValue("ignore", logging.INFO))
deserializer = Deserializer(backend, policy=policy, logger=logger)
```

### Logging Conventions
- Use `logger.log(level, message, *args)` with lazy formatting
- Policy objects define log levels per violation type
- Default logger names: `"XmlBackendLogger"`, `"hypomnema.api.load"`, etc.

### Common Code Patterns

**Mixed content handling (text + inline elements):**
```python
# Deserialization
content = []
if (text := self.backend.get_text(source)) is not None:
  content.append(text)
for child in self.backend.iter_children(source):
  child_obj = self.emit(child)
  if child_obj is not None:
    content.append(child_obj)
  if (tail := self.backend.get_tail(child)) is not None:
    content.append(tail)

# Serialization
last_child = None
for item in source.content:
  if isinstance(item, str):
    if last_child is None:
      self.backend.set_text(target, text + item)
    else:
      self.backend.set_tail(last_child, tail + item)
  else:
    child_elem = self.emit(item)
    self.backend.append_child(target, child_elem)
    last_child = child_elem
```

**Factory functions for creating objects:**
```python
# api/utils.py pattern
def create_tuv(lang: str, *, content: list[str | InlineElement] | None = None, **kwargs) -> Tuv:
  return Tuv(lang=lang, content=content or [], **kwargs)
```

---

## 5. Critical Implementation Details

### Handler Orchestration

**`emit()` must be set before use**. Handlers call `emit()` for recursive deserialization/serialization, but it is injected by the orchestrator. **Never call `_deserialize()` or `_serialize()` directly outside orchestrator context.**

```python
# Incorrect
handler._deserialize(element)

# Correct
handler.emit(element)  # dispatches to orchestrator
```

### XML Namespaces

TMX uses `xml:lang` attribute (namespace `http://www.w3.org/XML/1998/namespace`). Backends auto-register `xml` prefix. For other namespaces, use `backend.register_namespace()`.

### Attribute Name Mapping

Python identifiers cannot contain hyphens. Naming convention:
- `o-encoding` → `o_encoding`
- `xml:lang` → `lang` (special case, omit `xml:` prefix in Python)
- `o-tmf` → `o_tmf`

### Streaming API

Use `load(path, filter="tu")` to process large files without loading entire document into memory.

**Valid filter values**: Any TMX tag name (`"tu"`, `"tuv"`, `"prop"`, etc.)

**Return value**: Generator yielding elements matching filter tag.

**Backend behavior**: `iterparse()` clears yielded elements from memory. Do not keep references to parsed objects when streaming.

**Example**:
```python
# Memory-efficient processing of large TMX
for tu in load("large.tmx", filter="tu"):
  process(tu)
  # tu is cleared after this iteration
```

---

## 6. Edge Cases and Validation

### Policy-Driven Validation

Default behavior is strict (raise on any violation). Users configure tolerance per violation type.

**Common Policy Keys**:
- `missing_seg`: TUV without `<seg>` element
- `multiple_seg`: TUV with multiple `<seg>` elements (spec allows one)
- `extra_text`: Text content outside allowed locations
- `required_attribute_missing`: Missing required attribute

**Policy Defaults**: See `xml/policy.py` for complete list.

### Edge Cases That Must Be Handled

1. **Empty `<tuv>` without `<seg>`**: Policy `missing_seg` controls behavior (raise/ignore/create empty content)
2. **Multiple `<seg>` in `<tuv>`**: TMX 1.4b allows exactly one. Policy `multiple_seg` chooses which to keep (first/last/raise)
3. **BCP-47 language codes**: Not validated. Trust user input. Validation would require external dependency (incompatible with zero-dependency goal).
4. **Datetime format**: Must be ISO-8601 with 'Z' suffix. Python's `datetime.isoformat()` does not append 'Z' automatically; handlers must add it.
5. **Arbitrary inline nesting**: `<sub>` can contain `<bpt>` which contains `<sub>` recursively. Handlers must recurse correctly via `emit()`.

### Known Limitations

- **No BCP-47 validation**: Would require `langcodes` or similar dependency. Intentionally omitted to maintain zero-dependency core.
- **`<ude>` and `<map>` elements not implemented**: Rare in practice, TMX spec allows omitting them. Users can extend handlers if needed.
- **No DTD validation**: Would require `lxml` as mandatory dependency. Trade-off for zero-dependency core.

---

## 7. Performance and Security

### Performance Considerations

- **lxml is 3-5x faster** than stdlib for files over 10MB
- **Streaming reduces memory** from O(file size) to O(largest element)
- **`slots=True` reduces memory** by ~40% for dataclasses (matters at scale)

### Security Concerns

- **XML entity expansion attacks**: stdlib backend is safe by default. lxml backend configures `resolve_entities=False` for untrusted input (already done in `backends/lxml.py`).
- **Path traversal**: `make_usable_path()` in `xml/utils.py` normalizes paths before file operations.

---

## 8. AI Pair Programmer Guidelines

### Response to Ambiguity

When encountering ambiguous requirements, respond:
```
Ambiguity detected: [specific issue]. Clarify: [option A] or [option B]?
```

Do not make assumptions. Wait for explicit confirmation.

### Code Review Checklist

**Correctness**:
- [ ] **Strict Backend Usage**: Does NOT access `element.tag`, `element.attrib`, or any XML object methods directly
- [ ] **No Direct Imports**: Does NOT import `xml.etree` or `lxml` outside of `xml/backends/`
- [ ] Handles None values per policy
- [ ] Logs before raising exceptions (if logger present)
- [ ] Recursive `emit()` used (not direct `_deserialize()` or `_serialize()`)
- [ ] Mixed content (text/tail) handled correctly
- [ ] All dataclasses use `slots=True`
- [ ] Mutable defaults use `field(default_factory=...)`

**Readability**:
- [ ] Type hints on all signatures
- [ ] Docstrings for public APIs (if explicitly requested)
- [ ] Variable names clear and descriptive

**Performance**:
- [ ] No unnecessary loops over large collections
- [ ] Streaming API used for large files (when applicable)

### Preferred Explanation Style

- **Concrete examples** from existing code with file paths and line numbers
- **Minimal prose** — code snippets and diffs preferred
- **Diff format** for modifications:
  ```diff
  - old_code()
  + new_code()
  ```

### Common Errors to Prevent

- **Using `xml:lang` as Python identifier**: Use `lang` in dataclasses (namespace prefix omitted)
- **Direct XML access**: Always use `backend.get_tag(element)`, never `element.tag`
- **Missing `slots=True`**: All dataclasses must have `slots=True`
- **Mutable defaults**: Use `field(default_factory=list)`, never `= []`
- **Calling handler methods directly**: Use `emit()`, not `_deserialize()` or `_serialize()`
- **User input validation**: When users pass `content` parameter, validate it is list, not string

---

## 9. Quick Reference

### File Locations

| Task | File Path |
|------|-----------|
| Add dataclass | `src/hypomnema/base/types.py` |
| Add deserializer | `src/hypomnema/xml/deserialization/_handlers.py` |
| Add serializer | `src/hypomnema/xml/serialization/_handlers.py` |
| Modify policies | `src/hypomnema/xml/policy.py` |
| Public API changes | `src/hypomnema/__init__.py`, `src/hypomnema/api/core.py` |
| Backend interface | `src/hypomnema/xml/backends/base.py` |

### Class Hierarchy

```
BaseElementDeserializer (abstract)
├── TmxDeserializer
├── HeaderDeserializer
├── TuDeserializer
├── TuvDeserializer
└── [InlineElement]Deserializer (Bpt, Ept, It, Ph, Hi, Sub)

BaseElementSerializer (abstract)
├── TmxSerializer
├── HeaderSerializer
├── TuSerializer
├── TuvSerializer
└── [InlineElement]Serializer (Bpt, Ept, It, Ph, Hi, Sub)

XmlBackend (abstract)
├── StandardBackend (xml.etree.ElementTree)
└── LxmlBackend (lxml.etree)
```

### Key Imports

```python
# User-facing API
import hypomnema as hm
tmx = hm.load("file.tmx")
hm.save(tmx, "out.tmx")

# Internal handler development
from hypomnema.xml.deserialization.base import BaseElementDeserializer
from hypomnema.base.types import Tu, Tuv, InlineElement
from hypomnema.xml.utils import check_tag
```

### Python Version

- **Minimum**: 3.13 (uses PEP 695 generic syntax)
- **Target**: Latest stable Python 3.x

### Tooling

- **Package manager**: `uv`
- **Formatter**: ruff
- **Linter**: ruff
- **Test framework**: pytest
