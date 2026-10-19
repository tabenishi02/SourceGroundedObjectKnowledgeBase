# Source Grounded Object Knowledge Base — Phase F Preparation

更新日: 2026-10-12

- Target: `Phase F — Source / Evidenceパイプラインの簡略化`
- Status: Complete — F-01〜F-05
- Active redesign branch: `integration/knowledge-base-redesign`
- Phase E status: Complete — E-01〜E-05
- Structural prerequisite: D-05 Wave 2 complete — ingestion modules moved to `src/sgokb/ingestion/`
- Next task: `G-01 [P0] Object Evidence Package formatを確定する`

## 1. 目的

本書は、Phase Eで完成したcanonical Object / Source / Evidence / Version / Object Result contractを、Phase Fの既存Capture / Import / Normalize / Evidence pipelineへ安全に接続するための開始条件・現状差分・実装順序を整理する。

Phase Fでは旧Prototypeの高コストFragment / Final Document pipelineを延命することを目的としない。Web Captureで取得済みRawを再利用し、Generative LLMなしでcanonical Evidence StoreからObject Evidence Packageの入力を作れる状態へ移行する。

## 2. Phase E完了監査

Task masterを再監査し、Phase Eの未完了checkboxが0件であることを確認した。

```text
E-01  Object schema                                      完了
E-02  Semantic Facet schema                              完了
E-02A 全Class Facet taxonomy survey                      完了
E-02B Facet vocabulary横断統合                           完了
E-02C Class / Facet境界gold cases                        完了
E-03  Source / Evidence / Evidence Link / Provenance     完了
E-04  Versioning                                         完了
E-05  Object Result JSON Schema                          完了
```

Phase Eの物理成果物:

```text
Migration 003  Object / Class / Relation skeleton
Migration 004  Semantic Facet / Statement / Attribute / Temporal Scope
Migration 005  55 Facet taxonomy / Class profile freeze
Migration 006  canonical Source / Evidence / Provenance
Migration 007  immutable Version lifecycle

Object Result Schema
  sgokb.object-result/1.0
  JSON Schema Draft 2020-12
```

Phase F準備開始時の回帰基準:

```text
ruff:       passed
pytest:     137 passed before structural Wave 2
compileall: passed
```

D-05 Wave 2のcompatibility test追加後はfull suite 138 passedを基準とする。

## 3. Phase Fの対象Task

```text
F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する
F-02 [P0] 標準パイプラインからFragment生成を外す
F-03 [P0] Object Evidence Retrievalを実装する
F-04 [P1] Evidence Selectionのtoken/size budgetを設計する
F-05 [P1] ObjectとSource/Evidenceの明示linkを維持できるUI/CLIを設計する
```

Phase F完了条件は、**生成LLMなしでObjectに関連するEvidence Package入力集合を構築できること**である。

## 4. D-05 Wave 2 structural prerequisite

F-01のbehavior変更とfile moveを分離するため、Phase F開始準備としてD-05 Wave 2を先行実施した。

canonical path:

```text
src/sgokb/ingestion/
├─ __init__.py
├─ importer.py
├─ extraction.py
└─ context.py
```

旧path:

```text
src/sgokb/importer.py
src/sgokb/extraction.py
src/sgokb/context.py
```

はロジックを持たないcompatibility re-export shimとして維持する。

新しいproduction importは`sgokb.ingestion.*`を使用する。旧Prototype / external consumerは移行期間中、旧top-level pathを利用可能とする。

このstructural moveでは次を変更しない。

- Web Capture Bundle validation behavior
- extractor algorithm
- chunk algorithm
- page context algorithm
- DB schema
- Source identity semantics
- Evidence semantics

## 5. 現行Prototype ingestion path

現在の標準`Application`には旧Prototype ingestion pathが残っている。

```text
*.webcapture.zip
  ↓ WebCaptureImporter.read()
Bundle
  ↓ Application.import_path()
Repository.import_bundle()
  ↓
legacy sources / snapshots / artifacts
  ↓ Application.process()
ExtractorRegistry.select()
  ↓
Block[]
  ↓ chunks()
legacy normalized_runs / evidence / page_contexts
  ↓
snapshots.active_run
```

### Import

`Repository.import_bundle()`は現在、URLを検索してSourceを再利用する。

```sql
SELECT id FROM sources WHERE url=?
```

legacy `sources.url`にはglobal UNIQUEがある。

