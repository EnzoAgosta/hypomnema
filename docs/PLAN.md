# Hypomnema v2 plan

Hypomnema v2 is a typed Python library being built for reading, creating,
transforming, and writing TMX 1.4b translation memories. The target is a
streaming, lxml-only library with hardened parsing, structural validation
against a bundled DTD, and Pydantic domain models.

This document is a guidepost, not the TMX specification. It records the agreed
direction and identifies what is still pending. Implementation status is
called out explicitly; the reader/writer APIs below remain targets until
built.

Sources of truth:

- [TMX 1.4b specification](Spec-TMX-1.4b.md), converted
  from the official GALA publication: value semantics, prose requirements,
  recommendations, and examples. The DTD is not a substitute for this text.
- [Bundled DTD](../src/hypomnema/resources/tmx14.dtd): element/attribute inventory
  and XML content models. Do not duplicate that inventory in this plan.
- [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html), sections 2.1 and
  2.2.9: language-tag grammar and well-formedness versus validity.
- [GAPS.md](GAPS.md): review context, decisions, and remaining questions.
  Agreed decisions are incorporated here; unresolved details stay explicit.

## Current implementation and verification

- **Project shell exists.** Python 3.14 minimum; runtime dependencies are lxml
  and Pydantic. The dev group contains pytest, Ruff, ty, and types-lxml.
  `ruff.toml` currently sets two-space indentation and 120-character lines.
- **`bcp47.py` is implemented, tested, and reviewed.** It checks RFC 5646
  ABNF well-formedness, not registry validity. Non-ASCII input is rejected
  before case conversion, including Kelvin-sign lookalikes.
  `tests/test_bcp47.py` covers RFC examples, all grandfathered literals,
  grammar boundaries, malformed input, and API behavior (529 cases; the
  suite's expectations were also cross-checked against an independent ABNF
  oracle).
- **`validators.py` is implemented and tested.** `tests/test_validators.py`
  locks the value contracts (GAPS 1-3, including the lossless
  datetime-offset policy).
- **`models.py` and `validation.py` are implemented and tested.** The models
  carry the settled field names (``metadata``/``variants``, ``metadata``/
  ``content``), explicit discrimination, nonempty required children, the
  automatic language and deprecation advisories, and native-vs-JSON dump
  semantics (`tests/test_models.py`). `validation.py` implements the
  decision-11/12/13 explicit checks -- per-flow bpt/ept pairing, i
  uniqueness, and the x advisory -- with fuzz-tested acceptance and
  rejection (`tests/test_validation.py`). Both survived dedicated
  adversarial reviews.
- **XML projection is implemented, reviewed, and tested for all 14 node
  models.** Parsing uses direct tag dispatch and explicit attribute mapping;
  building uses explicit content dispatch plus native model-field iteration
  and the shared value formatters. A plan-interpreter prototype was built,
  compared against this simpler shape, and superseded and deleted. `TmxNode` is
  the closed 14-model union typing projection;
  `TmxModel` remains the shared base. Text/tail handling, plain-text slots,
  recursive content, metadata ordering, hex values, and the `<seg>` wrapper
  are covered.
- **Projection is not the final conformance boundary.** `from_element()` runs
  fragment DTD validation plus local model validation only; broader domain
  checks are not invoked. `to_element()` builds a detached tree; its caller
  owns whole-tree/domain revalidation and output DTD validation. The
  `Ude.base`/`Map.code` requirement and mutation/cycle handling still await
  implementation or an explicit boundary decision.
- **I/O and the public facade remain placeholders.** `io.py` and the package
  `__init__.py` are unfinished. `TmxError`, `TmxSpecError`, and `TmxWarning`
  exist; the parse/state errors and readers/writers do not.
- **Verification is green: 1,088 tests.** Grammar (529), value (220), model
  (84), and validation (30) cases are joined by 225 XML cases: build 64,
  content 38, DTD 19, parse 58, projection contract 46. Ruff and ty pass, as
  does the XML suite with warnings escalated to errors. Tests were reviewed
  and harmonized: shared fresh construction fixtures, independent
  module-local expectations, narrow explicit warning marks, no autouse
  suppression. No coverage/property-testing dependencies or CI exist.
