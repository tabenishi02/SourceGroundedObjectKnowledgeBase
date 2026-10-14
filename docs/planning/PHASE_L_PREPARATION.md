# Source Grounded Object Knowledge Base — Phase L Preparation

更新日: 2026-10-14

- Status: **In Progress**
- Phase: `Phase L — 旧Prototype移行・削除`
- Previous phase: `Phase K — SGOKB / UPDS連携試験` — Complete
- Previous closure: `docs/planning/PHASE_K_CLOSURE_AUDIT.md`
- Current task: `L-02 [P0] Final Document table / code / CLIの移行方針を確定する`
- Working branch: `main`

---

## 1. Phase Lの目的

Phase Lでは、Object / Evidence / Version / Search / MCP中心の新standard workflowが成立した後もrepository内に残る旧Prototype資産を整理する。

目的は単純なコード削減ではない。

> **旧Prototypeの履歴・既存DB・研究再現性を壊さず、Fragment / Final Document中心の高コスト処理を標準運用から完全に退役させる。**

Phase L完了条件:

> 旧Prototypeの高コスト処理が通常運用に残存していない。

---

## 2. Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| L-01 | P0 | Complete | Fragment table / code / CLIの処遇を確定した |
| L-02 | P0 | Next | Final Document table / code / CLIの処遇を確定する |
| L-03 | P1 | Pending | 既存Prototype DB migrationを設計する |
| L-04 | P1 | Pending | 旧benchmarkをarchiveする |
| L-05 | P0 | Pending | 不要依存関係・compatibility layerを削除する |

推奨順序は`L-01 → L-02 → L-03 → L-04 → L-05`とする。

L-01/L-02で何を保持するかを決める前にschemaやdependencyを削除しない。

L-01 decision:

- `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`

---

## 3. 既に確定している標準Pipeline境界

Phase Fでstandard workflowからFragment生成は除外済みである。

```text
Web Capture Bundle
  → canonical Source / Locator
  → Snapshot / Raw Artifact
  → Normalization Run
  → Evidence
  → Object Evidence Retrieval
  → Object Evidence Package
  → Object Result validation / import
  → accepted Object Knowledge Version
```

標準経路ではGenerative LLMによるFragment生成・Fragment依存Final Document生成を行わない。

旧機能はPhase Lまでlegacy / research compatibilityとして残されている。

関連正本:

- `docs/design/STANDARD_PIPELINE_BOUNDARY.md`
- `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
- `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
- `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`

---

## 4. Legacy DB資産の棚卸し

### 4.1 migration 001由来

`src/sgokb/migrations/001_initial.sql`には旧Prototype schemaが現在も含まれる。

主なlegacy領域:

```text
entities
entity_relations
entity_evidence
ai_runs
fragment_runs
fragments
fragment_evidence
search_items                 # evidence / fragment混在
search_fts
embedding_spaces             # Prototype Embedding Space
embeddings
documents
```

一方、旧`source / snapshot / artifact / normalized_run / evidence`にも移行対象データが存在する。

```text
sources
snapshots
artifacts
normalized_runs
evidence
```

これらは「削除対象」と即断せず、L-03でcanonical Source / Evidence schemaへの移送可否を評価する。

### 4.2 migration 002由来

`002_knowledge_capture.sql`にはHigh Recall Fragment / Final / benchmark系の補助tableが残る。

```text
page_contexts
extraction_jobs
extraction_batches
evidence_assessments
entity_candidates
structured_documents
ai_observations
benchmark_runs
benchmark_cases
```

これらのうち、Source分類等へ再利用可能な情報と、Fragment generation専用ledgerを区別する必要がある。

### 4.3 canonical replacementはすでに存在する

migration 006以降では新canonical Source / Evidence schemaをadditiveに導入している。

```text
source_records
source_locators
source_snapshots
raw_artifacts
normalization_runs
evidence_records
source_object_associations
evidence_links
...
```

`006_source_evidence_schema.sql`自身が旧Prototype tablesをPhase L data migrationまで保持すると明記している。

したがってL-03では旧tableを直接dropする前に、移送・整合性検証・rollback方針を決める。

---

## 5. Legacy code / CLI資産の棚卸し

### 5.1 Fragment generation

主な対象:

```text
src/sgokb/capture.py
src/sgokb/domain/_prototype.py::validate_fragments
src/sgokb/application.py legacy Fragment methods
src/sgokb/knowledge_repository.py legacy Fragment persistence/search
src/sgokb/prompts/fragment_extraction.*
src/sgokb/prompts/high_recall.*
```

CLI:

```text
legacy-fragment
fragment alias
```

L-01で次を確定した。

