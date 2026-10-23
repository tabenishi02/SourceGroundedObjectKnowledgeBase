# N05D-04R2 / R2-05 — Hybrid Search Migration

Updated: 2026-10-23

- Task: `R2-05 [P0] — Hybrid Search migration`
- Base before R2-05: `b3cb0150632a4a121bda5967a0ae172b95204688`
- Status: **Complete - Reference Workstation runtime verification PASS**
- R2-06: **Next / Not Started**
- Production cutover: **Not Performed**

## 1. Goal

Migrate the canonical Hybrid Object Search code path from the Phase-I broad
`object_overall` assumption to the R2 active family:

```text
object_overview
+ facet
+ statement
```

while preserving the public `search_objects` / `HybridObjectSearch.search`
capability and deferring production generation bootstrap/cutover/rollback to
R2-07.

## 2. Implemented files

```text
src/sgokb/domain/search.py
src/sgokb/retrieval/hybrid_search_r2.py
src/sgokb/retrieval/vector_maintenance.py
src/sgokb/retrieval/__init__.py
tests/test_hybrid_search_r2.py
```

The accepted Phase-I implementation remains in `hybrid_search.py` as the
historical/pre-cutover base. The canonical package export now routes
`HybridObjectSearch` through the R2 generation-aware layer.

## 3. Channel contract

The canonical active Object-level channel is now:

```text
semantic_object_overview
```

`ObjectSearchChannel.SEMANTIC_OBJECT` remains as the source-compatible Python
member for the active Object-level channel and resolves to the R2 value.

An explicit legacy enum value remains available for diagnostics:

```text
semantic_object_overall
```

Normal active R2 retrieval must not emit an `object_overall` representation
membership.

## 4. One request / one generation

`HybridObjectSearch.search()` now resolves the Knowledge Search generation once
at request start and stores that immutable request-local choice in a ContextVar.
All Knowledge-aware lexical and semantic operations in the request consume that
same generation.

Supported active contracts are currently:

```text
phase-i-search-v1 / v1
n05d04r2-hierarchical-v2 / v2
```

An unknown active contract fails explicitly.

### 4.1 Pre-cutover compatibility

Migration 018 intentionally does not create the singleton active pointer because
R2-07 must first validate/register the runtime Vector namespace.

Therefore, while `knowledge_search_active_generation` has no row, R2-05 keeps the
historical Phase-I serving path. It does not fabricate a `ready` v1 generation.

Once R2-07 creates the pointer, the compatibility path is no longer used and all
Knowledge channels are scoped to the resolved generation.

## 5. Knowledge lexical generation scoping

When an active generation exists, Knowledge lexical retrieval now routes through:

```text
active generation
  -> knowledge_search_generation_memberships
  -> knowledge_search_representation_memberships
  -> search_representations / search_representation_fts
```

The physical FTS table may still contain both legacy `object_overall` and new
`object_overview` rows. Only memberships linked to the resolved generation are
eligible before the candidate limit.

R2 v2 uses:

```text
object_overview
facet
statement
```

Phase-I v1 uses:

```text
object_overall
facet
statement
```

## 6. Semantic generation scoping

For an active R2 generation, semantic candidate generation uses:

```text
semantic_object_overview
semantic_facet
semantic_statement
```

The Vector hard filter includes the resolved `generation_id` for R2 points, in
addition to the existing kind/Class/Facet/current/history/temporal filters.

Returned vector hits are then verified against SQLite generation membership.
A returned R2 payload whose `generation_id` does not equal the request generation
is an integrity error; it is not silently accepted or replaced from another
generation.

The legacy v1 generation remains compatible with the pre-R2 Vector namespace,
which may not carry `generation_id` in historical payloads. R2-07 owns explicit
legacy namespace registration and the final namespace switch.

## 7. Generation-aware Vector point builder

The canonical `KnowledgeVectorIndexBuilder` / maintenance builder now accepts an
optional internal:

```text
generation_id
```

When supplied:

