# Hypomnema

[![PyPI version](https://badge.fury.io/py/hypomnema.svg)](https://badge.fury.io/py/hypomnema)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

**Industrial-grade TMX 1.4b parsing and serialization for Python.**

Hypomnema is a strictly typed infrastructure library for working with [TMX 1.4b](https://resources.gala-global.org/tbx14b) (Translation Memory eXchange) files. It is designed as a foundation for building localization tools, CAT software, and NLP pipelines.

> **Warning:** Hypomnema is pre-1.0 software. Expect breaking changes without notice until version 1.0.0.

## Why Hypomnema?

Most TMX parsers are simple XML wrappers. Hypomnema offers:

- **Full TMX 1.4b Level 2 Compliance**: Arbitrary inline element nesting depth, complete attribute modeling
- **Policy-Driven Error Handling**: Configure exactly how to handle malformed data
- **Backend Agnostic**: Use `lxml` for speed or standard library `xml.etree` for zero-dependency deployments
- **Full Type Safety**: Modern Python 3.13+ type annotations with structured dataclasses
- **Roundtrip Integrity**: Deserialize to objects, manipulate, serialize back
- **Streaming API**: Process large TMX files element-by-element without loading everything into memory

## What is TMX?

TMX (Translation Memory eXchange) is an open XML standard for exchanging translation memory data between tools and providers. A TMX file contains translation units (TU) with source and target language variants (TUV), each containing segmented text. TMX files often include inline markup for formatting, placeholders, and tags that must be preserved during processing.

## Installation

```bash
pip install hypomnema
# or
uv add hypomnema
```

For maximum performance with large files:

```bash
pip install "hypomnema[lxml]"
# or
uv add hypomnema[lxml]
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
            print(f"French: {tuv.text}")

# Save changes
hm.dump(tmx, "output.tmx")
```

## High-Level API

### Loading Files

```python
import hypomnema as hm

# Load entire file
tmx = hm.load("input.tmx")

# Streaming: yield translation units one at a time (memory efficient)
for tu in hm.load("large.tmx", filter="tu"):
    print(tu.tuid)

# Filter multiple element types
for element in hm.load("file.tmx", filter=["tu", "prop"]):
    if isinstance(element, hm.Tu):
        print(element.creationtool)
    else:
        print(element.type)

# Specify encoding
tmx = hm.load("file.tmx", encoding="utf-16")
```

### Saving Files

```python
import hypomnema as hm

hm.dump(tmx, "output.tmx")
hm.dump(tmx, "output.tmx", encoding="utf-16")
```

## Element Creation

Convenience functions for creating TMX elements:

```python
import hypomnema as hm

# Structural elements
header = hm.create_header(srclang="en", creationtool="my-tool")
tuv = hm.create_tuv("en", content=["Hello"])
tu = hm.create_tu(tuid="001", variants=[tuv])
tmx = hm.create_tmx(header=header, body=[tu])

# Inline elements
bpt = hm.create_bpt(i=1, type="bold", content=["text"])
ept = hm.create_ept(i=1)
it = hm.create_it(pos=hm.Pos.BEGIN, type="italic")
ph = hm.create_ph(type="variable", x=100)
hi = hm.create_hi(content=["highlighted"])
sub = hm.create_sub(content=["sub-flow"], datatype="text")

# Auxiliary elements
prop = hm.create_prop("customer", "acme-corp")
note = hm.create_note("Translation note")
```

## Text Extraction

Extract plain text content from elements, skipping inline markup:

```python
import hypomnema as hm

tuv = hm.create_tuv(
    "en",
    content=[
        "Hello ",
        hm.create_bpt(i=1, content="Bpt text"),
        "World",
        hm.create_ept(i=1, content="Ept text")
        ],
    )

# Quick access via .text property
print(tuv.text)  # "Hello World"

# Iterate over text segments
for text in hm.iter_text(tuv):
    print(text)  # "Hello " then "Bpt text" then "World" then "Ept text"

# Ignore specific element types
for text in hm.iter_text(tuv, Ignore=[hm.Bpt]):
    print(text)  # "Hello " then "World" then "Ept text"
```

## Policy Configuration

Real-world TMX files are often imperfect. Policies let you configure how Hypomnema handles validation errors:

```python
import logging
import hypomnema as hm
from hypomnema.xml.policy import PolicyValue

policy = hm.XmlPolicy(
    missing_seg=PolicyValue("ignore", logging.WARNING),
    extra_text=PolicyValue("ignore", logging.INFO),
    invalid_attribute_value=PolicyValue("ignore", logging.DEBUG),
    required_attribute_missing=PolicyValue("ignore", logging.ERROR),
)

tmx = hm.load("messy.tmx", policy=policy)
hm.dump(tmx, "clean.tmx", policy=policy)
```

<details>
<summary>Available Policy Keys</summary>

**Deserialization:**

- `missing_handler` — No handler for element type
- `invalid_tag` — Unexpected XML tag encountered
- `required_attribute_missing` — Mandatory TMX attribute absent
- `invalid_attribute_value` — Attribute violates TMX spec
- `extra_text` — Unexpected text within elements
- `missing_seg` — TUV missing required segment
- `multiple_seg` — TUV has multiple segments
- `empty_content` — Element has no text content

**Serialization:**

- `required_attribute_missing` — Mandatory dataclass field is None
- `invalid_attribute_type` — Field type incompatible with XML
- `invalid_content_type` — Content is not a string
- `missing_handler` — No handler for dataclass type
- `invalid_object_type` — Handler received unexpected type
- `invalid_child_element` — Child not permitted by TMX structure
- `multiple_headers` — Multiple header elements
- `missing_header` — Mandatory header missing

**Namespace:**

- `invalid_namespace` — Invalid namespace prefix or URI
- `existing_namespace` — Namespace already registered
- `missing_namespace` — Namespace not registered

</details>

## Low-Level API

For finer control over parsing and serialization:

```python
import hypomnema as hm

# Choose backend
backend = hm.LxmlBackend()      # Fast, feature-rich
# or
backend = hm.StandardBackend()  # Portable, stdlib only

# Deserialize
deserializer = hm.Deserializer(backend=backend)
root = backend.parse("file.tmx")
tmx = deserializer.deserialize(root)

# Manipulate
new_tuv = hm.create_tuv("de", content=["Guten Tag"])
new_tu = hm.create_tu(variants=[new_tuv])
tmx.body.append(new_tu)

# Serialize
serializer = hm.Serializer(backend=backend)
xml_element = serializer.serialize(tmx)
backend.write(xml_element, "output.tmx")
```

## QName Support

Work with XML qualified names:

```python
from hypomnema.xml.qname import QName

# Simple name
qname = QName("tag")

# Clark notation
# namespace map required when using prefixed/Clark notation
qname = QName("{http://www.example.com}tag", nsmap={"ns": "http://www.example.com"})
print(qname.uri)             # "http://www.example.com"
print(qname.local_name)      # "tag"
print(qname.prefix)          # "ns"
print(qname.qualified_name)  # "{http://www.example.com}tag"

# Use with tag filtering
for tu in hm.load("file.tmx", filter=qname):
    print(tu.tuid)
```

## Creating TMX from Scratch

```python
import hypomnema as hm

header = hm.create_header(
    srclang="en",
    creationtool="my-tool",
    segtype=hm.Segtype.SENTENCE,
)

source = hm.create_tuv(
    "en",
    content=[
        "Click ",
        hm.create_bpt(i=1, type="link"),
        "here",
        hm.create_ept(i=1),
        " to continue.",
    ],
)

target = hm.create_tuv(
    "fr",
    content=[
        "Cliquez ",
        hm.create_bpt(i=1, type="link"),
        "ici",
        hm.create_ept(i=1),
        " pour continuer.",
    ],
)

tu = hm.create_tu(
    tuid="001",
    variants=[source, target],
    props=[hm.create_prop("domain", "ui")],
    notes=[hm.create_note("Button label")],
)

tmx = hm.create_tmx(header=header, body=[tu])
hm.dump(tmx, "output.tmx")
```

## TMX 1.4b Level 2 Compliance

Hypomnema is the **only Python library** that fully implements the TMX 1.4b Level 2 specification:

- **Arbitrary Nesting Depth**: No limits on inline element nesting. `<bpt>`/`<ept>` pairs, `<ph>` placeholders, and `<sub>` elements can nest to any depth.
- **Complete Inline Element Support**: All six inline markup elements (`<bpt>`, `<ept>`, `<it>`, `<ph>`, `<hi>`, `<sub>`) with proper mixed content handling.
- **Full Attribute Modeling**: Every TMX attribute is typed, including enumerations for `segtype`, `pos`, and `assoc`.
- **Metadata Preservation**: Properties and notes supported at all valid nesting levels.

### Intentionally Omitted Elements

- `<ude>` — User Defined Encoding
- `<map>` — Character mapping

These elements relate to custom encodings and are rarely encountered. If needed, subclass the handler classes in `xml/deserialization/_handlers.py` and `xml/serialization/_handlers.py`.

## Architecture

Hypomnema is built on three decoupled layers:

1. **Backend Layer** (`hypomnema.xml.backends`) — Abstracts XML parser implementation
2. **Orchestration Layer** (`hypomnema.xml`) — Manages serialization/deserialization dispatch
3. **Handler Layer** — Specialized classes for each TMX element type

## Supported Elements

**Structural:** `Tmx`, `Header`, `Tu`, `Tuv`

**Inline:** `Bpt`, `Ept`, `It`, `Ph`, `Hi`, `Sub`

**Auxiliary:** `Prop`, `Note`

**Enumerations:** `Segtype`, `Pos`, `Assoc`

## Terminology Reference

See [TERMINOLOGY.md](./TERMINOLOGY.md) for TMX 1.4b terminology.

## Contributing

Contributions are welcome! Please open an issue before submitting a pull request.

## License

MIT
