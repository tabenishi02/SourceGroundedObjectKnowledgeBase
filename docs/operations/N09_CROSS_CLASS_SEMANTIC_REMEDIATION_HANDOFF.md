# N-09 Cross-class Semantic Retrieval Remediation / Next Chat Handoff

更新日: 2026-10-27

- 対象: SGOKB happy-path acceptance / Section N
- 種別: acceptance execution record / N-09 blocker remediation / next-chat handoff
- authoritative procedure: `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md`
- test plan: `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md`
- related remediation: `docs/operations/M05_HISTORICAL_DERIVED_RECONCILIATION.md`
- repository: `tabenishi02/SourceGroundedObjectKnowledgeBase`
- authority: **GitHub `main` を正本とし、この文書内のSHAより現在の`main`を優先する**
- handoff作成直前に確認した`main` HEAD: `5eba4629b12cc071dab33d04faa7521a361d6977`

---

## 1. この文書の目的

2026-10-27までに実施したSGOKB正常系運用受入試験の状態と、N-09 `Cross-class semantic retrieval`をBLOCKしていたfixture不足へのremediationを固定し、別ChatGPT conversationから手順を弱めずに作業を再開できるようにする。

この文書はacceptance procedureそのものを置き換えない。判定・command surface・PASS条件について矛盾がある場合は、**現在のGitHub `main`上の`SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md`をauthoritative**とする。

次チャットでは過去の会話内容をauthorityにせず、まずcurrent `main`と本書を読み、現在のDB/runtime実測を基準に続行すること。

---

## 2. 現在の受入試験状態

実行済みSectionの総括:

| Section | 状態 | 備考 |
| --- | --- | --- |
| A | PASS | Environment / CLI |
| B | PASS | Object Registry |
| C | PASS | Source / capture ingestion |
| D | PASS | source processing / evidence lineage |
| E | PASS | Evidence selection |
| F | PASS | Package build / stage / preflight / export |
| G | PASS | External AI Structured Object Result |
| H | PASS | Result intake / validation / import |
| I | PASS | Registry proposal lifecycle |
| J | PASS | Version update flow; earlier J-02 remediation included |
| K | PASS | Relation read/traversal; K-03 code remediation included |
| L | PASS | Render |
| M | PASS | Lexical Search; M-05 historical-derived reconciliation remediation included |
| N-01 | PASS | semantic runtime |
| N-02 | PASS | index status |
| N-03 | PASS | index rebuild |
| N-04 | PASS | semantic paraphrase retrieval |
| N-05 | PASS | overview-level semantic retrieval |
| N-06 | PASS | facet semantic retrieval |
| N-07 | PASS | statement semantic retrieval |
| N-08 | PASS | current/historical Version scope |
| N-09 | **NOT RUN / BLOCKED → blocker remediated, rerun pending** | OBJ-B/C accepted semantic Knowledgeを追加済み |

**Section N全体はまだCompleteではない。**

次の正式作業はN-09の再実行である。N-09がPASSした時点でSection NをComplete / PASSへ更新できる。

---

## 3. N-09がBLOCKした理由

N-09はOBJ-A / OBJ-B / OBJ-Cをそれぞれ識別すべきsemantic queryを実行し、semantic retrievalが単一test classだけに限定されていないことを確認する試験である。

最初のN-09 precondition auditでは次の状態だった。

```text
=== OBJ-A ===
Name = 孫悟空(ドラゴンボール)
CurrentVersionId = ca4741fd-1a50-4ffb-b318-bf097b2dc5be
AcceptedVersionCount = 2
SearchRepresentationMembershipCount = 34

=== OBJ-B ===
Name = ドラゴンボール
CurrentVersionId = None
AcceptedVersionCount = 0
SearchRepresentationMembershipCount = 0

=== OBJ-C ===
Name = ツンデレ
CurrentVersionId = None
AcceptedVersionCount = 0
SearchRepresentationMembershipCount = 0
```

したがって正式判定は次のとおりだった。

```text
N-09 : NOT RUN / BLOCKED
Reason: acceptance fixture lacks semantic Knowledge for OBJ-B / OBJ-C
```

これはsemantic engine defectの証明ではない。Semantic vector builderはaccepted Knowledge membershipを対象とするため、Registry Objectだけ存在しaccepted Knowledge VersionがないOBJ-B/CはN-09のsemantic targetになれない。

このため、試験条件をlexicalへ弱めたり、Aだけで代替したり、DBを手動編集したりせず、**OBJ-BとOBJ-Cについて通常のPackage → external AI → Result → Import → derived sync workflowを実行してaccepted V1を作成する**方針を採用した。

