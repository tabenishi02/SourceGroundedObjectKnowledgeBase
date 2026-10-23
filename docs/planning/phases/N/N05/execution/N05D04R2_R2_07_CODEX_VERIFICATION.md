# N05D-04R2 / R2-07 — Codex Runtime Verification and Cutover Handoff

Updated: 2026-10-23

## 1. Purpose

Complete local verification for **R2-07 [P0] — Derived Search rebuild / cutover / rollback**,
correct R2-07-scoped defects if found, and only then integrate the implementation branch to GitHub
`main` and perform the approved local generation cutover/rollback drill.

Do **not** start R2-08.

GitHub source state at handoff creation:

```text
main = 87663bf000811d7082395aa23325ca30ef0be4bb   # R2-06 Complete
implementation branch = r2-07-implementation
```

Normative R2-07 implementation record:

`docs/planning/phases/N/N05/N05D04R2_DERIVED_SEARCH_CUTOVER.md`

Normative upstream contracts:

- `docs/planning/phases/N/N05/N05D04R2_PERSISTENCE_VERSIONING_MIGRATION_DESIGN.md`
- `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`
- `docs/planning/phases/N/N05/N05D04R2_HYBRID_SEARCH_MIGRATION.md`
- `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md`
- `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`

## 2. Original workspace safety is mandatory

The original workspace contains three R1 user-aborted uncommitted assets. They must remain
byte-identical.

Before any pull / checkout / worktree operation:

```powershell
git status --short --branch
git diff --stat
git diff --cached --stat
git rev-parse HEAD
```

Record SHA-256 for all three preserved R1 assets before and after R2-07.

Forbidden in the original workspace:

```text
git reset --hard
git clean
forced checkout over local modifications
pull before status/diff inspection
```

Use a separate clean worktree for `r2-07-implementation`.

## 3. Review the implementation before execution

Review at least:

```text
src/sgokb/application_generation.py
src/sgokb/application_derived.py
src/sgokb/cli/generation.py
src/sgokb/cli/runtime.py
src/sgokb/retrieval/generation.py
src/sgokb/retrieval/vector_maintenance.py
src/sgokb/retrieval/hybrid_search_r2.py
src/sgokb/retrieval/similarity_r2.py
src/sgokb/migrations/018_search_generation_contract.sql
tests/test_generation_lifecycle_r2.py
tests/test_generation_lifecycle_qdrant_r2.py
```

Also search active production consumers for direct construction of a raw
`QdrantVectorIndexAdapter` that bypasses `route_generation_vector_index()`.

Normal Hybrid Search and Similarity serving must reach the generation router through the canonical
Application / CLI / MCP composition roots.

## 4. Static / import verification first

Run the project under its supported Python baseline as available locally. The project still declares
Python `>=3.10`; R2-07 code must not require a later-only stdlib API.

At minimum:

```powershell
python -m compileall src tests
ruff check `
  src/sgokb/application_generation.py `
  src/sgokb/application_derived.py `
  src/sgokb/cli/generation.py `
  src/sgokb/cli/runtime.py `
  src/sgokb/retrieval/generation.py `
  src/sgokb/retrieval/vector_maintenance.py `
  tests/test_generation_lifecycle_r2.py `
  tests/test_generation_lifecycle_qdrant_r2.py
ruff format --check `
  src/sgokb/application_generation.py `
  src/sgokb/application_derived.py `
  src/sgokb/cli/generation.py `
  src/sgokb/cli/runtime.py `
  src/sgokb/retrieval/generation.py `
  src/sgokb/retrieval/vector_maintenance.py `
  tests/test_generation_lifecycle_r2.py `
  tests/test_generation_lifecycle_qdrant_r2.py
```

Fix only R2-07-scoped findings.

Known unrelated baseline remains:

```text
n05_resource_preflight.py:69 E501
```

Do not mix that fix into R2-07.

## 5. Focused lifecycle tests

Run first:

```powershell
pytest -q `
  tests/test_generation_lifecycle_r2.py `
  tests/test_generation_lifecycle_qdrant_r2.py
```

