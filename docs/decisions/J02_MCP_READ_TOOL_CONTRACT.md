# J-02 MCP Read Tool Contract

更新日: 2026-10-14

Status: Accepted

対象Task: `J-02 [P0] MCP read toolsを定義する`

## 1. Decision

SGOKBの初期MCP Knowledge Access Layerでは、read capabilityを次の7 Toolへ整理する。

```text
search_objects
find_similar_objects
get_object
get_objects
get_object_relations
get_object_evidence
search_evidence
```

公開ToolはSQLite / Repository / Qdrant / Embedding Providerを直接扱わず、J-01で確立した`KnowledgeReadApplication`を経由する。

Tool contract versionは次とする。

```text
sgokb.mcp-read-tools.v1
```

Application read contractとは別versionとして管理する。

---

## 2. Active read Tools

### 2.1 `search_objects`

用途:

- Object IDが不明な状態からObjectを探索する。
- name / alias / Knowledge text / Semantic representationを利用する。
- 通常結果単位は1 Objectとする。

主要input:

```text
query
mode = lexical | semantic | hybrid
filters
limit
candidate_limit?
```

`hybrid`を既定とする。

`semantic_search_objects`は独立Toolにしない。

```text
search_objects(mode="semantic")
```

で同じcapabilityを表現する。

理由は、検索mode以外のfilter / result / ranking contractが同一であり、Toolを分離すると重複contractになりやすいためである。

### 2.2 `find_similar_objects`

用途:

- 既知Objectを基準にSemantic Similarityを取得する。
- Object overall similarity。
- Facet-specific similarity。

主要input:

```text
object_id
facet?
source_version_id?
cross_class = false
include_archived = false
limit
```

Facet similarity専用Toolは作らない。

```text
find_similar_objects(object_id, facet="values")
```

で表現する。

Facet未存在時はoverall similarityへsilent fallbackしない。

### 2.3 `get_object`

用途:

- stable `object_id`から1 Objectを取得する。
- current accepted Knowledgeまたは明示Versionを取得する。
- Facet subsetを取得する。

主要input:

```text
object_id
version_id?
facets?
include_relations = true
include_evidence_refs = true
```

Version省略時でもResponseへ`resolved_version_id`を含める。

### 2.4 `get_objects`

用途:

- 既知Object ID群をbatch取得する。
- UPDS等がSelection Event群から複数Objectをまとめて取得する。

主要input:

```text
object_ids
version_ids?
facets?
include_relations = true
include_evidence_refs = true
```

初期MCP contractでは最大100 Object / requestとする。

### 2.5 `get_object_relations`

用途:

- 既知Objectの構造化Relationを取得する。
- 初期MVPでは決定論的な1-hop Relation retrievalを基本とする。

主要input:

```text
object_id
version_id?
include_evidence_refs = true
```

free-text Relation Searchとは分離する。

### 2.6 `get_object_evidence`

用途:

- 1 Objectを起点にEvidence候補を取得する。
- explicit Source association、name / alias、lexical、optional semantic等を利用する。

主要input:

```text
object_id
max_candidates
semantic?
```

これは任意queryによるEvidence Searchではなく、Object-oriented Evidence retrievalである。

### 2.7 `search_evidence`

用途:

- Evidence Storeを任意queryで直接検索する。
- Object Knowledge Searchとは別結果型として扱う。

主要input:

```text
query
mode = lexical | semantic | hybrid
limit
source_ids?
object_id?
association_status?
language?
include_historical = false
```

結果単位は1 `evidence_id`とし、Source / Snapshot / Normalized Run等のprovenanceを保持する。

通常はeffective Snapshot / Normalized Run世代のみを検索対象とし、historical Evidenceは`include_historical=true`で明示的に有効化する。

J-02実装として`EvidenceSearch`をRetrieval Coreへ追加し、`KnowledgeReadApplication.search_evidence()`経由でMCP Adapterから利用可能にした。

---

## 3. `build_context`の扱い

`build_context`はPhase J全体で必要なcapabilityだが、selection policyはJ-04の責務である。

J-02では名称と最小contractだけを予約する。

```text
build_context
  status = reserved_j04
```

J-04完了まではactive Tool一覧へ含めず、`tools/list`相当の結果にも公開しない。

これによりJ-02でroleplay / comparison / analysis / creative等のFacet selection policyを先取りして固定しない。

---

## 4. Tool schema policy

Tool definitionは`src/sgokb/mcp/tool_contracts.py`を正本とする。

各Toolは次を持つ。

```text
name
title
description
inputSchema
outputSchema
annotations
```

SchemaはJSON Schema Draft 2020-12として定義する。

