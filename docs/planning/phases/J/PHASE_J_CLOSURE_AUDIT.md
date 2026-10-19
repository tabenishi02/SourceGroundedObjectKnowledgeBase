# Source Grounded Object Knowledge Base — Phase J Closure Audit

更新日: 2026-10-14

- Status: **Complete**
- Phase: `Phase J — MCP Knowledge Access Layer`
- Scope: J-01〜J-06の完了状態、MCP boundary、local client acceptance、Phase Kへの引継ぎ
- Previous phase: `Phase I — 意味検索・類似検索`
- Next phase: `Phase K — SGOKB / UPDS連携試験`
- Next task: `K-01 [P1] UPDSからSGOKB Objectを参照する最小ユースケースを定義する`

---

## 1. 結論

Phase JのTaskと完了条件を再監査した結果、**未完了Taskは0件**だった。

```text
J-01 Retrieval Core / MCP Adapter boundary      Complete
J-02 MCP read Tool contract                    Complete
J-03 MCP Resource contract                     Complete
J-04 deterministic Context Builder             Complete
J-05 MCP read / write separation               Complete
J-06 local MCP Client acceptance               Complete
```

J-06はGitHub-hosted Windows runnerに加え、2026-10-14にReference Workstation上でもRemote Desktop Commander経由でfollow-up acceptanceを実施済みである。

Phase Jを**Complete / Closed**とし、Phase Kへ移行可能と判定する。

---

## 2. Task別監査

| Task | Status | 主な正本 / 実装 |
|---|---|---|
| J-01 | Complete | `docs/decisions/J01_RETRIEVAL_MCP_APPLICATION_BOUNDARY.md`, `src/sgokb/application_read.py`, `src/sgokb/retrieval/object_read.py` |
| J-02 | Complete | `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`, `src/sgokb/mcp/tool_contracts.py`, `src/sgokb/retrieval/evidence_search.py` |
| J-03 | Complete | `docs/decisions/J03_MCP_RESOURCE_CONTRACT.md`, `src/sgokb/mcp/resource_contracts.py`, `src/sgokb/mcp/adapter.py` |
| J-04 | Complete | `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`, `src/sgokb/retrieval/context_builder.py` |
| J-05 | Complete | `docs/decisions/J05_MCP_WRITE_BOUNDARY.md`, `src/sgokb/mcp/write_policy.py` |
| J-06 | Complete | `docs/decisions/J06_LOCAL_MCP_CLIENT_ACCEPTANCE.md`, `src/sgokb/mcp/server.py`, `tests/test_j06_mcp_client_acceptance.py` |

---

## 3. Phase J完了条件の確認

Phase Jの完了条件は、

> LLM / AgentがDB構造を知らずにSGOKB Knowledgeを取得できる。

である。

J-01〜J-06により次の経路が成立した。

```text
MCP Client / LLM / Agent
        ↓
MCP Tool / Resource contract
        ↓
MCPReadAdapter
        ↓
KnowledgeReadApplication
        ↓
Retrieval Core
        ↓
Canonical SQLite / Derived Search Index
```

MCP ClientはSQLite table、Qdrant backend、Repository implementationを知る必要がない。

したがってPhase J完了条件を満たす。

---

## 4. Phase Kへ固定して渡すMCP契約

Phase Kでは原則として次を再設計しない。

```text
Application contract          sgokb.application-read.v1
MCP read Tool contract        sgokb.mcp-read-tools.v1
MCP Resource contract         sgokb.mcp-resources.v1
Context Builder contract      sgokb.context-builder.v1
MCP write policy              sgokb.mcp-write-policy.v1
MCP transport baseline        local stdio
MCP MVP                       read-only
```

active read Toolは次の8個である。

```text
search_objects
find_similar_objects
get_object
get_objects
get_object_relations
get_object_evidence
search_evidence
build_context
```

Resource Templateは次の3種である。

