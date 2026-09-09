# Validation contract review

Working review sheet, not a replacement for `PLAN.md` or a list of behavior to
preserve just because the implementation currently does it. Edit the **Decision**
lines directly. Decisions 1–5 and 8 are implemented and tested, as are the
decision-11/12/13 explicit checks and the decision-15 warnings; decision 6 was
resolved by the prose audit into decisions 11–18. Decision 7's writer-side half
awaits the writer. Question 9 is resolved for the projection layer (decision
below); its writer half awaits the writer. Question 10 is decided (below); its
verification awaits the reader.
The XML projection (decisions 17–18) is implemented, reviewed, and tested: the
suite is 1088 tests, 225 of them XML (build 64, content 38, dtd 19, parse 58,
contract 46), all clean under Ruff, `ty`, `pytest`, and `pytest -W error`.
Observations retain the context of the initial review; a recorded decision is
not a claim that the code already implements it beyond the suites named above.

Sources of truth:

- [`PLAN.md`](PLAN.md): intended library policy and architecture.
- [TMX 1.4b specification](Spec-TMX-1.4b.md): value semantics,
  cross-field requirements, and recommendations that the DTD cannot express.
- [TMX DTD](../src/hypomnema/resources/tmx14.dtd): XML attributes and content models.
- [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html), sections 2.1 and 2.2.9:
  language-tag syntax and the distinction between well-formedness and validity.

## Values

### 1. Native integers bypass the lexical restrictions

**Observed:** `parse_integer()` rejects negative strings, but passes native
negative integers through. `parse_hex_integer()` does the same. Their aliases
have no nonnegative constraint; `TMXUnicodeCodePoint` separately checks its range.
Both parsers also pass `bool` through, relying on downstream strict validation.

**Proposed direction:** enforce the same numeric domain for Python, XML, and JSON
inputs. Decide whether the standalone parser functions reject booleans themselves
or deliberately rely on their Pydantic aliases. The decimal digit-only policy is
in the plan; the spec describes `i`, `x`, and `usagecount` as numbers, while the
bundled XML DTD uses CDATA, so do not claim the DTD enforces this value policy.

**Decision:** We take the stance that attributes the spec defines as "Numbers"
MUST be valid unsigned integers. So negative ints (even native ones) error,
bool error, leading zeros are fine, floats error as well.

### 2. Validation exception boundary

**Observed:** decimal, hexadecimal, and datetime converters raise `TypeError` for
unsupported Python types. Pydantic does not wrap validator `TypeError` as
`ValidationError`. The plan promises plain Pydantic `ValidationError` for bad
direct model construction and eventual `TmxSpecError` wrapping at the XML boundary.

**Proposed direction:** bad user values reaching models should produce
`ValidationError`, without broadly catching programming errors. Standalone BCP 47
functions have a separate, explicit contract: the predicate returns false for
non-strings; the raising validator raises `TypeError`.

**Decision:** bad user input reaching models produces a catchable Pydantic
`ValidationError`, with underlying causes retained where applicable. Use Pydantic's
native error aggregation and enable `validation_error_cause=True`; the cause may
be an exception group rather than a single `TypeError`.

Validators must report rejected input through Pydantic's supported validation-error
mechanism. Deliberately translated underlying exceptions retain their chains, but
we neither manufacture a `TypeError` for every rejection nor broadly catch
programming errors. Enabling error causes does not itself make Pydantic catch
validator `TypeError`s. The standalone BCP 47 exception contract stays unchanged.

### 3. Datetime input breadth and serialization modes

**Observed:** `parse_datetime()` delegates to `datetime.fromisoformat()` after
requiring a `T`/`t` somewhere in string input. This is not a complete implementation
of every ISO 8601 form. It preserves input offsets, attaches UTC to naive values,
and truncates microseconds; formatting emits canonical UTC. `PlainSerializer`
currently serializes integer, hex, and datetime aliases to strings in both Python
and JSON dumps, not only JSON.

