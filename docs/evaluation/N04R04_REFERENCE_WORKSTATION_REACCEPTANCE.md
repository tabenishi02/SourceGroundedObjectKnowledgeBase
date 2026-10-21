# N-04R-04 Reference Workstation Re-Acceptance Result

更新日: 2026-10-22

- N-04R-04: **Complete / PASS**
- N-04: **Complete** under the corrected Knowledge Access responsibility boundary.
- Next task: **N-04R-05 — Grounded Generation Asset Disposition** (not started).
- N-05 / N-06 remain Ready; Phase N as a whole is not Complete.

## Authority and execution identity

- Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Harness freeze: `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
- Execution handoff: `docs/planning/phases/N/N04/execution/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE_HANDOFF.md`
- Case spec and harness: `benchmark/n04-knowledge-access-cases-v1.json`, `benchmark/n04-knowledge-access-formal-harness-v1.json`.
- Initial synchronized main: `f502f4e5e315abdb8152169c76d9aae5e3261a79`; initial working tree clean.
- Repair / formal input HEAD: `d4ac29c541473c4cdb86877944bca92b23692cb9`; branch `main`, clean before formal execution.
- Run ID (Asia/Tokyo): `20261022T052331+0900`
- Raw evidence root: `.local/n04r04/20261022T052331+0900/` (ignored; not committed).
- Environment: Python 3.10.6; Windows platform build `10.0.26300`, recorded in `environment.json`.
- Runtime: accepted P-06 local semantic configuration; Qdrant 1.19.2, qdrant-client 1.19.1, Harrier model `microsoft/harrier-oss-v1-0.6b` revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`; torch 2.6.0+cu124, sentence-transformers 6.1.0, transformers 5.20.1.
- Public transport: real `python -m sgokb --db .local/n03/sgokb-n03.sqlite mcp serve --semantic-runtime`; MCP SDK 2.3.0, negotiated protocol 2026-07-28, SGOKB MCP server 0.2.0.

## Preflight repair and rerun

Initial preflight run `20261022T051538+0900` failed before formal case execution: Windows CRLF checkout bytes differed from frozen LF Git blobs, and the preflight dependency blacklist literals triggered its own dependency-free source test. That run and its logs remain intact (initial focused 2 failed / 18 passed; full suite 2 failed / 491 passed).

The repair adds LF checkout attributes only for the two bound files, and statically audits the evaluator AST for standard-library-only imports and absence of dynamic loading/execution. Existing test assertions are unchanged; 12 portability/dependency regression tests were added. No production Knowledge Access code, formal case, Gate, budget, expected Object, or evaluator payload was changed.

Frozen blob identities remain exactly:

- Case spec: `ab3374508467575955f0f9da911f551178a93b6e`
- Formal evaluator: `060037e5316dd819472018f54c1d5600786e3e74`

The repaired run restarted every mandatory preflight command from the beginning:

| Command | Result |
|---|---|
| `python benchmark/tools/n04r03_harness_preflight.py` | PASS |
| `python -m pytest -q tests/test_n04r03_knowledge_access_harness.py tests/test_n04r04_evidence_evaluator.py tests/test_j04_context_builder.py tests/test_j06_mcp_client_acceptance.py` | 20 passed |
| `python -m pytest -q` | 505 passed, 0 failed, 0 skipped; 2 existing local-Qdrant warnings |
| `python -m ruff check .` | PASS |
| `git diff --check` | PASS |

## Formal cases

All requests and responses were obtained from the real MCP server/client. `tools/list` contains the exact 8 public read tools, all with `readOnlyHint=true`. No direct SQLite query was used to create any Consumer Context. The independent safety auditor uses a read-only SQLite connection solely to capture canonical snapshots.

| Case | Objects / public path | Used / limit characters | Omitted / truncated | Required checks | Result |
|---|---|---:|---|---:|---|
| 1 roleplay | Saber → `build_context` | 640 / 12000 | 0 / false | 17 / 17 | PASS |
| 2 comparison | Fate/stay night → `find_similar_objects` rank 1 → `build_context` | 1513 / 24000 | 0 / false | 26 / 26 | PASS |
| 3 creative | Tsundere + Hero's Journey → `build_context` | 1299 / 24000 | 0 / false | 17 / 17 | PASS |

Case 2 actually returned BLEACH as rank 1, Object `57db855c-574a-4b38-b474-421c165894f1`, Version `6e75aa45-9c13-42ef-87b4-923beac43bef`. Those returned identities were used unchanged in the Context request/response; the candidate was not hardcoded. Similarity ranking quality was not assessed (N-06 responsibility).

