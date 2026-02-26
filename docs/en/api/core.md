---
title: Core API
---

# Core API

The `load()` and `dump()` functions are the main entry points for working with TMX files.

## load()

Load a TMX file into Python objects.

### Signature

```python
def load(
    path: str | PathLike,
    filter: str | None = None,
    encoding: str | None = None,
    **kwargs: Unpack[LoadOptions],
) -> Tmx | Generator[BaseElement]
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| PathLike` | required | Path to the TMX file |
| `filter` | `str \| None` | `None` | Tag filter for streaming (e.g., `"tu"`) |
| `encoding` | `str \| None` | `"utf-8"` | Character encoding |

### LoadOptions

| Option | Type | Description |
|--------|------|-------------|
| `backend` | `XmlBackend` | Custom XML backend |
| `backend_logger` | `Logger` | Logger for backend operations |
| `nsmap` | `Mapping[str, str]` | Custom namespace mappings |
| `namespace_handler` | `NamespaceHandler` | Custom namespace handler |
| `deserializer` | `Deserializer` | Custom deserializer |
| `deserializer_policy` | `XmlDeserializationPolicy` | Error handling policy |
| `deserializer_logger` | `Logger` | Logger for deserialization |

### Returns

- If `filter` is `None`: Returns a `Tmx` object
- If `filter` is set: Returns a `Generator[BaseElement]`

### Raises

| Exception | When |
|-----------|------|
| `FileNotFoundError` | File does not exist |
| `IsADirectoryError` | Path is a directory |
| `ValueError` | Root element is not `<tmx>` |
| Various deserialization errors | Per policy configuration |

### Examples

```python
import hypomnema as hm

# Load entire file
tmx = hm.load("translations.tmx")

# Stream translation units (memory efficient)
for tu in hm.load("large.tmx", filter="tu"):
    process(tu)

# Custom encoding
tmx = hm.load("legacy.tmx", encoding="utf-16")

# Lenient error handling
from hypomnema import policy
tmx = hm.load(
    "messy.tmx",
    deserializer_policy=policy.XmlDeserializationPolicy(
        missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE),
    ),
)
```

---

## dump()

Save a TMX object to a file.

### Signature

```python
def dump(
    tmx: Tmx,
    path: PathLike | str,
    encoding: str | None = None,
    **kwargs: Unpack[DumpOptions],
) -> None
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tmx` | `Tmx` | required | The TMX object to save |
| `path` | `str \| PathLike` | required | Output file path |
| `encoding` | `str \| None` | `"utf-8"` | Character encoding |

### DumpOptions

| Option | Type | Description |
|--------|------|-------------|
| `backend` | `XmlBackend` | Custom XML backend |
| `serializer` | `Serializer` | Custom serializer |
| `serializer_policy` | `XmlSerializationPolicy` | Error handling policy |
| `serializer_logger` | `Logger` | Logger for serialization |

### Raises

| Exception | When |
|-----------|------|
| `TypeError` | `tmx` is not a `Tmx` instance |
| `ValueError` | Serialization fails |
| `OSError` | Cannot write to path |

### Examples

```python
import hypomnema as hm

# Basic save
hm.dump(tmx, "output.tmx")

# Custom encoding
hm.dump(tmx, "output.tmx", encoding="utf-16")

# Parent directories are created automatically
hm.dump(tmx, "deeply/nested/output.tmx")
```

## See Also

- [Helpers](/en/api/helpers) — Factory functions for creating TMX objects
- [Backends](/en/api/backends/) — XML parsing options
- [Policy](/en/api/policy/) — Error handling configuration
