# Source Grounded Object Knowledge Base — 非機能要件

更新日: 2026-10-11

- Task: `B-07 [P1] 非機能要件を更新する`
- Status: Accepted
- Parent: Phase B — 要件定義の全面更新
- Inputs:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
  - `docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md`
- Next: `Phase C — SGOKB / UPDS責務境界`

---

## 1. 目的

本書は、SGOKBが長期的なKnowledge Baseとして成立するための非機能要件を定義する。

B-01〜B-06では、SGOKBの目的、Object、Source / Evidence、Object Result、Search / Retrieval、人間工程 / 自動工程の論理要件を確定した。B-07では、それらが実運用で壊れず、復旧可能で、外部Serviceに依存しすぎず、性能を測定可能な状態で維持されるための横断要件を固定する。

本書では特に次を扱う。

- local-first / offline継続利用。
- authoritative dataと再生成可能なderived dataの区別。
- crash / partial failure時の整合性。
- Provenance integrity。
- Versioning / immutability。
- backup / restore / retention / hard delete。
- external processing / data egressのsecurity / privacy。
- credential / log / untrusted inputの扱い。
- Background Jobのretry / recovery。
- Embedding / Vector Index障害時のgraceful degradation。
- provider / model / backend交換可能性。
- 1 Object local automatic processingの10分Acceptance。
- interactive searchの応答目標。
- observability / audit / performance measurement。

本書は非機能上の契約を定義する。具体的DB column、backup script、job queue、credential backend、CLI option、GUI、retry回数、Vector backend、Embedding model等は後続Phaseで実装・選定する。

---

## 2. 結論

SGOKBの非機能設計は、次の原則を基準とする。

1. **Local-first** — 正本Knowledge、Source / Evidence、主要な検索・閲覧機能は特定cloud serviceなしで成立させる。
2. **Canonical dataを優先** — SQLite正本、Raw、Version、Evidence / Provenanceを派生Indexより優先して保全する。
3. **Derived dataは再生成可能にする** — FTS補助Index、Search Representation、Embedding、Vector Index、Markdown、Package等を正本としない。
4. **Failure isolation** — Embedding / Index / MCP / external serviceが壊れても、正本dataを破壊せず利用可能な機能を継続する。
5. **No silent fallback** — local provider障害を理由に、許可なくcloud providerへ送信しない。
6. **Append / Version優先** — 過去VersionやProvenanceを上書きするより、新しい世代を追加する。
7. **Detectable degradation** — stale / missing / corruptなIndexやProvenanceを正常状態として黙って利用しない。
8. **Recoverable operation** — backupから正本を復元し、derived dataを再構築できる。
9. **Explicit egress** — local dataを外部へ送る操作はB-06のHuman Decision boundaryを維持する。
10. **Measurable performance** — 10分目標や検索latencyを、hardware / workload / version付きで再現可能に測定する。

SGOKBの優先順位は次とする。

```text
Data integrity / provenance
  > recoverability
  > correctness of state / explicit boundaries
  > availability / graceful degradation
  > performance
  > convenience / automation rate
```

性能向上のために、Provenance破壊、silent cloud fallback、Version上書き、未検証Result自動Importを許容しない。

---

## 3. Data criticality / source of truth

### NFR-DAT-01 — Dataを正本性によって区分する

SGOKBのdata / artifactは少なくとも次の4区分で扱う。

| 区分 | 意味 | 代表例 | 消失時の扱い |
|---|---|---|---|
| Canonical / Authoritative | SGOKBの正本・Identity・履歴・Provenance | SQLite内Object / Version / Registry / Source / Snapshot / Evidence Link、Raw Artifact | backupからrestoreが必要 |
| Provenance-retained derived | 元から再計算可能でも、過去Versionから参照されるためIdentity /世代を保持する | Normalized Run、Evidence、import済みoriginal Result artifact、operation provenance | 参照中は任意削除不可 |
| Rebuildable derived | 正本から再生成でき、Identity上の正本ではない | Search Representation、Embedding、Vector Index、補助FTS、Markdown render | 削除 / rebuild可能 |
| Transient / exchange | 処理途中または外部交換用 | local Package staging、temporary files、cache | policyによりcleanup可能 |

EvidenceはRawから再抽出できる可能性があっても、既存Object Knowledge Versionが特定`evidence_id`へgroundingしているため、参照中のEvidenceを単純なcacheとして扱わない。

### NFR-DAT-02 — SQLiteをObject Knowledgeのcanonical storeとする

Object Identity、Registry、accepted Object Knowledge Version、Relation、Facet / Statement、Evidence Link、Source / Snapshot metadata等の構造化正本はSQLiteを基準とする。

Vector backend、MCP Server、Google Drive、Markdown、ChatGPT Result fileをSQLite正本の代替にしない。

### NFR-DAT-03 — Raw Artifactを原資料のcanonical artifactとする

Source Capture / Importで保持するRaw Artifactは、Evidence再抽出・Provenance監査の原資料として保全する。

Object KnowledgeやNormalized textが存在することを理由にRawを自動削除しない。

### NFR-DAT-04 — original Result artifactを監査可能に保持する

accepted Object Knowledge Versionを生成した外部`result.json`は、少なくともVersionが存在する間、その原artifactまたは内容hash +不変保存参照を追跡可能にする。

ImporterがnormalizationしたDB内容だけを残し、入力されたResultを完全に失う設計を標準にしない。

### NFR-DAT-05 — Package payloadとPackage audit metadataを分離する

Object Evidence Packageの複製本文は交換用derived artifactであり、永続正本ではない。

一方、少なくとも次はResult binding / export auditのため保持可能にする。

