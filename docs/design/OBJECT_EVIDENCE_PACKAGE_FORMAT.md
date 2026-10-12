# Source Grounded Object Knowledge Base — Object Evidence Package Format

更新日: 2026-10-13

- Task: `G-01 [P0] Object Evidence Package formatを確定する`
- Status: Complete
- Parent: Phase G — Google Drive / ChatGPT交換ワークフロー
- Prerequisites:
  - `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
  - `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
  - `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`
  - `docs/design/EVIDENCE_SELECTION_BUDGET.md`
  - `docs/design/OBJECT_EVIDENCE_RETRIEVAL.md`
- Follow-up:
  - G-02 `manifest.json` schema
  - G-03 `instructions.md`
  - G-04 local staging / Google Drive export
  - G-05 Result受け取り運用

---

## 1. 目的

Object Evidence Packageは、SGOKB内のcanonical Object / Knowledge / Evidenceから、1 ObjectのChatGPT分析に必要な情報だけを選択して外部交換するための**再生成可能なderived artifact**である。

PackageはSource / Evidence StoreやObject Knowledge Versionの正本ではない。Google Drive上のPackage fileをcanonical storeの代わりにしてはならない。

標準flowは次とする。

```text
Canonical Object / current Knowledge
              +
Object Evidence Retrieval / Selection
              ↓
      Local Package Build
              ↓
       Finalized Package
              ↓ explicit export
        Google Drive
              ↓ human operation
          ChatGPT
              ↓
          result.json
```

G-01では、Packageの物理ファイル構成、収録対象、current Knowledge carry-forward規則、Evidence serialization、budget境界、immutability / security境界を確定する。

`manifest.json`の個別field / JSON Schema、Package IDの具体生成方式、manifest canonicalization / hash方式の詳細はG-02へ残す。

---

## 2. Package format v1の基本原則

初期Package format familyを次の論理versionとして扱う。

```text
sgokb.object-evidence-package/1.0
```

G-02でこの値を`manifest.json`のschema / format versionとして機械検証可能にする。

Package v1は次の原則に従う。

1. **1 Package = 1 target Object** とする。
2. Packageは**自己完結したdirectory**とし、外部DB pathやabsolute local pathがなくても内容を読めるようにする。
3. Package directory名やGoogle Drive pathをIdentityとしない。
4. finalized Packageの内容は**immutable**とし、変更が必要なら新Packageをbuildする。
5. Package内Evidenceはcanonical Evidenceの交換表現であり、Source本文の意味を要約・再解釈しない。
6. Resultがgroundingに利用できるEvidenceは、標準workflowではPackageに実際に収録されたEvidence IDに限定する。
7. Raw Artifact全体、Embedding、Vector、検索score等、分析に不要なdataを丸ごとexportしない。
8. Package BuildとExternal Exportは別操作とする。

---

## 3. 標準directory layout

Package v1の標準layoutを次とする。

```text
<package-root>/
├─ manifest.json
├─ instructions.md
├─ current_object.json                # update Packageのみ必須
├─ schema/
│  └─ object-result-v1.schema.json
└─ evidence/
   ├─ source_001.md
   ├─ source_002.md
   ├─ source_003.md
   └─ ...
```

### 3.1 必須file

すべてのPackageに次を含める。

- `manifest.json`
- `instructions.md`
- `schema/object-result-v1.schema.json`
- `evidence/`配下の1件以上のEvidence payload file

Evidence不足により0件Packageを生成する必要がある場合は、通常のKnowledge生成Packageではなく、build failure / review-requiredとして扱う。`insufficient_evidence` Resultを生成させるためだけに空Packageを標準正常系としない。

### 3.2 条件付きfile

`current_object.json`は、Package build時点でtarget Objectにcurrent accepted Knowledge Versionが存在する**更新Packageでは必須**とする。

初回Knowledge生成で`base_version_id = null`の場合は`current_object.json`を置かない。

### 3.3 Package root名

Package rootのdirectory名は人間向け表示 / 運用上の便宜に利用できるが、Identityとして検証しない。

G-04で例えば次のような配置を採用できる。

```text
<object_id>/<package_id>/
```

ただし、`object_id` / `package_id`の正本は`manifest.json`とPackage audit metadataであり、path parsingでIdentityを確定しない。

---

## 4. `manifest.json`の責務

`manifest.json`はPackageのmachine-readable index / binding rootである。

