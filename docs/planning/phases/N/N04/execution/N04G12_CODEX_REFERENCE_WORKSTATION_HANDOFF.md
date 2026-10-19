# N-04G-12 Codex Reference Workstation Execution Handoff

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04G-12 [P0] Reference WorkstationでN-04を正式再受入する`
- Status: **Execution handoff ready / formal run not started**
- Branch: `phase-n/n04-prerequisite-derived-search`
- Frozen acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Frozen formal harness: `benchmark/n04-v2-formal-harness-v1.json`
- Harness Decision: `docs/decisions/N04G11_FORMAL_REACCEPTANCE_HARNESS_FREEZE.md`
- Task master: `docs/planning/N04_GROUNDED_GENERATION_TASKS.md`

---

## 1. Purpose

この文書は、Reference Workstation上でCodexがN-04G-12 formal re-acceptanceをそのまま実行できるようにするhandoffである。

このhandoff自体はformal runではない。Formal runはG-11で定義したpreflightを全てPASSし、start evidenceを書き終えた後、Case 1の最初のMCP request直前から開始する。

G-12ではG-07/G-08/G-11のFrozen semantics / rubric / model / retry policyを変更してはならない。

---

## 2. Codexへ渡す指示文

以下をCodexへそのまま渡す。

```text
SourceGroundedObjectKnowledgeBase の Phase N / N-04G-12 formal re-acceptanceをReference Workstation上で実施してください。

重要: これは設計・実装Taskではありません。Frozen acceptance / harnessをそのまま実行して証跡を残し、PASS/FAILを判定するTaskです。結果を良くする目的で条件を変更しないでください。

最初に必ず以下を確認してください。

- docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md
- docs/decisions/N04G08_N04_V2_ACCEPTANCE_SPEC_FREEZE.md
- docs/decisions/N04G08_G11_GENERATION_SETTINGS_CLARIFICATION.md
- docs/decisions/N04G11_FORMAL_REACCEPTANCE_HARNESS_FREEZE.md
- benchmark/n04-ai-use-cases-v2.json
- benchmark/n04-v2-formal-harness-v1.json
- docs/design/N04G09_GROUNDED_GENERATION_IMPLEMENTATION.md
- docs/evaluation/N04G10_GROUNDED_GENERATION_REGRESSION.md
- docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md
- docs/planning/N04_GROUNDED_GENERATION_TASKS.md

## A. Repository sync / preflight preparation

1. Reference Workstation上のSourceGroundedObjectKnowledgeBase repositoryを特定してください。通常は C:\codex 配下を想定しますが、pathを決め打ちせず既存checkoutを確認してください。
2. branch `phase-n/n04-prerequisite-derived-search`へ移動してください。
3. `git fetch` 後、remote branchへ fast-forward only で同期してください。rebase / merge commit / force操作はしないでください。
4. working treeがcleanであることを確認してください。`.local` 等のGit ignored runtime/evidence fileは可です。
5. current HEAD、branch、remote tracking状態を記録してください。
6. G-11 harnessに書かれた値とlocal environmentを照合してください。

Formal run前なら、必要に応じて `.local/n04-v2/` 配下にuntrackedのlocal runner/helperを作成して構いません。ただしGit-managed source/test/benchmark/Decision文書を変更しないでください。

## B. Frozen harness値

次を変更せず使用してください。

Reference Workstation:
- Windows 11
- Python 3.10.6
- GPU RTX 4090 24GB
- evaluation DB `.local/n03/sgokb-n03.sqlite`

Semantic runtime:
- embedding model `microsoft/harrier-oss-v1-0.6b`
- revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`
- dimensions 1024
- local-only
- Qdrant 1.19.2
- HTTP 6333 / gRPC 6334
- collection prefix `sgokb_n03_eval`

MCP:
- Python SDK 2.3.0
- protocol 2026-07-28
- stdio
- command `python -m sgokb mcp serve --semantic-runtime`
- AI入力はMCP public read boundaryのみから取得する
- consumer側のdirect SQLite Knowledge readは禁止

LM Studio:
- version 0.4.25.0
- endpoint `http://127.0.0.1:1234/v1`
- cloud inference禁止
- Web補完禁止
- 新規model download禁止

