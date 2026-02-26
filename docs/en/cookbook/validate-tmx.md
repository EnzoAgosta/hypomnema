---
title: Validate TMX
---

# Validate TMX

Check a TMX file for structural issues and malformed data.

## Problem

You want to verify a TMX file is valid before processing it.

## Solution

```python
import hypomnema as hm
from hypomnema import policy
import logging

def validate_tmx(tmx_path: str) -> list[str]:
    """Validate a TMX file and return list of issues."""
    issues = []
    
    # Set up logging to capture warnings
    logger = logging.getLogger("validator")
    logger.setLevel(logging.DEBUG)
    
    class IssueHandler(logging.Handler):
        def emit(self, record):
            issues.append(f"{record.levelname}: {record.getMessage()}")
    
    logger.addHandler(IssueHandler())
    
    # Use strict policy (the default)
    try:
        tmx = hm.load(tmx_path, deserializer_logger=logger)
        
        # Additional validation checks
        if not tmx.body:
            issues.append("WARNING: TMX has no translation units")
        
        for i, tu in enumerate(tmx.body):
            if len(tu.variants) < 2:
                issues.append(f"WARNING: TU {i} has fewer than 2 variants")
            
            for tuv in tu.variants:
                if not tuv.content:
                    issues.append(f"WARNING: TU {i} TUV {tuv.lang} has empty content")
    
    except Exception as e:
        issues.append(f"ERROR: Failed to parse: {e}")
    
    return issues

# Usage
issues = validate_tmx("suspicious.tmx")
if issues:
    print("Issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("TMX is valid!")
```

## Lenient Validation

Check what issues exist without failing:

```python
def check_tmx_health(tmx_path: str) -> dict:
    """Analyze TMX health without raising errors."""
    stats = {
        "parse_errors": [],
        "missing_dates": 0,
        "empty_segments": 0,
        "single_variant_tus": 0,
        "total_tus": 0,
    }
    
    # Lenient policy to capture issues without failing
    lenient_policy = policy.XmlDeserializationPolicy(
        missing_seg=policy.Behavior(policy.RaiseIgnore.IGNORE),
        invalid_datetime_value=policy.Behavior(policy.RaiseNoneKeep.NONE),
    )
    
    try:
        tmx = hm.load(tmx_path, deserializer_policy=lenient_policy)
        
        stats["total_tus"] = len(tmx.body)
        
        for tu in tmx.body:
            if len(tu.variants) < 2:
                stats["single_variant_tus"] += 1
            
            for tuv in tu.variants:
                if not tuv.content:
                    stats["empty_segments"] += 1
                if tuv.creationdate is None:
                    stats["missing_dates"] += 1
    
    except Exception as e:
        stats["parse_errors"].append(str(e))
    
    return stats
```

## Schema Validation

For TMX specification compliance, combine with XML schema validation:

```python
from lxml import etree

def validate_against_tmx_dtd(tmx_path: str) -> list[str]:
    """Validate TMX structure against DTD."""
    issues = []
    
    # Note: You'll need the TMX DTD file
    # Download from: https://www.gala-global.org/tmx-14b.dtd
    
    try:
        parser = etree.XMLParser(dtd_validation=True)
        etree.parse(tmx_path, parser)
    except etree.XMLSyntaxError as e:
        issues.append(f"DTD validation error: {e}")
    
    return issues
```

## Common Issues to Check

| Issue | Detection |
|-------|-----------|
| Empty segments | `if not tuv.content` |
| Missing language codes | `if not tuv.lang` |
| Invalid dates | Policy catches during parsing |
| Duplicate TUs | Compare content hashes |
| Unbalanced inline tags | Check `bpt.i` matches `ept.i` |

## See Also

- [Error Handling Tutorial](/en/tutorial/08-error-handling) — Policy configuration
