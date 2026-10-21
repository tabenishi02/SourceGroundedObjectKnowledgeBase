# N-04R-05 Grounded Generation Asset Disposition

更新日: 2026-10-22

- Task: `N-04R-05 — Grounded Generation Asset Disposition`
- Parent: `N-04 [P0]`
- Status: **Complete / Disposition Accepted**
- Repository authority: GitHub `main`
- Parent decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- N-04 formal result: **Complete / PASS** (`docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md`)

## 1. Decision

G-01〜G-25で追加されたGrounded Generation関連資産は、2026-10-22以降のSGOKB core責務として扱わない。

現行SGOKBの正式責務は次で終了する。

```text
Canonical / Derived SGOKB
  ↓
Retrieval / Similarity
  ↓
Context Builder
  ↓
MCP / public read boundary
  ↓
External Consumer boundary
```

Consumer側の推論・生成・grounding検証・presentation生成はSGOKB coreの責務ではない。

したがってGrounded Generation資産を次の4分類へ固定する。

```text
KEEP_CORE
KEEP_EXPERIMENTAL
MOVE_CONSUMER_SIDE
RETIRE
```

結論として、**Grounded Generation実装・Verifier・Classifier・Presentation系でKEEP_COREとする資産は0件**である。

## 2. Classification semantics

### KEEP_CORE

現行SGOKB product / public Knowledge Access responsibilityに必要であり、production回帰・Phase Nの現行Gateとして維持する。

### KEEP_EXPERIMENTAL

SGOKB coreの要件・Gateではないが、今後のConsumer-side grounded generation研究や設計検討に再利用価値があるため、historical / research evidenceとして保持する。

- production authorityを持たない。
- N-04 / N-05 / N-06 / N-07のGateに使用しない。
- default production dependencyにしてはならない。
- 将来利用する場合は、その時点のConsumer-side要件から改めて採否を判断する。

### MOVE_CONSUMER_SIDE

機能の責務は有効だが、ownerがSGOKB coreではない。将来Grounded Generation capabilityを継続する場合は、外部AI Consumer / orchestration layerへ移す。

現時点では移行先project/repositoryを確定していないため、**物理移動は行わずSGOKB repository内でhistorical implementationとしてfreeze**する。

- 新規SGOKB featureからimportしてはならない。
- public CLI / MCPへ接続してはならない。
- canonical workflowの必須dependencyにしてはならない。
- 次に機能開発を再開する場合、最初の作業はConsumer-side extractionとする。

### RETIRE

旧N-04 generation-quality acceptance専用の実行資産として役割を終了する。

- 今後のformal Gateとして実行しない。
- 新しい修正・model selection・threshold tuningを継続しない。
- historical reproducibilityのため、今回のTaskでは削除しない。
- 将来repo cleanupを行う場合はGit historyまたはarchiveへ退避できる。

## 3. KEEP_CORE

Grounded Generation chain自体にはKEEP_CORE資産はない。

ただし、Grounded Generation調査と混同して削除してはならない現行N-04 core資産は次である。

```text
docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md
docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md
docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md
docs/evaluation/N04R04_REFERENCE_WORKSTATION_REACCEPTANCE.md
benchmark/n04-knowledge-access-cases-v1.json
benchmark/n04-knowledge-access-formal-harness-v1.json
benchmark/tools/n04r03_harness_preflight.py
benchmark/tools/n04r04_evaluate_evidence.py
tests/test_n04r03_knowledge_access_harness.py
tests/test_n04r04_evidence_evaluator.py
tests/test_n04r04_preflight_portability.py
```

また、Grounded Generation以前から存在する次のproduction boundaryも当然KEEP_COREである。

```text
src/sgokb/application_read.py
src/sgokb/retrieval/
src/sgokb/mcp/
```

これらはN-04R-04で実MCP経路として正式受入済みである。

## 4. MOVE_CONSUMER_SIDE

### 4.1 Grounded Generation application / implementation

次はConsumer-side capabilityへownerを移す。

```text
src/sgokb/application_grounding.py
src/sgokb/application_grounding_v4.py
src/sgokb/grounding/**
```

対象には次を含む。