Generator:
- identifier `sgokb-n04-mistral32`
- model `Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf`
- Q4_K_M
- context 8192
- GPU offload=max
- parallel=1
- seed=20261018
- stream=false

Case parameters:
- Case 1 roleplay: temperature 0.2 / max_tokens 700
- Case 2 comparison: temperature 0.0 / max_tokens 900
- Case 3 creative: temperature 0.2 / max_tokens 1100

Semantic validator:
- identifier `sgokb-n04-phi4`
- model `phi-4-Q4_K_S.gguf`
- Q4_K_S
- context 8192
- GPU offload=max
- parallel=1
- temperature=0.0
- max_tokens=64
- seed=20261018
- stream=false

GeneratorとvalidatorはVRAM都合でsequential load/unloadして構いません。ただしidentifier/model/settingsは変更しないでください。

## C. Preflight

G-11のpreflight全項目をformal run開始前に確認してください。

最低限:
1. git clean
2. evaluation DB存在
3. active `.sqlite-wal`なし
4. N-03 6 Object identity確認
5. Harrier/Qdrant利用可能
6. `system integrity` PASS
7. LM Studio versionが0.4.25.0
8. generator/validator model fileがlocalに存在
9. Frozen identifier/load configで両model load可能
10. benchmarkとは無関係なneutral structured-output smoke testを両modelで成功
11. Frozen command/environmentでMCP stdio initialize/tool discovery成功

Preflightで問題が出た場合、formal runは開始しないでください。別model、別parameter、cloud/Webへfallbackしないでください。

Infrastructureだけで直せる問題ならFrozen値を変えずに修復してpreflightをやり直して構いません。Frozen harness値自体を変えなければならない場合は作業を停止し、G-11 reopenが必要と報告してください。

## D. Evidence root / formal start

run_idは `YYYYMMDDTHHMMSS+0900` 形式で作成し、

`.local/n04-v2/runs/<run_id>/`

をevidence rootにしてください。

Formal start前に最低限以下を書いてください。
- run.json
- git-start.json
- environment.json
- harness.json（Frozen harness manifestのcopy + hashが分かる形）
- lm-studio-models.json
- mcp-runtime.json
- canonical-before.json
- integrity-before.json

Canonical beforeはactive WALがないquiescent状態で `.local/n03/sgokb-n03.sqlite` のSHA-256を記録してください。

これらを書き終えた後、Case 1の最初のMCP request直前からformal run開始です。

Formal start後はGit-managed fileを一切編集しないでください。start HEADとend HEADは同一でなければなりません。

## E. Grounded-generation execution implementation

既存production codeを使用してください。

中心API:
- `sgokb.application_grounding.GroundedGenerationApplication`
- `project_context(...)`
- `build_request(...)`
- `request_prompt_text(...)`
- `validate(...)`
- `decide(...)`
- `build_retry_feedback(...)`
- `parse_output(...)`
- `render(...)`

Semantic validator adapterはG-09 `SemanticValidatorAdapter` protocolに従うlocal-only adapterとして、Git ignored `.local/n04-v2/` 配下で実装して構いません。

Validatorへ渡す情報は:
- target unit text
- declared semantic role
- cited K units only
- purpose
- presentation role
- minimal taxonomy/use-case rule

のみです。Web、外部retrieval、uncited Knowledge、generator会話全体を渡さないでください。

Validator system prompt / strict verdict schemaは `benchmark/n04-v2-formal-harness-v1.json` を正本としてください。

Generator requestは `GroundedGenerationRequestBuilder.to_prompt_text(request)` 相当の文字列をsole user messageとしてLM Studio `/v1/chat/completions`へ送ってください。

`response_format=json_schema` で `src/sgokb/grounding/output.py::GENERATION_OUTPUT_SCHEMA` をstrict schemaとして使用してください。

独自のcase-specific system prompt、hidden answer、補足factを追加しないでください。

## F. Case 1 — Saber Roleplay

