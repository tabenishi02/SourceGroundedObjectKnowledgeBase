# Source Grounded Object Knowledge Base — Phase G Preparation

更新日: 2026-10-12

- Target: `Phase G — Google Drive / ChatGPT交換ワークフロー`
- Status: Ready to start
- Active redesign branch: `integration/knowledge-base-redesign`
- Phase F status: Complete — F-01〜F-05
- Integration baseline after Phase F: `3a3c465c2e04b616773427e9f61408a1661f7b87`
- Next task: `G-01 [P0] Object Evidence Package formatを確定する`

## 1. 本書の目的

本書は、Phase Fで成立したcanonical Evidence Retrieval / Selection / operator controlを、Phase GのObject Evidence Package・Google Drive・ChatGPT human-in-the-loop workflowへ接続するための開始条件、既存資産、未実装gap、実装順序を整理する。

Phase GではChatGPT APIによる自動生成pipelineを構築しない。標準workflowは次を維持する。

```text
Canonical SGOKB DB
  ↓ local automation
Object Evidence Package
  ↓ local staging
Human explicit export
  ↓
Google Drive / ChatGPT Web/Desktop
  ↓ human return
result.json
  ↓ local incoming
Phase H Validation / explicit Import
```

Package BuildとExternal Export、Result検出とauthoritative Importをそれぞれ分離する。

## 2. Phase F完了監査

Phase F Task masterを再監査した結果、F-01〜F-05の5 Taskはすべて完了している。

```text
F-01 [P0] canonical Capture / Import / Normalize / Evidence接続      完了
F-02 [P0] standard pipelineからFragment生成を除外                   完了
F-03 [P0] Object Evidence Retrieval                                 完了
F-04 [P1] Evidence Selection token / size budget                    完了
F-05 [P1] Source↔Object / Evidence operator controls                完了

未完了checkbox                                                        0
```

F-05 PR #25は`integration/knowledge-base-redesign`へsquash merge済みで、統合後のfull regressionは`159 passed`だった。

Phase F完了時点で標準pathは次まで成立している。

```text
Web Capture Bundle
  ↓
Source / Snapshot / Raw Artifact
  ↓
Normalization Run
  ↓
Canonical Evidence
  ↓
Object Evidence Retrieval
  ↓
Bounded Evidence Selection
  ↓
Operator Source association / Evidence override
```

したがってPhase GはEvidence収集やFragment抽出を再設計し直すPhaseではない。

## 3. Phase G対象Task

Task master上のPhase Gは次の5 Taskである。

```text
G-01 [P0] Object Evidence Package formatを確定する
G-02 [P0] manifest.json schemaを定義する
G-03 [P0] ChatGPT用instructions.mdを設計する
G-04 [P0] Local Package staging / Google Drive export方式を実装する
G-05 [P1] Result受け取り運用を定義する
```

Phase G完了条件:

> APIを利用せず、ユーザーがChatGPTとの手動工程を介して1 Objectを往復できる。

## 4. Phase Gへ引き継ぐ既存資産

### 4.1 F-03 — Object Evidence Retrieval

利用可能:

- effective Snapshot / Run scope
- explicit Source↔Object association
- Object name / alias
- Source metadata
- canonical Evidence FTS
- optional semantic retrieval
- manual Evidence include / exclude
- Evidence selection reason
- Evidence provenance context

Phase Gはこのretrieval結果をPackage候補入力として利用する。

### 4.2 F-04 — bounded Evidence Selection

利用可能:

- estimated token / UTF-8 byte / item count hard budget
- Source diversity pass
- relevance fill
- duplicate / near-duplicate / overlap suppression
- structural grouping / nearby Evidence relation
- omission reason
- protected manual include

Package Builderは第二のselection algorithmを作らず、F-04 outputを基本入力とする。

### 4.3 F-05 — operator controls

利用可能:

```text
association list / suggest / set / clear
evidence candidates / select
  --include-evidence
  --exclude-evidence
```

`candidate / confirmed / excluded` Source↔Object associationとPackage selection overrideは既に分離されている。

### 4.4 E-05 — Object Result contract