The Qdrant test must use local `QdrantClient(location=":memory:")`; it must not touch production
collections.

Required assertions:

1. migration-seeded v1 generation is not trusted blindly;
2. verified v1 namespace can become `ready` and bootstrap active;
3. R2 candidate builds in a different namespace;
4. candidate reaches `ready` without changing active pointer;
5. R2 membership family contains `object_overview/facet/statement` and zero `object_overall`;
6. eligible Facet/Statement embeddings are reused by representation identity;
7. only missing representations are embedded;
8. generation membership digest is stable across the build;
9. source catalog cannot change during build;
10. point count equals membership count;
11. point membership IDs exactly equal SQLite generation membership IDs;
12. every R2 point carries exactly the candidate `generation_id`;
13. candidate build failure leaves v1 active and marks candidate failed;
14. not-ready / stale / invalid target cutover is rejected;
15. cutover pointer+audit transaction succeeds atomically;
16. Hybrid Search serves from R2 after cutover;
17. Overall Similarity serves hierarchical R2 after cutover;
18. Facet Similarity remains same-Facet raw cosine after cutover;
19. rollback returns serving to verified v1 raw-cosine behavior;
20. the same R2 candidate can be cut over again after rollback;
21. `bootstrap/cutover/rollback/recovery` audit kinds are recorded correctly;
22. interrupted non-active `building` generations become failed without pointer change.

If the implementation or tests do not prove an item above, add a focused R2-07 regression before
continuing.

## 6. Required R2 regression suite

After focused PASS, run at least:

```powershell
pytest -q `
  tests/test_search_generation_migration.py `
  tests/test_search_representation.py `
  tests/test_object_overview_r2.py `
  tests/test_hybrid_search.py `
  tests/test_hybrid_search_r2.py `
  tests/test_object_similarity.py `
  tests/test_object_similarity_r2.py `
  tests/test_generation_lifecycle_r2.py `
  tests/test_generation_lifecycle_qdrant_r2.py