MCP `build_context`を使用し、v2 benchmarkのexact条件:
- object Saber `326a97cf-47aa-4760-a7f1-07bfe639fcf0`
- purpose=roleplay
- max_characters=12000
- include_attributes=true
- include_relations=true
- include_evidence_refs=false
- current accepted Version

MCP raw request/response、Context Builder output、Grounded Context/K mapping、context_fingerprintを保存してください。

Generator task文とcontract requirementsは `benchmark/n04-ai-use-cases-v2.json` のCase 1をそのまま使用してください。

Attempt 1 → validation V0〜V5 → `GroundingFailureController.decide()` を実行してください。

retryable failureなら最大1回だけAttempt 2を実行します。
Attempt 2では同じContext/model/temperature/max_tokens/seed/schema/taskを完全固定し、`build_retry_feedback()`由来のstructured validator feedbackだけ追加してください。

ACCEPTED時のみdeterministic rendererでrendered.txtを作成してください。

## G. Case 2 — Similar Work Comparison

最初にMCP `find_similar_objects`をFate/stay night `d5824d33-7008-4121-9cfe-1f95a19667fd`へ実行してください。

条件:
- cross_class=false
- limit=5
- current scope
- real semantic runtime

returned current Workのrank 1をcomparison targetにしてください。
BLEACH IDをhardcodeしてretrievalを迂回しないでください。

similarity-request.json / similarity-response.jsonへsource, candidate, rank, score, score_type, resolved versionを保存してください。

その後v2 benchmarkのexact comparison Context条件:
- purpose=comparison
- max_characters=24000
- attributes=true
- relations=false
- evidence refs=true

をMCP経由で取得し、Grounded Contextへprojectしてください。

Attempt / validation / retry / renderはCase 1と同じFrozen flowで実施してください。

## H. Case 3 — Concept Combination Creative

MCP `build_context`で:
- Tsundere `8c83f986-f491-41a8-8645-9f71dd5874b9`
- Hero's Journey `fee32007-0f92-449a-ba21-4ec2f78d1cd4`
- purpose=creative
- max_characters=24000
- attributes=true
- relations=true
- evidence refs=false

をcurrent accepted Versionから取得してください。

Grounded source Concept knowledgeとnew creative additionをvisibleに分離するFrozen contractをそのまま評価してください。

Attempt / validation / retry / renderは同じFrozen flowです。

## I. Per-case evidence

各case最低限:
- mcp-request.json
- mcp-response.json
- context-builder.json
- grounded-context.json
- attempt-1/request.json
- attempt-1/http-request.json
- attempt-1/http-response.json
- attempt-1/raw-output.txt
- attempt-1/parsed-output.json
- attempt-1/validation.json
- attempt-1/decision.json
- terminal.json
- rubric.json

