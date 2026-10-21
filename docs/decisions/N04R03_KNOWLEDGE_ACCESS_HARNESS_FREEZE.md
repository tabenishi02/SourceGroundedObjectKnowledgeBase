# N-04R-03 Knowledge Access Harness Freeze

更新日: 2026-10-22

- Task: `N-04R-03 — Harness Reconstruction`
- Parent: `N-04 [P0]`
- Status: **Complete / Harness Frozen for N-04R-04**
- Parent Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Current acceptance: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`

## 1. Decision

N-04 formal harnessを、SGOKBの**Knowledge Access Boundaryだけを判定するHarness**として再構築し、N-04R-04 Reference Workstation re-acceptance用にfreezeする。

現行Harness:

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
tests/test_n04r03_knowledge_access_harness.py
```

旧v2/v3 Grounded Generation harnessはhistorical evidenceとして保持するが、current authorityではない。

## 2. Formal boundary

```text
SGOKB canonical / derived data
  ↓
Retrieval / Similarity
  ↓
Context Builder
  ↓
MCP / public read surface
  ↓
External Consumer boundary  ← formal harness ends here
```

Consumer側のLLM推論・生成・grounding遵守は判定しない。

## 3. Formal case gates

各ケースで必要なGate:

```text
public_boundary
canonical_scope
context_contract
traceability
budget_contract
```

Case 2のみ追加:

```text
retrieval_integration
```

意味:

- `public_boundary`: direct SQLiteでConsumer入力を作らず、正式MCP/Application read pathを使用する。
- `canonical_scope`: intended Object / current accepted Versionだけを使用する。
- `context_contract`: `sgokb.context-builder.v1`に従いpurpose / object / version / metadataが正しい。
- `retrieval_integration`: Similarity結果から得たcurrent Work candidateをContextへ接続する。
- `traceability`: Object / resolved Version /必要なEvidence referenceを追跡できる。
- `budget_contract`: `used_characters <= limit_characters`、omission / truncation metadataを保持し、partial statement truncationを行わない。

## 4. Global gates

3ケース共通で次を要求する。

```text
canonical_invariance
integrity
regression
```

- formal runはread-only。
- before / afterでcanonical Object / Version / Knowledge / Source / Evidence / Provenanceを変更しない。
- `system integrity`をPASSする。
- focused tests / full pytestを0 failureで完了する。

## 5. Explicitly removed from formal harness

次はN-04 formal Gateではない。

```text
local LLM generation
consumer output grounding
Atomicity classifier
Content-Type classifier
Source Fact verifier
Interpretation verifier
Grounded Generation certification
Certified Content
Presentation Generator
Frozen 47 confirmation
```

Reference Consumer Demonstrationを行うことは許容するが、専用`reference-consumer/` evidenceへ分離し、formal verdictへ影響させない。

## 6. Frozen representative cases

### Case 1

```text
Saber
326a97cf-47aa-4760-a7f1-07bfe639fcf0
purpose=roleplay
max_characters=12000
```

### Case 2

```text
source = Fate/stay night
d5824d33-7008-4121-9cfe-1f95a19667fd

find_similar_objects
  cross_class=false
  include_archived=false
  limit=5

source + highest-ranked returned current Work candidate
  -> build_context purpose=comparison
  -> max_characters=24000
```

N-03固定datasetでBLEACHが返ることはobservationとして記録できるが、候補をhardcodeしてSimilarity pathを迂回してはならない。

### Case 3

```text
Tsundere
8c83f986-f491-41a8-8645-9f71dd5874b9

Hero's Journey
fee32007-0f92-449a-ba21-4ec2f78d1cd4

purpose=creative
max_characters=24000
```

## 7. Evidence contract

正式run root:

```text
.local/n04r04/<run_id>/
```

最低限保存:

```text
environment.json
mcp-tools.json
case-1-roleplay/request.json
case-1-roleplay/context.json
case-1-roleplay/evaluation.json
case-2-comparison/similarity-request.json
case-2-comparison/similarity.json
case-2-comparison/context-request.json
case-2-comparison/context.json
case-2-comparison/evaluation.json
case-3-creative/request.json
case-3-creative/context.json
case-3-creative/evaluation.json
canonical-before.json
canonical-after.json
integrity.json
focused-pytest.log
full-pytest.log
overall-evaluation.json
```

Consumer demonstrationを行う場合:

```text
reference-consumer/
```

へ分離する。

## 8. Preflight

N-04R-04開始前に次をすべてPASSさせる。

```powershell
python benchmark/tools/n04r03_harness_preflight.py
python -m pytest -q tests/test_n04r03_knowledge_access_harness.py tests/test_j04_context_builder.py tests/test_j06_mcp_client_acceptance.py
python -m pytest -q
python -m ruff check .
git diff --check
```

R-03ではReference Workstation formal run自体は行わない。実機preflightと3ケース実行はN-04R-04の責務とする。

## 9. Result semantics

正式状態:

```text
PASS
FAIL
BLOCKED
```

- PASS: 全case required Gate + global GateがPASS。
- FAIL: SGOKB自身のKnowledge Access responsibilityにdefectがある。
- BLOCKED: 必要runtimeが利用不能でformal Gateを評価できない。

Consumer AIの出力失敗を`FAIL`へ変換してはならない。

## 10. Historical authority separation

Historical only:

```text
benchmark/n04-v2-formal-harness-v1.json
benchmark/n04-v3-formal-harness-v1.json
G-12 / G-22 formal generation-quality runs
G-23〜G-25 verifier/classifier research
```

Current authority:

```text
docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md
docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md
docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
```

## 11. Completion decision

N-04R-03 deliverablesを満たした。

```text
machine-readable case spec        created
formal harness                    created
preflight                         created
focused regression test           created
evidence directory contract       frozen
historical/current separation      explicit
consumer generation dependency     removed
```

**N-04R-03 = Complete.**

Next:

`N-04R-04 — Reference Workstation Re-Acceptance`