`src/sgokb/exchange/object_result.py`には既に次がある。

- `sgokb.object-result/1.0`
- static Object Result JSON Schema
- runtime `ObjectResultContract`
- target Object / Classification / effective Facet profile binding
- Package binding fields: `package_id`, `package_schema_version`, `manifest_sha256`, `base_version_id`

Phase GはResult schemaを作り直さず、Package側をこのcontractへ接続する。

### 4.5 E-04 — Version lifecycle

`VersionRepository`には`current_version_id()` / `version_by_id()`、full snapshot lifecycle、base Version stale contract、Classification snapshot、accepted/current pointerがある。

Package生成時の`base_version_id`取得には再利用できる。

### 4.6 D-06 — runtime / exchange path policy

既に次が確定している。

```text
exchange/
├─ staging/
├─ incoming/
└─ processed/
```

- `exchange/`はGit管理外。
- Package stagingはlocal derived artifact。
- Google Drive同期directoryは原則Repository外。
- 同期directoryへのwriteもExternal Export。
- Package BuildとExternal Exportを同一操作にしない。

## 5. 現行`exchange/`実装の状態

Phase G開始時点の`src/sgokb/exchange/`は次のみである。

```text
src/sgokb/exchange/
├─ __init__.py
├─ object_result.py
└─ schemas/
   └─ object-result-v1.schema.json
```

未実装:

- Evidence Package value model / builder / serializer
- Package manifest schema
- Package identity / hash builder
- `instructions.md` template / renderer
- `current_object.json` serializer
- local staging writer
- export preflight / export decision
- Google Drive sync-folder exporter
- incoming result receipt workflow

## 6. G-01開始時の主要gap

### 6.1 current Knowledge read/serialize APIが不足

Version lifecycleは存在するが、current accepted VersionをPackage用`current_object.json`へ完全snapshotとして読み出す高位APIはまだない。

必要なread対象:

- Object identity context
- Version metadata / Classification snapshot
- Facet status / Knowledge Statements
- Attributes / Relations / Temporal scope
- Evidence Links

`SemanticRepository`はwrite API中心であり、Package serializer用read modelが必要になる。

### 6.2 current VersionのEvidence Link一括取得が不足

`SourceRepository.evidence_links_for_target()`は個別Knowledge target用である。G-01ではcurrent Version全体が参照するEvidence集合をcarry-forward候補として取得するAPIが必要になる。

### 6.3 carry-forward EvidenceとF-04 budgetの統合policyが未確定

G-01では次を決める必要がある。

- current grounding Evidenceをどこまでprotectedにするか。
- protected Evidenceだけでbudget超過した場合のfail / review behavior。
- current Evidenceと新規retrieval Evidenceがduplicateの場合の扱い。
- current Evidenceがhistorical Snapshot / Runに属する場合のPackage inclusion。

通常retrievalのeffective generation scopeと、accepted current Knowledgeのhistorical groundingを混同しないことが重要である。

### 6.4 Package payloadとaudit metadataの境界が未実装

Package directoryは再生成可能なderived artifactである。一方、NFR-DAT-05により少なくとも次は監査可能にする必要がある。

- package identity / manifest/schema version / package hash
- target Object / base Version
- included Evidence ID集合
- instructions version
- export destination / timestamp

## 7. G-01 Package formatで決める範囲

初期directory contract候補:

```text
<object-id>/
├─ manifest.json
├─ instructions.md
├─ current_object.json        # current accepted Versionがある場合のみ
└─ evidence/
   ├─ source_001.md
   ├─ source_002.md
   └─ ...
```

G-01では少なくとも次を確定する。

1. Package root naming rule。
2. file set / required-optional rule。
3. Evidence file grouping単位。
4. Evidence IDを本文内で機械的に参照できるformat。
5. Source / Snapshot / Evidence provenanceの最小表現。
6. selection reason / omission auditの保持位置。
7. `current_object.json`のformat。
8. current Knowledge grounding Evidence carry-forward policy。
9. Raw Artifact本文を標準Packageへ無制限に含めないこと。
10. ResultがPackage外Evidenceを引用できないmembership boundary。

