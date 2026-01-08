# AI Pair Programmer Context: hypomnema

**Python TMX 1.4b library | Zero runtime deps | Backend-agnostic | Policy-driven error handling**

**Hypomnema** is an industrial-grade TMX 1.4b parsing/serialization library for Python. Currently in early development (0.4.x) with a focus on the internal API (backends, data models, policies). The public convenience API will come later.

## Working Style
- **Response style**: Terse, to the point, maximal clarity
- **Code review priority**: Correctness → Readability → Performance → Documentation (last)
- **When uncertain**: Ask first
- **Planning**: Output plan → await approval → implement

## Development Status

**API Stability:** LOW - Expect breaking changes without notice until version 1.x.x or explicit stabilization.

**Before using any function or class, agents must:**
1. Read the current implementation to understand the actual API
2. Verify parameter names, return types, and behavior match expectations
3. Check `pyproject.toml` for current Python version requirements

**Runtime**:
- **Core**: None (uses stdlib xml.etree)
- **Optional**: `lxml>=6.0.2` (faster parsing, better namespace handling)

**Do:**
- Use latest Python features (targeting 3.14+)
- Use `list`/`tuple` directly, not `List`/`Tuple` from `typing`
- Use new generic syntax (e.g., `class Foo[T]`)
- Use `type Alias = ...` for type aliases
- Use `slots=True` on dataclasses (follow existing patterns)
- Add type annotations (user will refine them later with `ty` tool)

**Don't:**
- Add docstrings to generated code (user adds NumPy-style docstrings later)
- Generate tests unless explicitly requested
- Add external dependencies without prior approval
- Use external libraries not already in `pyproject.toml`

```python
# Public API modules
__all__ = ["load", "save", "create_tu", "create_tuv"]

The project uses a custom type checker called `ty` (not mypy/pyright). Agents should:
- Focus on logical correctness over type annotation perfection
- Proceed with implementation if confident, even if LSP shows type warnings
- Let the user handle type annotation refinements

## Testing

**Do NOT run tests automatically** - testing infrastructure is not fully built yet.

When tests are requested:
- Use `pytest`
- Leverage parameterization for comprehensive coverage
- Follow existing test patterns in `tests/`

### Planning Process

- **Core:** No required dependencies (works with stdlib `xml.etree`)
- **Optional:** `lxml>=6.0.2` for performance (use `LxmlBackend`)
- **Never add new dependencies without explicit approval**

## Common Pitfalls

1. **Generic type handling:** The data models use complex generics (e.g., `Tuv[list[Prop], list[Note], list[InlineElementAndStr]]`). Always read `base/types.py` before modifying.

2. **Policy system:** `policy.py` defines `DeserializationPolicy` and `SerializationPolicy` with `PolicyValue` wrappers. Understand this before touching error handling.

3. **Backend abstraction:** Two backends exist - `StandardBackend` (stdlib) and `LxmlBackend` (lxml). Read `xml/backends/base.py` before modifying backend interface.

4. **TMX 1.4b quirks:** Note, Prop, and other elements support optional `lang` and `o_encoding` attributes. Always verify against the spec.
