# Source Grounded Object Knowledge Base — Phase M Preparation

更新日: 2026-10-16

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
| M-01 | P0 | **In Progress** | 新しいObject中心CLIを設計する |
| M-02 | P1 | **Complete (2026-10-16)** | 旧CLIとの互換性を決定する |
| M-03 | P1 | **Workflow specified / Blocked by M-01 implementation** | 1 Object標準手順を1ページで実行可能にする |

推奨順序は `M-01 → M-02 → M-03` とする。

M-01でtarget command taxonomy・side-effect境界・exit/output contractを確定し、その後M-02で既存entrypointとの移行方法を決める。M-03は確定したCLIだけを使って標準運用手順を作る。

M-02はM-01のtop-level taxonomy承認後に先行してcompatibility policyだけを確定した。M-01の未承認事項は引き続きIn Progressであり、M-02完了によって暗黙に確定しない。

M-03については、2026-10-16に1 Object標準workflowを`docs/operations/OBJECT_STANDARD_WORKFLOW.md`へ1ページで定義した。ただし現在のactive CLIにはObject登録、Search / Similarity、operator-facing MCP起動など必要routeがまだ揃っていないため、M-01 implementation cutoverまでは「実行可能」条件を満たさずComplete扱いにしない。

### M-01で承認済みの部分Decision

2026-10-16に、CLIのtop-level taxonomyとして**Domain namespace方式（案A）**を採用した。

Decision:

- `docs/decisions/M01_CLI_NAMESPACE_TAXONOMY.md`

基本形:

```text
sgokb source ...
sgokb object ...
sgokb association ...
sgokb evidence ...
sgokb registry ...
sgokb package ...
sgokb result ...
sgokb version ...
sgokb search ...
sgokb similar ...
sgokb render ...
sgokb mcp ...
sgokb system ...
```

M-01全体はまだ未完了であり、各namespace配下の最終command、side-effect境界、Output / Error / Exit contract、selector、Registry proposal、Relation write boundary等は引き続き承認待ちである。

### M-02で確定したCompatibility Decision

2026-10-16に、旧CLIとの互換性について次を確定した。

Decision:

- `docs/decisions/M02_CLI_COMPATIBILITY_POLICY.md`

要点:

- deprecated execution compatibilityを長期維持しない。
- 新しいDomain namespace側の同等operationを実装・検証した変更と同じcutoverで、対応する旧command / aliasを削除する。
- 将来のpublic CLI entrypointは`sgokb` 1本とする。
- `sgokb-package`はPackage / Result等の移行完了時に削除し、deprecated wrapperとして残さない。
- Phase Lで削除済みのFragment / Final / old benchmark等のPrototype CLIは復活させない。
- CLI pathをbreaking changeとして切っても、canonical Source / Evidence / Package / Result / Version / Search / MCP semanticsは維持する。
- M-01で未確定の最終subcommand名、Output / Error / Exit contract等はM-02では確定しない。

### M-03標準workflow

標準運用の正本:

- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`

固定した工程:

```text
Object登録 / 確認
→ Source Capture import
→ Normalize / Evidence
→ Source↔Object association確認
→ Evidence selection
→ Package build
→ stage / preflight / explicit export
→ ChatGPT手動分析
→ Result detect / receive
→ validate / review
→ explicit Result import
→ accepted Version
→ render
→ Object / Search / Similarity確認
→ MCP read確認
```

Human decision boundaryとして、Object Identity、External Export、ChatGPT外部工程、authoritative Result Import、review-required Result、Registry proposalを自動通過させない。

M-03をCompleteへ移すGateは、M-01で必要routeが実装され、`sgokb-package`を使わず新`sgokb`だけで上記workflowを完走でき、focused integration testが成功することである。

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

M-02のDecisionにより、`sgokb-package`は将来のpublic contractとして維持せず、新`sgokb`側へ同等operationが移行したcutoverで削除する。

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

## 6. M-01 command taxonomy

### 6.1 採用済みtop-level taxonomy

**Domain namespace方式（案A）を採用済み。**

```text
sgokb source ...
sgokb object ...
sgokb association ...
sgokb evidence ...
sgokb registry ...
sgokb package ...
sgokb result ...
sgokb version ...
sgokb search ...
sgokb similar ...
sgokb render ...
sgokb mcp ...
sgokb system ...
```

詳細な根拠と不採用案は `docs/decisions/M01_CLI_NAMESPACE_TAXONOMY.md` を正本とする。

### 6.2 正本タスクが要求する最低限

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

各操作を採用済みDomain namespaceへどう配置するか、最終command名をどうするかはM-01の残りの設計判断で確定する。