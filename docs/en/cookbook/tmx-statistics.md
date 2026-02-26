---
title: TMX Statistics
---

# TMX Statistics

Extract metrics and statistics from a TMX file.

## Problem

You want to know:
- How many translation units are in the file
- What languages are present
- Date ranges
- Tool that created the file

## Solution

```python
import hypomnema as hm
from collections import Counter

def tmx_stats(tmx_path: str) -> dict:
    """Extract statistics from a TMX file."""
    stats = {
        "tu_count": 0,
        "languages": Counter(),
        "creation_tool": None,
        "creation_date": None,
        "source_lang": None,
        "oldest_entry": None,
        "newest_entry": None,
    }
    
    tmx = hm.load(tmx_path)
    
    # Header info
    stats["creation_tool"] = f"{tmx.header.creationtool} {tmx.header.creationtoolversion}"
    stats["creation_date"] = tmx.header.creationdate
    stats["source_lang"] = tmx.header.srclang
    
    # Body stats
    dates = []
    for tu in tmx.body:
        stats["tu_count"] += 1
        
        for tuv in tu.variants:
            stats["languages"][tuv.lang] += 1
            
            if tuv.creationdate:
                dates.append(tuv.creationdate)
    
    if dates:
        stats["oldest_entry"] = min(dates)
        stats["newest_entry"] = max(dates)
    
    return stats

# Usage
stats = tmx_stats("translations.tmx")
print(f"TUs: {stats['tu_count']}")
print(f"Languages: {dict(stats['languages'])}")
print(f"Created by: {stats['creation_tool']}")
print(f"Date range: {stats['oldest_entry']} to {stats['newest_entry']}")
```

## Streaming for Large Files

For large files, use streaming to avoid memory issues:

```python
def tmx_stats_streaming(tmx_path: str) -> dict:
    """Extract statistics using streaming."""
    stats = {
        "tu_count": 0,
        "languages": Counter(),
    }
    
    for tu in hm.load(tmx_path, filter="tu"):
        stats["tu_count"] += 1
        for tuv in tu.variants:
            stats["languages"][tuv.lang] += 1
    
    return stats
```

Note: Header info isn't available when streaming. Parse it separately if needed.

## Extended Statistics

Add more detailed metrics:

```python
def detailed_stats(tmx_path: str) -> dict:
    tmx = hm.load(tmx_path)
    
    word_counts = Counter()
    char_counts = Counter()
    
    for tu in tmx.body:
        for tuv in tu.variants:
            text = hm.helpers.text(tuv)
            word_counts[tuv.lang] += len(text.split())
            char_counts[tuv.lang] += len(text)
    
    return {
        "word_counts": dict(word_counts),
        "character_counts": dict(char_counts),
    }
```

## See Also

- [Validate TMX](/en/cookbook/validate-tmx) — Check for issues before analyzing
