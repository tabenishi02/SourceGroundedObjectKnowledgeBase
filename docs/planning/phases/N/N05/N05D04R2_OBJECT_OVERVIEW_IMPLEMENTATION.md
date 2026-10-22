# N05D-04R2 — R2-04 compact `object_overview` implementation

Updated: 2026-10-23

- Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Task: `R2-04 [P0] — Implement compact object_overview`
- Status: **Complete - Reference Workstation verification PASS**
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

## 9. Reference Workstation verification - 2026-10-23

**R2-04 = Complete.** Verification basis: `0e8204a5479b26ba9651783affa237d364591a21`.
The original workspace had three pre-existing uncommitted R1 assets. They were
backed up locally and left intact. Verification used the isolated branch
`verification/r2-04-runtime` and the existing workstation venv with `PYTHONPATH`
pointing to this worktree's `src`; package resolution was explicitly checked.
No environment/package/CUDA/model update or production cutover was performed.

### Executed checks

```text
python -m pytest -q tests/test_search_representation.py tests/test_object_overview_r2.py tests/test_search_generation_migration.py
  14 passed (13 existing cases plus the populated pre-018 preservation case)
python -m ruff check src tests benchmark/tools/n05d04r2_object_overview_diagnostic.py
  PASS
python -m ruff format --check tests/test_search_generation_migration.py
  PASS
git diff --check
  PASS
```

Repository-wide `ruff check .` was also attempted. It reports one pre-existing,
unrelated E501 in `benchmark/tools/n05_resource_preflight.py:69`. That line exists
unchanged at the verification basis; the old workspace's R1 line-wrap fix was
not appropriated into this R2-04 commit. All R2-04 source/test/static checks pass.
The full pytest suite was not required or run for this bounded runtime check.

### Populated migration 003..018 preservation

Added `populated_pre018_database` and
`test_pre018_populated_migration_preserves_ids_content_vectors_and_fts` in
`tests/test_search_generation_migration.py`. It actually applies 003..017,
creates accepted canonical Object/Version data, legacy overall and Evidence
representations/memberships, an Embedding Space and two persisted vector rows,
closes the database, then opens the normal Repository to apply 018.

Exact pre/post rows match for representations (including IDs/content/hash),
Knowledge/Evidence memberships (including IDs), Embedding bytes/metadata,
Embedding Space, Objects and Versions. Legacy generation membership IDs match
the original Knowledge membership IDs. FTS rows equal all representations and
MATCH queries plus FTS `integrity-check` pass. SQLite `integrity_check = ok` and
`foreign_key_check = []` before and after. The final schema chain is exactly
003..018. Existing focused tests additionally reject both overview-in-v1 and
overall-in-R2 generation mixtures and verify fresh migration behavior.

The real Large copy independently migrated from 003..017 to 018, preserving
all **1204 v1 representations and 1204 Knowledge memberships** byte-for-byte.
That historical interrupted DB has **zero persisted Embedding rows**; vector
preservation is therefore established by the populated synthetic migration
fixture above, not falsely inferred from the empty Large embedding table.

### Actual Large structure and exact tokenizer result

Source fixture:
`.local/n05/20261022T130413+0900/large/cold-01/sgokb.sqlite`
in the original repository clone; opened read-only and SQLite-backed-up for
migration/materialization. Direct counts confirm **40 Sources / 2000 Evidence
candidates**; saved `package-build.json` confirms **350 package Evidence**.

- Object: `object-n05-large`; Version `b9dc52be-32ea-4c31-b05e-d530635f12ed`.
- Source DB SHA-256 before/after:
  `ca321321f57cacc8731c206dea022035a9c3e11c76cf7fa454ef314434d8d5b1` (unchanged,
  also matching the preserved N05D-02 fingerprint).
- Statements **1200** = **5 facet-less Summary + 1195 detailed Facet Statements**.
- Overview includes all five Summary bodies and all three content-Facet key/name
  identities; none of the 1195 detailed bodies appears in the overview.
- All detailed bodies remain in their respective Facet and Statement builders.
  Explicit R2 materialization on the disposable copy retains **3 Facet / 1200
  Statement memberships**, adds one overview and preserves the old overall.
- Copy FK/integrity and FTS content/index checks pass after materialization.
- Overview: **264 UTF-8 bytes / 264 characters / 103 exact tokens**.
- Overview SHA-256:
  `04a76bfc3b9cde60516e4f527a714f78cc56518b51dd23257a9f776401b11221`.

Executed the committed diagnostic tool with the source DB above and the original
clone's local model cache:

```text
python benchmark/tools/n05d04r2_object_overview_diagnostic.py --database <source-large-db> --cache-folder <existing-local-model-cache> --output <local-evidence>/object-overview-diagnostic.json
```

Frozen tokenizer: `microsoft/harrier-oss-v1-0.6b`, revision
`f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`; local-files-only/offline,
`add_special_tokens=True`, `padding=False`, **`truncation=False`**.
**103 <= 4096: PASS**, with no model replacement, embedding inference, arbitrary
chunking, CPU inference fallback or attention/CUDA changes.

Local-only evidence in the verification worktree: `.local/r2-04/`, containing
the diagnostic JSON, disposable copied DB, structure/migration audit and overview.
Raw databases/text/logs are not committed. Reproducible migration assertions are
committed in the focused test. No R2-05/R2-06/R2-07 or production cutover ran.

## 10. Current state

```text
R2-01 = Complete
R2-02 = Complete
R2-03 = Complete
R2-04 = Complete
R2-05 = Next / Not Started
R2-06 = Not Started
N05D-04R2 = Active
N05D-04 = BLOCKED / Not Complete
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

Next: **R2-05 [P0] - Hybrid Search migration** (not started by this verification).
