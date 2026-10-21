# N-04 Post-G22 Two-Stage Remediation — Historical Record

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Historical trigger: `N-04G-22` valid formal FAIL (`0 / 3 Case PASS`)
- Historical scope: G-23〜G-27 two-stage Grounded Generation remediation
- Current status: **Historical / Superseded as N-04 completion path**
- Superseding decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`

## 1. Historical chain

```text
G-22 valid formal FAIL
  ↓
G-23 Two-stage architecture decision
  ↓
G-23A-E responsibility decomposition
  ↓
G-23B Stage 1 contract
  ↓
G-23C Certification / Certified Content
  ↓
G-23D Stage 2 contract
  ↓
G-23E Provider schema / retry
  ↓
G-23F v4 Design Freeze
  ↓
G-24 v4 implementation
  ↓
G-25A Residual Classifier Benchmark
       VALID_FAIL_NO_SELECTION
```

G-25B / G-26 / G-27 were blocked by the historical classifier-selection path and are no longer required for current N-04 completion.

## 2. Historical task state

| Task | Historical state |
|---|---|
| N-04G-23 | Complete / Architecture Accepted |
| N-04G-23A-E | Complete / Architecture Accepted |
| N-04G-23B | Complete / Contract Accepted |
| N-04G-23C | Complete / Contract Accepted |
| N-04G-23D | Complete / Contract Accepted |
| N-04G-23E | Complete / Contract Accepted |
| N-04G-23F | Complete / v4 Design Frozen |
| N-04G-24 | Complete |
| N-04G-25A | VALID_FAIL_NO_SELECTION |
| N-04G-25B | Historical blocked / not required now |
| N-04G-26 | Historical blocked / not required now |
| N-04G-27 | Historical blocked / not required now |

## 3. Why the chain is superseded

このchainは、Consumer-generated textをSGOKB自身が検証・certifyしなければN-04をCompleteにできないという旧前提に基づいていた。

2026-10-22のResponsibility Boundary Reconstructionで、formal N-04は次までに限定された。

```text
SGOKB
  ↓
Retrieval / Similarity
  ↓
Context Builder
  ↓
MCP / public read boundary
  ↓
External Consumer boundary  ← formal N-04 ends here
```

したがってv4 Grounded Generation / classifier / certificationはcurrent N-04の必須経路ではない。

## 4. v4 assets remain preserved

次を削除しない。

- v4 Decision documents
- G-24 implementation code
- G-24 tests
- development classifier corpora
- benchmark results
- Frozen 47 assets
- G-25A manifests / selection evidence

N-04R-05で将来処遇を決める。

## 5. Current N-04 path

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Active
N-04R-03 Formal Harness Reconstruction           Pending
N-04R-04 Reference Workstation Re-Acceptance     Pending
N-04R-05 Grounded Generation Asset Disposition   Pending
```

Current authority:

- `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`

## 6. Constraints

- G-25A classifier selectionをN-04のために再開しない。
- G-25B / G-26 / G-27をN-04のために実施しない。
- Frozen 47をcurrent N-04 acceptanceのために実行しない。
- historical v4 Gatesを緩和・変更して見かけのPASSを作らない。
- historical resultsを削除・上書きしない。