**Questions:** does “any ISO 8601 instant” mean the subset accepted by this parser,
or a broader explicitly enumerated set? Should `model_dump()` expose native values
and only JSON/XML use strings? Normalization and accepted syntax should be tested
against explicit examples, not just self-round-trips.

**Decision:** Python-mode `model_dump()` exposes native values for the integer,
hexadecimal, and datetime aliases. JSON/XML serialize these values as strings.

Accept native `datetime` values and date-time strings representable and parseable
by `datetime.fromisoformat()`, not the full ISO 8601 repertoire. Input must include
both date and time: date-only strings are rejected even though `fromisoformat()`
accepts them. Date-time syntax follows that parser rather than the current code's
narrower `T`/`t` separator requirement. Date objects, time objects, unrelated strings,
and other input types are rejected. Do not build a broader ISO parser or claim
full ISO conformance.

Assume UTC when timezone information is absent. Preserve an explicitly supplied
timezone/offset in the model and its offset in JSON/XML output; do not convert to
canonical UTC. This supersedes the original plan's canonical-UTC policy. It does
not promise lexical preservation of input strings or preservation of a named
Python timezone's identity in serialized timestamps.

Preserve fractional seconds to the precision supported by `datetime` (microseconds)
in both the model and JSON/XML output. Do not truncate to whole seconds. This
supersedes the original plan's truncation policy; parsing remains bounded by
`datetime.fromisoformat()` rather than promising arbitrary-precision timestamps.

Offsets finer than whole minutes -- seconds and fractional seconds -- are
accepted wherever `fromisoformat` accepts them and serialized back exactly
(`±HHMM[SS[.ffffff]]`): output offsets are never rounded to whole seconds, and
formatting must never land outside the parser's representable offset range. A
`tzinfo` whose `utcoffset()` is `None` is behaviorally naive and is stamped UTC
like any naive value.

## Models

### 4. Tagged input and union discrimination

**Observed:** every node has a frozen literal `element` with a default, but the
unions are ordinary Pydantic unions, not explicitly discriminated as the plan says.
Multiple node types have overlapping shapes when the tag is absent (for example,
inline nodes with only optional fields). Dumped JSON carries the tag; hand-authored
nested dictionaries need not.

**Questions:** must nested dictionaries include `element`? Should ambiguous untagged
input be rejected rather than inferred? Keep convenient constructors such as
`Hi()` distinct from the rules for selecting a node type from a union. Mixed
string/node content needs a discrimination approach that still accepts strings.

**Decision:** use explicit `element` discrimination for heterogeneous model unions
(option 2). Node identity comes from the chosen class or an explicit tag, never
from guessing based on field shape.

- Keep `element` defaulted and frozen: constructors such as `Hi()` and direct
  validation through `Hi.model_validate(...)` already identify the class and do
  not require the caller to repeat its tag. Already-typed model instances remain
  accepted in content sequences.
- Dictionaries/JSON in slots choosing between multiple model types must carry
  `element`. Reject missing or unknown tags; do not fall back to inference.
- Mixed content remains ordinary strings plus a tagged model-only union. Attach
  the discriminator to the model union, not to the surrounding string/node union.
- No additional tag requirement where the model type is already unambiguous,
  such as the `Sub` branch of `str | Sub`.

The extra verbosity for hand-authored dictionaries is acceptable; explicit model
constructors are the preferred Python construction interface. (Implemented and
tested in `tests/test_models.py`.)

### 5. Structurally incomplete models versus writer failures

**Observed:** `TranslationUnit()` and `Ude(name="example")` are accepted despite
DTD `tuv+` and `map+` requirements. `TranslationUnit.items` also permits notes after
variants, which the DTD rejects. This followed the original plan's “DTD owns order
and cardinality” direction, but conflicted with its claim that a writer DTD failure
necessarily meant an internal model/projection bug rather than bad caller data.
The revised plan incorporates the decision below; it is implemented and tested.
An empty variant content tuple is different: it can represent a legal empty
`<seg/>`, because the XML builder will supply the wrapper.

