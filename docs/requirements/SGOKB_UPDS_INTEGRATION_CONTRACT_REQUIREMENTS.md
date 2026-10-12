# Source Grounded Object Knowledge Base — SGOKB → UPDS Integration Contract要件

更新日: 2026-10-12

- Task: `C-04 [P1] SGOKB→UPDS連携契約を定義する`
- Status: Accepted
- Related:
  - `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
  - `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
  - `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`

## 1. 本書の位置づけ

C-01ではSGOKBをWorld / Object Knowledge Layer、C-02ではUPDSをPersonal Inference Layer、C-03ではConceptのcanonical所有をSGOKBと定義した。

C-04では、これらの責務境界を実際のシステム間参照へ落とし込むため、**SGOKBからUPDSへObject Knowledgeを提供する論理契約**を確定する。

本書は主に次を固定する。

- 依存方向
- stable Object IDの参照規則
- Knowledge Versionの参照規則
- Object / Facet / Relation / Concept等の取得境界
- current参照とpinned Version参照の違い
- stale / superseded / unavailable時の扱い
- cacheの扱い
- MCPとDB direct accessの境界
- failure時のgraceful degradation
- contract versioning
- UPDSからSGOKBへのwriteを標準連携から除外すること

具体的なDB物理schemaはPhase E、MCP Tool名・Resource URI・JSON Schema等のtransport詳細はPhase Jで確定する。本書はそれらが満たすべき意味契約を定義する。

---

## 2. 正式決定

SGOKBとUPDSの標準連携契約を次のように確定する。

> **SGOKBはcanonical World / Object Knowledge Provider、UPDSはPersonal Inference Consumerとする。UPDSはSGOKBのstable `object_id`を永続参照の基本単位とし、推論時に実際に利用したKnowledgeを再現する必要がある場合はimmutableな`knowledge_version_id`を併記する。標準連携はSGOKB Retrieval / Application Coreを介したMCP read accessとし、UPDSからSGOKB SQLiteへの直接参照・直接更新を契約としない。**

基本依存方向は次とする。

```text
SGOKB Canonical Store
        ↓
Retrieval / Application Core
        ↓
MCP Adapter
        ↓
UPDS
        ↓
Semantic Observation / Pattern / Preference Hypothesis
```

UPDSからSGOKB canonical KnowledgeへPersonal Inferenceを書き戻す逆方向の依存は標準契約に含めない。

---

## 3. 依存方向と責務

### INT-01 — SGOKBはKnowledge Provider

SGOKBはUPDSへ次のWorld / Object Knowledgeを提供できなければならない。

- Object Identity
- Primary / Additional Class
- accepted Object Knowledge Version
- Semantic Facet
- Knowledge Statement
- World / Object Relation
- Concept Object
- 必要に応じたSource / Evidence reference
- Search / Similarity結果

SGOKBはこれらの取得時にPersonal Preference推論を行わない。

### INT-02 — UPDSはKnowledge Consumer

UPDSはSGOKB KnowledgeをPersonal Inferenceの入力として利用する。

UPDS側が所有するものはC-02の通り、Selection Event、Semantic Observation、Pattern、Preference Hypothesis、Alternative Explanation、User-oriented Evidence Set等である。

### INT-03 — SGOKBはUPDSに依存しない

SGOKB CoreはUPDS schema、UPDS database、Preference Hypothesis、User profileが存在しなくても完全に動作できなければならない。

SGOKB Object / Conceptのcanonical Knowledge生成・検索・VersioningはUPDSの存在を前提にしない。

### INT-04 — UPDSはSGOKB canonical schemaへ直結しない

UPDSはSGOKB SQLite table構造を直接Knowledge Access Contractとして利用してはならない。

禁止する依存例:

```text
UPDS SQL
  SELECT ... FROM sgokb_object_versions ...
```

SGOKB側でtable rename、normalization、storage backend変更等が起きても、Integration Contractを満たす限りUPDSが壊れない境界を維持する。

---

## 4. Object Identity参照契約

