# N05D-04R2 / R2-05 — Hybrid Search Migration

Updated: 2026-10-23

- Task: `R2-05 [P0] — Hybrid Search migration`
- Base before R2-05: `b3cb0150632a4a121bda5967a0ae172b95204688`
- Status: **Implementation Complete / Runtime Verification Pending**
- R2-06: **Not Started**
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

## 11. Runtime verification gate

Do not mark R2-05 Complete until the reference workstation verifies at minimum:

```text
pytest tests/test_hybrid_search_r2.py
pytest tests/test_hybrid_search.py tests/test_hybrid_search_r2.py
relevant generation/migration tests
Ruff / format / diff checks for R2-05 files
```

The existing Phase-I Hybrid test file contains a historical migration-version
assertion written before Migration 018. If it still expects schema version 17,
update that expectation to the current migration version as a test-maintenance
change; do not change runtime behavior to satisfy the stale assertion.

Required evidence:

- focused Hybrid tests PASS;
- exact-name/alias priority regression PASS;
- contribution-cap regression PASS;
- current/historical and Class/Facet/temporal regression PASS;
- active R2 results contain no `object_overall` match;
- active generation isolation PASS for lexical and semantic paths;
- Qdrant adapter regression PASS where the optional dependency is available;
- R2-05 Ruff/static checks PASS.

If all pass, update:

```text
R2-05 = Complete
R2-06 = Next / Not Started
```

Next task after verified completion:

`R2-06 [P0] — Object Similarity migration`