**Questions:** may models represent incomplete construction states? If yes, what
error does writing a structurally invalid model raise, and does it permanently
fail the writer? If not, where are these structural constraints enforced without
creating a second schema implementation?

**Decision:** reject structurally invalid construction, including a translation
unit without variants or a user-defined encoding without maps. Models own the
corresponding structural constraints as well as value validation; this intentionally
revises the plan's exclusive assignment of cardinality to the DTD. Independent DTD
validation and agreement tests remain safeguards against drift.

Separate a translation unit's metadata (`Note | Property`, interleaved in one tuple)
from its variants (a separate nonempty tuple). Keep each group's order and write
metadata before variants, as the DTD requires. Do not split notes from properties.
Variants likewise keep metadata separate from segment content, as they already do.
An empty segment remains legal. Settled field names: `metadata`/`variants`
     on the translation unit, `metadata`/`content` on the variant, `metadata`
     on the header.

This promises structural correctness, not meaningful translations or completeness
beyond what the TMX contract requires.

### 6. Cross-field and segment-wide spec requirements

**Observed:** the spec's `Ude.base` requirement when a map carries `code` is not
implemented; the model docstring explicitly defers it. The spec also requires
paired `bpt`/`ept` codes within a segment and unique `bpt.i` values within that
segment (see the `bpt`, `ept`, and `i` sections). These are not DTD constraints and
there are currently no corresponding model validators.

**Proposed direction:** audit mandatory prose rules separately from recommendations
before claiming complete strictness. Decide validation scope for inline pairing,
including nested `hi`/`sub` content; the spec explicitly allows overlapping native
code pairs, so ordinary XML-style stack nesting would be the wrong rule.

**Decision:** audit the complete spec prose before claiming full strictness.
Mandatory requirements become validation rules. Recommendations may warrant
warnings where actionable, but not every departure warrants one. Examples and
conventions must not accidentally become requirements. The detailed audit and
placement of individual rules will be discussed when this work begins.

### 7. Assignment safety for constraints involving several nodes

**Observed:** tuple fields prevent unchecked list mutation, but their child models
remain mutable. Adding `code` to an existing child `Map`, for example, would not
trigger validation of its parent `Ude`. `validate_assignment` on each model alone
cannot guarantee that an already-built tree still satisfies parent-level rules.

**Questions:** is assignment validation a local guarantee only, with complete
validation before serialization? Or should the model API prevent changes that
invalidate parents? Avoid promising that tuples solve cross-node mutation safety.

**Decision:** successful assignment satisfies the model's local constraints.
There is no promise that a failed assignment rolls back all changes, and no parent
tracking or cascading revalidation when a child changes.

Broader rules, such as the `Ude`/`Map` relationship, must be checked by explicit
validators/functions available to callers and by the writer. Their exact API is
still to be designed. Do not assume `model_validate(existing_model)` deeply
revalidates existing instances: Pydantic trusts instances by default, so any such
entry point must deliberately ensure the required validation actually runs.

Two edge behaviors that follow from this policy: (a) per-assignment checks
cannot see two-step cycles -- `h1.content = (h2,); h2.content = (h1,)` passes
each local check and produces a model that fails serialization; cycle detection
is a candidate for the decision-11 explicit checks and the writer boundary, and
the hazard is documented for users. The cycle outcome itself is not covered by
a cycle-detection test, so calling it "pinned" would overstate it. (b)
`model_construct` and `model_copy(update=...)` bypass validation entirely and
can embed invalid states; only a data round trip
(`model_validate(model.model_dump())`) is a deep check today. Only (b) is
pinned by tests.

The writer is the final conformance boundary: it must check applicable domain/prose
rules as well as DTD structure before accepting data for output. Successfully
completed output must be spec-compliant TMX, not necessarily meaningful or complete
translation data. This does not make streaming output transactional or guarantee
intact bytes after an I/O failure; partial-output failure semantics remain part of
the later writer design.

