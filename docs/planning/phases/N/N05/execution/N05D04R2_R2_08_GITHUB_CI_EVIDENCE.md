# N05D-04R2 / R2-08 — GitHub CI Supplementary Verification Evidence

Updated: 2026-10-23

Status: **Supplementary implementation/regression evidence only / Reference Workstation quality gate still pending**

This record captures the GitHub Actions checks run while the Reference Workstation command path was unavailable. It is not a substitute for the frozen Harrier OSS v1 0.6B quality run or the Windows/reference-workstation full regression required to complete R2-08.

## 1. Scope

Candidate branch:

```text
r2-08-search-quality
base main: 6c5120c7e34312486ca75a83805adb9065dec56e
```

The candidate diff after removing the temporary CI workflow contains only:

```text
benchmark/n05d04r2-object-similarity-gold-test-map-v1.json
benchmark/n05d04r2-search-quality-acceptance-v1.json
docs/evaluation/N05D04R2_SEARCH_QUALITY_ACCEPTANCE.md
docs/planning/phases/N/N05/execution/N05D04R2_R2_08_CODEX_VERIFICATION.md
scripts/run_n05d04r2_search_quality_acceptance.py
tests/test_n05d04r2_search_quality_acceptance.py
```

No N-04 frozen corpus, N-04 manifest, canonical Knowledge schema, production Search algorithm, or production data was changed by R2-08.

## 2. CI environment

```text
GitHub Actions hosted runner
OS: Ubuntu 24.04.5
Python: CPython 3.10.22
R2 candidate branch only
```

Installed test extras:

```text
.[dev,mcp,vector-qdrant]
```

Harrier / sentence-transformers was intentionally not installed for this supplementary CI. Therefore the frozen model quality harness was not run here.

## 3. Focused verification

Successful run:

```text
run_id: 39939820527
job_id: 120368209170
head: 417130ac746cacbe3304f75926793fafbed108b6
```

Results:

```text
compileall                         PASS
ruff check                        PASS
ruff format --check               PASS
focused R2-08 pytest              86 passed / 0 failed / 0 skipped
warnings                          2
```

The two warnings are local/in-memory Qdrant limitations:

- payload indexes have no effect in local Qdrant except supported text-index behavior;
- local Qdrant performs exact brute-force search so ANN search parameters have no effect.

These are expected test-backend warnings and not acceptance failures.

The focused suite covered:

```text
tests/test_n05d04r2_search_quality_acceptance.py
tests/test_hybrid_search_r2.py
tests/test_object_similarity_r2.py
tests/test_generation_lifecycle_r2.py
tests/test_generation_lifecycle_qdrant_r2.py
tests/test_object_overview_r2.py
tests/test_search_quality_gold.py
tests/test_j02_evidence_search.py
```

This gives executable evidence for the R2 Hybrid, hierarchical Similarity, generation isolation, object_overview, Qdrant local smoke, Phase-I gold contract, and Evidence Search regression surfaces.

## 4. Full pytest supplementary run

Run:

```text
run_id: 39940008886
job_id: 120368830992
head: 338f2f82a815d28396cbc2c441bc7d82b375cf51
```

Preceding checks:

```text
compileall                         PASS
ruff check                        PASS
ruff format --check               PASS
focused R2-08 pytest              86 passed / 0 failed / 0 skipped
```

Full pytest result:

```text
639 passed
2 failed
2 warnings
elapsed: 130.38 s
```

The only failures were:

```text
tests/test_n04g23ar_candidate_eval_contract.py::test_g23ar_preflight_passes_against_tracked_inputs
  RuntimeError: Frozen G-23A Gold corpus SHA mismatch

tests/test_n04g25a_development.py::test_frozen_corpus_counts_and_group_holdouts
  ValueError: Frozen development input hash mismatch
```

Both failures are exact-byte SHA checks for historical/experimental N-04 research corpora. None of the files involved in those checks are changed by the R2-08 diff. The same CI run passed all 639 other tests, including all R2-08 focused tests.

This record therefore classifies the two failures as **outside the R2-08 change surface and unsuitable for waiver of the Reference Workstation gate**. The most likely class is checkout-byte/hash-environment sensitivity, but this CI evidence alone does not prove the exact byte-normalization cause.

Required disposition:

- do not modify the frozen N-04 corpora or their expected hashes as part of R2-08;
- do not count the GitHub Actions full suite as a formal full-regression PASS;
- rerun full pytest on the Reference Workstation / normal Windows repository checkout;
- R2-08 completion still requires that local full regression to PASS or any pre-existing failure to be separately proven and dispositioned under its own authority.

## 5. What this CI proves

Supported by CI:

```text
R2-08 acceptance contract/test code imports and compiles
candidate code is Ruff-clean / formatter-clean in scoped files
focused R2 Search/Similarity/Generation/Evidence regression = 86/86 PASS
R2 similarity gold has executable test traceability
local Qdrant R2 smoke paths pass
no R2-08 focused regression failure observed
639 additional repository tests pass in Linux CI
```

Not proven by CI:

```text
Harrier OSS v1 0.6B frozen gold quality metrics
Reference Workstation CUDA/VRAM/resource observations
24 Object-query and 22 Statement-query metric acceptance
manual classification of any model-quality negative delta
Reference Workstation full pytest PASS
R1 user-aborted asset SHA preservation
production/reference DB invariance during the R2-08 run
```

## 6. Remaining R2-08 completion work

On the Reference Workstation, follow:

`docs/planning/phases/N/N05/execution/N05D04R2_R2_08_CODEX_VERIFICATION.md`

At minimum complete:

```text
1. original workspace status/diff + three R1 asset SHA-256 pre-check
2. clean worktree from the current R2-08 candidate
3. focused regression (expected to remain PASS)
4. python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only
5. inspect automatic gate and every negative metric delta
6. confirm 24 Object / 22 Statement / 5 contract / 4 Phase-I Similarity / 6 R2 Similarity / 3 Evidence cases
7. record latency/resource observations with frozen Harrier 0.6B
8. full pytest on the normal Windows/reference checkout
9. Ruff/format/diff
10. R1 asset SHA-256 post-check
11. only after all gates PASS, merge candidate to main and mark R2-08 Complete
```

R2-09 remains **Not Started** until that gate passes.
