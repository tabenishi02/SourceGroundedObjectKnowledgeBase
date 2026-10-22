# N05D-04R2 — Next Chat Handoff

Updated: 2026-10-23

- Project: Source Grounded Object Knowledge Base
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent task: `N-05 [P0] — Performance`
- Current remediation: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Current next task: **R2-01 — Impact survey / redesign freeze**
- Formal N-05: **BLOCKED / Not Complete**
- Formal performance target: **Not Judgeable**
- Authoritative branch: **GitHub `main`**

## 1. Read these documents first

Use GitHub `main` as the source of truth and read in this order:

1. `docs/planning/phases/N/N05/execution/N05D04R2_NEXT_CHAT_HANDOFF.md`
2. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
3. `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`
4. `docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md`
5. `docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md`
6. `docs/evaluation/N05_PERFORMANCE.md`
7. `docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md`
8. `docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md`
9. `docs/planning/phases/N/PHASE_N_PREPARATION.md`
10. historical Phase I designs relevant to R2-01:
    - `docs/requirements/SEARCH_REQUIREMENTS.md`
    - `docs/design/SEARCH_REPRESENTATION_SCHEMA.md`
    - `docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md`
    - `docs/design/OBJECT_SIMILARITY_SEARCH.md`
    - `docs/planning/phases/I/PHASE_I_PREPARATION.md`

Do not infer current state from old chat text if it conflicts with these main-branch documents.

## 2. Current state

```text
N05D-01 = Complete
N05D-02 = Complete / old-contract memory viability
N05D-03 = Complete historical checkpoint
N05D-04 = BLOCKED / Not Complete
N05D-04R1 = Historical partial / user-aborted
N05D-04R2 = Active
R2-01 = Next / Not Started
N-05 = BLOCKED / Not Complete
performance target = Not Judgeable
```

Do not start R2-02 or implementation work before R2-01 exit conditions are satisfied.

## 3. Why R2 exists

The old active Object-level search representation duplicated all detailed content-Facet Statement bodies even though the same accepted Knowledge was also materialized as Facet and Statement representations.

Large N-05 produced:

```text
object_overall tokens: 18,847
Harrier 0.6B full embedding: ~628–643 s
Torch peak allocated: ~51.1 GiB
Windows Shared GPU memory: ~34.2 GiB
```

The issue is therefore not only model size/runtime tuning. The active Derived Search representation architecture itself duplicated detailed Knowledge into one giant full-attention input.

The user explicitly selected the structural remediation:

```text
compact object_overview
+ Facet representations
+ Statement representations
+ bounded Object aggregation
+ hierarchical Object Similarity
```

This is semantic partitioning along canonical Object / Facet / Statement boundaries, not arbitrary token chunking.

## 4. Target architecture

```text
Object
├─ object_overview   # compact Object-level context
├─ facet             # existing detailed Facet representation
└─ statement         # existing detailed Statement representation
       ↓
 bounded multi-representation candidate generation
       ↓
 Object aggregation / hierarchical similarity
       ↓
 1 Object = 1 result
```

`object_overview` should contain deterministic canonical Object-level context such as:

```text
canonical name
aliases
Primary Class
Facet-less Summary Statements
content Facet identities (name/key only)
known Attributes
Relations
```

It must not re-copy all content-Facet Statement bodies.

## 5. Migration principle

Do not silently redefine persisted `object_overall` v1 semantics.

Default redesign direction:

```text
new active kind = object_overview
old object_overall = historical/transition artifact
```

Use a side-by-side Derived Search migration so old and new artifacts remain distinguishable for:

- quality comparison;
- performance comparison;
- cutover validation;
- rollback.

Canonical Knowledge must not be rewritten to implement the Derived Search redesign.

## 6. Model policy

