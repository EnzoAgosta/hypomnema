---
title: Deserialization Policy
---

# XmlDeserializationPolicy

Controls error handling during XML-to-object conversion.

## Class

```python
@dataclass(slots=True, kw_only=True, frozen=True)
class XmlDeserializationPolicy:
    # All options with defaults...
```

## Policy Options

### Child Elements

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `invalid_child_tag` | `RAISE` | RaiseIgnore | Unexpected child element |
| `multiple_seg` | `RAISE` | DuplicateChildAction | Multiple `<seg>` in `<tuv>` |
| `multiple_headers` | `RAISE` | DuplicateChildAction | Multiple `<header>` elements |
| `multiple_body` | `RAISE` | DuplicateChildAction | Multiple `<body>` elements |
| `missing_header` | `RAISE` | RaiseIgnore | No `<header>` in `<tmx>` |
| `missing_body` | `RAISE` | RaiseIgnore | No `<body>` in `<tmx>` |
| `missing_seg` | `RAISE` | RaiseIgnore | No `<seg>` in `<tuv>` |

### Attributes

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `required_attribute_missing` | `RAISE` | RaiseIgnore | Missing required attribute |

### Text Content

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `missing_text_content` | `RAISE` | RaiseIgnore | Element missing required text |
| `extra_text` | `RAISE` | RaiseIgnore | Unexpected text content |

### Value Parsing

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `invalid_datetime_value` | `RAISE` | RaiseNoneKeep | Unparsable datetime |
| `invalid_enum_value` | `RAISE` | RaiseNoneKeep | Invalid enum value |
| `invalid_int_value` | `RAISE` | RaiseNoneKeep | Unparsable integer |

### Handlers

| Option | Default | Actions | Description |
|--------|---------|---------|-------------|
| `invalid_tag` | `RAISE` | RaiseIgnoreForce | Unexpected element tag |
| `missing_deserialization_handler` | `RAISE` | RaiseIgnoreDefault | No handler for element type |

## Usage

### Strict Mode (Default)

```python
from hypomnema import load

tmx = load("file.tmx")  # Raises on any violation
```

### Lenient Mode

```python
from hypomnema import load, policy
import logging

lenient = policy.XmlDeserializationPolicy(
    missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE),
    invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.NONE),
    extra_text=policy.Behavior(policy.RaiseIgnore.IGNORE, logging.WARNING),
)

tmx = load("messy.tmx", deserializer_policy=lenient)
```

### With Logging

```python
import logging

logger = logging.getLogger("hypomnema.deserializer")
logger.setLevel(logging.DEBUG)

lenient = policy.XmlDeserializationPolicy(
    missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE, logging.WARNING),
)

tmx = load("file.tmx", deserializer_policy=lenient, deserializer_logger=logger)
```

## Common Configurations

### Ignore All Issues

```python
ignore_all = policy.XmlDeserializationPolicy(
    invalid_child_tag=policy.Behavior(policy.RaiseIgnore.IGNORE),
    missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE),
    invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.NONE),
    invalid_enum_value=policy.Behavior(policy.RaiseNoneKeep.NONE),
    invalid_int_value=policy.Behavior(policy.RaiseNoneKeep.NONE),
    extra_text=policy.Behavior(policy.RaiseIgnore.IGNORE),
    required_attribute_missing=policy.Behavior(policy.RaiseIgnore.IGNORE),
)
```

### Keep Invalid Values

```python
keep_invalid = policy.XmlDeserializationPolicy(
    invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.KEEP),
    invalid_enum_value=policy.Behavior(policy.RaiseNoneKeep.KEEP),
)
# Datetimes and enums stay as strings when invalid
```

### Handle Duplicates

```python
handle_duplicates = policy.XmlDeserializationPolicy(
    multiple_seg=policy.Behavior(policy.DuplicateChildAction.KEEP_FIRST),
    multiple_headers=policy.Behavior(policy.DuplicateChildAction.KEEP_FIRST),
)
```

## See Also

- [Serialization Policy](/en/api/policy/serialization)
- [Tutorial: Error Handling](/en/tutorial/08-error-handling)