これはE-03の「Source IdentityをURLから独立させる」canonical contractとは一致しない。

### Normalize / Evidence

`Repository.save_normalized()`は、

- legacy `normalized_runs`を作成
- legacy `evidence`を作成
- legacy `search_items`へEvidenceを登録
- legacy `page_contexts`を保存
- `snapshots.active_run`を新Runへ更新

する。

失敗時に旧active runを保持する点は有用だが、canonical E-03にはまだeffective Run selectorがない。

## 6. 再利用する既存実装

### 6.1 WebCaptureImporter — Keep

`sgokb.ingestion.importer.WebCaptureImporter`は次を既に実施する。

- ZIP entry安全性検証
- entry数 / 展開byte上限
- required artifact検証
- checksum coverage / SHA-256 / byte数検証
- Bundle format/version検証
- capture UUID / timestamp / filename整合
- page URL / title validation
- component status整合
- MHTML status / artifact整合
- frame artifact存在確認

このreaderはExtension Hostに依存せず、F-01でも再利用する。

### 6.2 Extractor — Keep / Modify minimally

`sgokb.ingestion.extraction`は次を再利用できる。

- Rendered DOMから本文rootを選ぶ
- noise除去
- heading / paragraph / list / table / quote / postを構造単位化
- DOM position保持
- frame / open Shadow DOMのoptional extraction
- site-specific root selection

F-01ではcanonical Evidence persistenceへ接続するためのmetadata / location変換を追加できるが、抽出algorithm全面変更は行わない。

### 6.3 Page Context — Modify / map

`sgokb.ingestion.context`はdeterministicなpage-level observationを生成できる。

現行field:

```text
source_type
publisher_type
page_purpose
page_summary
subject_candidates
source_published_at
source_updated_at
source_independence
signals
```

これをcanonical Source classification / metadataへbest-effort mappingする。

`page_contexts`を新canonical正本としてそのまま再利用しない。

## 7. canonical target path

F-01のtargetはE-03で確定済みの次のchainである。

```text
Web Capture Bundle
  ↓
SourceRecord
  + SourceLocator
  ↓
SourceSnapshot
  ↓
RawArtifact 1..N
  ↓
NormalizationRun
  ↓
EvidenceRecord 0..N
  + EvidenceLocation 0..N
```

canonical persistenceは既に`SourceRepository`として存在する。

利用可能な代表operation:

```text
create_source()
add_locator()
create_snapshot()
add_classification()
add_metadata()
add_raw_artifact()
create_normalization_run()
add_evidence()
add_evidence_location()
associate_object()
evidence_provenance()
validate_evidence_references()
```

したがってF-01の中心は新tableを一から設計することではなく、既存ingestion dataをこのcontractへ正しく変換するapplication orchestrationである。

## 8. F-01 gap matrix

| 項目 | Prototype | canonical target | F-01で必要な作業 |
|---|---|---|---|
| Source identity | URL UNIQUE | URL非依存stable ID | Source resolution policyを追加 |
| Locator | `sources.url`列 | 0..N `source_locators` | page URL / canonical URLをlocator化 |
| Snapshot ID | `capture_id` | stable Snapshot ID | `capture_id`維持を基本とする |
| Capture completeness | manifest内 | Snapshot列 + warnings | `success/partial`をcanonical enumへmap |
| Raw | Bundle path + artifact rows | `raw_artifacts` | Bundle内全Artifactを登録 |
| Raw location | snapshot raw_path | `storage_ref + logical_path` | ZIP pathとentry pathを分離 |
| Normalize | legacy run | `normalization_runs` | extractor key/version/config/outputを登録 |
| Evidence | legacy `evidence` | `evidence_records` | normalized mode + ordinalで保存 |
| Evidence location | metadata JSON内 | `evidence_locations` | DOM path / heading path等をrow化 |
| Source classification | `site/source_type` | multi-axis rows | resource/media/genre/site等へmap |
| Page metadata | `page_contexts` | metadata provenance rows | language/date/summary等をmap |
| Object association | `entity_evidence` | Source↔Object association | F-05を見据えcandidate/confirmed/excluded利用 |
| Active/effective Run | `snapshots.active_run` | 未固定 | selection policyをF-01で確定 |
| Search indexing | import時`search_items` | derived layer | F-01でcanonical正本と混同しない |

## 9. Source resolutionで守る境界

F-01ではURL一致をSource Identityそのものとして復活させてはならない。