### INT-ID-01 — 永続参照の基本単位は`object_id`

UPDSからSGOKB Objectを長期参照する場合、基本IdentityはSGOKBが発行するstable `object_id`とする。

次を永続Identityとして使用してはならない。

- display name
- alias
- URL
- Source ID
- file path
- search ranking position
- Embedding vector
- content hash
- current Version番号のみ

Object名称や分類が変化しても、同一Objectである限り`object_id`は維持する。

### INT-ID-02 — `object_id`を再利用しない

archive、merge、supersede等でObjectが通常利用対象から外れても、既に発行済みの`object_id`を別Objectへ再利用してはならない。

### INT-ID-03 — Conceptも通常Objectと同じIdentity契約を使用する

C-03で確定したConceptは特別な別ID体系を作らず、SGOKB Objectとしてstable `object_id`を持つ。

UPDSの`concept_ref`はこのObject IDを参照する。

### INT-ID-04 — 名前からの再解決をsilent実行しない

保存済み`object_id`が取得不能になった場合、同名Objectを検索して自動的に置換してはならない。

名称一致はIdentity一致ではない。

---

## 5. Knowledge Version参照契約

### INT-VER-01 — IdentityとKnowledge Versionを分離する

次を別概念として扱う。

```text
object_id
= 長期的に同じ対象を指すIdentity

knowledge_version_id
= そのObjectについてacceptedされた特定時点のKnowledge snapshot
```

### INT-VER-02 — accepted Knowledge Versionはimmutable

UPDSが参照したaccepted `knowledge_version_id`の内容をSGOKB側で後から意味的に上書きしてはならない。

訂正・追加が必要な場合は新しいVersionを作成する。

これにより、UPDSは過去推論時のKnowledgeを再現可能にする。

### INT-VER-03 — current参照

UPDSがVersionを明示せずObject Knowledgeを要求した場合、SGOKBは原則としてその時点のcurrent accepted Knowledge Versionを返す。

ただしResponseには、**実際に返した`resolved_version_id`を必ず識別可能にする。**

つまり、

```text
request:
  object_id = obj-A
  version = current / omitted

response:
  object_id = obj-A
  resolved_version_id = ver-7
  is_current = true
```

という意味契約を持つ。

### INT-VER-04 — pinned Version参照

UPDSは再現性が必要な場合、特定のaccepted `knowledge_version_id`を明示して取得できなければならない。

例:

```text
object_id = obj-A
knowledge_version_id = ver-5
```

SGOKBにver-7が存在していても、pinned requestではver-5を返す。

### INT-VER-05 — UPDSは推論に利用したVersionを記録する

Semantic Observation、Pattern、Preference Hypothesis等がSGOKB Knowledgeの意味内容に依存する場合、UPDSは少なくとも論理上、次を追跡できなければならない。

- SGOKB `object_id`
- 実際に利用した`knowledge_version_id`
- retrieved / observed timestamp
- 必要に応じたFacet / Relation scope

単に「currentを使った」という情報だけでは再現性がないため、取得後はresolved Versionを記録する。

### INT-VER-06 — 新Version発生は過去推論を自動改変しない

SGOKB Objectがver-5からver-6へ更新されても、ver-5を用いて構築したUPDS Semantic ObservationやPreference Hypothesisをsilentに書き換えてはならない。

必要なら再評価を行い、新しいObservation / Hypothesis revisionを生成する。

---

## 6. stale / freshness契約

### INT-ST-01 — staleはinvalidと同義ではない

UPDSが参照した`knowledge_version_id`より新しいcurrent VersionがSGOKBに存在する場合、その参照は**stale candidate**となり得る。

しかし、過去時点の推論再現に使用する限り、古いVersionはinvalidではない。

```text
ver-5 used by Hypothesis H1
current = ver-7

H1の歴史的再現
  → ver-5を利用可能

現在のPreference再評価
  → ver-7で再評価候補
```

### INT-ST-02 — freshness判定はVersion比較で行えること

UPDSは保存済み`knowledge_version_id`とSGOKB current Versionを比較し、少なくとも次を区別できる設計を前提とする。

