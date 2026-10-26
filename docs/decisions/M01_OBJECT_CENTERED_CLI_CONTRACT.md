# M-01 Object-centered CLI Contract

更新日: 2026-10-16

- Status: **Accepted / Implemented**
- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-01 [P0] 新しいObject中心CLIを設計・実装する`
- Supersedes the partial/non-decision portions of: `M01_CLI_NAMESPACE_TAXONOMY.md`
- Compatibility policy: `M02_CLI_COMPATIBILITY_POLICY.md`

---

## 1. Decision

SGOKBのoperator-facing CLIは、public entrypointを`sgokb` 1本へ統一し、M-01で承認済みのDomain namespace方式を最終contractとする。

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

旧`sgokb-package` entrypointはM-02のatomic cutover policyに従い削除する。旧flat commandやdeprecated aliasを新CLIのwrapperとして残さない。

---

## 2. Command surface

### Source

```text
sgokb source import <path>
sgokb source process [--snapshot <id>]
sgokb source status
sgokb source snapshots
sgokb source select-snapshot --source <source-id> --snapshot <snapshot-id> --reason <text>
sgokb source select-run --snapshot <snapshot-id> --run <run-id> --reason <text>
```

旧`extract` aliasは廃止する。

後続Snapshot / Normalization Runは新しいという理由だけで自動effective化しない。operatorが内容を確認した後、`select-snapshot` / `select-run`を明示実行してappend-only selection eventを記録する。両commandはcanonical stateを変更する`WRITE`操作であり、`--reason`を必須とする。

### Object

```text
sgokb object add --name <name> --primary-class <class> [--alias <value> ...]
sgokb object list
sgokb object show (--object <id> | --name <exact>) [--knowledge] [--version <id>]
sgokb object rename (--object <id> | --name <exact>) --to <name>
sgokb object status (--object <id> | --name <exact>) --set active|archived

sgokb object alias list (--object <id> | --name <exact>)
sgokb object alias add (--object <id> | --name <exact>) <value>

sgokb object class set-primary (...) <class>
sgokb object class add (...) <class>
sgokb object class remove (...) <class>

sgokb object events (...)
sgokb object relations (...) [--version <id>] [--no-evidence]
```

### Association / Evidence

```text
sgokb association list|suggest|set|clear ...

sgokb evidence candidates ...
sgokb evidence select ...
sgokb evidence show <evidence-id>
sgokb evidence provenance <evidence-id>
sgokb evidence search <query> ...
```

### Registry

```text
sgokb registry class list|show ...
sgokb registry relation-type list|show ...
sgokb registry proposal list|show ...
sgokb registry proposal accept <proposal-ref> [--note ...]
sgokb registry proposal reject <proposal-ref> [--note ...]
sgokb registry proposal apply <proposal-ref>
```

### Package / Result / Version / Render

```text
sgokb package build ...
sgokb package stage ...
sgokb package preflight ...
sgokb package export ...

sgokb result detect ...
sgokb result receive ...
sgokb result list ...
sgokb result pending
sgokb result validate <receipt-id>
sgokb result review <receipt-id>
sgokb result import <receipt-id>

sgokb version show <version-id>
sgokb version diff <before> <after>

sgokb render (--object <id> | --version <id>)
```

### Search / Similarity / MCP

```text
sgokb search <query> [--mode lexical|semantic|hybrid] ...
sgokb similar (--object <id> | --name <exact>) ...
sgokb mcp serve [--semantic-runtime]
```

### System

```text
sgokb system status
sgokb system integrity
sgokb system index status
sgokb system index rebuild
sgokb system backup status
sgokb system backup create
sgokb system restore plan <backup>
sgokb system restore apply <backup> [--acknowledge-overwrite]
```

durable background-job runtimeが存在しないため、実体のない`job status` commandは導入しない。

---

## 3. Object selector contract

Persistent `object_id`をauthoritative selectorとする。

```text
--object <stable-object-id>
```

人間操作の便宜として次を許可する。

```text
--name <exact-canonical-name-or-alias>
```

`--name`はexact matchのみとし、fuzzy selectionは行わない。canonical name / aliasで一意に解決できない場合はerrorとする。write operationは解決後のstable Object IDを対象に実行する。

---

## 4. Relation write boundary

`object relate`によるaccepted Knowledge Relationの直接書込みは**採用しない**。

理由:

- RelationはObject Result schema上Evidence groundingを必要とする。
- accepted Relationはimmutable Object Knowledge Versionの一部である。
- 直接Object RegistryへRelationを書き込むと、Result Validation / Version Import / Evidence Link境界を迂回する。

したがってRelationは次の境界とする。

```text
Read:
  sgokb object relations ...

Write:
  Package → Object Result → validate/review → sgokb result import
