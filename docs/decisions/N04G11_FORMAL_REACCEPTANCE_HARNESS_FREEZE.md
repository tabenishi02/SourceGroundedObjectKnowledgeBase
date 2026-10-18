# N-04G-11 Formal Re-Acceptance Harness / Evidence Freeze

更新日: 2026-10-18

- Status: **Accepted / Harness Frozen**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Task: `N-04G-11 [P0] formal re-acceptance harness / evidence手順をfreezeする`
- Design Freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Acceptance Freeze: `docs/decisions/N04G08_N04_V2_ACCEPTANCE_SPEC_FREEZE.md`
- Machine acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Frozen harness manifest: `benchmark/n04-v2-formal-harness-v1.json`
- Implementation: `docs/design/N04G09_GROUNDED_GENERATION_IMPLEMENTATION.md`
- Regression: `docs/evaluation/N04G10_GROUNDED_GENERATION_REGRESSION.md`

---

## 1. Decision

N-04 v2 formal re-acceptanceで使用するReference Workstation harness、actual local model、runtime、generation/validation設定、実行順序、evidence path、preflight、canonical safety、regression procedureを本書と`benchmark/n04-v2-formal-harness-v1.json`でFreezeする。

G-12では本書の値を結果に合わせて変更してはならない。

変更が必要になった場合:

1. formal runを停止する。
2. 既存evidenceを削除しない。
3. harness値の変更ならG-11を明示的にreopenする。
4. rubric / retry semantics / grounded-generation semanticsへ影響する場合はG-08 / G-07まで必要範囲でreopenする。
5. 再Freeze後に別runとして開始する。

---

## 2. G-08 generation-settings wording clarification

G-11照合で、G-08本文 / v2 machine specの一部説明に次の曖昧さを確認した。

```text
same generation settings for all three cases
```

一方、Frozen v2 benchmarkの各caseには既に異なる数値が固定されている。

```text
Case 1: temperature=0.2 / max_tokens=700
Case 2: temperature=0.0 / max_tokens=900
Case 3: temperature=0.2 / max_tokens=1100
```

ここではG-07 / G-06の本来のretry invariantを正本とし、次のように解釈を固定する。

- **generator model / runtime / endpoint / quantization / context load profileは3 case共通で固定する。**
- **temperature / max_tokensはv2 benchmarkに記載されたcase別Frozen値を使用する。**
- **同一caseのAttempt 1とAttempt 2ではtemperature / max_tokensを含むgeneration settingsを完全一致させる。**
- caseの結果を見てad-hocにparameterを変更することは禁止する。

これはrubric、retry回数、failure semantics、case inputの変更ではない。G-07はretry前後のgeneration settings固定を要求しており、3 caseのtemperature/max_tokens同一化は要求していないため、G-07 Design Freezeはreopenしない。

Freeze history preservationのためG-08 original本文は直接書き換えず、binding clarification `docs/decisions/N04G08_G11_GENERATION_SETTINGS_CLARIFICATION.md` を追加し、G-12では本clarificationを併読する。

---

## 3. Reference Workstation / evaluation data

Freeze:

```text
OS: Windows 11
Python: 3.10.6
GPU: NVIDIA RTX 4090 24GB
Evaluation DB: .local/n03/sgokb-n03.sqlite
Source dataset: benchmark/n03-real-data-vertical-slice-v1.json
Acceptance spec: benchmark/n04-ai-use-cases-v2.json
Evidence root: .local/n04-v2/runs/<run_id>/
run_id: YYYYMMDDTHHMMSS+0900
```

Production DBは使用しない。

Formal run開始後、source / test / benchmark / Decision文書を変更しない。`git-start.json`と`git-end.json`のHEADは一致しなければならない。

---

## 4. Semantic retrieval runtime

N-03 / N-04 v1で使用したprofileを再利用する。

```text
Embedding model: microsoft/harrier-oss-v1-0.6b
Revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Dimensions: 1024
local_files_only: true
Qdrant: 1.19.2
HTTP: http://localhost:6333
gRPC: 6334
prefer_grpc: true
collection prefix: sgokb_n03_eval
```

