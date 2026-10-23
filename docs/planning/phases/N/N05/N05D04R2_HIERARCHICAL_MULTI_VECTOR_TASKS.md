# N05D-04R2 — Hierarchical Multi-Vector Redesign Task Breakdown

Updated: 2026-10-24

- Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Status: **Active / R2-05 and Candidate E R2-06 remediation verified / R2-08 formal review pending**
- Formal N-05: **BLOCKED / Not Complete**
- Design plan: `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_REDESIGN.md`
- R2-01 freeze: `docs/planning/phases/N/N05/N05D04R2_IMPACT_SURVEY.md`
- R2-02 freeze: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`
- R2-03 freeze: `docs/planning/phases/N/N05/N05D04R2_PERSISTENCE_VERSIONING_MIGRATION_DESIGN.md`
- R2-04 implementation: `docs/planning/phases/N/N05/N05D04R2_OBJECT_OVERVIEW_IMPLEMENTATION.md`

## 1. Execution order

```text
R2-01 Impact survey / design freeze                    Complete
  ↓
R2-02 Requirements + representation contract revision Complete
  ↓
R2-03 Persistence/versioning/migration design          Complete
  ↓
R2-04 object_overview builder implementation           Complete
  ↓ runtime verification PASS
R2-05 Hybrid Search migration                          Complete
R2-06 Hierarchical Object Similarity redesign          Complete
          ↓
R2-07 Derived Search rebuild / cutover / rollback      Complete
          ↓
R2-08 Search-quality acceptance                       FAIL / Not Complete
          ↓
R2-09 Performance/resource acceptance + formal N-05 rerun
          ↓
R2-10 Closure / Phase N state update
```

Do not start R2-05/R2-06 until the R2-04 runtime verification gate passes. Do not start R2-09 formal N-05 timing before R2-08 passes.

## 2. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| R2-01 | P0 | **Complete** | affected contracts/code/data pathsをinventoryし、redesign boundaryをfreeze |
| R2-02 | P0 | **Complete** | Search Requirements / Search Representation / Hybrid / Similarity designをv2へ改定 |
| R2-03 | P0 | **Complete / Design Freeze** | `object_overview` persistence、builder version、generation/cutover/rollbackを設計 |
| R2-04 | P0 | **Complete** | deterministic compact `object_overview` builderとmaterializationを実装し、focused/runtime evidenceでexitを確認 |
| R2-05 | P0 | **Complete** | Hybrid Searchを`object_overview + facet + statement`へ移行 |
| R2-06 | P0 | **Complete** | overall Object Similarityをhierarchical multi-vector方式へ再設計・実装 |
| R2-07 | P0 | **Complete** | Derived Search side-by-side rebuild / Qdrant cutover / rollbackを実装・検証 |
| R2-08 | P0 | **FAIL / Not Complete** | frozen gold拡張、quality acceptance、N-06影響確認 |
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

### Status

**Complete / Design Freeze.**

Normative deliverable:

`docs/planning/phases/N/N05/N05D04R2_PERSISTENCE_VERSIONING_MIGRATION_DESIGN.md`

### Goal

新kindを安全に導入し、v1 derived artifactsと混在・誤読しない migration contractを固定する。

### Frozen decisions

```text
active Object kind          = object_overview
legacy readable Object kind = object_overall
generic OBJECT enum alias   = retired, not remapped
next migration              = 018_search_generation_contract.sql
builder version identity    = per representation kind
Knowledge generation        = explicit generation identity
active routing              = singleton SQLite pointer
generation membership       = separate generation -> membership link
Embedding reuse             = representation x Embedding Space
Vector namespace            = generation x Embedding Space x backend
Vector point identity       = membership ID inside generation namespace
current/historical          = membership + canonical current pointer
```

Additional rules:

- `object_overall` rows are preserved and never relabeled to overview;
- unchanged Facet/Statement memberships may be shared by v1/v2 generations;
- unchanged Facet/Statement Harrier embeddings may be reused;
- `object_overview` must receive new representation/embedding identity;
- Qdrant v1 and v2 are isolated by namespace rather than mixed in one serving collection;
- Knowledge lexical retrieval is active-generation scoped even though the FTS content table may contain both old and new rows;
- candidate cutover is one transactional active-pointer switch after all preconditions pass;
- interrupted candidate rebuild leaves the previous active generation unchanged;
- rollback requires the previous generation to remain catalog/integrity compatible;
- physical v1 cleanup is deferred until later acceptance/retention decisions;
- Evidence Search remains outside the Knowledge generation migration.

### Safety requirements

- no canonical Knowledge rewrite;
- no destructive v1 delete before accepted v2 cutover;
- v1/v2 query mixing impossible after cutover;
- interrupted rebuild leaves previous active generation usable or explicitly unavailable, never half-current;
- current/historical semantics remain membership-based;
- builder content-contract version is not misused as generation/cutover identity.

### Exit

Schema and cutover design are frozen. Migration/domain/builder implementation can proceed without further persistence-semantic decisions.

---

## R2-04 [P0] — Implement compact `object_overview`

### Status

**Complete - Reference Workstation runtime verification PASS (2026-10-23).**

Implementation record:

`docs/planning/phases/N/N05/N05D04R2_OBJECT_OVERVIEW_IMPLEMENTATION.md`

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
src/sgokb/migrations/018_search_generation_contract.sql
tests/test_search_representation.py
migration/generation-focused tests
```