- current
- stale / newer version available
- superseded object
- unavailable
- unresolved

これらの物理status名はUPDS側schemaで決められるが、意味差は保持する。

### INT-ST-03 — push更新通知を初期必須にしない

初期Integration Contractでは、SGOKBがUPDSへObject更新をpush配信することを必須としない。

UPDSは分析開始時、再評価時、定期maintenance等で必要なObjectのcurrent Versionを取得・比較できればよい。

将来event / subscription方式を追加してもよいが、Core契約にはしない。

---

## 7. Object lifecycle / merge / split契約

### INT-LIFE-01 — Object statusを取得可能にする

SGOKB Responseは少なくとも論理上、対象Objectが通常利用可能か、archived / superseded等の状態かを識別可能にする。

### INT-LIFE-02 — merge / supersede時は参照履歴を失わない

Object AがObject Bへ統合された場合、Aの`object_id`を別用途へ再利用しない。

可能であればSGOKBは、

```text
object_id = A
status = superseded
superseded_by = B
```

相当のresolution情報を返せる設計とする。

UPDSがBへ参照を更新する場合も、元のA参照を監査上追跡できることが望ましい。

### INT-LIFE-03 — splitをsilent one-to-one変換しない

Object Aが後からB / Cへ分割された場合、UPDSの既存A参照をBまたはCの一方へ自動変換してはならない。

one-to-many Identity変更は曖昧性があるため、unresolved / review-required相当として扱う。

### INT-LIFE-04 — hard deleteは参照破壊を前提にしない

SGOKBの一般運用ではaccepted Versionや参照中Objectのhard deleteを避ける。

やむを得ず利用不能になった場合、UPDSは既存参照を別Objectへ推測置換せず`unavailable`として保持する。

---

## 8. Knowledge取得scope

### INT-GET-01 — Identity lookup

UPDSは既知の`object_id`からObjectを取得できなければならない。

これは最も基本的な連携操作である。

### INT-GET-02 — batch取得

Selection Event群を分析する用途では複数Objectを扱うため、複数`object_id`をまとめて取得できる論理capabilityを要求する。

Transport上のTool名・件数上限・paginationはPhase Jで確定する。

### INT-GET-03 — Facet選択取得

UPDSは必要なSemantic Facetだけを取得できる設計を優先する。

例:

```text
Character群
  → values / personality / themesのみ

Work群
  → themes / worldview / toneのみ
```

UPDS分析のたびにObject全体や全Evidence corpusを無条件に転送する必要はない。

### INT-GET-04 — Relation取得

UPDSはSGOKBのWorld / Object Relationを取得できなければならない。

初期契約では少なくとも1-hop Relationを扱えることを前提とする。

Relation取得時もPersonal RelationをSGOKBへ混在させない。

### INT-GET-05 — Concept取得

UPDSはConcept `object_id`を通常Objectと同じ仕組みで取得できる。

Concept専用の第二Knowledge APIを必須にしない。

### INT-GET-06 — Evidenceは必要時のみ取得可能にする

UPDSの標準分析ではSGOKB Object Knowledge参照を基本とする。

ただし、Personal Inferenceの監査・説明・再確認等で必要な場合は、Object KnowledgeがgroundingしているSGOKB Evidence / Sourceへ辿れることを維持する。

UPDSがSGOKBのSource corpus全体を第二の正本として複製することは標準契約にしない。

---

## 9. Logical response envelope

C-04では物理JSON Schemaを確定しないが、SGOKB→UPDS Responseは少なくとも次の意味情報を保持できなければならない。

```text
integration response
├─ contract_version
├─ provider = SGOKB
├─ object_id
├─ requested_version_id?       # pinned request時
├─ resolved_version_id
├─ is_current
├─ object_status
├─ primary_class
├─ additional_classes
├─ requested_scope
├─ knowledge
│  ├─ summary / attributes
│  ├─ facets
│  ├─ statements
│  └─ relations
├─ evidence_refs?              # 要求時または必要時
├─ retrieved_at
└─ warnings / resolution info
```

