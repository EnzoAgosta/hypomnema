# Hypomnema

[![PyPI version](https://badge.fury.io/py/hypomnema.svg)](https://badge.fury.io/py/hypomnema)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

**Industrial-grade TMX 1.4b parsing and serialization for Python.**

Hypomnema is a strictly typed infrastructure library for working with [TMX 1.4b](https://resources.gala-global.org/tbx14b) (Translation Memory eXchange) files. It is designed as a foundation for building localization tools, CAT software, and NLP pipelines, focusing on correctness, type safety, and memory efficiency when handling large datasets.

> **Warning**  
> This project is currently in **Alpha**. It is a work in progress and should not be used for full production workflows until the 1.0 version is released. API changes may occur.

## Why Hypomnema?

While other TMX libraries exist, Hypomnema is built with modern Python engineering standards to address common pain points:

- **Strict Type Safety**: Every TMX element is modeled as a typed Python dataclass. This ensures your code is robust, autocompletion works perfectly, and you catch errors at static analysis time rather than runtime.
- **Policy-Driven Error Handling**: Real-world TMX files are often messy. Instead of crashing on a single malformed date or missing attribute, Hypomnema uses a granular **Policy System**. You define exactly how to handle specific errors (raise, ignore, use default, or keep raw value) without compromising the integrity of the rest of the file.
- **Full TMX 1.4b Level 2 Compliance**: Supports arbitrary inline element nesting depth and complete attribute modeling.
- **Memory Efficient**: Supports streaming processing for large TMX files.
- **Backend Agnostic**: Works with standard `xml` or `lxml` (for performance).

## Installation

Install using `uv` (recommended):

```bash
uv add hypomnema
```

Or using `pip`:

```bash
pip install hypomnema
```

For maximum performance with large files (enables `lxml` backend):

```bash
uv add "hypomnema[lxml]"
# or
pip install "hypomnema[lxml]"
```

## Quick Start

```python
import hypomnema as hm

# Load a TMX file
tmx = hm.load("translations.tmx")

# Inspect the content
print(f"Source language: {tmx.header.srclang}")
print(f"Translation units: {len(tmx.body)}")

# Find a specific translation unit
for tu in tmx.body:
    for tuv in tu.variants:
        if tuv.lang == "fr":
            print(f"French: {tuv.content}")

# Save changes
hm.dump(tmx, "output.tmx")
```

## Advanced Usage

### Streaming Large Files

For large translation memories, use the streaming API to process units one by one without loading the whole file into RAM:

```python
import hypomnema as hm

# Stream translation units ('tu') only
for tu in hm.load("massive_memory.tmx", filter="tu"):
    print(f"Processing TU: {tu.tuid}")
    # Process units here...
```

### Creating and Saving TMX Files

You can programmatically create TMX files using the helper factory functions:

```python
import hypomnema as hm
from hypomnema import helpers

# 1. Create a Header
header = helpers.create_header(
    creationtool="hypomnema",
    segtype="sentence",
    srclang="en-US",
    adminlang="en-US"
)

# 2. Create a Translation Unit (TU) with variants
# TUVs can contain plain text or mixed content with inline tags
tuv_en = helpers.create_tuv("en-US", content="Hello world")
tuv_fr = helpers.create_tuv("fr-FR", content=["Bonjour ", helpers.create_ph(x=1, type="lb"), "le monde"])

tu = helpers.create_tu(
    tuid="1",
    srclang="en-US",
    variants=[tuv_en, tuv_fr]
)

# 3. Create the TMX object
tmx = helpers.create_tmx(header=header, body=[tu])

# 4. Save to disk
hm.dump(tmx, "output.tmx")
```

### Policy Configuration

Real-world TMX files are often imperfect. Policies let you configure how Hypomnema handles validation errors:

```python
import logging
import hypomnema as hm
from hypomnema.xml.policy import Behavior, XmlDeserializationPolicy

policy = XmlDeserializationPolicy(
    missing_seg=Behavior("ignore", logging.WARNING),
    extra_text=Behavior("ignore", logging.INFO),
)

tmx = hm.load("messy.tmx", deserializer_policy=policy)
```

<details>
<summary>Available Policy Keys</summary>

**Deserialization:**

- `invalid_child_tag`: Action for unexpected child elements.
- `missing_text_content`: Action for elements missing required text.
- `invalid_tag`: Action for unexpected element tags.
- `extra_text`: Action for unexpected text content.
- `required_attribute_missing`: Action for missing required attributes.
- `multiple_seg`: Action for multiple <seg> elements in <tuv>.
- `multiple_headers`: Action for multiple <header> elements.
- `invalid_datetime_value`: Action for unparsable datetime values.
- `invalid_enum_value`: Action for invalid enum values.
- `invalid_int_value`: Action for unparsable integer values.
- `missing_deserialization_handler`: Action for missing element handlers.
- `missing_seg`: Action for <tuv> elements without <seg>.
- `multiple_body`: Action for multiple <body> elements.
- `missing_header`: Action for <tmx> elements without <header>.
- `missing_body`: Action for <tmx> elements without <body>.

**Serialization:**

- `invalid_element_type`: Action for unexpected object types.
- `missing_text_content`: Action for objects missing required text.
- `required_attribute_missing`: Action for missing required attributes.
- `invalid_child_element`: Action for invalid child element types.
- `invalid_attribute_type`: Action for attributes with wrong types.
- `missing_serialization_handler`: Action for missing element handlers.

**Namespace:**

- `existing_namespace`: Action when registering an already-existing prefix.
- `inexistent_namespace`: Action when resolving an unregistered prefix.

</details>

### Text Extraction

Extract plain text content from elements, skipping inline markup:

```python
from hypomnema import helpers, Bpt

tuv = helpers.create_tuv(
    "en",
    content=[
        "Hello ",
        helpers.create_bpt(i=1, content="Bpt text"),
        "World",
        helpers.create_ept(i=1, content="Ept text")
        ],
    )

# Quick access via text helper
print(helpers.text(tuv))  # "Hello World"

# Iterate over text segments
for text in helpers.iter_text(tuv):
    print(text)  # "Hello " then "Bpt text" then "World" then "Ept text"

# Ignore specific element types
for text in helpers.iter_text(tuv, ignore=Bpt):
    print(text)  # "Hello " then "World" then "Ept text"
```

## TMX 1.4b Level 2 Compliance

Hypomnema is the **only Python library** that fully implements the TMX 1.4b Level 2 specification:

- **Arbitrary Nesting Depth**: No limits on inline element nesting. `<bpt>`/`<ept>` pairs, `<ph>` placeholders, and `<sub>` elements can nest to any depth.
- **Complete Inline Element Support**: All six inline markup elements (`<bpt>`, `<ept>`, `<it>`, `<ph>`, `<hi>`, `<sub>`) with proper mixed content handling.
- **Full Attribute Modeling**: Every TMX attribute is typed, including enumerations for `segtype`, `pos`, and `assoc`.
- **Metadata Preservation**: Properties and notes supported at all valid nesting levels.

## Development

To contribute or run tests locally:

1. Clone the repository.
2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```
3. Run the test suite:
   ```bash
   uv run pytest
   ```

## License

MIT