---

## 4. Acceptance workspace /主要Object ID

Repository root:

```text
C:\codex\SourceGroundedObjectKnowledgeBase
```

主要PowerShell変数:

```powershell
$Db           = ".local/acceptance/sgokb-happy-path.sqlite"
$ExportRoot   = ".local/acceptance/export"
$IncomingRoot = ".local/acceptance/incoming"
$BuildRoot    = ".local/acceptance/package-build"
$StagingRoot  = ".local/acceptance/staging"
$RenderRoot   = ".local/acceptance/render"
$BackupRoot   = ".local/acceptance/backups"
$RestoreDb    = ".local/acceptance/restored/sgokb-happy-path.sqlite"
```

Objects:

```text
OBJ-A / 孫悟空(ドラゴンボール)
Object ID: 96e987d4-8f71-4f6d-887d-9d63b44df48e
Primary Class: class:character

OBJ-B / ドラゴンボール
Object ID: 5c07e8c8-1298-402f-b750-2d8b58fb9fad
Primary Class: class:work

OBJ-C / ツンデレ
Object ID: c02d3ed1-1844-419b-a74b-893671a2a141
Primary Class: class:concept
```

Sources relevant to B/C remediation:

```text
SRC-B1: 35ac828a-c1dd-42e2-a964-19680d7eca82
SRC-C1: 3b887b7c-c1a7-40e7-b826-9bc24efdd353
SRC-R1: ef7127a3-c572-41bf-b0bd-9d5ec932420f
```

---

## 5. OBJ-A canonical / semantic state

Accepted Versions:

```text
V1: b21556b2-ffb6-4baa-82e4-dc9a34d4bceb
V2/current: ca4741fd-1a50-4ffb-b318-bf097b2dc5be
```

V2には、適用済みRelation Type `relation:protagonist_of_work`を用いたOBJ-A → OBJ-B relationが存在する。

```text
Relation ID: bff7268b-4d4e-4999-ad7f-347f96c7b8a9
Relation Type: relation:protagonist_of_work
Target: OBJ-B / ドラゴンボール
Grounding Evidence: 334fe9a0-2f73-4bf8-8fb2-558475d39fb3
```

N-01〜N-08はPASS済み。

代表的N-01 query:

```text
カカロットという本名を持つサイヤ人の主人公
```

OBJ-A V2がrank 1でsemantic retrievalされた。

N-08ではcurrent V2とexplicit historical V1のscope分離を確認し、両方rank 1で期待Objectを取得した。

---

## 6. M-05 remediation state

M-05でhistorical accepted VersionのSearch Representation membership不足が判明したため、derived reconciliationを修正した。

関連文書:

```text
docs/operations/M05_HISTORICAL_DERIVED_RECONCILIATION.md
```

修正後contract:

- `system derived sync --object <object-id>`はcurrent mutable targetを維持したまま、そのObjectの全accepted Version履歴をreconcileする。
- historical sync専用の`--version`は追加しない。
- `--semantic-runtime`時はaccepted-history membershipsに必要なEmbedding / Vector Indexもreconcileする。
- canonical Knowledge Versionは変更しない。

OBJ-AではV1/V2それぞれ17 memberships、unique representations 19を確認した。

このremediationを含むmainを前提にN-08までPASSしている。

---

## 7. OBJ-B N-09 remediation — COMPLETE / PASS

OBJ-Bについて通常workflowでaccepted V1を作成した。

### 7.1 Evidence / Package

Evidence selection:

```text
candidate_count: 500
selected_count: 7
omitted_count: 493
estimated_tokens: 11936 / 12000
bytes: 41666 / 65536
items: 7 / 64
sources: 2
```

Package:

```text
Package ID: pkg_1e6e0a07-f7b2-407d-9fae-eb70a51ba021
Manifest SHA-256: 79208ffa9e0f0bfb694a46fd4b209642de9ef05e7cea8d3c5877f29d038f565f
Base Version: null
Evidence count: 7
Source generation count: 2
```

External analysis result:

```text
Result SHA-256: 272c7083366924b93e215814f7c34ce5fdfc037249d91049c8cc342f6f02b85d
Result status: complete
Attributes: []
Relations: []
Registry proposals: []
```

OBJ-Aのstable Object IDが当該Packageに含まれないため、OBJ-B ResultからOBJ-A relationを捏造しなかった。これは正常なgrounding boundaryである。

### 7.2 Intake / Import

```text
Receipt ID: b86fdb6c-71e2-4f40-9f15-03e772440209
Import ID: 45095d7b-5da9-4dd7-8de7-e57e17bf10f6
OBJ-B V1: d2e8d178-4439-43b7-8368-bb562247a394
Result status: complete
```

