# J-03 MCP Resource Contract

更新日: 2026-10-14

Status: Accepted

対象Task: `J-03 [P1] MCP Resourcesを定義する`

## 1. Decision

SGOKBの初期MCP Resource surfaceは、検索やparameterized operationではなく、**既知のstable IDを安定URIでdereferenceするread surface**として定義する。

初期Resource Templateは次の3種類とする。

```text
sgokb://object/{object_id}
sgokb://object/{object_id}/version/{version_id}
sgokb://evidence/{evidence_id}
```

Resource contract versionは次とする。

```text
sgokb.mcp-resources.v1
```

J-02のTool contract `sgokb.mcp-read-tools.v1`、J-01のApplication read contract `sgokb.application-read.v1`とは独立versionとして管理する。

---

## 2. ResourceとToolの責務境界

Resourceは「既知Identityを読む」用途に限定する。

```text
Resource
  stable URI → known Object / Version / Evidenceを取得

Tool
  query / filter / ranking / batch / traversal / selectionを実行
```

したがって、次はResource URIへ埋め込まない。

- free-text search
- Semantic Search mode
- Facet filter
- batch Object IDs
- Relation traversal条件
- Evidence candidate limit
- historical search toggle
- Context Builder policy

これらはJ-02/J-04のTool責務である。

URI query stringでTool parameterを代用することも禁止する。

例:

```text
禁止:
sgokb://object/obj-1?facet=values
sgokb://evidence/evi-1?historical=true
```

---

## 3. Object current Resource

```text
sgokb://object/{object_id}
```

stable `object_id`を既知として、その時点のcurrent accepted Knowledgeを読む。

ResponseはJ-01のObject read contractを利用し、Version省略時でも必ず次を含む。

```text
object_id
requested_version_id = null
resolved_version_id
is_current = true
object_status
requested_scope
knowledge
warnings
```

このURI自体はstableだが、返却Knowledgeはcurrent Versionの更新に伴い変化し得る。

したがって、再現性が必要な参照には次のpinned Version Resourceを使用する。

---

## 4. Object pinned Version Resource

```text
sgokb://object/{object_id}/version/{version_id}
```

特定のaccepted Knowledge Versionを読む。

`knowledge_version_id`はaccepted後immutableというC-04契約に従うため、このResourceは再現可能なKnowledge snapshot参照として利用する。

`version_id`が指定`object_id`に属さない場合やaccepted Versionでない場合は、ApplicationのKnowledge request errorとして失敗させる。

同名Object検索やcurrent Versionへのsilent fallbackは行わない。

---

## 5. Evidence Resource

```text
sgokb://evidence/{evidence_id}
```

1件のcanonical Evidenceを直接dereferenceする。

返却内容は少なくとも次を保持する。

```text
evidence
  evidence_id
  content
  source_id
  snapshot_id
  run_id
  extraction_mode
  language
  content_hash

snapshot
source
raw_artifact_ids
context
  source label
  snapshot title
  active locators
  Evidence locations
  metadata
```

これによりObject Knowledgeの`evidence_refs`やEvidence Search resultから、検索をやり直さずに根拠へ直接辿れる。

J-03実装として`KnowledgeReadApplication.get_evidence()`を追加し、MCP AdapterはStorageへ直接アクセスせずApplication境界からEvidenceを取得する。

---

## 6. 初期Resourceに含めないもの

### Source Resource

初期MVPでは`sgokb://source/{source_id}`を公開しない。

理由:

- 現在の主用途はObject KnowledgeからEvidenceへgroundingを辿ることである。
- Evidence ResourceがSource / Snapshot / locator / Raw Artifact provenanceを含む。
- Source単独の閲覧surfaceを先に増やすより、必要性が確認されてから追加する方がcontractを小さく保てる。

将来、Source catalog参照が独立ユースケースになった場合はadditiveに追加可能とする。

### Relation Resource

Relationはcurrent/pinned Version、direction、predicate等のscopeを伴うため、初期MVPでは`get_object_relations` Toolを正規surfaceとする。

### Search result Resource

検索順位やscoreはquery-time stateでありstable IdentityではないためResource化しない。

### Context Resource

Context selectionはJ-04のdeterministic Context Builder責務であり、J-03では定義しない。

---

## 7. Resource Templateを使用する理由