- package identity
- manifest / schema version
- package hash
- target Object
- base Version
- included Evidence ID集合
- instructions version
- exported destination / timestamp（exportした場合）

Package directory本体がcleanupされても、「何をChatGPTへ渡したか」をDB + Evidence Storeから説明できることを目指す。

---

## 4. Local-first / Offline要件

### NFR-OFF-01 — Core read pathはInternet接続を必須にしない

既にlocalへ保存されたdataについて、Internetが利用できない状態でも少なくとも次を利用可能にする。

- Object ID / name / alias lookup
- current accepted Knowledge表示
- Source / Evidence表示
- Relation traversal
- Lexical Search
- 既存local Vector Indexが利用可能な場合のSemantic / Similarity Search
- local rendering
- local MCP read（MCP Server自体が起動している場合）

### NFR-OFF-02 — Application起動をcloud availabilityへ依存させない

SGOKB Coreの起動時に、ChatGPT、Google Drive、外部Embedding API、外部Vector DB等へ接続できないことを理由として、local canonical DBを開けない状態にしない。

外部Service health checkを行う場合も、local core startupを不必要にblockしない。

### NFR-OFF-03 — Offline時に利用不能な機能を明示する

Internetや外部Serviceが必要な処理は、利用不能であることを明示して停止する。

例:

- Web Source Captureのnetwork取得。
- Google Drive sync / external export completion確認。
- ChatGPT Web/Desktop分析。
- external Embedding / reranker / OCR等。

失敗をlocal data corruptionとして扱わない。

### NFR-OFF-04 — 外部Service停止中もlocal workを蓄積できる

Google Drive / ChatGPT等が利用できない場合でも、可能な範囲で次を継続できることを目指す。

- Source Import / Normalize / Evidence生成。
- Object登録。
- Package local build。
- accepted Knowledge閲覧・検索。
- local providerによるEmbedding / indexing。

外部分析待ちPackageは`ready for export`等の状態で保持し、再接続後に明示exportできる。

### NFR-OFF-05 — local provider障害時にcloudへsilent fallbackしない

local Embedding / reranker / OCR等が失敗した場合、設定されていないcloud providerへ自動送信して処理を継続してはならない。

provider切替がexternal data egressを伴う場合はB-06のExternal Processing boundaryを適用する。

---

## 5. Availability / Graceful degradation

### NFR-AVL-01 — Derived subsystem障害をcanonical storeから隔離する

次の障害だけを理由にaccepted Object Knowledge Versionをrollback / deleteしてはならない。

- Embedding generation failure
- Vector Index update failure
- FTS rebuild failure
- Markdown rendering failure
- MCP Server failure
- Google Drive sync failure
- external AI service failure

### NFR-AVL-02 — Vector Search停止時もIdentity / Lexical readを継続する

Vector backendが停止・破損・未構築の場合、可能であれば次へgraceful degradationする。

```text
Identity Lookup / Object Read
  → 利用継続

Lexical Search
  → 利用継続

Semantic / Similarity Search
  → unavailable / degradedを明示
```

Semantic resultがないことを「類似Objectが存在しない」と誤表示しない。

### NFR-AVL-03 — stale Indexをcurrentとしてsilent利用しない

current Object Knowledge VersionとIndex membership / representation versionが一致しない場合、Indexを`stale`相当として検出可能にする。

検索側は少なくとも次のいずれかを選択できなければならない。

- stale semantic resultを使わずLexicalへfallbackする。
- staleであることを明示して限定利用する。
- Index更新完了までSemantic機能を一時停止する。

古いVectorを新VersionのVectorであるかのように表示しない。

### NFR-AVL-04 — MCP停止でDB / CLIを失わない

MCPはAccess Adapterであり、canonical storeではない。

MCP Serverが停止しても、local CLI / Application層からObject Knowledgeを閲覧・保守できなければならない。

### NFR-AVL-05 — 部分的なSource障害を全体障害に拡大しない

一部Raw Artifact欠損、checksum mismatch、Normalizer失敗等があっても、影響範囲を識別し、無関係なSource / Objectの閲覧・検索を可能な限り継続する。

壊れたProvenanceを正常扱いして新Knowledge生成へ使わない。

---

## 6. Transaction / Crash consistency

### NFR-TXN-01 — canonical writeはtransaction boundaryを持つ

Object Registry、Knowledge Version Import、current Version切替、Relation / Evidence Link更新等のcanonical writeは、途中失敗によって半端な正本状態を残さないtransaction boundaryを持たなければならない。

### NFR-TXN-02 — Version creationとcurrent pointerを整合させる

新Version作成中にprocessが停止した場合、少なくとも次のどちらかへ復旧できる設計とする。

- 新Versionが未accepted /未currentとして残る。
- transaction全体がrollbackし旧currentを維持する。

存在しない / incomplete Versionを`current_version`が指す状態を許容しない。

### NFR-TXN-03 — derived processingをcanonical transactionから分離する

Embedding / Vector Index / rendering等はcanonical Version commit後に失敗し得る。

これらの失敗を理由として正しくcommitされたVersionを破壊しない。

canonical commit後は、派生処理を`pending / running / ready / failed / stale`等の独立状態として追跡可能にする。

### NFR-TXN-04 — file outputはpartial fileを完成品として見せない

Package、Result copy、backup manifest、rendered artifact等のfile writeは、可能な限りtemporary file / stagingを経由し、完全に書き終えた後に完成状態へ切り替える。

process killやdisk fullで途中fileが生成されてもvalid artifactとして誤認しない。

### NFR-TXN-05 — duplicate / retryをidempotentに扱う

少なくとも次でretry /重複検出を可能にする。

