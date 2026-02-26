---
title: Policy Overview
---

# Policy

Policy-driven error handling for deserialization and serialization.

## Philosophy

Instead of raising exceptions unconditionally, policies let you configure how hypomnema responds to various error conditions:

- **RAISE** — Raise an exception (strict)
- **IGNORE** — Skip silently
- **NONE** — Use `None` as the value
- **KEEP** — Keep original value
- **DEFAULT** — Use a default value

## Behavior Class

```python
@dataclass(frozen=True, slots=True)
class Behavior[T: ActionEnum]:
    action: T
    log_level: int | None = None
```

Each policy option is a `Behavior` combining an action with an optional log level.

```python
from hypomnema import policy

behavior = policy.Behavior(
    policy.RaiseIgnore.IGNORE,
    logging.WARNING,  # Log at WARNING level
)
```

## Action Enums

| Enum | Actions |
|------|---------|
| `RaiseIgnore` | `RAISE`, `IGNORE` |
| `RaiseNoneKeep` | `RAISE`, `NONE`, `KEEP` |
| `RaiseIgnoreDefault` | `RAISE`, `IGNORE`, `DEFAULT` |
| `DuplicateChildAction` | `RAISE`, `KEEP_FIRST`, `KEEP_LAST` |
| `RaiseIgnoreOverwrite` | `RAISE`, `IGNORE`, `OVERWRITE` |
| `RaiseIgnoreDelete` | `RAISE`, `IGNORE`, `DELETE` |
| `RaiseIgnoreForce` | `RAISE`, `IGNORE`, `FORCE` |

## Sections

- [Deserialization Policy](/en/api/policy/deserialization) — XML parsing error handling
- [Serialization Policy](/en/api/policy/serialization) — Object-to-XML error handling
