# Source Grounded Object Knowledge Base — Phase M Preparation

更新日: 2026-10-16

- Status: **Complete (2026-10-16)**
- Phase: `Phase M — CLI / 操作フロー`
- Previous phase: `Phase L — 旧Prototype移行・削除` — Complete
- Previous closure: `docs/planning/PHASE_L_CLOSURE_AUDIT.md`
- Current task: なし（M-01〜M-03 Complete）
- M-01 implementation branch: `task/m-01-object-centered-cli`

---

## 1. Phase Mの目的

Phase Mでは、Phase A〜Lで成立したcanonical Source / Evidence / Object / Version / Search / MCPの機能を、日常運用で直接利用できるCLIと1 Object標準操作フローへ整理する。

Phase Mの完了条件は次とする。

> **日常運用で内部DB操作を必要としない。**

Phase MはKnowledge Modelを再設計するPhaseではない。既存のcanonical Application / Repository / Exchange / Retrieval / MCP境界を、operatorが安全・一貫して使える操作面へまとめる。

---

## 2. Phase Lからの引継ぎと現在状態

Phase LはCompleteであり、legacy cleanup残件はPhase Mを妨げない。

確定済み:

- Fragment / old Final / old benchmark / Prototype Search runtimeはactive treeから削除済み。
- Generative LLM runtimeと旧Prototype CLI互換surfaceは削除済み。
- migration001/002はactive chainから削除済み。
- M-01でmigration017を追加したため、fresh canonical DBはmigration003〜017から構築する。
- Prototype DB version1/2は非破壊でfail-fast拒否する。
- canonical Source / Evidence / Object / Version / Search / MCP / UPDS境界は維持する。
- Sample Raw 106件は保持する。

独立した既知制約:

- `tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch`に既知failureが1件ある。期待messageが`SHA-256 mismatch`であるのに、実装は先に`Package file size mismatch`を返す既存差異であり、M-01起因ではない。
- repository全体には既存Ruff違反が残る。M-01変更対象コードのRuffは成功している。
- `mcp`、semantic embedding runtime等のoptional dependencyを必要とする実runtime試験は環境によりskipされる。

---

## 3. Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| M-01 | P0 | **Complete (2026-10-16)** | 新しいObject中心CLIを設計・実装する |
| M-02 | P1 | **Complete (2026-10-16)** | 旧CLIとの互換性を決定する |
| M-03 | P1 | **Complete (2026-10-16)** | 1 Object標準手順を1ページで実行可能にする |

実施順序は `M-01 → M-02 → M-03` とする。

M-01でObject中心CLIのtaxonomy、side-effect境界、Output / Error / Exit contract、selector、Registry proposal、Search/MCP/System compositionを確定し、実装した。M-02では旧entrypointの互換方針を確定し、M-01 cutoverで`sgokb-package`を削除した。

M-03の標準workflow自体は`docs/operations/OBJECT_STANDARD_WORKFLOW.md`へ定義済みである。新しい`sgokb`だけを使った1 Object end-to-end実行とMCP stdio readが成功し、Phase M完了Gateを満たした。受入結果は`docs/planning/M03_LOCAL_ACCEPTANCE.md`を参照する。

---

## 4. M-01 完了内容

M-01の設計・実装正本:

- `docs/decisions/M01_CLI_NAMESPACE_TAXONOMY.md`
- `docs/decisions/M01_OBJECT_CENTERED_CLI_CONTRACT.md`

### 4.1 Public entrypoint

public CLIは1本に統一した。

```text
sgokb = sgokb.cli:main
```

旧`sgokb-package` entrypointはM-02 Decisionに従いcutoverと同時に削除した。deprecated wrapperは残さない。

### 4.2 Domain namespace

採用したtop-level taxonomy:

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

基本原則は `sgokb <domain> <action>` とする。

### 4.3 実装済みcommand surface

```text
source
  import
  process
  status
  snapshots

object
  add
  list
  show
  rename
  status
  alias list/add
  class set-primary/add/remove
  events
  relations

association
  list
  suggest
  set
  clear

evidence
  candidates
  select
  provenance
  search

registry
  class list/show
  relation-type list/show
  proposal list/show/accept/reject/apply

package
  build
  stage
  preflight
  export

result
  detect
  receive
  list
  pending
  validate
  review
  import

version
  show
  diff

search
similar
render

mcp
  serve

system
  status
  integrity
  index status/rebuild
  backup status/create
  restore plan/apply
```

### 4.4 Object selector

stable Object IDをauthoritative selectorとする。

```text
--object <stable-object-id>
--name <exact-canonical-name-or-alias>
```

`--name`はcanonical name / aliasへの完全一致かつ一意解決時のみ許可する。曖昧な場合はexit 3で停止し、fuzzy resolutionをwrite操作へ使用しない。

### 4.5 Output / Error / Exit contract

通常commandのmachine-readable output contractは`sgokb.cli/1.0`とする。

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

失敗:

```json
{
  "schema_version": "sgokb.cli/1.0",
  "ok": false,
  "command": "object.show",
  "error": {
    "code": "object_not_found",
    "message": "Object was not found",
    "details": {}
  }
}
```

- 正常結果: stdout
- error / diagnostic: stderr
- `--format json`: stable machine contract
- `--format text`: human-oriented、stable APIとはみなさない

exit code:

```text
0 success
1 unexpected internal error
2 CLI / input error
3 not found / selector ambiguity
4 precondition / review-required / blocked
5 optional runtime/provider unavailable
6 I/O / external-operation failure
7 integrity / consistency error
8 batch partial failure
```

