# Source Grounded Object Knowledge Base — 既存依存関係・DB移行棚卸し

更新日: 2026-10-09

- Task: `A-03 [P1] 既存DB・CLI・モジュール・テストの依存関係を棚卸しする`
- Related Decision: `SGOKB-KB-001`
- Related:
  - `docs/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
  - `docs/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
  - `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

## 1. 目的

本書は、A-02で分類した既存資産を実装単位へ落とし込み、Fragment / Final Document中心の旧Prototype機能を標準パイプラインから外した場合の影響範囲を整理する。

対象は次のとおり。

- SQLite schema / foreign key / search index / embedding
- CLI command
- `src/sgokb` module
- prompt / JSON Schema
- `tests/`
- `scripts/`
- 既存実データDBの移行可否

本書は削除手順そのものではない。実際のschema migration、legacy table退避、物理削除はPhase E / Lで設計・実施する。

---

## 2. 結論

既存SGOKBは、次の3層に分離して扱うのが安全である。

```text
[再利用可能な基盤]
Source / Snapshot / Artifact
        ↓
Normalized Run / Evidence / Page Context
        ↓
FTS / Embedding基盤

[新設計へ変換する層]
Entity
  ↓
Object / Object Version / Facet / Relation / Evidence Link

[旧Prototype固有層]
Fragment Extraction
  ↓
Fragment
  ↓
Final Document
```

最上段のSource / Evidence系は新設計へそのまま持ち込める。Entity系はIDを維持したObjectへの変換が可能である。Fragment / Final Document系は正本として移行する必要はなく、legacy / archive扱いにできる。

したがって、**既存実データDBは移行可能と判断する**。Raw Captureから全件を再収集し直す必要はない。

ただし、現行`search_items`と`embeddings`はFragmentとEvidenceを同一Indexへ載せ、`embeddings.item_id`が`search_items.id`へ依存しているため、Object中心schema導入時はEmbedding Indexを再構築する方が安全である。

---

## 3. DB依存関係

### 3.1 再利用するSource / Evidence系

```text
sources
  └─ snapshots
      ├─ artifacts
      ├─ normalized_runs
      │   ├─ evidence
      │   └─ page_contexts
      └─ active_run -> normalized_runs
```

### `sources`

依存される側。`snapshots.source_id`、`evidence.source_id`から参照される。

**判断:** Keep。

### `snapshots`

`source_id`でSourceを参照し、`active_run`で現在のNormalized generationを指す。Artifact、Evidence、Page Context、旧Fragment Extractionの起点でもある。

**判断:** Keep。

Fragment系を廃止してもSnapshot自体は影響を受けない。

### `artifacts`

Snapshotの取得Artifact hash / sizeを保持する。

**判断:** Keep。

Fragment / Documentへの依存なし。

### `normalized_runs`

Snapshotから抽出したBlockとconfigurationを世代管理する。

**判断:** Keep。

旧Fragment Runから参照されているが、Fragment側をlegacy化してもNormalized Run自体は保持する。

### `evidence`

`normalized_runs`, `sources`, `snapshots`を参照する一次資料側の検索単位。

**判断:** Keep。

新Object KnowledgeでもEvidence Linkの終点として必要である。

### `page_contexts`

`normalized_run` / `snapshot_id`に依存するSource metadata層。

**判断:** Keep寄りのModify。

Fragment Extraction専用ではないため、Source/Evidence Retrieval metadataとして再利用できる。

---

## 4. Entity → Object移行対象

現行依存関係:

```text
entities
  ├─ entity_relations
  ├─ entity_evidence
  ├─ fragment_runs
  ├─ fragments
  ├─ extraction_jobs
  └─ documents
```

### `entities`

Character / Work / Concept等をすでに共通IDで保持しているため、新`objects`の前身として利用可能。

**推奨移行:** `entities.id`をそのまま`objects.object_id`へ引き継ぐ。

これにより、既存RelationやEvidence Linkを移し替える際にID変換表を不要にできる。

### `entity_relations`

**推奨移行:** `object_relations`へコピーし、subject/object IDを維持する。

metadataの`origin`等は新Relation provenanceへ移行可能。

### `entity_evidence`

**推奨移行:** `object_evidence`または新Evidence Link schemaへコピーする。

Evidence IDはKeep対象なので参照先を維持できる。

### 注意点

Entityを先にDROPしてはいけない。`fragment_runs`, `fragments`, `extraction_jobs`, `documents`がforeign keyでEntityを参照しているためである。

安全な順序は、

1. `objects`等の新schemaを追加
2. EntityをObjectへコピー
3. Relation / Evidence Linkをコピー
4. 新Object workflowへ切替
5. 旧Fragment / Documentをlegacy化
6. 最後にEntity互換層の扱いを決定

とする。

---

## 5. Fragment系DBの依存関係

```text
ai_runs
   ↓