- 既存Fragment dataはlegacy read-only / audit資産として保全する。
- canonical schemaへFragment tableを持ち込まない。
- 新規Fragment generation write pathは退役させる。
- `capture.py`、Fragment prompt、Application / RepositoryのFragment write pathはactive packageからRetireする。
- `legacy-fragment`と`fragment` aliasはRetireする。
- research-only runtimeは維持せず、研究再現性はGit履歴・baseline・archive資料で確保する。
- `search_items(kind='fragment')`とlegacy Fragment embeddingはcurrent Searchへ移行しない。

詳細は`docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`を正本とする。

### 5.2 Final Document generation

主な対象:

```text
src/sgokb/final.py
src/sgokb/prompts/final_document.*
src/sgokb/prompts/final_order.*
legacy document / structured_documents tables
```

CLI:

```text
legacy-generate
generate alias
```

`final.py`はFragment clusterを入力に巨大Markdown / structured documentを作る旧workflowであり、新canonical Object Knowledgeの正本ではない。

一方、`src/sgokb/rendering/markdown.py`のObject Knowledge rendererは新設計資産なので、旧Final生成と混同して削除しない。

### 5.3 Legacy benchmark

主な対象:

```text
src/sgokb/benchmark.py
scripts/run_evaluation.py
scripts/run_speed_preflight.py
scripts/run_strata_preflight.py
scripts/run_strata_speed_preflight.py
scripts/run_upgrade_evaluation.py
benchmark/ 内のPrototype評価資産
```

CLI:

```text
legacy-benchmark
benchmark alias
```

ただし`benchmark/search-quality-gold-v1.json`やPhase IのSearch品質benchmarkは現行資産であり、Fragment速度benchmarkと一括archiveしない。

---

## 6. Provider / dependency境界

現行`pyproject.toml`の必須dependencyは、

```text
beautifulsoup4
httpx
jsonschema
```

であり、Generative LLM SDKそのものは必須dependencyとして固定されていない。

Embedding関連optional dependencyは現行standard Searchで必要なため維持対象:

```text
local-embedding
fast-embedding
vector-qdrant
```

`src/sgokb/providers.py`にはEmbedding adapterとlegacy Generative LLM adapterが同居しているため、L-05では次を分けて判断する。

```text
Embedding provider      → Keep
Generative LLM provider → legacy/research用途を確認してRetire/Isolate候補
```

L-01ではFragment generationのためだけにGenerative LLM runtimeを維持しないことを確定した。Final / benchmark等の残存用途はL-02/L-04を踏まえてL-05で最終判断する。

---

## 7. Compatibility layer棚卸し

D-05で意図的に残した互換surfaceがある。

### module shim

代表例:

```text
src/sgokb/importer.py
src/sgokb/extraction.py
src/sgokb/context.py
src/sgokb/search.py
```

これらはcanonical implementationへのre-export shimであり、L-05で削除条件を満たすか確認する。

### legacy method / CLI alias

```text
fragment()          → legacy_fragment()
capture_fragments() → legacy_capture_fragments()
generate()          → legacy_generate()
build_document()    → legacy_build_document()

fragment  → legacy-fragment
generate  → legacy-generate
benchmark → legacy-benchmark
```

L-01でFragment系method / CLIはRetire対象と確定した。CLI package conversion自体はPhase Mの責務であるため、L-05で実削除する際もPhase Mとの境界を維持する。

---

## 8. L-01決定結果 — Complete

正本:

- `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`

Decision:

> **既存Fragmentデータはlegacy read-onlyとして保全し、新規Fragment生成write pathは完全に退役させる。Fragment generation code / prompt / CLIをresearch-only runtimeとして現行packageに残さない。研究再現性はGit履歴・固定baseline・archive資料で確保する。**

主な確定事項:

1. `fragments / fragment_runs / fragment_evidence`をcanonical schemaへ持ち込まない。
2. existing Fragment rowsはL-03 migration完了前に削除しない。
3. Fragmentからaccepted Object Knowledgeを自動生成しない。
4. Fragment write pathはPhase Lで停止する。
5. `capture.py`、Fragment prompt、Fragment generation methodをactive packageからRetireする。
6. `legacy-fragment`と`fragment` aliasをRetireする。
7. Fragment search representation / embeddingをcurrent Searchへ移送しない。
8. legacy Fragment provenanceは監査可能性を保持する。
9. research-only runtimeは維持しない。
10. 実DB migrationはL-03、archiveはL-04、code / dependency cleanupはL-05へ分離する。

---

## 9. L-02で決めるべきこと

Final DocumentはKnowledge正本用途を廃止済みである。

L-02では次を分離する。

