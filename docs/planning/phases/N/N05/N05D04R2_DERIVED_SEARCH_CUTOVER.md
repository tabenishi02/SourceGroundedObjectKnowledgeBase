# N05D-04R2 / R2-07 — Derived Search rebuild / cutover / rollback

Updated: 2026-10-23

Status: **Complete / Local Verification and Reference Cutover PASS**

The local verification and reference cutover/rollback/re-cutover drill in
`execution/N05D04R2_R2_07_CODEX_VERIFICATION.md` passed. R2-08 is Next / Not Started.

R2-08 is not started.

## 1. Goal

R2-07 makes the persistence contract frozen in R2-03 executable:

```text
active Phase-I v1 generation
        |
        | remains serving while candidate is built
        v
R2 candidate generation (building)
  -> representation membership snapshot
  -> reusable / missing Embeddings
  -> isolated generation-specific Vector namespace
  -> identity / digest / count / payload verification
  -> ready
        |
        | atomic pointer + audit transaction
        v
active R2 generation
        |
        +-- rollback -> previous ready/catalog-compatible v1 generation
```

Canonical Object / Version / Facet / Statement / Evidence / Provenance state is not rolled back or
rewritten by these operations.

## 2. Runtime components

### 2.1 Generation lifecycle application

`src/sgokb/application_generation.py`

`KnowledgeSearchGenerationApplication` owns:

- legacy v1 registration / bootstrap;
- deterministic source-catalog digest;
- deterministic generation-membership digest;
- R2 candidate creation;
- R2 representation materialization for every accepted Version;
- Embedding reuse and missing-Embedding generation;
- isolated Vector namespace build;
- generation shape / namespace / digest verification;
- ready transition;
- atomic cutover;
- rollback;
- automatic recovery after post-switch smoke failure;
- interrupted-build failure marking;
- operator status.

A candidate reaching `ready` **does not switch serving traffic automatically**.

### 2.2 Generation-aware representation maintenance

`src/sgokb/retrieval/generation.py`

`GenerationAwareSearchRepresentationBuilder` preserves pre-bootstrap Phase-I behavior. After an
active pointer exists:

- active v1 materializes / links `object_overall + facet + statement`;
- active R2 materializes / links `object_overview + facet + statement`.

This keeps normal post-cutover incremental writes on the active representation contract without
requiring public callers to pass a generation or representation kind.

### 2.3 Generation-specific Vector namespaces

`GenerationQdrantVectorIndexAdapter` binds one adapter instance to an exact persisted namespace.
A new R2 namespace adds the `generation_id` payload index and never aliases the old v1 collection.

`GenerationRoutingVectorIndexAdapter` routes normal Hybrid Search, Similarity and maintenance by:

1. explicit `generation_id` Vector filter when one is present;
2. otherwise the persisted active Knowledge Search generation;
3. pre-bootstrap compatibility only when no active pointer exists.

For Phase-I v1 the generation route is resolved at the namespace layer while the generation filter
is stripped before Qdrant evaluation because historical v1 points do not contain a
`generation_id` payload.

### 2.4 Vector identity audit

New R2 Qdrant namespaces are scanned after rebuild. The audit verifies:

- every Vector point carries the exact Search membership ID;
- the point-ID set equals the generation membership-ID set;
- the stored Embedding Space ID is correct;
- R2 points carry the exact candidate `generation_id`;
- duplicate / missing / foreign points fail closed.

The same membership-identity proof is required for the existing v1 namespace before it can be
registered `ready` and bootstrapped as active.

### 2.5 Normal maintenance routing

`KnowledgeVectorMaintenanceBuilder` now resolves the active generation when a generation was not
supplied explicitly. Candidate builds supply their generation explicitly, so they cannot write to
the active namespace accidentally.

`DerivedSearchOperatorApplication` injects:

- `GenerationAwareSearchRepresentationBuilder`;
- the generation-routing Vector adapter;
- `KnowledgeSearchGenerationApplication`.