- Capture Bundle Import (`capture_id`等)
- Result Import (artifact hash / provenance)
- Search Representation build
- Embedding upsert
- Index rebuild

同じ入力をretryしただけで不必要なObject / Version / Evidenceを無制限に増やさない。

---

## 7. Provenance / Integrity要件

### NFR-INT-01 — Provenance chainを機械検証可能にする

少なくとも次のchainについて、参照先存在と基本整合性を検証できなければならない。

```text
Object Knowledge Version
  → Statement / Attribute / Relation
  → Evidence Link
  → Evidence
  → Normalized Run
  → Snapshot
  → Raw Artifact
  → Source
```

### NFR-INT-02 — Artifact checksumを利用する

Raw Artifact、Package / Result等、byte-level integrityに意味があるartifactはhash / checksumを保持できることを要件とする。

checksum不一致を正常dataと同一扱いしない。

### NFR-INT-03 — Integrity状態を少なくとも3段階で扱える

実装上の名称は後続Phaseで確定してよいが、論理上次を区別できることを要求する。

- healthy / verified: 必要な参照とartifactが確認できる。
- degraded / warning: 一部派生dataやoptional artifactが欠落しているが、canonical dataは利用可能。
- broken: 必須Provenance参照やcanonical artifactが欠落・不一致で、新規Knowledge生成へ安全に使用できない。

### NFR-INT-04 — broken provenanceを新Knowledgeへsilent利用しない

過去Knowledge Versionが壊れたEvidenceを参照している場合、そのVersion自体を履歴として表示することはできる。

しかし、新しいPackage / Result generationでbroken Evidenceを通常Evidenceとして無警告利用しない。

### NFR-INT-05 — quick checkとfull checkを分離可能にする

毎回すべてのRaw fileを再hashすることを必須にしない。

少なくとも将来、次を分離できる設計とする。

- quick integrity check: DB参照、file存在、主要metadata。
- full integrity check: checksum、全Provenance chain、Index membership等。

full checkはmanual / scheduled maintenanceとして実行可能にする。

### NFR-INT-06 — Backup自体も検証可能にする

backupは作成成功messageだけを信頼せず、manifest / checksum / DB integrity等を使ってrestore可能性を確認できることを要件とする。

---

## 8. Versioning / Immutability

### NFR-VER-01 — accepted Knowledge Versionを論理的にimmutableとする

accepted Object Knowledge Versionの意味内容を後からin-place編集し、同じVersion IDの意味を変更することを標準操作にしない。

修正は原則、新Version作成で表現する。

### NFR-VER-02 — rollbackを過去Version破壊で表現しない

rollbackは過去Versionへcurrent pointerを戻す、または明示的promotion eventとして扱い、後続Versionを削除して履歴をなかったことにする方式を標準にしない。

### NFR-VER-03 — Source / Snapshot / Evidence historyも上書きしない

Source更新、recapture、Normalizer変更、Evidence再生成は新Snapshot / Run / Evidence generationとして保持し、過去Provenanceを上書きしない。

### NFR-VER-04 — IDを再利用しない

削除・ArchiveされたObject / Source / Version等のstable IDを別の意味対象へ再利用しない。

### NFR-VER-05 — schema migrationでIdentityを不用意に再発番しない

project rename、table rename、backend交換、schema version更新だけを理由として既存Object / Source / Snapshot / Evidence IDを再発番しない。

---

## 9. Backup / Restore

### NFR-BKP-01 — canonical dataのbackupを必須運用として扱う

最低限、次をbackup対象に含める。

- canonical SQLite DB。
- Raw Artifact store。
- imported Result artifact / audit artifactのうちaccepted Versionへ必要なもの。
- DB外に置くcanonical / provenance-bearing manifest。
- recoveryに必要なconfiguration metadata（secretそのものを平文backupすることは要求しない）。

Vector Index、Embedding cache、Markdown、Package payload等のrebuildable derived dataは、backup容量削減のため除外可能とする。

### NFR-BKP-02 — backupはDBとfile storeの整合点を記録する

active DB fileを単純copyして壊れたbackupを作らない。

SQLite Online Backup相当、write quiesce、snapshot等の安全な方法を利用し、backup generationごとに少なくとも次を記録できるようにする。

- backup timestamp
- schema version
- application / migration version
- DB integrity result
- artifact count / manifest
- hash / checksum（適用可能な範囲）

具体的方法は運用設計で決定する。

### NFR-BKP-03 — RPO目標を24時間以内とする

通常運用におけるcanonical dataのRecovery Point Objectiveは、**24時間以内**を初期目標とする。

このため、production運用では少なくとも日次相当でbackup generationを作成できることを要件とする。

Source Captureや大量Import直後に任意manual backupを実行できることも望ましい。

### NFR-BKP-04 — RTO目標を4時間以内とする

有効なbackupが存在し、同等のlocal machine / software環境を利用できる前提で、canonical DB + Raw / Provenanceを再利用可能な状態へ戻すRecovery Time Objectiveを**4時間以内**とする。

この4時間には、全Embedding / Vector Indexの完全再構築完了を必須としない。

canonical read + Lexical / minimum retrievalを先に復旧し、Semantic Indexは後からrebuildできる。

### NFR-BKP-05 — backup copyをactive data directoryと分離する

backupをactive SQLite / Raw storeと同一directoryだけに置き、誤削除・directory corruptionで同時消失する状態を標準にしない。

少なくとも別backup destinationを指定可能にする。

別physical device / NAS / cloud等のoff-device copyを利用できる設計を推奨するが、cloud destinationはExternal Data Egress policyを適用し、無断送信しない。

