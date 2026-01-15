# AGENTS.md

## Project Overview

**Hypomnema** is an industrial-grade TMX 1.4b parsing/serialization library for Python. Currently in early development (0.5.x) with a focus on the internal API (backends, data models, policies). The public convenience API will come later.

**Key Resources:**
- [TMX 1.4b Specification](https://resources.gala-global.org/tbx14b)
- Repository: https://github.com/EnzoAgosta/hypomnema
- Terminology Reference: [TERMINOLOGY.md](./TERMINOLOGY.md)

**API Stability:** LOW - Expect breaking changes without notice until version 1.x.x.

## Commands

### Building and Installation

```bash
uv sync                    # Install all dependencies including dev
uv sync --no-dev           # Install only runtime dependencies
```

### Linting and Formatting

```bash
uvx run ruff --config ./.ruff.toml check src/ tests/              # Lint all source and test files
uvx run ruff --config ./.ruff.toml format src/ tests/             # Format all files
uvx run ruff --config ./.ruff.toml check --fix src/ tests/        # Auto-fix linting issues
```

### Testing

```bash
pytest                    # Run all tests
pytest tests/file.py      # Run tests in specific file
pytest tests/file.py::TestClassName::test_method  # Run single test
pytest -v                 # Verbose output
pytest -x                 # Stop on first failure
```

**Backend Parameterization:** Tests use the `backend` fixture from `conftest.py` which runs against `StandardBackend`, `LxmlBackend`, and `StrictBackend` automatically. `StrictBackend` compliance is mandatory.

## Code Style

### Imports

```python
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from hypomnema.xml.backends.standard import StandardBackend
```

- Standard library first, then third-party, then local
- Use absolute imports for package modules
- Sort imports within each group alphabetically
- Use `__all__` to define public API exports

### Formatting

- **Line length:** 100 characters
- **Indent width:** 2 spaces
- **Quotes:** Double quotes (`"`) for strings
- Use ruff for automatic formatting: `uvx run ruff --config ./.ruff.toml format <files>`

### Types

- Use modern Python type syntax (3.14+)
- Use `list`/`tuple` directly, NOT `List`/`Tuple` from `typing`
- Use new generic syntax: `class Foo[T]`
- Use `type Alias = ...` for type aliases
- Use `slots=True` on all dataclasses
- Add type annotations (user refines them later with `ty` tool)

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `StandardBackend`, `DeserializationPolicy`)
- **Functions/methods:** `snake_case` (e.g., `deserialize()`, `_default()`)
- **Constants:** `SCREAMING_SNAKE_CASE` (e.g., `DEFAULT_LOG_LEVEL`)
- **Private methods:** Leading underscore (e.g., `_validate_attrs()`)
- **Type aliases:** `PascalCase` (e.g., `InlineElementAndStr`)

### Error Handling

- Use custom exceptions from `hypomnema.base.errors`
- Policy violations use `PolicyValue` with `Literal["raise", "ignore", ...]` behaviors
- Never silently ignore errors without explicit policy configuration
- Log at appropriate level before executing policy behavior

### Dataclasses

```python
@dataclass(slots=True)
class PolicyValue[Behavior: str]:
    behavior: Behavior
    log_level: int

@dataclass(slots=True, kw_only=True)
class DeserializationPolicy:
    missing_handler: PolicyValue[...] = _default("raise")
```

- Always use `slots=True` for memory efficiency
- Use `kw_only=True` for configuration classes
- Use `field(default_factory=...)` for mutable defaults
- Define `_default()` helper for consistent policy field initialization

### Enums

```python
class Segtype(StrEnum):
    """Segmentation level per TMX 1.4b spec."""
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
```

- Use `StrEnum` for string-based enums (values are actual strings)
- Add docstrings to enum classes

## Type Checking

The project uses a custom type checker called `ty` (not mypy/pyright):
- Focus on logical correctness over type annotation perfection
- Proceed with implementation if confident, even if LSP shows type warnings
- Let the user handle type annotation refinements

## Testing Guidelines

- **Structure:** `Test<Name>Happy` for valid paths, `Test<Name>Error` for exceptions
- **Backend fixture:** Always use `backend` fixture from `conftest.py` for tests that use a backend
- **Policy tests:** Mutate policy in-place (`serializer.policy.rule = ...`) not create new instances
- **Logging:** Use `test_logger` fixture for test logging

## Common Pitfalls

1. **Generic type handling:** Complex generics like `Tuv[list[Prop], list[Note], list[InlineElementAndStr]]`. Read `base/types.py` first.

2. **Policy system:** `policy.py` has `PolicyValue` wrappers for all behaviors. Understand before modifying error handling.

3. **Backend abstraction:** Two backends - `StandardBackend` (stdlib) and `LxmlBackend` (lxml). Read `xml/backends/base.py` before modifying interface.

## Dependencies

- **Core:** No required dependencies (stdlib `xml.etree`)
- **Optional:** `lxml>=6.0.2` for performance (`LxmlBackend`)
- **Dev:** pytest, pytest-cov, pytest-mock, types-lxml
- **Never add dependencies without explicit approval**

## What Not To Do

- Add docstrings to generated code (use NumPy-style)
- Generate or run tests unless explicitly requested
- Add external dependencies without approval
- Use libraries not in `pyproject.toml`
- Bypass the backend abstraction layer in handlers
- Use `typing.List`/`typing.Tuple` (use built-in types instead)
