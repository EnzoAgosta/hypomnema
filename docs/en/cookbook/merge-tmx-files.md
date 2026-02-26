---
title: Merge TMX Files
---

# Merge TMX Files

Combine multiple TMX files into a single translation memory.

## Problem

You have several TMX files from different sources and want to merge them into one.

## Solution

```python
import hypomnema as hm
from pathlib import Path

def merge_tmx(files: list[str], output_path: str, source_lang: str = "en"):
    """Merge multiple TMX files into one."""
    all_tus = []
    first_header = None
    
    for file_path in files:
        tmx = hm.load(file_path)
        
        if first_header is None:
            first_header = tmx.header
        
        all_tus.extend(tmx.body)
    
    # Create merged TMX with first file's header
    merged = hm.helpers.create_tmx(
        header=first_header or hm.helpers.create_header(srclang=source_lang),
        body=all_tus,
    )
    
    hm.dump(merged, output_path)

# Usage
merge_tmx(
    ["project_a.tmx", "project_b.tmx", "project_c.tmx"],
    "merged.tmx",
)
```

## Deduplication

Remove duplicate translation units:

```python
def merge_deduplicate(files: list[str], output_path: str):
    """Merge TMX files, removing duplicates."""
    seen = set()
    unique_tus = []
    
    for file_path in files:
        for tu in hm.load(file_path, filter="tu"):
            # Create a hash based on content
            key = tuple(
                (tuv.lang, hm.helpers.text(tuv))
                for tuv in sorted(tu.variants, key=lambda v: v.lang)
            )
            
            if key not in seen:
                seen.add(key)
                unique_tus.append(tu)
    
    merged = hm.helpers.create_tmx(body=unique_tus)
    hm.dump(merged, output_path)
```

## Handling Conflicting Headers

When merging files with different metadata:

```python
def merge_with_unified_header(files: list[str], output_path: str):
    """Merge with a fresh header."""
    all_tus = []
    
    for file_path in files:
        tmx = hm.load(file_path)
        all_tus.extend(tmx.body)
    
    # Create new header for merged file
    header = hm.helpers.create_header(
        srclang="en",
        creationtool="merge-script",
        props=[
            hm.helpers.create_prop("merged-from", ", ".join(files)),
        ],
        notes=[
            hm.helpers.create_note(f"Merged from {len(files)} files"),
        ],
    )
    
    merged = hm.helpers.create_tmx(header=header, body=all_tus)
    hm.dump(merged, output_path)
```

## Streaming Merge for Large Files

```python
def merge_large(files: list[str], output_path: str):
    """Merge large files using streaming."""
    all_tus = []
    
    for file_path in files:
        for tu in hm.load(file_path, filter="tu"):
            all_tus.append(tu)
    
    # Create with minimal header
    merged = hm.helpers.create_tmx(body=all_tus)
    hm.dump(merged, output_path)
```

Note: This still loads all TUs into memory. For truly massive merges, write directly to XML.

## See Also

- [Split by Language](/en/cookbook/split-tmx-by-language) — The inverse operation
