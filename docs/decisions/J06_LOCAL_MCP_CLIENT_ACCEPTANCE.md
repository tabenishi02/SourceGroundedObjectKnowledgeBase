# J-06 Local MCP Client Acceptance

更新日: 2026-10-14

Status: Accepted

対象Task: `J-06 [P0] ローカルMCP Clientで受入試験する`

## 1. Decision

Phase JのMCP Knowledge Access Layerは、ローカルMCP Clientから実際のMCP transportを通して利用できる状態を受入条件とする。

J-06ではMCP Python SDK v2を薄いtransport bindingとして追加し、SGOKB固有のKnowledge semantics / validation / selectionは引き続きJ-01〜J-05で確定したApplication / Adapter側を正本とする。

```text
Local MCP Client
      ↓ stdio
MCP Python SDK v2 Server
      ↓
MCPReadAdapter
      ↓
KnowledgeReadApplication
      ↓
Retrieval Core
      ↓
Canonical SQLite / Derived Search Index
```

MCP SDKはcore dependencyにはせず、optional dependency `mcp` とする。

```text
mcp>=2,<3
```

J-06実測時に解決されたversionは`mcp 2.3.0`である。

---

## 2. Local transport baseline

初期MVPのlocal transportは`stdio`とする。

J-06ではHTTP listenerを実装・起動しない。MCP ClientがServer subprocessを起動し、stdin/stdoutだけで通信する。

これにより初期MVPではnetwork port、loopback listener、LAN公開を必要としない。

将来Streamable HTTP等を追加する場合は別のserver compositionとして扱い、loopback外への公開には少なくとも次を要求する。

- explicit enable
- authentication
- authorization scope
- J-05 write policyとの分離
- audit / deployment configuration

非loopback公開へsilent fallbackしない。

---

## 3. SDK binding boundary

追加した`src/sgokb/mcp/server.py`はtransport adapterに限定する。

責務:

- MCP initialize / protocol negotiation
- `tools/list`
- `tools/call`
- `resources/list`
- `resources/templates/list`
- `resources/read`
- stdio lifecycle

非責務:

- SQLite query
- Repository直接参照
- Embedding Provider構築
- Vector backend構築
- Context selection policy
- write / canonical mutation

Tool input/output validationとKnowledge operationのdispatchは`MCPReadAdapter`を経由する。

J-05で定義した`MCPWriteAdapter`はread-only serverへ登録しない。

---

## 4. Acceptance environment

初回受入環境（GitHub-hosted Windows runner）:

```text
OS: Microsoft Windows Server 2025
Python: 3.12.10
MCP Python SDK: 2.3.0
Transport: local stdio subprocess
Protocol negotiation: 2026-07-28
```

2026-10-14にRemote Desktop Commander経由でReference Workstation上のfollow-up受入試験も実施した。

```text
OS: Windows 11
Python: 3.10.6
MCP Python SDK: 2.3.0
Ruff: 0.17.0
Transport: local stdio subprocess
Protocol negotiation: 2026-07-28
Repository HEAD: 0991b642006a4a00fec6d88c805551bb33faa25e
```

Reference Workstationでは実repoをGitHub側HEADへfast-forwardしたうえで、`tests/test_j06_mcp_client_acceptance.py`を実行し、local MCP Client → stdio Server subprocess → `MCPReadAdapter` → `KnowledgeReadApplication` → Repository / Retrieval Coreの経路を確認した。

LM Studio等の特定GUI Host固有の設定画面はこのfollow-upでも受入条件には含めていない。Phase JのP0完了条件はclientがDB schemaを知らずにKnowledgeを取得できることであり、特定Host UIへの依存は設けない。

---

## 5. Real retrieval fixture

J-06の最終transport testでは固定レスポンスだけのfake Applicationを使用しない。

Server subprocess内で次を構築する。

```text
Temporary SQLite Repository
  ├─ object:alpha / version:alpha:v1
  └─ object:beta  / version:beta:v1
        ↓
SearchRepresentationBuilder
        ↓
3-dimensional deterministic Embedding
        ↓
ExactVectorIndexAdapter
        ↓
KnowledgeReadApplication
        ↓
MCPReadAdapter
        ↓
MCP Server
```