The current accepted Versions, purpose/include options, omission/budget contracts and provenance policies pass. Case 2 retains 4 Evidence references; Case 1/3 omit Evidence references. Additional public `get_object` reads corroborate current Versions. Completion review also checked all 10 returned Statements against the recorded canonical Version and exact text, and the 4 Evidence refs through Statement grounding → Evidence → Source/Snapshot/Normalization Run.

The real-data fixture contains no persisted Attributes or Relations; their include-option contract and handling are covered by the focused regression tests. Coverage sufficiency and Consumer prose quality are not acceptance Gates. No local LLM generation, classifier/verifier inference, Grounded Generation v3/v4, Frozen 47 or Consumer-output quality evaluation was run.

## Canonical invariance, integrity and regression

Before/after snapshots use the same read-only transaction and deterministic sorted table/row serialization, with no run timestamp injected. They capture all canonical Object/Version/accepted Knowledge/Facet/Statement/Attribute/Relation/Source/Snapshot/Evidence/grounding/provenance tables. The exact comparison covers 52 retained tables, including unchanged auxiliary evidence read indices; search-derived and SQLite-internal tables are excluded by the saved procedure. Empty Attributes/Relations are captured explicitly. This is semantic row-state comparison, not a database-file hash comparison.

- Canonical JSON before == after: **PASS**.
- Deterministic snapshot serialization SHA-256: `f3a4e2e3bc6f8a65adbeddcce961060a113845535d181a2124d038f9b6f47966`.
- Captured core counts: 6 Objects, 6 accepted Versions, 12 Statements, 54 Object-Version Facets, 8 Sources, 8 Snapshots, 515 Evidence records, 12 Evidence links; stable identities preserved.
- Actual `system integrity`: **PASS**; SQLite `integrity_check=ok`, no foreign-key violations.

After all three formal cases:

| Command | Result |
|---|---|
| Focused pytest (the mandatory 4 files plus `tests/test_n04r04_preflight_portability.py`) | 32 passed, 0 failed |
| `python -m pytest -q` | 505 passed, 0 failed, 0 skipped; 2 existing local-Qdrant warnings, 157.39 s |
| `python -m ruff check .` | PASS |
| `git diff --check` | PASS |

The warnings describe payload-index and search-parameter limitations of local Qdrant in existing tests, not the production Qdrant server or a new regression. `regression.json` records all four return codes as 0. The tracked HEAD and worktree stayed unchanged throughout the formal cases and post-run regression.

## Formal decision and evidence identity

Authoritative result: `.local/n04r04/20261022T052331+0900/overall-evaluation.json`, produced by the unchanged frozen evaluator with return code 0. Formal overall result: **PASS**; 3/3 cases and all canonical/integrity/regression global Gates PASS. Completion-review replay of the evaluator matches the saved result exactly.

All 20 required evidence files are present. Selected evidence SHA-256:

| Evidence file | SHA-256 |
|---|---|
| `overall-evaluation.json` | `81093373aaec50c8921b8e61aa63d16e7692d0066ce4d2cd3575ea689770bcad` |
| `mcp-tools.json` | `3b35a28ffe18dfac1b1b8aebf61712a1fc5d6b90689a742e0f46d09e42398aca` |
| `canonical-before.json` | `343b413d1f7811e18f2bf5ac62d28232c53c5f42fbaa6be35c75be190211168d` |
| `canonical-after.json` | `343b413d1f7811e18f2bf5ac62d28232c53c5f42fbaa6be35c75be190211168d` |
| `integrity.json` | `79e1b0fe31c40d3c414b453f8fda5b86743a44ae0ce7d5d091c3f374b67ac463` |
| `regression.json` | `c36f6819dc70c9aa37f091fca1990e1919e596b3871958e32062b2b67b0b63dc` |

Raw Knowledge, source/provenance payloads, SQLite files and logs remain local and ignored. Only this aggregate evidence summary is committed. Historical G-12/G-22/G-25 evidence is preserved; the responsibility Decision supersedes their role as current N-04 prerequisites without changing those historical outcomes.

**N-04R-04 = Complete; N-04 = Complete.** Next: **N-04R-05 — Grounded Generation Asset Disposition**. No asset removal, R-05 disposition decision, N-05 performance work or N-06 quality evaluation was performed in this task.