- only memberships linked to that generation become points;
- R2 point payloads contain `generation_id`;
- shared Facet/Statement representation embeddings remain reusable;
- `object_overall` cannot enter an R2 generation because Migration 018's
  generation-kind guard remains authoritative.

This is preparation for R2-07. R2-05 does not create or switch Qdrant namespaces.

## 8. Scope-safety behavior retained

The accepted Phase-I filtering and bounded aggregation behavior remains the base
implementation:

```text
RRF k = 60
Object-level semantic cap = 1
Facet semantic cap = 2
Statement semantic cap = 3
Knowledge lexical cap = 3
exact name > exact alias > non-exact
1 Object = 1 result
```

R2 representation selection preserves:

- Facet filter -> `facet + statement` only;
- no Object overview fallback for Facet-scoped retrieval;
- derivation filter -> Statement only;
- temporal scope / valid-at filter -> Statement only;
- current / explicitly requested historical Version isolation;
- explicit semantic failure / Hybrid degraded-channel behavior.

## 9. Focused regression added

`tests/test_hybrid_search_r2.py` covers:

1. active R2 semantic family uses `object_overview` and excludes `object_overall`;
2. generation-specific Vector points contain the R2 generation ID;
3. Knowledge lexical retrieval excludes memberships not linked to the active generation;
4. Facet-scoped retrieval has no overview or other-Facet fallback;
5. one request resolves the active generation exactly once;
6. a Vector backend that returns a mismatched generation payload produces an integrity error.

## 10. Explicitly not performed in R2-05

R2-05 does **not**:

- mark the migration-seeded v1 generation `ready`;
- register the existing production v1 Qdrant collection;
- create the candidate v2 Qdrant namespace;
- switch `knowledge_search_active_generation`;
- retire/delete v1 data;
- implement hierarchical Object Similarity;
- begin R2-06 or R2-07;
- change Harrier 0.6B, embedding dimension, truncation policy, CUDA/PyTorch, or FA2.

## 11. Reference Workstation verification - 2026-10-23

**R2-05 = Complete; R2-06 = Next / Not Started.**
Verification HEAD before local fixes: `c061631b2837b752b43272c10274a8be0fe8b191`;
R2-05 implementation base: `b3cb0150632a4a121bda5967a0ae172b95204688`.

R1 user-aborted assets were locally backed up and preserved byte-for-byte in the
original workspace. Checks ran in isolated `verification/r2-05-runtime` using the
existing workstation venv and this worktree's `src`. No package/model/GPU change.

### Executed tests

```text
python -m pytest -q tests/test_hybrid_search_r2.py
  24 passed
python -m pytest -q tests/test_hybrid_search.py tests/test_hybrid_search_r2.py
  33 passed
python -m pytest -q tests/test_search_generation_migration.py tests/test_search_representation.py tests/test_object_overview_r2.py
  14 passed
```

Related tests: **70 passed** across:

```text
tests/test_j01_application_semantics.py
tests/test_j01_retrieval_mcp_boundary.py
tests/test_j02_mcp_read_tools.py
tests/test_j06_mcp_client_acceptance.py
tests/test_n04p02_search_representation_sync.py
tests/test_n04p03_embedding_sync.py
tests/test_n04p04_vector_index_sync.py
tests/test_n04p05_derived_cli.py
tests/test_n02_integration.py
tests/test_vector_index.py
```

The non-overlapping Hybrid + migration/builder + related groups total **117
passed, 0 failed, 0 skipped**. R2-only 24 is a subset of Hybrid 33, not additional.
Qdrant dependency was available. Both the existing v1 Hybrid adapter regression
and the new active-R2 adapter regression passed using real qdrant-client local
`:memory:` mode. Its payload-index/full-scan parameter warnings are expected;
this does not certify a production ANN namespace or constitute a cutover test.
No full-suite run beyond these scoped groups was required or performed.

### Findings and fixes