最低限、次を区別する。

1. callerが既存`source_id`を明示した場合
2. locator一致候補が1件だけ存在する場合
3. 同じlocatorを持つSource候補が複数存在する場合
4. locator一致Sourceが存在しない場合

推奨方針:

- 明示`source_id`を最優先する。
- URL/canonical URL一致はidentity proofではなくresolution signalとして扱う。
- ambiguousなlocator一致をsilent mergeしない。
- 新Source作成を許容する。
- 同一`capture_id`の再Importはidempotentに扱う。
- 同一`capture_id`でRaw内容が異なる場合はrejectする。

具体的なSource resolver API名はF-01で確定する。

## 10. Web Capture → canonical field mapping

### Source Locator

最低限:

```text
manifest.page.url
  -> kind=url

metadata/document.json canonical_url (存在時)
  -> kind=canonical_url
```

canonical URLで実URLを上書きしない。

### Snapshot

```text
capture_id                -> snapshot_id
captured_at               -> captured_at
capture_method            -> web_capture
capture_tool.name         -> capture_tool
capture_tool.version      -> capture_version
manifest.page.title       -> title
manifest                  -> manifest_json
Bundle metadata indexes   -> metadata_json
manifest.warnings         -> warnings_json
```

Web Capture v1.0の`completeness=success`はcanonical `complete`、`partial`は`partial`へmapする。

正式BundleはMain DOM成功時だけ生成されるため、通常Importで`failed` Snapshotを新規作成する必要はない。

### Raw Artifact

Bundle内の各Artifactをcanonical Raw Artifactとして追跡する。

推奨表現:

```text
storage_ref = *.webcapture.zip の保存参照
logical_path = dom/main.html 等のBundle内相対path
sha256 / bytes = checksums / reader検証結果
```

artifact kindの初期例:

```text
capture_manifest
rendered_dom
frame_dom
metadata
mhtml
checksums
```

kind vocabularyはF-01実装時に固定しすぎず、logical pathを必ず保持する。

### Classification / metadata

最低限のcandidate mapping:

```text
resource_type   = web_page                     deterministic
media_type      = document.content_type        captured
site            = hostname                     deterministic
document_genre  = legacy classify() result     deterministic
publisher_kind  = context.publisher_type       deterministic
page_purpose    = context.page_purpose          deterministic
```

metadata candidate:

```text
language
canonical_url
source_published_at
source_updated_at
page_summary
subject_candidates
source_independence
```

legacy `source_type`という単一軸をcanonical Source identityへ埋め込まない。

## 11. Normalization / Evidence mapping

### Normalization Run

Extractorごとに新Runを追加する。

```text
extractor_key       = extractor.name
extractor_version   = extractor.version
configuration       = normalization options
output              = blocks / processing summary
status              = complete / partial / failed
```

Runは実際に使用したRaw Artifact IDを必ず参照する。

main DOMのみ処理した場合はmain DOM Raw Artifactをinputとする。`include_auxiliary=True`なら利用したframe / shadow metadata等のRaw Artifactもinputへ含める。

### Evidence

現行`chunks()`の出力は原文意味を保持した構造抽出/whitespace正規化であるため、初期F-01では`extraction_mode=normalized`を基本とする。

Evidence metadataには現行の次を保持できる。

```text
section
positions
artifact
kinds
blocks_metadata
start
```

### Evidence Location

現行metadataから少なくとも次をcanonical locationへ分離する。

```text
positions[] -> dom_path
section     -> heading_path
ordinal     -> block_order相当の順序情報として利用可能
```

Raw上の位置へ人間が戻れる情報を失わない。

## 12. effective Snapshot / Run selection

F-01で最も重要な未実装境界の1つである。

要件上、

```text
latest Snapshot != automatic effective Snapshot
latest Run      != automatic effective Run
```

である。

最新Captureがerror page、ログイン切れ、partial、誤抽出である可能性があるため、timestamp最大値だけで既定世代を選ばない。

F-01では次を決定する必要がある。

- default selection policy
- manual override方法
- selection理由 / originの追跡方法
- failed / partial Runが既存正常Runを置換しない保証
- retrieval時にeffective / historical scopeを区別する方法

必要ならadditive migrationでselection pointer / eventを追加する。Migration 006を書き換えない。

## 13. legacy coexistence方針

F-01で既存Prototype DBの意味migrationを行わない。

