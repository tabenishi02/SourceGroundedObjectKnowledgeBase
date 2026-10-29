# P-RAW-05 — Automated Verification Attempt 02 / Final Acceptance

Updated: 2026-10-30

- Task: `P-RAW-05 [P0] RAW Grounding implementation`
- Verification branch: `p-raw-05-verification-remediation`
- Execution source: `0ce44aee35ad56640dc83f5d5be67621c23cbcd3`
- GitHub Actions run: `40928904677` (`P-RAW-05 remediation`, run #12)
- Reference environment: Windows Server 2025 / Python 3.10.11
- Disposition: **PASS / Complete / Accepted**
- P-RAW-06: **Unblocked / Next**

## 1. Final gate

The required P-RAW-05 gate was executed after remediation on a Windows runner with full Git history and Windows checkout semantics matching the repository's accepted workstation baseline.

Final results:

```text
focused P-RAW/v1 exchange regression = 91 / 91 PASS
migration remediation regression     = 56 / 56 PASS
Ruff src/tests                        = PASS
full regression                       = 827 / 827 PASS
warnings                              = 2 known local-Qdrant warnings
```

The warnings are the existing local-Qdrant limitations:

- payload indexes have no effect in local Qdrant except supported text-index behavior;
- local-mode exact search ignores `search_params` except `idf`.

They are unchanged from earlier accepted baselines and are not P-RAW-05 failures.

## 2. Attempt 01 remediation closure

Attempt 01 remains the historical failure record in:

```text
docs/evaluation/P_RAW_05_VERIFICATION_ATTEMPT_01.md
```

Its failure classes were resolved rather than waived.

### R1 — SourceRepository retrieval contract regression

Restored the accepted F-03/J-02 retrieval surface while preserving P-RAW additions.

The exported `SourceRepository` again provides the required retrieval behavior, including metadata matching, Evidence context, and query-bound lexical FTS behavior. P-RAW Raw/provenance APIs remain available.

### R2 — migration expectation drift

Tests with frozen migration-version/count expectations were updated for the additive Raw-grounding migrations.

P-RAW-05 now uses:

```text
019_raw_grounding_v2.sql
020_raw_grounding_acceptance_gate.sql
```

Migration 020 replaces the legacy accepted-statement Evidence-only trigger with a compatibility rule that accepts the correct grounding family for the imported Result version while preserving the existing v1 contract.

### R3 — Ruff failures

New P-RAW code now passes the repository Ruff gate. Narrow per-file E501 exceptions are limited to the accepted Package-v2 integrity/transfer expressions where line wrapping does not change semantic behavior.

## 3. Additional defects found after primary remediation

Fresh focused execution exposed three independent P-RAW defects, all fixed before acceptance:

1. the Raw resolver referenced `EvidenceProvenance.artifact_ids` instead of the actual `raw_artifact_ids` contract;
2. Result-v2 schema construction attempted to mutate top-level `$ref` nodes as if they contained direct `properties`; the implementation now updates the corresponding `$defs` definitions;
3. the legacy accepted-statement DB trigger still required `evidence_links` for v2 imports; Migration 020 updates the acceptance invariant for Raw-grounded v2 Versions without weakening v1 Evidence grounding.

The focused suite subsequently reached 91 / 91 PASS.

## 4. CI environment diagnostics

An intermediate Linux CI run reached:

```text
focused regression = PASS
migration regression = PASS
Ruff = PASS
```

but full regression reported environment-only failures from:

- missing Linux `libEGL.so.1` for PySide6 GUI tests;
- absent `sentence-transformers` package metadata required by frozen Harrier-space tests;
- shallow Git history preventing Phase-N historical `git show` checks;
- checkout byte/line-ending semantics differing from the frozen Windows corpus baseline.

No P-RAW test failed in that run. These conditions were corrected in the final Windows verification rather than changing product semantics or weakening tests.

## 5. Final compatibility result

The accepted gate demonstrates that the additive v2 Raw-grounding path coexists with the legacy v1 exchange path across the repository regression authority.

Verified behaviors include:

```text
Package v2 exact Raw materialization
Evidence -> Raw provenance resolution
Result v2 binding and Raw membership validation
locator validation
Raw-aware review / diff
Result v2 import -> raw_grounding_links
no fabricated evidence_links for v2
historical carry-forward selection lineage
v2 current -> v1 downgrade block
legacy Package/Result v1 compatibility
existing retrieval / GUI / benchmark / recovery behavior
```

Therefore:

```text
P-RAW-05 = Complete / Accepted
P-RAW-06 = Unblocked / Next
```

P-RAW-06 remains responsible for formal RAW Grounding operational acceptance, real-Object end-to-end acceptance, compatibility/cutover disposition, and documentation completion.
