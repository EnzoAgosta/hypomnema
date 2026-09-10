# Spec-audit × hypomnema cross-reference report (independent subagent output)

**Legend.** A = handled by implemented value layer or a recorded decision; B = decided against / out of scope; C = deferred to XML/reader/writer (or step-4 prose-audit) work per PLAN/GAPS; D = open, treated in detail below.

## 1. Mandatory rules M1–M25

| ID | Class | Evidence / residual |
|----|-------|---------------------|
| M1 | **D** | Enforce-decision agreed (GAPS #6: mandatory prose → validation rules; PLAN "Prose-rule audit" pre-registers "paired bpt/ept identifiers"). Semantics/scope/placement genuinely open → §3. |
| M2 | **D** | Same; PLAN explicitly leaves "unique `bpt.i` values within a segment" scope unsettled ("Scope across nested `hi`/`sub` content ... remain to be settled"). → §3. |
| M3 | **A** | `TMXInteger` (`parse_integer`) on `Bpt.i`, `Ept.i` (validators.py). Matches GAPS #1 decision exactly (negative native ints, bool, float all error; leading zeros OK). Residual: spec says only "Number" — unsigned-ness is our stricter recorded policy (GAPS #1), not spec text; fine, already owned. |
| M4 | **D** | Merge with M1 (same mechanism, same package). → §3. |
| M5 | **A** | `TMXInteger` on `Bpt.x`, `It.x`, `Ph.x`, `Hi.x`, `Ut.x`. Residual (not a gap): spec's `x` "Used in" omits `ut`, but the DTD declares `x` on `ut`; models follow the DTD (PLAN: DTD is the attribute inventory). |
| M6 | **D** | Not even in PLAN's known-rules list; x-matching across sibling `tuv`s. → §3. |
| M7 | **C** | PLAN strictness layer 3 names it verbatim: "Broader validators handle relationships such as `<ude base>` being required when a child `<map>` carries `code`." Residual: shares the not-yet-designed broader-validation API (GAPS #7). |
| M8 | **A** | `TMXHexInteger` (`parse_hex_integer`) on `Map.code`. `#x` prefix, ASCII hex digits, unsigned; matches GAPS #1. No range constraint needed — spec gives none for `code`. |
| M9 | **A** | `TMXUnicodeCodePoint` (`TMXHexInteger` + `validate_unicode_scalar`): 0–0x10FFFF, surrogates excluded, PUA included. Audit's truncated-sentence ambiguity (A1) resolved to the strong reading — moot. |
| M10 | **A** | `TMXAsciiText` (`validate_ascii`) on `Map.ent`. |
| M11 | **A** | `TMXAsciiText` on `Map.subst`. |
| M12 | **A** | `TMXIdentifier` (`validate_identifier`) on `TranslationUnit.tuid`. Residual (deliberate): uses Python's Unicode `str.isspace()` — stricter than the spec's undefined "white spaces"; acceptable and arguably desirable. |
| M13 | **A** | `TMXInteger` on `TranslationUnit.usagecount`, `TranslationUnitVariant.usagecount`. |
| M14 | **A** | `TMXDatetime` (`parse_datetime`) on `creationdate`/`changedate`/`lastusagedate` (Header, TU, Tuv). Residual (recorded, not a gap): input repertoire is `datetime.fromisoformat()`-bounded, not all of ISO 8601 — explicit PLAN/GAPS #3 value-policy boundary. |
| M15 | **A** | `TMXLanguageTag` / `TMXSourceLanguage` via `bcp47.validate_well_formed_language_tag`. Residual (recorded): spec cites RFC 3066, we implement RFC 5646 ABNF (PLAN names RFC 5646 as source); 3066-legal tags are a subset, so this is a deliberate documented superset. |
| M16 | **C** | For *validation* there is nothing to enforce (any casing legal); for *comparison* the policy is recorded in GAPS #8 (case-insensitive `lang`/`xml_lang` compare). The remaining comparison use (M18's srclang↔`xml:lang`) is deferred with M18. |
| M17 | **D** | Inheritance family. → §3. |
| M18 | **D** | Inheritance + equality strength. → §3. (`*all*` acceptance itself is A: `TMXSourceLanguage`.) |
| M19 | **D** | Inheritance family. → §3. |
| M20 | **D** | Inheritance family. → §3. |
| M21 | **A** | `TMXAssoc = Literal["p","f","b"]` on `Ph.assoc` — the strong (closed-enumeration) reading enforced. Verified: quote accurate (spec line 524), `assoc CDATA #IMPLIED` on `ph` only in DTD. |
| M22 | **C** | GAPS #9 owns the text/whitespace boundary. **Audit error on scope** — see §4. Interacts with GAPS #9's rejection-boundary question. |
| M23 | **D** | `ut` warning policy undecided. → §3. |
| M24 | **D** | Level-2 parity/stripping; contested strength; merge with M6 and ambiguity A6. → §3. |
| M25 | **C** | Physical-encoding layer. Writer: "Output is namespace-free, UTF-8 by default" (PLAN Writer) — UTF-8 is one of the three permitted encodings, so the writer side is satisfied by design. Reader encoding acceptance and any non-UTF-8 output path belong to I/O work (PLAN Reader/Writer sections). Residual: if output encoding is ever configurable to UTF-16, the BOM requirement (verified spec line 87) must be honored — lxml adds one for UTF-16, but that's an implementation-time check. |

## 2. Recommendations R1–R13

| ID | Class | Evidence |
|----|-------|----------|
| R1 | **C** | Warning-candidate review per GAPS #6 ("Recommendations may warrant warnings where actionable") / PLAN step 4. Note `Map` currently allows all three absent — correct for a "should". |
| R2 | **B** | Unenforceable even as a warning: the antecedent ("unpublished property types") is an out-of-band fact. Excluded by the GAPS #6 framework ("not every departure warrants one"; examples/conventions must not become requirements). |
| R3 | **C** | Non-exhaustive recommended list; value space must stay open (audit agrees). Whether unknown `datatype` values warrant a warning is a step-4 warning-choice. |
| R4 | **C** | Same treatment as R3 for `type` values. |
| R5 | **A** | `format_datetime` emits exactly `YYYYMMDDThhmmss[.ffffff]Z/±HHMM...` — the recommended pattern. Input breadth beyond the pattern is a recorded decision (GAPS #3), and the pattern is only recommended. |
| R6 | **B** | Authoring guidance, not a document constraint (PLAN: examples/conventions must not become requirements). |
| R7 | **A** | `TMXEncodingName` / `warn_unknown_encoding` (validators.py) — implemented soft warning for `o-encoding` and `ude base`, exactly matching "if possible". Residual: Python `codecs` lookup ≈ IANA registry, a pragmatic proxy, not the IANA list itself. |
| R8 | **B** | Out-of-band publication duties (audit itself says so); no document predicate exists. |
| R9 | **B** | Descriptive ("Logically, ... will"); DTD floor is `tuv+`, and GAPS #5 puts the nonempty-variants constraint on the model. Single-`tuv` TUs are common; no warning plausible. |
| R10 | **B** | Pure convention ("can", "may want"); PLAN forbids promoting conventions. |
| R11 | **C** | Satisfied by design — strict is the only read policy, DTD-validating every fragment (PLAN strictness layers 1–2, Reader section); implementation is reader work. We exceed the rule (validate everything, not just "suspicious" files). |
| R12 | **B** | Decided against: "TMX 1.4b is namespace-free, so strict input is too. Foreign namespaces are not matched by local name" (PLAN, Namespaces). Even the `lisa.org/tmx14` namespace would be rejected on read; the §1.1 *embedding* use case is out of scope for a standalone-TMX library. |
| R13 | **B** | Informative appendix; nothing normative (audit agrees). |

## 3. Ambiguities and contradictions

| ID | Class | Evidence |
|----|-------|----------|
| A1 (truncated `unicode` sentence) | **A** | Resolved to the stronger reading by `TMXUnicodeCodePoint`; quote verified (spec line ~1049: "Its value must be a" immediately before the value description). |
| A2 (`assoc` strength) | **A** | Strong reading enforced (`TMXAssoc`). Verified: no "recommended"/"not exhaustive" hedge, unlike datatype/type. |
| A3 (`srclang`↔`xml:lang` "will") | **D** | Same open question as M18. → §3. |
| A4 (`x` optional) | **A** | Settled correctly by the audit; DTD `x CDATA #IMPLIED` (verified); models use `x: TMXInteger | None`. |
| A5 (`version` presence) | **D** | Genuine reader-boundary decision; see §3. |
| A6 (Level 2 "Assuming:") | **D** | Merged into M24. → §3. |
| C1 (tmx15.dtd URL) | **B** | Spec typo (verified, spec line 1389); we bundle `tmx14.dtd`; nothing to enforce. |
| C2 (deprecated `lang`) | **A** (decision) / residual implementation | GAPS #8 records the full policy (validate both, warn on legacy-only and on case-insensitive difference, never synthesize, `xml_lang` required on Tuv). Residual: `TranslationUnitVariant.lang` is still plain `str` in models.py and the advisories are unimplemented — exactly the "predates decision 8" state the task flags. |
| C3 (`assoc` CDATA vs prose enum) | **A** | Duplicate of M21 — `TMXAssoc` enforces the prose enum. |

## 4. Detailed treatment of OPEN findings

### D-1: M1 + M4 — bpt/ept pairing within a segment (merge with M2 into one mechanism)

- **What to enforce:** within one segment's content tree, every `<bpt i="n">` has a *subsequent* (later in document order) `<ept i="n">`. M4 is the pairing-by-i mechanism; M1 is the ordering clause. Verified quotes (spec lines 231/361/469 — repeated under `seg`, `hi`, `sub` Contents; line 766 under `i`).
- **Where it could live:** the whole segment content tree — including nested `hi`/`sub` — is *local to one `TranslationUnitVariant` model*, so a model-level validator on `Tuv` is technically feasible. But per GAPS #7 there is no cascading revalidation: mutating a child `Bpt` would not re-run a `Tuv` validator. So realistically: a `Tuv`-level model validator **plus** the not-yet-designed user-invocable broader-validation re-check **plus** the writer boundary (PLAN layer 3, Writer section).
- **Strength reading:** audit's MANDATORY is right — "must", repeated three times. The audit is also right that pairing ≠ nesting (the spec's `i` section explicitly blesses overlapping ranges; PLAN already records that a stack-nesting check would be wrong).
- **Open questions:** (a) does the seg scope include `bpt`s nested in `hi`/`sub` (PLAN explicitly unsettled)? (b) is an *orphan `ept`* (no preceding `bpt` with that i) forbidden? The spec only constrains bpt→ept, not the converse. (c) may two `ept`s share an i? (d) exact error classification (error vs advisory) — GAPS #6 says mandatory = rule, so error, but confirm. (e) does "subsequent corresponding" add anything beyond "same i, later position" once M2 uniqueness holds?
- **Interactions:** needs the GAPS #7 broader-validation API for post-mutation revalidation. No GAPS #9/#10 interaction beyond sharing the XML boundary.

### D-2: M2 — unique `bpt.i` within a segment

- **What:** no two `bpt`s in one segment share `i`. Quote verified (line 798: "Must be unique for each `<bpt>` within a given `<seg>` element").
- **Where:** same placement analysis as D-1 (single-`tuv` scope; `Tuv`-level + explicit recheck + writer).
- **Strength:** MANDATORY, unambiguous. Note the audit left an ambiguity unflagged: the spec's scope phrase is "within a given `<seg>`", but `hi`/`sub` can nest inline elements — whether nested content counts toward the same seg's uniqueness namespace is unstated (this is the same question as D-1(a), and PLAN names it).
- **Interactions:** with D-1 (pairing is well-defined only if uniqueness holds — so these two rules should be validated together, one pass over the content tree).

### D-3: M6 + M24 + A6 — cross-`tuv` inline correspondence / Level-2 parity (merge into one rule family)

- **What:** M6: elements carrying `x` in one `tuv` have matching elements (same `x`) in sibling `tuv`s of the same `tu` (and an `ept` matches via its bpt's `x`). M24: same count/order/kind of inline elements across `tuv`s; no `ut`; `hi`/`sub` stripped.
- **Where:** spans sibling `Tuv` models, so not model-local. Crucially, it is **per-TU** — which fits the streaming architecture exactly (the TU is the unit of memory and of reader/writer validation; PLAN Reader `</tu>` step and Writer `write(unit)` step are the natural invocation points). Could also be user-invocable broader validation on a `TranslationUnit`.
- **Strength:** this is the weakest MANDATORY claim in the audit, and it should be contested. §4.3 sits under "Assuming:" and defines *tool capability* (export/import round-trip), not document validity. A TMX file with unequal inline tags across `tuv`s is still DTD-valid, useful Level-1-ish TMX. The `x` section's "is used to match" is definitional prose about the mechanism, like M18's "will". A validator-design reading could demote both to warnings or leave them to consumers.
- **Interactions:** needs the unsettled broader-validation API; M24's "no `ut`" clause interacts with D-5 (ut policy); the parity definition interacts with GAPS #9 (what counts as "the same kind" when `hi`/`sub` nest inline elements?).

### D-4: M17 + M18 + M19 + M20 — inheritance/defaulting family (merge into one design decision)

- **What:** four rules, one shared question: does the library **materialize** inherited/defaulted values in models (segtype←header; srclang←header; adminlang as the default language for note/prop lacking `xml:lang`; datatype→"unknown" when absent), or leave fields `None` and document resolution semantics? Separately, M18 has an enforcement clause: must a source `tuv`'s `xml:lang` equal the effective srclang (unless `*all*`)?
- **Where:** model-local is impossible without parent tracking (PLAN explicitly rejects parent tracking). Options: (i) reader materialization in `parse.py` — but that changes output fidelity (a materialized `segtype`/`datatype` would be written back, altering the document), which collides with GAPS #9's round-trip semantics; (ii) documented resolution semantics with no code; (iii) document-level broader validation where the API has header context. For M18's equality clause specifically: the writer *can* enforce it, because `TmxWriter.__enter__` holds the header — a document-level writer check is feasible in the planned architecture.
- **Strength:** the audit's MANDATORY label is misleading for M17/M19/M20 — these are interpretive semantics ("uses the one defined in...", "default value"), and *absence is legal*, so there is nothing a document validator can reject. M18's correspondence clause is the one genuinely normative-looking candidate, and the audit itself flags it as ambiguous (A3).
- **Interactions:** GAPS #9 (materialization vs round-trip fidelity); the broader-validation API question; writer design (header context).

### D-5: M23 — `<ut>` policy

- **What:** decide whether the deprecated `<ut>` is accepted silently, accepted with a `TmxWarning`, or rejected. The Level-2 ban ("not allowed in compliant documents", verified line 1237) does not translate directly: we don't implement conformance levels, and `ut` is legal 1.4b (PLAN models it deliberately).
- **Where:** `TmxWarning` advisory at model validation/assignment and writer validation — the pattern GAPS #8 established for legacy `lang`. Rejection would contradict PLAN's "deprecated constructs are modeled".
- **Strength:** the audit's MANDATORY is overstated for our purposes — deprecation carries no sanction at Level 1, and the Level-2 ban is conditional on a level we don't track. A warning (or nothing) is the defensible reading; full rejection is not.
- **Interactions:** the general warnings policy (PLAN step 4 "Recommendations and warning choices get their own review"); M24's "no ut in Level 2" if that family is ever enforced.

### D-6: A5 — `version` presence on `<tmx>`

- **What:** on read, is a `<tmx>` with no `version` attribute accepted (DTD `#FIXED "1.4"` would supply it — but our parser config sets `attribute_defaults=False`, so absence is *observable*) or rejected (spec §3.1.1 lists `version` under "Required attributes")?
- **Where:** the reader's document-order check — PLAN's Reader section already says the reader enforces "one `<tmx version="1.4">`", which reads as presence-required, but that text predates this ambiguity and isn't recorded as a decision about the absent case.
- **Strength:** requiring presence matches the spec's required-attributes list and is the stronger reading; accepting absence matches DTD-default semantics. Either is defensible; presence-required is cheaper and stricter-consistent. Should be recorded as an explicit decision either way.
- **Interactions:** GAPS #10 — whether an input internal subset could inject a `version` default is exactly the internal-subset policy question (with `attribute_defaults=False` it should not, but GAPS #10 demands hostile-fixture verification, not flag-wording trust).

## 5. Errors / corrections to the audit

1. **M22 scope error (verified).** The audit claims the "without leading or trailing white spaces" parenthetical applies to `seg`, `hi`, and `sub` "by the same Contents wording". False: only `<seg>` Contents carries it (spec line 227). `<hi>` Contents says "Text data," and `<sub>` says "Code data," with no parenthetical (verified lines ~358–362, ~467–471). M22 constrains `seg` only. Also unflagged: the spec *itself* says "All spacing and line-breaking characters are significant within a `<seg>` element" (line 215) — internal tension the audit missed; relevant to how strictly GAPS #9 treats this.
2. **Strength misclassifications in the inheritance family (M17, M19, M20, half of M18).** "Uses the one defined in the header", "specifies the default language for note/prop", and "Default value: unknown" are interpretive semantics — absence is legal, so no document can violate them. Calling them MANDATORY *constraints* is a category error; they are defaults the *application* applies. Only M18's `xml:lang`-equals-srclang clause is even a candidate document constraint, and the audit's own ambiguity A3 concedes it could be descriptive.
3. **Duplication the audit created:** M21 ≡ contradiction 3 (same finding, listed twice); A1 ≡ M9's strength basis; A2 ≡ M21; A3 ≡ M18; A6 ≡ M24. Also M1/M4 are the same mechanism (pairing by `i`) stated in the `Contents` and `i` sections, and M3/M5/M13 are one mechanism (the `Number` value description) split per attribute, as are M10/M11 (ASCII) and M8/M9 (hex).
4. **M6/M24 MANDATORY classification is contested** (not a misquote — quotes verified at lines 1099, 1230, 1261 — but a classification challenge): §4.3's "Assuming:" framing defines tool-capability preconditions, not per-document requirements. The audit acknowledges this in A6 and then still counts it MANDATORY.
5. **Unflagged DTD-superset attribute:** the audit's sanity pass covers the deprecated `lang`, but misses that `x` is declared on `<ut>` in the DTD while the spec's `x` "Used in" list (bpt, it, ph, hi — verified line 1121) omits `ut`. Same superset pattern; harmless for us (models follow the DTD inventory per PLAN).
6. **M2 scope ambiguity unflagged:** "within a given `<seg>`" versus `bpt`s nested in `hi`/`sub` — the audit treats per-seg scope as settled; it isn't (PLAN explicitly defers it).

Everything else spot-checked (M1, M3–M13, M14–M16, M18–M21, M25, R1–R12, C1–C3 quotes): quotes are accurate; no misquotes found.

## 6. Work-package grouping for the OPEN set

**WP-1: Segment-internal inline rules (M1, M2, M4).**
Open questions before coding: nested `hi`/`sub` scope; orphan-`ept` and duplicate-`ept.i` legality; pairing definition under overlaps; whether one `Tuv`-level model validator suffices at construction, with the broader API covering mutation (GAPS #7); error type (expect `TmxSpecError` at XML boundary, `ValidationError` at model boundary).

**WP-2: Cross-variant (TU-level) inline rules (M6, M24, A6) — and it subsumes the `ut` question if parity is enforced.**
Open questions: enforce-as-error vs warning vs consumer concern (strength is contested — settle this first); precise definition of "matching" via `x` and of "same kind/order"; treatment of absent `x`; whether `hi`/`sub` count in parity; invocation point (reader `</tu>`, writer `write(unit)`, user-invocable on a `TranslationUnit`).

**WP-3: Document-level inheritance/defaulting semantics (M17, M18, M19, M20, and M16's remaining comparison use).**
Open questions: materialize-in-models vs document-vs-enforce vs pure documentation (round-trip fidelity vs GAPS #9); whether M18's equality clause is a writer-enforced error (writer holds header context) or descriptive; API shape for rules needing header context.

**WP-4: Warnings policy (R1, R3, R4, M23; pattern already set by R7 and GAPS #8).**
Open questions: which recommendations earn a `TmxWarning`; `ut` deprecation warning; unknown `datatype`/`type` value warnings; single consolidated review per PLAN step 4.

**WP-5: Reader-boundary details (A5 version presence; M25 encoding policy).**
Tiny but must be recorded as decisions: require `version` present (likely yes); reader encoding-acceptance and output-encoding config surface; both fold into PLAN steps 5–6, with A5 additionally touching GAPS #10's internal-subset verification.

Sequencing note: WP-1 and WP-2 are blocked only on the broader-validation API design (GAPS #7); WP-3 additionally on reader/writer shape; WP-4 is independent; WP-5 rides along with existing planned steps.

---

**Summary:** 11 findings are already handled by the locked value layer (M3, M5, M8–M13, M21, R5, R7, plus ambiguity A1/A2/A4 and contradiction C3); 8 are decided against or out of scope (R2, R6, R8–R10, R12, R13, C1); 6 are deferred with a committed home (M7, M16, M22, M25, R1, R3, R4, R11 — the warning-choice and XML-boundary items); and 6 clusters are genuinely open (M1/M2/M4, M6/M24/A6, M17–M20, M23, A5) needing one of five work packages. The audit is largely accurate on quotes, but contains one scope error (M22), a systematic strength misclassification in the inheritance family, five duplicated findings, and one contested MANDATORY classification (M6/M24).