```text
旧Fragment-based Final generation  → Retire候補
canonical Object Markdown renderer → Keep
```

検討対象:

- `documents`
- `structured_documents`
- `src/sgokb/final.py`
- final prompt群
- `legacy-generate`
- `generate` alias
- 過去生成Markdownのarchive/read-only価値

L-01によりFragment generation runtimeはRetire確定済みなので、L-02で旧Final生成を残す場合も新規Fragment生成を前提にしてはならない。

---

## 10. L-03 migration準備

L-03は単なるSQL `DROP TABLE` Taskではない。

最低限、次のmappingを作る。

```text
legacy sources             → source_records + source_locators
legacy snapshots           → source_snapshots
legacy artifacts           → raw_artifacts
legacy normalized_runs     → normalization_runs
legacy evidence            → evidence_records + evidence_locations
legacy entity references   → Objectへのmapping可否を個別評価
legacy Fragment/Document   → migrate / archive / leave legacy の判断
```

要件:

- stable legacy IDの追跡可能性を失わない。
- Raw hash / Evidence provenanceを保持する。
- migrationを再実行して二重Importしない。
- migration前back up / rollback pathを定義する。
- migration後にrow count / reference / checksum等を検証する。
- accepted Object Knowledgeをlegacy Fragmentから自動生成しない。
- Fragment dataはL-01のread-only / audit方針に従う。

---

## 11. L-04 benchmark archive境界

archive対象は「Fragment/Final生成性能を現行MVP KPIとして扱う仕組み」である。

Keep対象:

- current Object Search quality gold
- Embedding / Vector backend評価
- Phase I Search / Similarity regression

Retire/archive対象:

- fragments/sec
- fragments per evidence
- Final Document生成速度
- High Recall extraction model比較をcurrent acceptance基準とすること

既存`docs/archive/prototype-0.2/`は歴史資料保存先としてすでに存在するため、L-04ではそこへの統合または専用archive locationを検討できる。

L-01ではFragment research runtimeを現行packageに残さないと確定したため、必要な再現情報はGit baseline / archive manifestへ寄せる。

---

## 12. L-05 cleanup gate

不要dependency / shim / aliasを削除する前に次を満たす。

- production codeが旧shimをimportしていない。
- current tests / scriptsがcanonical pathへ移行済み。
- standard CLI / package entrypointがlegacy codeを必要としない。
- legacy read-only方針がL-01/L-02で確定済み。
- migration方針がL-03で確定済み。
- benchmark archive方針がL-04で確定済み。
- full testまたは既知failureを明示したfocused regressionが通る。

Embedding dependencyは削除対象ではない。

Fragment generation code / prompt / CLIはL-01でRetire対象と確定済みだが、L-03 migration検証に必要なread pathを先に削除しない。

---

## 13. Phase Lで変更してはいけない境界

Phase L cleanupを理由に次を再設計しない。

- Object / Facet / Relation canonical schema
- Source / Evidence canonical semantics
- accepted Knowledge Version immutability
- Search Representation / Embedding Space semantics
- MCP read contract
- SGOKB / UPDS ownership boundary
- Object Result exchange contract

必要なcleanupで新canonical behaviorの変更が必要になった場合は、Phase Lのlegacy removalと別変更として扱う。

---

## 14. Definition of Ready

- [x] Phase FでFragmentをstandard pipelineから除外済み。
- [x] Object Knowledge canonical schema / Versioningが成立済み。
- [x] Object Evidence Package / Result import workflowが成立済み。
- [x] Search / SimilarityがFragment非依存で成立済み。
- [x] MCP Knowledge AccessがFragment非依存で成立済み。
- [x] SGOKB / UPDS integration contractがFragment非依存で成立済み。
- [x] Legacy Fragment / Final assetsの主要配置を棚卸しした。
- [x] Canonical Source / Evidence schemaとlegacy schemaの併存を確認した。
- [x] L-01でFragment資産の退役方針を確定した。

**Phase Lは進行中であり、L-02へ移行可能である。**

---

## 15. Phase L開始時の原則

1. まずL-01でFragmentの処遇をdecision化する。
2. decision前にlegacy table / codeを削除しない。
3. migration 001/002を過去履歴として書き換えない。
4. schema除去が必要なら新migrationとして実施する。
5. existing DB migrationを先に検証し、fresh DBだけを見て判断しない。
6. canonical Source/EvidenceやEmbedding assetをlegacy cleanupへ巻き込まない。
7. structural moveとbehavior削除を可能な限り分離する。

L-01は完了したため、次Taskは以下とする。

```text
L-02 [P0] Final Document table / code / CLIの移行方針を確定する
```