### 8. Deprecated language attributes

**Observed:** `Note.lang` and `Property.lang` use `TMXLanguageTag`, whereas
`TranslationUnitVariant.lang` is plain `str`. The DTD still requires `xml:lang` on
`tuv`; legacy `lang` is permitted in addition, not as a DTD substitute for it.

**Proposed direction:** apply the language value contract consistently unless the
spec gives a reason not to. Explicitly settle whether simultaneously supplied
`lang` and `xml_lang` may differ; do not introduce equality or fallback behavior
without a spec/policy basis.

**Decision:** validate both language attributes consistently as language tags.
For `TranslationUnitVariant`, `xml_lang` is required; providing only legacy `lang`
is an error. For `Note` and `Property`, both attributes remain optional. A legacy
`lang` without `xml_lang` is accepted with a warning: it is technically correct,
but `lang` is deprecated; use `xml:lang` if possible.

When both attributes are present and differ, warn rather than reject. Compare tags
case-insensitively, so `en-US` and `EN-us` do not conflict. Apply the advisory checks
at validation/assignment and writer validation, including when child mutation may
have changed the state. Do not normalize one attribute from the other.

When only `xml_lang` is supplied, leave `lang` as `None` and omit that attribute
from XML output.

## XML boundary

### 9. Semantic normalization and XML-representable text

**Observed:** `Note.text` and `Property.text` accept both `None` and `""`. Mixed
content tuples may contain adjacent strings and empty strings. XML does not
necessarily preserve those distinctions. Plain Python strings can also contain
characters that XML 1.0 cannot represent, independently of the valid Unicode scalar
range used for the textual `map unicode="#x..."` attribute.

**Questions:** normalize text at model construction or define round-trip equality
semantically? At which boundary are XML-illegal text characters rejected, with what
error? Tests must preserve significant whitespace while allowing only intentional
normalizations. Do not equate a textual code-point attribute with literal XML text.

**Decision:** `Note.text`/`Property.text` keep `None` and `""` distinct in the
models and in in-memory lxml; on serialized XML both empty states parse back to
`None`, and the future writer will spell every note/prop/seg with explicit
start/end tags even when empty (writer not yet implemented). Mixed content
preserves combined text, not chunk boundaries: adjacent and empty strings in a
tuple collapse into whatever the serialized text reads back as. Structural
formatting whitespace is discarded only after DTD validity has been
established. Text inside note/prop/seg and inline text and tails are preserved
exactly; comments and PIs are discarded but their tails are retained, and a
tail belongs to the parent's content, never to the child model. `<map>` is
EMPTY: even formatting whitespace inside it is invalid. XML-illegal literal
text or attribute values raise `TmxSpecError` at projection time; the scalar
`map unicode="#x0"` remains legal.

### 10. Input DOCTYPE and entity wording needs an executable contract

**Observed:** the original plan claimed internal subsets were never loaded.
Disabling external DTD loading does not mean libxml2 ignores all internal-subset
declarations. The revised plan marks this as unresolved: parser flags are
implementation choices, not themselves proof of the security guarantee.

**Proposed direction:** settle the desired externally observable policy (for example,
DOCTYPE accepted but never authoritative, versus rejecting internal declarations).
Then verify no external-resource access, no untrusted defaults changing the modeled
data, and the chosen entity behavior using hostile fixtures. Do not weaken parsing
limits merely to make a fixture pass.

**Update:** the package DTD now loads through `importlib.resources`, tested in a
cold process independent of the working directory; wheel packaging is still
pending (housekeeping below). A workaround is in place: lxml 6.1.3 attaches a
synthetic `xmlns:xml` declaration when validating a fragment that is not its
document's root, so `validate_fragment()` deep-copies such fragments into an
independently owned tree for validation only and projects the untouched
original. Whether an explicit `xmlns:xml` declaration is intrinsically illegal
is deferred upstream -- do not assume it is. The entity-rejection helper tests
exercise our error surface; they are not a parser-safety proof.