R2-04 may implement the persistence/domain pieces frozen by R2-03 that are necessary to store and materialize `object_overview`, but it must not perform production cutover.

Implemented on `main`:

```text
OBJECT_OVERVIEW enum + explicit legacy OBJECT_OVERALL
per-kind builder version selection
build_object_overview()
materialize_version_r2()
migration 018 coexistence/generation schema
object_overview uniqueness + FTS support
generation kind guards
focused builder/migration tests
exact Harrier token diagnostic tool
```

The existing `materialize_version()` remains the v1 serving path until R2-05/R2-06 migrate downstream retrieval; this prevents a half-cutover.

### Tests

- deterministic byte-identical output;
- no Facet Statement body duplication;
- Summary Statements retained;
- Attributes/Relations retained;
- Facet identity inventory deterministic;
- reuse/membership semantics correct;
- current/historical isolation preserved;
- accepted Version boundary preserved;
- migration preserves v1 IDs/content/memberships/embeddings;
- generation membership cannot mix v1 overall into an R2 candidate.

Focused pytest: **14 passed**, including populated pre-018 migration preservation.
R2 source/tests/diagnostic Ruff, test format and diff checks PASS. See the
implementation record for the unrelated repository-wide baseline E501.

### Resource diagnostic

On the N-05 Large fixture:

```text
record exact object_overview token count
engineering target <= 4096 tokens
no truncation
```

The frozen Large fixture has 1200 Statements. Its fixture builder places 5 into `knowledge.summary` and the remaining 1195 into three content Facets. The R2 overview structurally includes the five Summary Statements and Facet identities, not those 1195 Facet Statement bodies.

Exact measurement is provided by:

`benchmark/tools/n05d04r2_object_overview_diagnostic.py`

The diagnostic uses the frozen Harrier revision with `truncation=False` and does not mutate the supplied benchmark database.

If >4096, do not truncate; return to design review.

### Exit

Builder/materialization focused tests PASS and Large fixture no longer produces a giant mandatory Object-level input.

Confirmed exit evidence (2026-10-23):

```text
focused pytest PASS
migration 003..018 preservation/integrity PASS
repository-required static/Ruff checks PASS
exact Large object_overview Harrier token count recorded
exact token count 103 <= 4096, truncation=False
```

---

## R2-05 [P0] — Hybrid Search migration

### Status