### NFR-BKP-06 — backup retentionの初期基準を持つ

production用default policyは少なくとも次の世代を保持できることを目標とする。

- daily generation: 直近7世代以上。
- weekly generation: 直近4世代以上。

monthly / long-term archiveは容量・運用に応じて追加可能とする。

具体的scheduler / rotation実装は後続運用設計で決定する。

### NFR-BKP-07 — restore testを実施可能にする

backupは作成するだけでなく、別path / test environmentへrestoreし、DB参照・Raw存在・Provenance integrityを検証できなければならない。

Release / schema migration前後、および定期運用でrestore testを実施できる手順を用意する。

---

## 10. Retention / Hard delete

### NFR-RET-01 — 参照中canonical / provenance dataを自動purgeしない

次は通常retention cleanupで自動削除しない。

- current / historical Object Knowledge Versionが参照するEvidence。
- そのEvidenceのNormalized Run / Snapshot / Raw Artifact。
- accepted Versionのoriginal Result provenance。
- stable Identity / Registry history。

### NFR-RET-02 — historical Knowledge Versionを既定で保持する

Object Knowledge Versionはrollback / audit / change analysisのため、既定では期限による自動削除を行わない。

容量問題が生じた場合も、まずrebuildable derived data / duplicate exchange artifactをcleanupし、Knowledge historyを優先して保持する。

### NFR-RET-03 — Hard deleteを管理操作とする

Canonical Object / Source / Snapshot / Evidence / VersionのHard deleteは日常操作にしない。

Hard deleteを行う場合は少なくとも次を要求する。

- 明示的な管理操作。
- dependency / reference impactの事前表示。
- dry-runまたはpreview。
- referenced dataを削除する場合の強いwarning / override。
- Stable IDを再利用しないこと。
- audit record。

### NFR-RET-04 — ArchiveとDeleteを区別する

通常利用対象から外すだけならArchiveを優先し、物理削除と同一視しない。

Object / SourceをArchiveしても過去Version / Evidence / external referenceが壊れないことを要求する。

### NFR-RET-05 — Rebuildable derived dataは容量管理のため削除可能とする

次はcanonical参照を壊さないことを確認した上で、再生成可能なためcleanup対象にできる。

- obsolete Vector Index generation。
- Embedding cache。
- rendered Markdown。
- local Package staging copy。
- temporary / failed build directory。

ただしPackage audit metadataやaccepted VersionへのResult provenanceまで同時削除しない。

---

## 11. Security / Privacy / External Data Egress

### NFR-SEC-01 — Local-onlyをdefault security postureとする

SGOKB Coreは、設定しない限りlocal dataを外部Serviceへ送信しないことをdefaultとする。

External Export / External Processingを利用するときだけ、B-06で定義したdata egress boundaryを越える。

### NFR-SEC-02 — Data minimizationを適用する

外部Packageへは、そのObject分析に必要なEvidence / current Knowledge / metadataを選択し、Source Store全体や無関係Objectを丸ごと送信することを標準にしない。

### NFR-SEC-03 — export dispositionを判定可能にする

外部送信前のpreflightでは、少なくとも論理上次の3状態を扱えることを要件とする。

| disposition | 意味 |
|---|---|
| `allow` | 現在のpolicy上、追加reviewなしで明示export操作可能 |
| `review_required` | authenticated content、個人情報、rights不明、sensitivity不明等により追加確認が必要 |
| `blocked` | credential / secret等、標準policyでは外部送信禁止 |

この値はSourceの客観的「秘密度」を完全分類するものではなく、destination / policy / content metadataから導く**export decision**である。

最終field名・判定ruleはPhase G / Security設計で確定する。

### NFR-SEC-04 — credential / secretを標準Packageへ含めない

少なくとも次を外部Knowledge Packageへ含めない。

- browser cookie
- session token
- OAuth access / refresh token
- API key
- password
- OS credential material
- private key

Raw DOM / MHTML等に意図せず機密情報が含まれる可能性は別途検査・warning対象とする。

### NFR-SEC-05 — secretを平文configへ保存しない

外部provider credentialが必要な場合、可能な限りOS-protected credential store、environment injection、secret manager等を利用し、Git管理対象configへ平文secretを保存しない。

Windows標準運用ではOS保護機構を利用可能な実装を優先する。

### NFR-SEC-06 — logへsecret /全文dataを不用意に出さない

標準operation log / error logへ次を常時dumpしない。

- credential / token。
- full Raw HTML / MHTML。
- full Evidence Package本文。
- full Result本文。

必要なdiagnosticではID、hash、件数、path、安全なexcerpt等を優先する。

### NFR-SEC-07 — Result / Packageをuntrusted inputとして扱う

外部AIから返されたJSON / Markdown / URL / path文字列を、command、arbitrary file path、SQL、HTMLとして無検証実行しない。

path traversal、unexpected absolute path、script / command instruction等をdataとして扱い、明示されたSGOKB operation contract外のside effectを発生させない。

### NFR-SEC-08 — remote network exposureをdefaultにしない

MCP / API / serviceを将来network公開する場合でも、local-only bindingを初期安全既定とする。

loopback外へ公開する場合は少なくとも次を設計上要求する。

- 明示的enable。
- authentication / authorization。
- access scope。
- transport securityが必要な環境での保護。
- external data egressとしての認識。

詳細はPhase Jで決定する。

### NFR-SEC-09 — local failureからexternal providerへ自動切替しない

性能・可用性向上を理由に、local Embedding / OCR / reranker failure時にcloud providerへsilent fallbackする実装を禁止する。

external provider利用は別の明示configuration / policyとする。

---