- grounded generation request construction
- generated output parsing / schema
- atomicity / semantic-role validation
- source-fact verification adapter
- interpretation derivation validation
- material sufficiency gate
- retry / failure handling
- deterministic presentation / rendering
- v4 structured proposition / certification / stage pipeline

これらはKnowledge Providerではなく、**SGOKB Contextを利用して文章を生成・検証するConsumer orchestration**の責務である。

### 4.2 Coupled implementation tests

次のようなGrounded Generation implementation自体を検証するtestも同じownerへ移す。

```text
tests/test_n04_grounded_generation.py
tests/test_n04g20_adversarial_regression.py
tests/test_n04g24_v4_implementation.py
tests/test_n04g24_v4_provider_runtime.py
```

物理移動までは行わないが、SGOKB core regression requirementとして新規機能を追加してはならない。

### 4.3 Grounded Generation architecture contracts

Grounded Generationの機能要件・architectureとして今後も利用可能なG-series Decision / Designは、Consumer-side capabilityの設計資料としてownerを移す。

主対象:

```text
docs/decisions/N04G01_*.md ... N04G07_*.md
docs/decisions/N04G14_*.md ... N04G18_*.md
docs/decisions/N04G23*.md
docs/design/N04G09_GROUNDED_GENERATION_IMPLEMENTATION.md
```

特にG-14〜G-18およびG-23系の、atomic proposition、role provenance、certification、two-stage generation、terminal render等の設計は研究価値を認めるが、SGOKB core architecture authorityではない。

## 5. KEEP_EXPERIMENTAL

### 5.1 Failure analysis / evaluation evidence

実際の生成失敗から得た分析は、Consumer-side設計を考える資料として保持する。

代表:

```text
docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
docs/evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md
docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md
docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md
docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md
docs/evaluation/N04G24_V4_IMPLEMENTATION_RESULT.md
docs/evaluation/N04G25A_DEVELOPMENT_CLASSIFIER_SELECTION.md
```

これらは「SGOKBが必要とするproduction behavior」の証明ではなく、**LLM生成品質を保証しようとした場合に何が難しかったかを示すresearch evidence**として扱う。

### 5.2 Frozen 47 / adversarial semantic corpus

次をresearch corpusとして保持する。

```text
benchmark/n04g23a-atomicity-role-gold-seed-v1.json
benchmark/n04g23a-atomicity-role-gold-v1.json
benchmark/n04g23a-atomicity-role-paraphrase-profile-v1.json
benchmark/n04g23a-atomicity-role-prompt-profiles-v1.json
benchmark/n04g23ae-role-compatibility-v1.json
benchmark/n04g23ae-v4-gate-desk-replay-v1.json
benchmark/n04g23ar-judge-candidates-v1.json
benchmark/n04g23ar-split-paraphrase-profile-v1.json
```

`benchmark/n04g23a-atomicity-role-gold-v1.json`の47 Goldは、**current N-04 final confirmationではない**。再実行をN-04 completion条件として要求してはならない。

### 5.3 G-25A development corpus / result

G-25Aは`VALID_FAIL_NO_SELECTION`という有効な研究結果を残したため、dataset/result自体は保持する。

```text
benchmark/n04g25a-atomicity-development-v1.jsonl
benchmark/n04g25a-content-type-development-v1.jsonl
benchmark/n04g25a-candidate-manifest-v1.json
benchmark/n04g25a-development-manifest-v1.json
benchmark/n04g25a-development-policy-lock-v1.json
benchmark/n04g25a-split-manifest-v1.json
benchmark/results/n04g25a-development-selection-reference-workstation.json
```

ただし、ここからSGOKB classifier選定を再開しない。

## 6. RETIRE

### 6.1 Old formal N-04 generation-quality harnesses

次はformal acceptanceとしてretireする。

```text
benchmark/n04-ai-use-cases-v1.json
benchmark/n04-ai-use-cases-v2.json
benchmark/n04-ai-use-cases-v3.json
benchmark/n04-v2-formal-harness-v1.json
benchmark/n04-v3-formal-harness-v1.json
benchmark/n04-v3-material-profiles-v1.json
benchmark/n04-v3-source-fact-verifier-profile-v1.json
```

