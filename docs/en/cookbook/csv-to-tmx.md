---
title: CSV to TMX
---

# CSV to TMX

Convert a spreadsheet or CSV file into a TMX translation memory.

## Problem

You have translations in a CSV file:

```csv
source_en,target_fr,target_de
Hello,Bonjour,Hallo
Goodbye,Au revoir,Auf Wiedersehen
Thank you,Merci,Danke
```

You want to convert it to TMX format.

## Solution

```python
import csv
import hypomnema as hm

def csv_to_tmx(csv_path: str, output_path: str, source_lang: str = "en"):
    """Convert CSV to TMX."""
    tus = []
    
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Get target language columns (all except source)
        source_col = reader.fieldnames[0]
        target_cols = [c for c in reader.fieldnames if c != source_col]
        
        for row in reader:
            # Extract language code from column name (e.g., "target_fr" -> "fr")
            variants = [
                hm.helpers.create_tuv(source_lang, content=[row[source_col]])
            ]
            
            for col in target_cols:
                lang = col.split("_")[-1]  # Extract language code
                variants.append(
                    hm.helpers.create_tuv(lang, content=[row[col]])
                )
            
            tus.append(hm.helpers.create_tu(variants=variants))
    
    tmx = hm.helpers.create_tmx(
        header=hm.helpers.create_header(srclang=source_lang),
        body=tus,
    )
    
    hm.dump(tmx, output_path)

# Usage
csv_to_tmx("translations.csv", "output.tmx", source_lang="en")
```

## Discussion

### Column Naming Convention

This example expects columns named like `target_fr`, `target_de`. The language code is extracted from the suffix.

### Missing Values

Handle missing translations gracefully:

```python
for col in target_cols:
    if row[col]:  # Only add if not empty
        lang = col.split("_")[-1]
        variants.append(
            hm.helpers.create_tuv(lang, content=[row[col]])
        )
```

### Adding Metadata

Include row numbers or IDs:

```python
tus.append(hm.helpers.create_tu(
    tuid=f"row-{row_num}",
    variants=variants,
))
```

## See Also

- [Merge TMX Files](/en/cookbook/merge-tmx-files) — Combine multiple converted files
- [Validate TMX](/en/cookbook/validate-tmx) — Check the output