SGOKBにはObject / Evidenceが多数存在し得るため、`resources/list`で全recordを列挙する方式は採用しない。

初期実装では次とする。

```text
resources/list
  → static Resourceなし

resources/templates/list
  → 3 Resource Template
```

これによりKnowledge Base件数に比例した巨大Resource一覧をMCP Clientへ送らない。

Object discoveryは`search_objects`、Evidence discoveryは`search_evidence`を利用し、取得したIDをResource URIへ変換する。

---

## 8. URI rule

URI schemeは`sgokb`とする。

IDはopaque identifierとしてpath segmentへpercent-encodeする。

例えば内部IDが、

```text
object:alice
```

ならcanonical URIは、

```text
sgokb://object/object%3Aalice
```

となる。

Readerはdecode後のIDをApplicationへ渡す。

次を拒否する。

- `sgokb`以外のscheme
- unknown authority
- unsupported path shape
- empty ID
- query string
- fragment
- decode後に`/`を含むpath segment

URI parserは`src/sgokb/mcp/resource_contracts.py`を正本とする。

---

## 9. Representation

Resource MIME typeは初期MVPで統一して次とする。

```text
application/json
```

Resource contentのJSON envelopeは次とする。

```text
resource_contract_version
application_contract_version
data
```

例:

```json
{
  "resource_contract_version": "sgokb.mcp-resources.v1",
  "application_contract_version": "sgokb.application-read.v1",
  "data": {}
}
```

MCP SDK bindingは`MCPReadAdapter.read_resource()`が返す、

```text
uri
mimeType
text
```

をResource contentとして公開できる。

---

## 10. Failure contract

### Invalid Resource URI

unsupported URI shapeは`MCPResourceURIError`としてAdapter境界で拒否する。

### Unknown Object / Version / Evidence

Application read contractの`KnowledgeRequestError`として失敗させる。

別Objectやcurrent Versionへ推測置換しない。

### MCP unavailable

ClientはSQLite direct fallbackを行わないというC-04/J-01契約を維持する。

### External fallback

Resource解決失敗時にWeb/API/cloud providerから同名情報をsilent取得しない。

---

## 11. SDK boundary

J-03でもMCP Server lifecycle / transportを導入しない。

SDK bindingは概念上次を接続する。

```text
resources/list
  → MCPReadAdapter.list_resources()

resources/templates/list
  → MCPReadAdapter.list_resource_templates()

resources/read(uri)
  → MCPReadAdapter.read_resource(uri)
```

AdapterはRepository / SQLite / storage moduleを直接importしない。

実装箇所:

```text
src/sgokb/mcp/resource_contracts.py
src/sgokb/mcp/adapter.py
src/sgokb/application_read.py
tests/test_j03_mcp_resources.py
```

---

## 12. Verification target

J-03では次を検証する。

- Resource Templateが3種類で固定される。
- 全KB recordを`resources/list`で列挙しない。
- Object current URIがcurrent Application readへ解決される。
- pinned Version URIが指定Versionへ解決される。
- Evidence URIがcanonical Evidence + provenanceへ解決される。
- Resource URIにTool-like query parameterを許可しない。
- percent-encoded opaque IDを正しくround-tripする。
- AdapterがStorage / SQLiteを直接参照しない。
- J-01/J-02 read Tool regressionを壊さない。

検証結果:

```text
Ruff: All checks passed
Pytest: 48 passed, 2 skipped
```

検証用GitHub Actions Workflowは結果確認後に削除した。

---

## 13. J-03 Definition of Done

- [x] ResourceとToolの責務境界を固定した。
- [x] Object current Resource URIを定義した。
- [x] Object pinned Version Resource URIを定義した。
- [x] Evidence Resource URIを定義した。
- [x] Source / Relation / Search result / Contextを初期Resource対象外と判断した。
- [x] Resource Template方式を採用し、全record列挙を避けた。
- [x] URI canonicalization / validation ruleを定義した。
- [x] JSON representationとResource contract versionを定義した。
- [x] Application経由のResource dereferenceを実装した。
- [x] focused testを追加した。

---

## 14. Next task

次のTaskは次とする。

```text
J-04 [P0] Context Builderを設計する
```

J-04ではroleplay / comparison / analysis / creative等の用途に応じた、LLM推論を伴わないdeterministic Knowledge selectionを定義する。