## 12. Background Job / Retry / Recovery

### NFR-JOB-01 — Background Jobの状態を追跡可能にする

Embedding、Index update、rebuild、render、integrity scan等の非同期処理を実装する場合、少なくとも論理上次を区別可能にする。

- pending
- running
- succeeded / ready
- failed
- stale / superseded
- cancelled（対応する場合）

### NFR-JOB-02 — Retryはboundedかつidempotentにする

失敗Jobを無限busy loopで再実行しない。

具体的retry回数・backoffは実装Phaseで決定するが、同じJobをretryしてもcanonical VersionやIdentityが増殖しないことを要求する。

### NFR-JOB-03 — permanent errorとtransient errorを区別可能にする

例:

- temporary file lock / provider unavailable → retry候補。
- invalid schema / missing Evidence / corrupt Raw → human actionまたはrepairが必要。

すべての失敗を同じretry loopへ送らない。

### NFR-JOB-04 — superseded jobをcurrentへ誤適用しない

Object Version v3向けEmbedding job実行中にv4がcurrentとなった場合、v3用結果をv4 representationとして登録しない。

Job inputにVersion / representation hash / Embedding Space等のpreconditionを持てる設計とする。

### NFR-JOB-05 — rebuildをonline recoveryとして実行可能にする

Vector Index消失・backend交換・Embedding model変更時、SQLite canonical storeからfull rebuildできなければならない。

rebuild中も可能な限りObject read / Lexical Searchを継続する。

### NFR-JOB-06 — progress / failure reasonを観測可能にする

長時間処理では、少なくとも対象数、完了数、失敗数、開始時刻、最終errorを確認可能にする。

単に「動いている / 止まった」だけのblack boxにしない。

---

## 13. Search / Index lifecycle

### NFR-IDX-01 — Embedding Spaceを混在させない

model、revision、dimension、preprocessing / normalization等が異なるVectorを、同一距離空間として無条件比較しない。

Embedding Space metadataを追跡し、model変更時は別generation / rebuildとして扱う。

### NFR-IDX-02 — Representation Builder versionを追跡する

Object / Facet / StatementのSearch Representation生成方法が変わった場合、旧representationと新representationを区別できなければならない。

### NFR-IDX-03 — backend交換でcanonical Knowledgeをmigrationしない

sqlite-vector / sqlite-vec / LanceDB / Qdrant等を比較・交換しても、Object Knowledgeの正本Schema / Identityをbackend専用形式へ移行する必要がない構造とする。

### NFR-IDX-04 — Index generationを再構築可能にする

Vector backendのdata directoryが完全消失しても、canonical store + Embedding configurationから再生成可能であることを受入条件とする。

### NFR-IDX-05 — Index rebuild中のVersion scopeを明示する

current / historical、accepted / archived等のscopeを再構築時に再現できなければならない。

historical Vectorをcurrent resultへ混在させない。

### NFR-IDX-06 — cache reuseはhash / version条件を検証する

representation hashやEmbedding Spaceが一致する場合にVector再利用することは許容する。

単にObject IDが同じという理由だけで旧Vectorを再利用しない。

---

## 14. Schema migration / Compatibility

### NFR-MIG-01 — DB schema versionを明示する

applicationが対応できない新旧Schemaを黙って開いて書き換えない。

Schema versionを確認し、必要migrationを明示的に実行可能にする。

### NFR-MIG-02 — 破壊的migration前にbackup可能にする

table再構築、大量data変換、ID mapping変更等を伴うmigrationは、事前backup / dry-run / migration reportを行える設計とする。

### NFR-MIG-03 — migrationを再実行可能または安全に失敗させる

途中failure後にDBが未知の半端状態になることを避ける。

migration history / transaction / checkpoint等を利用し、再実行・rollback・manual recoveryのどれが必要か判断できるようにする。

### NFR-MIG-04 — legacy ID / provenanceを維持する

旧Prototypeからのmigrationでは、B-02 / B-03で定義したとおり、可能な限り既存Object相当ID、source_id、snapshot_id、evidence_id等を保持し、renameだけで再採番しない。

### NFR-MIG-05 — old applicationによるnew DB writeを防ぐ

新Schema DBを旧version applicationが誤って更新し破損させる危険がある場合、compatibleでないwriteを拒否できることを要件とする。

---

## 15. Supported environment / Portability

### NFR-ENV-01 — Windows 11をPrimary supported environmentとする

現行運用・Web Page Capture / Native Host環境に合わせ、初期production / acceptanceのPrimary OSをWindows 11とする。

SGOKB CoreのDomain / Storage / Retrieval logicは、必要がない限りWindows固有APIへ密結合しないことを推奨するが、初期Releaseで他OSの完全supportを必須とはしない。

### NFR-ENV-02 — Docker / always-on serverをCore要件にしない

個人用local Knowledge Baseとして、SQLite + local processで成立する構成を標準とする。

Vector backend比較の結果、optional server backendを採用可能だが、canonical Knowledgeへのアクセスまでそのserverへ依存させない。

### NFR-ENV-03 — provider / backend固有仕様をCore Domainへ漏らさない

Embedding provider、Vector backend、ChatGPT、Google Drive、MCP transport等はadapter境界を持ち、Core Object / Evidence / Version semanticsを外部製品のschemaへ従属させない。

### NFR-ENV-04 — dependency versionを再現可能にする

production / benchmarkで使用するPython package、Embedding model、Vector backend等のversionを記録可能にし、benchmark結果や不具合を後から再現できるようにする。

---

## 16. Performance — 1 Object automated workflow

### NFR-PERF-01 — Standard Objectのp95を10分以内とする

