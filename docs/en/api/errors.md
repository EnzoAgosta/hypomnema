---
title: Errors
---

# Errors

Exception hierarchy for hypomnema.

## Base Exception

```python
class HypomnemaError(Exception):
    """Base exception for all hypomnema errors."""
```

## Deserialization Errors

```python
class DeserializationError(HypomnemaError):
    """Base for deserialization errors."""


class ElementDeserializationError(DeserializationError):
    """Error deserializing an element."""


class AttributeDeserializationError(DeserializationError):
    """Error deserializing an attribute."""
```

## Serialization Errors

```python
class SerializationError(HypomnemaError):
    """Base for serialization errors."""


class ElementSerializationError(SerializationError):
    """Error serializing an element."""


class AttributeSerializationError(SerializationError):
    """Error serializing an attribute."""
```

## Backend Errors

```python
class BackendError(HypomnemaError):
    """Base for backend errors."""


class ParseError(BackendError):
    """Error parsing XML."""


class WriteError(BackendError):
    """Error writing XML."""
```

## Policy Errors

```python
class PolicyError(HypomnemaError):
    """Error in policy configuration."""
```

## When Exceptions Are Raised

| Exception | When Raised |
|-----------|-------------|
| `ParseError` | Malformed XML |
| `ElementDeserializationError` | Invalid element structure |
| `AttributeDeserializationError` | Invalid/missing attribute |
| `ElementSerializationError` | Cannot serialize object |
| `AttributeSerializationError` | Invalid attribute value |

## Exception Messages

All exceptions include:

- Element tag (when applicable)
- Attribute name (when applicable)
- Brief description of the issue

```python
try:
    tmx = load("invalid.tmx")
except ElementDeserializationError as e:
    print(e)  # "Error deserializing <tuv>: missing required attribute 'lang'"
```

## Catching Specific Errors

```python
from hypomnema import errors

try:
    tmx = load("file.tmx")
except errors.ParseError:
    print("XML is malformed")
except errors.AttributeDeserializationError:
    print("Missing or invalid attribute")
except errors.DeserializationError:
    print("General deserialization error")
```

## Policy-Driven Exceptions

Many exceptions can be suppressed via policies:

```python
from hypomnema import policy

lenient = policy.XmlDeserializationPolicy(
    required_attribute_missing=policy.Behavior(policy.RaiseIgnore.IGNORE),
)

tmx = load("file.tmx", deserializer_policy=lenient)  # Won't raise for missing attrs
```

## See Also

- [Deserialization Policy](/en/api/policy/deserialization)
- [Tutorial: Error Handling](/en/tutorial/08-error-handling)