- **Package-resource loading is implemented and tested.** A cold subprocess
  loads and validates with the bundled DTD from an unrelated working
  directory. Attached-fragment validation carries a tested lxml namespace
  workaround; upstream investigation is deferred. Wheel inclusion and loading
  outside the checkout are still unverified. The README remains out of date.

## Hard constraints

- lxml is the only XML layer. No backend abstraction, no stdlib
  `ElementTree` compatibility.
- Pydantic models are the public domain objects. They own value validation
  and selected structural constraints; explicit broader validation handles
  rules involving a tree rather than one locally assigned field.
- Streaming is the primary document API. The target memory bound is the
  header plus the largest single translation unit, independent of unit count.
- The supported vocabulary is TMX 1.4b and nothing else. Deprecated
  constructs (`<ude>`, `<map>`, `<ut>`, legacy `lang`, `srclang="*all*"`) are
  modeled; vendor extensions are rejected. Value-policy boundaries, such as
  the datetime parser's supported repertoire, are stated below.
- Strict is the only read policy. Unknown elements or attributes, invalid
  content models, malformed values, and broken document structure are errors.
- Successfully completed writer output must be spec-compliant TMX. This
  does not promise meaningful translations or completeness beyond the TMX
  requirements, nor intact output after an interrupted write or I/O failure.
- Python 3.14 minimum. Gates: `uv run ty check`, Ruff, and `uv run pytest`.
  Dependencies move through `uv` only.

## Out of scope

- Vendor dialects and extension elements.
- Lenient skip/preserve/normalize modes. No mode flag ships until a
  non-strict behavior is actually designed; leniency is not a boolean.
- A whole-document container. The header plus unit iteration is the document
  abstraction; a container would either hoard memory or wrap an iterator.
- `load()`/`dump()` convenience wrappers, v1's `ops/` package (redesigned
  later, against the settled domain), registry-backed language validation.
- Lexical fidelity. Comments, processing instructions, entity spelling,
  attribute order, and original datetime spellings are not preserved.
  Semantic text and modeled structure are; datetime offsets and supported
  fractional precision are retained, not normalized away.
- A full ISO 8601 parser or arbitrary-precision timestamps beyond Python's
  `datetime` representation.
- Parent tracking, cascading validation on child mutation, or a guarantee
  that failed assignments roll back all changes.

## Strictness has three layers

Keep schema rules out of XML assembly and text/tail handling. Projection
invokes the relevant independent layers rather than becoming a second schema
language. Some overlap between models and the DTD is intentional; independence
is useful when it catches drift.

1. **XML safety and well-formedness:** a hardened lxml parser configuration.
   Malformed XML is `TmxParseError`. Untrusted input declarations must not
   gain authority or cause external-resource access; internal-subset behavior
   remains an explicit parser-security question below.
2. **TMX structure:** a bundled, trusted `tmx14.dtd` validates each completed
   `<header>` and `<tu>` before model conversion. The reader separately
   enforces document order: one `<tmx version="1.4">`, one `<header>`, one
   `<body>`, only `<tu>` children. Models also reject structurally invalid
   construction, such as missing required children, and encode legal groups
   rather than letting callers construct arbitrary child orderings.
3. **Domain and prose rules:** Pydantic validators own values such as
   datetimes, integers, language tags, and prose enums such as `assoc`.
   Broader validation must handle relationships such as `<ude base>` being
   required when a child `<map>` carries `code`. Per-flow pairing and the
   cross-variant `x` advisory already have explicit APIs; the remaining
   whole-tree checks do not. The writer must call applicable checks, and
   strict reading must enforce them on consumed data. Neither projection
   direction alone currently provides that complete guarantee.

Namespaces: TMX 1.4b is namespace-free, so strict input is too. Foreign
namespaces are not matched by local name, since that would let another
vocabulary impersonate TMX. `xml:lang` is the one predefined-namespace
exception.

Comments and processing instructions are XML syntax, not TMX domain data. The
reader accepts and discards them and keeps their tails: `a<!--c-->b` reads as
`ab`.