B-06で定義したlocal automatic processingについて、Reference Environment上の**Standard Object workloadでp95 10分以内**を初期Acceptance targetとする。

対象segment:

```text
Pre-analysis local segment
  Evidence Retrieval
  Package selection / budget
  manifest / instructions
  local Package build
  preflight

Post-analysis local segment
  Result parse / Validation
  Diff
  Version Import / current promotion
  Search Representation
  incremental Object / Facet / Statement Embedding
  Lexical / Vector Index update
  standard derived rendering
```

### NFR-PERF-02 — Reference Environmentを固定して測る

B-07時点のPrimary reference workstationを次とする。

- OS: Windows 11
- CPU: Intel Core i5-13600KF
- RAM: 128 GB
- GPU: NVIDIA GeForce RTX 4090 24 GB
- Storage: local filesystem。benchmark実行時に実際のdevice / volume種別と空き容量を記録する

GPUを利用しないconfiguration、別PC、external provider等は別profileとして測定し、Reference Environment結果と混ぜない。

### NFR-PERF-03 — Standard Object workloadを定義する

N-05の初期Standard profileは次を基準とする。

- target Object: 1件。
- Objectに関連するSource: 5〜20件程度。
- Evidence Retrieval candidate: 最大1,000件程度。
- Packageへ選択されるEvidence: 50〜200件程度。
- current / candidate Knowledge Statement: 最大500件程度。
- Object / Facet / Statement Embeddingの増分更新を含む。
- F-04 / G-01で確定するtoken / size budgetを超えない。

ここでの件数はperformance fixtureのenvelopeであり、Package formatそのもののhard schema limitではない。

### NFR-PERF-04 — Large Object workloadを別profileで測る

大きめObjectを平均値へ混ぜず、別profileとして少なくとも次を評価する。

- Source: 20〜100件程度。
- Evidence candidate: 最大5,000件程度。
- Package Evidence: 200〜500件程度。
- Knowledge Statement: 最大2,000件程度。
- full / substantial incremental Embedding update。

Large profileは**p95 20分以内を初期operational target**とし、Standard profileの10分Acceptanceとは別に報告する。

Large profileが頻繁に発生する場合は、F-04 / I / Nでbudget・incremental strategyを再検討する。

### NFR-PERF-05 — Human / external timeを計測から除外し、別記録する

B-06どおり、次をlocal 10分Acceptanceへ含めない。

- Source探索 / Capture network待ち。
- Package manual review。
- Google Drive sync待ち。
- ChatGPT操作 /生成待ち。
- Result返却操作。
- review-required human decision。
- external provider network latency。

ただしend-to-end user workflow把握のため、可能なら別metricとして記録する。

### NFR-PERF-06 — normal retryは時間へ含める

通常運用でautomatic retryが発生し得る処理は、そのretry時間をlocal segmentへ含める。

失敗runを除外して成功runだけ測り、実運用性能を過小評価しない。

### NFR-PERF-07 — cold / warm条件を記録する

Embedding modelやbackendが常駐するかにより性能が大きく変わるため、benchmarkは次を記録する。

- process / provider cold startの有無。
- model load time。
- index cache warm / cold。
- GPU利用状態。

production標準がlong-running providerならwarm p95をAcceptanceへ使用できるが、cold start結果も別途記録する。

### NFR-PERF-08 — benchmark metadataを必須にする

N-05結果には少なくとも次を記録する。

- Git commit / release version。
- DB schema version。
- OS / CPU / RAM / GPU。
- storage情報。
- Object / Source / Evidence / Statement件数。
- Package bytes / token estimate。
- Embedding model / revision / dimension。
- Representation Builder version。
- Vector backend / configuration。
- 各segment wall-clock。
- failure / retry数。

### NFR-PERF-09 — Full rebuildを10分Object targetへ含めない

Embedding model全面変更、Vector backend交換、全Index消失からのfull rebuildはmaintenance operationであり、1 Object通常処理10分の対象外とする。

ただしrebuild時間・throughput・peak RAM / VRAM / diskをPhase I / Nで測定する。

---

## 17. Interactive retrieval performance

### NFR-QRY-01 — Interactive queryは秒単位で返す

Reference Environment + Phase Iのreference corpusで、warm stateの初期targetを次とする。

| operation | p95 target |
|---|---:|
| exact Object ID / registry lookup | 250 ms以内 |
| Lexical Object / Evidence Search | 1 s以内 |
| Semantic / Hybrid Object Search | 3 s以内 |
| Object / Facet Similarity Search | 3 s以内 |
| 1-hop Relation traversal | 1 s以内 |

これらはDB / backend実測でPhase I / Nにて検証し、品質を犠牲にしない範囲で最適化する。

### NFR-QRY-02 — cold model loadをquery latencyと分離記録する

Semantic query embedding modelを都度loadするconfigurationでは、cold start timeを別途記録する。

UI / CLIが何十秒も無反応になる場合は、provider常駐・preload・progress表示等を検討する。

### NFR-QRY-03 — timeout時に不完全結果を完全結果として返さない

semantic channel等がtimeoutした場合、Lexical結果だけを返すことはできるが、`semantic unavailable / partial`等を識別可能にする。

---

## 18. Resource / Capacity要件

### NFR-CAP-01 — canonical store増加とderived index増加を別計測する

容量監視では少なくとも次を分ける。

- SQLite canonical DB。
- Raw Artifact store。
- Result / audit artifact。
- Package / exchange staging。
- Embedding / Vector Index。
- backup generations。

Vector Index肥大化を理由にRaw / historical Versionを削除する前に、derived generation cleanup / quantization / backend見直しを優先する。