```text
sgokb://object/{object_id}
sgokb://object/{object_id}/version/{version_id}
sgokb://evidence/{evidence_id}
```

---

## 5. Identity / Version契約

Phase Kへ次を固定して引き継ぐ。

- long-lived Identityはstable `object_id`。
- accepted Knowledge snapshotはimmutable `knowledge_version_id`。
- current requestでも実際に返した`resolved_version_id`を返す。
- pinned accepted Versionを取得できる。
- Facet subset等のpartial scopeをfull snapshotと誤認させない。
- Object名、alias、search rankを永続Identityとして使用しない。

これは`docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`のC-04契約をPhase J transportへ実装した結果である。

---

## 6. Read / write boundary

Phase J MVPはread-onlyで完了した。

`MCPReadAdapter`へcanonical mutationを追加しない。

将来write capabilityを追加する場合も、

```text
MCPWriteAdapter
  → proposal / staging
  → explicit validation / review / authorization
  → authoritative import / apply path
```

とし、MCPからaccepted Object Knowledgeへ直接writeしない。

UPDS Preference HypothesisやPersonal InferenceをSGOKB canonical Knowledgeへ自動write-backしない。

---

## 7. Failure / fallback boundary

Phase Kでも次を維持する。

- MCP停止時にUPDSがSGOKB SQLiteへdirect fallbackしない。
- local provider / vector backend障害時にexternal cloudへsilent fallbackしない。
- partial / degraded / unavailableを完全成功として隠さない。
- MCP Serverはcanonical storeの必須runtime dependencyではない。
- operator側Application / CLIはMCP停止時もcanonical dataを利用可能である。

---

## 8. J-06 acceptance結果

GitHub-hosted Windows runner:

```text
Windows Server 2025
Python 3.12.10
MCP Python SDK 2.3.0
Ruff: All checks passed
Pytest: 61 passed, 2 skipped
```

Reference Workstation follow-up:

```text
Windows 11
Python 3.10.6
MCP Python SDK 2.3.0
Ruff 0.17.0: All checks passed
J-06 acceptance: 2 passed
Focused regression: 61 passed, 2 skipped in 7.72s
```

Reference Workstationではlocal MCP Client → stdio Server subprocess → `MCPReadAdapter` → `KnowledgeReadApplication` → Repository / Retrieval Coreの経路を実行した。

GitHub runnerとReference Workstationで同一のfocused regression結果を確認した。

---

## 9. Non-blocking follow-up

次はPhase J blockerではない。

- LM Studio等、特定GUI Host固有のMCP登録UI検証。
- Streamable HTTP等のnetwork transport追加。
- non-loopback公開時の具体的authentication implementation。
- MCP proposal write Toolの実装。
- Reference Workstation既存`.venv`のsystem-site-packages分離。

これらを理由にPhase Jを未完了へ戻さない。

---

## 10. Phase Kへの外部依存監査

`tabenishi02/UserPreferenceDiscoverySystem`の`main`を確認したところ、現時点では主に次で構成される。

```text
README.md
docs/PROJECT_CONCEPT.md
```

UPDSの実装runtime / database / MCP consumer codeはまだ存在しない。

したがってPhase Kでは次を区別する。

1. SGOKB側のintegration contract / fixtureで検証可能な事項。
2. 実UPDS実装が必要なcross-repository end-to-end事項。

K-01はユースケースと参照契約の定義Taskであるため、UPDS runtime未実装でも開始可能である。

K-02 / K-03はまずSGOKB側contract fixtureで検証し、実UPDS実装後にcross-repo acceptanceを追加できる形にする。

---

## 11. Closure decision

Phase Jの残Taskは0件であり、追加修正を要求するPhase J blockerは存在しない。

**Phase JをCloseし、Phase K Readyとする。**

次Task:

```text
K-01 [P1] UPDSからSGOKB Objectを参照する最小ユースケースを定義する
```