## Architecture

Target responsibilities, with current placeholders identified above:

```text
src/hypomnema/
  __init__.py    public facade and __all__
  errors.py      error hierarchy and TmxWarning
  bcp47.py       standalone RFC 5646 grammar validation (stdlib only)
  validators.py enums, Annotated value aliases, parse/format functions
  models.py     all Pydantic TMX models (recursive family, one module)
  xml/
    dtd.py      loads and caches the bundled DTD; validates single fragments
    names.py    shared XML namespace and expanded xml:lang name
    content.py  plain text and the one text/child/tail interleave implementation
    parse.py    explicit element -> model dispatch with DTD-checked structure
    build.py    explicit model -> element dispatch, native attribute iteration
  validation.py explicit cross-node checks (decision 11); writer calls them
  io.py         TmxReader, TmxWriter, HeaderPeek
  resources/
    tmx14.dtd

The spec text and the prose-audit working documents live in `docs/`
(`Spec-TMX-1.4b.md`, `spec_audit.md`, `crossreference.md`), not in the
package; only the DTD ships as a resource.
```

Dependencies point one way: errors and the independent BCP 47 module, then
validators, then models, then validation, then XML, then I/O. `models.py`
never imports lxml or validation. Models and projection do not automatically
invoke broader checks; the future reader/writer must invoke the applicable
checks at their own conformance boundaries.

## Models

The implemented shared base configuration is:

```python
class TmxModel(BaseModel):
  model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True, validation_error_cause=True)
```

Deliberate `BeforeValidator` functions perform the few conversions we mean to
allow; nothing inherits Pydantic's loose coercion by accident. The base
enables `validation_error_cause=True` (GAPS decision 2).

### Shape and ordering

- Repeated fields are tuples. A shared validator accepts lists or tuples on
  input and stores tuples. This prevents unchecked list mutation, while
  `model.items += (value,)` rebinds and undergoes assignment validation.
- Metadata that can interleave stays interleaved. Never split notes from
  properties: use one ordered `Note | Property` tuple. The header retains
  its ordered `Note | Property | Ude` children.
- A translation unit has a metadata tuple and a separate **nonempty** variant
  tuple. Write metadata first, then variants, preserving each group's order.
  This matches `(note|prop)*, tuv+`; there is no legal interleaving across
  those groups to preserve. Settled field names: `metadata` and `variants` on
  the unit, `metadata` and `content` on the variant, `metadata` on the header
  (its one interleaved group).
- A variant likewise keeps metadata separate from segment content, as the
  current model already does. There is no `Segment` model: `<seg>` has no
  attributes or identity and is written around the variant's content tuple.
  Empty segment content is legal.
- Reject structurally invalid construction. `TranslationUnit()` without
  variants and `Ude(name="example")` without maps are errors in the target
  design, not construction states deferred to the writer's DTD check.
- Two inline-content grammars, exactly as the DTD says: `seg`/`hi`/`sub` take
  general inline content; paired and placeholder tags take text plus `<sub>`
  only. One shared union would accept illegal nesting.
- Field names are mechanical: the spec attribute with `-` and `:` replaced
  by `_`. So `o_tmf`, `xml_lang`, and otherwise verbatim, including `type`,
  `i`, and `x`. Class names stay descriptive (`TranslationUnit`, not `Tu`).

A representative node skeleton, unchanged in shape by the union decision:

```python
class Bpt(TmxModel):
  element: Literal["bpt"] = Field(default="bpt", frozen=True)
  i: TMXInteger
  x: TMXInteger | None = None
  type: str | None = None
  content: ModelSequence[SubContentItem] = ()
```

### Tagged input and JSON

Every node has a defaulted, frozen `element: Literal["..."]`. It identifies
the XML tag and the JSON node type. Explicit model constructors are the
preferred Python interface: `Hi()` already identifies its class, and callers
do not have to repeat the tag. The same applies to direct
`Hi.model_validate(...)` and already-typed instances in content sequences.

