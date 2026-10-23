# N05D-04R2 / R2-06 — Hierarchical Object Similarity Redesign

Updated: 2026-10-23

- Parent: `N05D-04R2 — Hierarchical Multi-Vector Derived Search Redesign`
- Task: `R2-06 [P0] — Hierarchical Object Similarity redesign`
- Status: **Complete / Runtime Verification PASS**
- Production cutover: **Not Started — R2-07 owns cutover / rollback**
- Baseline model: **Harrier OSS v1 0.6B unchanged**

## 1. Decision

For `find_similar_objects(object_id, facet=None, ...)`, adopt **candidate B**:

```text
Object overview candidate channel
+ same-Facet candidate channels
+ bounded same-Facet Statement candidate channels
        ↓
bounded candidate Object union
        ↓
bounded component aggregation
        ↓
1 Object = 1 SimilarObjectResult
```

The final overall score is:

```text
score_type = hierarchical_similarity
```

It is not described as one cosine similarity.

Facet-specific similarity remains the existing same-Facet raw cosine operation:

```text
find_similar_objects(..., facet=<facet>)
score_type = cosine_similarity
```

No fallback from a missing requested Facet to overview, another Facet, or legacy
`object_overall` is allowed.

## 2. Why candidate B

### A. overview candidates + Facet/Statement rerank

Not selected as the R2 baseline.

Advantages:

- fewer ANN searches;
- simplest operational shape.

Disadvantage:

- a genuinely similar Object whose compact overview is insufficient can be removed
  before detailed Facet/Statement evidence is consulted;
- this conflicts with the R2 gold requirement that detailed Knowledge can establish
  similarity when overview alone is insufficient.

### B. overview + Facet multi-channel candidate union + bounded aggregation

**Selected.**

Advantages:

- overview remains a broad Object anchor;
- detailed same-Facet evidence can independently introduce a candidate;
- a small number of important Statements can independently introduce a candidate;
- every source query, candidate set, and final contribution has an explicit bound;
- no new synthetic vector semantics are introduced;
- component evidence remains inspectable.

Trade-off:

- more ANN searches than A, so source-side query counts are hard-capped.

### C. derived aggregate vector from child vectors

Not selected.

R2 has no accepted semantic proof that an average/sum/other aggregate of child
vectors represents the same semantic object as canonical hierarchical similarity.
It would add a new derived representation contract solely for implementation
convenience and would require separate quality/versioning work.

## 3. Generation routing

The operation resolves the active Knowledge Search generation **once at operation
start**.

Routing is:

```text
no active pointer
  -> pre-cutover Phase-I compatibility path

active phase-i-search-v1
  -> generation-scoped object_overall / Facet cosine compatibility

active n05d04r2-hierarchical-v2
  -> hierarchical overall similarity
     or same-Facet cosine when facet is explicitly requested
```

All R2 Vector evidence must carry the same `generation_id` as the resolved active
generation. A payload mismatch is an integrity error.

SQLite membership details are also resolved through:

```text
active generation
  -> knowledge_search_generation_memberships
  -> knowledge_search_representation_memberships
```

A Vector point that is not linked to that generation is an integrity error.

## 4. R2 source representation selection

For overall similarity, the accepted source Version contributes:

```text
object_overview : exactly 1
Facet           : at most 8
Statement       : at most 12
```

### 4.1 Overview

The active R2 generation must contain exactly one `object_overview` membership for
the source Version. Missing or duplicate overview membership is an integrity error.

### 4.2 Facet source cap

At most 8 content Facet memberships are selected in deterministic canonical Facet
key / membership order.

Each Facet query can compare only against the **same canonical Facet**.

### 4.3 Statement source cap

At most 12 detailed Statement memberships are selected.

Facet-less Summary Statements are not queried again as detailed Statement evidence,
because their semantic role is already present in `object_overview`.

Faceted Statements are selected by deterministic round-robin across Facets, with
stable local-key / Statement / membership ordering inside each Facet. This prevents
a large Facet from consuming the source Statement budget merely because it contains
many Statements.

Each Statement query can compare only against candidate Statements in the same
canonical Facet.

## 5. Candidate generation bounds

Per source query:

```text
overview ANN limit  = 128
Facet ANN limit     = 24
Statement ANN limit = 12
```

Maximum ANN calls for one R2 overall operation:

```text
1 overview + 8 Facets + 12 Statements = 21 searches
```

Maximum raw point hits before Object deduplication:

```text
128 + (8 * 24) + (12 * 12) = 464
```

The source Object is excluded in the Vector hard filter **before** each ANN limit.

The post-union Object candidate cap is:

```text
128 Objects
```

Candidates default to the same Primary Class as the source. `cross_class=True`
removes that class constraint explicitly.

Candidates are current accepted Versions. The source may be an explicitly requested
historical accepted Version.

## 6. Per-source-query Object bound

One source representation query may return several Statement points from the same
candidate Object.

Before cross-query aggregation, retain only the best point from each candidate
Object for that one source query.

Therefore an Object cannot gain multiple contributions from merely having many
candidate Statements that all match one source Statement.

## 7. Final component caps and weights

Frozen R2-06 baseline:

| Component | Base weight | Max evidence per candidate |
|---|---:|---:|
| overview | 0.50 | 1 |
| same-Facet | 0.30 | 2 |
| same-Facet Statement | 0.20 | 3 |

These are R2-06 algorithm constants. They are not representation builder versions
or generation identifiers.

## 8. Aggregation formula

For each raw component cosine `c`:

```text
bounded_cosine(c) = max(0, min(1, c))
```

The raw cosine remains recorded unchanged for explainability. Only its bounded
positive form contributes to hierarchical ranking.

Let active source components be those for which the source has at least one selected
representation. Normalize the base component weights over those source components:

```text
normalized_weight_j
  = base_weight_j / sum(base_weight for active source components)
```

For component `j`, define:

```text
slot_count_j
  = min(component_evidence_cap_j, selected_source_count_j)
```

Take the candidate's highest bounded evidence items for that component, up to its
component cap. Missing evidence leaves the corresponding slot contribution at zero.

```text
component_score_j
  = sum(top bounded cosine values) / slot_count_j

component_contribution_j
  = normalized_weight_j * component_score_j

hierarchical_similarity
  = sum(component_contribution_j)
```

Therefore:

```text
0 <= hierarchical_similarity <= 1
```

Statement count, Facet count, or duplicate candidate points cannot increase the
score without crossing one of the frozen source/evidence caps.

## 9. Deterministic ordering

Final ordering:

```text
hierarchical_similarity DESC
object_id ASC
version_id ASC
```

Component evidence is ordered deterministically by:

```text
component order: overview -> facet -> statement
contribution DESC
source membership ID
candidate membership ID
```

## 10. Explainability contract

Each bounded overall evidence item exposes:

```text
component
source_representation_id
source_membership_id
candidate_representation_id
candidate_membership_id
representation_kind
facet
source_statement_id
candidate_statement_id
raw score
raw score_type = cosine_similarity
bounded contribution to final score
```

`SimilarObjectResult.score_type` for overall R2 results is always:

```text
hierarchical_similarity
```

The existing `representation_id` / `membership_id` fields remain for compatibility.
For overall R2 results they are a compatibility anchor, preferring the candidate
`object_overview` evidence when present. They must not be interpreted as the sole
basis of the final hierarchical score.

`ObjectSimilarityResponse` additionally exposes the source membership anchor and
resolved generation when available.

## 11. Facet-specific compatibility

When `facet` is supplied:

- source membership must be that exact Facet;
- candidates must be current membership of the same exact Facet;
- raw cosine ranking remains unchanged;
- `score_type = cosine_similarity`;
- no overview or Statement fallback is introduced.

## 12. Pre-cutover compatibility

R2-06 does not perform production cutover.

Before R2-07 establishes an active generation pointer, the existing Phase-I
Similarity path remains available unchanged. This preserves deployed v1 behavior
while the R2 implementation is present but not yet activated.

An explicitly active Phase-I v1 generation remains generation-scoped and continues
to use `object_overall` for overall similarity. This supports later rollback
eligibility without pretending that `object_overall` is an R2 representation.

## 13. Implementation

Added/changed implementation surface:

```text
src/sgokb/domain/search.py
src/sgokb/domain/__init__.py
src/sgokb/retrieval/similarity_r2.py
src/sgokb/retrieval/__init__.py
tests/test_object_similarity_r2.py
```

The historical Phase-I implementation in:

```text
src/sgokb/retrieval/similarity.py
```

is retained as the explicit pre-cutover/v1 compatibility base.

## 14. Regression / gold-oriented cases

R2-06 adds focused cases for:

1. overview tie resolved by detailed Facet evidence;
2. overview + Facet tie resolved by a small number of important Statements;
3. a large Object with many irrelevant Statements not winning by Statement count;
4. same-Facet boundary preventing cross-Facet Statement evidence;
5. source Object exclusion before ANN limit;
6. same-class default and explicit `cross_class=True`;
7. historical source Version with current candidate Versions;
8. active-generation isolation and absence of `object_overall` in R2 evidence;
9. generation payload mismatch as an integrity error;
10. one operation resolving generation exactly once;
11. bounded source query count and bounded result evidence count;
12. active-R2 Facet-specific raw-cosine behavior unchanged;
13. Qdrant in-memory R2 smoke when the optional dependency is present.

## 15. Runtime verification — PASS (2026-10-23)

Verified GitHub main input: `d1c491bd89913a0adf2c70fc80604dc3752634ce`.
Reference Workstation: Python 3.10.6, pytest 9.1.1, Ruff 0.17.0,
qdrant-client 1.19.1. An isolated verification worktree was used. The original workspace's three R1
user-aborted assets were backed up and preserved byte-for-byte (SHA-256).

| Command (`python -m pytest -q`) | Result |
|---|---|
| `tests/test_object_similarity_r2.py` | 19 passed |
| `tests/test_object_similarity.py tests/test_object_similarity_r2.py` | 28 passed |
| `tests/test_hybrid_search.py tests/test_hybrid_search_r2.py` | 33 passed |
| `tests/test_search_generation_migration.py tests/test_search_representation.py tests/test_object_overview_r2.py` | 14 passed |
| Application / MCP / CLI / Vector / Derived Search group below | 83 passed |

**158 unique tests passed, 0 failed, 0 skipped**; the standalone 19 R2 tests are
included in the joint Similarity count. The 83-test group covers
`test_j01_similarity_application.py`, `test_j01_retrieval_mcp_boundary.py`,
`test_j01_application_semantics.py`, `test_j02_mcp_read_tools.py`,
`test_j06_mcp_client_acceptance.py`, `test_m01_cli.py`, `test_vector_index.py`,
`test_n04p02_search_representation_sync.py`, `test_n04p03_embedding_sync.py`,
`test_n04p04_vector_index_sync.py`, `test_n04p05_derived_cli.py` and
`test_n02_integration.py`.

Findings and scoped maintenance:

- The historical-source fixture assigned different vectors to identical reused
  overview content. Give its Versions different Summary content, assert distinct
  overview representation IDs, and retain historical-source/current-candidate
  ranking assertions. Embedding reuse and production behavior are unchanged.
- Update the stale CLI integrity assertion from schema 17 to 18.
- Add active-v1 overall/Facet cosine compatibility and real Application -> CLI/MCP
  serialization checks, including established fields and additive evidence.
- Exercise ten source Facets / thirty Statements: only 8/12 child queries run,
  exactly 21 ANN calls / 464 maximum hit slots; 130 candidates still yield at most
  128 distinct Objects. Per-result evidence remains at most 1/2/3 and score `[0,1]`.
- Verify both generation payload mismatch rejection and SQLite membership rejection
  even with a matching payload, one generation resolution per operation, active-R2
  `object_overall` exclusion, current/historical isolation, and explicit no-fallback
  on a missing source Facet. G01-G06 contracts PASS with frozen constants unchanged.
- Canonical consumer import review finds only the internal Phase-I base import in
  `similarity_r2.py`; active consumers use the public R2 wrapper.
- Ruff formatting of `similarity_r2.py` is AST-identical to the input implementation.

Qdrant dependency is available. R2 hierarchical, existing v1 Similarity, Hybrid and
Vector adapter regressions PASS in memory. Local Qdrant warns that payload indexes
have no effect and search is brute force: this proves adapter/filter semantics,
not native-server ANN performance. No production Qdrant namespace was touched.

Static checks:

- `python -m ruff check src tests`: PASS.
- R2-06 source/domain/export/test files plus the maintained CLI test:
  `python -m ruff format --check`: PASS (8 files).
- `git diff --check`: PASS.
- `python -m ruff check .`: only the documented unrelated baseline
  `benchmark/tools/n05_resource_preflight.py:69 E501`; left unchanged. All R2-06
  files and `src tests` pass. Full pytest was not required or run for this task.

```text
R2-06 = Complete
R2-07 = Next / Not Started
N-05 = BLOCKED / Not Complete
```

No production generation readiness/active pointer, canonical DB, Qdrant namespace,
v1 artifact retirement, R2-07 rebuild/cutover/rollback or formal N-05 run was performed.