For the first R2 acceptance, keep:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dtype: bfloat16
dimension: 1024
```

Do not combine representation redesign with:

- Harrier 270M adoption;
- PyTorch upgrade;
- FlashAttention-2 installation;
- CPU fallback;
- truncation;
- arbitrary token chunking.

Harrier 270M is a later contingency only if the hierarchical redesign still fails explicit performance/resource/operational requirements.

## 7. Historical diagnostic evidence to retain

### N05D-01

Qdrant storage/path problem resolved by controlled cutover to:

```text
C:\Qdrant\SGOKB
```

### N05D-02

Old-contract 18,847-token input completed fresh-process 3/3 but with severe memory/time cost.

### First N05D-04 rerun

Run `20261023T025413+0900`:

```text
Standard cold 3/3 PASS
Standard warm 18 PASS / 2 FAIL
```

The two failures were disk exhaustion (`No space left on device` / WAL buffer cannot fit). Large had not completed when stopped. Treat as environment BLOCKED / user-aborted, not a performance FAIL.

Future formal start gate:

```text
free disk >= 32 GiB
```

### N05D-04R1

Run `20261023T035147+0900` was user-aborted partial diagnostic evidence:

```text
auto SDPA smoke -> math backend observed
forced Flash -> unavailable in tested Windows PyTorch build
forced Efficient -> tested Q=16 / KV=8 GQA shape rejected
full auto trial -> ABORTED_by_user
```

Do not resume R1 automatically.

## 8. Important local-worktree warning

The user/Codex reported that R1 raw evidence and **uncommitted local diagnostic changes were retained** when the R1 test was stopped.

Therefore, before any local `git pull`, checkout, reset, or R2 implementation:

1. inspect `git status` and local diff;
2. identify which uncommitted files belong to R1 diagnostic tooling/tests/docs;
3. preserve/stash/commit/dispose them explicitly according to evidence-retention needs;
4. do not use `git reset --hard` or otherwise discard them implicitly;
5. only after local state is reconciled, sync to current `origin/main`.

GitHub `main` remains the design/documentation source of truth; local uncommitted R1 work is historical diagnostic material, not the R2 design source of truth.

## 9. R2 task sequence

```text
R2-01 Impact survey / redesign freeze
  ↓
R2-02 Requirements + representation contract revision
  ↓
R2-03 Persistence/versioning/migration design
  ↓
R2-04 compact object_overview implementation
  ├─→ R2-05 Hybrid Search migration
  └─→ R2-06 Hierarchical Object Similarity redesign
          ↓
R2-07 Derived Search rebuild / cutover / rollback
          ↓
R2-08 Search-quality acceptance
          ↓
R2-09 Performance/resource acceptance + formal N-05 rerun
          ↓
R2-10 Closure / Phase N state update
```

Formal N-05 timing is prohibited before R2-08 quality acceptance passes.

## 10. R2-01 — exact next task

### Goal

Inventory every active dependency on the old `object_overall` semantics before changing canonical design documents or production code.

### Search/inventory at minimum

```text
object_overall
SearchRepresentationKind
build_object_overall
semantic_object_overall
find_similar_objects
knowledge_search_representation_memberships
search_representation_embeddings
KnowledgeVectorIndexBuilder
search-quality gold
N-03 / N-04 / N-05 / N-06 fixtures
CLI/MCP/public outputs exposing representation_kind
migrations / DB constraints
rebuild / derived-state lifecycle
```

### Classification

Every dependency must be assigned one of:

```text
KEEP unchanged
RENAME / compatibility shim
CHANGE semantics
MIGRATE data
REBUILD derived artifact
UPDATE gold/test
HISTORICAL only
```

### Required deliverable

`docs/planning/phases/N/N05/N05D04R2_IMPACT_SURVEY.md`

### Exit conditions

R2-01 is Complete only when:

- no unresolved active `object_overall` consumer remains outside the inventory;
- canonical Knowledge tables are confirmed outside semantic-content migration scope;
- CLI/MCP/domain API compatibility obligations are explicitly documented;
- migration/rebuild/test/gold/doc impact is fully enumerated;
- unresolved design questions are listed for R2-02/R2-03 instead of being silently decided in implementation.

## 11. Formal performance remains frozen

Do not alter N-05 workload or gates as part of R2-01:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
Standard cold 3 + warm 20
Large cold    3 + warm 20
```

Future formal execution occurs only at R2-09 with a new run ID.

## 12. Expected first response in the next chat

After reading the handoff and linked documents, report briefly:

1. current N-05/R2 state;
2. why R2 was selected;
3. what R2-01 will inspect;
4. what it will produce;
5. confirm that no implementation or formal benchmark will be started before the impact survey/design freeze.