**Decision (recorded 2026-09-09, after hostile-fixture probing of libxml2
behavior):** input DOCTYPEs are accepted and ignored; internal subsets are
accepted too. The bundled DTD remains the only validation authority -- the
document's own subset never participates in validation, and external subsets
are never fetched (`load_dtd=False` holds, verified). The reader validates
values, not provenance; the residual behavior is a documented caveat, not a
rejected input class.

What the probing established, against the proposed flag set
(`resolve_entities=False`, `load_dtd=False`, `attribute_defaults=False`,
`dtd_validation=False`, `no_network=True`, `huge_tree=False`):

- libxml2 always processes the internal subset, whatever the flags say. An
  internal-subset `ATTLIST` default fills in an *absent* attribute (specified
  values always win), even with `attribute_defaults=False`.
- Entity references in *attribute values* are always expanded -- an XML spec
  mandate that `resolve_entities=False` cannot prevent. Internal-subset
  entities expand silently in attributes.
- Entity references in *content* stay `_Entity` nodes under
  `resolve_entities=False`; the projection already rejects them
  (`TmxSpecError`).
- Attribute references to *external* entities are parse errors under
  `resolve_entities=False`; they are never resolved, fetched, or read.
- `no_network=True` does **not** block `file://`. The protection against local
  file disclosure is `resolve_entities=False`, not the network flag.
- External-subset declarations are not applied (`load_dtd=False` verified);
  our fragment validation uses our own DTD object regardless, so a document's
  subset can never change what we accept structurally.
- Nested internal-entity expansion (billion laughs) hits libxml2's
  amplification cap with `huge_tree=False`.
- `docinfo.internalDTD` is truthy for *any* DOCTYPE, including
  external-id-only ones, and ATTLIST declarations are not introspectable
  through it. `iterparse` has no doctype event; a mid-feed `XMLPullParser`
  tree does expose docinfo. These facts made cheap detection *possible*, but
  detection was rejected as policy (below).

Why acceptance is safe enough to document rather than reject: the injection
surface is already fenced by the library's own strictness. Injection only
fills absent attributes; unknown attributes and elements are `TmxSpecError` in
projection, and every value flows through the model validators, so a hostile
`ATTLIST version CDATA "9.9"` is rejected, not honored. For every accepted
document D there is an equivalent D (same values spelled out, DOCTYPE removed)
that is also accepted and produces an identical model. The accepted *model
set* is unchanged; only the set of byte sequences producing it grows. The
residual cost is therefore epistemic: the docs must not claim byte-level
attribute-presence observability. Consumers needing byte-strict presence
semantics can pre-screen with `docinfo.internalDTD` themselves.

Roads deliberately not taken: a hand-written prolog scanner to reject internal
subsets (owning XML machinery to enforce a property whose violation is
model-invisible), and rejecting all DOCTYPEs (a `docinfo.internalDTD` check
could do it, but it breaks canonical `<!DOCTYPE tmx SYSTEM "tmx14.dtd">`
compatibility for no protective gain).

This revises decision 16's wording: the version presence check runs on
post-parse data -- "version present in the accepted model, where the
document's internal subset may supply it."

Verification list (to implement with the reader's parser configuration;
none of this is pinned by tests yet):

1. **No external-resource access:** `file://` and `http://` external entities,
   referenced from content and from attribute values, under the reader's exact
   parser configuration: content references surface as `_Entity` rejection,
   attribute references are parse errors, nothing is fetched. This is the
   load-bearing guarantee (the network flag alone does not provide it).
2. **Content entity rejection end to end:** unresolved entities in content
   produce `TmxSpecError` via the existing `content.py` rule, re-verified
   through the streaming reader path, not only fragment projection.
3. **Predefined entities and character references** (`&amp;`, `&lt;`, `&#xN;`)
   parse normally through the same path.
