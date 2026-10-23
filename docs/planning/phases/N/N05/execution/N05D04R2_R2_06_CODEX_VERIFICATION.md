# N05D-04R2 / R2-06 — Codex Runtime Verification Handoff

Updated: 2026-10-23

## 1. Purpose

Verify the GitHub-main R2-06 implementation and only mark R2-06 Complete when all
focused/regression/static gates pass.

Do **not** start R2-07.

Normative implementation record:

`docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md`

Frozen gold:

`benchmark/n05d04r2-object-similarity-gold-v1.json`

## 2. Local safety first

The original local workspace contains three user-aborted R1 uncommitted assets that
must remain byte-identical.

Before pull/checkout/worktree operations run:

```powershell
git status --short --branch
git diff --stat
git diff --cached --stat
git rev-parse HEAD
```

Record hashes of the three preserved R1 assets before and after verification.

Forbidden:

```text
git reset --hard
git clean
forced checkout over the original workspace
pull before inspecting local state
```

Prefer a separate clean verification worktree if necessary.

## 3. R2-06 implementation surface

Review at least:

```text
src/sgokb/domain/search.py
src/sgokb/domain/__init__.py
src/sgokb/retrieval/similarity_r2.py
src/sgokb/retrieval/similarity.py
src/sgokb/retrieval/__init__.py
tests/test_object_similarity.py
tests/test_object_similarity_r2.py
benchmark/n05d04r2-object-similarity-gold-v1.json
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md
```

Also search for active callers that bypass canonical `sgokb.retrieval.ObjectSimilaritySearch`
by importing the historical `retrieval.similarity.ObjectSimilaritySearch` directly.
Historical tests/base implementation are allowed; active Application/CLI/MCP callers are
not.

## 4. Frozen R2-06 algorithm

Overall R2:

```text
candidate strategy = B
source overview = 1
source Facet query cap = 8
source Statement query cap = 12
overview ANN limit = 128
Facet ANN limit = 24 each
Statement ANN limit = 12 each
raw hit upper bound = 464
candidate Object cap = 128
component weights = overview 0.50 / Facet 0.30 / Statement 0.20
per-result evidence caps = 1 / 2 / 3
final score_type = hierarchical_similarity
```

Facet-specific:

```text
same canonical Facet only
score_type = cosine_similarity
no fallback
```

Do not tune these constants during verification merely to make a test pass. A
semantic failure should return to R2-06 design review.

## 5. Required focused tests

Run at least:

```powershell
pytest tests/test_object_similarity_r2.py
pytest tests/test_object_similarity.py tests/test_object_similarity_r2.py
pytest tests/test_hybrid_search.py tests/test_hybrid_search_r2.py
pytest tests/test_search_generation_migration.py tests/test_search_representation.py tests/test_object_overview_r2.py
```

Then run relevant Application / CLI / MCP / vector-maintenance regressions, including:

```text
tests/test_j01_similarity_application.py
tests/test_j02_mcp_read_tools.py
tests/test_m01_cli.py
similarity-related CLI tests
similarity-related MCP tests
Derived Search maintenance tests
Vector Index/Qdrant tests
```

`tests/test_m01_cli.py` still contains a stale historical assertion expecting schema
migration `17`. Migration 018 is already the current schema. If this assertion is
still present in the verification checkout, update only that stale expectation to
`18`; do not treat it as an R2-06 algorithm change.

Use repository-supported test selection rather than inventing a new formal N-05 run.

## 6. Required semantic assertions

Explicitly verify:

1. overview-only ties can be resolved by same-Facet evidence;
2. overview+Facet ties can be resolved by bounded Statement evidence;
3. many irrelevant candidate Statements do not create count boost;
4. Statement and Facet evidence never cross canonical Facet boundaries;
5. source Object is excluded in Vector filters before ANN limit;
6. same Primary Class is default and `cross_class=True` expands explicitly;
7. historical source Version uses its own embeddings while candidates remain current;
8. active R2 evidence contains no `object_overall`;
9. all R2 evidence comes from one resolved active generation;
10. generation payload mismatch is an integrity error;
11. generation is resolved once per similarity operation;
12. overall final `score_type` is `hierarchical_similarity`;
13. component raw `score_type` is `cosine_similarity`;
14. final score is bounded to `[0,1]`;
15. exposed evidence is bounded to at most 6 items per result;
16. total source ANN query count is at most 21;
17. Facet-specific similarity remains raw same-Facet cosine with no fallback;
18. pre-cutover/no-pointer Phase-I similarity remains compatible;
19. active Phase-I v1 generation/rollback compatibility remains valid. Add a focused
    regression if this active-v1 path is not already explicitly covered; do not start
    R2-07 to perform this check.

## 7. Qdrant

If `qdrant-client` is installed, run the in-memory R2 smoke test and existing v1
Similarity/Hybrid Qdrant regressions.

Confirm R2 payload `generation_id` filtering and SQLite generation membership
verification agree.

No production Qdrant collection may be created, changed, dropped, or cut over.

## 8. Static checks

Run repository-standard Ruff / format / diff checks on all R2-06 changed files.

Known unrelated baseline:

```text
n05_resource_preflight.py:69 E501
```

Do not mix that unrelated fix into R2-06.

## 9. Compatibility review

Check:

- `KnowledgeReadApplication.find_similar_objects()` remains source-compatible;
- CLI and MCP callers do not need representation kind or generation arguments;
- MCP `find_similar_objects` output schema intentionally allows additive properties,
  so `evidence`, `source_membership_id`, and `generation_id` remain additive output;
- CLI/MCP dataclass serialization accepts the additive fields without dropping the
  established fields;
- additive similarity evidence serialization does not break exact-schema tests;
- old base result fields remain present;
- Facet-specific callers still see the existing raw cosine contract.

If exact serialized-output tests require updates solely because the new fields are
additive, update those expectations and document why.

## 10. Documentation after PASS

Only after all gates pass:

1. update `docs/design/OBJECT_SIMILARITY_SEARCH.md` with the R2-06 frozen algorithm
   and remove language saying the exact formula/caps are still pending;
2. update `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`:

```text
R2-06 = Complete
R2-07 = Next / Not Started
```

3. update the R2-06 implementation record from Runtime Verification Pending to
   Complete and record test/Qdrant/static evidence.

Do not start R2-07.

## 11. GitHub

If verification requires R2-06 fixes, commit only R2-06-scoped changes.

After PASS, commit documentation/test fixes and push GitHub `main`.

Final report must include:

```text
branch
final HEAD
working tree status
R1 asset hash preservation
changed files
focused pytest results and unique PASS count
Qdrant result
Ruff / format / diff result
active consumer bypass search result
algorithm constants unchanged or justified design-review return
new gold results
boundedness result
active-generation isolation result
object_overall exclusion result
payload mismatch result
one-operation/one-generation result
historical/current result
active-v1 generation compatibility result
Facet-specific regression result
Application/CLI/MCP compatibility result
commit SHA
push result
R2-06 final status
next = R2-07 [P0] — Derived Search rebuild / cutover / rollback (Not Started)
```