Evidence fileはSource単位groupingを初期案とする価値が高い。ただしMarkdown fileを新Evidence正本にしない。

## 8. G-02 `manifest.json`で決める範囲

少なくとも次をschema化する。

```text
schema_version
package_id
created_at
manifest_sha256 contract

target:
  object_id
  name
  aliases
  primary_class_id
  additional_class_ids

base_version_id
expected_result_schema_version
instructions_version
sources[]
evidence[]
files[]
selection / budget summary
warnings
```

`package_id`はopaque identity、`manifest_sha256`はcontent integrityとして分離するのが初期推奨である。

manifest本文にhash自身を含めると循環するため、G-02ではhash対象を明示する。初期候補は「`manifest_sha256` fieldを除外したcanonical JSONのSHA-256」とする。

## 9. G-03 `instructions.md`設計入力

instructionsは独自Knowledge formatを発明せず、Object Result schemaを説明する。

最低限:

- target Objectだけを分析する。
- supplied Package Evidenceのみを正式groundingに使用する。
- Package外Evidence ID / unknown Object IDを捏造しない。
- `direct_statement / synthesis / interpretation / reported_view`を区別する。
- reported viewにはattributionを付ける。
- Statement / known Attribute / RelationにEvidence referenceを付ける。
- effective Facetを全件status付きで返す。
- Evidence不足 / conflict / gap / unresolved referenceを構造化する。
- Registry proposalをKnowledge本体へ混ぜない。
- canonical return artifactは`result.json`。

instructions versionはmanifestへ記録する。

## 10. G-04 local staging / export gap

Package Buildはまず次へ出力する。

```text
exchange/staging/<package-id>/
```

これは外部送信ではない。

External Export前のpreflightには最低限次を含める。

- package ID / hash
- target Object / base Version
- files
- included Source / Evidence count
- current Knowledge同梱有無
- warning / destination / export decision

初期export decision contractは`allow / review_required / blocked`相当とする。

初期Google Drive integrationは、CoreへのOAuth/API依存を避けるため、`local staging → explicit copy → configured Google Drive sync folder`を第一候補とする。

## 11. G-05 Result receipt gap

`exchange/incoming/`は定義済みだが運用未実装である。

G-05で最低限決める。

- `result.json`必須。
- incomingへ置いただけではImportしない。
- detection / Validation / authoritative Importを分離する。
- malformed / missing / duplicate resultの扱い。
- ChatGPT分析失敗時のPackage rebuild / abandon。
- processedへ移動する時点。
- accepted Result original artifact保全はPhase Hへ引き継ぐ。

## 12. Phase G推奨実装順序

Task番号順を維持する。

### G-01 — Package format

- `src/sgokb/exchange/evidence_package.py`等のPackage model
- current Version reader / serializer
- current grounding Evidence carry-forward retrieval
- F-04 selectionとの統合
- in-memory Package representation

### G-02 — manifest schema

- `sgokb.evidence-package/1.0`
- JSON Schema
- canonical JSON serialization
- package ID / manifest hash
- manifest validator

### G-03 — instructions

- versioned instructions template
- deterministic renderer
- instructions version constant
- golden test

### G-04 — staging / export

- staging writer / atomic publish
- preflight
- configured sync-folder exporter
- export audit metadata

### G-05 — incoming workflow

- incoming locator
- package/result binding discovery
- receipt metadata
- explicit validate handoff
- processed transition rule

## 13. Phase Gで先取りしないもの

Phase Hへ残す:

- authoritative Result DB Import
- full DB-aware Result validation orchestration
- Object Version commit / current promotion
- Diff / Review UI
- accepted Result artifact canonical retention

Phase Iへ残す: persistent Embedding / Vector backend / reranker改善。

Phase Jへ残す: MCP Tool / Resource正式contract。

Phase Mへ残す: CLI全体の最終command naming / operator UX polish。

## 14. G-01で追加すべき主要test