Semantic queryだけはnetwork / external modelを必要としないdeterministic test embedderを用いる。

したがってSemantic Search / Similarity SearchはMCP wire responseをfakeしておらず、実際のApplication / Retrieval Core / Search Representation / Vector Index経路を通る。

---

## 6. Accepted scenarios

Windows local MCP Clientから次を確認した。

### Protocol / discovery

- protocol version `2026-07-28`で初期化できる。
- Server名`sgokb`を取得できる。
- J-04までのactive read Tool 8個を列挙できる。
- 全read Toolが`readOnlyHint=true`を維持する。
- Resource Template 3種を列挙できる。
- static Resource全件列挙は空のままである。

### Object read

- `get_object`でknown stable Object IDを取得できる。
- `resolved_version_id`を取得できる。
- `get_objects`で複数Objectを取得できる。
- batch resultがrequest orderを維持する。

### Semantic / Similarity

- `search_objects(mode="semantic")`がMCP越しに実Retrieval Coreへ到達する。
- `find_similar_objects`がMCP越しに実Vector Indexへ到達する。

### Context Builder

- `build_context`をMCP越しに呼べる。
- purposeを保持する。
- `max_characters`をContext budgetへ反映する。
- `used_characters <= max_characters`を維持する。

### Resource

- `sgokb://object/{object_id}`をMCP Resourceとしてdereferenceできる。
- Resource envelopeからObject / resolved Versionを取得できる。

---

## 7. MCP停止時の独立性

MCP Serverをcanonical storeの必須runtime dependencyにはしない。

受入試験ではMCP subprocessとは別に、MCP Serverを起動していない状態で次を確認した。

- `KnowledgeReadApplication`からcanonical Objectを直接readできる。
- `python -m sgokb --help`が正常終了する。

これはoperator / CLI側の可用性要件である。

UPDS等のMCP consumerがMCP停止時にSQLiteへ直接fallbackしてよい、という意味ではない。consumer dependencyは引き続きMCP境界を維持する。

---

## 8. Verification result

GitHub-hosted Windows runnerの最終runで次を確認した。

```text
MCP Python SDK: 2.3.0
Ruff: All checks passed
Pytest: 61 passed, 2 skipped
```

2026-10-14のReference Workstation follow-upでは次を確認した。

```text
MCP Python SDK: 2.3.0
Ruff 0.17.0: All checks passed
J-06 acceptance: 2 passed
Focused regression: 61 passed, 2 skipped in 7.72s
```

focused regressionにはJ-06に加えてJ-05〜J-01、Object Evidence Retrieval、Hybrid Search、Object Similarityを含めた。Reference WorkstationでもGitHub runnerと同じ結果となったため、Codexによる代替検証は不要と判断した。

---

## 9. Definition of Done

- [x] 実MCP Python SDK bindingを追加した。
- [x] local stdio Client / Serverのinitializeを確認した。
- [x] single Object readを確認した。
- [x] multiple Object readを確認した。
- [x] Semantic SearchをMCP越しに確認した。
- [x] Similarity SearchをMCP越しに確認した。
- [x] Context length controlをMCP越しに確認した。
- [x] MCP Resource dereferenceを確認した。
- [x] MCP停止時もcanonical Application read / CLIが独立して利用できることを確認した。
- [x] initial MVPがstdio read-onlyでnetwork listenerを持たないことを固定した。
- [x] loopback外公開を将来追加する場合のexplicit enable + authentication / scope要件を維持した。
- [x] focused regressionが成功した。

---

## 10. Phase J result

J-01〜J-06が完了したため、Phase J — MCP Knowledge Access Layerは完了とする。

Phase J完了条件:

> LLM/AgentがDB構造を知らずにSGOKB Knowledgeを取得できる。

次のTaskはPhase Kの次とする。

```text
K-01 [P1] UPDSからSGOKB Objectを参照する最小ユースケースを定義する
```