```text
legacy:
  sources / snapshots / artifacts / normalized_runs / evidence / page_contexts

canonical:
  source_records / source_locators / source_snapshots / raw_artifacts /
  normalization_runs / evidence_records / evidence_locations
```

既存legacy recordのcanonical copy / ID preservation migrationはPhase Lの責務である。

F-01では新しいcanonical ingestion pathを成立させ、旧Prototype Fragment / Final workflowが必要な期間はlegacy pathを破壊しない。

### dual-writeを既定にしない

同じoperationでlegacyとcanonicalへ常時dual-writeすると、

- transaction boundaryが複雑になる
- Source identity semanticsが混在する
- 二重正本化する
- Phase L migration判定が難しくなる

ため、標準方針にはしない。

新canonical use caseとlegacy compatibility use caseを明示的に分離する方が安全である。

## 14. F-01推奨実装順序

### F-01A — Source resolution / effective selection contract

先に次を設計する。

- CaptureをどのSourceへbindするか
- ambiguous locatorの扱い
- canonical Snapshot duplicate判定
- effective Snapshot / Run selection

必要なschema追加がある場合はadditive migrationとする。

### F-01B — canonical Capture Import

`WebCaptureImporter`のvalidated Bundleから、

- Source / Locator
- Snapshot
- Raw Artifact
- captured metadata

をcanonical `SourceRepository`へ保存する。

### F-01C — canonical Normalize / Evidence

既存Extractorを利用し、

- Normalization Run
- Evidence Record
- Evidence Location
- deterministic Source classification / metadata

を保存する。

### F-01D — compatibility / integration tests

legacy pathを破壊せず、新canonical pathだけを直接試験する。

F-02で標準pipelineからFragment generationを外す前に、Capture → canonical Evidenceが独立して成立することを確認する。

## 15. F-01で追加すべき主要test

最低限、次を回帰試験化する。

1. valid Web Capture Bundleからcanonical Source chainを作れる。
2. `capture_id`をSnapshot IDとして維持できる。
3. 同一captureのretryがidempotent。
4. 同一capture ID + 異なるRawをrejectする。
5. URL一致だけでambiguous Sourceをsilent mergeしない。
6. page URLとcanonical URLを別locatorとして保持する。
7. manifest completeness / warningsを保持する。
8. Bundle内Raw Artifactのhash / bytes / logical pathを保持する。
9. Normalization Runが利用Raw Artifactへ結び付く。
10. EvidenceからRun → Snapshot → Raw → Sourceへ辿れる。
11. Evidence locationからDOM path / heading pathへ戻れる。
12. Source classification / metadataのoriginを保持する。
13. failed reprocessingで既存effective Runを置換しない。
14. historical Run / Evidenceを削除しない。
15. Generative LLMを呼ばずCapture → Evidenceまで完了する。
16. legacy top-level ingestion import pathが引き続き利用できる。

## 16. F-02〜F-05への引き継ぎ

### F-02

**Implementation status: Complete (2026-10-12).**

canonical Evidence path成立後、標準処理からFragment generationを外した。標準CLIの`import` / `process`はcanonical Source / Evidence pathを利用し、Fragment / Final /旧benchmarkは`legacy-*`として明示した。

旧`capture.py` / Fragment tableは直ちに削除せず、Phase Lまでlegacy / research compatibilityとして保持する。物理`_legacy/`移動はbehavior変更と分離し、Phase Lで実施判断する。正本は`docs/design/STANDARD_PIPELINE_BOUNDARY.md`。

### F-03

**Implementation status: Complete (2026-10-12).**

Object Evidence Retrievalはcanonical Evidenceを対象とし、次をselection signalとして実装した。

- name / alias
- explicit Source↔Object association（confirmed / candidate、excludedは自動候補除外）
- effective Source metadata
- canonical Evidence FTS（Migration 009）
- semantic cosine（明示Embedder設定時のみ。Phase Iまでのon-demand baseline）
- manual include / exclude

通常scopeはeffective Snapshot / Runのみとし、候補ごとにselection reasonを複数保持する。設計正本は`docs/design/OBJECT_EVIDENCE_RETRIEVAL.md`。

### F-04

**Implementation status: Complete (2026-10-12).**

