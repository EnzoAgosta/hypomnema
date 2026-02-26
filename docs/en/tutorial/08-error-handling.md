---
title: Error Handling
---

# Error Handling

TMX files in the wild often contain irregularities: missing attributes, malformed dates, unexpected elements. Hypomnema uses a policy-driven approach to handle these situations.

## The Default: Strict Mode

By default, hypomnema raises exceptions on any violation:

```python
import hypomnema as hm

# This raises an exception if the file has issues
tmx = hm.load("malformed.tmx")
```

## Configuring Policies

Policies let you control what happens when issues are encountered:

```python
from hypomnema import policy, load

# Be lenient with malformed data
lenient_policy = policy.XmlDeserializationPolicy(
    missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE),
    invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.NONE),
    extra_text=policy.Behavior(policy.RaiseIgnore.IGNORE),
)

tmx = load("messy.tmx", deserializer_policy=lenient_policy)
```

## Available Behaviors

Each policy option uses an "action" enum:

| Action | Effect |
|--------|--------|
| `RAISE` | Raise an exception (default for most) |
| `IGNORE` | Skip the problem silently |
| `NONE` | Use `None` as the value |
| `KEEP` | Keep the original (string) value |
| `DEFAULT` | Use a default value |

## Common Policy Options

### Missing `<seg>` in `<tuv>`

```python
missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE)
```

A TUV without a `<seg>` element will have an empty `content` list instead of raising.

### Invalid Datetime Values

```python
invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.NONE)
```

Malformed dates become `None` instead of raising.

### Extra Text Content

```python
extra_text=policy.Behavior(policy.RaiseIgnore.IGNORE)
```

Text in unexpected locations is ignored.

### Multiple `<seg>` Elements

```python
multiple_seg=policy.Behavior(policy.DuplicateChildAction.KEEP_FIRST)
```

When a TUV has multiple `<seg>` elements, keep the first one.

## Logging

You can enable logging to see what issues were encountered:

```python
import logging

logger = logging.getLogger("hypomnema")
logger.setLevel(logging.DEBUG)

tmx = load("file.tmx", deserializer_logger=logger)
```

## Full Example: Lenient Loading

```python
from hypomnema import policy, load, deserialization
import logging

logger = logging.getLogger("my-loader")
logger.setLevel(logging.WARNING)

lenient_policy = policy.XmlDeserializationPolicy(
    missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE, logging.WARNING),
    invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.NONE, logging.INFO),
    invalid_int_value=policy.Behavior(policy.RaiseNoneKeep.NONE, logging.INFO),
    extra_text=policy.Behavior(policy.RaiseIgnore.IGNORE, logging.DEBUG),
)

tmx = load(
    "legacy.tmx",
    deserializer_policy=lenient_policy,
    deserializer_logger=logger,
)
```

## Next Steps

Now you can handle any TMX file, even malformed ones. Next, let's learn about [backends](/en/tutorial/09-backends).
