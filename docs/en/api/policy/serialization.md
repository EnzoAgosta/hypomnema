---
title: Serialization Policy
---

# XmlSerializationPolicy

Controls error handling during object-to-XML conversion.

## Class

```python
@dataclass(slots=True, kw_only=True, frozen=True)
class XmlSerializationPolicy:
    # All options with defaults...
```

## Policy Options

### Elements

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `invalid_element_type` | `RAISE` | RaiseIgnoreForce | Unexpected object type |
| `invalid_child_element` | `RAISE` | RaiseIgnore | Invalid child element type |

### Attributes

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `required_attribute_missing` | `RAISE` | RaiseIgnore | Missing required attribute |
| `invalid_attribute_type` | `RAISE` | RaiseIgnore | Wrong attribute type |

### Text Content

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `missing_text_content` | `RAISE` | RaiseIgnoreDefault | Missing required text |

### Handlers

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `missing_serialization_handler` | `RAISE` | RaiseIgnoreDefault | No handler for type |

## Usage

### Strict Mode (Default)

```python
from hypomnema import dump

dump(tmx, "output.tmx")  # Raises on any violation
```

### Lenient Mode

```python
from hypomnema import dump, policy

lenient = policy.XmlSerializationPolicy(
    missing_text_content=policy.Behavior(policy.RaiseIgnoreDefault.DEFAULT),
)

dump(tmx, "output.tmx", serializer_policy=lenient)
```

### With Logging

```python
import logging

logger = logging.getLogger("hypomnema.serializer")
lenient = policy.XmlSerializationPolicy(
    invalid_attribute_type=policy.Behavior(policy.RaiseIgnore.IGNORE, logging.WARNING),
)

dump(tmx, "output.tmx", serializer_policy=lenient, serializer_logger=logger)
```

## See Also

- [Deserialization Policy](/en/api/policy/deserialization)
- [Core API: dump](/en/api/core#dump)
