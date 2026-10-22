# N05D-04R2 — Hierarchical Multi-Vector Redesign Task Breakdown

Updated: 2026-10-23

- Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Status: **Active / R2-01〜R2-02 Complete**
- Formal N-05: **BLOCKED / Not Complete**
- Design plan: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- R2-01 freeze: `docs/planning/phases/N/N05/N05D04R2_IMPACT_SURVEY.md`
- R2-02 freeze: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

## 1. Execution order

```text
R2-01 Impact survey / design freeze                    Complete
  ↓
R2-02 Requirements + representation contract revision Complete
  ↓
R2-03 Persistence/versioning/migration design          Next
  ↓
R2-04 object_overview builder implementation
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

Do not start R2-09 formal N-05 timing before R2-08 passes.

## 2. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| R2-01 | P0 | **Complete** | affected contracts/code/data pathsをinventoryし、redesign boundaryをfreeze |
| R2-02 | P0 | **Complete** | Search Requirements / Search Representation / Hybrid / Similarity designをv2へ改定 |
| R2-03 | P0 | **Next / Not Started** | `object_overview` persistence、builder version、generation/cutover/rollbackを設計 |
| R2-04 | P0 | Not Started | deterministic compact `object_overview` builderとmaterializationを実装 |
| R2-05 | P0 | Not Started | Hybrid Searchを`object_overview + facet + statement`へ移行 |
| R2-06 | P0 | Not Started | overall Object Similarityをhierarchical multi-vector方式へ再設計・実装 |
| R2-07 | P0 | Not Started | Derived Search side-by-side rebuild / Qdrant cutover / rollbackを実装・検証 |
| R2-08 | P0 | Not Started | frozen gold拡張、quality acceptance、N-06影響確認 |
| R2-09 | P0 | Not Started | resource acceptance後、新run_idでformal N-05を全46 sample再実行 |
| R2-10 | P0 | Not Started | docs / decision / closure auditを更新しN-05 final stateを確定 |

---

## R2-01 [P0] — Impact survey / redesign freeze

### Status

**Complete.**

Deliverable:

`docs/planning/phases/N/N05/N05D04R2_IMPACT_SURVEY.md`

### Goal

実装前に、`object_overall`へ依存しているすべてのcontract・code path・gold・benchmarkを列挙し、変更漏れを防ぐ。

### Required survey

最低限次を検索・分類する。

```text
object_overall
SearchRepresentationKind
build_object_overall
semantic_object_overall
find_similar_objects
knowledge_search_representation_memberships
search_representation_embeddings
KnowledgeVectorIndexBuilder
Search quality gold
N-03/N-04/N-05/N-06 fixtures
MCP / CLI outputs exposing representation_kind
```

分類:

```text
KEEP unchanged
RENAME / compatibility shim
CHANGE semantics
MIGRATE data
REBUILD derived artifact
UPDATE gold/test
HISTORICAL only
```

### Exit

- no unresolved active `object_overall` consumer remains outside the inventory;
- canonical Knowledge tables confirmed out-of-scope for semantic content migration;
- exact compatibility obligations for CLI/MCP/domain API documented.

---

## R2-02 [P0] — Requirements and design contract revision

### Status

**Complete / Design Freeze.**

Normative deliverable:

`docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`

Updated canonical design:

```text
docs/requirements/SEARCH_REQUIREMENTS.md
docs/design/SEARCH_REPRESENTATION_SCHEMA.md
docs/design/HYBRID_SEARCH_OBJECT_AGGREGATION.md
docs/design/OBJECT_SIMILARITY_SEARCH.md
```

Historical superseding notes:

```text
docs/planning/phases/I/PHASE_I_PREPARATION.md
docs/planning/phases/I/PHASE_I_CLOSURE_AUDIT.md
```

### Goal

新しいhierarchical multi-vector semanticsを、実装より先に正本designへ反映する。

### Frozen decisions

1. `object_overview` exact semantic fields: canonical name, aliases, Primary Class, facet-less Summary Statements, content Facet key/name inventory, searchable Attributes, Relations.
2. `object_overall` is legacy-only after cutover and is not a rename/alias of `object_overview`.
3. Relation remains in `object_overview`; a canonical `relationships` content Facet may also carry Relation semantics. No independent Relation representation kind is added.
4. `builder_key = sgokb-canonical-search`; `object_overview` uses content-contract builder version 2; unchanged Facet/Statement/Evidence remain version 1. Builder version is not Derived Search generation identity.
5. Hybrid active semantic channels are `semantic_object_overview / semantic_facet / semantic_statement`; first R2 baseline keeps RRF `k=60` and contribution caps `1 / 2 / 3`, with Knowledge lexical cap `3`.
6. Overall Object Similarity is bounded hierarchical multi-vector; final `score_type = hierarchical_similarity`. Facet-specific Similarity remains same-Facet `cosine_similarity`.
7. Overall Similarity exposes bounded overview/Facet/Statement component evidence including representation/membership identity, raw cosine, and aggregate contribution.
8. Arbitrary token chunking, silent truncation, synthetic replacement summaries, and model-change workarounds are not the redesign.
9. First R2 baseline keeps Harrier OSS v1 0.6B unchanged.

### Exit

All implementation-visible R2 semantics are frozen. No unresolved semantic design question blocks R2-03 persistence/schema/cutover design.

---

## R2-03 [P0] — Persistence / versioning / migration design

### Goal

新kindを安全に導入し、v1 derived artifactsと混在・誤読しない migration contractを固定する。

### Required decisions

Evaluate and fix:

```text
SearchRepresentationKind = object_overview addition
legacy object_overall parse/read compatibility
DB CHECK/enum constraints
new migration number
builder version persistence
Derived Search generation identity
active/candidate generation switching
membership uniqueness
embedding reuse eligibility
vector point payload kind/generation
full rebuild behavior
rollback behavior
legacy cleanup
```

### Safety requirements

- no canonical Knowledge rewrite;
- no destructive v1 delete before accepted v2 cutover;
- v1/v2 query mixing impossible after cutover;
- interrupted rebuild leaves previous active generation usable or explicitly unavailable, never half-current;
- current/historical semantics remain membership-based;
- builder content-contract version is not misused as generation/cutover identity.

### Deliverable

Design note plus migration plan, before writing migration SQL.

### Exit

Schema and cutover design approved; migration implementation can proceed without further semantic decisions.

---

## R2-04 [P0] — Implement compact `object_overview`

### Goal

全Facet Statementを再掲しないdeterministic Object-level representationを実装する。

### Expected content

```text
Object name
aliases
Primary Class
Facet-less Summary Statements
content Facet name/key inventory
known structured Attributes
Relations
```

Explicitly exclude:

```text
content Facet Statement bodies
Statement IDs / UUIDs
workflow metadata
gap / unresolved / proposal metadata
LLM-generated synthetic summary
```

### Implementation scope

Expected files include:

```text
src/sgokb/domain/knowledge.py
src/sgokb/retrieval/search_representation.py
src/sgokb/storage/semantic_repository.py
migration(s)
tests/test_search_representation.py
```

### Tests

- deterministic byte-identical output;
- no Facet Statement body duplication;
- Summary Statements retained;
- Attributes/Relations retained;
- Facet identity inventory deterministic;
- reuse/membership semantics correct;
- current/historical isolation preserved;
- accepted Version boundary preserved.

### Resource diagnostic

On the N-05 Large fixture:

```text
record exact object_overview token count
engineering target <= 4096 tokens
no truncation
```

If >4096, do not truncate; return to design review.

### Exit

Builder/materialization focused tests PASS and Large fixture no longer produces a giant mandatory Object-level input.

---

## R2-05 [P0] — Hybrid Search migration

### Goal

Normal semantic/hybrid Object Searchをnew active representationへ移行する。

### Required changes

```text
semantic_object_overall -> semantic_object_overview
knowledge lexical active-kind update
Qdrant kind/generation filter update
match/result representation_kind update
bounded compatibility handling for old clients/tests
```

Keep unless quality evidence says otherwise:

```text
RRF k=60
Object overview contribution cap=1
Facet cap=2
Statement cap=3
Knowledge lexical cap=3
exact identity priority tier
```

### Required regression

- `1 Object = 1 result`;
- Statement-count boost remains bounded;
- exact name/alias priority unchanged;
- Facet/temporal/derivation filters exclude Object-level overview where semantically unsafe;
- degraded semantic behavior unchanged;
- explanations identify overview/facet/statement matches;
- legacy `object_overall` does not leak into active v2 results.

### Exit

Existing Hybrid gold passes or any deliberate ranking change is justified by new gold evidence.

---

## R2-06 [P0] — Hierarchical Object Similarity redesign

### Goal

Remove the one-giant-vector assumption from `find_similar_objects(facet=None)`.

### Required design benchmark

Evaluate bounded algorithms that combine at least:

```text
overview ↔ overview
same-Facet ↔ same-Facet
bounded detailed Statement evidence
```

Candidate approaches may include:

```text
A. overview candidate generation + Facet/Statement rerank
B. overview + Facet multi-channel candidate union + bounded score aggregation
C. derived aggregate vector from existing child vectors, only if semantics/quality are demonstrated
```

Do not select an algorithm solely by implementation simplicity.

### Hard constraints

- no unbounded all-pairs Statement comparison;
- candidate count and per-channel contribution bounded;
- same Primary Class default and `cross_class=True` semantics preserved;
- Facet-specific API remains same-Facet only;
- Source Object excluded before candidate limit;
- historical Source / current Candidate semantics preserved;
- final overall `score_type = hierarchical_similarity`; do not call a fused aggregate raw cosine similarity;
- matched overview/Facet/Statement evidence remains inspectable and bounded.

### New gold cases

Add cases where:

- overview/name/summary alone is insufficient;
- similarity depends on one or more detailed Facets;
- similarity depends on a small number of important Statements;
- a large Object with many irrelevant Statements must not dominate a smaller but genuinely similar Object.

### Exit

Algorithm fixed by quality + latency evidence and implemented with focused regression tests.

---

## R2-07 [P0] — Derived Search rebuild / cutover / rollback

### Goal

Candidate v2 representation/embedding/vector stateをside-by-sideで構築し、安全にcurrent retrievalへ切り替える。

### Required work

- rebuild v2 Search Representations from canonical accepted Knowledge;
- generate missing Harrier 0.6B embeddings;
- build isolated Qdrant namespace/generation;
- verify counts and membership identity;
- run semantic + filtered query smoke;
- switch active generation atomically or through an explicitly safe sequence;
- verify old v1 state no longer serves normal current retrieval;
- preserve rollback path and evidence.

### Required invariants

```text
canonical state before == after
all current accepted Versions represented
all searchable Statements represented
all content Facets represented
no mixed v1/v2 active result
Qdrant failure cannot corrupt canonical Knowledge
```

### Exit

Cutover/rollback rehearsal PASS on isolated/reference data.

---

## R2-08 [P0] — Search-quality acceptance

### Goal

performance remediationによるretrieval品質劣化をformal rerun前に検出する。

### Required evaluation

Re-run/extend:

```text
benchmark/search-quality-gold-v1.json
Object Semantic / Hybrid
Statement retrieval
Facet similarity
Object hierarchical similarity
filters/current-history/temporal
Evidence Search non-regression
```

N-06 assets/results must be reviewed because this redesign changes Retrieval semantics before N-06 closure.

### Acceptance

- required Search contracts PASS;
- no unexplained material regression in MRR/Recall/nDCG;
- hierarchical similarity new cases PASS;
- latency/resource values recorded;
- model remains Harrier 0.6B for causal comparison.

If quality fails, return to R2-05/R2-06; do not switch models merely to hide the regression.

### Exit

Quality acceptance explicitly authorizes performance testing.

---

## R2-09 [P0] — Performance/resource acceptance and formal N-05 rerun

### Goal

根本修正後のsystemをReference Workstationで正式評価する。

### Preflight

- clean `main == origin/main`;
- >=32 GiB free on repository/Qdrant hosting volumes;
- remediated Qdrant runtime active;
- Harrier 0.6B accepted runtime fixed;
- no material competing CUDA workload;
- full regression/Ruff/diff PASS;
- R2-08 quality acceptance PASS.

### First diagnostic comparison

Before 46 formal samples, compare v1 vs v2 Large fixture:

```text
object-level token length
peak allocated/reserved
Dedicated/Shared GPU memory
derived_incremental_sync wall-clock
end-to-end sample wall-clock
```

This diagnostic does not replace formal samples.

### Formal run

Use a new run ID and start at Standard cold-01:

```text
Standard cold 3 + warm 20
Large cold    3 + warm 20
```

Formal gates remain:

```text
Standard warm p95 <= 600 s
Large warm p95    <= 1200 s
terminal failure / abort = 0
```

No failed sample replacement.

### Exit

Deterministic evaluator returns judgeable PASS/FAIL and post-run safety/regression evidence is complete.

---

## R2-10 [P0] — Closure and state update

### Goal

redesignとN-05最終結果を全正本へ反映する。

### Update at minimum

```text
docs/evaluation/N05_PERFORMANCE.md
docs/evaluation/N05D04_RESOURCE_PREFLIGHT_AND_VRAM_RESEARCH.md
docs/planning/phases/N/N05/N05_PERFORMANCE_BENCHMARK.md
docs/planning/phases/N/N05/N05_BLOCKER_DIAGNOSTIC_PLAN.md
docs/planning/phases/N/N05/execution/N05D04_FORMAL_RERUN_HANDOFF.md
docs/planning/phases/N/PHASE_N_PREPARATION.md
Phase I superseding design/closure notes
```

### Final state

If formal performance PASS:

```text
N05D-04R2 = Complete
N05D-04   = Complete
N-05      = Complete / PASS
```

If judgeable FAIL:

```text
N05D-04R2 implementation/quality = Complete
N-05 = FAIL / Not Complete
```

and create a new explicit optimization/design task rather than silently continuing R2.

If environment/evidence BLOCKED:

```text
N-05 = BLOCKED / Not Complete
```

with the new blocker isolated.

## 3. Model-change contingency

Harrier 270M is explicitly **not** part of R2-01 through R2-09 baseline execution.

Only open a model-change task if hierarchical redesign with Harrier 0.6B still shows unacceptable:

```text
performance
resource pressure
operational stability
```

or if a separately motivated quality/cost study justifies it.

A model change requires a new Embedding Space identity, full Derived Search rebuild, and N-06/search-quality re-acceptance.

## 4. Current next task

**Next: R2-03 [P0] — Persistence / versioning / migration design.**

Do not start production implementation, migration execution, Derived Search rebuild, R2-08 quality acceptance, or R2-09 formal 46-sample execution as part of R2-02.