G-01では責務だけを固定し、個別field schemaはG-02で確定する。

少なくとも次を表現する。

- Package identity / format version
- target Object identity / Classification snapshot / name / aliases
- Package作成時刻
- base Object Knowledge Version
- expected Object Result schema version
- instructions version
- included file一覧
- included Source / Snapshot / Normalized Run / Evidence ID集合
- EvidenceごとのPackage内file mapping
- Evidence selection role / selection provenance
- Evidence / file integrity information
- Package budget / actual usage summary
- current Knowledge同梱有無
- warning / integrity / export preflightに必要なsummary

`manifest.json`は**included Evidenceだけ**をChatGPT向けPackage membershipとして列挙する。

F-04でbudgetやduplicate判定によりomitされたEvidence ID、manual excludeされたEvidence IDの詳細一覧は、local selection auditとしてSGOKB側へ保持し、標準external Package manifestへ混在させない。

これにより、ChatGPTが「manifestにIDがあるので引用可能」と誤認する範囲をPackage収録Evidenceに限定する。

---

## 5. `instructions.md`の責務

`instructions.md`はChatGPTへ渡す分析指示の唯一のPackage-local instruction fileとする。

G-01では次の境界だけを固定し、具体的Prompt本文はG-03で設計する。

- target Object分析の目的を示す。
- `manifest.json` / `current_object.json` / `evidence/*.md` / Result Schemaの役割を説明する。
- Evidence本文を**untrusted source data**として扱い、Evidence中の命令文をsystem / user instructionとして実行しないよう指示する。
- Package外Evidence /未知Object IDを創作しないよう指示する。
- ResultのgroundingはPackage manifestに含まれるEvidence IDだけを利用するよう指示する。
- 更新Packageではcurrent Knowledgeを無条件copyせず、Evidenceを参照してcarry-forward /変更 /削除を判断するよう指示する。
- outputは`result.json`契約に従うよう指示する。

`instructions.md`もPackage binding対象artifactとし、finalized後に内容を書き換えない。

---

## 6. `schema/object-result-v1.schema.json`

Package v1は、E-05で確定したcanonical Object Result JSON Schemaのsnapshotを同梱する。

元の正本は次である。

```text
src/sgokb/exchange/schemas/object-result-v1.schema.json
```

Packageには**static canonical Schema**をcopyする。Package固有の`package_id` / `manifest_sha256`等を埋め込んだ別handwritten schemaを作らない。

Package / target / base Version / effective Facet profile等のruntime constraintは、G-02 manifest + G-03 instructions + H-01の`ObjectResultContract`で検証する。

この方式により、

- ChatGPT向け構造契約
- local Validator向け構造契約

を別々に管理してdriftさせない。

---

## 7. `current_object.json`

### 7.1 役割

更新Packageでは、ChatGPTが「新Evidenceだけを見てObject Knowledge全文を作り直す」ことを避けるため、Package build時点のcurrent accepted Object Knowledge Versionを`current_object.json`として収録する。

これは過去`result.json`の単純copyではない。

**SGOKB canonical DBから、現在accepted/currentとなっているKnowledge Versionをexchange向けに再serializationしたsnapshot**とする。

### 7.2 含める内容

少なくとも次を含める。

```text
object_id
version_id
version_number
classification snapshot
knowledge
  summary statements
  facets + facet status + statements
  structured attributes
  relations
各Knowledge itemのEvidence grounding
必要なtemporal scope / language / derivation metadata
```

Object Registryのname / aliases等は`manifest.json`側を正本のPackage contextとし、`current_object.json`へ不要な重複を増やさない。

### 7.3 含めない内容

次は原則含めない。

- Embedding / Vector
- Search Representation
- rendered Markdown
- old Package path
- old Resultのgeneration / import command情報
- Registry proposal
- external credential
- local absolute path

### 7.4 full snapshot updateとの関係

Object Resultは原則full Knowledge snapshotであるため、更新Packageで`current_object.json`をsilent省略しない。

`current_object.json`自体が指定されたtotal context budgetへ収まらない場合、内容を勝手に削って通常Packageとして続行せず、Package buildをblockしてoperatorへ返す。

limited / scoped update方式を将来導入する場合は、通常full updateと異なる明示contractを追加する。

---

## 8. current Knowledge carry-forward Evidence

### 8.1 carry-forward集合