At a slot choosing between multiple model types, dictionaries/JSON must
supply `element`. Implemented **explicit discriminated unions** reject missing
or unknown tags rather than guessing from overlapping field shapes.

Mixed content remains ordinary strings plus a tagged model-only union:

```python
type InlineNode = Annotated[Bpt | Ept | Ph | It | Hi | Ut, Field(discriminator="element")]
type SegContentItem = str | InlineNode
```

Attach the discriminator to the model union, not to the surrounding
string/node union. No extra tag requirement is needed where the model type
is unambiguous, such as the `Sub` branch of `str | Sub`.

Tagged JSON preserves modeled node identity, so a dumped `<hi>` cannot
revalidate as `<ph>`. It is a model representation, not an XML preservation
format. Normal dumps include the tag; deliberately omitting defaulted fields
can remove it and is not the complete round-trip representation.

`TmxNode` is a separate, plain union of the 14 concrete node models. It types
projection inputs and outputs; it neither replaces the content discriminators
nor includes the bare `TmxModel` base. There are no standalone domain models
for `tmx`, `body`, or `seg`.

### Assignment and whole-tree validation

The guarantee is **successful assignment satisfies the model's local
constraints**. Tuples do not make child models immutable. Changing a child
can invalidate a relationship with its parent; no parent tracking or
cascading validation will be added to prevent that. Failed assignment is
not promised to be transactional.

Broader validators must be user-invocable and must run in the writer, in
addition to DTD validation. Do not assume `model_validate(existing_model)`
performs a deep check: Pydantic trusts existing instances by default. The
chosen explicit-validation API must actually recheck the necessary data,
with its implementation and instance-handling policy verified by tests.

## Values and serialization

- **Datetimes:** accept native `datetime` values and date-time strings
  representable and parseable by `datetime.fromisoformat()`. Require both
  date and time, rejecting date-only strings even though that parser accepts
  them. There is no additional `T`/`t` separator restriction; date-time syntax
  follows `fromisoformat()`. Reject standalone `date`/`time`
  objects, unrelated strings, and other input types. This is a deliberately
  bounded Python datetime policy, not a claim to implement all ISO 8601 forms.
- **Datetime preservation:** assume UTC when no timezone is provided.
  Otherwise retain the supplied timezone/offset in the model and its offset
  in JSON/XML output; do not force UTC. Preserve fractional seconds to
  `datetime`'s microsecond precision, with no truncation to whole seconds.
  Exact lexical spelling, arbitrary sub-microsecond precision, and a named
  timezone's Python identity in serialized text are not promised. The
  spec's basic UTC timestamp pattern is a recommendation. The shared formatter
  emits `YYYYMMDDTHHMMSS[.ffffff]Z` for zero offsets and retains other offsets
  as `±HHMM[SS[.ffffff]]`, including fractional offset seconds.
- **Decimal integers:** attributes treated as numbers must be unsigned
  integers. Reject negative native integers, booleans, and floats as well as
  signed, whitespace-padded, non-ASCII, or underscore-containing strings.
  Leading zeros are accepted; their spelling need not be retained. This is
  the library's explicit numeric policy, not something the CDATA DTD enforces.
- **Hexadecimal values:** `<map unicode>` and `<map code>` use `#x`-prefixed
  hex strings or native unsigned integers, with no booleans or floats.
  Unicode code points must be Unicode scalar values (0 through `0x10FFFF`,
  excluding surrogates, including private-use areas). Formatting keeps the
  `#x` prefix and hexadecimal digits rather than decimalizing the value.
- **Languages:** RFC 5646 ABNF well-formedness, not registry membership or
  other validity rules. Duplicate variants and extension singletons remain
  well-formed and are accepted. Tags are ASCII and case-insensitive, with
  their spelling preserved. `srclang` also accepts `*all*`, normalizing its
  case to that spelling. Registry checks can become an opt-in later.
- **Other values:** enums where the DTD or prose defines them (`segtype`,
  `pos`, `assoc`); whitespace-free `tuid`; ASCII `map ent` and `map subst`.
  Encoding names describe source material and stay strings, not Python
  codec objects. Unknown names produce a soft warning rather than rejection.