4. **Internal-subset ATTLIST fills an absent required attribute:** accepted;
   the resulting model equals the model of the same document with the value
   spelled out (the D-equivalence claim, pinned by test).
5. **Internal-subset ATTLIST injects an invalid value** (`version="9.9"`, a
   malformed language tag): rejected by model validation with
   `TmxSpecError`, proving the fence is model validation, not the flags.
6. **Internal-subset ATTLIST injects an unknown attribute:** rejected
   (`TmxSpecError`), bounding the injection surface to model-valid,
   TMX-known attribute names.
7. **Internal-subset entity expanded in an attribute value:** accepted
   (documented caveat), model equals the spelled-out equivalent.
8. **External-subset declarations are inert:** a DOCTYPE naming an external
   DTD (existing or nonexistent) with hostile `ATTLIST`/entity declarations
   changes nothing; the document parses as if the subset were absent.
9. **Amplification cap:** nested internal-entity expansion exceeds the cap
   and fails without unbounded memory (`huge_tree=False` in effect).
10. **Encoding independence:** the hostile fixtures above behave identically
    with a BOM and in UTF-16; no security property may depend on the
    transport encoding.

## Prose-rule audit (decisions 11-18)

Recorded after the completed spec-vs-DTD audit (independent spec-only pass in
`spec_audit.md`, cross-reference against this sheet and the code in
`crossreference.md`). These decisions supersede the "to be settled when
this work begins" hedges in decisions 6 and 7.

### 11. Broader validation is two-tier

**Decision:** cheap local constraints and cheap advisories run automatically
through Pydantic validation and assignment. Expensive cross-node correctness
checks are never automatic: they are public, explicit functions in the
`validation` module that the user invokes at their own runtime cost, and the
writer always calls them before converting a model to XML -- successfully completed output
must be spec-compliant. Explicit check functions raise Pydantic
`ValidationError` at the model level (consistent with decision 2); the writer
wraps failures into `TmxSpecError` with context. Post-mutation revalidation
still requires an explicit call; there is no parent tracking (decision 7).

### 12. bpt/ept pairing and `bpt.i` uniqueness: per-flow scopes

**Decision:** scopes are the "flow" containers: a variant's segment content,
and each `<sub>`'s content. `<sub>` represents an embedded segment's own flow,
so its inline elements pair within it and reuse of `i` across scopes is legal.
`<hi>` is transparent: a highlight lives in the current flow, so its inline
elements join the enclosing flow's namespace (including a `<sub>` scope when
nested there). Within one flow, in document order: every `bpt` must have a
corresponding `ept` and every `ept` a corresponding `bpt` (an unmatched element
of either kind is an error), `i` values are unique among `bpt`s and among
`ept`s, and each `ept` appears after its `bpt`. Matching is per-`i` with
ordering, deliberately NOT stack nesting: the spec permits overlapping native
code pairs. Enforced by the decision-11 explicit checks, plus DTD-independent
agreement tests. Reaffirmed as written. The spec prose ("unique within given
seg") is ambiguous: independent pairing with seg-wide `i` uniqueness is a
plausible alternative reading, deliberately not selected. Treat this policy as
our documented interpretation, not an unambiguous spec mandate; an earlier
hedge here ("only the bpt direction is spec-mandated") overlooked the `ept`
definition and was removed rather than resolved by changing behavior.

### 13. Cross-variant `x` correspondence is advisory

**Decision:** the spec's `x`-matching and Level-2 parity text (§4.3 under
"Assuming:") defines tool capability, not document validity; enforcing tag
parity as an error would reject DTD-valid files. When a variant's set of `x`
values (from `bpt`, `it`, `ph`, `hi`, including nested content) disagrees with
a sibling variant's, emit one `TmxWarning` per translation unit as part of the
tu-level explicit check. Never an error.

### 14. Inherited and defaulted attributes are documented, not enforced