### NFR-CAP-02 — disk fullを安全に失敗させる

容量不足時にpartial canonical writeを成功扱いしない。

少なくともPackage / backup / Index build等の大容量operationでは、利用可能容量を事前 / 実行中に検出し、errorを明示できることを目指す。

### NFR-CAP-03 — peak RAM / VRAMをbenchmarkする

Phase I / NのEmbedding / backend比較ではlatencyだけでなく、peak RAM / VRAM / disk usageも記録する。

RTX 4090を使えることを理由に、Core read pathがGPU必須となる設計にはしない。

---

## 19. Observability / Audit

### NFR-OBS-01 — 主要operationへ相関可能なIDを持たせる

Source Import、Package Build / Export、Result Validation / Import、Version promotion、Index rebuild等を後から追跡できるよう、operation / run identityを持てることを要件とする。

### NFR-OBS-02 — operation logは状態・時間・件数を記録できる

少なくとも次のようなmetadataを記録可能にする。

- operation kind。
- start / end timestamp。
- trigger origin（manual / scheduled / retry等）。
- target Object / Source / Version / Package / Result ID。
- processed / succeeded / failed count。
- duration。
- final state / error category。

### NFR-OBS-03 — timestampはtimezone-awareにする

publication / capture / import / generation / operation time等で時刻を保持する場合、timezone情報を失わない形式を使用する。

表示上のlocal timezoneと保存表現を分離できる設計を推奨する。

### NFR-OBS-04 — user-facing statusを確認可能にする

長時間処理やdegraded状態をUI / CLIから確認できることを目指す。

例:

- index pending / stale / failed。
- backup last success。
- integrity warning。
- result review required。
- package ready for export。

### NFR-OBS-05 — errorはactionableであること

error message / statusは、少なくとも次のどれに該当するか判断できるようにする。

- retry可能。
- data repairが必要。
- user reviewが必要。
- external serviceが必要。
- configuration変更が必要。

---

## 20. Maintainability / Testability

### NFR-MNT-01 — Core semanticsとAdapterを分離する

Source / Evidence / Object / Version / Retrieval semanticsを、ChatGPT、Google Drive、Vector backend、MCP等のadapter実装から分離する。

外部製品変更がObject IdentityやKnowledge Versionのmigrationへ直結しない構造を要求する。

### NFR-MNT-02 — deterministic処理を再実行可能にする

Normalization、Package manifest生成、Search Representation等のdeterministic処理は、version / configurationを追跡し、同じ入力条件で再検証できるようにする。

### NFR-MNT-03 — failure injection可能なtest boundaryを持つ

Phase Nでは少なくとも次のfailureを再現可能にする。

- process interruption / crash。
- disk full相当。
- invalid Result。
- missing / corrupt Raw。
- Vector backend unavailable。
- Embedding provider failure。
- stale Version。
- external export未承認。
- MCP unavailable。

### NFR-MNT-04 — testが実ユーザーdataを破壊しない

integration / benchmark / migration testは、production DB / Raw storeへ直接書き込まず、fixture / copy / isolated test directoryを利用できることを要件とする。

### NFR-MNT-05 — benchmarkとcorrectness testを分離する

速度が速いことをSchema / Provenance / retrieval correctnessの代替にしない。

性能比較では同じcorrectness条件を満たすconfiguration同士を比較する。

---

## 21. 非機能Acceptance / Failure Recovery test

Phase Nでは少なくとも次を受入試験する。

### Offline / dependency

1. Internet切断状態でObject read / Lexical Searchが利用できる。
2. ChatGPT / Driveが利用不能でもlocal Package Buildまで進められる。
3. local provider failureからcloud providerへsilent fallbackしない。
4. MCP停止でもCLI / canonical DBが利用できる。

### Canonical / transaction

5. Result Import途中にprocessを停止しても旧currentまたは完全な新currentのどちらかへ復旧できる。
6. partial fileをvalid Package / backupとして扱わない。
7. 同一Result retryで不要なVersionが増殖しない。

### Provenance

8. Raw欠損 / checksum mismatchを検出できる。
9. broken Evidenceを新Packageへsilent利用しない。
10. Object KnowledgeからEvidence / Raw / Sourceまで追跡できる。

### Index / derived

11. Vector Index directoryを削除してもcanonical Knowledgeを失わない。
12. SQLite正本からVector Indexをfull rebuildできる。
13. current Version更新後に旧Vectorをcurrentとしてsilent利用しない。
14. Index更新失敗後にLexical / Object readを継続できる。
15. Embedding model / Representation Builder変更を別generationとして再構築できる。

### Backup / restore

16. scheduled相当backupを生成できる。
17. backupを別pathへrestoreできる。
18. restore後にDB integrity + Raw / Provenance checkを通せる。
19. RPO 24h / RTO 4hの運用条件を実測または手順上確認できる。

### Security / egress

20. Package BuildだけではDrive sync directoryへ書き込まれない。
21. `blocked` export itemを標準exportで外部送信できない。
22. credential / tokenがPackage / standard logへ混入しない。
23. external providerへのsilent fallbackがない。
24. remote network exposureがexplicit enableなしに有効にならない。

### Performance

25. Standard Object profileのlocal automated segmentがReference Environmentでp95 10分以内。
26. Large Object profileを別集計し、p95 20分targetを評価する。
27. interactive retrievalのp95 targetをPhase I reference corpusで評価する。
28. benchmark metadataがhardware / model / backend / workload / commitを含む。

---

## 22. 後続Phaseへの引き継ぎ

### Phase C

- SGOKB / UPDS連携でもSGOKB canonical storeのavailability / privacy boundaryを維持する。
- UPDSがSGOKB DBへ直接writeすることを前提にしない。

