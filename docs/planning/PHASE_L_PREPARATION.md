# Source Grounded Object Knowledge Base — Phase L Preparation

更新日: 2026-10-14

- Status: **Ready to Start**
- Phase: `Phase L — 旧Prototype移行・削除`
- Previous phase: `Phase K — SGOKB / UPDS連携試験` — Complete
- Previous closure: `docs/planning/PHASE_K_CLOSURE_AUDIT.md`
- Current task: `L-01 [P0] Fragment table / code / CLIの移行方針を確定する`
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
| L-01 | P0 | Next | Fragment table / code / CLIの処遇を確定する |
| L-02 | P0 | Pending | Final Document table / code / CLIの処遇を確定する |
| L-03 | P1 | Pending | 既存Prototype DB migrationを設計する |
| L-04 | P1 | Pending | 旧benchmarkをarchiveする |
| L-05 | P0 | Pending | 不要依存関係・compatibility layerを削除する |

推奨順序は`L-01 → L-02 → L-03 → L-04 → L-05`とする。

L-01/L-02で何を保持するかを決める前にschemaやdependencyを削除しない。

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

Phase Fではstandardから除外済みだが、Phase Lで`完全削除 / legacy read-only / research-only`のどれにするかを確定する。

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
Embedding provider     → Keep
Generative LLM provider → legacy/research用途を確認してRetire/Isolate候補
```

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

CLI package conversion自体はPhase Mの責務であるため、Phase Lで互換aliasを削除する場合もPhase Mとの境界を確認する。

---

## 8. L-01で決めるべきこと

L-01ではFragment資産を物理削除する前に、処遇をdecisionとして固定する。

最低限の論点:

1. `fragments / fragment_runs / fragment_evidence`を新DBで維持するか。
2. 既存DBのFragmentを監査・研究目的で読み出す必要があるか。
3. Fragment write pathを完全停止するか。
4. `capture.py`をarchive / `_legacy` / deleteのどれにするか。
5. Fragment promptをpackage dataに残すか。
6. `legacy-fragment`を維持するか。
7. `fragment` aliasをPhase Lで削除するか、Phase Mまで残すか。
8. `search_items(kind='fragment')` / Prototype embeddingとの関係をどう扱うか。
9. Fragment provenanceを移行後も監査可能にする必要があるか。
10. 既存tests / scriptsの研究再現価値をどこまで維持するか。

L-01の推奨判断基準は、**標準運用への必要性ではなく、legacy dataの読み出し・研究再現性に本当に価値が残るか**である。

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

**Phase Lは開始可能である。**

---

## 15. Phase L開始時の原則

1. まずL-01でFragmentの処遇をdecision化する。
2. decision前にlegacy table / codeを削除しない。
3. migration 001/002を過去履歴として書き換えない。
4. schema除去が必要なら新migrationとして実施する。
5. existing DB migrationを先に検証し、fresh DBだけを見て判断しない。
6. canonical Source/EvidenceやEmbedding assetをlegacy cleanupへ巻き込まない。
7. structural moveとbehavior削除を可能な限り分離する。

次Task:

```text
L-01 [P0] Fragment table / code / CLIの移行方針を確定する
```