Value aliases use public Pydantic functional metadata (`BeforeValidator`,
`AfterValidator`, `PlainSerializer`) so a `TMXDatetime` is honestly a
`datetime`. Python-mode `model_dump()` retains native values for integer,
hexadecimal, and datetime aliases. JSON and XML use their string formatters,
sharing one formatter per value type; serializers must not turn Python-mode
dumps into strings. XML output still goes directly from model fields to the
projection walker rather than through `model_dump()`.

### Deprecated language attributes and warnings

`lang` is deprecated; `xml_lang` is the standard field for `xml:lang`.
Validate both as language tags, with these policies:

- A variant requires `xml_lang`; legacy `lang` cannot substitute for it.
- Notes and properties may omit either or both attributes. Legacy `lang`
  without `xml_lang` is accepted with a warning: technically correct, but
  deprecated; use `xml:lang` if possible.
- If both attributes differ, warn rather than reject. Compare
  case-insensitively, so `en-US` and `EN-us` do not conflict. Run advisory
  checks on validation/assignment and writer validation.
- Never synthesize one attribute from the other. If only `xml_lang` is
  supplied, `lang` remains `None` and is omitted from XML.

Warnings use `TmxWarning`, allowing callers to filter or escalate advisories.
Implemented advisories: unknown encoding names, legacy `lang` without or
differing from `xml_lang`, deprecated `<ut>` use, `<map>` without any of
`code`/`ent`/`subst`, and the cross-variant `x` mismatch (decision 13).

## Prose-rule audit

The complete spec prose has been audited against the DTD: a spec-only pass
(`spec_audit.md`) followed by a cross-reference against this plan, the
recorded decisions, and the code (`crossreference.md`). Mandatory prose rules
become validation rules; recommendations may warrant warnings; examples and
conventions never become requirements merely because the spec illustrates
them. Most findings are already covered by the value layer, excluded by prior
decisions, or deferred to XML/I-O work; the remainder is settled as GAPS
decisions 11-16:

- **Two-tier validation (11):** cheap local constraints and advisories run
  automatically in models; expensive cross-node correctness checks are public
  explicit functions that the writer always calls before converting anything
  to XML.
- **bpt/ept pairing and `bpt.i` uniqueness (12):** enforced per flow scope --
  a variant's segment content and each `<sub>`'s content, with `<hi>`
  transparent -- using per-`i` matching with ordering, deliberately not stack
  nesting, since the spec permits overlapping native code pairs.
- **Cross-variant `x` correspondence (13):** advisory (one `TmxWarning` per
  translation unit on disagreement), never an error; Level-2 parity is not
  enforced.
- **Inheritance/defaulting semantics (14):** documented resolution semantics,
  never materialized or enforced.
- **Warnings (15):** `<ut>` use and `<map>` without `code`/`ent`/`subst` warn;
  non-recommended `datatype`/`type` values do not.
- **`version` (16):** required present and exactly `1.4` on read; the writer
  always emits it.

The spec also contains DTD/spec mismatches worth knowing (the tmx15.dtd URL
typo, the undocumented deprecated `lang`, `version` required-vs-`#FIXED`) and
the seg-whitespace rule applies to `<seg>` only, not `<hi>`/`<sub>` -- see
`crossreference.md` section 5.

## Projection: direct dispatch

The model-to-XML mapping was first built as data-driven plans executed by
generic walkers, then rebuilt as direct dispatch after comparing both shapes
on a working slice. Plans moved mapping decisions into data without removing
them, and the interesting TMX shapes -- interleaved metadata, separated
variant groups, the `<seg>` wrapper, two inline grammars -- needed plan
vocabulary growth that read worse than explicit code. The plan-interpreter code
was deleted once direct dispatch won.

Parsing (`parse.py`) dispatches on the element tag and maps every attribute
explicitly to its model field, ending in `model_validate` so XML's string
attributes flow through the settled value aliases. `ValidationError` becomes
`TmxSpecError` with element and line context. The DTD validates the fragment
once before projection; recursion then works on DTD-checked structure.
`tmx`, `body`, and `seg` have no standalone domain models and are rejected
with a clear message.