```

Then run relevant maintenance / Application / CLI / MCP / Vector regressions, including:

```text
tests/test_n04p02_search_representation_sync.py
tests/test_n04p03_embedding_sync.py
tests/test_n04p04_vector_index_sync.py
tests/test_n04p05_derived_cli.py
tests/test_j01_similarity_application.py
tests/test_j01_retrieval_mcp_boundary.py
tests/test_j02_mcp_read_tools.py
tests/test_m01_cli.py
tests/test_vector_index.py
```

Run the repository-wide suite if local runtime cost is acceptable. Report unique PASS / FAIL / skip
counts.

## 7. Review normal incremental maintenance after cutover

Explicitly prove that after R2 is active:

- `DerivedSearchOperatorApplication.sync()` materializes `object_overview`, not `object_overall`;
- the newly materialized memberships are linked to the active R2 generation;
- Embedding sync uses the frozen Harrier Embedding Space;
- Vector sync writes to the active R2 namespace;
- no normal active consumer writes a new `object_overall` representation/vector;
- pre-bootstrap compatibility remains intact when no active pointer exists.

If generation digests intentionally represent the original cutover snapshot while active
incremental memberships evolve, document that semantic explicitly. If the R2-03 contract instead
requires the active generation digests/binding counts to be refreshed after successful incremental
sync, implement that refresh within R2-07 and cover it with a regression test. Do not leave the
meaning ambiguous.

## 8. One-operation / one-generation routing under cutover

R2-05/R2-06 already resolve the generation once per public retrieval operation. R2-07 adds namespace
routing.

Add or confirm a regression where the persisted active pointer changes between Vector calls during
one operation. The operation must never accept evidence from two generations.

Acceptable behavior is either:

- all calls are explicitly routed to the operation's originally resolved generation; or
- a concurrent switch causes a deterministic fail-closed integrity error before mixed evidence can
  be returned.

Silent cross-generation mixing is prohibited.

## 9. Git integration after local fixture tests PASS

Only after sections 4-8 are green:

1. commit R2-07-scoped corrections on the implementation branch;
2. update the R2-07 implementation record with test results;
3. fast-forward GitHub `main` to the verified R2-07 implementation;
4. confirm local `main == origin/main`;
5. keep the verification worktree clean.

Do not mark R2-07 Complete yet if the production/reference cutover drill below has not passed.

## 10. Production/reference state discovery

Do not guess the production database or Qdrant location.

Determine them from the current repository/config/task execution path. Record:

```text
DB absolute path
DB size
DB SHA-256 before R2-07
schema migration level
Qdrant URL / transport
legacy collection/namespace name
Embedding Space ID
Embedding model/revision/dimension
current Object / accepted Version counts
current Search membership counts by kind
current Vector point count
```

Confirm the frozen model is still Harrier OSS v1 0.6B with the approved revision and 1024 dimensions.

Do not change provider/model/runtime variables during this task.

## 11. Backup and canonical non-mutation proof

Before production/reference bootstrap:

- create a recoverable SQLite backup using the repository-supported backup mechanism where possible;
- hash the backup;
- record `PRAGMA integrity_check` and `PRAGMA foreign_key_check`;
- compute a deterministic digest/count snapshot over canonical semantic tables.

The SQLite file itself will change because R2-07 persists generation metadata. Therefore
"canonical non-mutation" means the canonical Object/Version/Facet/Statement/Source/Evidence/
Provenance/classification data remains byte/row-equivalent in its semantic fields, not that the whole
SQLite file hash remains unchanged.

At minimum compare canonical counts and deterministic row digests before/after for the tables that
R2-07 is not allowed to mutate.

## 12. Legacy v1 bootstrap preflight

Run the explicit operator entrypoint from the verified commit:

```powershell
python -m sgokb.cli.generation --db <production-db> status
python -m sgokb.cli.generation --db <production-db> bootstrap
```

Bootstrap must fail closed unless:

- the migration-seeded v1 generation membership set is valid;
- legacy point count matches membership count;
- exact legacy Vector point IDs match exact membership IDs;
- source catalog / membership digests can be persisted consistently.

If the real production v1 namespace cannot pass this proof, **do not cut over**. Diagnose and fix
R2-07-scoped derived-state issues first; do not reconstruct canonical Knowledge or silently rebuild
v1 in place.

After bootstrap verify:

```text
active_generation = search-generation:phase-i-v1
state = ready
switch audit kind = bootstrap
legacy namespace unchanged
normal Hybrid/Similarity behavior unchanged
```

## 13. Build the production/reference R2 candidate

Run:

```powershell
python -m sgokb.cli.generation --db <production-db> build
```

Capture the returned:

```text
generation_id
source_catalog_digest
membership_digest
membership_count
reused_embedding_count
created_embedding_count
backend_key
namespace_key
point_count
```

Then independently verify:

- generation state = ready;
- active pointer is **still v1**;
- R2 `object_overall` membership count = 0;
- every accepted Version has exactly one `object_overview`;
- eligible content Facet set matches canonical data;
- eligible Statement set matches canonical data;
- membership count == point count;
- exact point-ID set == membership-ID set;
- every R2 Vector payload has the exact candidate generation ID;
- no v1 namespace was dropped/rebuilt/renamed;
- only new R2 namespace storage was created;
- canonical table digest is unchanged.

## 14. Pre-cutover smoke against candidate namespace

Before moving the active pointer, perform direct candidate-namespace checks if necessary using the
lifecycle/test helpers. Prove:

- semantic Hybrid queries return expected Objects;
- Overall Similarity returns `hierarchical_similarity`;
- Facet Similarity returns same-Facet `cosine_similarity`;
- `object_overall` is absent;
- wrong generation payload/membership is rejected.

Do not use the formal R2-08 quality benchmark here.

## 15. Atomic R2 cutover

When all previous gates are green:

```powershell
python -m sgokb.cli.generation --db <production-db> cutover <r2-generation-id>
```

Do not use `--no-smoke` for acceptance.

Verify immediately:

```text
active_generation = <r2-generation-id>
activation_revision incremented once
switch audit kind = cutover
Hybrid semantic read = R2 generation
Overall Similarity = hierarchical_similarity
Facet Similarity = same-Facet cosine
object_overall normal serving = absent
```

If the built-in post-switch smoke fails, the implementation must record recovery and restore v1.
Treat that as R2-07 failure until corrected and rerun.

## 16. Rollback drill

With no canonical Knowledge change between cutover and rollback:

```powershell
python -m sgokb.cli.generation --db <production-db> rollback
```

Verify:

- active pointer returns to `search-generation:phase-i-v1`;
- audit kind = rollback;
- legacy namespace was never rebuilt by the rollback;
- Hybrid uses v1 membership family;
- Overall Similarity returns the historical raw `object_overall` cosine contract;
- Facet Similarity remains same-Facet raw cosine;
- R2 candidate remains ready and intact;
- canonical table digest remains unchanged.

## 17. Forward re-cutover

Prove reversibility by switching the same ready candidate forward again:

```powershell
python -m sgokb.cli.generation --db <production-db> cutover <r2-generation-id>
```

The final intended R2-07 serving state is active R2, not v1, unless a newly discovered safety issue
requires leaving production on v1. If a safety issue forces v1 to remain active, report R2-07 as
Blocked / Not Complete.

## 18. Failure drills

Use fixture / cloned DB + in-memory Qdrant for destructive negative tests; do not corrupt production
state intentionally.

Prove:

- candidate build failure leaves active generation unchanged;
- not-ready generation cutover is rejected;
- stale catalog rollback/cutover is rejected;
- membership digest mismatch is rejected;
- point-count mismatch is rejected;
- point-ID mismatch is rejected;
- R2 payload generation mismatch is rejected;
- interrupted building generation recovery does not change active pointer;
- smoke failure records recovery and restores previous active generation.

## 19. Final integrity checks

After the final forward R2 cutover:

- `PRAGMA integrity_check = ok`;
- `PRAGMA foreign_key_check` has zero violations;
- canonical semantic table digest/count snapshot equals pre-R2-07 snapshot;
- v1 and R2 namespaces both still exist;
- active pointer resolves to R2;
- R2 Vector binding is ready;
- legacy v1 remains ready and rollback-capable **for the same catalog snapshot**;
- original R1 assets have identical SHA-256 values;
- original workspace has no new unintended modifications.

## 20. Documentation / tracker after PASS

Only after all applicable local gates and the cutover/rollback/re-cutover drill pass:

1. update `docs/planning/phases/N/N05/N05D04R2_DERIVED_SEARCH_CUTOVER.md` to
   `Status: Complete` and record exact evidence;
2. update `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`:

```text
R2-07 = Complete
R2-08 = Next / Not Started
```

3. if the tracker names the next task differently, follow the current GitHub-main tracker rather
   than this handoff text;
4. commit/push all R2-07-scoped verification fixes/docs to `main`;
5. do not begin R2-08.

## 21. Final report

Report:

```text
branch/worktree used
final main HEAD
main == origin/main
working-tree status
R1 asset SHA-256 preservation
Python version(s) used
changed files after verification fixes
focused pytest result
R2 regression result
maintenance/Application/CLI/MCP result
repository-wide pytest result if run
Ruff/format/diff result
legacy generation ID/state
legacy source_catalog_digest
legacy membership_digest
legacy membership count
legacy namespace / point count
R2 generation ID/state
R2 source_catalog_digest
R2 membership_digest
R2 membership count
R2 namespace / point count
R2 object_overall count
Embedding reused count
Embedding newly-created count
Vector membership-ID audit result
R2 generation-payload audit result
bootstrap result
cutover result
rollback result
forward re-cutover result
Hybrid smoke result
Overall Similarity smoke result
Facet Similarity smoke result
negative/failure drill result
canonical semantic digest before/after
SQLite integrity_check / foreign_key_check
production final active generation
commit SHA / push result
R2-07 final status
next task
```