`sgokb mcp serve`だけは例外で、stdoutをMCP stdio transport専用とし、CLI JSON envelopeを混在させない。

### 4.6 Side-effect境界

commandを次の5分類で扱う。

```text
READ         canonical stateを変更しない
DERIVED      再生成可能artifact/indexのみ変更
WRITE        canonical SQLiteを変更
EXTERNAL     external destinationへ副作用を発生
MAINTENANCE  backup / restore等の保守操作
```

CLIはRepositoryのraw DB操作を直接operator contractとして公開せず、既存Application/serviceまたはM-01で追加した薄いApplication境界を利用する。

### 4.7 Relation write boundary

旧計画にあった`object relate`は**実装しない**。

理由:

- accepted RelationはObject Knowledge Versionの一部である。
- RelationはEvidence groundingを必須とする。
- direct Registry-style writeではVersion / Evidence / Result Import境界を迂回してしまう。

したがって:

```text
sgokb object relations   # read-only
```

を提供し、Relationのauthoritative writeは次だけに限定する。

```text
Package
→ Object Result
→ result validate / review
→ explicit result import
→ accepted Version
```

### 4.8 Registry proposal review / apply

Object Result内の`registry_proposals`はResult Import時に自動適用しない。

```text
AI proposal
→ Result Importでproposal metadataを保持
→ operator accept / reject
→ accepted proposalだけexplicit apply
```

M-01ではmigration017と`RegistryProposalRepository`を追加し、review decisionとapply結果を監査可能にした。対応kind:

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

ChatGPT分析instructionsもv1.1へ更新し、各proposal kindの標準payload形を定義した。

### 4.9 Search / Similarity

Search / Similarityは`KnowledgeReadApplication`をcanonical read boundaryとして利用する。

Object Search:

```text
sgokb search "query" --mode lexical
sgokb search "query" --mode semantic --semantic-runtime
sgokb search "query" --mode hybrid --semantic-runtime
```

Hybrid Searchはsemantic runtime障害時に既存contractどおりdegraded channelを返せる。`--require-full-runtime`指定時はdegradationを成功扱いせずexit 5とする。

Embedding providerは明示構成し、silent cloud fallbackを行わない。

### 4.10 MCP

operator-facing起動route:

```text
sgokb mcp serve
```

composition:

```text
Repository
→ KnowledgeReadApplication
→ MCPReadAdapter
→ read-only MCP Server
→ stdio
```

MCP transportからSQLiteを直接操作せず、既存J-05 write boundaryを維持する。

### 4.11 System operations

追加したoperator-facing保守route:

```text
sgokb system status
sgokb system integrity
sgokb system index status
sgokb system index rebuild
sgokb system backup status
sgokb system backup create
sgokb system restore plan
sgokb system restore apply
```

`restore apply`は既存target DBをsilent overwriteせず、明示acknowledgementを要求する。

durable background job runnerは現在存在しないため、実体のない`job status` commandは追加しない。必要になった時点でruntimeと同時に設計する。

---

## 5. M-01 validation

2026-10-16、GitHub Actions上のPython 3.12環境で検証した。

結果:

```text
M-01 focused tests: 45 passed
M-01 changed-code Ruff: All checks passed
full suite excluding known unrelated baseline: 292 passed / 4 skipped / 1 deselected
known Package Transfer baseline: 1 failed (expected existing failure)
```

focused範囲には次を含む。

- Object-centered CLI / JSON contract / selector
- Source pipeline CLI migration
- Association / Evidence CLI migration
- MCP stdio output boundary
- Registry proposal accept / reject / apply
- Object analysis instruction contract
- migration017 / integrity check
- `sgokb-package` entrypoint removal

既知Package Transfer failureはM-01前から存在する同一事象であり、M-01回帰とは扱わない。

---

## 6. M-02 Compatibility Decision

正本:

- `docs/decisions/M02_CLI_COMPATIBILITY_POLICY.md`

確定事項:

- deprecated execution compatibilityを長期維持しない。
- public CLIは`sgokb` 1本とする。
- `sgokb-package`は新`sgokb`側へoperationが移行したcutoverで削除する。
- Phase Lで削除済みのPrototype CLIは復活させない。
- breaking CLI path変更を許可してもcanonical Source / Evidence / Package / Result / Version / Search / MCP semanticsは維持する。

M-01実装でこのcutoverを実施済みである。

---

## 7. M-03 標準workflow

標準運用の正本:

- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`

工程:

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
→ accepted Version確認
→ render
→ Object / Search / Similarity確認
→ MCP read確認
```

Human decision boundaryとして、Object Identity、External Export、ChatGPT外部工程、authoritative Result Import、review-required Result、Registry proposalを自動通過させない。

M-03では新しい`sgokb`だけでこのworkflowを1 Object end-to-end完走した。Result fixtureで通常のvalidate/review/importを通し、Render / Lexical Search / read-only MCPで同じaccepted Knowledgeを確認した。必須Gate全PASSにより、「日常運用で内部DB操作を必要としない」というPhase M完了条件を満たした。Semantic/Similarityはoptional runtime未構成のためSKIP。

---

## 8. Phase Mで再設計しない事項

M-01実装でも次は既存canonical contractを維持する。

- Object / Facet / Relation schemaの意味
- Source / Evidence semantics
- accepted Version immutability
- Object Result schema / Validation / Importの基本contract
- external Package exportのexplicit acknowledgement
- Search Representation / Embedding Space identity
- MCP read-only boundary
- SGOKB / UPDS ownership boundary
- migration003〜016の既存内容

M-01で追加したschema変更はRegistry proposal review/apply audit用migration017のみである。
