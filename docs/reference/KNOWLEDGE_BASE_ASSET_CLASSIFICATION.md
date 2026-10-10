# Source Grounded Object Knowledge Base — 既存資産 Keep / Modify / Replace / Retire 分類

更新日: 2026-10-09

- Task: `A-02 [P0] 既存機能を Keep / Modify / Replace / Retire に分類する`
- Related Decision: `SGOKB-KB-001`
- Related:
  - `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

## 1. 目的

本書は、Knowledge Base再設計に際して、現行Prototypeの機能・データ・実装資産を次の4分類へ整理する。

- **Keep**: 新設計でも責務が基本的に変わらず、原則として再利用する。
- **Modify**: 基本的な価値・実装資産は再利用するが、Object中心設計へ合わせて責務・Schema・API等を変更する。
- **Replace**: 現行の目的・中心モデルが新設計と衝突するため、新しい仕組みへ置換する。部分的なアルゴリズムや検証コードの再利用は妨げない。
- **Retire**: 新しい標準運用から外す。即時削除を意味せず、legacy read-only / research-only / archiveとして残す可能性はPhase Lで決定する。

この分類は「ファイルを直ちに削除・移動する指示」ではない。正確な依存関係、既存DB移行可否、削除順序はA-03およびPhase Lで扱う。

---

## 2. 結論サマリー

### Keep

1. Web Page Capture Chrome extension / Native Host / Capture Bundle Format
2. Raw ImportとCapture Bundle検証
3. Source / Snapshot / Artifactの履歴保持
4. checksum / content hash / Raw不変性検証
5. HTML構造抽出・Normalize・Evidence生成の基盤
6. Raw → Snapshot → EvidenceのProvenance
7. SQLiteを正本DBとして利用する方針とmigration基盤
8. FTS5によるLexical Search基盤
9. Embedding provider abstraction / Embedding Space分離
10. Hybrid Searchの検索器としての基本構造
11. 破壊的上書きを避ける世代管理・再処理思想

### Modify

1. Entity → Object
2. Entity Relation / Evidence Link → Object Relation / Evidence Link
3. Page Context / Source分類
4. `search_items` と検索candidate model
5. Embedding対象
6. Hybrid Searchのfilter / ranking対象
7. Application service / orchestration
8. CLI
9. AI run / generation provenance記録
10. Benchmark / EvaluationのうちRetrieval品質評価
11. Structured Markdown renderingの一部
12. package metadata / dependency構成

### Replace

1. Fragment中心Knowledge Model
2. 全Evidenceを生成LLMでFragment化するHigh Recall Capture
3. Fragment抽出job / batch / coverage管理
4. Entity CandidateのLLM自動抽出を標準Knowledge生成へ組み込む方式
5. Fragmentを前提とするFinal Document生成
6. `documents` / `structured_documents` をKnowledge正本として扱う方式
7. `fragment` / `generate` を中心とする標準操作フロー
8. Local Generative LLMを標準Knowledge生成器として呼び出すPipeline

### Retire

1. Fragment生成速度を主要KPIとするbenchmark
2. 全Evidence Fragment化を前提にしたモデル速度比較・運用評価を現行MVPの受入基準として扱うこと
3. Fragment coverage / fragments-per-evidenceを標準Knowledge品質指標として扱うこと
4. 旧Final Documentの巨大Markdown生成を日常運用の必須成果物とすること
5. Prototype固有のlegacy CLI経路を新設計の標準操作として維持すること

---

## 3. Keep — 原則再利用する資産

### K-01 Web Capture / Native Host / Capture Bundle

**対象例**

- `extensions/web-page-capture/`
- Web Capture Bundle v1.0
- Capture時のDOM / metadata / frame / shadow DOM / MHTML等

**理由**

再設計後も入力はWeb上の一次資料であり、取得工程はFragmentやFinal Documentの存在に依存しない。SGOKBの目的がObject Knowledge Baseへ変わっても、Sourceを再現可能な形で取得する責務は維持される。

**方針**

原則Keep。後続でObject workflowへ接続するが、Capture拡張機能自体を再設計理由だけで作り直さない。

### K-02 Raw Import / Bundle Validation

**対象例**

- `src/sgokb/importer.py`
- ZIP path traversal防止
- 必須Artifact検証
- checksum coverage検証
- `capture_id` / timestamp / filename整合性検証
- duplicate Capture判定

**理由**

Raw Sourceの真正性と安全なImportはKnowledge Modelから独立した基盤である。

**方針**

Keep。Bundle format変更が必要になった場合も、既存v1.0 readerはlegacy readerとして価値を持つ。

### K-03 Source / Snapshot / Artifact / Normalized Run

**対象DB**

- `sources`
- `snapshots`
- `artifacts`
- `normalized_runs`
- `evidence`

**理由**

Sourceと取得時点Snapshotを分離し、Raw hashと処理世代を保持する構造は、新設計のProvenanceと再生成可能性に直接利用できる。

**方針**

概念としてKeep。列追加や命名調整はあり得るが、履歴を失う置換は行わない。

### K-04 checksum / content hash / Raw不変性

**対象例**

- SHA-256
- `raw_sha256`
- Evidence `content_hash`
- reprocess時のRaw変更拒否

**理由**

Object KnowledgeがどのSource generationから派生したかを追跡するために必要である。

**方針**

Keep。

### K-05 HTML構造抽出 / Normalize / Evidence生成

**対象例**

- `src/sgokb/extraction.py`
- `GenericExtractor`
- `WikipediaExtractor`
- `PixivExtractor`
- DOM position保持
- noise除去
- Block抽出
- chunk化

**理由**

新設計でもRaw HTMLを直接ChatGPTへ無制限に渡すのではなく、検索可能なEvidence層を作る必要がある。DOM位置と構造を保持したEvidenceはProvenanceにも有効である。

**方針**

基盤をKeep。サイト固有抽出精度やchunk budgetはPhase Fで調整可能とする。

### K-06 Provenance

**対象例**

- Source ID / Snapshot ID / Evidence ID
- Raw path / Raw SHA256
- Artifact / DOM position
- Entity-Evidence linkの考え方

**理由**

新Object Knowledgeでも最終的にSource / Evidenceへ遡れることが必須である。

**方針**

Provenance思想とSource/Evidence側の実装をKeep。Entity固有部分はObjectへModifyする。

### K-07 SQLite / migration / transaction基盤

**対象例**

- `Repository`
- SQLite WAL
- `PRAGMA foreign_keys=ON`
- `schema_migrations`
- SQL migration file方式

**理由**

再設計後もローカル正本DBとしてSQLiteを使用する方針と一致する。新Object schema導入のためにRDB自体を交換する理由はない。

**方針**

Keep。新Schemaはadditive migrationまたは明示migrationで追加する。

### K-08 Lexical Search / FTS5

**対象例**

- `search_fts`
- trigram tokenizer
- 短い日本語Queryへのliteral containment fallback

**理由**

Object Evidence RetrievalおよびObject Knowledge検索でLexical Searchは引き続き必須である。

**方針**

検索エンジン部分をKeep。検索対象SchemaはModifyする。

### K-09 Embedding abstraction / Embedding Space

**対象例**

- `Embedder` protocol
- `CompatibleEmbedder`
- `SentenceTransformerEmbedder`
- model / revision / dimension / configurationごとのEmbedding Space分離
- vector validation

**理由**

生成LLMを標準Pipelineから外してもEmbeddingは必要である。model変更時にVectorを混在させない設計も新要件に合致する。

**方針**

Keep。対象をEvidence / FragmentからEvidence / Object / Facetへ変更する。

### K-10 Hybrid Search engineの骨格

**対象例**

- lexical + semantic candidate
- Reciprocal Rank Fusion
- replaceable reranker
- VectorIndex abstraction

**理由**

FTSとSemantic Searchを組み合わせる設計は新方針と一致する。

**方針**

アルゴリズムとadapter境界をKeep。candidate rowとfilterはModifyする。

---

## 4. Modify — 新Object設計へ適応させる資産

### M-01 Entity → Object

**現行**

- `entities`
- `entity_relations`
- `entity_evidence`
- `entity add/list/relate/link`

**変更後**

共通Object + `primary_class` / `additional_classes` + Class Registryを中心とするObject modelへ移行する。Object Version、Facet、Relation、Evidence Linkを扱えるようにする。

**理由**

Entityという抽象概念自体は新Objectに近く、完全廃棄する必要はない。一方、VersioningとFacetを正本として扱えないためSchema変更が必要である。

### M-02 Page Context / Source metadata

**現行**

`source_type`, `publisher_type`, `page_purpose`, `subject_candidates`等をdeterministic / inferred / overrideで保持する。

**変更方針**

Source/Evidence retrievalの補助metadataとして再利用する。ただしObject候補自動生成のための情報と、Sourceそのもののmetadataを分離する。

### M-03 Search candidate model

**現行**

`search_items.kind` は `evidence` / `fragment` 固定である。

**変更後候補**

- Evidence
- Object overall
- Object Facet
- 必要に応じRelation representation

**理由**

Hybrid Search engine自体は再利用できるが、Fragmentを主要検索単位とするSchemaは新設計に合わない。

### M-04 SearchFilter / Facet / Object filters

`SearchFilter.entity` をObject中心へ変更し、Primary / Additional / ancestor Class、facet、source等のfilterを新Schemaに合わせる。

### M-05 Embedding対象

**現行**

Active Evidence / Fragment。

**変更後**

- Evidence embedding
- Object overall embedding
- Facet embedding
- 必要に応じRelation text embedding

Embedding provider abstraction自体はKeepする。

### M-06 Application orchestration

**現行**

`import → process → fragment → embed → search → generate`

**変更後**

`import → process → Object/Evidence link → package build/export → result validate/import → embed → search/render`

`Application` の「CLIとprovider/SQLを分離するapplication service」という役割は維持し、use caseを差し替える。

### M-07 CLI

**そのまま残しやすいコマンド**

- `import`
- `process` / `extract`
- `snapshots`
- `status`
- `search` の基本UI

**変更対象**

- `entity` → `object`
- `embed` の対象/filter
- `provenance` の対象
- `fragment`
- `generate`
- `coverage`
- benchmark系

新Object中心CLIの詳細はPhase Mで決定する。

### M-08 Generative AI provider資産

**現行**

- `CompatibleLLM`
- `LMStudioLLM`
- `StrataLLM`
- `llm_from_env`

**分類**

Modify。標準Knowledge生成への必須依存から外し、research / optional adapterへ降格する方向とする。

**理由**

A-01は生成AI APIそのものを禁止していない。既存adapterはモデル比較や研究用途で再利用価値があるため、即時Retireとはしない。

### M-09 AI run / generation provenance

`ai_runs`、model/revision、prompt/version、input/output、実行観測を記録する考え方は有用である。

ただし今後はローカルLLMの自動呼び出しだけでなく、Evidence Package、ChatGPT Result、import run等のgeneration provenanceを記録できる形へ変更する。

### M-10 Benchmark / Evaluation基盤

**Keep寄りでModifyする部分**

- versioned dataset
- RetrievalのRecall@K / MRR / nDCG
- human / LLM judge channelの区別
- schema適合と意味品質を混同しない方針
- checkpoint /再開可能性

**変更理由**

評価対象をFragment品質・Final巨大文書から、Object Result品質、Evidence retrieval、Similarity Search、Import validationへ移す必要がある。

### M-11 Markdown rendering

`final.py` のFinal Knowledge model自体はReplaceだが、構造化データからMarkdownを決定論的にrenderする考え方、citation表示、Source note表示等は新`rendering`層へ転用可能である。

---

## 5. Replace — 新設計へ置換する資産

### R-01 Fragment Knowledge Model

**対象**

- `fragment_runs`
- `fragments`
- `fragment_evidence`
- `validate_fragments()`
- Fragment Facet / epistemic metadataを正本Knowledgeの中心とする設計

**置換先**

Object Version / Semantic Facet / Relation / Evidence Linkを持つStructured Object Knowledge。

### R-02 High Recall Fragment Capture

**対象**

- `src/sgokb/capture.py`
- `HighRecallCapture`
- 全Evidence assessment
- batch / window分割
- LLM quote selection
- 0 Fragment理由管理

**理由**

これは「全Evidenceを生成LLMでFragment化する」旧標準Pipelineの中心実装であり、SGOKB-KB-001と直接衝突する。

**置換先**

Object Evidence Retrieval + Evidence Package生成。

### R-03 Fragment extraction job / coverage model

**対象DB**

- `extraction_jobs`
- `extraction_batches`
- `evidence_assessments`

**対象CLI**

- `coverage`

**置換先**

Package build run、Evidence selection ledger、Result import run等。必要な追跡能力は維持するが、「全EvidenceがFragmentを持つか」を成功条件にしない。

### R-04 Entity Candidate generation

**対象**

- `entity_candidates`
- High Recall extraction中にLLMがEntity候補を生成する処理

**理由**

新設計ではObject対象を人間が明示的に扱うことを基本とし、LLM自動発見をKnowledge生成の必須工程としない。

将来補助機能として候補提示を導入する場合は、正本Object登録とは分離する。

### R-05 Final Document Knowledge Model

**対象**

- `documents`
- `structured_documents`
- `StructuredFinal`
- `cluster_fragments()`
- Fragment集合を正本相当のFinalへ統合するフロー

**置換先**

Structured Object Result → Validation → Object Version Store。

MarkdownはObject JSON/DBから生成する派生表示へ変更する。

### R-06 標準Generative LLM Pipeline

**対象**

- `Application.call_llm()`をFragment/Final標準処理として使用する構成
- `fragment_extraction`, `high_recall`, `final_order`等のPrompt contract

**置換先**

Object Evidence Package → Human-in-the-loop ChatGPT → result.json → Import Validator。

既存provider adapter自体はoptional/research資産としてModify扱いとする。

---

## 6. Retire — 標準運用・主要評価指標から外す資産

### T-01 Fragment生成速度benchmarkを主要KPIとすること

モデルtokens/s、Fragment生成時間、全Evidence Fragment化完了時間は歴史的Prototype比較として保存できるが、新SGOKBの主要性能指標から外す。

### T-02 Fragment coverageをKnowledge品質の主要指標とすること

`evidence_with_fragments`, `fragment_coverage`, `average_fragments_per_evidence`は旧Pipelineのcoverage指標である。

新設計ではEvidence Retrieval Recall、Object Resultの根拠適合、検索品質等へ置換する。

### T-03 巨大Final Markdownを必須成果物とすること

Markdown表示そのものは残せるが、全Knowledgeを1本の巨大文書へ統合することを日常運用の完了条件から外す。

### T-04 Prototype固有legacy CLIを新標準として維持すること

次を新Object workflowの標準コマンドとはしない。

- `fragment`
- legacy `generate`
- `coverage`
- Fragment/Final専用benchmark phase

削除時期とcompatibility期間はPhase L / Mで決定する。

### T-05 旧モデル速度・Final生成文書を現行仕様とみなすこと

次の文書・benchmark資産は削除ではなくArchive候補とする。

- Fragmentモデル比較
- Local Generative LLM速度予備試験
- Prototype Final品質・処理時間評価
- Fragment Pipeline改善案

D-02で`docs/archive/prototype-0.2/`等への配置を検討する。

---

## 7. DB table単位の暫定分類

| Table | 分類 | 方針 |
|---|---|---|
| `schema_migrations` | Keep | migration基盤として継続 |
| `sources` | Keep | Source正本として継続 |
| `snapshots` | Keep | 取得世代・Raw参照として継続 |
| `artifacts` | Keep | Capture artifact整合性保持 |
| `normalized_runs` | Keep | Evidence再生成可能性を保持 |
| `evidence` | Keep | 一次資料由来の検索単位として継続 |
| `page_contexts` | Modify | Source metadataとして再評価 |
| `entities` | Modify | Objectへ移行 |
| `entity_relations` | Modify | Object Relationへ移行 |
| `entity_evidence` | Modify | Object Evidence Linkへ移行 |
| `search_items` / `search_fts` | Modify | Fragment固定を解除しObject/Facet対応 |
| `embedding_spaces` | Keep | model/revision/config分離を継続 |
| `embeddings` | Modify | Object/Facet等の対象追加 |
| `ai_runs` / `ai_observations` | Modify | Generation/Import provenanceへ一般化 |
| `fragment_runs` | Replace | Object Version / Facet生成へ置換 |
| `fragments` | Replace | Object Facet等へ置換 |
| `fragment_evidence` | Replace | Object/Facet Evidence Linkへ置換 |
| `extraction_jobs` | Replace | Package/Evidence selection runへ置換候補 |
| `extraction_batches` | Replace | 旧Fragment batch contractを廃止 |
| `evidence_assessments` | Replace | Fragment coverage前提を廃止 |
| `entity_candidates` | Replace | 標準Object登録から分離 |
| `documents` | Replace | Object Version Store + Rendererへ置換 |
| `structured_documents` | Replace | Structured Object Result/Versionへ置換 |
| `benchmark_runs` / `benchmark_cases` | Modify | 新評価軸へ再利用 |

これはA-02時点の責務分類であり、既存実データをどのtableからどこへmigrationするかはA-03 / L-03で確定する。

---

## 8. コード資産単位の暫定分類

| 主な資産 | 分類 | 注記 |
|---|---|---|
| `extensions/web-page-capture/` | Keep | 取得層として独立継続 |
| `src/sgokb/importer.py` | Keep | Raw Bundle reader / validation |
| `src/sgokb/extraction.py` | Keep | Evidence生成基盤。chunk等は調整可 |
| `src/sgokb/repository.py` | Modify | SQLite基盤はKeep、Entity/Fragment/Document部分を再構成 |
| `src/sgokb/knowledge_repository.py` | Replace/Modify | Fragment extraction部分はReplace、追跡・run管理パターンは再利用可 |
| `src/sgokb/domain.py` | Modify | Embedder等はKeep、SearchFilter/LLM/Fragment validationを再編 |
| `src/sgokb/context.py` | Modify | Source metadataとして再利用 |
| `src/sgokb/search.py` | Modify | engine骨格Keep、candidate schema変更 |
| `src/sgokb/providers.py` Embedding部分 | Keep | 新検索でも利用 |
| `src/sgokb/providers.py` Generative LLM部分 | Modify | optional/researchへ降格 |
| `src/sgokb/application.py` | Modify | application service境界維持、use case交換 |
| `src/sgokb/cli.py` | Modify | Object中心CLIへ全面再編 |
| `src/sgokb/capture.py` | Replace | High Recall Fragment pipeline |
| `src/sgokb/final.py` | Replace | Final Knowledge model。rendering部のみ転用候補 |
| `src/sgokb/benchmark.py` | Modify | Retrieval評価再利用、Fragment/Final phaseはRetire |
| `benchmark/`旧Fragment/Finalケース | Retire/Archive | 新goldとは分離して保存 |
| Prototype速度・モデル比較docs | Retire/Archive | 歴史的評価として保持 |

---

## 9. 移行時の原則

1. **Keep資産でも無条件コピーしない。** Object schemaへ依存する参照だけは変更する。
2. **Replaceは即deleteを意味しない。** 新Vertical Sliceが成立するまで旧Prototypeを動作可能な比較基準として保持する。
3. **Raw / Source / Snapshot / EvidenceをFragment削除の巻き添えにしない。**
4. **Embedding providerとGenerative LLM providerを同一扱いにしない。** 生成LLMを標準から外してもEmbeddingは標準機能として残す。
5. **検索アルゴリズムと検索対象Schemaを分離する。** Hybrid Searchの骨格は再利用し、Fragment固定だけを外す。
6. **Markdown rendererとMarkdown正本を区別する。** 表示生成は残せるが、正本はStructured Object Dataとする。
7. **Prototype評価結果を削除しない。** 現行仕様から外し、Archive / Historical Evidenceとして保持する。

---

## 10. A-03へ引き継ぐ確認事項

A-02では責務レベルの分類を完了した。A-03では、この分類をコード・DB・テスト依存へ具体化する。

最低限、次を確認する。

- `fragments` / `documents`を参照する全Python module / CLI / test / script
- `entities`をObjectへ変更した場合のforeign keyとfilter影響
- `search_items.kind`の`evidence/fragment`固定箇所
- Fragment削除時にEvidence/FTS/Embeddingを独立維持できるか
- `ai_runs`をlegacy generation記録として保持しつつ新generation provenanceへ拡張できるか
- 実データSQLite DBからSource / Snapshot / Evidence / Entity相当データを安全に移行できるか
- Prototype benchmark / docs / fixturesのArchive対象一覧

A-03完了までは、旧tableやmoduleの物理削除を行わない。