1. current VersionなしObjectからPackage modelを構築できる。
2. current VersionありObjectで`base_version_id`を取得できる。
3. current Knowledge serializerがfull snapshotを再現する。
4. current VersionのEvidence Linkをcarry-forward候補として取得できる。
5. historical grounding Evidenceをcurrent Knowledge由来として明示的にPackageへ含められる。
6. F-04 selected Evidenceとcarry-forward Evidenceの重複を処理できる。
7. Package外Evidenceがincluded setへ紛れ込まない。
8. manual include / exclude provenanceを維持する。
9. Source diversity / selection reason / omission reasonを失わない。
10. Fragment / generative LLMを呼ばない。
11. Raw Artifact本文を無制限にPackageへ埋め込まない。
12. F-01〜F-05 regressionを破壊しない。

## 15. Phase G Definition of Ready

- [x] Phase A〜F完了。
- [x] canonical Source / Evidence Storeがある。
- [x] Object Evidence Retrievalがある。
- [x] bounded Evidence Selectionがある。
- [x] operator Source association / Evidence overrideがある。
- [x] Object Result static schemaがある。
- [x] Version lifecycle / current pointerがある。
- [x] `exchange/staging / incoming / processed` policyがある。
- [x] Google Drive writeをExternal Exportとして扱う境界がある。
- [x] local-first / no-silent-cloud-fallback要件がある。
- [x] Phase Gの不足APIと実装順を特定した。

以上によりPhase Gは開始可能である。

## 16. G-01開始時に読む文書

1. `docs/planning/PHASE_G_PREPARATION.md`
2. `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
3. `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
4. `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
5. `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
6. `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
7. `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
8. `docs/design/OBJECT_EVIDENCE_RETRIEVAL.md`
9. `docs/design/EVIDENCE_SELECTION_BUDGET.md`
10. `docs/design/OPERATOR_ASSOCIATION_CONTROLS.md`
11. `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`
12. `docs/design/VERSIONING_SCHEMA.md`
13. `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`

実装確認:

- `src/sgokb/application.py`
- `src/sgokb/retrieval/evidence.py`
- `src/sgokb/retrieval/package.py`
- `src/sgokb/exchange/object_result.py`
- `src/sgokb/storage/object_repository.py`
- `src/sgokb/storage/semantic_repository.py`
- `src/sgokb/storage/source_repository.py`
- `src/sgokb/storage/version_repository.py`

## 17. 次チャット用指示文

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。
Phase A〜Fは完了しています。

再設計の正規作業基盤はintegration/knowledge-base-redesignです。
まず以下を確認してください。
- docs/planning/PHASE_G_PREPARATION.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md
- docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md
- docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md
- docs/requirements/OBJECT_RESULT_REQUIREMENTS.md
- docs/design/OBJECT_EVIDENCE_RETRIEVAL.md
- docs/design/EVIDENCE_SELECTION_BUDGET.md
- docs/design/OPERATOR_ASSOCIATION_CONTROLS.md
- docs/design/OBJECT_RESULT_JSON_SCHEMA.md
- docs/design/VERSIONING_SCHEMA.md
- docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md

今回実施するTask:
G-01 [P0] Object Evidence Package formatを確定する

F-03〜F-05でcanonical Evidence retrieval、bounded selection、operator controlsまで成立しています。
G-01ではそれらを入力として、current accepted Knowledgeとそのgrounding Evidenceのcarry-forwardを含むObject Evidence Packageの論理formatを設計・実装してください。
Packageはderived local artifactでありcanonical Source of truthにはしないでください。
通常retrievalのeffective Evidenceとcurrent Knowledgeが参照するhistorical Evidenceを混同せず、F-04 hard budget、manual override、selection provenanceを維持してください。
G-02のmanifest JSON Schemaを過剰に先取りせず、G-01で必要なPackage value modelとserialization boundaryを確定してください。
```

## 18. 結論

Phase Fには残Taskはない。

Phase Fにより、生成LLMなしでcanonical EvidenceをObject単位にretrieveし、hard budget内へ選択し、operatorがSource association / Evidence overrideを明示的に調整できる状態まで完成した。

Phase Gではこの出力を外部交換可能なderived Packageへ変換し、local staging → explicit export → ChatGPT human-in-the-loop → result.json returnという往復経路を構築する。

**Next: `G-01 [P0] Object Evidence Package formatを確定する`**
