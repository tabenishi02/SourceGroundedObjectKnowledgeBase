# Source Grounded Object Knowledge Base — Phase M Preparation

更新日: 2026-10-15

- Status: **Ready**
- Phase: `Phase M — CLI / 操作フロー`
- Previous phase: `Phase L — 旧Prototype移行・削除` — Complete
- Previous closure: `docs/planning/PHASE_L_CLOSURE_AUDIT.md`
- Current task: `M-01 [P0] 新しいObject中心CLIを設計する`
- Working branch: `main`

---

## 1. Phase Mの目的

Phase Mでは、Phase A〜Lで成立したcanonical Source / Evidence / Object / Version / Search / MCPの機能を、日常運用で直接利用できるCLIと1 Object標準操作フローへ整理する。

Phase Mの完了条件は、再設計タスク正本どおり次とする。

> **日常運用で内部DB操作を必要としない。**

Phase Mは新しいKnowledge Modelを設計するPhaseではない。既存のcanonical Application / Repository / Exchange / Retrieval / MCP境界を、operatorが安全・一貫して使える操作面へまとめる。

---

## 2. Phase Lからの引継ぎ状態

Phase LはCompleteであり、M-01開始を妨げるlegacy cleanup残件はない。

確定済み:

- Fragment / old Final / old benchmark / Prototype Search runtimeはactive treeから削除済み。
- Generative LLM runtimeと旧CLI互換surfaceは削除済み。
- migration001/002はactive chainから削除済み。
- fresh DBはmigration003〜016だけから構築する。
- Prototype DB version1/2は非破壊でfail-fast拒否する。
- canonical Source / Evidence / Object / Version / Search / MCP / UPDS境界は維持されている。
- Sample Raw 106件は保持されている。

独立した既知制約:

- `tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch`に既知failureが1件ある。Phase L起因ではなく、M-01のCLI設計を妨げない。
- Ruff既存違反38件は変更対象外に残る。
- `mcp`、`sentence_transformers`等のoptional dependencyを必要とする実runtime試験は環境によりskipされる。

Phase L完了監査:

- `docs/planning/PHASE_L_CLOSURE_AUDIT.md`

---

## 3. Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| M-01 | P0 | **Next** | 新しいObject中心CLIを設計する |
| M-02 | P1 | Pending | 旧CLIとの互換性を決定する |
| M-03 | P1 | Pending | 1 Object標準手順を1ページで実行可能にする |

推奨順序は `M-01 → M-02 → M-03` とする。

M-01でtarget command taxonomy・side-effect境界・exit/output contractを確定し、その後M-02で既存entrypointとの移行方法を決める。M-03は確定したCLIだけを使って標準運用手順を作る。

---

## 4. 現行CLIの棚卸し

### 4.1 `sgokb`

`pyproject.toml`:

```text
sgokb = sgokb.cli:main
```

現行`src/sgokb/cli.py`が提供する操作:

```text
import
process / extract
association list
association suggest
association set
association clear
evidence candidates
evidence select
provenance evidence
status
snapshots
```

主用途:

- Web Capture Bundle → canonical Source / Snapshot import
- Snapshot → Evidence normalization
- Source↔Object association
- Object Evidence Retrieval / Selection
- Evidence provenance
- Source/Snapshotの簡易状態確認

不足:

- Object registry CRUD
- Object read/show
- Class / Alias操作
- Relation操作
- Registry proposal review/apply
- Package / Result操作
- Search / Similarity
- Markdown Render
- MCP server起動
- integrity / derived-index / backup / recovery status

### 4.2 `sgokb-package`

`pyproject.toml`:

```text
sgokb-package = sgokb.package_cli:main
```

現行`src/sgokb/package_cli.py`が提供する操作:

```text
build
stage
preflight
export
detect
receive
receipts
pending-validation
validate-result
import-result
render-markdown
review-result
diff-versions
```

機能はcanonicalだが、Phase G/Hの実装単位を反映した専用entrypointであり、Object中心の日常CLIとしては分断されている。

M-01ではcommand semanticsを再利用しつつ、Object / Package / Result / Search / MCP / Operationsを一貫したtaxonomyへ整理する。

---

## 5. 既存Application / Storageで利用できる能力

### 5.1 Object registry

`ObjectRepository`には少なくとも次が存在する。

```text
create_object
get_object
list_objects
rename_object
set_status
set_primary_class
add_additional_class
remove_additional_class
add_alias
stage_class_proposal
register_relation_type
registry_events
```

M-01ではこれらを直接CLIからDB操作するのではなく、必要なら薄いApplication serviceを置いてoperator-facing contractを固定する。

### 5.2 Knowledge read / Search

`KnowledgeReadApplication`には次のcanonical read surfaceがある。

```text
search_objects
find_similar_objects
get_object
get_objects
get_object_relations
build_context
Evidence Search系read
```

