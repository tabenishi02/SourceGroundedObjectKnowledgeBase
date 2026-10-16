# M-03 Codex Handoff

更新日: 2026-10-16

- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-03 [P1] 1 Object標準手順を1ページで実行可能にする`
- Status: **Local acceptance handoff**
- Standard procedure: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Acceptance record: `docs/planning/M03_LOCAL_ACCEPTANCE.md`

---

## Codexへ依頼する内容

Reference Workstation上でM-03のローカル受入を実施する。

必須条件:

- production DBを使用しない。
- Google Drive等の実外部destinationへ書き込まない。
- `.local/m03-acceptance/`等の専用領域にDB / Package / export / incoming / renderを隔離する。
- public CLIは`sgokb`だけを使用し、内部SQLite直接操作・Python REPL・旧`sgokb-package`をworkflow実行手段として使わない。
- 既存validator / migration / Package contractを試験のために弱めない。
- external ChatGPT工程そのものは自動化したとみなさず、post-analysis CLI wiringの検証にはdeterministic valid Object Result fixtureを利用してよい。

実施範囲:

1. checkoutを最新化し、M-03文書を確認する。
2. Windows 11 / PowerShell環境で`sgokb --help`とeditable installを確認する。
3. isolated fresh DBを作り、既存Sample Rawまたはtest fixtureを1件選ぶ。
4. `OBJECT_STANDARD_WORKFLOW.md`どおり、Object add → Source import/process → Association confirmed → Evidence select → Package build/stage/preflight/exportを実行する。
5. current Object Result schemaへ適合するdeterministic Result fixtureを作り、Result receive → validate → review → importを実行する。
6. `object show --knowledge`、`object relations`、`render`、Lexical Searchを確認する。
7. MCP Python SDK v2 clientから`sgokb --db <isolated-db> mcp serve`へstdio接続し、同じObjectのaccepted Knowledgeをreadできることを確認する。
8. local Embedding provider + Vector runtimeが構成済みならSemantic Search / Similarityも確認する。未構成ならoptional skipとして理由を記録する。
9. 可能なら`tests/test_m03_standard_workflow.py`を追加し、network不要のfocused end-to-end testとして上記local pipelineをCLI boundaryから固定する。
10. 変更ファイルのRuffとfocused testsを実行する。既知Package Transfer baseline failureは別件として明示する。
11. 結果を`docs/planning/M03_LOCAL_ACCEPTANCE.md`へ記録する。
12. 必須Gateが全PASSした場合だけ、`KNOWLEDGE_BASE_REDESIGN_TASKS.md`のM-03と`PHASE_M_PREPARATION.md`をCompleteへ更新する。不具合があればCompleteにせず修正・再試験する。
13. 実装・テスト・文書変更をcommitし、GitHubへpushする。

最終報告には、実行した主要command、isolated DB / fixture、各GateのPASS/FAIL、追加修正、test結果、commit SHAを含める。
