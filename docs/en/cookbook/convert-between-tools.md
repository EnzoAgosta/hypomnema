---
title: Convert Between Tools
---

# Convert Between Tools

Handle metadata differences when converting TMX between translation tools.

## Problem

Different CAT tools use proprietary metadata in `<prop>` elements:

```xml
<!-- MemoQ TMX -->
<prop type="x-memoq:context">UI|Buttons</prop>

<!-- SDL Trados TMX -->
<prop type="x-sdl:context">domain:software</prop>

<!-- XTM TMX -->
<prop type="x-xtm:filename">main.ui</prop>
```

You need to convert between these formats.

## Solution

```python
import hypomnema as hm

TOOL_METADATA_MAP = {
    "memoq": {
        "context": "x-memoq:context",
        "filename": "x-memoq:document",
    },
    "sdl": {
        "context": "x-sdl:context",
        "filename": "x-sdl:filename",
    },
    "xtm": {
        "context": "x-xtm:contextId",
        "filename": "x-xtm:filename",
    },
}

def convert_metadata(
    tmx_path: str,
    output_path: str,
    source_tool: str,
    target_tool: str,
):
    """Convert tool-specific metadata between formats."""
    tmx = hm.load(tmx_path)
    
    source_map = TOOL_METADATA_MAP.get(source_tool, {})
    target_map = TOOL_METADATA_MAP.get(target_tool, {})
    
    # Build reverse map: source_prop_type -> canonical_name
    reverse_source = {v: k for k, v in source_map.items()}
    
    converted_tus = []
    for tu in tmx.body:
        # Extract and convert props
        new_props = []
        canonical_values = {}
        
        for prop in tu.props:
            # Map source tool props to canonical names
            canonical = reverse_source.get(prop.type)
            if canonical:
                canonical_values[canonical] = prop.text
            else:
                # Keep unknown props as-is
                new_props.append(prop)
        
        # Convert canonical to target tool props
        for canonical, value in canonical_values.items():
            target_type = target_map.get(canonical)
            if target_type:
                new_props.append(hm.helpers.create_prop(
                    text=value,
                    type=target_type,
                ))
        
        converted_tus.append(hm.helpers.create_tu(
            tuid=tu.tuid,
            srclang=tu.srclang,
            variants=tu.variants,
            props=new_props,
            notes=tu.notes,
        ))
    
    # Update header for target tool
    new_header = hm.helpers.create_header(
        srclang=tmx.header.srclang,
        creationtool=target_tool,
        props=[
            hm.helpers.create_prop(
                text=f"Converted from {source_tool}",
                type="x-conversion-source",
            ),
        ],
    )
    
    output_tmx = hm.helpers.create_tmx(header=new_header, body=converted_tus)
    hm.dump(output_tmx, output_path)

# Usage
convert_metadata("memoq_export.tmx", "for_sdl.tmx", "memoq", "sdl")
```

## TUV-Level Metadata

Handle metadata at the variant level:

```python
def convert_tuv_metadata(tmx_path: str, output_path: str):
    """Convert TUV-level metadata."""
    tmx = hm.load(tmx_path)
    
    converted_tus = []
    for tu in tmx.body:
        new_variants = []
        
        for tuv in tu.variants:
            new_props = []
            
            for prop in tuv.props:
                # Convert prop types as needed
                new_type = convert_prop_type(prop.type)
                new_props.append(hm.helpers.create_prop(
                    text=prop.text,
                    type=new_type,
                    lang=prop.lang,
                ))
            
            new_variants.append(hm.helpers.create_tuv(
                lang=tuv.lang,
                content=tuv.content,
                props=new_props,
            ))
        
        converted_tus.append(hm.helpers.create_tu(variants=new_variants))
    
    output_tmx = hm.helpers.create_tmx(body=converted_tus)
    hm.dump(output_tmx, output_path)
```

## Stripping Unknown Metadata

Remove all tool-specific props:

```python
def strip_proprietary_metadata(tmx_path: str, output_path: str):
    """Remove all x- prefixed properties."""
    tmx = hm.load(tmx_path)
    
    def filter_props(props):
        return [p for p in props if not p.type.startswith("x-")]
    
    converted_tus = []
    for tu in tmx.body:
        converted_tus.append(hm.helpers.create_tu(
            tuid=tu.tuid,
            srclang=tu.srclang,
            variants=[
                hm.helpers.create_tuv(
                    lang=tuv.lang,
                    content=tuv.content,
                    props=filter_props(tuv.props),
                )
                for tuv in tu.variants
            ],
            props=filter_props(tu.props),
            notes=tu.notes,
        ))
    
    output_tmx = hm.helpers.create_tmx(
        header=hm.helpers.create_header(
            srclang=tmx.header.srclang,
            props=filter_props(tmx.header.props),
        ),
        body=converted_tus,
    )
    hm.dump(output_tmx, output_path)
```

## See Also

- [Validate TMX](/en/cookbook/validate-tmx) — Check converted files