### INT-ENV-01 — 実際に返したVersionを明示する

`resolved_version_id`相当はVersion省略requestでも必須情報とする。

### INT-ENV-02 — request scopeとresponse scopeを識別可能にする

Facet subset等を要求した場合、返却内容がObject全Knowledgeなのか部分scopeなのかを利用側で識別できるようにする。

部分取得を完全Object Knowledge snapshotとして誤認してはならない。

### INT-ENV-03 — warningとKnowledgeを分離する

stale、superseded、missing Facet、partial response等のwarningをKnowledge Statement本文へ埋め込まず、machine-readableに分離できる契約とする。

---

## 10. Facet / Statement / Relationの参照安定性

### INT-REF-01 — cross-version durable referenceは`object_id`を基礎とする

C-04時点ではObject内部の全Statement / Relation record IDがVersionを跨いで永続することを保証しない。

したがってUPDSが長期参照する基礎は、

```text
object_id
+ knowledge_version_id
+ optional facet / statement / relation locator
```

とする。

### INT-REF-02 — Statement IDを永久Identityと仮定しない

後続E-02 / E-03等で明示的にpersistent Statement Identityを採用しない限り、Statement IDやRelation record IDはVersion-scoped referenceとして扱う。

### INT-REF-03 — Facet keyはsemantic scope identifier

`values`、`themes`、`personality`等のFacet keyは検索・取得scopeとして利用できるが、Facet本文自体のVersionは親Object Knowledge Versionへ従う。

---

## 11. Search / discovery契約

### INT-SRCH-01 — UPDSはSGOKB Searchを利用可能

既知ID取得だけでなく、必要に応じてUPDSはSGOKBのLexical / Semantic / Hybrid / Similarity / Relation検索を利用できる。

例:

- Selection targetに関連するConcept候補を検索する。
- 選択Objectに意味的に近いObjectを探索する。
- 共通Facet候補を調査する。

### INT-SRCH-02 — Search resultはPreference Evidenceそのものではない

SGOKB Search ranking、Similarity score、distance等をUser Preference probabilityへ変換してはならない。

C-02の推論境界を維持する。

### INT-SRCH-03 — 推論へ採用した候補はIdentity / Versionへ解決する

Search resultをPersonal Inferenceへ実際に採用する場合、可能な限りstable `object_id`と利用した`knowledge_version_id`へ解決して記録する。

「検索順位3位」等を長期参照にしない。

---

## 12. Cache契約

### INT-CACHE-01 — UPDS cacheを許容する

性能・offline利用のため、UPDSがSGOKB Responseをlocal cacheすることは許容する。

ただしcacheはcanonical Knowledge Storeではない。

### INT-CACHE-02 — cacheは出所を保持する

cache entryは少なくとも次を追跡可能にする。

- SGOKB `object_id`
- `knowledge_version_id`
- Integration Contract version
- retrieved timestamp
- requested scope

### INT-CACHE-03 — cached dataをcurrentとsilent表示しない

SGOKBへfreshness確認できない状態でcacheを利用する場合、そのKnowledgeがcurrentであると保証してはならない。

必要に応じて`cached / freshness unknown`相当として扱う。

### INT-CACHE-04 — cacheから第二正本を作らない

UPDSはcached SGOKB Object Knowledgeを独自に修正・Version管理して、SGOKBと競合する第二のWorld Knowledge正本にしてはならない。

---

## 13. MCP / transport契約

### INT-MCP-01 — 標準transportはMCP read access

UPDSからSGOKBを利用する標準方式はMCP Knowledge Access Layerとする。

MCPはSGOKB Retrieval / Application Coreを呼び出すAdapterであり、SQLite tableをそのまま公開しない。

### INT-MCP-02 — 論理契約をMCP Tool名に固定しすぎない

C-04で必要なのは、

- Object取得
- batch Object取得
- Facet取得
- Relation取得
- Search / Similarity
- 必要時Evidence参照

というcapabilityである。