Phase Mの`search` / `similar` / `object show` / 将来のcontext操作は、このtransport-neutral application boundaryを優先して使う。

### 5.3 Package / Result / Render

既存service:

```text
ObjectEvidencePackageBuilder
PackageTransferService
ResultReceiptService
ResultValidationService
ObjectVersionImportService
MarkdownRenderService
DiffReviewService
```

Phase Mでは既存service semanticsを変更せずCLI taxonomyへ配置する。

### 5.4 MCP

`src/sgokb/mcp/server.py`にはread-only server生成とstdio runnerが存在する。

```text
create_read_server(adapter)
run_stdio_server(server)
run_stdio(adapter)
```

不足しているのはoperator-facing composition rootであり、`mcp serve`がRepository / KnowledgeReadApplication / MCPReadAdapter / optional runtime providerをどう構成するかをM-01で決める。

---

## 6. M-01で確定すべきcommand taxonomy

再設計タスク正本が要求する最低限:

```text
object add/list/show
object relate
package build
package export
result validate
result import
Registry proposal review / apply
search
similar
render
mcp serve
```

加えて、既存canonical操作を失わないこと。

```text
source import / process相当
association controls
evidence controls
provenance
status / snapshot inspection
package stage / preflight
result detect / receive / review / list
version diff
```

M-01では、以下のようなnamespace案を比較し、正式taxonomyを決定する。

```text
sgokb source ...
sgokb object ...
sgokb association ...
sgokb evidence ...
sgokb package ...
sgokb result ...
sgokb search ...
sgokb similar ...
sgokb render ...
sgokb mcp serve
sgokb system ...
```

これはPreparation時点の候補であり、M-01のDecisionではない。

---

## 7. M-01の主要設計論点

### 7.1 1 executableへ統合するか

現状は`sgokb`と`sgokb-package`の2 entrypointがある。

M-01でtargetを設計し、M-02で既存`sgokb-package`をどう扱うか決定する。

候補:

1. `sgokb`へ完全統合し、`sgokb-package`を削除する。
2. `sgokb`を正本とし、`sgokb-package`を一時compatibility wrapperとして残す。
3. 2 entrypointを正式に維持する。

Object中心の日常操作というPhase Mの目的からは1または2が有力だが、最終決定はM-01/M-02で行う。

### 7.2 `object relate`の意味

canonical `object_relations`はObject Knowledge Versionに属する。

そのため`object relate`を単純なRegistry mutationとして実装すると、accepted Version immutabilityやObject Result import contractと衝突する可能性がある。

M-01では次を明示する。

- Registry-level relation type管理とKnowledge relationを分ける。
- Knowledge relationを直接CLI mutation可能にするか。
- Result Importを唯一のauthoritative Knowledge relation write pathとするか。
- `object relate`をproposal / candidate operationとして定義するか。

既存Versioning / Result Import境界を壊してはならない。

### 7.3 Object registry mutationとKnowledge Version mutationを分離する

Object name / aliases / class assignment / lifecycle statusはRegistry操作である。

Knowledge Statement / Attribute / RelationはVersioned Knowledgeである。

CLI名が同じ`object` namespaceでも、この2種類のauthoritative writeを混同しない。

### 7.4 Registry proposal review / apply

現行`ObjectRepository`にはproposal stagingがあるが、operator-facing review/apply flowは未完成である。

M-01では少なくとも次を定義する。

```text
proposal list/show
proposal accept/reject
proposal apply
```

acceptとapplyを同一transactionにするか、reviewとmutationを分離するかも決める。

### 7.5 Search runtime composition

`KnowledgeReadApplication`はprovider / vector indexを外部注入する。

CLIでは次を明確化する。

- lexical-only時の依存
- semantic/hybrid時のEmbedding provider設定
- Vector backend選択
- optional dependency不足時の明示error
- cloudへのsilent fallback禁止

### 7.6 MCP composition

`mcp serve`ではread-only contractを維持する。

MCP transportからSQLite/storageへ直接到達させず、

```text
MCP Server
  → MCPReadAdapter
  → KnowledgeReadApplication
  → Retrieval / Repository
```

を維持する。

### 7.7 Side-effect classをCLI仕様に反映する

最低限、操作を次に分類する。

```text
Read-only
Local derived artifact
Canonical authoritative write
External side effect
Maintenance / recovery
```

例:

- `search` / `object show` → Read-only
- `package build` / `render` → Local derived artifact
- `result import` / Object registry mutation → Canonical authoritative write
- `package export` → External side effect
- backup / restore / rebuild → Maintenance / recovery

External side effectやreview-required mutationでは、既存のexplicit acknowledgement思想を維持する。

### 7.8 Output contract

現行CLIはJSON中心である。

M-01では少なくとも次を決める。

