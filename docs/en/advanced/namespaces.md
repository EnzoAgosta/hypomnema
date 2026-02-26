---
title: Namespaces
---

# Namespaces

Advanced namespace handling in TMX files.

## TMX and Namespaces

TMX uses one standard namespace:

- `xml:lang` — Language attribute (namespace: `http://www.w3.org/XML/1998/namespace`)

Custom namespaces may appear in proprietary extensions.

## NamespaceHandler

The `NamespaceHandler` class manages namespace prefixes:

```python
from hypomnema.backends import NamespaceHandler

handler = NamespaceHandler(
    nsmap={"xml": "http://www.w3.org/XML/1998/namespace"},
)
```

### Methods

```python
class NamespaceHandler:
    def register(self, prefix: str, uri: str) -> None: ...
    def resolve(self, prefix: str) -> str | None: ...
    def get_qname(self, local: str, prefix: str | None = None) -> str: ...
    def parse_qname(self, qname: str) -> tuple[str | None, str]: ...
```

## Registering Custom Namespaces

```python
from hypomnema import load, backends

ns_handler = backends.NamespaceHandler()
ns_handler.register("memoq", "http://www.memoq.com/tmx")
ns_handler.register("sdl", "http://sdl.com/tmx")

backend = backends.LxmlBackend(namespace_handler=ns_handler)

tmx = load("proprietary.tmx", backend=backend)
```

## The nsmap Parameter

Provide a namespace map when loading:

```python
tmx = load(
    "file.tmx",
    nsmap={
        "xml": "http://www.w3.org/XML/1998/namespace",
        "memoq": "http://www.memoq.com/tmx",
    },
)
```

## Handling xml:lang

The `xml:lang` attribute is handled automatically:

```python
# In XML
<tuv xml:lang="en">

# In Python
tuv.lang  # "en" (not "xml:lang")
```

When serializing, `lang` becomes `xml:lang` automatically.

## Namespace-Aware Filtering

When streaming, use qualified names if filtering namespaced elements:

```python
# Filter by local name (works for most cases)
for prop in load("file.tmx", filter="prop"):
    ...

# For namespaced elements, check with backend
backend = backends.LxmlBackend()
tags = backend.prep_tag_set(["{http://custom.ns}prop"])
```

## Policy for Namespaces

```python
from hypomnema import policy

ns_policy = policy.NamespacePolicy(
    existing_namespace=policy.Behavior(policy.RaiseIgnoreOverwrite.OVERWRITE),
    inexistent_namespace=policy.Behavior(policy.RaiseIgnore.RAISE),
)
```

| Option | Default | Description |
|--------|---------|-------------|
| `existing_namespace` | `RAISE` | When registering an existing prefix |
| `inexistent_namespace` | `RAISE` | When resolving an unregistered prefix |

## See Also

- [Backends](/en/api/backends/)
- [Policy](/en/api/policy/)