具体的なTool名、引数、Resource URI、pagination、maximum batch sizeはPhase Jで確定する。

### INT-MCP-03 — DB direct fallbackを行わない

MCPが停止した場合、UPDSが自動的にSGOKB SQLiteを直接開くfallbackを標準動作にしてはならない。

Storage schema couplingを防ぐためである。

### INT-MCP-04 — cloud serviceへsilent fallbackしない

SGOKB / MCPが利用不能な場合、同等Knowledgeを外部cloud APIへ無断送信・取得して処理継続するfallbackを禁止する。

---

## 14. Failure / graceful degradation

### INT-FAIL-01 — Selection Eventの記録はSGOKB停止と分離する

SGOKB / MCPが一時的に利用不能でも、UPDSは可能であればSelection Event等のPersonal-side観測事実を記録できる。

ただしSGOKB Knowledgeを必要とするSemantic enrichmentはpending / unavailable等として扱う。

### INT-FAIL-02 — Knowledge未取得を推測補完しない

SGOKBが取得不能だからという理由で、UPDSがObject definition、Facet、Concept Relation等を独自推測してcanonical SGOKB Knowledgeの代替にしてはならない。

### INT-FAIL-03 — cache利用時はfreshnessを明示する

既存cacheで分析を継続できる場合でも、freshness unknown / stale可能性を保持する。

### INT-FAIL-04 — partial responseを完全Knowledgeとして扱わない

missing Facet、取得上限、provider failure等で部分Responseしか得られない場合、UPDSはそれを完全なObject Knowledgeとして扱ってはならない。

---

## 15. Contract versioning / compatibility

### INT-COMP-01 — Integration Contract versionを持つ

SGOKB→UPDS ResponseにはIntegration Contract / payload schemaのversionを識別できる情報を持たせる。

### INT-COMP-02 — incompatible major changeをsilent受理しない

意味解釈が変わるbreaking changeでは、UPDSが旧契約としてsilent処理しないようにする。

具体的versioning方式はPhase J / Schema設計で確定するが、少なくともmajor compatibility boundaryを表現できるようにする。

### INT-COMP-03 — additive fieldに過剰結合しない

将来SGOKB Responseへ新しいoptional fieldが追加されても、UPDSが未知fieldの存在だけで失敗しないforward-compatible設計を優先する。

### INT-COMP-04 — semantic contract changeを単なるfield追加として隠さない

同じfield名の意味を互換性なく変更する場合はcontract version更新を伴う。

---

## 16. Privacy / data minimization境界

### INT-PRIV-01 — SGOKB requestへPersonal Profileを不要にする

Object Knowledge取得のために、UPDSがPreference Hypothesis、心理Profile、全Selection履歴等をSGOKBへ渡すことを標準要件にしない。

通常は、

- object_id
- Version
- requested Facet / Relation scope
- search query

等、Knowledge取得に必要な最小情報だけを送る。

### INT-PRIV-02 — SGOKB ResponseはWorld / Object Knowledgeを返す

UPDS専用requestであっても、SGOKB側が「このユーザー向けに好みを推測したObject Profile」を返すことを標準機能にしない。

### INT-PRIV-03 — local-firstを維持する

標準MCP連携はlocal-firstとし、外部送信を暗黙に発生させない。

---

## 17. UPDS専用Context/Profileの扱い

### INT-CTX-01 — 初期契約では汎用Knowledge取得を利用する

初期C-04契約では、SGOKBにUPDS専用のPreference分析ロジックを実装しない。

UPDSは汎用Object / Facet / Relation retrievalを利用する。

### INT-CTX-02 — 専用Contextは不足が実証された場合のみ追加する

Phase Kで汎用取得だけでは明確に不足すると確認された場合、UPDS向けContext/Profileを追加検討できる。

その場合もSGOKB側でPersonal Inference自体を実行しない。

---

## 18. Reverse direction / write契約

### INT-WRITE-01 — C-04標準契約はread direction

C-04は主として、

```text
SGOKB → UPDS
```

のKnowledge read contractを定義する。

