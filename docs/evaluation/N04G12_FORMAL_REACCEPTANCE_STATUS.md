# N-04G-12 Formal Re-Acceptance Status

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04G-12 [P0] Reference WorkstationでN-04を正式再受入する`
- Status: **Complete — valid formal re-acceptance executed; 0/3 Case PASS**
- N-04 status: **Failed / not Complete**
- N-05 status: **blocked**
- Frozen acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Frozen harness: `benchmark/n04-v2-formal-harness-v1.json`
- Codex handoff: `docs/planning/N04G12_CODEX_REFERENCE_WORKSTATION_HANDOFF.md`
- Detailed result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md` (G-12 v2 execution record)

## 1. Execution decision

Reference Workstation上で全preflightをPASSし、G-11 frozen条件で正式実行した。以前のChatGPT remote-command利用上限によるformal未開始状態は、今回のCodexローカル実行で解消した。GitHub Actions等の代替環境は使用していない。

- run_id: `20261018T213810+0900`
- start/end HEAD: `843c0332456a7857d567510b4a15162b645293ce` (identical)
- branch: `phase-n/n04-prerequisite-derived-search`
- formal start: `2026-10-18T21:41:05.251722+09:00`
- generator: `sgokb-n04-mistral32`
- semantic validator: `sgokb-n04-phi4`
- evidence root: `.local/n04-v2/runs/20261018T213810+0900/` (Git-ignored)

MCP public read boundaryからKnowledgeを取得し、Case 2は実際のSimilarity rank 1のBLEACHを選んだ。Generator sole-user request、strict schema、bounded semantic validation、production failure controller / retry feedback / deterministic rendererを使用した。Context/model/settings/rubric/retry policyは変更していない。formal中のtracked file / HEAD / harness / local helper hash不変を記録した。

## 2. Case results

| Case | Terminal | Formal verdict | Retry | Failure |
|---|---|---|---|---|
| 1 Roleplay | ACCEPTED | FAIL | 0 | Unsupported Holy Grail War fact and relationship claims survived validation/rendering. |
| 2 Comparison | REJECTED | FAIL | 1 | Attempt 1 unsupported claim; Attempt 2 missing support refs; unsupported interpretive premises. |
| 3 Creative | REJECTED | FAIL | 1 | Both attempts failed V0 missing visible presentation label. |

Attempt 1を含む全evidenceを保存した。各caseの`rubric.json`でFrozen retrieval/output/critical項目を手動評価し、model自己採点は使用していない。Case 2/3の拒否結果はrenderしなかった。

Formal runは**valid**。SYSTEM/HARNESS defectによる無効化はなく、実行infrastructureを理由とするG-11 reopenは不要。実モデルのgrounding/validation/generation contract failuresを保存した。

## 3. Safety / regression

```text
canonical before SHA-256: 0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d
canonical after SHA-256:  0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d
canonical equal: true
integrity before / after: PASS / PASS
focused grounding pytest: 21 passed / 0 failed
focused read-path pytest: 27 passed / 0 failed
full pytest: 382 passed / 0 skipped / 0 failed (2 local-Qdrant warnings)
ruff: PASS
git diff --check: PASS
start HEAD == end HEAD: true
```

正確なcommandsと結果はacceptance record、全stdout/stderr/exit codeはrun rootの`regression/`に保存。`overall-evaluation.json`と`git-end.json`を完成させた後に、今回のGit-managed documentationを更新した。Raw model output、DB、local evidenceはcommitしない。

## 4. Completion and next action

```text
N-04G-12 = Complete (formal re-acceptance executed)
N-04 = Failed / not Complete
N-05 = blocked
P-06 = Complete (unchanged)
PR #39 = Draft / unmerged
```

3/3 Case PASS条件を満たさないためN-04をCompleteへ変更しない。次はfailure evidenceに基づく別途remediation / 再受入計画の決定。Unsupported clauseのsemantic false acceptance、material claimのstylistic誤分類、interpretation premise validation、visible label生成・retryを検討対象とする。この実行ではsource/test/benchmark/DecisionやFrozen条件を変更せず、追加model/parameter fallbackも行っていない。