fragment_runs
   ↓
fragments
   ├─ fragment_evidence -> evidence
   └─ search_items(kind='fragment')
          ↓
       search_fts
          ↓
       embeddings

extraction_jobs
   ├─ extraction_batches
   │    └─ ai_runs
   ├─ evidence_assessments
   └─ entity_candidates
```

### `fragment_runs`

`normalized_runs`, `snapshots`, `entities`, `ai_runs`へ依存する。

### `fragments`

`fragment_runs`, `entities`へ依存する。

### `fragment_evidence`

FragmentからEvidenceへのProvenanceを保持する。

### `extraction_jobs`

High Recall Fragment Extractionの実行状態そのもの。`fragment_run`を参照し、Entity / Contextにも依存する。

### `extraction_batches`

Fragment生成batch checkpoint。

### `evidence_assessments`

全EvidenceをFragment化する方式におけるcoverage管理。

### `entity_candidates`

Fragment Extraction中にLLMが返すEntity候補を保存する。

**総合判断:** Replace / legacy対象。

これらを単純DROPすると、旧評価結果と処理履歴を失う。Phase Lまでは既存tableをread-only historyとして残し、新標準パイプラインから参照しない方式が安全である。

---

## 6. Final Document系DBの依存関係

```text
entities
  ↓
documents
  ├─ ai_runs
  └─ structured_documents
```

### `documents`

Entity単位のMarkdownとcitationを保持する。

### `structured_documents`

Documentへ1:1でぶら下がり、旧Final representation / clusterを保持する。

**判断:** Knowledge正本としてReplace。

既存文書は歴史的生成物として保持可能だが、新Object Knowledgeへ自動的に正本昇格させない。

`final.py`のrenderingロジックの一部は、新しいObject JSON → Markdown Rendererの参考または再利用候補とする。

---

## 7. Search / Embedding依存関係

現行:

```text
Evidence ─┐
          ├─ search_items(kind=evidence|fragment)
Fragment ─┘
                 ↓
              search_fts
                 ↓
        lexical candidate

search_items.id
      ↓
embeddings.item_id
      + embedding_spaces
