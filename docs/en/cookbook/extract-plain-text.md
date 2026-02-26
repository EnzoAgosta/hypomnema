---
title: Extract Plain Text
---

# Extract Plain Text

Strip inline markup and get raw text from a TMX file.

## Problem

You want the plain text content without formatting tags, placeholders, or other markup.

## Solution

```python
import hypomnema as hm

def extract_plain_text(tmx_path: str, output_path: str):
    """Extract plain text from a TMX file."""
    tmx = hm.load(tmx_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for i, tu in enumerate(tmx.body):
            f.write(f"=== TU {i + 1} ===\n")
            
            for tuv in tu.variants:
                text = hm.helpers.text(tuv)
                f.write(f"[{tuv.lang}] {text}\n")
            
            f.write("\n")

# Usage
extract_plain_text("formatted.tmx", "plain_text.txt")
```

## Export to Parallel Corpus

Create a tab-separated file for machine translation:

```python
def export_parallel_corpus(
    tmx_path: str,
    output_path: str,
    source_lang: str,
    target_lang: str,
):
    """Export language pair as TSV for MT training."""
    tmx = hm.load(tmx_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for tu in tmx.body:
            source_text = None
            target_text = None
            
            for tuv in tu.variants:
                if tuv.lang == source_lang:
                    source_text = hm.helpers.text(tuv)
                elif tuv.lang == target_lang:
                    target_text = hm.helpers.text(tuv)
            
            if source_text and target_text:
                f.write(f"{source_text}\t{target_text}\n")

# Usage
export_parallel_corpus("translations.tmx", "corpus.tsv", "en", "fr")
```

## Iterating Over Text Segments

For more control, iterate over text parts:

```python
def extract_with_positions(tmx_path: str):
    """Extract text, noting where inline elements were."""
    tmx = hm.load(tmx_path)
    
    for tu in tmx.body:
        for tuv in tu.variants:
            print(f"\n[{tuv.lang}]")
            
            for i, item in enumerate(tuv.content):
                if isinstance(item, str):
                    print(f"  Text: {item}")
                else:
                    # Inline element
                    print(f"  Markup: <{type(item).__name__}>")
```

## Ignoring Specific Markup

Skip certain inline elements when extracting text:

```python
# Get text, ignoring placeholders (e.g., variables)
for tu in tmx.body:
    for tuv in tu.variants:
        text_parts = list(hm.helpers.iter_text(tuv, ignore=hm.Ph))
        text = "".join(text_parts)
```

## Sentence-Level Extraction

If your TMX is sentence-segmented, export as one sentence per line:

```python
def export_sentences(tmx_path: str, output_dir: str):
    """Export each language as a separate sentence file."""
    from pathlib import Path
    
    tmx = hm.load(tmx_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Collect sentences by language
    sentences = {}
    for tu in tmx.body:
        for tuv in tu.variants:
            if tuv.lang not in sentences:
                sentences[tuv.lang] = []
            sentences[tuv.lang].append(hm.helpers.text(tuv))
    
    # Write each language
    for lang, sents in sentences.items():
        with open(output_dir / f"{lang}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(sents))

# Usage
export_sentences("corpus.tmx", "sentences/")
```

## See Also

- [CSV to TMX](/en/cookbook/csv-to-tmx) — The inverse operation