- Initial combined Hybrid run: 1 failure / 13 passes. The failure was the stale
  `max(schema_migrations.version) == 17` assertion. Updated only that expected
  current schema version to **18**; no migration/runtime behavior change.
- R2 wrapper had I001, two unused imports and one overlong condition. Removed
  unused imports and formatted the wrapper. Production class ASTs match exactly
  before/after; no algorithm/contract change.
- Added 19 parameterized regression cases (R2 total 5 -> 24) for missing runtime
  evidence. An initial new RRF fixture incorrectly assumed one Object would rank
  first in every channel among equal vectors with independently ordered UUIDs.
  It now scopes the RRF calculation to one explicit Version and still asserts
  the exact `3 / 61` score; name/alias/non-exact ordering remains separately
  asserted across three Objects. No skip/xfail or relaxed contract was added.

### Mandatory contract results

| Contract | Runtime evidence |
|---|---|
| Active-generation lexical/semantic isolation | PASS in lexical, semantic and hybrid modes; unlinked Knowledge and injected foreign-generation points excluded |
| Active R2 family/channels | PASS: overview/facet/statement; no overall match; overview channel serialized through real MCP/Application chain |
| v1/pre-cutover channel identity | PASS: both emit semantic_object_overall; active R2 emits semantic_object_overview |
| One generation resolution/request | PASS for hybrid request |
| Generation payload mismatch | PASS: explicit RuntimeError in semantic mode; no foreign hit accepted |
| Facet no-fallback | PASS for populated requested Facet and missing requested Facet, including no overview/other-Facet rescue |
| Temporal/derivation scopes | PASS: Statement-only; valid-at/specific temporal scope and derivation selection verified |
| Current/historical isolation | PASS in all three modes; one Object result, matches remain in selected Version |
| RRF and caps | PASS: k=60, overview=1, Facet=2, Statement=3, Knowledge lexical=3; extra Statement/match counts cannot increase ranks beyond caps |
| Exact identity | PASS: exact name > exact alias > non-exact |
| Semantic degradation | PASS: missing backend raises in semantic mode, hybrid retains lexical results with explicit degraded channel |
| Application/maintenance/CLI/MCP | PASS: relevant regression groups plus active-R2 real MCPReadAdapter -> KnowledgeReadApplication -> Retrieval Core |

### Direct-import bypass review

Searched all tracked Python consumers for `hybrid_search` imports and
`HybridObjectSearch` references. The only import of the Phase-I Hybrid class is
the intentional internal base import in `hybrid_search_r2.py`. Application,
scripts and tests consume `sgokb.retrieval.HybridObjectSearch`; no active consumer
bypass remains. A regression imports only frozen RRF/cap constants from the base,
not its engine. Canonical Hybrid export resolves to the R2 wrapper; canonical
Vector builder aliases the maintenance builder, whose parent is the R2 builder.

### Static checks

```text
python -m ruff check src tests
  PASS
python -m ruff format --check src/sgokb/domain/search.py src/sgokb/retrieval/hybrid_search_r2.py src/sgokb/retrieval/vector_maintenance.py src/sgokb/retrieval/__init__.py tests/test_hybrid_search.py tests/test_hybrid_search_r2.py
  PASS (6 files)
git diff --check
  PASS
```

Repository-wide `ruff check .` reports only the known unrelated
`benchmark/tools/n05_resource_preflight.py:69 E501`. That pre-existing resource
script and its original-workspace uncommitted fix were deliberately untouched.

### Safety and next task

All active-generation pointers/readiness writes were limited to fresh disposable
pytest fixture databases. No production DB pointer/readiness, Qdrant collection,
v1 artifact, accepted model, truncation policy, CUDA/PyTorch or FA2 setting changed.
No quality/ANN/production cutover acceptance is claimed from these tests.

Next: **R2-06 [P0] - Hierarchical Object Similarity redesign (Not Started)**.
R2-06/R2-07 and the formal N-05 rerun were not started. N-05 remains BLOCKED /
Not Complete.
