# N05D-04R2 / R2-08 — Local Search-quality verification handoff

Updated: 2026-10-23

Status: **Ready for local verification / R2-08 not Complete**

This handoff completes the local-only portion of R2-08 after the acceptance contract/harness is prepared in branch `r2-08-search-quality`.

Do not start R2-09.

## 1. Safety first

The original workspace contains three R1 user-aborted assets that must be preserved.

Before any checkout/pull/reset/clean operation in the original workspace:

```powershell
git status --short --branch
git diff --stat
git diff --cached --stat
git rev-parse HEAD
```

Record the exact three R1 paths and SHA-256 values. Do not modify, stage, delete, reset, clean, or overwrite them.

Prefer a clean verification worktree/clone for this task. Never use `git reset --hard` or `git clean` against the original workspace.

Record free disk and the current active R2 generation before testing. The reference production DB must not be used as the synthetic gold harness DB.

## 2. Git authority

At preparation time:

```text
base main HEAD: 6c5120c7e34312486ca75a83805adb9065dec56e
candidate branch: r2-08-search-quality
```

Fetch the current branch head from origin before starting because this handoff document itself may be followed by additional candidate commits.

Verify branch diff contains only R2-08 acceptance assets/docs and no accidental production algorithm change.

## 3. Read first

Review:

```text
docs/evaluation/N05D04R2_SEARCH_QUALITY_ACCEPTANCE.md
benchmark/n05d04r2-search-quality-acceptance-v1.json
scripts/run_n05d04r2_search_quality_acceptance.py
tests/test_n05d04r2_search_quality_acceptance.py
benchmark/search-quality-gold-v1.json
benchmark/n05d04r2-object-similarity-gold-v1.json
docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md
docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_OBJECT_SIMILARITY.md
```

Confirm the candidate harness does not mutate the reference DB/Qdrant namespace and creates only `.local/n05d04r2-search-quality.sqlite` plus result evidence.

## 4. Static / syntax review

Run from the clean verification worktree:

```powershell
python -m compileall `
  scripts/run_n05d04r2_search_quality_acceptance.py `
  tests/test_n05d04r2_search_quality_acceptance.py

python -m ruff check `
  scripts/run_n05d04r2_search_quality_acceptance.py `
  tests/test_n05d04r2_search_quality_acceptance.py

python -m black --check `
  scripts/run_n05d04r2_search_quality_acceptance.py `
  tests/test_n05d04r2_search_quality_acceptance.py
```

Use the repository's actual formatting command if Black is not the configured formatter. Fix candidate-owned issues. Do not expand scope to the known unrelated `n05_resource_preflight.py:69 E501`.

Review specifically:

- fresh DB migration 018 behavior;
- synthetic R2 generation creation;
- R2 generation membership completeness;
- Harrier revision/dimension assertion;
- no embedding of legacy `object_overall` in the acceptance run;
- Exact Vector generation payload;
- R2 Hybrid/Similarity generation resolution;
- baseline metric paths and comparison semantics;
- output/result JSON determinism where expected.

## 5. Focused contract suite

Run:

```powershell
python -m pytest `
  tests/test_n05d04r2_search_quality_acceptance.py `
  tests/test_hybrid_search_r2.py `
  tests/test_object_similarity_r2.py `
  tests/test_generation_lifecycle_r2.py `
  tests/test_generation_lifecycle_qdrant_r2.py `
  tests/test_object_overview_r2.py `
  tests/test_search_quality_gold.py `
  tests/test_j02_evidence_search.py -q
```

All must PASS. Skips must be explained; do not count a skipped Qdrant test as runtime evidence if the dependency is expected on the reference workstation.

The six R2 similarity gold IDs must be traceable to passing regression cases:

```text
R2SIM-G01 detail_facet_breaks_overview_tie
R2SIM-G02 small_statement_evidence_breaks_overview_and_facet_tie
R2SIM-G03 large_irrelevant_statement_count_has_no_volume_boost
R2SIM-G04 canonical_facet_boundary_is_hard
R2SIM-G05 generation_and_current_version_isolation
R2SIM-G06 bounded_work_contract
```

If current tests do not make that traceability explicit enough, add a small machine-readable mapping/test. Do not create a second competing semantic gold.

## 6. Frozen Harrier quality run

Use the already cached frozen model, no downloads/fallback/model substitution:

```powershell
python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only
```

Expected output:

```text
.local/n05d04r2-search-quality-result.json
```

Required runtime identity:

```text
model    microsoft/harrier-oss-v1-0.6b
revision f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dim      1024
family   object_overview + facet + statement
```

Do not enable Harrier 270M, truncation, FlashAttention-2, PyTorch/CUDA changes, or CPU fallback changes during this acceptance.

