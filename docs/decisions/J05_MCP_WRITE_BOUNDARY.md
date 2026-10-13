# J-05 MCP Write Boundary

更新日: 2026-10-14

Status: Accepted

対象Task: `J-05 [P1] MCP write系はread系と分離する`

## 1. Decision

SGOKBの初期MCP MVPは**read-only**とする。

現在公開するMCP surfaceは、J-01〜J-04で確定したread Tool / Resourceのみである。MCP write capabilityはread Tool contractへ追加せず、将来必要になった場合も**別contract・別Adapter・別Application port**として実装する。

```text
MCP read client
      ↓
MCPReadAdapter
      ↓
KnowledgeReadApplication
      ↓
Retrieval Core
      ↓
Canonical / Derived read stores
```

write系は次の別境界とする。

```text
future MCP write client
      ↓
MCPWriteAdapter
      ↓
Proposal / Staging Application
      ↓
Proposal Staging
      ↓
explicit validation / review / authorization
      ↓
existing authoritative import/apply path
      ↓
Canonical SGOKB
```

J-05時点では`MCPWriteAdapter`は存在するが、active Toolは**0個**であり、`call_tool()`は明示的に拒否する。

---

## 2. MVP policy

write policy version:

```text
sgokb.mcp-write-policy.v1
```

将来write Toolを公開する場合の独立Tool contract namespace:

```text
sgokb.mcp-write-tools.v1
```

初期値は次とする。

```text
mvp_enabled = false
canonical_mutation_allowed = false
staging_target = proposal_staging
require_explicit_server_enable = true
require_authorization_scope = true
require_audit_record = true
automatic_promotion_allowed = false
```

このpolicyは`src/sgokb/mcp/write_policy.py`を実行時正本とする。

---

## 3. Canonical writeをMCPから直接行わない

MCP write Toolが将来追加されても、次を直接行ってはならない。

- accepted Object Knowledgeの作成・更新・削除。
- current Knowledge Versionの切替。
- `ObjectVersionImportService.import_receipt()`等のauthoritative importを直接呼ぶ。
- Registry proposalのreview bypass / direct apply。
- Source / Evidence / Object / Relationのcanonical tableをRepository経由で直接更新する。
- Derived Indexをproposal内容だけでcanonical状態として更新する。
- migration / DB schema mutationを行う。

既存のauthoritative import pathは、validated immutable Result receiptとreview acknowledgementを前提にaccepted Object Versionを作成する。MCPからこのauthority boundaryを迂回しない。

---

## 4. Future write capabilityはproposal-only

将来`propose_object`等を追加する場合、その名前はJ-05時点ではpublic contractとして固定しない。

write Toolが許される責務は次までとする。

1. proposal/staging recordまたはartifactを作成する。
2. caller / request / payload / timestamp等、必要なaudit情報を保持する。
3. proposal IDとvalidation/review状態を返す。
4. canonical反映には別の明示的なvalidation / review / authorization / import操作を要求する。

禁止する挙動:

```text
MCP write Tool
  → proposal生成
  → 自動approve
  → 自動canonical import
```

proposal作成成功を「Knowledge更新成功」と表現してはならない。

---

## 5. Read / Write Adapter分離

`MCPReadAdapter`には今後もmutation methodを追加しない。

read Tool一覧は`read_tool_contracts()`のみから生成し、write capabilityを混在させない。

```text
MCPReadAdapter.list_tools()
  = read Toolのみ

MCPWriteAdapter.list_tools()
  = J-05 MVPでは空
```

これにより、read-only server compositionでは`MCPWriteAdapter`自体を登録せずに運用できる。

write capabilityを有効化する将来server compositionは、read serverとは別に明示的なenable設定とauthorization scopeを要求する。

---

## 6. MCP Tool annotations

現在のread Toolは引き続き次とする。

```text
readOnlyHint = true
openWorldHint = false
```

将来proposal write Toolを追加する場合は少なくとも次を明示する。

```text
readOnlyHint = false
openWorldHint = false
```

proposal creationが純粋なadditive mutationなら`destructiveHint = false`を候補とする。`idempotentHint`はidempotency keyや重複proposal contractが確定した場合のみtrueにする。

ただしMCP annotationはclient向けbehavior hintであり、authorization / permission enforcementの代替にはしない。実際のwrite許可はserver composition、scope、Application boundaryで強制する。

---

## 7. Security / Authority boundary

write surfaceを将来有効化する場合の最低条件:

- default disabled。
- explicit server enable。
- readとは別authorization scope。
- audit record必須。
- request size / schema validation。
- canonical DBへdirect mutation禁止。
- stagingからcanonicalへのautomatic promotion禁止。
- accepted Knowledge反映は既存のvalidation / review / import authority boundaryを通す。

loopback外へ公開する場合のauthentication / scope要件はJ-06およびserver composition設計で具体化する。

---

## 8. Why read-only MVP

read-onlyを初期MVPとする理由:

- Phase Jの目的はLLM/AgentがDB schemaを知らずにKnowledgeを**取得**できること。
- writeを同時に公開すると、Agent outputとcanonical Knowledge authorityの境界が曖昧になる。
- SGOKBはSource / Evidence / Version / Provenanceの検証経路を重視しており、MCP convenience writeで迂回させる利益が小さい。
- read serverはmutation permissionを持たずに構成でき、事故面積を小さくできる。
- proposal-only writeなら将来Agent支援を追加してもcanonical integrityを維持しやすい。

---

## 9. Implementation

追加:

```text
src/sgokb/mcp/write_policy.py
tests/test_j05_mcp_write_separation.py
```

`MCPWriteAdapter`はMVPでzero-tool Adapterとして実装する。

公開packageからpolicy / disabled Adapterを参照可能にするが、read Tool registryには登録しない。

---

## 10. Verification contract

J-05 testでは次を固定する。

- MVP write surfaceはdisabled。
- write Tool listは空。
- write callは`MCPWriteDisabledError`。
- canonical mutation / automatic promotionは禁止。
- staging targetは`proposal_staging`。
- explicit enable / authorization scope / auditを要求するpolicy。
- `propose_object` / import / apply / delete系名称がread Tool一覧へ混入しない。
- active read Toolはすべて`readOnlyHint=true`を維持する。

---

## 11. Definition of Done

- [x] MCP MVPをread-onlyと確定した。
- [x] read / write contract namespaceを分離した。
- [x] `MCPWriteAdapter`を`MCPReadAdapter`から分離した。
- [x] MVP write Toolを0個とした。
- [x] future writeをproposal/staging-onlyに限定した。
- [x] canonical direct mutationを禁止した。
- [x] automatic promotionを禁止した。
- [x] explicit enable / authorization / audit要件を固定した。
- [x] read Tool registryへwrite capabilityが混入しないtestを追加した。

---

## 12. Next task

次のTaskは次とする。

```text
J-06 [P0] ローカルMCP Clientで受入試験する
```
