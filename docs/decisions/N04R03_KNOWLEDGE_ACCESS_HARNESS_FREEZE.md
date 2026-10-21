# N-04R-03 Knowledge Access Harness Freeze

更新日: 2026-10-22

- Task: `N-04R-03 — Harness Reconstruction`
- Parent: `N-04 [P0]`
- Status: **Complete / Harness Frozen for N-04R-04**
- Parent Decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Current acceptance: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`

## 1. Decision

N-04 formal harnessを、SGOKBの**Knowledge Access Boundaryだけを判定するHarness**として再構築し、N-04R-04 Reference Workstation re-acceptance用にfreezeする。

現行Harness資産:

```text
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
tests/test_n04r03_knowledge_access_harness.py
tests/test_n04r04_evidence_evaluator.py
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
- `context_contract`: `sgokb.context-builder.v1`に従いpurpose / Object / Version / include optionが正しい。
- `retrieval_integration`: Similarity結果から得たtop current Work candidateを、そのIDのままContextへ接続する。
- `traceability`: Object / resolved Version /必要なEvidence referenceを追跡できる。
- `budget_contract`: `used_characters <= limit_characters`、omission / truncation metadataを保持し、partial statement truncationを行わない。

`include_evidence_refs=true`のCase 2では、Context内に公開Evidence referenceが実際に残ることもdeterministic evaluatorで確認する。`false`のCase 1/3ではEvidence referenceがConsumer Contextへ残らないことを確認する。

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
- focused tests / full pytest / Ruff / `git diff --check`を成功させる。

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
include_attributes=true
include_relations=true
include_evidence_refs=false
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
  -> include_attributes=true
  -> include_relations=false
  -> include_evidence_refs=true
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
include_attributes=true
include_relations=true
include_evidence_refs=false
```

## 7. Machine-readable freeze binding

`benchmark/n04-knowledge-access-formal-harness-v1.json`は、current case specとformal evaluatorをGit blob SHAで固定する。

```text
case spec:
  benchmark/n04-knowledge-access-cases-v1.json
  ab3374508467575955f0f9da911f551178a93b6e

formal evaluator:
  benchmark/tools/n04r04_evaluate_evidence.py
  b960845477e384d06bc925564c92f20564ab62de
```

`n04r03_harness_preflight.py`はこのbindingと、現行MCP / Context Builder contract version、代表3ケース、formal Gate集合、historical/current authority分離を検査する。

## 8. Deterministic formal evaluator

`benchmark/tools/n04r04_evaluate_evidence.py`はR-04で保存されたraw MCP evidenceのみからformal verdictを作る。

評価内容:

- requestがpublic Toolである。
- requestのObject / purpose / budget / include optionがfreeze値と一致する。
- MCP / Context Builder contract versionが一致する。
- Object ID / resolved Version / `is_current`が正しい。
- Context Builder selection policyが要求optionと一致する。
- budget / omission / truncation semanticsが正しい。
- Case 2のContext candidate IDが実Similarity top resultと一致する。
- Evidence referenceのinclude / omit policyが一致する。
- canonical before / afterが一致する。
- integrity / regression resultがPASSする。

必要なformal evidenceが不足・読取不能で判定できない場合は`BLOCKED`とし、SGOKB defectを意味する`FAIL`と混同しない。

Consumer outputは読み込まず、formal verdictへ影響させない。

## 9. Evidence contract

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
regression.json
focused-pytest.log
full-pytest.log
overall-evaluation.json
```

Consumer demonstrationを行う場合:

```text
reference-consumer/
```

へ分離する。

## 10. Preflight

N-04R-04開始前に次をすべてPASSさせる。

```powershell
python benchmark/tools/n04r03_harness_preflight.py
python -m pytest -q tests/test_n04r03_knowledge_access_harness.py tests/test_n04r04_evidence_evaluator.py tests/test_j04_context_builder.py tests/test_j06_mcp_client_acceptance.py
python -m pytest -q
python -m ruff check .
git diff --check
```

R-03ではReference Workstation formal run自体は行わない。実機preflightと3ケース実行はN-04R-04の責務とする。

## 11. Result semantics

正式状態:

```text
PASS
FAIL
BLOCKED
```

- PASS: 全case required Gate + global GateがPASS。
- FAIL: SGOKB自身のKnowledge Access responsibilityにdefectがある。
- BLOCKED: 必要runtime/evidenceが利用不能でformal Gateを評価できない。

Consumer AIの出力失敗を`FAIL`へ変換してはならない。

## 12. Historical authority separation

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
benchmark/tools/n04r04_evaluate_evidence.py
```

## 13. Completion decision

N-04R-03 deliverablesを満たした。

```text
machine-readable case spec          created / frozen
formal harness                      created / frozen
static preflight                    created
formal evidence evaluator           created
focused regression tests            created
evidence directory contract         frozen
R-04 execution handoff              created
historical/current separation       explicit
consumer generation dependency      removed
```

Reference Workstationでのpreflight / formal 3-case executionはR-04へ意図的に分離した。

**N-04R-03 = Complete.**

Next:

`N-04R-04 — Reference Workstation Re-Acceptance`