Building (`build.py`) dispatches on the model type, writes attributes by
iterating the model's native fields (excluding the discriminator and explicit
child slots), and formats values with the shared per-type formatters,
including hexadecimal `Map` values. Content handling is explicit per shape:
plain text, ordered metadata/variant groups, the `<seg>` wrapper, and mixed
inline content.

`content.py` is the only code that touches lxml's text/tail mechanics, in
both directions. Earlier experiments exposed how easily sharing incorrect
interleave logic can make round-trip checks pass vacuously.

Text boundary (GAPS #9, settled for projection): models and in-memory lxml
trees preserve `None` versus explicitly empty text; serialized XML does not
-- both empty spellings parse back as `None`, and the future writer will emit
explicit start/end tags even for empty elements. Mixed content preserves
combined text, not string chunk boundaries. Structural formatting between
children is discarded only after DTD validation; `note`/`prop`/`seg` text and
inline tails are kept exactly; comments and PIs are dropped with their tails
retained. XML-illegal literal text or attribute values raise `TmxSpecError`
at the boundary; a scalar `map unicode="#x0"` remains legal.

Projection never pretty-prints. Future I/O may indent element-only containers
(`tmx`, `header`, `body`, `tu`, `tuv`, `ude`) but must never touch
text-bearing content.

The completeness safeguard is DTD-driven testing: tests parse the bundled DTD
and assert that models and both projection directions agree with it in both
directions -- every declared attribute exercised with distinct values,
nothing covered that is not declared, wrappers accounted for explicitly.
Drift fails a named test, not a customer file.

## Parser security

Input XML is untrusted. The proposed hardened `iterparse` configuration is:

```text
resolve_entities=False   load_dtd=False   attribute_defaults=False
dtd_validation=False     no_network=True  huge_tree=False
```

Only the packaged DTD has schema authority. Input DOCTYPEs are not preserved;
external DTD/resource loading must not occur. The intended reader rejects
unresolved entity nodes in content and does not weaken libxml2 limits with
`huge_tree=True`.

**Internal subsets remain unresolved (GAPS #10).** `load_dtd=False` does not
mean libxml2 ignores all internal declarations. Do not repeat the old claim
that internal subsets are never loaded or treat these flags as a security
proof. At parser implementation time, settle the policy for accepting or
rejecting internal declarations and verify actual behavior with hostile
fixtures: no external-resource access, no untrusted defaults changing modeled
data, and explicit entity handling. This question is deferred, not decided
by the wording of the proposed flags.

## Reader

Planned API:

```python
with TmxReader(path) as reader:
  if reader.header_peek.srclang != "en":
    return
  header = reader.read_header()
  for unit in reader:
    consume(unit)
```

- `header_peek` is a frozen dataclass built from the `<header>` start-event
  attributes, validated through the same `validators.py` functions, available
  without explicitly consuming header children. It lets consumers bail out
  without processing a potentially large header/body. It is not a TMX node
  and never touches projection; missing or invalid header attributes raise
  `TmxSpecError` at `__enter__`. Parser read-ahead must be accounted for when
  verifying early-exit behavior.
- `read_header()` visibly advances the stream through the header children and
  returns the full validated header model. There is no skip path: consuming
  the header must look like the side effect it is.
- Iteration yields one detached `TranslationUnit` at a time. At each `</tu>`
  the reader DTD-validates, converts, applies the relevant domain checks,
  clears the element, and deletes preceding siblings. Target memory is
  O(header + largest TU), constant in unit count.
- One iterator per reader, and it is a plain resumable cursor: `break`,
  `islice`, and raw `next()` are all fine. Lifecycle misuse (iterating before
  `read_header()`, a second iterator, use after close) raises
  `ReaderStateError`.
- Use a manual start/end event loop, not `iterparse(tag="tu")`: tag filtering
  suppresses events but still builds skipped subtrees. Track depth and check
  stray text between body children explicitly, because removed TUs mean no
  complete `<body>` ever exists for the DTD to check.
- Strictness covers what was consumed. Early exit does not validate unread
  bytes.

Paths and binary streams are accepted, text streams rejected. The reader
closes only what it opened. Lifecycle, security, read-ahead, and bounded-memory
claims all await implementation and verification.

## Writer

Planned API:

```python
with TmxWriter(destination, header=header) as writer:
  for unit in units:
    writer.write(unit)
```

- `__enter__` validates the complete header's domain/prose constraints,
  builds it, and DTD-validates it before the destination sees a byte. Then
  lxml's `xmlfile` writes the declaration, optional canonical DOCTYPE
  (`doctype=True` emits `<!DOCTYPE tmx SYSTEM "tmx14.dtd">`, default off),
  root, header, and opening `<body>`.
- `write(unit)` checks the unit's current domain/prose constraints, builds
  one `<tu>`, DTD-validates it, and commits it in a single `xmlfile.write`
  call. Validation cannot trust that a mutable model is still valid merely
  because it was valid at construction. DTD validation alone cannot enforce
  the prose rules.
- A validation failure may be invalid caller data after mutation or a
  model/projection bug; it is not necessarily an internal bug. The current
  lifecycle direction is to fail and stay failed, not silently skip bad
  units. Exact error classification and partial-output behavior will be
  settled and tested with the writer; callers wanting skip-bad-units
  semantics use explicit validation before writing.
- Successfully completed output is spec-compliant TMX. The writer must check
  all applicable document-level as well as fragment-level rules identified
  by the audit; per-TU DTD success is not by itself proof of this guarantee.
- Output is namespace-free, UTF-8 by default. Input encoding never leaks into
  output decisions. Datetime offsets/precision are modeled values, unlike
  the input document's transport encoding, and are retained.
- Streaming output is not transactional. With a usable destination, cleanup
  may close scopes around a successfully written prefix, but exceptions,
  interrupted writes, or I/O failures can leave partial output. No blanket
  well-formedness/compliance promise covers failed writes. Callers needing
  all-or-nothing output write to a temporary path and rename on success.

## Errors

Planned TMX error hierarchy:

```text
TmxError
├── TmxParseError      bytes are not usable XML
├── TmxSpecError       data violates the TMX contract
├── ReaderStateError   reader lifecycle misuse
└── WriterStateError   writer lifecycle misuse
```

`except TmxError` catches everything the I/O APIs raise about TMX itself.
`OSError` and system exceptions propagate untouched. Direct model validation
of rejected user input raises Pydantic `ValidationError`, preserving its
field locations and aggregated detail rather than replacing it with a custom
wrapper.

Enable `validation_error_cause=True` for underlying exceptions to appear as
an exception-group cause where applicable. This does not make Pydantic catch
validator `TypeError`s: deliberately report bad user input through supported
validation errors and preserve translated causes without broadly catching
programming mistakes or manufacturing a `TypeError` for every rejection.

The standalone BCP 47 API remains distinct: its predicate returns false for
non-string input; its raising validator raises `TypeError` for non-strings
and `ValueError` for malformed tags.

`TmxWarning(UserWarning)` is a separate advisory category, not part of the
error hierarchy. It already exists; the TMX exception classes do not yet.

## Testing

Tests live under root `tests/`. Start with flat modules (`test_bcp47.py`, then
`test_validators.py` and `test_models.py`); introduce an XML subtree when there
is XML code to test. Use plain test functions, parametrized input/expected
examples, and inline setup. Shared fixtures are for genuinely shared needs,
not a prerequisite for creating a model.

- **Grammar:** derive expectations from the RFC independently of the
  implementation's tables. This is the first implemented test slice.
- **Values:** exercise parse/format functions and strict Pydantic aliases,
  including native inputs, error boundaries, warnings, and both Python and
  JSON serialization. Assert expected values, not only self-round-trips.
- **Models:** lock down tuple behavior, explicit discrimination, recursion,
  cardinality, metadata order, assignment boundaries, and tagged JSON.
  Broader-rule tests follow the prose audit and chosen validation API.
- **Projection:** hand-authored XML to expected models, hand-authored models
  to expected XML structure/text, and additional round trips. Reader/writer
  agreement alone is not an independent oracle. Include DTD-derived
  agreement tests and exact mixed-content/whitespace assertions.
- **I/O:** lifecycle, stream ownership, error context, malicious XML,
  document structure, and bounded memory once implemented. Small security
  tests run normally; genuinely expensive memory/performance checks may be
  separately marked. Include native lxml allocations in memory measurements,
  not only Python allocations.
- **Packaging:** verify the bundled DTD in a built wheel and load it via
  package resources outside the source checkout.

`uv run pytest` runs every current test by default. No mocks are needed for
the existing grammar suite. Coverage and property-based testing may be useful
later, but no dependencies or coverage target have been adopted.

## Performance posture

Keep the earlier experimental design conclusions, and re-measure when a
real decision depends on them rather than treating historical results as
verified performance of the current placeholders:

- Plain Pydantic validation is the default. `model_construct` is not a
  validation-bypassing optimization strategy.
- XML output goes model, plan, element. `model_dump()` in the middle adds
  allocations without serving the projection design.
- Streaming, not weaker validation, is the answer to memory.
- Benchmarks need an independent oracle (expected XML plus DTD validation
  plus read-back), and compared implementations must not share the algorithm
  under test. Shared mixed-content bugs can make equivalence checks pass
  vacuously.
- Earlier per-fragment DTD-cost experiments (scripts since removed; their
  conclusions are retained here) suggest validation is affordable, but measure
  in the first actual end-to-end streaming benchmark before optimizing
  anything; there is no current integrated pipeline to benchmark yet.

## Roads deliberately not taken

- XML backend abstraction: one client, pure overhead.
- `model_dump()`-based XML output: adds an unnecessary intermediate form.
- Introspection-based projection compiler, and then data-driven plans: both
  superseded by direct dispatch plus DTD-derived agreement tests.
- Separate note/prop lists: reorders valid documents. Separating a TU's
  metadata from its variants is different and matches the DTD's groups.
- One universal inline union: accepts DTD-illegal nesting.
- Inferring node identity from dictionary shape: require explicit tags at
  heterogeneous model slots instead.
- Registry language validation by default: validity is not well-formedness.
- Forced UTC conversion or second-only timestamps: retain supplied offsets
  and supported fractional precision instead.
- Automatic parent revalidation on child mutation: use local assignment
  checks and explicit broader validation, with the writer as final boundary.
- Preserving input DOCTYPEs, transport encodings, or timestamp spellings:
  lexical/transport facts are not the preservation contract.

## Sequence from here

Work create, then test, then document, per piece, with review between stages.
Do not turn pending decisions or known gaps into passing tests that bless
accidental current behavior.

1. **Review the BCP 47 test slice.** (Done; the API now says well-formed.)
2. **Bring values into line with the decisions above.** (Done; GAPS 1-3
   implemented, tested, and adversarially reviewed.)
3. **Bring model shape into line.** (Done; GAPS 4/5/8 plus the decision-15
   warnings, field names settled, tested and reviewed.)
4. **Audit the full TMX prose and design broader validation.** (Done; the
   audit ran as two independent passes and decisions 11-16 are recorded and
   implemented.)
5. **Build projection.** (Done; DTD loader with cold-load and attached-
   fragment coverage, direct dispatch in both directions, shared content
   interleave, GAPS #9's text boundary settled, DTD-driven agreement tests,
   and the deep-recursion regression. The `Ude.base` requirement and broader
   whole-tree checks remain decision-11 work, not projection gaps.)
6. **Build reader and writer.** Reapply the earlier XML spike conclusions
   (lifecycle, buffering, DTD cost), resolve
   GAPS #10's internal-subset/entity policy, and verify hardened parsing,
   validate-before-commit, lifecycle, domain conformance, and bounded memory.
   Then add the corresponding I/O suite and end-to-end streaming benchmark.
7. **Finish distribution and public surface.** Verify wheel resources, add
   the facade/`__all__`, update the README, and document the settled API and
   guarantees. CI and any additional test tooling can be chosen when needed.

A failed experiment changes this plan, not an excuse to silently weaken the
agreed validation or safety contract.