現行`chunks(size=1000, overlap=100)`を最終budgetとして固定せず、`EvidenceBudget` / `EvidencePackageSelector`を実装した。推定token / UTF-8 byte / item数をhard limitとし、Source diversity pass後にF-03 relevance順で残余budgetを埋める。manual includeはprotected、duplicate / near-duplicate /高overlap chunkはPackage-local suppressionとし、近接Evidenceは`structure_group`で追跡する。非採用candidateにはbudget / duplicate理由を保持する。設計正本は`docs/design/EVIDENCE_SELECTION_BUDGET.md`。

### F-05

**Implementation status: Complete (2026-10-12).**

`source_object_associations`をcanonical operator surfaceへ接続し、`association list/suggest/set/clear`を実装した。suggestionはF-03 retrieval候補をSource単位へ集約するread-only表示で、operatorが明示setするまで永続化しない。candidate / confirmed / excluded、subject relationship、noteをmanual originで維持できる。Evidence単位のmanual include / excludeは`evidence candidates/select`からF-03/F-04へ渡すPackage selection controlとし、Knowledge `evidence_links`とは分離した。正本は`docs/design/OPERATOR_ASSOCIATION_CONTROLS.md`。

F-05完了によりPhase FのTaskはすべて完了した。

## 17. F-01 Definition of Ready

- [x] Phase A〜D完了。
- [x] Phase E E-01〜E-05完了。
- [x] canonical Source / Evidence schema実装済み。
- [x] canonical SourceRepository実装済み。
- [x] Web Capture Bundle v1.0 format確定済み。
- [x] WebCaptureImporter安全性検証実装済み。
- [x] Extractor / structural Block extraction実装済み。
- [x] D-05 Wave 2 ingestion package移動完了。
- [x] 旧top-level import compatibility shimあり。
- [x] legacy / canonical Source table共存中。
- [x] Phase L data migrationとF-01 behavior接続を分離済み。
- [x] F-01で決めるSource resolution / effective selection論点を明示済み。
- [x] full regression baselineを確認済み。

以上によりF-01は開始可能である。

## 18. F-01開始時に読む文書

必須:

1. `docs/planning/PHASE_F_PREPARATION.md`
2. `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
3. `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
4. `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
5. `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
6. `docs/design/SOURCE_EVIDENCE_SCHEMA.md`
7. `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`
8. `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
9. `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
10. `extensions/web-page-capture/docs/CAPTURE_BUNDLE_FORMAT.md`

実装確認:

- `src/sgokb/ingestion/importer.py`
- `src/sgokb/ingestion/extraction.py`
- `src/sgokb/ingestion/context.py`
- `src/sgokb/application.py`
- `src/sgokb/repository.py`
- `src/sgokb/storage/source_repository.py`
- `tests/test_core.py`
- `tests/test_source_evidence_schema.py`

## 19. 次チャット用指示文

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。
Phase A〜Eは完了し、Phase F開始準備も完了しています。

再設計の正規作業基盤はintegration/knowledge-base-redesignです。
D-05 Wave 2として importer / extraction / context の ingestion package移動も完了済みです。

まず以下を確認してください。
- docs/planning/PHASE_F_PREPARATION.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md
- docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md
- docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md
- docs/design/SOURCE_EVIDENCE_SCHEMA.md
- docs/design/OBJECT_RESULT_JSON_SCHEMA.md
- docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md
- docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md
- extensions/web-page-capture/docs/CAPTURE_BUNDLE_FORMAT.md

今回実施するTask:
G-01 [P0] Object Evidence Package formatを確定する

F-01〜F-05は完了し、Phase Fは完了しています。F-03〜F-05でcanonical Evidence retrieval、bounded selection、operator association / manual Evidence overrideが成立しました。G-01ではこれらの出力を入力として、current Knowledge carry-forward、Evidence/Source provenance、selection controlsを保持するObject Evidence Package formatを確定してください。Packageはderived local artifactでありcanonical正本にはしないでください。
```

## 20. 結論

Phase Eには未完了Taskはない。

Phase F開始前のstructural prerequisiteとしてD-05 Wave 2も完了し、Importer / Extractor / Page Contextは`src/sgokb/ingestion/`へ正規配置された。旧top-level pathはcompatibility shimとして維持している。

F-01でcanonical ingestion、F-02でstandard / legacy境界、F-03でObject Evidence Retrieval、F-04でbounded Evidence Selection、F-05でoperator association / Evidence override CLIまで完了した。Phase Fの完了条件である「生成LLMなしでObjectに関連するEvidence Package入力集合を構築できること」を満たした。

**Next: `G-01 [P0] Object Evidence Package formatを確定する`**
