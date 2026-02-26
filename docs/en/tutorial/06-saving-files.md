---
title: Saving Files
---

# Saving Files

Once you've created or modified a TMX document, save it with `dump()`.

## Basic Saving

```python
import hypomnema as hm

tmx = hm.helpers.create_tmx(...)

hm.dump(tmx, "output.tmx")
```

## Encoding

By default, files are saved as UTF-8. Specify a different encoding if needed:

```python
hm.dump(tmx, "output.tmx", encoding="utf-16")
```

## Pretty Printing

The XML output is formatted with indentation for readability. This is handled automatically by the serialization backend.

## Appending to Existing Files

If you want to add TUs to an existing file, load it, modify the body, and save:

```python
tmx = hm.load("existing.tmx")

# Add new translation units
tmx.body.extend([
    hm.helpers.create_tu(...),
    hm.helpers.create_tuv(...),
])

hm.dump(tmx, "existing.tmx")  # Overwrites
```

## Creating Parent Directories

If the output path doesn't exist, parent directories are created automatically:

```python
hm.dump(tmx, "output/subdir/translations.tmx")
# Creates output/subdir/ if needed
```

## Serialization Options

For advanced control, you can pass a custom serializer:

```python
from hypomnema import serialization, policy

serializer = serialization.Serializer(
    policy=policy.XmlSerializationPolicy(
        # Configure behavior...
    ),
)

hm.dump(tmx, "output.tmx", serializer=serializer)
```

See [API Reference: Serialization Policy](/en/api/policy/serialization) for details.

## Next Steps

Now you can save TMX files. Next, let's learn about [streaming large files](/en/tutorial/07-streaming) for memory-efficient processing.