Retry時:
- retry-feedback.json
- attempt-2/* 同一構成

Case 2:
- similarity-request.json
- similarity-response.json

ACCEPTED時のみ:
- rendered.txt

Attempt 1がFAILでも削除しないでください。

## J. Formal rubric evaluation

各caseのmachine validationとは別に `benchmark/n04-ai-use-cases-v2.json` のretrieval/output/critical_failuresを1項目ずつ判定してください。

Allowed verdict:
- PASS
- FAIL
- NOT_APPLICABLE

各判定に短い理由と、関連unit ID / K ref / evidence pathを付けてrubric.jsonへ保存してください。

Generator自身のself-scoreをformal判定に使用しないでください。

Case PASS:
- terminal=ACCEPTED
- retrieval/context Gate全PASS
- output Gate全PASS
- critical failure 0

INSUFFICIENT_CONTEXT / REJECTED / SYSTEM_FAILUREはCase FAILです。

## K. Canonical after / regression

Case 3終了後、MCP/read clientを閉じ、evaluation DBをquiescentにしてください。

- canonical-after.json: DB SHA-256
- canonical-compare.json: before/after比較
- integrity-after.json: system integrity

を保存してください。

Formal PASSにはbefore/after DB SHA-256完全一致とintegrity before/after PASSが必要です。

その後Reference Workstation上でG-11のexact regressionを実行してください。

1. `python -m pytest -q tests/test_n04_grounded_generation.py`
2. `python -m pytest -q tests/test_j06_mcp_client_acceptance.py tests/test_j04_context_builder.py tests/test_j01_similarity_application.py tests/test_n04p05_derived_cli.py`
3. `python -m pytest -q`
4. `python -m ruff check src/sgokb/grounding src/sgokb/application_grounding.py tests/test_n04_grounded_generation.py`
5. `git diff --check`

stdout/stderr/exit codeをFrozen evidence pathのregression logsへ保存してください。

最後にgit-end.jsonを保存し、start/end HEAD一致を確認してください。

## L. Overall evaluation

Overall PASSには:
- Case 1 PASS
- Case 2 PASS
- Case 3 PASS
- canonical hash identical
- integrity before/after PASS
- focused regressions PASS
- full pytest 0 failed
- Ruff PASS
- git diff --check PASS
- start HEAD == end HEAD

が全て必要です。

1つでも満たさなければN-04はCompleteにしないでください。

結果を `.local/n04-v2/runs/<run_id>/overall-evaluation.json` に保存してください。

## M. Formal run後のGit更新

formal evaluationとgit-end記録が完了してから初めてGit-managed docsを更新して構いません。

PASSの場合:
- docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md にv2 execution recordを追記
- docs/planning/N04_GROUNDED_GENERATION_TASKS.md でN-04G-12 Complete / N-04 Complete
- docs/planning/PHASE_N_PREPARATION.md のN-04をComplete
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md のN-04をComplete
- N-05へ進行可能と記載

FAILの場合:
- N04_AI_USE_CASE_ACCEPTANCE.mdへv2 failureを追記
- G-12はComplete（formal re-acceptance executed）としてよいが、N-04自体はFailedのまま
- failure class / exact evidence /次に必要な設計・実装修正を記録
- N-05へは進めない

SYSTEM/HARNESS defectでformal run自体を無効と判断した場合:
- evidenceを保存
- G-12 Completeにはしない
- G-11 reopenが必要かを明記

Git更新後、必要なtest/format確認を行い、変更をcommit/pushしてください。

Raw model output / local DB / `.local/n04-v2/` evidenceはGitへcommitしないでください。

最終報告では:
- run_id
- start/end HEAD
- preflight result
- generator/validator identity
- 3 caseのterminal / formal PASS/FAIL
- retry有無
- unsupported/contradictory/separation issue
- canonical hash comparison
- integrity
- focused/full pytest
- N-04 CompleteかFailedか
- commit SHA

をまとめてください。

条件を勝手に変更してPASSさせることは禁止です。失敗した場合は失敗結果をそのまま残してください。
```

---

## 3. ChatGPT側からのhandoff理由

2026-10-18時点でReference WorkstationのDesktop Commander device `FNB1Main` はOnlineだが、Desktop Commanderの月間利用上限に達しておりremote command executionが停止している。

したがって、このChatGPT sessionからG-11 Frozen harnessをReference Workstation上でformalに実行することはできない。

これはSGOKB / N-04のacceptance failureではなく、**formal run未開始**である。

代替としてGitHub Actions等でformal G-12を実行してはならない。G-11はReference Workstation / local LM Studio / local evaluation DB / local Qdrant profileをFreezeしているためである。

---

## 4. Return payload expected from Codex

Codex実行後、ChatGPTへ最低限次を返す。

```text
run_id
formal run valid / invalid
preflight PASS/FAIL
start HEAD
end HEAD
generator exact identifier
validator exact identifier
Case 1 terminal + formal verdict
Case 2 terminal + formal verdict
Case 3 terminal + formal verdict
retry usage per case
canonical before SHA-256
canonical after SHA-256
canonical equal true/false
integrity before/after
focused grounding pytest
focused read-path pytest
full pytest
ruff
git diff --check
overall N-04 decision
formal evidence root
post-run documentation commit SHA
```

ChatGPTはこの返却結果とGitHub更新内容を照合した後に、N-04 Complete / Failedの最終状態を確認する。
