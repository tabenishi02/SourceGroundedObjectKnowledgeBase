# M-03 Local Acceptance Plan

更新日: 2026-10-16

- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-03 [P1] 1 Object標準手順を1ページで実行可能にする`
- Status: **Pending local execution**
- Standard procedure: `docs/operations/OBJECT_STANDARD_WORKFLOW.md`
- Reference environment: Windows 11 / PowerShell / local SGOKB checkout

---

## 1. 目的

`OBJECT_STANDARD_WORKFLOW.md`に記載した1 Object標準手順が、Reference Workstation上で実際に次の条件を満たすことを確認する。

- public entrypointは`sgokb`だけを使用する。
- production DBや既存運用dataを変更しない隔離環境で検証する。
- Source Import → Normalize → Association → Evidence → Package → Result → accepted Version → Render → Searchをend-to-endで確認する。
- Package Export / Result Importの明示Human boundaryを維持する。
- MCPはstdio read-only clientから確認する。
- Semantic/Similarity runtimeは構成済みの場合だけ追加確認し、未構成ならoptional skipとして記録する。

---

## 2. 安全条件

ローカル受入では次を必須とする。

1. production DBを使わない。
2. Google Drive等の実外部destinationへ書き込まない。
3. `.local/m03-acceptance/`等の専用領域へDB、Package、export、incoming、renderを隔離する。
4. 既存Sample Rawまたはtest fixtureを入力に使用し、元ファイルを変更しない。
5. 既存migration / validator / Package contractを受入のために弱めない。
6. 既知のPackage Transfer test 1件はM-03とは別issueとして扱い、結果を隠さない。

---

## 3. 必須ローカル確認

### A. Environment / entrypoint

- local checkoutを最新`main`またはM-03作業branchへ同期する。
- editable installを確認する。
- `sgokb --help`が成功する。
- `pyproject.toml`のpublic scriptが`sgokb`のみであることを確認する。
- 旧`sgokb-package`をM-03 workflowで使用しない。

### B. Isolated 1 Object workflow

`docs/operations/OBJECT_STANDARD_WORKFLOW.md`をそのまま辿り、少なくとも次を確認する。

```text
Object add/show
→ Source import/process
→ Association confirmed
→ Evidence candidates/select
→ Package build/stage/preflight/export
→ Result receive/validate/review/import
→ Object show --knowledge
→ object relations
→ render
→ lexical search
```

外部ChatGPT工程そのものはlocal automated testへ偽装しない。post-analysis pathの受入には、現在のObject Result schemaに適合するdeterministic fixtureを使用してよい。fixtureは「ChatGPT品質を検証した」と解釈せず、Result transport / validation / importのCLI wiring確認だけに使う。

### C. MCP read

- optional dependency `mcp`を利用可能にする。
- stdio child processとして次を起動する。

```text
sgokb --db <isolated-db> mcp serve
```

- MCP clientから最低1回Object readを行う。
- CLI `object show --knowledge`で解決したstable `object_id` / accepted Versionと一致することを確認する。
- MCPからwrite operationが露出していないことを維持する。

### D. Semantic / Similarity — optional runtime

Reference Workstationでlocal Embedding provider + Vector runtimeが構成済みなら次も実行する。

```text
sgokb --db <isolated-db> search <query> --mode semantic --semantic-runtime --require-full-runtime
sgokb --db <isolated-db> similar --object <object-id>
```

未構成の場合は`optional runtime unavailable`としてskip理由を記録する。M-03必須GateはLexical Search + MCP readまでとする。

---

## 4. Focused integration test

可能なら`tests/test_m03_standard_workflow.py`を追加し、network不要・production data不要で次をCLI boundaryから確認する。

1. isolated fresh DBを作る。
2. test Web Capture Bundleをimport / processする。
3. Objectを作りSource associationを`confirmed`へする。
4. Evidence selectionからPackageをbuild / stage / preflightする。
5. temp directoryへexplicit exportする。
6. current Object Result schemaへ適合するdeterministic Result fixtureを作る。
7. Resultをreceive / validate / review / importする。
8. `object show --knowledge`でcurrent accepted Versionを確認する。
9. render artifact生成を確認する。
10. lexical searchで対象Objectを取得する。
11. direct SQLite mutation、`sgokb-package`、Generative LLM APIを使用しない。

MCP subprocess readは既存J-06 acceptance coverageを再利用してもよいが、M-03のisolated DB / Objectを直接読めるfocused checkを追加できるなら優先する。

---

## 5. 実行後の記録

受入完了後、この文書のStatusを`Complete`へ変更し、以下を追記する。

```text
実施日時:
OS / Python:
branch / commit:
DB path (isolated):
input fixture:

sgokb entrypoint: PASS/FAIL
Object → Evidence: PASS/FAIL
Package build/stage/preflight/export: PASS/FAIL
Result receive/validate/review/import: PASS/FAIL
accepted Object read: PASS/FAIL
Render: PASS/FAIL
Lexical Search: PASS/FAIL
MCP stdio read: PASS/FAIL
Semantic Search: PASS / SKIP / FAIL
Similarity: PASS / SKIP / FAIL
Focused integration test: <result>
Ruff changed files: <result>
Known unrelated baseline: <result>

Findings / fixes:
- ...
```

必須項目がすべてPASSした場合のみ、次も更新する。

- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`のM-03を`[x] Complete`へ変更する。
- `docs/planning/PHASE_M_PREPARATION.md`をPhase M Completeへ更新する。
- Phase Mの完了条件「日常運用で内部DB操作を必要としない」を満たしたことを明記する。

不具合が見つかった場合は、M-03を完了扱いせず修正・再試験する。