### INT-WRITE-02 — Preference HypothesisをSGOKBへ書き戻さない

UPDSのPersonal InferenceをSGOKB Object / Concept Knowledgeへ自動書き込みしてはならない。

### INT-WRITE-03 — Concept proposalはcanonical writeと分離する

C-03で定義したConcept proposal等を将来UPDSからSGOKBへ渡す場合でも、proposal / staging / reviewを介し、canonical DBへの直接writeにしない。

### INT-WRITE-04 — MCP writeはPhase Jでreadと分離して判断する

将来MCP write capabilityを設ける場合も、read Toolsとは責務・permission・validation boundaryを分ける。

---

## 19. 代表フロー

### 19.1 Selection EventからSemantic Observation

```text
UPDS
Selection Event
  target_object_id = Character A
        │
        │ MCP get Object / selected Facets
        ▼
SGOKB
object_id = Character A
current_version = v7
values = responsibility
 themes = self-sacrifice
        │
        ▼
UPDS
Semantic Observation
├─ selection_event_id = ...
├─ sgokb_object_id = Character A
├─ sgokb_version_id = v7
└─ observed semantic features
```

### 19.2 過去推論の再現

```text
Hypothesis H1
used:
  Character A v5
  Character B v3

SGOKB current:
  Character A v7
  Character B v4

H1再現
  → A v5 / B v3をpinned取得

現在状態で再評価
  → A v7 / B v4を取得
  → H2等の新revisionを生成
```

### 19.3 Concept参照

```text
SGOKB
Concept X
object_id = concept-X
version = v4
        │
        ▼
UPDS
Pattern P
├─ concept_ref = concept-X
├─ concept_version_ref = v4
└─ supporting Selection Events
```

### 19.4 SGOKB停止時

```text
Selection Event発生
       ↓
UPDSへ記録可能
       ↓
SGOKB / MCP unavailable
       ↓
Semantic enrichment = pending
       ↓
DB direct / cloud fallbackはしない
       ↓
SGOKB復旧後にresolve
```

---

## 20. C-04で確定しない事項

次は後続Phaseで具体化する。

### Phase E

- Object / Version / Relation等の物理DB schema
- persistent / version-scoped内部IDの詳細
- Facet / Statement physical representation

### Phase J

- MCP Toolの正式名称
- Tool input / output JSON Schema
- Resource URI
- pagination / batch size
- error code
- authentication / permission詳細
- concrete contract version format

### Phase K

- 実UPDSを用いた最小ユースケース
- stable ID参照の実機検証
- SGOKB / UPDS Semantic Index分離確認
- UPDS専用Context/Profileの必要性評価

これらを未確定だからという理由で、C-04の責務・Identity・Version・transport boundaryを変更しない。

---

## 21. C-04完了条件チェック

- [x] SGOKB → UPDSの基本依存方向を確定した。
- [x] SGOKBをcanonical Knowledge Provider、UPDSをPersonal Inference Consumerとした。
- [x] stable `object_id`を永続参照の基本単位とした。
- [x] `object_id`と`knowledge_version_id`を分離した。
- [x] current参照時もresolved Versionを返す要件とした。
- [x] pinned Versionによる過去推論再現を定義した。
- [x] staleをinvalidと同一視しない契約を定義した。
- [x] merge / split / unavailable時の参照方針を定義した。
- [x] Object / batch / Facet / Relation / Concept / Evidence取得scopeを定義した。
- [x] Search resultをPreference probabilityとみなさないことを再確認した。
- [x] UPDS cacheをderived cacheとしてのみ許容した。
- [x] MCPを標準transportとし、DB direct accessを標準契約から除外した。
- [x] SGOKB停止時のDB direct / cloud silent fallbackを禁止した。
- [x] Contract versioningの必要性を定義した。
- [x] Personal Profileのdata minimization境界を定義した。
- [x] Personal InferenceのSGOKB canonical write-backを禁止した。
- [x] Phase E / J / Kへの引き継ぎを整理した。

以上をもってC-04を完了とする。