OBJ-B current versionは`d2e8d178-4439-43b7-8368-bb562247a394`。

### 7.3 Semantic derived sync

```text
complete: true
partial: false
search_representation: ready / 11 representations
embedding: ready / 11 created
vector_index: ready / qdrant / 11 points written
```

Formal state:

```text
OBJ-B accepted V1      : COMPLETE / PASS
OBJ-B derived semantic : COMPLETE / PASS
```

代表的Knowledgeには次を含む。

- 漫画『ドラゴンボール』では孫悟空が主人公として位置づけられている。
- 漫画派生作、テレビアニメ、劇場版、家庭用ゲーム、アーケードゲームなどへ長期展開されている。

---

## 8. OBJ-C N-09 remediation — COMPLETE / PASS

OBJ-Cについても通常workflowでaccepted V1を作成した。

### 8.1 Evidence selection

`evidence candidates`:

```text
object_id: c02d3ed1-1844-419b-a74b-893671a2a141
name: ツンデレ
scope: effective_snapshot_and_run
semantic: false
candidate_count: 62
Source: SRC-C1 / 3b887b7c-c1a7-40e7-b826-9bc24efdd353
```

`evidence select`:

```text
max_estimated_tokens: 12000
max_bytes: 65536
max_items: 64
estimated_tokens: 11958
bytes: 43665
items: 11
sources: 1
candidate_count: 62
selected_count: 11
omitted_count: 51
warnings: []
```

特にN-09 semantic retrievalへ有効なselected Evidence:

```text
9917a283-7d22-4ae0-a702-3a78d69090cb
  - ツンツン・デレデレの2つの性質を持つキャラクター類型という説明

ac909be1-ccaf-48db-a6a1-d10bc3bc9ab0
  - 「ツン」=敵対・攻撃
  - 「デレ」=好意・受容
  - 2つの真逆の側面
  - 恋愛以外に友人・ライバル関係へも広がる概念

ab58a4b5-6232-437d-a3f3-36dfc98b6b92
  - ツンギレ参照
  - ツンデレのキャラクター造形/性格の複数パターン紹介
```

### 8.2 Package build / export

```text
Package ID: pkg_3bc04ee6-21de-4b73-947c-907a9725cc7d
Manifest SHA-256: 1a30adab40b9c3106cac4ae9ae9ceb5a7b33b6884771c31428214ddef900bbb7
Object ID: c02d3ed1-1844-419b-a74b-893671a2a141
Base Version: null
Evidence count: 11
Source generation count: 1
```

Stage / Preflight / Exportはすべて`allow`。

```text
File count: 4
Total bytes: 60384
Credential findings: []
Warnings: []
Export audit event ID: cd0ff1c3-aa22-4a23-94d6-01fb03ea0fa0
```

Export ZIP:

```text
pkg_3bc04ee6-21de-4b73-947c-907a9725cc7d.zip
Size: 14758 bytes
Google Drive file ID: 19usZoCiIqE7GDiPXOlidQQAJd3vGjDNp
```

### 8.3 External AI Result

Package内部だけをsemantic evidenceとして使用し、`instructions.md`をauthoritative instruction、`schema/object-result-v1.schema.json`をresult schemaとして生成した。

Generation validation:

```text
JSON Schema: PASS
Package binding: PASS
Evidence membership: PASS
Effective facets exact/unique: PASS
Attributes: []
Relations: []
Conflicts: []
Gaps: []
Unresolved references: []
Registry proposals: []
```

Result:

```text
Result size: 7958 bytes
Result SHA-256: c2bcf0e6aa8b70b61d0a2707d3f6fb4b75520f4055c090fd9bff42289ca23b0f
Result status: complete
```

Effective Concept Facetsは6件すべて`content`:

```text
facet:overall
facet:definition
facet:properties
facet:implications
facet:related_concepts
facet:examples
```

### 8.4 Result intake / validation / review / import

`result detect`:

```text
Package known: true
Already received: false
Byte count: 7958
SHA-256: c2bcf0e6aa8b70b61d0a2707d3f6fb4b75520f4055c090fd9bff42289ca23b0f
```

Receive:

```text
Receipt ID: 3026c12f-7a7a-461e-be5c-738b7c755064
Intake state: ready_for_validation
Validation state: pending
```

Validate:

```text
validation_state: valid
is_valid: true
findings: []
```

Review:

```text
review_state: ready_to_import
requires_review: false
blocked: false
reasons: []
destructive_omissions: []
conflicts: []
gaps: []
unresolved_references: []
registry_proposals: []
```

