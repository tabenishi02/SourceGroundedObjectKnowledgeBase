# N05D-04R2 — R2-04 compact `object_overview` implementation

Updated: 2026-10-23

- Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Task: `R2-04 [P0] — Implement compact object_overview`
- Status: **Implementation Complete / Runtime Verification Pending**
- R2-03 persistence freeze: `docs/planning/phases/N/N05/N05D04R2_PERSISTENCE_VERSIONING_MIGRATION_DESIGN.md`
- R2-02 semantic freeze: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

## 1. Summary

R2-04 implementation is present on `main`.

Implemented:

```text
SearchRepresentationKind.OBJECT_OVERVIEW
legacy OBJECT_OVERALL retained explicitly
ambiguous OBJECT alias removed
per-kind builder versions
compact deterministic build_object_overview()
explicit materialize_version_r2()
migration 018 coexistence/generation schema
object_overview persistence constraints + uniqueness
FTS recreation/indexing after migration table swap
generation-kind guards
focused builder/migration tests
exact Harrier token diagnostic tool
```

Not performed by R2-04:

```text
Hybrid Search cutover
Object Similarity cutover
active-generation routing in retrieval
Qdrant generation namespace implementation/cutover
production data rebuild
R2-08 quality acceptance
R2-09 formal N-05 rerun
```

The serving v1 path remains intentionally intact until R2-05/R2-06 migrate retrieval.

## 2. Representation implementation

`src/sgokb/domain/knowledge.py` now defines explicit Object-level kinds:

```text
OBJECT_OVERVIEW = object_overview   # R2 active semantic contract
OBJECT_OVERALL  = object_overall    # Phase-I legacy-readable contract
```

The historical generic `OBJECT = object_overall` alias was removed rather than remapped.

`src/sgokb/retrieval/search_representation.py` now uses per-kind builder versions:

```text
builder_key      = sgokb-canonical-search
object_overall   = 1
object_overview  = 2
facet            = 1
statement        = 1
evidence         = 1
```

Facet/Statement/Evidence are therefore not falsely version-bumped by the R2 deployment generation.

## 3. `object_overview` content

`build_object_overview(version_id)` is deterministic, local, and non-generative.

It contains only:

```text
Object canonical name
normalized/deterministically ordered aliases
Primary Class from represented accepted Version
facet-less Summary Statements
content Facet key/name inventory
known structured Attribute key/name/value text
canonical Relation key/name/endpoints plus temporal context when present
```

It does not contain:

```text
content-Facet Statement bodies
Statement/Facet/Attribute/Relation/Evidence IDs
Evidence content
gap/proposal/conflict/workflow/debug metadata
LLM-generated summary
arbitrary token chunks
truncated canonical text
```

The legacy `build_object_overall()` remains available with builder version `1` for the still-serving Phase-I path and historical compatibility.

## 4. Transitional materialization boundary

R2-04 deliberately does **not** change the existing `materialize_version()` serving behavior yet.

Current transition contract:

```text
materialize_version()
  -> legacy object_overall + facet + statement

materialize_version_r2()
  -> candidate object_overview + facet + statement
```

Reason:

- R2-05 has not yet migrated Hybrid/Knowledge lexical retrieval;
- R2-06 has not yet migrated overall Object Similarity;
- changing the default materialization path in R2-04 would create a half-cutover where downstream active retrieval still expects `object_overall`.

`materialize_version_r2()` is the explicit candidate-building path until the later retrieval/cutover tasks make the v2 generation active.

## 5. Migration 018 implementation

Added:

`src/sgokb/migrations/018_search_generation_contract.sql`

The migration is schema/coexistence only.

It:

1. widens Search Representation kind constraints to include `object_overview`;
2. widens Knowledge membership constraints to include `object_overview`;
3. preserves old `object_overall` as a legal legacy value;
4. preserves v1 representation/membership/embedding rows during the table rebuild;
5. recreates indexes, validation triggers, compatibility view, and FTS after the table swap;
6. enforces one `object_overview` membership per Object + Version;
7. creates the R2 generation tables frozen by R2-03;
8. seeds deterministic legacy generation `search-generation:phase-i-v1` in `building` state;
9. links Knowledge memberships present at migration time to that legacy generation;
10. adds generation-kind guards that reject overview in the Phase-I generation and overall in an R2 generation.

