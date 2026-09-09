# Handoff: next session

State as of 2026-09-08. PLAN.md and GAPS.md are current; this file is working
notes, not policy. Tests: 1,088 passing (225 XML), Ruff/ty clean, XML suite
also green under `-W error`.

## Where we are

- All 14 node models project both ways (`xml/parse.py`, `xml/build.py`),
  using direct dispatch. The superseded plan-interpreter code (`xml/plans.py`)
  is deleted; the PLAN records why the approach lost.
- GAPS #9 (text boundary) is settled for projection; decision 12 (per-flow
  pairing/i uniqueness) reaffirmed with the documented-interpretation framing.
- Test suites live in `tests/xml/`: content, dtd, parse, build,
  projection_contract, plus a small `conftest.py` (fresh `minimal_node`,
  `minimal_header`, `valid_tmx_document` fixtures). Expectations stay
  module-local; warning suppression is narrow `TmxWarning` marks only.

## Next up (plan step 6: reader/writer)

1. Settle GAPS #10 (internal subsets/entities) with hostile fixtures before
   trusting parser flags. Entity rejection in `content.py` is a projection
   rule, not a parser-safety proof.
2. Design the remaining decision-11 surface: `Ude.base`/`Map.code`, whole-tree
   revalidation for the writer, two-step content cycles (GAPS 7a; pinned
   models tests do NOT cover cycles). Then the reader (`header_peek`,
   `read_header()`, per-TU iteration, bounded memory) and writer
   (validate-before-commit, explicit empty-tag spelling).
3. I/O suite, then the end-to-end streaming benchmark (plan step 6 end).

## Known loose ends

- lxml 6.1.3 artifact: validating an attached fragment whose descendants use
  `xml:lang` reports a synthetic `xmlns:xml` attribute; `dtd.py` deep-copies
  non-document-root fragments for validation only. Worth reducing to a
  reproducer and upstreaming; explicit `xmlns:xml` is legal XML, so don't
  assert its illegality anywhere.
- Wheel inclusion of the DTD and resource loading outside the checkout:
  unverified (the cold-load test runs against the checkout).
- Writer must document always-expanded empty tags; `None` vs `""` in models
  is preserved but collapses through serialized XML (agreed, intentional).
- Writer's per-TU conformance gate must call `validation.py` checks plus any
  new whole-tree checks; DTD success alone is insufficient.
- README is stale (v1); facade/`__all__` and docs update are plan step 7.
- Hunk review sessions: agent notes for the projection/test reviews are in
  the old session; nothing outstanding there.