### Phase D

- `.local/`、DB、Raw、Result、Package、Index、backupをGit管理対象から適切に除外する。
- production / backup / transient directoryを混同しない。

### Phase E

- canonical / derived区分をphysical schemaへ反映する。
- accepted Version immutable、current switch transaction、job state、Embedding Space / Representation metadataを設計する。
- Referential / Provenance integrity constraintを設計する。

### Phase F

- Normalize / Evidence generationのidempotency / retry / broken provenance isolationを実装する。
- effective Snapshot / Run selectionでbroken最新世代をsilent採用しない。

### Phase G

- Package build local stagingとExternal Export directoryを物理分離する。
- export preflightで`allow / review_required / blocked`相当を扱う。
- Package audit metadataを保存する。
- credentials / secretsをPackageへ含めない。

### Phase H

- Result Import transaction、original artifact retention、duplicate import、crash recoveryを実装する。
- accepted Version commit後のderived jobを独立stateで管理する。

### Phase I

- Embedding Space / Representation Builder / Vector Index generationを明示する。
- no-silent-fallback、stale detection、full rebuild、warm / cold performance benchmarkを実装・評価する。
- interactive p95目標を検証する。

### Phase J

- MCP停止がcanonical DBをblockしないAdapter構造を維持する。
- network公開をdefaultにせず、非loopback時のauth / scopeを設計する。

### Phase L

- legacy data migration前にbackup / dry-run / integrity reportを行う。
- ID / provenanceを可能な限り維持する。

### Phase M

- integrity / backup / job / index statusを確認できるCLIを設計する。
- destructive / external operationにpreview / explicit actionを用意する。

### Phase N

- 本書第21節をFailure / Recovery / Performance acceptanceへ反映する。
- N-05でStandard p95 10分、Large profile、cold / warm条件を記録する。
- N-06 / I-07でinteractive query latencyとretrieval品質を同時評価する。

### Phase O

- backup / restore / offline / external egress / security / recovery手順を運用文書へ含める。

---

## 23. B-07で意図的に決めない事項

次は後続設計 / 実測へ延期する。

- backup実装script / schedulerの具体方式。
- backup圧縮・差分backup format。
- OS credential backendの具体API。
- application-level encryption at restの採否。
- exact job queue / worker implementation。
- retry回数 / backoff秒数。
- final Index state enum。
- final export sensitivity metadata schema。
- F-04 / G-01のtoken / byte hard limit。
- Embedding model / dimension。
- Vector backend。
- ANN parameter。
- search fusion weight。
- final capacity ceiling。
- GUIのwarning表現。
- exact integrity scan cadence。

これらは本書のlocal-first、no-silent-fallback、canonical保全、recoverability、performance measurement契約を壊さない範囲で決定する。

---

## 24. 旧Prototypeからの変更点

旧Prototypeでは、主な性能問題はLocal Generative LLMの大量Fragment生成であり、処理時間benchmarkもそこへ集中していた。

新SGOKBでは非機能評価の中心を次へ変更する。

```text
旧:
LLM Fragment generation throughput
Final Document generation time

新:
Canonical data integrity
Provenance recoverability
Package / Result workflow safety
Incremental Search Representation / Embedding / Index update
Interactive Retrieval latency
Backup / Restore
Offline / degraded operation
External data egress safety
1 Object local automated workflow p95
```

また、旧Prototypeの「AI処理失敗を再試行して最終Documentを完成させる」だけでなく、canonical / derived / externalのfailure domainを分離し、壊れた派生処理によって正本を失わないことを重視する。

---

## 25. 完了条件への対応

### Offline / graceful degradation

Internet / ChatGPT / Drive / Vector backend / MCP等の停止時に、canonical dataと利用可能なlocal機能を維持する要件を定義した。

### 再生成可能性

Search Representation、Embedding、Vector Index、Markdown、Package等をcanonical dataから再生成可能なderived artifactとして定義した。

### Provenance integrity

Raw / Snapshot / Normalized Run / Evidence / Object Knowledgeのchainとchecksum / integrity stateを検証可能にした。

### Versioning / retention / hard delete

accepted Versionのimmutability、Archive優先、参照中Provenanceを自動削除しないこと、Hard deleteを管理操作とすることを定義した。

### Backup / Restore

RPO 24時間、canonical restore RTO 4時間、daily / weekly generation保持、restore testを初期要件として定義した。

### Security / Privacy / External Egress

local-only default、data minimization、export decision、secret保護、no-silent-cloud-fallback、remote exposureの明示enableを定義した。

### Background failure / Index recovery

Job state、bounded retry、stale detection、Vector Index full rebuild、Lexical fallbackを定義した。

### Performance

Reference Environment、Standard / Large workload、Standard p95 10分、Large p95 20分target、interactive query p95 target、benchmark metadataを定義した。

---

## 26. 結論

SGOKBの非機能要件では、**正本・Provenanceを最優先で保全し、Embedding / Index / MCP / cloud service等を交換・再生成可能な補助層として扱う。**

Internetや外部AIが利用不能でも保存済みKnowledgeを失わず、派生Indexが壊れてもcanonical storeから再構築でき、外部送信は明示policyなしに発生しない構造を基準とする。

性能についてはReference Environment上でStandard Objectのlocal automatic processingをp95 10分以内とし、Large Objectは別profileで評価する。検索はinteractive useを前提に秒単位のp95目標を置く。

B-07は以上をもって完了とし、Phase Bの要件定義更新を完了する。

次の作業は **Phase C — SGOKB / UPDS責務境界** とする。

**Status: Complete (2026-10-11)**