read Toolには次のannotationを付与する。

```text
readOnlyHint = true
openWorldHint = false
```

SGOKB read Toolはcanonical / derived local Knowledgeを読むclosed-world operationとして扱う。

未知input fieldは`additionalProperties=false`で拒否し、入力typoをsilent無視しない。

---

## 5. Response envelope

MCP read Toolのstructured responseは次のouter envelopeを持つ。

```text
tool_contract_version
application_contract_version
data
```

例:

```json
{
  "tool_contract_version": "sgokb.mcp-read-tools.v1",
  "application_contract_version": "sgokb.application-read.v1",
  "data": {}
}
```

これによりMCP Tool schema versionとApplication read model versionを独立して追跡する。

Object readの`data`内ではJ-01のcontractを維持し、少なくとも次を識別可能にする。

```text
object_id
requested_version_id
resolved_version_id
is_current
object_status
requested_scope
knowledge
warnings
```

---

## 6. Limits

初期MCP contractでは過大Responseを避けるため次を固定する。

```text
Object Search / Similarity / Evidence Search result limit: 100
get_objects batch: 100 Object
get_object_evidence max_candidates: 500
Facet selection: 50 Facet
```

内部Retrieval Coreがより大きいlimitを扱える場合でも、MCP public Tool contractは別途制限する。

---

## 7. Error / degradation contract

### Invalid Tool arguments

JSON Schema違反、unknown Tool、limit超過等は`MCPToolArgumentsError`としてAdapter境界で拒否する。

### Invalid Knowledge request

unknown Object / Version / Facet、invalid filter等はApplicationの`KnowledgeRequestError`を維持する。

### Retrieval runtime unavailable

Semantic-only Search / Similarity等でlocal runtimeが利用不能な場合は`RetrievalRuntimeUnavailableError`を維持する。

外部cloud providerへsilent fallbackしない。

### Hybrid degradation

Hybrid Searchでsemantic channelのみ利用不能な場合、Lexical resultを利用できる既存contractを維持し、`degraded_channels`へ明示する。

完全成功として隠さない。

---

## 8. MCP SDK boundary

J-02ではTool contractをSDK-neutralなPython definitionとして固定する。

現時点ではMCP Server lifecycle / stdio transport / HTTP transport / session管理を導入しない。

```text
MCP SDK binding
      ↓
MCPReadAdapter.list_tools()
MCPReadAdapter.call_tool()
      ↓
KnowledgeReadApplication
```

Server / transport bindingは後続Phase Jでこのcontractを利用する。

これによりMCP SDK version更新とSGOKB Knowledge Access semanticsを分離する。

---

## 9. Verification

J-02専用test:

```text
tests/test_j02_mcp_read_tools.py
tests/test_j02_evidence_search.py
```

同時にJ-01およびPhase I retrieval regressionを実行した。

検証結果:

```text
Ruff: All checks passed
Pytest: 38 passed, 2 skipped
```

確認した主要contract:

- active read Toolが7個に固定される。
- `semantic_search_objects`を重複公開しない。
- Facet Similarityを`facet` parameterで表現する。
- `build_context`がJ-04まで非activeである。
- read-only / closed-world annotationが付く。
- unknown input field / public limit超過を拒否する。
- Evidence Searchのeffective / historical scopeが分離される。
- Object association scopeがEvidence Searchへ適用される。
- Semantic Evidence Searchがprovenanceを保持する。
- semantic runtime未設定時にsemantic-onlyはexplicit failure、Hybridはdegraded状態を返す。
- J-01 / Hybrid Search / Object Similarity / Object Evidence Retrieval regressionが維持される。

検証用GitHub Actions Workflowは結果確認後に削除した。

---

## 10. J-02 Definition of Done

- [x] MCP read Toolのactive surfaceを固定した。
- [x] Tool名・説明・input/output JSON Schemaを定義した。
- [x] Object Search / Semantic Searchの重複を整理した。
- [x] Object / Facet Similarityの重複を整理した。
- [x] Object Get / Batch Get / Relation / Evidenceの責務を分離した。
- [x] general Evidence SearchをApplication / MCP境界へ追加した。
- [x] `build_context`をJ-04予約capabilityとして分離した。
- [x] read-only / closed-world annotationを固定した。
- [x] MCP Tool contract versionを固定した。
- [x] public request limitを固定した。
- [x] no-silent-fallback / degraded contractを維持した。
- [x] focused regression testsが通った。

---

## 11. Next task

次のTaskは次とする。

```text
J-03 [P1] MCP Resourcesを定義する
```

J-03ではToolとResourceの責務重複を整理し、`sgokb://object/<id>`等のResource URIを検討する。