**Complete - Reference Workstation runtime verification PASS (2026-10-23).**
R2-only 24 passed; Hybrid combined 33 passed; migration/representation 14 passed;
Application/maintenance/CLI/MCP/Vector 70 passed (**117 non-overlapping passes**).
Both v1 and R2 Qdrant local adapter regressions passed. R2 source/tests Ruff,
target format and diff checks PASS; known unrelated resource-preflight E501 is
unchanged. Stale migration expectation 17 -> 18 and wrapper lint were corrected;
no production algorithm change. Active generation, family/channel identity,
filter/no-fallback/history/RRF/cap/exact-priority/degradation gates passed.

Details: [runtime verification record](N05D04R2_HYBRID_SEARCH_MIGRATION.md#11-reference-workstation-verification---2026-10-23).
No production readiness/pointer/Qdrant/v1 artifact change or R2-06/R2-07 work.

### Goal

Normal semantic/hybrid Object Searchをnew active representationへ移行する。

### Required changes

```text
semantic_object_overall -> semantic_object_overview
knowledge lexical active-kind/generation update
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
- legacy `object_overall` does not leak into active v2 results;
- one request resolves one generation for all Knowledge channels.

### Exit

Existing Hybrid gold passes or any deliberate ranking change is justified by new gold evidence.

---

## R2-06 [P0] — Hierarchical Object Similarity redesign

### Status

**Complete / runtime verification PASS (2026-10-23).** Candidate B uses frozen
1/8/12 source queries, 128/24/12 query limits, weights 0.50/0.30/0.20 and evidence
caps 1/2/3. G01-G06, generation/history isolation, active-v1, Facet and public
Application/CLI/MCP compatibility PASS; 158 unique relevant tests passed.
[Implementation and verification record](N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md).

The design alternatives below are the original selection requirements.

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
- matched overview/Facet/Statement evidence remains inspectable and bounded;
- all Vector evidence must come from the request's resolved active generation.

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

### Status

**Complete / runtime verification and reference cutover drill PASS (2026-10-23).**
Full pytest 635 PASS; focused/Qdrant 29, R2 regression 104, compatibility 83 PASS
(focused is included in R2). Native reference bootstrap, isolated R2 build
(18 reused / 6 new embeddings), cutover, rollback and same-candidate re-cutover
PASS. Each generation has 24 memberships/points with exact identity/payload audit.
Final active is R2; v1 is intact and rollback-capable for the unchanged catalog.
Canonical digests/counts for 45 tables and three R1 asset hashes are unchanged.
[Execution and evidence record](N05D04R2_DERIVED_SEARCH_CUTOVER.md).

### Goal

Candidate v2 representation/embedding/vector stateをside-by-sideで構築し、安全にcurrent retrievalへ切り替える。

### Required work

- register/verify legacy v1 generation and existing Vector namespace;
- rebuild v2 Search Representations from canonical accepted Knowledge;
- generate missing Harrier 0.6B embeddings while reusing eligible Facet/Statement embeddings;
- build isolated generation-specific Qdrant namespace;
- verify counts, digests, membership identity and generation payload;
- run semantic + filtered query smoke;
- switch active generation through the frozen transactional SQLite pointer contract;
- verify old v1 state no longer serves normal current retrieval;
- rehearse eligible rollback and preserve evidence.

### Required invariants

```text
canonical state before == after
all current accepted Versions represented
all searchable Statements represented
all content Facets represented
no mixed v1/v2 active result
Qdrant failure cannot corrupt canonical Knowledge
active pointer never selects partial candidate
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

**R2-07 = Complete. Next: R2-08 [P0] — Search-quality acceptance
(Next / Not Started).**

Run `20261023T135304+0900` passed verified v1 bootstrap, isolated R2 build, atomic
cutover, rollback and forward re-cutover. Final active R2 has zero `object_overall`;
both 24-point namespaces are intact. Digests/counts of 45 canonical tables and
three R1 asset hashes are unchanged. Focused/Qdrant 29, R2 regression 104,
compatibility 83 and full pytest 635 PASS. Ruff `src tests`, scoped format and
diff PASS; documented unrelated `n05_resource_preflight.py:69 E501` remains unchanged.

[Implementation / runtime record](N05D04R2_DERIVED_SEARCH_CUTOVER.md).
R2-08, artifact retirement and formal N-05 rerun were not started.
N-05 remains BLOCKED / Not Complete.


## R2-05 Semantic remediation update (2026-10-24)

R2-05 = Complete / Semantic remediation runtime verified on the remediation branch.
Measured cause: compact overview over-authority in the inherited equal final
RRF. Stable tested weights 0.25 and 0.50 pass; selected overview=0.50 with
Facet=Statement=1.0. One internal Semantic Object ranking now votes in outer
Hybrid fusion. The 24-query Semantic regression is restored without changing
representations, model, filters, public match identities or R2-06 Similarity.

See `docs/evaluation/N05D04R2_R2_05_SEMANTIC_REGRESSION_ROOT_CAUSE_REVIEW.md`
and `benchmark/results/n05d04r2-r2-05-semantic-remediation.json`.

Current quality state supersedes the historical next-task notes above:
R2-08 = FAIL / Not Complete (separate R2-06 work/concept Similarity losses);
R2-09 = blocked / Not Started. R2-08 can be re-executed after separate Similarity
remediation. No Similarity remediation, performance benchmark or main merge
was performed by this task.


## R2-06 Candidate E runtime update (2026-10-24)

R2-06 remediation = Complete / Candidate E runtime verified on review branch.
All4 frozen Similarity cases, E1-E12 under handoff boundaries, R2SIM-G01..G06,
public/integrity regressions and Windows full suite PASS. All selected-query
Statement observations are retained; ordinary Facet median replaces global
source-slot pooling. Model, acquisition, generation and R2-05 remain unchanged.
See `docs/evaluation/N05D04R2_R2_06_CANDIDATE_E_RESULT.md`.

R2-08 remains Not Complete (prior FAIL not formally closed); code is eligible
for separate formal re-acceptance review. R2-09 remains blocked / Not Started.
No main merge or formal N-05 timing was performed.


## R2-09 execution update (2026-10-24)

This execution result supersedes earlier R2-09 next-task notes:
**R2-09 = BLOCKED / Not Complete; N-05 = BLOCKED / Not Complete;
N05D-04R2 = Active; R2-10 = Not Started.** R2-08 quality acceptance is unchanged.

Mandatory preflight PASS (654 pytest passed; repository-wide Ruff/diff PASS;
124.740 GiB free; external Qdrant healthy; no material competing CUDA workload).
Before GPU timing, source inspection established that the frozen performance
workflow uses default v1 `materialize_version` for fresh samples, producing
`object_overall` instead of the required R2 family. No Large diagnostic or formal
sample was started. Runner/model/scoring/gates were not changed. R1 assets remain
byte-identical. A separately reviewed R2 benchmark-wiring change is required
before a new acceptance attempt; no closure or optimization is started here.

Execution record: `docs/evaluation/N05D04R2_R2_09_PERFORMANCE_ACCEPTANCE_RESULT.md`.


## R2-09 wiring remediation verification (2026-10-24)

The v1-fallback blocker is resolved on `r2-09-runner-wiring-remediation`, pending
review/integration into main. Existing generation-aware maintenance, explicit
model-free empty-R2 bootstrap, and incremental namespace audit/metadata refresh
are connected without changing workload, model, scoring or performance gates.
Focused 158 and Windows full 669 tests PASS; compile, repository-wide Ruff,
changed-file format and diff PASS. One fresh Large diagnostic PASS: active R2,
overall leakage 0, overview 103 exact tokens, 1204 audited points, sync 49.1221762 s,
included total 54.8322218 s; canonical snapshots and three R1 asset hashes unchanged.

See `docs/evaluation/N05D04R2_R2_09_RUNNER_WIRING_REMEDIATION.md` for evidence and
resource peaks. No main merge or formal 46-sample benchmark performed. R2-09/N-05
remain Not Complete pending integration and formal acceptance; R2-10 Not Started.