Frozen MCP environment:

```text
SGOKB_DB=.local/n03/sgokb-n03.sqlite
SGOKB_MODEL_CACHE=.local/models
SGOKB_MODEL_LOCAL_ONLY=1
SGOKB_QDRANT_URL=http://localhost:6333
SGOKB_QDRANT_GRPC_PORT=6334
SGOKB_QDRANT_PREFER_GRPC=1
SGOKB_QDRANT_COLLECTION_PREFIX=sgokb_n03_eval
```

MCP server:

```text
python -m sgokb mcp serve --semantic-runtime
```

Transport / SDK:

```text
MCP Python SDK 2.3.0
protocol 2026-07-28
stdio
```

AI inputはMCP public read boundaryから取得する。ConsumerがSQLiteを直接queryしてKnowledge入力を構成することは禁止する。

---

## 5. Frozen generator

v1最終3 caseで使用済みのlocal modelを再利用する。

```text
Runtime: LM Studio 0.4.25.0
Endpoint: http://127.0.0.1:1234/v1
Identifier: sgokb-n04-mistral32
Model file:
  lmstudio-community/Mistral-Small-3.2-24B-Instruct-2506-GGUF/
  Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf
Quantization: Q4_K_M
Context length: 8192
GPU offload: max
Parallel: 1
Seed: 20261018
stream: false
```

### Structured output

Formal pathではLM Studio OpenAI-compatible `/v1/chat/completions`の`response_format=json_schema`を使用し、G-09の`GENERATION_OUTPUT_SCHEMA`をstrict schemaとして渡す。

Schema name:

```text
sgokb_grounded_generation_output_v1
```

Modelへ渡すmessageは:

```text
GroundedGenerationRequestBuilder.to_prompt_text(request)
```

を**sole user message**とする。

case固有のsystem prompt、hidden answer、外部fact、Web内容を追加しない。

### Case-specific inference parameters

```text
Case 1 roleplay:   temperature=0.2 / max_tokens=700
Case 2 comparison: temperature=0.0 / max_tokens=900
Case 3 creative:   temperature=0.2 / max_tokens=1100
```

これらはv2 benchmarkのFrozen値である。

Attempt 2では同一caseのAttempt 1と完全一致させる。

---

## 6. Frozen semantic validator

G-05のgenerator-independent local semantic validatorとして、v1初回で既に使用済みのPhi-4を固定する。

```text
Runtime: LM Studio 0.4.25.0
Endpoint: http://127.0.0.1:1234/v1
Identifier: sgokb-n04-phi4
Model file: microsoft/phi-4-gguf/phi-4-Q4_K_S.gguf
Quantization: Q4_K_S
Context length: 8192
GPU offload: max
Parallel: 1
Temperature: 0.0
max_tokens: 64
Seed: 20261018
stream: false
```

Phi-4はgeneratorとしてのv1 quality failureがあったが、G-11では自由生成器として使用しない。V4 unresolved unitだけを対象とするbounded semantic judgeとして利用する。

### Validator input boundary

渡してよいもの:

```text
target unit text
declared semantic role
cited K units only
purpose
presentation role
minimal taxonomy / use-case rule
```

禁止:

```text
Web
external retrieval
uncited SGOKB Knowledge
franchise-wide context
generator conversation outside target contract
model memoryをsupportとして使う指示
```

### Validator output

Strict JSON:

```json
{"verdict":"entailed | reasonable_derivation | role_valid | unsupported | contradictory | role_mismatch | indeterminate"}
```

rationale / chain-of-thoughtは要求しない。

Exact system promptはmachine harness manifestを正本とする。

### Model residency

RTX 4090 VRAM上でgeneratorとvalidatorを同時常駐できない場合、**sequential load / unloadを許可する**。

ただし次は変更禁止:

- identifier
- model file
- quantization
- context length
- GPU offload policy
- inference settings

load/unloadはmodel switchingではなくresidency managementとして扱う。各load stateをevidenceへ記録する。

---

## 7. Preflight boundary

Formal run開始前に全項目をPASSさせる。

