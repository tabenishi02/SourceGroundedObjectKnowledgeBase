# J-01 Retrieval Core / MCP Application Boundary

更新日: 2026-10-14

Status: Accepted

対象Task: `J-01 [P0] Retrieval CoreとMCP Adapterを分離する`

## 1. Decision

Phase JのKnowledge Accessは次の依存方向に固定する。

```text
Canonical SQLite / Derived Search Index
              ↓
        Retrieval Core
              ↓
 KnowledgeReadApplication
              ↓
        Transport Adapter
        ├─ MCP
        └─ future CLI
```

MCP AdapterはRepository、SQLite SQL、Embedding Provider、Vector Index backendを直接扱わない。

MCPは検索・Knowledge readを再実装せず、`KnowledgeReadApplication`へ委譲するtransport/schema adapterとする。

## 2. Application read boundary

`src/sgokb/application_read.py` に `KnowledgeReadApplication` を追加した。

Applicationから利用可能なread capabilityは次の通り。

```text
search_objects(...)
find_similar_objects(...)
get_object(...)
get_objects(...)
get_object_relations(...)
get_object_evidence(...)
```

`search_objects()` はPhase Iの `HybridObjectSearch` をそのまま利用する。

`find_similar_objects()` はPhase Iの `ObjectSimilaritySearch` をそのまま利用する。

したがってMCP用に別ranking、別filter、別similarity semanticsを作らない。

将来CLIでObject Knowledge read/searchを公開する場合も同じ `KnowledgeReadApplication` を使用する。既存Prototype由来のCLI search実装をMCP contractとして再利用しない。

## 3. Object Knowledge read model

`src/sgokb/retrieval/object_read.py` に `ObjectKnowledgeReader` を追加した。

このReaderはRetrieval Core内部に属し、Storage schemaをApplication向けread modelへ変換する。

Applicationの `get_object()` は最低限次を識別可能にする。

```text
contract_version
object_id
requested_version_id
resolved_version_id
is_current
object_status
name
aliases
primary_class
additional_classes
version_number
requested_scope
knowledge
  default_language
  result_status
  summary
  facets
    statements
  attributes
  relations
warnings
```

Version未指定時はcurrent accepted Versionを解決し、実際に解決した`resolved_version_id`を返す。

Versionを指定した場合は、そのVersionが対象Objectに属するaccepted Versionであることを確認する。

Facet subset等の部分取得は`requested_scope`で明示し、full Knowledge snapshotと誤認させない。

Statement / Attribute / Relationには、要求された場合のみEvidence ID / role参照を付与する。

Application read contract versionは次とする。

```text
sgokb.application-read.v1
```

これはJ-02の公開MCP Tool JSON Schema versionを先取りして固定するものではない。

## 4. Runtime composition

Semantic Search / Similarityで必要なruntime dependencyはMCP Adapter内で生成しない。

```text
Composition Root
  ├─ EmbeddingProvider
  ├─ EmbeddingSpaceSpec
  ├─ VectorIndexAdapter
  └─ Evidence Embedder
          ↓
KnowledgeReadApplication
          ↓
MCP Adapter
```

`KnowledgeReadApplication` constructorへ外部から注入する。

Similarity runtimeが未設定の場合はlocal capability unavailableとして明示的に失敗する。cloud provider等へsilent fallbackしない。

Hybrid Searchのdegraded behaviorはPhase I `HybridObjectSearch`の既存contractを維持する。

## 5. Transport-neutral error semantics

Application boundaryでは少なくとも次をtransport非依存に識別できる。

```text
KnowledgeRequestError
  code = invalid_knowledge_request

RetrievalRuntimeUnavailableError
  code = retrieval_runtime_unavailable
```

unknown Object / Version / Facetやinvalid filter等はrequest errorとして扱う。

Semantic / Similarity runtime未設定等はretrieval runtime unavailableとして扱う。

MCP JSON-RPC error等への変換方法はJ-02で決める。

## 6. MCP adapter boundary

`src/sgokb/mcp/adapter.py` に `MCPReadAdapter` を追加した。

Adapterは `KnowledgeReadApplicationPort` のみを参照する。

禁止する依存:

```text
mcp -> Repository
mcp -> sqlite3
mcp -> storage/*
mcp -> Qdrant client
mcp -> Embedding provider implementation
```

現時点のAdapter method名はPython内部capability名であり、公開MCP Tool名・JSON Schemaを確定するものではない。

MCP SDK / transport / Server lifecycleもJ-01では導入しない。

## 7. Verification

J-01専用testを追加した。

```text
tests/test_j01_retrieval_mcp_boundary.py
tests/test_j01_similarity_application.py
tests/test_j01_application_semantics.py
```

加えてPhase Iの回帰として次を同時実行した。

```text
tests/test_hybrid_search.py
tests/test_object_similarity.py
tests/test_f03_object_evidence_retrieval.py
```

GitHub Actionsによる一時verification run結果:

```text
Ruff: All checks passed
Pytest: 27 passed, 2 skipped
```

検証用Workflowは結果確認後に削除し、恒久設定として残していない。

## 8. J-01 Definition of Done

- [x] MCP AdapterがRepository / SQLite SQLを直接呼ばない。
- [x] Object SearchをApplication API経由で実行できる。
- [x] Object SimilarityをApplication API経由で実行できる。
- [x] current / pinned Version Object readをApplication API経由で行える。
- [x] Retrieval runtime dependencyをAdapter外から注入できる。
- [x] Application APIと直接Retrievalでranking/filter semanticsが変わらない。
- [x] backend/provider障害のno-silent-fallback contractを維持する。
- [x] J-02がTool schemaを設計できるtransport-neutral response contractが存在する。
- [x] focused regression testsが通る。

## 9. Non-goals / next task

J-01では次を確定しない。

- 公開MCP Tool名
- Tool JSON Schema
- MCP Resource URI
- Context Builder policy
- write permission / proposal write
- Server transport / lifecycle

次のTaskは次とする。

```text
J-02 [P0] MCP read toolsを定義する
```