**Decision:** the spec's inheritance semantics (tu `segtype`/`srclang` fall
back to the header, `datatype` defaults to "unknown", header `adminlang`
languages note/prop) are instructions for applications interpreting missing
attributes -- an app-level concern like registry validity, out of our
correctness-and-grammar scope. Nothing is materialized into models (that would
break round-trip fidelity) and nothing is enforced. Resolution semantics are
documented for consumers. The `srclang`-equals-source-`xml_lang` clause is
descriptive of producers, not a validation rule.

### 15. Deprecation and recommendation warnings

**Decision:** using the deprecated `<ut>` warns with `TmxWarning` (automatic,
cheap, following the legacy `lang` pattern from decision 8). A `<map>` with
none of `code`/`ent`/`subst` warns (the spec's "should", R1 in the audit).
Unknown `datatype`/`type` values do not warn: their recommended lists are
explicitly non-exhaustive, so any string is contract-legal. Standard Python
warning semantics apply on top: under default filters, identical advisories
deduplicate per message and call site, and `-W error` escalation turns them
into exceptions rather than `ValidationError`s. A far-future
convenience (autocomplete-friendly `Literal | str` aliases for the recommended
lists) is parked, not scheduled.

### 16. `version` is required on read

**Decision:** the reader requires `<tmx version="1.4">` at init -- present AND
exactly `1.4` -- and raises `TmxSpecError` otherwise; the writer always emits
it. `attribute_defaults=False` makes absence observable, and the internal-subset
verification from question 10 must confirm no hostile fixture can inject the
attribute.

### 17. Projection is direct, model-driven, and narrow

**Decision:** the superseded "hardcoded per-model projection plans" approach
(since deleted) was replaced by direct projection.
`from_element()` runs the package DTD once over the fragment, then matches the
element tag against the model classes and validates explicit attributes with
`model_validate()`. `to_element()` accepts only `TmxNode` models and directly
iterates native fields through shared formatters (hex for `Map.unicode`/`code`,
datetime, integers). `TmxNode` is a closed union of the 14 node models under a
separate `TmxModel` base; there are no standalone models for `tmx`/`body`/`seg`.
Neither direction performs broader domain or whole-tree validation:
`from_element()` checks the DTD plus per-model constraints only, and
`to_element()` builds a detached element tree -- the caller owns domain checks
and DTD validation of the output. Projection never pretty-prints; the future
I/O layer pretty-prints element-only containers and never text-bearing
content. Content is built eagerly per element (fixing recursion on deep valid
250-`hi` trees); no guarantee is made for arbitrary depth or cyclic models.

### 18. XML test structure: shared fixtures, local oracles, narrow warnings

**Decision:** the XML suites share fresh construction scaffolding only
(`minimal_node`, `minimal_header`, and `valid_tmx_document` fixtures in
`tests/xml/conftest.py`); examples and oracles stay local to each test module.
`TmxWarning` advisories are muted only where legitimately emitted, via explicit
narrow `filterwarnings` marks, never globally.

## Housekeeping / verification later

- The plan now reflects the existing `ruff.toml` settings: two-space indentation
  and 120-character lines. No formatter configuration was changed.
- The error hierarchy has `TmxError`, `TmxSpecError`, and `TmxWarning`; `io.py`
  and the reader/writer facade are placeholders, as are full-tree validation,
  the decision-6 `Ude.base`/`code` rule, a cycles policy, and a hardened I/O
  lifecycle. These are unfinished work, not failing-test targets.
- Verify the DTD is included in a built wheel and loadable through package resources
  outside the checkout. The tested cold-process, cwd-independent
  `importlib.resources` load runs against the checkout, not a wheel.
- The lxml attached-fragment `xmlns:xml` workaround (deep-copy for validation
  only) is housekeeping, not policy; revisit if a fixed lxml changes the
  behavior.
- No coverage/property-testing dependency or CI configuration has been added.
  Explicit examples are the first slice; choose additional tooling when useful.