## 7. Result review

The automatic gate must PASS.

Record at minimum:

- R2 representation counts and vector point count;
- generation ID / membership digest / source catalog digest;
- Object Semantic metrics;
- Hybrid metrics;
- exact identity accuracy;
- Statement semantic metrics;
- 5 contract case results;
- existing 4 Similarity case results split overall/facet;
- 3 Evidence Search cases for lexical/association and semantic paths;
- `object_overall_leakage = false`;
- one Object = one result;
- single generation payload;
- benchmark wall-clock;
- available Torch CUDA max allocated/reserved observation.

For every item under `baseline_evaluation.review_on_negative_delta` with `requires_review=true`, inspect case-level result IDs and classify:

```text
INTENDED_R2_CHANGE
NEUTRAL_NOT_MATERIAL
UNINTENDED_REGRESSION
```

Do not invent a tolerance after seeing results. Any unexplained negative metric delta blocks acceptance. Overall Similarity may differ because its semantics intentionally changed, but the difference must be consistent with the R2-06 frozen contract and all six hierarchical similarity cases must PASS.

## 8. Native Qdrant semantic smoke

R2-07 already accepted native generation cutover. R2-08 should add a quality-oriented smoke against an isolated/in-memory or disposable native Qdrant namespace using the R2 gold fixture if practical:

- generation payload hard filter;
- `object_overall` absent;
- Hybrid top results agree with Exact reference on the critical identity/Facet cases;
- Facet Similarity remains same-Facet;
- no v1/v2 mixing.

Do not rebuild or overwrite the active production namespace for this quality smoke.

## 9. Regression and hygiene

After focused/gold acceptance:

```powershell
python -m pytest -q
```

Run repository-scoped Ruff/format/diff checks consistent with R2-07. The known unrelated `n05_resource_preflight.py:69 E501` may remain only if unchanged from the accepted baseline.

Recheck:

```powershell
git status --short --branch
git diff --check
```

Re-hash the three R1 assets in the original workspace and prove byte-for-byte equality with the initial values.

## 10. N-06 interaction

Confirm:

- `PHASE_N_PREPARATION.md` still treats N-06 as Ready;
- R2-08 reuses the Phase-I frozen Search gold as the current N-06 Search-quality authority;
- no separate committed N06 execution result is being silently treated as authoritative;
- N-06 must later run with active R2 Retrieval semantics;
- R2-08 does not close N-06.

Do not execute N-06 closure work in this task.

## 11. Completion decision

R2-08 may be marked Complete only if:

```text
focused R2/search/evidence suite        PASS
frozen Harrier gold harness             automatic PASS
negative comparable deltas              all explained / no material regression
R2SIM-G01..G06                           6/6 PASS
filter/current-history/temporal          PASS
Facet Similarity                         PASS
Evidence Search                           PASS
single active generation                 PASS
object_overall leakage                    0
full regression                           PASS
Ruff/format/diff                          PASS
R1 assets                                 SHA-256 unchanged
N-06 impact                               documented
```

If PASS:

1. Update `docs/evaluation/N05D04R2_SEARCH_QUALITY_ACCEPTANCE.md` with exact measured results and evidence.
2. Update `docs/planning/phases/N/N05/N05D04R2_HIERARCHICAL_MULTI_VECTOR_TASKS.md`:
   - R2-08 = Complete
   - R2-09 = Next / Not Started
   - keep N05D-04R2 Active
   - keep N05D-04 / N-05 BLOCKED / Not Complete
   - performance target Not Judgeable
3. Update `docs/planning/phases/N/PHASE_N_PREPARATION.md` only where current-next/status text is stale; do not mark N-05 Complete.
4. Commit candidate changes, fast-forward/merge safely to `main`, push, and prove local main == origin/main and clean verification worktree.
5. Do **not** start R2-09.

If quality fails:

- do not merge a false Complete state;
- mark R2-08 FAIL/BLOCKED with exact failing cases;
- classify root cause as R2-05 Hybrid or R2-06 Similarity where possible;
- do not change embedding model as a workaround;
- stop before R2-09.

## 12. Final report

Return:

```text
final HEAD / branch / clean status
R1 paths + before/after SHA-256
changed files
focused pytest PASS/FAIL/skip
full pytest PASS/FAIL/skip
Harrier model/revision/dimension
R2 representation/vector counts
Hybrid metrics and Phase-I deltas
Semantic metrics and deltas
Statement metrics and deltas
Similarity overall/facet metrics and deltas
R2SIM-G01..G06 result
contract 5/5 result
Evidence Search result
object_overall leakage
generation isolation
latency/resource observations
negative-delta classification
N-06 impact decision
Ruff/format/diff result
commit/push/main integration
R2-08 final status
next task
```