1. Git working treeがclean。Git管理外`.local` evidence/runtime fileは可。
2. `.local/n03/sgokb-n03.sqlite`が存在する。
3. active `.sqlite-wal`が存在しないquiescent evaluation DB状態。
4. N-03の6 Object identityが確認できる。
5. Harrier local-only / Qdrant profileが利用可能。
6. `python -m sgokb ... system integrity`がPASS。
7. LM Studio versionが`0.4.25.0`。
8. generator / validatorのFrozen model fileが既にlocalに存在する。
9. Frozen identifier/load configurationで両modelをloadできる。
10. benchmark非依存のneutral structured-output smoke requestが両modelで成功する。
11. MCP stdio initialize / Tool discoveryがFrozen command/environmentで成功する。

Preflight failure時は**formal Case 1未開始**とする。

モデルやparameterを代替して続行しない。必要な変更がFrozen harness値へ及ぶ場合はG-11をreopenする。

Preflight failure evidenceは削除しない。

### Formal start

全preflight PASS後、次を保存した直後をformal run開始点とする。

```text
git-start.json
environment.json
harness.json
lm-studio-models.json
mcp-runtime.json
canonical-before.json
integrity-before.json
```

その後に行う最初のCase 1 MCP requestからformal evaluation対象とする。

---

## 8. Exact case order / runtime sequence

順序を固定する。

```text
Preflight
  ↓
Canonical / integrity before
  ↓
Case 1 — Saber Roleplay
  ↓
Case 2 — Similar Work Comparison
  ↓
Case 3 — Concept Combination Creative
  ↓
Canonical / integrity after
  ↓
Focused grounding regression
  ↓
Focused read-path regression
  ↓
Full pytest
  ↓
Ruff / git diff --check
  ↓
Overall evaluation
```

case順を結果に応じて変更しない。

### Per-case flow

```text
MCP request / response
  ↓
Context Builder result
  ↓
Grounded Context projection / K*
  ↓
Generation Attempt 1
  ↓
V0〜V5 Validation
  ↓
GroundingFailureController
  ├─ ACCEPTED -> deterministic render
  ├─ INSUFFICIENT_CONTEXT -> terminal
  ├─ retryable -> structured retry feedback -> Attempt 2 once
  ├─ REJECTED -> terminal
  └─ SYSTEM_FAILURE -> terminal
  ↓
Case rubric evaluation
```

Retry時にnew retrievalしない。

---

## 9. Evidence tree — Frozen

Root:

```text
.local/n04-v2/runs/<run_id>/
```

Top level:

```text
run.json
git-start.json
git-end.json
environment.json
harness.json
lm-studio-models.json
mcp-runtime.json
canonical-before.json
canonical-after.json
canonical-compare.json
integrity-before.json
integrity-after.json
overall-evaluation.json
regression/
```

Case directories:

```text
case-1-roleplay/
case-2-comparison/
case-3-creative/
```

各case最低限:

```text
mcp-request.json
mcp-response.json
context-builder.json
grounded-context.json
attempt-1/
  request.json
  http-request.json
  http-response.json
  raw-output.txt
  parsed-output.json
  validation.json
  decision.json
terminal.json
rubric.json
```

Retry時:

```text
retry-feedback.json
attempt-2/
  request.json
  http-request.json
  http-response.json
  raw-output.txt
  parsed-output.json
  validation.json
  decision.json
```

Case 2追加:

```text
similarity-request.json
similarity-response.json
```

`ACCEPTED`時のみ:

```text
rendered.txt
```

failed Attempt 1をRetry成功後に削除しない。

raw outputはGitへcommitしない。

---

## 10. Canonical safety procedure

N-04 v2はread-only acceptanceである。

Formal開始前:

1. evaluation DBをquiescentにする。
2. active WALがないことを確認する。
3. `.local/n03/sgokb-n03.sqlite`のSHA-256を`canonical-before.json`へ保存する。
4. `system integrity` resultを`integrity-before.json`へ保存する。

3 case終了後:

1. MCP / read clientを終了しDBをquiescentにする。
2. DB SHA-256を`canonical-after.json`へ保存する。
3. before / after SHA-256を比較し`canonical-compare.json`へ保存する。
4. `system integrity` resultを`integrity-after.json`へ保存する。

Formal PASSには:

```text
before SHA-256 == after SHA-256
integrity before = PASS
integrity after = PASS
```

を要求する。

DB hash mismatchはN-04 failureであり、内容を都合よく除外しない。

---

## 11. Post-case regression — Frozen

Reference Workstationでcase完了後に実行する。

```text
python -m pytest -q tests/test_n04_grounded_generation.py

python -m pytest -q \
  tests/test_j06_mcp_client_acceptance.py \
  tests/test_j04_context_builder.py \
  tests/test_j01_similarity_application.py \
  tests/test_n04p05_derived_cli.py

python -m pytest -q

python -m ruff check \
  src/sgokb/grounding \
  src/sgokb/application_grounding.py \
  tests/test_n04_grounded_generation.py

git diff --check
```

PowerShellでは行継続記号をbacktickへ読み替えてよい。実行commandとexit codeをlogへ残す。

Required:

- focused grounding PASS
- focused read-path PASS
- full pytest 0 failed
- new skip / xfailでfailureを隠さない
- Ruff PASS
- git diff --check PASS

G-10 CI結果をG-12のReference Workstation regressionの代わりにはしない。

---

## 12. Rubric authority

Machine validatorとformal Case rubricを分離する。

### Machine grounding Gate

G-09実装:

```text
V0〜V5
GroundingFailureController
DeterministicRenderer
```

を使用する。

### Final case rubric

`benchmark/n04-ai-use-cases-v2.json`のcase-specific acceptance / critical_failuresをCodex / human evidence reviewで判定する。

Allowed verdict:

```text
PASS
FAIL
NOT_APPLICABLE
```

各itemへ短い理由とevidence path / unit ID / K refを付ける。

Generator self-scoreはformal authorityにしない。

### Formal Case PASS

```text
terminal = ACCEPTED
AND retrieval/context gates all PASS
AND output gates all PASS
AND critical failure count = 0
AND canonical invariance maintained
```

`INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILURE`はCase FAIL。

Overall N-04 v2 PASS:

```text
3 / 3 Case PASS
AND canonical hash identical
AND integrity before/after PASS
AND focused regressions PASS
AND full pytest 0 failed
AND start HEAD == end HEAD
```

---

## 13. Formal-run prohibited actions

開始後は禁止:

- source / test / benchmark / rubric編集
- generator model切替
- validator model切替
- case結果を見てparameter変更
- retry時のnew retrieval
- Web / cloud factual supplementation
-別Contextへ差替え
- failed outputのpartial salvage
- failed Attempt 1 evidence削除
- failed caseだけ条件変更して再試行

Formal runに失敗した場合、そのrunをそのまま保存してN-04 resultとして評価する。

Harness defectが判明した場合はFailure class Iとしてrunを無効扱いにできるが、evidenceは保存し、G-11をreopenして別run IDで再実施する。

---

## 14. Definition of Done

- [x] Reference Workstation / evaluation DBをFreezeした。
- [x] MCP command / environment / transportをFreezeした。
- [x] actual generator identifier / model file / load configをFreezeした。
- [x] case別generation parameterをFreezeした。
- [x] generator-independent semantic validator identifier / settings / verdict schemaをFreezeした。
- [x] structured-output mechanismをFreezeした。
- [x] preflight / formal start boundaryをFreezeした。
- [x] exact case order / retry sequenceをFreezeした。
- [x] evidence root / file treeをFreezeした。
- [x] canonical before/after procedureをFreezeした。
- [x] Reference Workstation regression commandsをFreezeした。
- [x] final rubric authority / Overall GateをFreezeした。
- [x] G-08 wording ambiguityをG-07 retry invariantとv2 case値に整合させた。

---

## 15. Next task

次は:

```text
N-04G-12 [P0]
Reference Workstation formal N-04 v2 re-acceptanceを実施し、N-04 Complete判定を行う
```

とする。