更新Packageでは、`current_object.json`内のcanonical Knowledge itemが参照しているEvidence IDを重複除去して`carry_forward_evidence_ids`相当の集合とする。

対象は少なくとも、current Version内の次で参照されるEvidenceである。

- summary Statement
- Facet Statement
- known structured Attribute
- Relation
- その他accepted Versionのgrounded canonical Knowledge item

Evidence roleが`supports`だけでなく`contradicts` / `contextualizes`であっても、current Knowledgeの根拠として参照されていれば集合へ含める。

### 8.2 historical Evidenceも許容する

current Knowledgeが過去Snapshot /過去Normalization RunのEvidenceを参照している場合、そのEvidenceをlatest/effective scope外という理由で捨てない。

G-01 Package Builderはcarry-forward EvidenceをF-03の通常effective scopeへ追加する**system-protected include**として扱う。

これにより、

```text
current Knowledge
  -> historical Evidence E-old
new retrieval
  -> effective Evidence E-new
```

を同じ更新Packageへ含められる。

### 8.3 budget上の扱い

carry-forward EvidenceはF-04の`protected_evidence_ids`として扱い、通常retrieval candidateより先に確保する。

manual includeと同様に、budget不足を理由としてsilent omissionしてはならない。

carry-forward Evidence集合だけでhard budgetを超える場合、標準Package buildは**失敗**とする。

operatorは次のいずれかを選ぶ。

- Evidence budgetを明示的に増やす。
- current Knowledgeを先に別Versionとして整理する。
- 将来導入されるlimited/scoped update contractを明示利用する。

通常full updateで旧Knowledge groundingを見せずに全文再生成させるfallbackは行わない。

### 8.4 provenance異常

current Versionが参照するEvidenceについて、

- Evidence record不存在
- Snapshot / Run / Source chain破損
- required artifact integrity failure

等がある場合、そのEvidenceを正常なcarry-forward入力としてsilent利用しない。

standard Package buildはblockまたはreview-requiredとし、Provenance修復または明示的な別workflowへ戻す。

---

## 9. Evidence selectionとPackage membership

Package Evidence集合は次の順序で構築する。

```text
1. current Knowledge grounding Evidenceを収集
2. operator manual includeを収集
3. F-03 Object Evidence Retrievalを実行
4. carry-forward / manual includeをprotected candidate化
5. F-04 EvidencePackageSelectorを実行
6. Source diversity + relevance fill
7. Package-local duplicate / overlap suppression
8. finalized included Evidence集合を確定
```

標準Resultが引用可能なのは、Step 8で確定し`manifest.json`へincludedとして記録されたEvidence IDだけである。

F-03 candidateだったがF-04でomitされたEvidenceは、DBには存在していても当該Package Resultから引用してはならない。

ChatGPTが追加Sourceの必要性を判断した場合は、架空Evidence IDを作らず、gap / unresolved informationとして返し、Source Capture → 新Package Buildへ戻す。

---

## 10. Evidence payload file

### 10.1 grouping unit

`evidence/source_NNN.md`は、単なる`source_id`単位ではなく次の**Source generation**単位でgroupingする。

```text
(source_id, snapshot_id, normalization_run_id)
```

同一Sourceでもhistorical carry-forward Evidenceと新しいeffective generationが混在する場合は別fileへ分ける。

これにより、異なる取得時点・Normalizer世代のEvidenceを1つのSource本文のように誤認させない。

### 10.2 file naming

file名は次のようなzero-padded ordinalを利用する。

```text
source_001.md
source_002.md
...
```

Source IDをfilesystem pathへ直接埋め込むことを必須としない。file名はIdentityではなく、`manifest.json`がfileとSource generationを対応付ける。

### 10.3 Source header

各file冒頭には、分析上必要な範囲のSource / Snapshot metadataを明示する。

例:

```text
source_id
snapshot_id
normalization_run_id
source label / title
observed locator
publication / update time（判明時）
snapshot capture time
language（判明時）
resource / genre / publisher分類（判明時）
対象Objectとのsubject_relationship（確認済みの場合）
```

publication time / capture timeを混同しない。

historical Snapshot fileでは、そのSnapshotで観測されたtitle / locator / metadataを優先し、現在のSource metadataだけで過去世代を上書き表現しない。

### 10.4 Evidence block

1 Evidence blockは少なくとも次を表示する。

```text
evidence_id
extraction mode
source location / section / block / page / timestamp等
content hash（利用可能な場合）
Evidence content
```

