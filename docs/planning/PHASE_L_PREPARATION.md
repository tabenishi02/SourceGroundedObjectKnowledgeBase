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

> **旧Prototypeから必要なcanonical資産を安全に移行し、Fragment / Final Document中心の高コスト処理と不要なlegacy dataを標準運用・active schema・active packageから退役させる。**

Phase L完了条件:

> 旧Prototypeの高コスト処理と不要なlegacy資産が通常運用に残存していない。

---

## 2. Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| L-01 | P0 | Complete (Revised) | Fragment table / code / CLIを削除対象と確定した |
| L-02 | P0 | Next | Final Document table / code / CLIの処遇を確定する |
| L-03 | P1 | Pending | 既存Prototype DBを破棄しcanonical DBをclean rebuildする |
| L-04 | P1 | Pending | 旧benchmarkをarchive / deleteする |
| L-05 | P0 | Pending | 不要依存関係・compatibility layerを削除する |

推奨順序は`L-01 → L-02 → L-03 → L-04 → L-05`とする。

L-01/L-02で何を保持・削除するかを決める前にschemaやdependencyを変更しない。

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

Source / Snapshot / Raw Artifact / Evidence等は削除対象と即断せず、L-03でcanonical Source / Evidence schemaへの移送可否を評価する。

Fragment関連tableはL-01で削除対象と確定した。

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

Fragment専用ledgerは削除候補とし、`page_contexts` / `ai_observations`等は他のcanonical用途が存在するか個別評価する。

### 4.3 runtime data調査によりclean rebuild可能と確認した

2026-10-14のlocal runtime調査で以下を確認した。

- `.local/sgokb.sqlite` は主要データtableが0件であり、本番正本を保持していない。
- `evaluation.sqlite` / `extraction-fix-verification.sqlite` / `upgrade.sqlite` は106件の`sample/` Raw corpusを使う評価用DBである。
- `i07-search-gold.sqlite` は`*.invalid` / `memory://`を用いたsynthetic benchmark DBである。
- `sgokb-capture-acceptance.sqlite` は`https://example.com/`を用いたacceptance DBである。
- 一時DBで現行schemaの新規生成に成功した。
- canonical DBへ引き継ぐ必要があるproduction Source / Evidence / Object Knowledgeは確認されなかった。

このためL-03では既存Prototype DBのdata migrationを行わず、**old runtime DBを削除してcanonical baselineからclean rebuildする**。

`sample/` Raw Capture corpusはDBとは独立した回帰試験資産として保持する。

`001_initial.sql` / `002_knowledge_capture.sql`を含む既存migration chainをそのままfresh DBへ適用するとlegacy tableが再生成されるため、L-03でactive bootstrap / canonical baselineを整理する。---

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

L-01の改定後Decisionでは次を確定した。

- Fragment関連table / rowsをactive DBから削除する。
- 既存Fragment dataを恒久read-only archiveとして保持しない。
- Fragment生成・参照write/read pathを削除する。
- `capture.py`、Fragment prompt、Fragment validation、Application / RepositoryのFragment処理をactive packageから削除する。
- `legacy-fragment`と`fragment` aliasを削除する。
- research-only runtimeは維持しない。
- `search_items(kind='fragment')`とFragment embeddingを削除する。
- Fragmentをaccepted Object Knowledgeへ自動変換しない。
- 歴史的code / promptはGit履歴で確認する。

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
Generative LLM provider → Final / benchmark等の残存用途を確認後Retire候補
```

L-01ではFragment generationのためだけにGenerative LLM runtimeを維持しないことを確定した。

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

L-01でFragment系method / CLIはDelete対象と確定した。CLI package conversion自体はPhase Mの責務であるため、L-05で実削除する際もPhase Mとの境界を維持する。

---

## 8. L-01決定結果 — Complete (Revised)

正本:

- `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`

Decision:

> **Fragment関連資産は、現時点で必要な具体的用途が存在しないため、active DB・active package・standard CLIから完全に削除する。既存Fragment rowsをread-only archiveとして恒久保持しない。必要な歴史的実装情報はGit履歴で確認する。**

主な確定事項:

1. `fragments / fragment_runs / fragment_evidence`を削除する。
2. Fragment専用補助tableも他用途がなければ削除する。
3. Fragmentからaccepted Object Knowledgeを自動生成しない。
4. Fragment write/read/search pathを削除する。
5. `capture.py`、Fragment prompt、Fragment generation / validation methodを削除する。
6. `legacy-fragment`と`fragment` aliasを削除する。
7. Fragment search representation / embeddingを削除する。
8. Fragment rowsを外部archiveすることを必須としない。
9. research-only runtimeは維持しない。
10. 既存DBのdata migrationは行わず、canonical baselineからclean rebuildする。
11. DB clean rebuild設計はL-03、code / dependency cleanupはL-05へ分離する。

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
- 過去生成Markdownの保持価値

L-01によりFragment自体は削除前提となったため、L-02で旧Final生成を残す場合もFragment保持を前提にしてはならない。

---

## 10. L-03 clean rebuild準備

L-03は既存Prototype DBをcanonical DBへ変換するdata migration Taskではない。

採用方針:

```text
existing Prototype / evaluation DB
  -> production移行対象なしを確認
  -> delete

