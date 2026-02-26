---
layout: home

hero:
  name: "Hypomnema"
  text: "TMX for Python"
  tagline: Type-safe, policy-driven, zero-dependency TMX 1.4b library
  actions:
    - theme: brand
      text: Get Started
      link: /en/tutorial/01-installation
    - theme: alt
      text: API Reference
      link: /en/api/

features:
  - title: Full TMX 1.4b Support
    details: Complete implementation of the TMX 1.4b specification, including all inline elements with arbitrary nesting depth.
  - title: Type-Safe Dataclasses
    details: Work with Python dataclasses, not raw XML nodes. Full type hints for IDE autocomplete and static analysis.
  - title: Policy-Driven Error Handling
    details: Configure how the library responds to malformed data—raise, ignore, or use defaults per violation type.
  - title: Zero Runtime Dependencies
    details: Uses only Python stdlib by default. Optional lxml backend available for 3-5x performance boost on large files.
---