Existing `status` / `sync` behavior remains and generation status is additive.

R2-07 local verification clarifies the incremental contract against R2-03 sections
13 and 26: active generation digests describe the latest **successfully audited**
active membership/catalog snapshot, not an immutable historical cutover snapshot.
A successful semantic sync (including all Objects in a batch) verifies canonical
membership shape, exact namespace point identity/payload, total point count and
unchanged catalog/membership snapshots. Only then are active `source_catalog_digest`,
`membership_digest` and the current space/backend binding digest/count published
atomically. Partial/failed sync does not publish new digests. Other generations
retain their previous snapshots and become stale rollback targets after canonical
changes; there is no implicit dual-write to v1. Embedding sync and status count only
the active family, avoiding new legacy `object_overall` work after cutover.

One retrieval operation pins its resolved generation in a context-local Vector
routing scope, including active-v1 and pre-bootstrap operations. A concurrent
pointer switch cannot redirect subsequent Vector calls to another namespace.
The Application constructor also routes injected namespace-capable backends;
CLI `system index rebuild` routes to the active namespace instead of overwriting
legacy storage. Lifecycle switches acquire `BEGIN IMMEDIATE` before final target
verification and commit pointer/audit together. Smoke treats degraded/empty semantic
Search as failure. Qdrant identity audit additionally checks each backend UUID
against the deterministic Embedding Space + membership-ID mapping.


### 2.6 Read runtime

`src/sgokb/cli/runtime.py` wraps the production Qdrant adapter with generation routing before it is
injected into `KnowledgeReadApplication`.

Normal Search / Similarity / MCP callers still do not provide generation IDs or representation
kinds.

## 3. Legacy v1 bootstrap

Migration 018 deliberately seeded:

```text
id               = search-generation:phase-i-v1
contract_key     = phase-i-search-v1
contract_version = 1
state            = building
```

R2-07 does **not** blindly mark it ready.

`bootstrap_legacy()` requires:

1. the seeded generation contract identity is valid;
2. membership shape matches accepted canonical Knowledge;
3. one `object_overall` membership exists for every accepted Version;
4. the Statement and content-Facet membership sets match canonical eligibility;
5. no `object_overview` membership leaks into v1;
6. the existing Vector namespace point count matches;
7. the Vector point membership-ID set matches the SQLite generation membership set;
8. source-catalog and membership digests are persisted;
9. the Vector binding is registered ready;
10. only then is the singleton active pointer bootstrapped transactionally with an audit row.

A mismatch fails closed and does not fabricate v1 readiness.

## 4. R2 candidate build

`build_r2_candidate()` performs:

```text
snapshot source_catalog_digest
create generation(state=building)
for every accepted Version:
    materialize object_overview v2 + Facet v1 + Statement v1
link only object_overview/facet/statement to candidate
validate canonical membership shape
persist membership_digest
verify source catalog unchanged
reuse existing compatible Embeddings
embed only missing representations
create isolated namespace
rebuild Vector points from candidate memberships only
verify point count
verify exact membership identity + R2 generation payload
verify membership_digest unchanged
verify source catalog unchanged
register Vector binding ready
mark generation ready
```

`object_overall` is forbidden in the R2 generation by both migration triggers and application
validation.

If any build step fails, the candidate is marked `failed`; any building Vector binding is marked
`failed`; the active generation is unchanged.

## 5. Embedding reuse

Reuse continues to use the R2-03 identity rule:

```text
representation_id + embedding_space_id
```

Generation ID is not added to the Embedding cache key.

Therefore unchanged Facet / Statement Search Representations can reuse their Harrier vectors.
`object_overview` is a v2 representation and is embedded only when its representation/space pair is
not already cached.

The frozen R2 baseline remains:

- `microsoft/harrier-oss-v1-0.6b`;
- revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`;
- bfloat16;
- 1024 dimensions;
- existing normalization / preprocessing contract.

No 270M substitution, truncation, FlashAttention-2, PyTorch/CUDA change or CPU fallback change is
introduced by R2-07.

## 6. Ready / cutover gate

A generation cannot be switched active unless all of the following are true at switch time:

- generation state is `ready`;
- expected contract matches the requested operation;
- current source-catalog digest equals the generation digest;
- canonical membership shape still matches;
- current membership digest equals the generation digest;
- a ready Vector binding exists for the frozen Embedding Space/backend;
- Vector binding digest equals the generation digest;
- persisted point count equals generation membership count;
- live namespace point count equals generation membership count;
- live point membership identities match exactly;
- R2 payload generation identities match exactly.

The pointer update and `knowledge_search_generation_switches` audit insertion occur inside the same
SQLite transaction.

## 7. Cutover smoke and automatic recovery

After an R2 cutover pointer switch, the lifecycle performs smoke reads through the normal
R2-capable retrieval implementations:

- semantic Hybrid Object Search;
- Overall Object Similarity;
- Facet Similarity when the chosen source Object has a content Facet.

If this post-switch smoke fails, the previous generation is re-verified and restored through a
`recovery` switch. A half-switched pointer is not silently accepted.

## 8. Rollback

The default rollback target is:

```text
search-generation:phase-i-v1
```

Rollback is permitted only if the target is still:

- `ready`;
- Phase-I v1;
- source-catalog compatible with the current canonical state;
- membership-digest valid;
- Vector binding / point count / point identity valid.

Rollback changes only Derived Search routing. Canonical Knowledge and representation content are
not reverted.

After rollback the same smoke gate is executed. Smoke failure triggers recovery back to the former
active generation.

The local R2-07 acceptance drill must also prove that the same ready R2 generation can be switched
forward again after a successful rollback.

## 9. Interrupted build recovery

`recover_interrupted_builds()` converts non-active `building` generations to `failed` and also marks
building Vector bindings failed. It never changes the active pointer.

Old failed namespaces are retained for later explicit cleanup. R2-07 does not automatically delete
an active or rollback-capable generation.

## 10. Operator entrypoint

R2-07 adds an explicit non-read operator module:

```powershell
python -m sgokb.cli.generation --db <DB> status
python -m sgokb.cli.generation --db <DB> bootstrap
python -m sgokb.cli.generation --db <DB> build
python -m sgokb.cli.generation --db <DB> cutover <generation-id>
python -m sgokb.cli.generation --db <DB> rollback
python -m sgokb.cli.generation --db <DB> recover
```

`--no-smoke` exists for controlled diagnostics only and must not be used for R2-07 acceptance.

## 11. Automated regression surface

Added:

- `tests/test_generation_lifecycle_r2.py`
- `tests/test_generation_lifecycle_qdrant_r2.py`

The focused suite covers:

- verified v1 bootstrap;
- ready candidate without automatic cutover;
- candidate build failure preserving active v1;
- R2 cutover;
- rollback;
- forward re-cutover;
- stale rollback target rejection;
- interrupted build recovery;
- not-ready cutover rejection;
- isolated generation namespace with Qdrant `:memory:`;
- R2 `object_overall` exclusion.

Existing R2-04/05/06, migration, maintenance, Application, CLI and MCP tests remain required in the
Codex acceptance run.

## 12. Production safety

GitHub-side implementation cannot prove the user's current local SQLite/Qdrant state. Therefore the
production bootstrap/build/cutover/rollback drill is intentionally delegated to the local Codex
verification step.

Before any production operation, Codex must:

1. inspect the original workspace and hash the three preserved R1 assets;
2. use a clean verification worktree;
3. identify the actual production DB and Qdrant endpoint from current configuration rather than
   guessing paths;
4. take a recoverable DB backup and record its hash;
5. record canonical-table digests separately from derived generation tables;
6. verify the current legacy Qdrant namespace before bootstrap;
7. run fixture + in-memory Qdrant gates first;
8. proceed to production cutover only when every preflight gate is green.

If production preflight cannot prove safety, R2-07 must remain Not Complete rather than performing a
speculative cutover.

## 13. Completion gate

R2-07 may become Complete only after local verification proves:

- legacy v1 bootstrap PASS;
- R2 candidate build PASS;
- Embedding reuse/new overview behavior PASS;
- membership/digest/count/payload audits PASS;
- isolated Qdrant namespace PASS;
- candidate ready without auto-cutover PASS;
- atomic R2 cutover PASS;
- Hybrid / Overall Similarity / Facet Similarity smoke PASS;
- rollback PASS;
- forward re-cutover PASS;
- stale / invalid target fail-closed behavior PASS;
- interrupted-build recovery PASS;
- canonical semantic tables unchanged by the drill;
- R1 local assets unchanged;
- focused/regression tests and static checks PASS.

Only then update the task tracker to:

```text
R2-07 = Complete
R2-08 = Next / Not Started
```

Do not start R2-08 as part of R2-07.


## 14. Local engineering verification (2026-10-23)

Input implementation HEAD: `ade8e8d03dce04884765778ed97cfacdbfbbdb31`.
Isolated worktree verification used Python 3.10.6. R1 user-aborted assets remain
byte-identical (three SHA-256 checks). Local evidence run:
`20261023T135304+0900`, under `.local/r2-07/` (raw files are not Git assets).

- Focused lifecycle/Qdrant: 29 passed.
- R2 regression: 104 passed (includes the 29 focused tests).
- Maintenance/Application/CLI/MCP/Vector compatibility: 83 passed.
- Full pytest: 635 passed, 0 failed/errors/skips, 2 local-Qdrant warnings.
- Compile PASS; Ruff `src tests` PASS; changed Python format PASS (20 files);
  diff check PASS. Global Ruff retains only the documented unrelated
  `benchmark/tools/n05_resource_preflight.py:69 E501`, unchanged.
- Regression proves concurrent cutover preserves one operation/one namespace,
  active incremental digest/count publication after complete audit, batch sync,
  cache reuse, invalid target identity/count/payload rejection and smoke recovery.
- CLI index rebuild bypass and active-family status counts corrected.
- Full suite first exposed six stale failures and two setup errors, reproduced
  unchanged on pre-R2-07 main. Update only exact schema-018 expectations and the
  explicit legacy/R2 representation enum expectations; do not relax assertions.
  The rerun is entirely green. Original failure evidence is retained.

This engineering checkpoint preceded the reference drill in Section 15; completion is based on both stages.


## 15. Reference workstation acceptance — PASS (2026-10-23)

Execution HEAD: `0b835e6ebecc6db3cd8545d27510fb17f364ef02`.
Run: `20261023T135304+0900`, under `.local/r2-07/`; backup/raw evidence remains
local and is not committed. The original R1 assets remain SHA-256 identical.

Reference identity was discovered from existing R-04 execution/runtime config:
`.local/n03/sgokb-n03.sqlite`, six Objects / six accepted Versions. Default
`.local/sgokb.sqlite` was absent and remains absent. Native Qdrant 1.19.2,
qdrant-client 1.19.1, PID 54084; external config/storage remain
`C:/Qdrant/SGOKB/qdrant.yaml` / `C:/Qdrant/SGOKB/storage`, HTTP 6333 / gRPC 6334.
Old workspace storage and all historical N05/N05D evidence are retained.

Frozen model: `microsoft/harrier-oss-v1-0.6b`, revision
`f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`, CUDA/bfloat16, dimension 1024,
maximum sequence length 32768, overflow reject, normalization enabled. No
truncation, CPU fallback, model/backend substitution or runtime update occurred.
The accepted reference provider batch size remains 64; no formal N-05 workload ran.
Embedding Space:
`23027d8fcb47c6ffb9e95681742e4c0aa8d14b301b642a974159f05883204bbf`.

SQLite backup API ran before Repository applied migration 018:
- source DB SHA-256: `0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d`;
- backup SHA-256: `40f55bf301ac3b27ef230f0bb964497b652f8b76f839f915e44e623d2755995b`;
- schema 003..017 upgraded to 018; before/after integrity `ok`, zero foreign-key violations.

| Identity | Verified v1 | R2 candidate / final |
|---|---|---|
| Generation | `search-generation:phase-i-v1` | `search-generation:r2:5c80093a-fd89-49a0-9431-d2d6f3f454ce` |
| State | ready, rollback-capable for this catalog | ready, final active |
| Namespace | `sgokb_n03_eval_23027d8fcb47c6ffb9e95681` | `sgokb_n03_eval_generation_3688b3402f3b519d3b6fabed` |
| Memberships / points | 24 / 24 | 24 / 24 |
| Family | overall 6, Facet 6, Statement 12 | overview 6, Facet 6, Statement 12; overall 0 |

Shared source catalog digest:
`73c3cf216f732d68e2bd092bcfae6766b032027adfbb715d0dc912275922a804`.

v1 membership/binding digest:
`4e4423e25eac3f5f4fe1be058180bbf380c1dda81d5f07bfac8eb1e7aa658f49`.

R2 membership/binding digest:
`3e43deb9368eef4af13ca2f1888728777c5267e1159f1648dacd0d59b302592b`.


Build reused 18 compatible Facet/Statement embeddings and created six missing
overview embeddings. Exact membership-ID/point UUID sets, Embedding Space identity,
point count and every R2 generation payload passed live namespace audit. All six
accepted Versions have exactly one overview; eligible Facets/Statements match
canonical data. Ready candidate left the active pointer on verified v1.

Operator CLI executed bootstrap -> R2 cutover -> v1 rollback -> same-candidate
forward re-cutover. Activation revisions 1/2/3/4 and audit kinds
bootstrap/cutover/rollback/cutover are verified. Built-in smoke remained enabled.
Independent candidate, cutover, rollback and re-cutover checks passed semantic
Hybrid (no degraded channels), Overall Similarity (hierarchical for R2, raw cosine
for v1), exact-Facet cosine and MCP adapter -> real Application reads. Query tracing
confirms each phase used only the expected namespace. Both namespaces remain;
v1 point/vector/payload digest is unchanged. Rollback did not rebuild/drop/rename
legacy storage. Final R2 vectors also equal the original ready-candidate snapshot.

The first candidate smoke helper incorrectly supplied Hybrid's private generation
DTO to Similarity and stopped before cutover with `AttributeError: is_r2`. Only
that untracked helper was corrected to use the actual DTO for each implementation.
Original helper/error/log evidence is retained. Continuation used the same ready
candidate, backup and canonical baseline and wrote separate continuation logs.
No production source/model/Gate changed after engineering verification.

Canonical proof covers 45 non-derived tables, including registry, Object/Version/
classification/Facet/Statement/Attribute/Relation/Source/Snapshot/Evidence/provenance
and package/import records. Deterministic row digests and counts are compared;
Search/FTS/embedding/generation metadata and Object derived status are excluded.
Before == after:

`2bc1ce515e5a15eef84ba9ab74fbb26fd4f0c0449dd4f0fb9316eea99618de21`.


Final independent audit rechecked live namespaces, UUID/payload identity, both
vector snapshots, revision/audit order, canonical equality, integrity/FK and all
three R1 asset hashes. RTX 4090 returned to 301 MiB after worker exit.

**R2-07 Complete; R2-08 Next / Not Started.** N-05 remains BLOCKED / Not Complete
pending quality/resource/performance acceptance. R2-08, formal N-05 rerun, artifact
retirement and security configuration changes were not performed.