Historical G-12 / G-22結果の再現証拠としてのみ保持する。

### 6.2 Old verifier / judge / classifier execution tooling

次の系統はactive SGOKB benchmark toolingからretireする。

```text
benchmark/tools/n04g20_*.py
benchmark/tools/n04g21*.py
benchmark/tools/n04g22_*.py
benchmark/tools/n04g23*.py
benchmark/tools/n04g25a_*.py
```

`benchmark/tools/n04r03_harness_preflight.py`と`n04r04_evaluate_evidence.py`は対象外でありKEEP_COREである。

### 6.3 Superseded execution-contract tests

旧generation-quality harnessやmodel-selection procedureだけを固定するtestはretire対象とする。

代表:

```text
tests/test_n04g21_harness_freeze_candidate.py
tests/test_n04g21r_offline_proof_contract.py
tests/test_n04g22_execution_contract.py
tests/test_n04g23a_atomicity_role_benchmark_contract.py
tests/test_n04g23a_required_repeatability_gate.py
tests/test_n04g23ar_candidate_eval_contract.py
tests/test_n04g25a_development.py
tests/test_n04g25a_selection.py
tests/test_n04g25a_training_policy.py
```

今回のR-05では削除しない。将来archive / test-suite cleanupを行う際に、production default suiteから外す対象とする。

### 6.4 Historical execution handoffs / active-task documents

次は実行指示としてretireする。

```text
docs/planning/phases/N/N04/N04_GROUNDED_GENERATION_TASKS.md
docs/planning/phases/N/N04/N04_GROUNDED_GENERATION_HANDOFF.md
docs/planning/phases/N/N04/post-g12/**
docs/planning/phases/N/N04/execution/N04G*.md
```

過去の実行経緯を追跡するためファイル自体は保持するが、current handoffとして使用しない。

## 7. Why code is not deleted in R-05

R-05の目的はasset ownership / future dispositionの決定であり、別repositoryへの大規模移行ではない。

今すぐ`src/sgokb/grounding/`を削除すると、

- historical G-12〜G-25実装と評価結果の再現性を失う
- Consumer-side移行先が未確定のまま有用な実装を捨てる
- 大量のtest / benchmark / docs参照を同時に破壊する

ため、今回のTaskでは物理削除をしない。

一方で、残っていることを理由にSGOKB core責務へ戻してもならない。

したがって当面の状態は次とする。

```text
repository location: unchanged
production authority: none
public CLI/MCP exposure: none
new SGOKB dependency: prohibited
future owner: Consumer-side grounded-generation capability
```

## 8. Dependency audit result

現行production entry pointを確認した結果、SGOKB public CLIは`Application` / `KnowledgeReadApplication` / derived maintenance / exchange / rendering等から構成され、`application_grounding`をimportしていない。

MCP adapterも`KnowledgeReadApplicationPort`を通じたread-only Knowledge operationに限定され、Grounded Generationを参照しない。

したがってGrounded Generation codeは、現行SGOKB public Knowledge Access pathから切り離された独立実装として扱える。

## 9. Rules after R-05

以後、SGOKBで次を禁止する。

1. N-04 completionのためにGrounded Generationを再開する。
2. G-25A classifier selectionを再開する。
3. Frozen 47をcurrent N-04 Gateとして実行する。
4. Consumer hallucinationを理由にSGOKB coreへverifierを追加する。
5. Grounded Generation codeをpublic MCP / CLIの必須pathへ接続する。

Consumer-side capabilityとして再開したい場合は、SGOKBとは別責務として新しい要件・project boundaryを先に定義する。

## 10. N-04 reconstruction closure

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Complete
N-04R-03 Formal Harness Reconstruction           Complete
N-04R-04 Reference Workstation Re-Acceptance     Complete / PASS
N-04R-05 Grounded Generation Asset Disposition   Complete
```

これによりN-04 responsibility reconstruction chainは終了する。

```text
N-04 = Complete / PASS
```

Phase Nの次の未完了P0 TaskはN-05 / N-06であり、相互に独立して開始できる。順次進める場合は`N-05 — Performance`を次Taskとする。