- default outputをJSONにするか
- human-readable format optionを持つか
- stdout / stderr境界
- stable machine-readable error shape
- exit code体系
- batch commandのpartial failure表現

MCPや自動化とCLIを併用するため、machine-readable contractを壊さないことを優先する。

### 7.9 Object selector

canonical IDを正本とする。

CLI convenienceとしてname / alias lookupを許可する場合でも、曖昧一致をsilentに解決しない。

候補:

```text
--object <stable-id>
--name <exact-name-or-alias>  # unique時だけ解決
```

M-01でselector ruleを統一する。

---

## 8. Operations系commandの設計対象

再設計タスク正本では次もM-01対象である。

```text
integrity status
Derived Index status
backup status / create
background-job status
rebuild
restore helper
```

Preparation時点ではcommand名を確定しない。

設計原則:

- SQLite正本とDerived Indexを区別する。
- integrity / foreign key / migration versionを確認可能にする。
- Derived Index rebuildをauthoritative Knowledge mutationと混同しない。
- backup/restoreはD-06以降のruntime保全方針に従う。
- restoreは既存DBを暗黙上書きしない。
- long-running jobが導入される場合、status / retry / failure visibilityを持つ。

---

## 9. M-02互換性Taskの実質的scope

L-05で旧Prototype CLIはすでに完全削除されたため、M-02で検討する「旧CLI」は主に次を指す。

```text
現在のsgokb top-level command形
現在のsgokb-package entrypoint
Phase G/H由来のflat package/result action名
```

Fragment / Final / old benchmark commandをdeprecated aliasとして復活させない。

M-02では次を決定する。

- `sgokb-package`を即時廃止するか移行期間を設けるか。
- 現行`import` / `process` / `status` / `snapshots`をnamespaced commandへ移す場合の互換性。
- CLI help / errorで移行先をどう示すか。
- compatibility wrapperを残す場合の削除期限。

---

## 10. M-03標準手順の到達点

M-03では1 Objectについて、内部SQLやPython REPLを使わず1ページで次を実行できる状態にする。

```text
1. Object登録 / 確認
2. Source Captureをimport
3. Normalize → Evidence
4. Source↔Object association確認
5. Evidence selection
6. Package build
7. Package stage / preflight / external export
8. ChatGPT手動分析
9. Result detect / receive
10. Result validate / review
11. Result import
12. accepted Version確認
13. Render
14. Search / Similarity確認
15. MCPからread確認
```

Drive連携等のexternal handoffは、実装済みexchange contractと人間承認境界を維持する。

M-03成果物候補:

```text
docs/operations/OBJECT_STANDARD_WORKFLOW.md
```

operations directoryを新設するかはM-03実施時に決める。

---

## 11. M-01で変更してはいけない境界

Phase Mを理由に次を再設計しない。

- Object / Facet / Relation schema
- Source / Evidence semantics
- accepted Version immutability
- Object Result schema / validation / import contract
- Package external-export approval boundary
- Search Representation / Embedding Space identity
- MCP read-only contract
- SGOKB / UPDS ownership boundary
- migration003〜016

CLIから使いにくいという理由だけでstorage layerのauthoritative semanticsを変えない。

必要なApplication service追加は、既存domain semanticsの薄いoperator-facing boundaryとして行う。

---

## 12. Definition of Ready

- [x] Phase Lはclosure audit済みでComplete。
- [x] 旧Prototype CLI/runtimeは除去済み。
- [x] fresh canonical DB bootstrapが成立している。
- [x] Object registry storage APIが存在する。
- [x] Source / Evidence canonical CLIが存在する。
- [x] Package / Result / Render serviceと専用CLIが存在する。
- [x] Search / Similarityのtransport-neutral Application boundaryが存在する。
- [x] MCP read adapter / stdio serverが存在する。
- [x] M-01〜M-03のTask scopeが正本に定義されている。
- [x] Phase Mで変更してはいけないcanonical境界を識別した。

**Phase MはReady。次TaskはM-01。**

---

## 13. M-01の推奨実施手順

1. current CLI / package CLI / pyproject entrypointを完全棚卸しする。
2. canonical Application / Storage / Exchange / Retrieval / MCPで既に可能な操作をmappingする。
3. operator use caseをRead / Derived / Canonical Write / External Side Effect / Maintenanceに分類する。
4. command namespace候補を2〜3案作り、長所・短所を比較する。
5. `object relate`とRegistry proposalのwrite semanticsを先に確定する。
6. output / error / exit code / selector / config contractを確定する。
7. target command treeをDecisionとして文書化する。
8. M-01の範囲で必要ならCLI skeleton / parser testsを実装する。ただしM-02のcompatibility判断を先取りしない。
9. M-02へentrypoint migration判断を引き継ぐ。

M-01成果物は、少なくともtarget command treeと各commandのside-effect class、入力・出力・authoritative boundaryを第三者が実装可能な粒度で記述する。
