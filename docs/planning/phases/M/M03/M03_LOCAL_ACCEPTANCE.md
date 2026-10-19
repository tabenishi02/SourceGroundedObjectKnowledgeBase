# M-03 Local Acceptance Plan

更新日: 2026-10-16

- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-03 [P1] 1 Object標準手順を1ページで実行可能にする`
- Status: **Complete (2026-10-16)**
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


---

## 6. Reference Workstation 受入結果

- 実施日時: 2026-10-16 14:56–15:00 JST
- OS / Python: Windows 11 Home build 26300 / Python 3.10.6 / PowerShell
- branch: `task/m-03-local-acceptance`
- baseline: `5e1467a037730e40f50d52fd3f38c270c7b1c45c`
- 検証対象の実装・test commit: `aa0e7d824e934419914d35e0decde309dc1fd7e1`
- editable install: `python -m pip install --no-build-isolation -e ".[dev,mcp]"` 成功。古いpipを更新して再導入した。MCP Python SDKは2.3.0。
- isolated DB: `.local/m03-acceptance/verified/test_standard_workflow_mcp_read/acceptance.sqlite`
- fixture: `tests/conftest.py::make_bundle`で生成したsynthetic Web Capture。本文は「M03 Example is a brave fictional character.」。元fixtureを保持して隔離領域の`raw/`へコピー。
- DB / Package build / staging / export / incoming / render / pytest一時領域はすべて`.local/m03-acceptance/`配下。production DBと実Google Driveへアクセスしていない。

| Gate | 結果 | 確認内容 |
|---|---|---|
| sgokb entrypoint | PASS | editable install、`sgokb --help`、public scriptは`sgokb`のみ |
| Fresh DB / integrity | PASS | public `system integrity`でmigration003〜017、integrity / foreign-key check成功 |
| Object → Evidence | PASS | add/show、Source import/process、association confirmed、candidates/select |
| Package | PASS | build/stage/preflight（allow）後、隔離した一時destinationへ明示export |
| Result | PASS | detect/receive/validate（valid）/Markdown review後、明示import |
| accepted Object read | PASS | `object show --knowledge`がaccepted Versionを解決。pending proposalなし |
| Relations / Render | PASS | relations read、accepted VersionのMarkdown artifact生成・内容確認 |
| Lexical Search | PASS | public lexical search結果に対象Objectあり |
| MCP stdio read | PASS | SDK v2 client → `sgokb --db <isolated-db> mcp serve` → `get_object`。CLI Knowledge全体と一致 |
| MCP write boundary / shutdown | PASS | 8 toolsすべてread-only、許可したtool集合と一致、前後のDB SHA-256不変。子process停止後もCLI read成功 |
| Semantic Search | SKIP | optional runtime unavailable。local-embeddingとvector-qdrant未導入、未構成。修正後の公開CLIはexit5 |
| Similarity | SKIP | 同上。修正後の公開CLIはexit5 |

外部ChatGPTの手動分析や分析品質は検証していない。Packageのbinding / Evidence ID / instructionsの有効Facet一覧に従うdeterministic Object Result fixtureを作成し、通常のValidation / Review / Importを通した。validator、migration、Package contractは変更していない。直接SQLite、Python REPL、旧`sgokb-package`をworkflow実行手段として使っていない。

### 主要コマンドと識別子

`sgokb --db <isolated-db>`を各commandの先頭に付け、次を順番に実行した。必須CLI 26回はすべてexit0。fixture作成以外のcanonical操作は公開CLI経由。

```text
system integrity / registry class show character
object add --name "M03 Example" --primary-class character
object show --object <ObjectId>
source import <RawBundle> / source process --snapshot <SnapshotId>
association list --object <ObjectId>
association set --object <ObjectId> --source <SourceId> --status confirmed
evidence candidates --object <ObjectId> / evidence select --object <ObjectId>
package build --object <ObjectId> --build-root <Root>/build
package stage <BuildPath> --staging-root <Root>/staging
package preflight <StagedPath> --destination <Root>/external-destination
package export <StagedPath> --destination <Root>/external-destination
result detect --incoming-root <Root>/incoming
result receive <ResultPath> --package-id <PackageId> --incoming-root <Root>/incoming
result validate <ReceiptId> --incoming-root <Root>/incoming
result review <ReceiptId> --incoming-root <Root>/incoming --review-format markdown
result import <ReceiptId> --incoming-root <Root>/incoming
object show --object <ObjectId> --knowledge
object relations --object <ObjectId>
render --object <ObjectId> --output-root <Root>/render
search "M03 Example" --mode lexical
registry proposal list --decision pending / system integrity
mcp serve  # SDK v2 clientでget_object、終了後にobject show --knowledgeを再確認
```

`<Root>`は上記isolated DBの親directory。Package exportもResult importも明示操作として実行した。review-requiredな内容の自動承認は行っていない。

| ID | 値 |
|---|---|
| object_id | `f1f78f9a-d214-4b3d-876b-c58a022c2409` |
| source_id | `ecd7fb87-d892-4585-97fc-294c278056b1` |
| snapshot_id | `517a63c9-0746-47dd-a262-034148de61bf` |
| package_id | `pkg_a29e4186-2f39-4902-9d06-30750053cc3e` |
| receipt_id | `60da6b9c-40c4-47fd-9d23-d23f7846a32e` |
| version_id | `75c0b393-b736-49de-870a-375eeb9cb269` |

### Test / findings

- `tests/test_m03_standard_workflow.py`: **2 passed**（修正後30.13秒）。公開CLI subprocessのみで全工程を通し、同じ新規Objectを実MCP stdio clientで読んだ。
- M-01 / Source / Evidence / Package / Result / Version / Diff Review / Render / J-06関連回帰: **153 passed, 1 deselected**。既知failureだけを分離。
- exit-code修正後の`tests/test_m01_cli.py`: **12 passed**（依存不足4経路と予期しない内部errorを隠さない確認を含む）。
- 変更Python 3 filesの`ruff check` / `ruff format --check`: **PASS**。
- `git diff --check`: **PASS**。
- 既知baselineを単独実行: **1 failed**。期待`SHA-256 mismatch`に対し実際`Package file size mismatch: evidence/source_001.md`。従来と同じ独立した既知failureで、変更していない。
- 発見・修正: optional Semantic/Similarity依存不足がexit1になった。CLI compositionでImportErrorまたはそれを原因とするRuntimeErrorだけを`RetrievalRuntimeUnavailableError`へ変換し、contract通りexit5とした。一般のRuntimeErrorはそのまま扱う。修正後に新規DBで同じworkflow全体を再実行し、全必須GateがPASS。
- fixture準備ではCapture filenameを保持し、instructionsの全必須Facetを`not_analyzed`として含めた。初期fixture不備を修正しただけで、検証規則は緩和していない。
- 詳細証跡（Git管理外）: `.local/m03-acceptance/focused-final.log`、`regression.log`、`known-baseline.log`、および`verified/test_standard_workflow_mcp_read/`の`commands.json` / `ids.json` / `mcp-read.json` / `optional-runtime.json`。端末固有pathを含むログはcommit対象外。

**判定: M-03 Complete / Phase M Complete。日常運用で内部DB操作を必要としない。** Semantic/Similarity runtimeの導入とChatGPT手動分析品質評価は、この受入の実施済み範囲に含めない。
