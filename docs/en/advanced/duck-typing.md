---
title: Duck Typing
---

# Duck Typing

Hypomnema supports duck typing via protocol classes, allowing you to use custom dataclasses while maintaining type safety.

## Protocol Classes

Hypomnema defines protocol classes for all major types:

```python
from hypomnema.base.types import (
    TmxLike, HeaderLike, TuLike, TuvLike,
    PropLike, NoteLike,
    BptLike, EptLike, ItLike, PhLike, HiLike, SubLike,
)
```

These protocols define the required attributes and types for each element.

## Why Use Protocols?

### Custom Dataclasses

Create your own dataclasses that work with hypomnema:

```python
from dataclasses import dataclass, field
from hypomnema.base.types import TuvLike

@dataclass
class MyTuv:
    """Custom TUV with additional fields."""
    lang: str
    content: list[str]
    
    # Additional fields not in standard Tuv
    confidence: float = 1.0
    source: str = "manual"
    
    # Optional fields with defaults
    creationid: str | None = None
    creationdate: datetime | None = None
    # ... other optional fields
```

### Type Checking

Protocols work with static type checkers:

```python
from hypomnema.base.types import TuvLike

def process_tuv(tuv: TuvLike) -> str:
    return "".join(tuv.content)

# Type checker accepts MyTuv
result = process_tuv(MyTuv(lang="en", content=["Hello"]))
```

### Using with dump()

Custom classes work with serialization:

```python
from hypomnema import dump, helpers

# Create TMX with custom TUV
tmx = helpers.create_tmx(
    body=[
        helpers.create_tu(
            variants=[
                MyTuv(lang="en", content=["Hello"], confidence=0.9),
                MyTuv(lang="fr", content=["Bonjour"], confidence=0.95),
            ],
        ),
    ],
)

dump(tmx, "output.tmx")  # Works!
```

## Protocol Requirements

Each protocol defines required and optional attributes:

### TuvLike Example

```python
@runtime_checkable
class TuvLike(Protocol):
    # Required
    lang: str
    
    # Optional (with defaults in Tuv)
    o_encoding: str | None
    datatype: str | None
    usagecount: int | None
    lastusagedate: datetime | None
    # ... more optional fields
    
    props: Sequence[PropLike]
    notes: Sequence[NoteLike]
    content: Sequence[str | BptLike | EptLike | ItLike | PhLike | HiLike]
```

Your class must provide at least the required attributes. Optional attributes can be omitted.

## Runtime Checking

Protocols are `@runtime_checkable`:

```python
from hypomnema.base.types import TuvLike

tuv = MyTuv(lang="en", content=["Hello"])
print(isinstance(tuv, TuvLike))  # True
```

## Limitations

### Serialization Ignores Extra Fields

When serializing, extra fields on custom classes are ignored:

```python
tuv = MyTuv(lang="en", content=["Hello"], confidence=0.9)
# confidence is NOT written to TMX (not in protocol)
```

### Required Defaults

For optional protocol fields, provide defaults matching the standard class:

```python
@dataclass
class MyTuv:
    lang: str
    content: list[str]
    
    # Match Tuv defaults
    props: list[Prop] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    o_encoding: str | None = None
```

## Creating Compatible Classes

Full example:

```python
from dataclasses import dataclass, field
from datetime import datetime
from hypomnema.base.types import TuvLike, PropLike, NoteLike

@dataclass
class MyProp:
    text: str
    type: str
    lang: str | None = None
    o_encoding: str | None = None

@dataclass
class MyNote:
    text: str
    lang: str | None = None
    o_encoding: str | None = None

@dataclass
class MyTuv:
    lang: str
    content: list[str]
    
    o_encoding: str | None = None
    datatype: str | None = None
    usagecount: int | None = None
    lastusagedate: datetime | None = None
    creationtool: str | None = None
    creationtoolversion: str | None = None
    creationdate: datetime | None = None
    creationid: str | None = None
    changedate: datetime | None = None
    changeid: str | None = None
    o_tmf: str | None = None
    props: list[MyProp] = field(default_factory=list)
    notes: list[MyNote] = field(default_factory=list)
```

## See Also

- [Custom Handlers](/en/advanced/custom-handlers) — For full control over (de)serialization
