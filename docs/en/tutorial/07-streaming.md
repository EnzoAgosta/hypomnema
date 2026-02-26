---
title: Streaming Large Files
---

# Streaming Large Files

Processing large TMX files (hundreds of megabytes or more) can exhaust memory if you load the entire file at once. Hypomnema provides streaming to process files efficiently.

## The Problem

```python
# DON'T do this with large files
tmx = hm.load("huge.tmx")  # Loads everything into memory
for tu in tmx.body:
    process(tu)
```

For a 500 MB TMX file, this could require several GB of RAM.

## The Solution: Streaming

Use the `filter` parameter to process TUs one at a time:

```python
# DO this instead
for tu in hm.load("huge.tmx", filter="tu"):
    process(tu)
    # tu is freed from memory after each iteration
```

This keeps memory usage constant regardless of file size.

## How It Works

With `filter="tu"`:

1. The parser reads the file incrementally
2. When it encounters a `<tu>` element, it deserializes it
3. The TU is yielded to your code
4. After processing, the TU is discarded
5. Memory is freed before reading the next TU

## Available Filters

You can filter by any TMX element tag:

```python
# Stream translation units
for tu in hm.load("file.tmx", filter="tu"):
    ...

# Stream TUVs (variants)
for tuv in hm.load("file.tmx", filter="tuv"):
    ...

# Stream properties
for prop in hm.load("file.tmx", filter="prop"):
    ...
```

## Important Limitations

**Don't keep references to streamed objects:**

```python
# WRONG: Keeps all TUs in memory
all_tus = list(hm.load("huge.tmx", filter="tu"))

# RIGHT: Process and discard
for tu in hm.load("huge.tmx", filter="tu"):
    save_to_database(tu)
```

**You can't access the header:**

When streaming, you only get the filtered elements. The header is not accessible. If you need header info, parse it first:

```python
# Two-pass approach for large files
# Pass 1: Get header info (fast, doesn't load body)
from xml.etree import ElementTree as ET
tree = ET.parse("huge.tmx")
srclang = tree.find("header").get("srclang")

# Pass 2: Stream TUs
for tu in hm.load("huge.tmx", filter="tu"):
    process(tu, srclang=srclang)
```

## Combining with Other Operations

Streaming works well with filtering and transformation:

```python
# Extract specific language pairs
for tu in hm.load("huge.tmx", filter="tu"):
    if tu.srclang == "en":
        for tuv in tu.variants:
            if tuv.lang == "fr":
                export_pair(tu, tuv)
```

## Next Steps

Now you can handle files of any size. Next, let's learn about [error handling](/en/tutorial/08-error-handling).