F-03の`retrieval_score`をEvidence本文の品質・信頼度のように表示しない。

selection reason / selected_by / budget cost等の監査metadataは原則`manifest.json`側へ置き、Evidence本文を分析に必要なSource contextへ集中させる。

### 10.5 Evidence本文のserialization

Evidence本文はcanonical `Evidence.content`を要約・翻訳・言い換えせず収録する。

Markdown構造との衝突を避けるため、Evidence本文はcode fence等の明確なdata delimiter内へ置く。serializerは本文中のbacktick連続長を確認し、本文より長いfenceを選ぶ等により、Evidence本文を切断・改変しない。

Evidence file上のheading / metadataはPackage representationであり、canonical Evidence contentそのものではない。

---

## 11. Evidence file ordering

Package内file orderはF-04で最初に採用されたEvidenceのselection orderを基準に、Source generationごとに決定する。

同一Source generation内では、可能な限り元資料上のlocation順でEvidence blockを並べる。

locationで順序を確定できない場合はF-04 selection orderを維持し、最後にstable `evidence_id`等でdeterministic tie-breakする。

この順序はtruth / authority rankingではなく、再現可能性と文脈可読性のための表示順である。

---

## 12. Budget contract

### 12.1 F-04 Evidence budgetを維持する

Evidence本文の基本hard limitはF-04を継続利用する。

初期default:

```text
max_estimated_tokens = 12,000
max_bytes            = 65,536
max_items            = 64
```

G-01で別の第二Evidence budgetを新設しない。

### 12.2 Package overheadをEvidence budgetと分離する

Package全体にはEvidence以外に次のoverheadがある。

- `manifest.json`
- `instructions.md`
- `current_object.json`
- Object Result JSON Schema
- Evidence file header / delimiter

特定ChatGPT modelのcontext上限をSGOKB package formatへ固定値として埋め込まない。

標準builderは少なくとも次を記録 / preflight表示可能にする。

- Evidence estimated tokens
- non-Evidence estimated tokens
- Package total estimated tokens
- Evidence bytes / item数 / Source generation数

### 12.3 total context budgetが指定された場合

caller / destination profileが`max_package_estimated_tokens`相当のtotal budgetを明示した場合、Package Builderはmandatory non-Evidence overheadを先に見積もり、残量をF-04へ渡すEvidence budgetへ反映する。

```text
total budget
 - mandatory instructions/schema/manifest estimate
 - current_object estimate
 = Evidenceに利用可能なtoken budget
```

carry-forward protected Evidenceが残量へ収まらない場合はsilent omissionせずbuild failureとする。

final serialization後にtotal budgetを超えた場合も、finalized Packageとしてexportせずrebuildへ戻す。

### 12.4 current Knowledgeをbudget都合でsilent truncationしない

`current_object.json`を途中まで切る、Facetを一部だけ落とす等のimplicit truncationは禁止する。

標準full updateでは、current Knowledge snapshotは全体を含めるか、Package buildを失敗させる。

---

## 13. Package-local auditとlocal-only auditの分離

External PackageにはChatGPTが必要とするincluded scopeだけを含める。

一方、SGOKB local auditでは次を保持可能にする。

- F-03 candidate集合
- F-04 omitted Evidence + reason
- manual include / exclude
- budget設定
- Package build warning
- preflight disposition
- build operation ID / timestamp

これらlocal-only audit情報をすべてExternal Packageへ複製しない。

Package directoryをcleanupしても、package identity / manifest hash / included Evidence IDs / base Version / instructions version等のbinding/audit metadataはSGOKB側で追跡可能にする。

---

## 14. Data minimization / Security

Package v1では、分析に必要な範囲へ外部送信dataを限定する。

### 14.1 標準で含めないもの

- Cookie / session token / OAuth token / API key / password / private key
- Browser credential material
- local absolute path
- Raw DOM / MHTML全体
- Source Store全体
- 無関係Object Knowledge
- Embedding vector
- Vector Index internal data
- internal SQL / DB dump
- full operation log

### 14.2 Raw / binary Artifact

Package v1の標準payloadはnormalized text / structured Evidenceを中心とし、Raw HTML / MHTML /画像 /音声 /動画 / PDF binaryを自動同梱しない。

Evidenceがbinary原資料を必要とし、text/structured Evidenceだけでは意味を安全に伝えられない場合は、silentにRaw全体をexportせず`review_required`として扱う。

