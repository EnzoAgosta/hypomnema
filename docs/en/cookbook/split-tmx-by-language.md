---
title: Split TMX by Language
---

# Split TMX by Language

Extract specific language pairs from a multilingual TMX file.

## Problem

You have a TMX with many languages, but only need certain pairs:

```xml
<!-- Has en, fr, de, es, it... but you only want en→fr -->
```

## Solution

```python
import hypomnema as hm

def extract_language_pair(
    tmx_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
):
    """Extract a single language pair from a TMX."""
    tmx = hm.load(tmx_path)
    
    filtered_tus = []
    
    for tu in tmx.body:
        source_tuv = None
        target_tuv = None
        
        for tuv in tu.variants:
            if tuv.lang == source_lang:
                source_tuv = tuv
            elif tuv.lang == target_lang:
                target_tuv = tuv
        
        # Only include TUs that have both languages
        if source_tuv and target_tuv:
            filtered_tus.append(hm.helpers.create_tu(
                tuid=tu.tuid,
                srclang=source_lang,
                variants=[source_tuv, target_tuv],
                props=tu.props,
                notes=tu.notes,
            ))
    
    output_tmx = hm.helpers.create_tmx(
        header=hm.helpers.create_header(srclang=source_lang),
        body=filtered_tus,
    )
    
    hm.dump(output_tmx, output_path)

# Usage
extract_language_pair("multilingual.tmx", "en-fr.tmx", "en", "fr")
```

## Extract Multiple Pairs

```python
def extract_all_pairs(tmx_path: str, output_dir: str):
    """Extract all language pairs as separate files."""
    from pathlib import Path
    
    tmx = hm.load(tmx_path)
    
    # Find all language combinations
    lang_pairs = set()
    for tu in tmx.body:
        langs = [tuv.lang for tuv in tu.variants]
        for i, l1 in enumerate(langs):
            for l2 in langs[i+1:]:
                lang_pairs.add((l1, l2))
    
    # Extract each pair
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    for source, target in sorted(lang_pairs):
        output_path = output_dir / f"{source}-{target}.tmx"
        extract_language_pair(tmx_path, str(output_path), source, target)
        print(f"Created {output_path}")
```

## Streaming for Large Files

```python
def extract_pair_streaming(
    tmx_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
):
    """Extract language pair using streaming."""
    filtered_tus = []
    
    for tu in hm.load(tmx_path, filter="tu"):
        source_tuv = None
        target_tuv = None
        
        for tuv in tu.variants:
            if tuv.lang == source_lang:
                source_tuv = tuv
            elif tuv.lang == target_lang:
                target_tuv = tuv
        
        if source_tuv and target_tuv:
            filtered_tus.append(hm.helpers.create_tu(
                srclang=source_lang,
                variants=[source_tuv, target_tuv],
            ))
    
    output_tmx = hm.helpers.create_tmx(body=filtered_tus)
    hm.dump(output_tmx, output_path)
```

## See Also

- [Merge TMX Files](/en/cookbook/merge-tmx-files) — The inverse operation