Import:

```text
Import ID: 20eef936-8f78-43f8-904f-f02f3cef50a4
Version ID: 7bc55d1b-e511-427c-861f-dd552ef25e56
Object ID: c02d3ed1-1844-419b-a74b-893671a2a141
Base Version: null
Result status: complete
Review acknowledged: false
Duplicate: false
```

### 8.5 OBJ-C current V1

```text
Object ID: c02d3ed1-1844-419b-a74b-893671a2a141
Name: ツンデレ
Primary Class: class:concept
Status: active
Current Version ID: 7bc55d1b-e511-427c-861f-dd552ef25e56
Version Number: 1
Is Current: true
Result Status: complete
```

Knowledge:

```text
Summary statements: 2
Facets: 6 / 6 content
Attributes: []
Relations: []
```

代表的current Knowledge:

- ツンデレは、ツンツンとデレデレという二つの性質を持つキャラクター類型の一つ。
- 「ツン」は敵対・攻撃、「デレ」は好意・受容として対照的に説明される。
- 恋愛感情に限らず、友人関係やライバル関係にも用いられるとされる。
- 対照的な側面によるギャップや関係性の魅力と結び付けて説明される。

### 8.6 OBJ-C semantic derived sync

実行:

```powershell
.\.venv\Scripts\sgokb.exe --db $Db system derived sync `
  --object $ObjectCId `
  --semantic-runtime
```

結果:

```text
semantic_requested: true
object_count: 1
completed_object_count: 1
partial: false
complete: true

search_representation:
  status: ready
  revision: 1
  representation_count: 19
  unique_representation_count: 19
  changed: true

embedding:
  status: ready
  representation_count: 19
  reused_embedding_count: 0
  created_embedding_count: 19
  changed: true

vector_index:
  status: ready
  backend_key: qdrant
  point_count: 19
  written_point_count: 19
  changed: true
```

Formal state:

```text
OBJ-C accepted V1      : COMPLETE / PASS
OBJ-C derived semantic : COMPLETE / PASS
```

HF Hubのunauthenticated request warningはrate-limit / download optimization warningであり、このsyncのfailureではない。

---

## 9. Semantic runtime / Qdrant configuration

Current accepted semantic composition:

```text
Embedding Space ID:
832920052e1d1a6d3bbe2a5ef9d3b0d09785b0e0f26bf3081b8728de2897d591

Embedding provider:
sentence-transformers

Model:
microsoft/harrier-oss-v1-0.6b

Model revision:
f9b9dc8d367d443f2479d27aa5d8d2850c0774ee

Dimension:
1024
```

Qdrant:

```text
Version: 1.19.2
Executable: .local\qdrant-1.19.2\qdrant.exe
Config: C:\Qdrant\SGOKB\qdrant.yaml
HTTP: 127.0.0.1:6333
GRPC: 127.0.0.1:6334
Storage: C:/Qdrant/SGOKB/storage
```

次チャットでもN/O/P/R等のsemantic試験中はQdrantを停止しないこと。

---

## 10. 現在のN-09 precondition

現在は次の3 Objectすべてにaccepted current Knowledgeとsemantic derived stateが存在する。

```text
OBJ-A / character
  current: ca4741fd-1a50-4ffb-b318-bf097b2dc5be
  semantic: READY

OBJ-B / work
  current: d2e8d178-4439-43b7-8368-bb562247a394
  semantic: READY

OBJ-C / concept
  current: 7bc55d1b-e511-427c-861f-dd552ef25e56
  semantic: READY
```

したがって、元のN-09 blocker conditionは解消済み。

**ただしN-09そのものはまだ再実行していないためPASS扱いにしてはならない。**

---

## 11. 次チャットで最初に実施する作業

### 11.1 Authority確認

最初に現在のGitHub `main`を確認し、少なくとも以下を読む。

```text
docs/operations/N09_CROSS_CLASS_SEMANTIC_REMEDIATION_HANDOFF.md
docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md
docs/operations/M05_HISTORICAL_DERIVED_RECONCILIATION.md
```

過去チャットのcommand syntaxではなく、current `main`のprocedureを優先する。

### 11.2 N-09を再実行

Current procedureのN-09 contract:

> OBJ-A、OBJ-B、OBJ-Cをそれぞれ識別すべき意味のあるsemantic queryを実行する。PASS条件はsemantic retrievalが1つのtest classだけに限定されないこと。

現在用意しているqueryは次の3つ。

```powershell
Write-Host "=== N-09A / Character / OBJ-A ==="

$N09A = .\.venv\Scripts\sgokb.exe --db $Db search `
    "カカロットという本名を持つサイヤ人の主人公" `
    --mode semantic `
    --semantic-runtime `
    --require-full-runtime `
    --limit 10

