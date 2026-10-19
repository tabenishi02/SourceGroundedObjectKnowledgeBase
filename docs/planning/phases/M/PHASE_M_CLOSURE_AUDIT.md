# Phase M Closure Audit

更新日: 2026-10-16

- Status: **Complete**
- Baseline: `7b4507ab5a80ebdb687c65d5e4627beb83806f3c`
- Scope: `M-01`〜`M-03` — Object-centered CLI / compatibility cutover / 1 Object standard workflow
- Completion criterion: **日常運用で内部DB操作を必要としない。**
- Next: `Phase N — Test / Evaluation / Acceptance`
- First task: `N-01 [P0] Unit Testを新ドメインへ更新する`

---

## 1. Task completion audit

| Task | Status | 正本 / Evidence |
|---|---|---|
| M-01 | **Complete (2026-10-16)** | `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`、PR #32 |
| M-02 | **Complete (2026-10-16)** | `docs/decisions/M02_CLI_COMPATIBILITY_POLICY.md`、M-01 cutoverで実施 |
| M-03 | **Complete (2026-10-16)** | `docs/operations/OBJECT_STANDARD_WORKFLOW.md`、`docs/planning/M03_LOCAL_ACCEPTANCE.md`、PR #34 |

Task master、`PHASE_M_PREPARATION.md`、`M03_STATUS.md`、M-03 local acceptanceを照合し、Phase Mに未完了の正式Taskがないことを確認した。

---

## 2. M-01 closure

operator-facing public CLIを`sgokb` 1本へ統一し、Domain namespace方式を実装した。

```text
source / object / association / evidence / registry
package / result / version / search / similar / render / mcp / system
```

確定した主なboundary:

- stable Object IDをauthoritative selectorとする。
- machine-readable contractは`sgokb.cli/1.0`。
- write / external export / maintenanceをread operationから区別する。
- Relationのauthoritative writeはEvidence-grounded Object Result Import経由だけとする。
- Registry proposalはResult Import時に自動適用せず、accept/rejectとexplicit applyを分離する。
- MCPは`KnowledgeReadApplication`経由のread-only stdio serverとする。
- Semantic runtime不足からcloudへsilent fallbackしない。
- backup / restoreはoperator-facing System operationとして提供し、restore overwriteは明示acknowledgementを要求する。

Migration 017でRegistry proposal review/apply auditを追加した。

---

## 3. M-02 closure

旧CLIをdeprecated wrapperとして長期維持しない方針を採用した。

- public entrypointは`sgokb`のみ。
- 旧`sgokb-package`は新Domain namespaceへ移行後に削除済み。
- 旧flat CLI aliasをcompatibility layerとして復活させない。
- breaking CLI path変更よりもcanonical Source / Evidence / Package / Result / Version semanticsの維持を優先する。

---

## 4. M-03 local acceptance

Reference Workstationでproduction DB・実Google Drive・Generative LLM APIを使用せず、隔離環境で標準workflowを受入した。

必須Gate:

```text
Object add/show
→ Source import/process
→ Association confirmed
→ Evidence candidates/select
→ Package build/stage/preflight/explicit export
→ Result detect/receive/validate/review/explicit import
→ accepted Object Knowledge
→ Relations read
→ Render
→ Lexical Search
→ MCP stdio read
```

結果:

- 必須CLI workflow: **PASS**
- accepted Knowledge / Render / Lexical Search: **PASS**
- MCP SDK v2 stdio read: **PASS**
- MCP read前後のDB SHA-256不変: **PASS**
- MCP停止後のCLI read: **PASS**
- `tests/test_m03_standard_workflow.py`: **2 passed**
- 関連回帰: **153 passed / 1 deselected**
- 修正後M-01 tests: **12 passed**
- changed Python files Ruff / format / `git diff --check`: **PASS**

M-03実行中に、optional Semantic/Similarity dependency不足がinternal errorのexit 1になる問題を発見した。ImportError起因のruntime unavailableをM-01 contractどおりexit 5へ変換し、標準workflow全体を再実行して必須Gateが再度PASSした。

---

## 5. Phase M残タスク監査

**Phase M内の残タスクは0件。**

次の項目は残存しているが、Phase Mの未完了Taskではない。

### 5.1 Package Transfer known baseline failure

```text
tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch
```

期待messageが`SHA-256 mismatch`である一方、実装は先に`Package file size mismatch`を返す既知差異。Phase M起因ではなく、M-03終了時にも同一failureとして再現した。

Phase NではN-01/N-07のtest/failure auditで扱う候補とする。Phase M closureのためにtestをxfail化したりcontractを弱めたりしない。

### 5.2 Semantic / Similarity runtime

Reference Workstationではlocal embedding / vector optional runtimeが未構成だったためM-03ではSKIPした。CLIのruntime-unavailable contract（exit 5）は確認済み。

実Semantic / Similarity品質・backend評価はPhase NのN-06で実施する。

### 5.3 ChatGPT / AI analysis quality

M-03はdeterministic Object Result fixtureでtransport / validation / import wiringを検証した。ChatGPT手動分析品質を合格と判定したものではない。

実データとAI利用品質はN-03 / N-04で評価する。

### 5.4 Performance / recovery / full acceptance

1 Object p95処理時間、Vector backend品質、Failure / Recovery、実データVertical SliceはPhase Nの責務である。M-03の1 Object workflow acceptanceとは分離する。

---

## 6. Closure decision

Phase Mの完了条件

> **日常運用で内部DB操作を必要としない。**

は、M-03 Reference Workstation acceptanceで満たした。

したがってPhase Mを**Complete**として閉じ、Phase Nへ移行する。

Phase Nは「CLIが動くこと」の再確認ではなく、新しいSGOKBの目的に対してTest / Evaluation / Acceptanceが十分かを評価するPhaseとする。