Sample Raw corpus
  -> keep

canonical baseline
  -> create new empty DB
  -> run canonical workflow tests
```

L-03で決めること:

- 削除対象runtime DBの最終inventory。
- active canonical schema baseline / bootstrap方式。
- 001/002等のhistorical Prototype migrationをactive bootstrapからどう分離するか。
- Fragment / Final / benchmark等のlegacy tableがfresh DBへ生成されないことの検証。
- clean DBからSource / Evidence / Object / Version / Search / MCPが正常に動作することの検証。
- Sample Rawを保持し、必要なtestでisolated DBへ再importする手順。

既存DB row count / legacy ID / Fragment provenanceの移送・整合性検証は不要とする。---

## 11. L-04 benchmark archive境界

Keep対象:

- current Object Search quality gold
- Embedding / Vector backend評価
- Phase I Search / Similarity regression

Retire/archive/delete対象:

- fragments/sec
- fragments per evidence
- Final Document生成速度
- High Recall extraction model比較をcurrent acceptance基準とすること

既存`docs/archive/prototype-0.2/`は歴史資料保存先として利用できるが、不要なbenchmark dataをすべて保存する必要はない。

L-04では「歴史資料として具体的価値があるか」を基準にarchive / deleteを判断する。

---

## 12. L-05 cleanup gate

不要dependency / shim / aliasを削除する前に次を満たす。

- production codeが旧shimをimportしていない。
- current tests / scriptsがcanonical pathへ移行済み。
- standard CLI / package entrypointがlegacy codeを必要としない。
- L-01/L-02で削除対象が確定済み。
- clean rebuild / canonical bootstrap方針がL-03で確定済み。
- benchmark archive/delete方針がL-04で確定済み。
- full testまたは既知failureを明示したfocused regressionが通る。

Embedding dependencyは削除対象ではない。

Fragment generation code / prompt / CLI / read-write pathはL-01でDelete対象と確定済みだが、L-03 migration実装に必要な一時helperを先に削除しない。

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
- [x] L-01でFragment資産を削除する方針を確定した。

**Phase Lは進行中であり、L-02へ移行可能である。**

---

## 15. Phase L実施原則

1. production移行対象データがないという2026-10-14のruntime auditをL-03の前提とする。
2. 既存Prototype / evaluation DBをcanonical data sourceとしてmigrationしない。
3. `sample/` Raw corpusは保持し、DB削除と分離する。
4. clean rebuild後のactive DBにlegacy Fragment / Final / benchmark tableを残さない。
5. historical migrationを保持する場合も、active canonical bootstrapへ不要なlegacy schemaを再導入しない。
6. canonical Source/Evidence、Object、Version、Search、MCPの現行semanticsは変更しない。
7. structural cleanupとbehavior cleanupを可能な限り分離する。
8. 「将来使うかもしれない」だけではlegacy runtime assetの保持理由にしない。

次Task:

```text
L-02 [P0] Final Document table / code / CLIの移行方針を確定する
```
