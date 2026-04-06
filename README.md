# Hypomnema

A type-safe Python library for manipulating, creating, and editing TMX (Translation Memory eXchange) files.

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

Hypomnema provides a robust, typed interface for working with TMX files — the industry-standard XML format for exchanging translation memory data between CAT tools and localization platforms.

Unlike generic XML libraries that treat TMX as untyped document trees, Hypomnema models the entire TMX specification as Python dataclasses. This gives you:

- **Compile-time validation** of TMX structure through type checkers
- **IDE autocomplete** for all TMX elements and attributes
- **Runtime safety** with validation of language codes, encodings, and enum values
- **Round-trip fidelity** — unknown elements are preserved, not discarded

## Key Features

- **Fully Typed Domain Model** — Every TMX element (`<tu>`, `<tuv>`, `<seg>`, `<bpt>`, etc.) is a type-safe dataclass
- **Decoupled Architecture** — Domain, Operations, and Backends are strictly separated layers
- **Pluggable XML Backends** — Use standard library `xml.etree` or `lxml` without changing your code
- **Streaming Support** — Memory-efficient iterparse/iterwrite for large TMX files
- **Extensible** — Register custom loaders/dumpers for non-standard elements
- **Future-Proof** — Architecture designed to support JSON, CSV, and other formats

## Design Philosophy & Architecture

Hypomnema follows a strict three-layer architecture with clear boundaries:

```
┌─────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                         │
│         (hypomnema.domain.nodes/attributes)             │
│                                                         │
│   • Typed dataclasses for all TMX elements              │
│   • Validation at construction time                     │
│   • Immutable, slot-based for memory efficiency         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 OPERATIONS LAYER                        │
│     (hypomnema.loaders, dumpers, ops.*)                 │
│                                                         │
│   • Loaders: XML → Domain objects                       │
│   • Dumpers: Domain objects → XML                       │
│   • Transformations: Walk, normalize, extract text      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND LAYER                         │
│      (hypomnema.backends.xml.standard/lxml)             │
│                                                         │
│   • Abstract XmlBackend interface                       │
│   • Swappable implementations (stdlib, lxml, future)    │
│   • Handles serialization/deserialization details       │
└─────────────────────────────────────────────────────────┘
```

**Why this matters:**

- **Swap backends without touching business logic** — Your code works with `TranslationUnit` objects, not XML elements
- **Add formats without rewrites** — A JSON backend would use the same domain objects
- **Testability** — Mock backends for unit tests, no file I/O required
- **Strict boundaries** — Each layer has a single responsibility and well-defined interface

## Installation

```bash
# Core library (uses standard library xml.etree)
pip install hypomnema

# With lxml backend for better performance
pip install hypomnema[lxml]

# Development dependencies
pip install hypomnema[dev]
```

Requires Python 3.13 or later.

## Quick Start

```python
from hypomnema.domain.nodes import (
    TranslationMemory,
    TranslationMemoryHeader,
    TranslationUnit,
    TranslationVariant,
)
from hypomnema.backends.xml.standard import StandardBackend
from hypomnema.loaders.xml import XmlLoader
from hypomnema.dumpers.xml import XmlDumper

# Create a backend (could use LxmlBackend instead)
backend = StandardBackend()

# Load a TMX file
loader = XmlLoader(backend)
tmx_element = backend.parse("translation_memory.tmx")
tm = loader.load(tmx_element)

# Work with typed objects
# reveal_type(tm)  # TranslationMemory
# reveal_type(tm.units[0])  # TranslationUnit
# reveal_type(tm.units[0].variants[0].segment)  # list[str | InlineNode | UnknownInlineNode]

# Modify the translation memory
tm.units.append(
    TranslationUnit.create(
        variants=[
            TranslationVariant.create(language="en-US", segment=["Hello"]),
            TranslationVariant.create(language="fr-FR", segment=["Bonjour"]),
        ]
    )
)

# Save back to XML
dumper = XmlDumper(backend)
output_element = dumper.dump(tm)
backend.write(output_element, "updated_memory.tmx")
```

## Type Safety First

Hypomnema's core philosophy is **type safety at every level**. The entire TMX structure is modeled as precise dataclasses:

### Domain Model Types

```python
from hypomnema.domain.nodes import (
    TranslationMemory,      # Root <tmx> element
    TranslationMemoryHeader, # <header> with metadata
    TranslationUnit,        # <tu> containing translation pairs
    TranslationVariant,     # <tuv> with language-specific content
    Bpt, Ept, It, Ph, Hi,   # Inline markup elements
    Note, Prop,             # Metadata elements
)

from hypomnema.domain.attributes import (
    LanguageCodeString,     # Validated BCP 47 codes
    EncodingString,         # Validated encoding names
    Segtype,                # Enum: block | paragraph | sentence | phrase
)
```

### Type-Safe Construction

All nodes provide `create()` class methods that validate inputs:

```python
from hypomnema.domain.nodes import TranslationVariant

# This works — language code is validated
variant = TranslationVariant.create(
    language="en-US",  # Validated against BCP 47
    segment=["Hello, world!"]
)

# This raises ValueError — invalid language code
variant = TranslationVariant.create(
    language="not_a_language",  # Raises: Invalid language code
    segment=["Hello"]
)

# This raises ValueError — invalid encoding
variant = TranslationVariant.create(
    language="en-US",
    original_encoding="not_an_encoding",  # Raises: Invalid encoding
    segment=["Hello"]
)
```

### Type-Safe Navigation

The type system guides you through the TMX structure:

```python
def process_unit(unit: TranslationUnit) -> None:
    # Type checker knows unit.variants is list[TranslationVariant]
    for variant in unit.variants:
        # Type checker knows variant.segment is InlineContent
        for item in variant.segment:
            match item:
                case str():
                    print(f"Text: {item}")
                case Bpt() | Ept() | It() | Ph() | Hi():
                    print(f"Tag: {type(item).__name__}")
                case UnknownInlineNode():
                    print("Unknown inline element (preserved)")
```

### Generic Backend Abstraction

The backend system uses Python 3.12+ generics for type-safe backend swapping:

```python
from hypomnema.backends.xml.standard import StandardBackend
from hypomnema.backends.xml.lxml import LxmlBackend
from hypomnema.loaders.xml import XmlLoader

# Both backends work identically
std_backend: StandardBackend = StandardBackend()
lxml_backend: LxmlBackend = LxmlBackend()

# Loader is generic over backend element type
loader = XmlLoader(std_backend)  # XmlLoader[Element]
# or
loader = XmlLoader(lxml_backend)  # XmlLoader[_Element]

# Domain objects are identical regardless of backend
tm = loader.load(element)  # TranslationMemory either way
```

### Static Type Checking

Hypomnema is fully typed and validated with mypy:

```python
# mypy will catch this error at check time:
tm: TranslationMemory = loader.load(element)
unit = tm.units[0]
print(unit.invalid_attribute)  # error: "TranslationUnit" has no attribute "invalid_attribute"
```

## Common Tasks

### Loading TMX Files

```python
from hypomnema.backends.xml.standard import StandardBackend
from hypomnema.loaders.xml import XmlLoader

backend = StandardBackend()
loader = XmlLoader(backend)

# Parse and load entire file
tmx_element = backend.parse("memory.tmx")
tm = loader.load(tmx_element)

# Or stream large files with iterparse
for tu_element in backend.iterparse("huge_memory.tmx", tag_filter="tu"):
    unit = loader.load_unit(tu_element)
    process_unit(unit)
    backend.clear(tu_element)  # Free memory
```

### Creating TMX from Scratch

```python
from datetime import datetime
from hypomnema.domain.nodes import (
    TranslationMemory,
    TranslationMemoryHeader,
    TranslationUnit,
    TranslationVariant,
    Note,
)

header = TranslationMemoryHeader.create(
    creation_tool="MyTool",
    creation_tool_version="1.0",
    segmentation_type="sentence",
    original_translation_memory_format="PlainText",
    admin_language="en-US",
    source_language="en-US",
    original_data_type="plaintext",
    created_at=datetime.now(),
)

tm = TranslationMemory.create(
    header=header,
    units=[
        TranslationUnit.create(
            notes=[Note.create(text="Important translation")],
            variants=[
                TranslationVariant.create(language="en-US", segment=["Hello"]),
                TranslationVariant.create(language="de-DE", segment=["Hallo"]),
            ]
        )
    ]
)
```

### Extracting Text Content

```python
from hypomnema.ops.text import join, iter_fragments, find

variant: TranslationVariant = ...

# Get all text as a single string
text = join(variant, recurse=True)

# Iterate over fragments
for fragment in iter_fragments(variant, recurse=True):
    print(fragment)

# Search with regex
match = find(variant, r"\{[^}]+\}", recurse=True)
```

### Walking the Tree

```python
from hypomnema.ops.walk import walk_units, walk_variants, walk_content

# Iterate over all translation units
for unit in walk_units(tm):
    print(f"Unit ID: {unit.spec_attributes.translation_unit_id}")

# Iterate over all variants
for variant in walk_variants(tm):
    print(f"Language: {variant.spec_attributes.language}")

# Walk inline content (respects nesting)
for item in walk_content(variant, recurse=True):
    match item:
        case str():
            print(f"Text: {item}")
        case Bpt():
            print(f"Begin tag: i={item.spec_attributes.internal_id}")
```

### Custom Loaders for Non-Standard Elements

```python
from hypomnema.loaders.xml import XmlLoader, XmlLoaderLike

class MyCustomElementLoader(XmlLoaderLike):
    def load(self, element) -> AnyNode:
        # Custom loading logic
        return CustomNode(...)

backend = StandardBackend()
loader = XmlLoader(backend)
loader.register_override("custom-element", MyCustomElementLoader())

# Now <custom-element> tags are handled by your loader
tm = loader.load(backend.parse("file.tmx"))
```

### Streaming Large Files

```python
from hypomnema.backends.xml.standard import StandardBackend
from hypomnema.dumpers.xml import XmlDumper

backend = StandardBackend()
dumper = XmlDumper(backend)

# Generate units on the fly
def generate_units():
    for source, target in translation_pairs:
        yield TranslationUnit.create(
            variants=[
                TranslationVariant.create(language="en-US", segment=[source]),
                TranslationVariant.create(language="fr-FR", segment=[target]),
            ]
        )

# Write incrementally (memory-efficient)
backend.iterwrite(
    "output.tmx",
    (dumper.dump_unit(unit) for unit in generate_units()),
    write_xml_declaration=True,
    write_doctype=True,
)
```

## Contributing

Contributions are welcome! Please see the [GitHub repository](https://github.com/EnzoAgosta/hypomnema) for:

- [Issue Tracker](https://github.com/EnzoAgosta/hypomnema/issues)
- [Source Code](https://github.com/EnzoAgosta/hypomnema)

## License

Hypomnema is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

_Hypomnema_ (ὑπόμνημα) — from Ancient Greek: "that which is written underneath," a reminder or memorandum. A fitting name for a translation memory library.