if ($LASTEXITCODE -ne 0) {
    throw "N-09A failed"
}

$N09A


Write-Host "`n=== N-09B / Work / OBJ-B ==="

$N09B = .\.venv\Scripts\sgokb.exe --db $Db search `
    "漫画を中心にテレビアニメ、劇場版、ゲームなどへ長期展開された作品" `
    --mode semantic `
    --semantic-runtime `
    --require-full-runtime `
    --limit 10

if ($LASTEXITCODE -ne 0) {
    throw "N-09B failed"
}

$N09B


Write-Host "`n=== N-09C / Concept / OBJ-C ==="

$N09C = .\.venv\Scripts\sgokb.exe --db $Db search `
    "敵対的なツンと好意的なデレという対照的な性質を持つキャラクター類型" `
    --mode semantic `
    --semantic-runtime `
    --require-full-runtime `
    --limit 10

if ($LASTEXITCODE -ne 0) {
    throw "N-09C failed"
}

$N09C
```

Expected identification:

```text
N-09A -> OBJ-A / 孫悟空(ドラゴンボール) / class:character
N-09B -> OBJ-B / ドラゴンボール / class:work
N-09C -> OBJ-C / ツンデレ / class:concept
```

判定では単にcommand exit codeを見るだけでなく、各queryが意図したObjectをsemantic channelでreasonable rankに取得し、3 Classへcross-class retrievalが成立していることを確認する。

Class filterを追加して試験を弱めない。current procedureが要求するcross-class性をそのまま検証する。

### 11.3 N-09 PASS後

N-09がPASSした場合のみ次を正式記録する。

```text
N-09     : Complete / PASS
Section N: Complete / PASS
```

その後、current acceptance procedureに従ってSection O以降へ進む。

N-09がFAILした場合は、結果を保存し、query quality、representation coverage、Embedding、vector index、rankingのどこが原因かを切り分ける。試験条件を弱めたりcanonical DBを手動修正して通過させてはならない。

---

## 12. Operational cautions

### 12.1 PowerShell / JSON

重要なCLI JSONを解析する場合、Windows PowerShell/文字コード/大型JSONによるfalse failureを避けるため、必要に応じてPython `json.loads(..., encoding="utf-8-sig")`を使う。

### 12.2 Qdrant

semantic section中は既存Qdrant processを維持する。

同じstorageを使う2つ目のQdrant processを起動するとWAL lockでexit 101になり得る。既存processが正常稼働している場合、これはSGOKB acceptance failureではない。

### 12.3 HF warning

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

は高いrate limit / faster downloadsを得るためのwarningであり、Embedding生成が正常完了している限りacceptance failureではない。

### 12.4 Result grounding

外部AI Result生成時はPackage内部情報だけをsemantic evidenceとして使用する。

- Web検索や外部知識でclaimを補わない。
- `manifest.evidence.included_evidence_ids`外のEvidence IDを使わない。
- Packageに存在しないstable Object IDを捏造しない。
- unknown Relation Typeを生成しない。
- `instructions.md`をauthoritative analysis instructionとする。
- result schemaへ完全準拠させる。

### 12.5 Acceptance discipline

- canonical SQLite stateを手動編集しない。
- failed conditionをskipしない。
- semantic testをlexical testへ弱めない。
- current/historical Version scopeを混在させない。
- helper/shell errorとSGOKB acceptance failureを区別する。

今回発生したresult download linkの一時的失敗や、PowerShell `Join-Path`の引数誤りはSGOKB acceptance failureではなくhelper/operator-layer issueとして扱った。

---

## 13. 次チャットへの最短引継ぎ要約

```text
SourceGroundedObjectKnowledgeBase happy-path acceptanceを継続中。
A〜MはPASS。
N-01〜N-08はPASS。
N-09は当初OBJ-B/Cにaccepted KnowledgeがなくBLOCKEDだった。

remediationとして通常workflowで
- OBJ-B V1 d2e8d178-4439-43b7-8368-bb562247a394
- OBJ-C V1 7bc55d1b-e511-427c-861f-dd552ef25e56
をacceptedし、両ObjectともSearch Representation / Embedding / Qdrant Vector IndexをREADYにした。

現在OBJ-A/B/Cすべてsemantic-ready。
N-09 blockerは解消済みだが、N-09自体はまだ再実行していない。
次タスクはcurrent mainのprocedureを確認後、N-09 cross-class semantic retrievalを3 queryで再実行し、PASSならSection NをComplete / PASSにすること。
```