```

正本計画にあった`object relate`は、このVersion/Evidence contractとの整合を優先して置換する。

---

## 5. Side-effect classes

operatorがcommandの危険度を判断できるよう、操作を論理的に次へ分類する。

| Class | 意味 | 代表例 |
|---|---|---|
| `READ` | canonical stateを変更しない | `object show`, `search`, `similar`, `system integrity` |
| `DERIVED` | 正本から再生成可能なartifact/indexを変更 | `package build`, `render`, `system index rebuild` |
| `WRITE` | canonical SQLite stateを変更 | `object add`, `association set`, `result import`, `registry proposal apply` |
| `EXTERNAL` | SGOKB外へdataを送出 | `package export` |
| `MAINTENANCE` | 保全・復旧操作 | `backup create`, `restore apply` |

CLI routeは既存Application / Service / Repository contractを利用し、raw SQLをoperator-facing APIとして公開しない。

---

## 6. Output / Error contract

machine-readable既定形式をJSONとし、contract versionを固定する。

```text
sgokb.cli/1.0
```

成功:

```json
{
  "schema_version": "sgokb.cli/1.0",
  "ok": true,
  "command": "object.show",
  "data": {},
  "warnings": []
}
```

error:

```json
{
  "schema_version": "sgokb.cli/1.0",
  "ok": false,
  "command": "object.show",
  "error": {
    "code": "object_selector_error",
    "message": "...",
    "details": {}
  }
}
```

- normal resultはstdoutへ出力する。
- errorはstderrへ出力する。
- `--format text`は人間向け表示でありstable machine contractとはしない。
- Hybrid Search等のgraceful degradationは`warnings`へ明示する。

---

## 7. Exit codes

```text
0  success
1  unexpected internal error
2  invalid CLI/input request
3  not found / selector ambiguity
4  blocked / unmet precondition / review acknowledgement required
5  optional retrieval/provider/runtime unavailable
6  I/O / external/provider operation failure
7  integrity / consistency failure
8  batch partial failure
```

batch Source Import / Processはitem単位の結果を返し、一部失敗時は8とする。

---

## 8. Registry proposal contract

Object Resultの`registry_proposals`はKnowledge Importの副作用として自動適用しない。

```text
Result Import
  ↓
proposal pending
  ↓
Human accept / reject
  ↓
accepted proposal only
  ↓
explicit apply
```

M-01ではMigration 017 `registry_proposal_reviews`を追加し、operator decisionとapply auditを保持する。

対象proposal kind:

```text
object_name
object_alias
primary_class
additional_class
new_class
new_facet
new_attribute
new_relation_type
```

`accept`は人間判断の記録、`apply`は別のcanonical mutationとする。apply済みproposalは再実行してもduplicateとして扱い、silent二重適用しない。

---

## 9. Search / Similarity runtime

Lexical readはlocal SQLiteだけで成立する。

Semantic / Hybrid / Similarityでfull semantic runtimeを使用する場合は、Phase Iで固定したlocal Embedding provider + Qdrant runtimeを明示的にcompositionする。

```text
--semantic-runtime
```

Hybrid Searchはsemantic channel障害時にLexicalへdegrade可能だが、`warnings`に`degraded_channels`を公開する。

完全runtimeを要求するautomation向けに次を提供する。

```text
--require-full-runtime
```

この場合、runtime不足またはdegradationはexit 5とする。local provider failureからcloud providerへsilent fallbackしない。

---

## 10. MCP composition root

operator-facing起動commandを次へ固定する。

```text
sgokb mcp serve
```

compositionは次とする。

```text
Repository
  → KnowledgeReadApplication
  → MCPReadAdapter
  → read-only MCP Server
  → stdio
```

MCP transportからSQLiteへ直接アクセスしない。J-05のread-only MVP boundaryを維持する。

---

## 11. System operations

### Integrity

`system integrity`は少なくともSQLite `integrity_check`、foreign-key integrity、applied migration集合を確認する。

### Derived index

`system index status`はcanonical derived-state / Embedding Space状態を表示し、`system index rebuild`はSQLite正本からVector Indexを再生成する。

### Backup / Restore

backupはSQLite backup APIで取得後にintegrity checkを行う。

restoreは先に`plan`を提供し、既存target DBを上書きする場合は次を必須とする。

```text
--acknowledge-overwrite
```

silent overwriteを禁止する。

---

## 12. M-02 compatibility cutover

`pyproject.toml`のpublic scriptは`sgokb`のみとする。

```text
sgokb = "sgokb.cli:main"
```

`sgokb-package`を削除し、旧`src/sgokb/package_cli.py`と旧flat `src/sgokb/cli.py`を新`src/sgokb/cli/` packageへ統合した。

旧command aliasをdeprecated wrapperとして保持しない。既存canonical semanticsは新Domain namespaceへ移し、既存回帰テストも新route / `sgokb.cli/1.0` envelopeへ移行する。

---

## 13. Implementation artifacts

主要実装:

```text
src/sgokb/cli/__init__.py
src/sgokb/cli/main.py
src/sgokb/cli/contracts.py
src/sgokb/cli/runtime.py
src/sgokb/application_admin.py
src/sgokb/system_ops.py
src/sgokb/storage/registry_proposal_repository.py
src/sgokb/migrations/017_cli_registry_proposal_reviews.sql
```

主要回帰:

```text
tests/test_m01_cli.py
```

加えて、旧CLI entrypointを直接試験していた既存Package/Render/Review/Source/Association/Evidenceテストを新`sgokb` contractへ移行する。

---

## 14. Non-goals

M-01では次を再設計しない。

- Object / Facet / Relation data model
- Source / Evidence semantics
- accepted Version immutability
- Object Result schema / Validation / Import semantics
- Package external-export approval boundary
- Search Representation / Embedding Space identity
- MCP read-only policy
- SGOKB / UPDS ownership boundary

M-01はそれらのcanonical capabilityを安全に操作するoperator-facing interfaceを完成させるTaskである。