It does **not**:

- relabel `object_overall` rows;
- create R2 overview content automatically;
- mark the legacy generation `ready` without runtime/integrity evidence;
- rebuild or delete Qdrant state;
- change the active search generation;
- delete v1 artifacts.

Legacy runtime/Qdrant registration and generation assembly/backfill remain R2-07 responsibilities.

## 6. Focused test coverage added

Updated:

`tests/test_search_representation.py`

Added:

`tests/test_object_overview_r2.py`
`tests/test_search_generation_migration.py`

Coverage includes:

- explicit enum family and retired generic alias;
- per-kind builder versions;
- deterministic byte-identical overview construction;
- compact exact output for a simple Object;
- content-Facet Statement body excluded from overview;
- Summary retained;
- content Facet identity inventory retained;
- non-content Facet state excluded from inventory;
- known Attribute key/name/value retained;
- Relation key/name/endpoints retained;
- internal IDs absent from overview text;
- explicit R2 materialization idempotency;
- one overview membership per Object + Version;
- no overall membership produced by the explicit R2 candidate path;
- Facet/Statement detail memberships retained/reused;
- current/historical Version membership semantics retained;
- candidate Version rejection;
- migration 018 presence/table creation;
- invalid representation kind rejection;
- overview FTS indexing;
- v1/v2 generation-kind mixing guards;
- SQLite foreign-key check on a fresh migrated database.

## 7. N-05 Large structural diagnostic

The frozen N-05 Large fixture contains:

```text
knowledge_statement_count = 1200
```

The current fixture builder assigns:

```text
first 5 Statements -> knowledge.summary
remaining 1195     -> first 3 canonical Facets
```

Under the R2 builder, `object_overview` therefore includes the 5 facet-less Summary Statements and the three content-Facet identities, but **does not include the remaining 1195 content-Facet Statement bodies**.

This establishes the intended structural correction: the mandatory Object-level representation no longer grows linearly with the Large fixture's detailed Facet Statement count.

## 8. Exact Harrier token diagnostic

Added:

`benchmark/tools/n05d04r2_object_overview_diagnostic.py`

The tool:

- opens the supplied benchmark SQLite database read-only;
- copies it to a temporary diagnostic database before Repository migration/building;
- requires the frozen Large fixture's 1200 Statements by default;
- builds `object_overview` without persisting it to the source database;
- loads the frozen tokenizer for:

```text
microsoft/harrier-oss-v1-0.6b
revision f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
```

- tokenizes with:

```text
add_special_tokens = true
truncation         = false
```

- records exact token count and the `<= 4096` engineering-target result;
- returns nonzero if the engineering target fails.

Example execution against a completed Large sample database:

```text
python benchmark/tools/n05d04r2_object_overview_diagnostic.py \
  --database <large-sample>/sgokb.sqlite \
  --output <evidence>/object-overview-diagnostic.json
```

No model downgrade, CPU fallback, or truncation is part of this diagnostic.

## 9. Verification state

The implementation and focused test cases have been committed, but this chat environment could not execute the repository's Python test/runtime suite or the local Harrier tokenizer against the user's benchmark database.

Therefore the following evidence is still required before R2-04 can be marked **Complete**:

```text
focused pytest PASS
migration 003..018 execution/preservation PASS on the repository runtime
ruff/static checks required by the repository PASS
N-05 Large exact object_overview token count recorded
object_overview token count <= 4096
no truncation confirmed
```

The exact token criterion is intentionally not replaced by an estimate.

## 10. Current state

```text
R2-01 = Complete
R2-02 = Complete
R2-03 = Complete
R2-04 = Implementation Complete / Runtime Verification Pending
R2-05 = Not Started
R2-06 = Not Started
N05D-04R2 = Active
N05D-04 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

R2-05 must not start until the R2-04 exit evidence above passes or an explicit decision accepts a different gate.
