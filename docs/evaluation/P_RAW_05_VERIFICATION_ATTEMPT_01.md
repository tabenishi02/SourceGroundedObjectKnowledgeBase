# P-RAW-05 — Automated Verification Attempt 01

Updated: 2026-10-30

- Task: `P-RAW-05 [P0] RAW Grounding implementation`
- Execution source: `main` at `adffdd0503494b0ea2046ee157636cfac2016321`
- Disposition: **FAIL / remediation required**
- P-RAW-06: **Blocked**

## Gate executed

The operator executed the required gate in order:

1. focused P-RAW/v1 exchange regression;
2. `ruff check src tests`;
3. full `pytest` regression.

Observed results:

```text
focused: 91 collected / 55 passed / 36 failed
Ruff:    20 E501 errors
full:    827 collected / 700 passed / 102 failed / 25 errors / 2 warnings
```

The two warnings are the previously known local-Qdrant warnings and are not the cause of this failure.

## Root-cause classes

### R1 — SourceRepository retrieval contract regression

The dominant failure is not a Raw-grounding semantic failure. Existing retrieval callers still require the accepted F-03/J-02 SourceRepository contract, but the current exported repository no longer provides:

- `metadata_matching_sources()`;
- `evidence_context()`.

In addition, the current `lexical_evidence_rows()` retained the query parameter but no longer used the FTS `MATCH ?` predicate. This caused both:

- `AttributeError` across Package/Result/review/recovery tests; and
- SQLite parameter-count errors in lexical Evidence search.

It also changed retrieval semantics by returning effective Evidence independently of the lexical query.

Remediation rule: restore the accepted retrieval contract without removing the P-RAW additions (`raw_artifact_by_id`, `normalization_input_raw_artifacts`, and other later Source APIs).

### R2 — Migration 019 expectation drift

P-RAW-05 intentionally adds `019_raw_grounding_v2.sql`. Several older tests still freeze migration version/count expectations at Migration 018.

Those assertions must be updated to the additive Migration 019 baseline. The implementation must not hide or renumber Migration 019 merely to satisfy stale tests.

Expected canonical baseline after P-RAW-05:

```text
latest migration version = 19
versions                  = 3..19 inclusive
migration row count       = 17
```

### R3 — Ruff E501 in new P-RAW files

The first implementation introduced 20 line-length violations in new v2 exchange files. These are verification failures and must be resolved or narrowly scoped where preserving exact instruction text is intentional.

### R4 — Secondary failures

CLI, GUI, benchmark, recovery, review, and Package/Result failures that terminate through R1 are treated as cascading failures until R1 is repaired and the suites are rerun. They are not independently waived.

Any failures remaining after R1–R3 remediation become new independent P-RAW-05 defects and must be fixed before acceptance.

## Remediation branch

Verification remediation is isolated on:

```text
p-raw-05-verification-remediation
```

Initial remediation restores the accepted Source retrieval surface through an exported SourceRepository extension while retaining the current canonical Source/Raw APIs.

## Acceptance rule

P-RAW-05 remains:

```text
Implementation Complete / Automated Verification FAILED / Remediation In Progress
```

It may become `Complete / Accepted` only after a fresh execution of all three gates returns PASS:

```text
focused regression = PASS
Ruff              = PASS
full regression   = PASS
```

No failure from Attempt 01 is waived into P-RAW-06.
