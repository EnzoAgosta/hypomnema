---
title: Filter by Date
---

# Filter by Date

Keep only translation units from a specific time period.

## Problem

You want to:
- Keep only recent translations
- Remove old, potentially stale entries
- Extract entries from a specific project phase

## Solution

```python
import hypomnema as hm
from datetime import datetime, UTC, timedelta

def filter_by_date(
    tmx_path: str,
    output_path: str,
    after: datetime | None = None,
    before: datetime | None = None,
):
    """Keep only TUs created within a date range."""
    tmx = hm.load(tmx_path)
    
    filtered_tus = []
    
    for tu in tmx.body:
        # Use TU date, or fall back to earliest TUV date
        tu_date = tu.creationdate
        if tu_date is None:
            dates = [tuv.creationdate for tuv in tu.variants if tuv.creationdate]
            tu_date = min(dates) if dates else None
        
        if tu_date is None:
            continue  # Skip entries without dates
        
        # Check date range
        if after and tu_date < after:
            continue
        if before and tu_date > before:
            continue
        
        filtered_tus.append(tu)
    
    output_tmx = hm.helpers.create_tmx(
        header=tmx.header,
        body=filtered_tus,
    )
    
    hm.dump(output_tmx, output_path)

# Usage: Keep only entries from last year
one_year_ago = datetime.now(UTC) - timedelta(days=365)
filter_by_date("all.tmx", "recent.tmx", after=one_year_ago)
```

## Filter by Last Modified

```python
def filter_recently_modified(tmx_path: str, output_path: str, days: int = 90):
    """Keep only TUs modified in the last N days."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    
    tmx = hm.load(tmx_path)
    filtered_tus = []
    
    for tu in tmx.body:
        # Check changedate on TU and all TUVs
        dates = [tu.changedate] if tu.changedate else []
        dates.extend(tuv.changedate for tuv in tu.variants if tuv.changedate)
        
        if dates and max(dates) >= cutoff:
            filtered_tus.append(tu)
    
    output_tmx = hm.helpers.create_tmx(header=tmx.header, body=filtered_tus)
    hm.dump(output_tmx, output_path)
```

## Filter by Usage Count

```python
def filter_by_usage(tmx_path: str, output_path: str, min_usage: int = 1):
    """Keep only TUs that have been used at least N times."""
    tmx = hm.load(tmx_path)
    
    filtered_tus = [
        tu for tu in tmx.body
        if any(tuv.usagecount and tuv.usagecount >= min_usage for tuv in tu.variants)
    ]
    
    output_tmx = hm.helpers.create_tmx(header=tmx.header, body=filtered_tus)
    hm.dump(output_tmx, output_path)
```

## Combining Filters

```python
def filter_combined(
    tmx_path: str,
    output_path: str,
    after: datetime | None = None,
    min_usage: int = 0,
):
    """Apply multiple filters."""
    tmx = hm.load(tmx_path)
    
    filtered_tus = []
    for tu in tmx.body:
        # Date filter
        if after:
            dates = [tuv.creationdate for tuv in tu.variants if tuv.creationdate]
            if not dates or min(dates) < after:
                continue
        
        # Usage filter
        if min_usage > 0:
            max_usage = max(
                (tuv.usagecount or 0 for tuv in tu.variants),
                default=0,
            )
            if max_usage < min_usage:
                continue
        
        filtered_tus.append(tu)
    
    output_tmx = hm.helpers.create_tmx(header=tmx.header, body=filtered_tus)
    hm.dump(output_tmx, output_path)
```

## See Also

- [TMX Statistics](/en/cookbook/tmx-statistics) — Analyze date ranges first