```

### `search_items`

`kind` CHECKが`evidence` / `fragment`に固定されている。

**判断:** Modify必須。

新設計では少なくともEvidence / Object overall / Object Facetを検索対象にする必要がある。

### `search_fts`

FTS5 + trigramという検索方式自体は再利用可能。

**判断:** Keepするが、index内容は再構築する。

### `embedding_spaces`

model / revision / dimension / configurationを分離する設計はそのまま有効。

**判断:** Keep。

### `embeddings`

`item_id`が`search_items.id`に依存する。この整数IDは新しいsearch item構築時に同一になる保証がない。

**判断:** Schemaの考え方はKeep/Modifyだが、**既存vectorの物理移行は原則行わず再Embeddingを推奨**する。

Evidence本文自体は保持されるため、Embeddingは再生成可能である。Fragment embeddingは新標準Knowledge Modelでは不要。

---

## 8. AI実行履歴 / Benchmark DB

### `ai_runs`

旧Fragment / Finalの生成履歴として多数のtableから参照される。

**判断:** 当面保持。

新設計ではChatGPT手動ResultやPackage importなどを記録できるgeneration/import provenanceへ拡張する。旧`ai_runs`を即時削除するとFragment/Document履歴のforeign keyが壊れるため、Phase Lまでは残す。

### `ai_observations`

`ai_runs`に付随する速度・usage等。

**判断:** legacy/research historyとして保持可能。

### `benchmark_runs` / `benchmark_cases`

DB構造自体は汎用的だが、現行caseはFragment / Final前提が多い。

**判断:** framework思想はModifyして再利用し、旧runはhistorical recordとして扱う。

---

## 9. CLI依存関係

| 現行command | 主依存 | 新設計での扱い |
|---|---|---|
| `import` | importer / sources / snapshots | Keep |
| `process` / `extract` | extraction / normalized_runs / evidence / page_context | Keep |
| `entity add/list/relate/link` | entities / relations / evidence link | `object`系へModify |
| `fragment` | LLM / capture / extraction_jobs / fragments | Replace、標準flowから削除 |
| `coverage` | extraction_jobs / evidence_assessments / fragments | Retire/legacy |
| `embed` | search_items / embeddings | Modify |
| `search` | SearchFilter / FTS / vector / reranker | Modify |
| `generate` | fragments / final / documents | Replace。将来`render`等へ分離 |
| `context` | page_contexts | Keep/Modify |
| `benchmark` | benchmark.py + Fragment/Final/Retrieval | Modify。旧phaseはarchive |
| `benchmark-score` | human/judge labels | Modifyして再利用可能 |
| `provenance evidence` | Source/Evidence | Keep |
| `provenance fragment/document` | legacy tables | legacy扱い |
| `status` | 全table件数 | Modify |
| `snapshots` | Source/Snapshot | Keep |

`cli.py`自体はadapterとして残すが、現在のparserとdispatchは旧Object flowへ強く結合しているため、Phase Mで再構成する。

---

## 10. `src/sgokb` module依存関係

### `importer.py` — Keep

Capture Bundle reader / validation。Knowledge Modelから独立。

### `extraction.py` — Keep

DOM → Block → Evidence。Fragment生成とは独立。

### `context.py` — Keep/Modify

Page ContextをSource/Evidence retrieval metadataとして利用可能。

### `repository.py` — Split / Modify

1ファイル内に、Source/Evidence、Entity、Fragment、Search、Embedding、Documentが混在している。

再設計時は責務別repositoryへ分割候補。ただしDB transaction / migration / low-level SQLite helperは再利用する。

### `knowledge_repository.py` — Mostly Replace

主にHigh Recall Extraction job、coverage、structured document、benchmark checkpointを扱うためFragment/Final依存が強い。

`ai_observations`やcheckpoint思想は抽出して再利用可能。

### `domain.py` — Modify

再利用:

- `digest`
- `json_text`
- `EmbeddingSpace`
- `Embedder` / `VectorIndex` / `Reranker` protocol
- vector validation

変更/廃止:

- `SearchFilter.entity`
- `LLM`を標準Core必須境界として扱うこと
- `validate_fragments`

新Object / Relation / Facet / Version value objectへ置換・拡張する。

### `search.py` — Modify

RRF、VectorIndex、reranker境界は再利用。Candidate rowとfilterをObject中心へ変更する。

### `providers.py` — Split

Embedding providerはKeep。

Generative LLM providerは標準runtime必須から外し、optional/research adapterへ移す候補。

### `capture.py` — Replace / Legacy

全EvidenceをLLMで評価しFragment化するHigh Recall Pipelineそのもの。

### `final.py` — Replace + Renderer部分再利用候補

Fragment clusterを正本Finalへまとめる責務は廃止。Markdown生成技術だけ新Rendererへ移植可能。

### `benchmark.py` — Modify

Retrieval metricとhuman/judge channelは再利用。Fragment / Final case処理はlegacy化する。

### `application.py` — Modify

Application Serviceという境界は維持するが、

```text
fragment / capture_fragments / generate / build_document
```

を標準use caseから外し、

```text
object / package / result import / render / object retrieval
```

へ置換する。

### `cli.py` — Modify

Moduleは維持できるがcommand構成を変更する。

---

## 11. Prompt / JSON Schema依存関係

現行Prompt:

- `fragment_extraction.md` / schema
- `high_recall.md` / schema
- `final_document.md` / schema
- `final_order.md` / schema

これらはFragment / Final Document中心の旧Pipelineへ結合している。

**判断:** 新標準運用ではReplace / archive。

Phase GでChatGPT用`instructions.md`、Phase E/HでObject Result JSON Schemaを新たに定義する。旧Promptはモデル比較再現用としてPhase L/Oまで保持する。

---

## 12. Test依存関係

### `tests/conftest.py`

現在の共通fixtureが、`Repository + FixtureLLM + FixtureEmbedder + Entity + Evidence`を一括で準備する。

**影響:** Modify必須。

新fixtureではSource/EvidenceまでをCore fixtureとし、Object / Result / Embedding fixtureを分離する。FixtureLLMを全テスト共通の前提にしない。

### `tests/test_core.py`

**そのまま残せる/小変更で残せる主な試験**

- Bundle checksum / format / duplicate検証
- Raw不変性
- structural extraction
- chunk overlap / section
- 日本語FTS
- vector validation
- processing failure時のactive generation保持
- embedding atomicity
- auxiliary frame / shadow isolation
- site-specific extractor
- migration reopen
- Raw overwrite guard

**Modify対象**

- Entity relation
- metadata filter
- semantic searchで`evidence + fragment`を期待する試験
- CLI command構成

**Replace/legacy対象**

- Fragment validation
- Fragment provenance
- Final Document grounding
- Fragment save rollback
- empty Fragment generation
- Final failure preservation

### `tests/test_upgrade.py`

Fragment High Recall / quote selection / coverage / resume / Final clusterを中心にした試験が大半を占める。

**Replace/legacy対象:**

- extraction window
- quote choice
- Fragment validation
- evidence assessment / coverage
- Final cluster / conflict
- Fragment generation resume

**再利用可能:**

- Page Context generation / override
- DB非破壊更新の思想
- retrieval metrics / human judgement metricの一部

### `tests/test_providers.py`

Embedding provider試験はKeep。

LLM / Strata / LM Studio試験はoptional/research provider testへ分類する。

### `tests/test_speed_preflight.py`

旧Fragment形式を固定入力として生成速度を測るため、現行MVPの標準test suiteからはarchive/researchへ移す候補。

### `tests/test_strata_speed_preflight.py`

同様に旧Fragment contractへ依存するためarchive/research候補。

---

## 13. Script依存関係

### `scripts/inventory_samples.py` — Keep

Raw Capture Bundleを読み、秘密データ本文をGit管理へ持ち込まずInventoryを作る。新設計でも有効。

### `scripts/run_evaluation.py` — Replace / Rewrite

Deterministic部のImport / Process / Raw不変性 / Lexical確認は再利用可能。

AI部は`fragment → embed → generate`へ強く依存するため、新Vertical Slice向けに書き直す。

### `scripts/run_upgrade_evaluation.py` — Legacy/Research

`fragment / retrieval / final` phaseと旧benchmark manifestへ依存。DB backup、integrity_check、foreign_key_check、Raw不変性検証の実装パターンは新migration dry-runへ再利用可能。

### `scripts/export_upgrade_review.py` — Legacy/Archive

`fragments`, `fragment_evidence`, `extraction_jobs`, `documents`, `structured_documents`を直接SQL参照するため旧schema依存が非常に強い。

### `scripts/run_speed_preflight.py` — Research/Archive

旧Fragment contractを生成速度比較の入力に利用。

### `scripts/run_strata_preflight.py` / `run_strata_speed_preflight.py` / `Use-Strata.ps1` — Research/Archive

生成LLM性能比較用。標準Knowledge workflowからは独立させる。

---

## 14. Fragment / Finalを外した場合の直接影響範囲

### 必ず変更または隔離が必要

```text
src/sgokb/capture.py
src/sgokb/final.py
src/sgokb/knowledge_repository.py
src/sgokb/application.py
src/sgokb/repository.py
src/sgokb/domain.py
src/sgokb/search.py
src/sgokb/cli.py
src/sgokb/providers.py
src/sgokb/benchmark.py
src/sgokb/prompts/*

tests/conftest.py
tests/test_core.py
tests/test_upgrade.py
tests/test_providers.py
tests/test_speed_preflight.py
tests/test_strata_speed_preflight.py

scripts/run_evaluation.py
scripts/run_upgrade_evaluation.py
scripts/export_upgrade_review.py
scripts/run_speed_preflight.py
scripts/run_strata_preflight.py
scripts/run_strata_speed_preflight.py
scripts/Use-Strata.ps1
```

### 基本的に維持できる

```text
extensions/web-page-capture/
src/sgokb/importer.py
src/sgokb/extraction.py
src/sgokb/context.py
scripts/inventory_samples.py
```

ただし物理的なmodule移動はPhase Dで行い、A-03では実施しない。

---

## 15. 既存実データDBの移行可否

### 結論

**移行可能。Raw Captureからの全面再構築は不要。**

根拠:

1. Raw / Source / Snapshot / Artifact / Normalized Run / EvidenceがFragmentより下位の独立した層として保存されている。
2. EvidenceはSource / Snapshot / Normalized Runへ直接Provenanceを持つ。
3. EntityはすでにUUID系の安定IDで管理され、新Objectへ同一IDで移行可能。
4. Entity-Evidence RelationもEvidence IDを保持している。
5. Prototype実データ評価ではSQLite integrity正常・foreign key errorなしが確認済みである。
6. 現行migration方式がadditiveであり、既存recordを残したまま新tableを追加できる。

### 移行対象別判断

| 現行データ | 移行判断 | 方針 |
|---|---|---|
| Source | 移行 | ID維持 |
| Snapshot | 移行 | ID / Raw path / hash維持 |
| Artifact | 移行 | そのまま保持 |
| Normalized Run | 移行 | 世代履歴保持 |
| Evidence | 移行 | Evidence ID維持 |
| Page Context | 移行 | Source metadataとして保持 |
| Entity | 移行 | 同一IDでObject化を第一候補 |
| Entity Relation | 移行 | Object Relationへ変換 |
| Entity Evidence | 移行 | Object Evidence Linkへ変換 |
| Evidence FTS | 再構築可 | 新search schemaへreindex |
| Evidence Embedding | 原則再生成 | search item ID変更リスク回避 |
| Fragment | 正本移行しない | legacy/archive判断をPhase Lで実施 |
| Fragment Embedding | 移行不要 | 新標準では不要 |
| Extraction Job / Assessment | 正本移行しない | historical record |
| Document / Structured Document | 正本移行しない | historical/renderer参考 |
| AI Run / Observation | 必要に応じ保持 | legacy provenance |
| Benchmark Run | history保持可 | 新評価とは別version |

### 実データ確認の範囲

Git管理外の`.local/*.sqlite`そのものは本A-03では変更していない。移行可否は、Git管理中のschema、現行実装、既存実データ評価結果に基づいて確認した。

実DBに対するmigration dry-run、件数照合、`PRAGMA integrity_check`、`PRAGMA foreign_key_check`、旧DBとのObject/Evidence ID照合はPhase L-03で実施する。

これは「移行可否が不明」という意味ではなく、**schema上は移行可能と確認済みで、破壊的migrationを実データへまだ実行していない**という区別である。

---

## 16. 推奨Migration Strategy

既存DBを直接作り替えるより、段階的なadditive migrationを推奨する。

```text
Step 1  既存Source / Evidence系をそのまま保持
Step 2  objects / object_versions / facets / object_relations / evidence_linksを追加
Step 3  entities → objectsへ同一IDでcopy
Step 4  entity_relations / entity_evidenceを新tableへcopy
Step 5  Object workflowを新table側へ切替
Step 6  search_items / FTS / embeddingsをObject対応schemaで再構築
Step 7  新Vertical Sliceの受入試験
Step 8  Fragment / Document系をlegacy read-only化
Step 9  Phase Lでarchive / drop可否を最終決定
```

この方式なら、新設計完成前に旧Prototypeデータを破壊せず、比較・rollbackが可能である。

---

## 17. A-03完了判断

A-03で要求された事項は次のとおり満たした。

- DB table / foreign key依存を整理した。
- Fragment / Final Documentを外した場合の影響範囲を一覧化した。
- CLI commandの依存先と移行分類を整理した。
- 主要moduleの依存・再利用可否を整理した。
- Prompt / Schemaの旧Pipeline依存を整理した。
- 全test fileの扱いを整理した。
- scriptsの扱いを整理した。
- 既存実データDBについて、Source/Evidence/Entityを保持した移行が可能と判断した。
- Embeddingは再Index / 再生成を基本とする判断を明記した。
- 実DBへの破壊的migrationはPhase L-03まで行わない境界を明記した。

この棚卸しにより、後続Phaseは旧PrototypeのFragment / Final Document依存を暗黙に引き継がず、新Object Knowledge Modelを設計できる状態になった。