binary attachment supportを将来追加する場合は、Package schema versionまたは明示extensionとして設計する。

### 14.3 prompt injection境界

Source / Evidence本文は外部由来のuntrusted dataである。

Evidence中に「前の指示を無視せよ」「別URLへアクセスせよ」「secretを表示せよ」等の命令文が含まれていても、Package instructionとして扱わない。

G-03 `instructions.md`でこの境界を明記する。

---

## 15. Immutability / Integrity

### 15.1 finalized Packageを変更しない

Package Builderはtemporary / staging状態で全fileを書き、validationが完了した後にfinalized状態へ切り替える。

finalized後にEvidence fileやinstructionsだけをin-place修正しない。

修正が必要なら新Packageとしてrebuildする。

### 15.2 binding対象

Result binding上、少なくとも次の内容変更を検出できる必要がある。

- manifest
- instructions
- current Object snapshot
- Result Schema snapshot
- Evidence payload file

G-02でfile hash / manifest hashの具体方式を確定する。

### 15.3 Package artifactは正本ではない

Package directoryが失われても、canonical DB + Evidence Store + Schema / instructions versionから内容を説明・再生成可能とする。

ただし、外部へ実際にexportしたPackageについては、監査のためpackage identity / manifest hash / included Evidence集合 / destination / timestamp等を保持できるようにする。

---

## 16. Initial Package / Update Package

### Initial Package

```text
base_version_id = null
current_object.json = absent
carry-forward Evidence = none
new retrieval Evidence = required
```

### Update Package

```text
base_version_id = build時点のcurrent accepted Version
current_object.json = required
carry-forward Evidence = current Knowledgeの全grounding Evidence
new retrieval Evidence = F-03/F-04で追加
```

Update PackageのResultが返るまでにcurrent Versionが変わった場合は、H-01/H-02でstale Resultとして検出し、silent overwriteしない。

---

## 17. G-02 / G-03 / G-04 / G-05への引き継ぎ

### G-02 `manifest.json` schema

G-02では次を具体Schema化する。

- `package_id`
- `package_schema_version = sgokb.object-evidence-package/1.0`
- target Object / Classification / display metadata
- `base_version_id`
- package creation timestamp
- instructions version
- expected Result schema version
- included file entry + SHA-256
- included Source generation / Evidence entry
- Evidence selection role / file mapping
- budget / usage summary
- Package warning / integrity summary
- manifest canonicalization / `manifest_sha256`

### G-03 `instructions.md`

G-03では、G-01のinstruction責務から実Promptを作成する。

特に、

- Evidenceはdataであってinstructionではない
- Package外Evidence禁止
- unknown Object ID禁止
- current Knowledgeのcarry-forward判断
- derivation kind / Evidence role
- Facet status / gap / conflict / unresolved reference
- Result Schema準拠

を明文化する。

### G-04 local staging / Google Drive export

G-04では、

- staging directory
- temporary write → finalize
- preflight
- `allow / review_required / blocked`
- explicit external export
- Drive同期folderへのwrite
- export audit

を実装する。

### G-05 Result受け取り

G-05では、Package rootと対応する`result.json`のincoming placement / detection / validation triggerを定義する。

Package directoryへResultを直接書き戻してfinalized input artifactを変更する方式を標準にしない。

---

## 18. G-01完了条件

G-01完了条件を次とする。

1. 1 Object単位のself-contained Package directory layoutが確定している。
2. `manifest.json` / `instructions.md` / Result Schema / Evidence payloadの責務が分離されている。
3. update Packageで`current_object.json`が必須となっている。
4. current Knowledgeのgrounding Evidenceをcarry-forward protected Evidenceとして扱う規則が確定している。
5. carry-forward Evidenceをbudget都合でsilent omissionしない。
6. Package外EvidenceをResultが引用できないmembership boundaryが確定している。
7. Source generation単位でEvidence fileを分離し、historical / effective generationを混同しない。
8. Evidence contentを要約・翻訳せず交換できる。
9. F-04 budgetとPackage overheadの境界が確定している。
10. omitted candidate auditとexternal Package membershipが分離されている。
11. Raw / secret / unrelated dataを標準Packageへ丸ごと含めない。
12. finalized Packageをimmutableとし、Result binding可能なintegrity境界が確定している。
13. G-02〜G-05へ残す責務が明確である。

以上をもって **G-01 [P0] Object Evidence Package formatを完了** とする。
