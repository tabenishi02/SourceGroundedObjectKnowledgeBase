# Source Grounded Object Knowledge Base — Phase L Preparation

更新日: 2026-10-15

- Status: **In Progress**
- Phase: `Phase L — 旧Prototype移行・削除`
- Previous phase: `Phase K — SGOKB / UPDS連携試験` — Complete
- Previous closure: `docs/planning/PHASE_K_CLOSURE_AUDIT.md`
- Current task: `L-04 [P1] 旧benchmarkをarchive / deleteする`
- Working branch: `main`

---

## 1. Phase Lの目的

Phase Lでは、Object / Evidence / Version / Search / MCP中心の新standard workflowが成立した後もrepository内に残る旧Prototype資産を整理する。

目的は単純なコード削減ではない。

> **旧Prototypeから必要な設計資産・Sample Rawを保持しつつ、Fragment / Final Document中心の高コスト処理、不要なlegacy data、旧runtime DBを標準運用・active schema・active packageから退役させる。**

Phase L完了条件:

> 旧Prototypeの高コスト処理と不要なlegacy資産が通常運用に残存していない。

---

## 2. Task一覧

| Task | Priority | Status | 概要 |
|---|---|---|---|
| L-01 | P0 | Complete (Revised) | Fragment table / code / CLIを削除対象と確定した |
| L-02 | P0 | Complete | Final Document table / code / CLIを削除対象と確定し、canonical RendererをKeepした |
| L-03 | P1 | Complete | Prototype DBをdata migrationせず、003〜016からclean rebuildする設計を確定した |
| L-04 | P1 | Next | 旧benchmarkをarchive / deleteする |
| L-05 | P0 | Pending | 不要依存関係・compatibility layerを削除する |

推奨順序は`L-01 → L-02 → L-03 → L-04 → L-05`とする。

L-01/L-02で何を保持・削除するかを決める前にschemaやdependencyを変更しない。

L-01 / L-02 / L-03 decisions:

- `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`
- `docs/decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md`
- `docs/decisions/L03_CANONICAL_DB_CLEAN_REBUILD_POLICY.md`

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

一方、旧`source / snapshot / artifact / normalized_run / evidence`にもPrototype-era dataを格納できるtableが存在する。

```text
sources
snapshots
artifacts
normalized_runs
evidence
```

Source / Snapshot / Raw Artifact / Evidenceという**概念とcanonical実装はKeep**する。ただし2026-10-14のruntime auditで移行すべきproduction rowsが存在しないことを確認したため、現存Prototype DBのrowsはcanonical DBへ移送しない。`sample/` Raw Capture corpusは別資産として保持する。

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

L-03では001/002全体をactive bootstrapから除外すると確定したため、これらをfresh canonical DBへ生成しない。

### 4.3 runtime data調査によりclean rebuild可能と確認した

2026-10-14のlocal runtime調査で以下を確認した。

- `.local/sgokb.sqlite` は主要データtableが0件であり、本番正本を保持していない。
- `evaluation.sqlite` / `extraction-fix-verification.sqlite` / `upgrade.sqlite` は106件の`sample/` Raw corpusを使う評価用DBである。
- `i07-search-gold.sqlite` は`*.invalid` / `memory://`を用いたsynthetic benchmark DBである。
- `sgokb-capture-acceptance.sqlite` は`https://example.com/`を用いたacceptance DBである。
- 一時DBで現行schemaの新規生成に成功した。
- canonical DBへ引き継ぐ必要があるproduction Source / Evidence / Object Knowledgeは確認されなかった。

このためL-03では既存Prototype DBのdata migrationを行わず、**old runtime DBを削除してcanonical migration 003〜016からclean rebuildする**方針を確定した。

`sample/` Raw Capture corpusはDBとは独立した回帰試験資産として保持する。

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

## 9. L-02決定結果 — Complete

正本:

- `docs/decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md`

Decision:

> **旧Fragment-based Final Document機能はactive schema / active package / standard CLIから完全に退役させる。`documents` / `structured_documents`、`final.py`、Final専用Prompt、`legacy-generate` / `generate` alias、旧Document保存・参照APIをDelete対象とする。Phase Hのcanonical `ObjectMarkdownRenderer`はKeepする。**

主な確定事項:

1. `documents` / `structured_documents`をcanonical baselineへ持ち込まない。
2. 既存Final rowsをcanonical Object Knowledgeへmigrationしない。
3. 旧Final dataを恒久archiveしない。歴史的実装はGit履歴で確認する。
4. `src/sgokb/final.py` / `StructuredFinal`をactive packageから削除する。
5. `final_document.*` / `final_order.*` Promptを削除する。
6. `legacy_build_document` / `build_document` / `legacy_generate` / `generate` / `legacy_render_document`を削除対象とする。
7. legacy Repository document APIと`provenance document` CLIを削除対象とする。
8. canonical `rendering/markdown.py` / Markdown repository / renderer tests / design docはKeepする。
9. Final benchmark / old generated outputのarchive/deleteはL-04で歴史的価値を基準に判断する。
10. DB clean baseline反映はL-03、物理code / prompt / CLI cleanupはL-05で実施する。

---

## 10. L-03決定結果 — Complete

正本:

- `docs/decisions/L03_CANONICAL_DB_CLEAN_REBUILD_POLICY.md`

Decision:

> **Prototype DBからcanonical DBへのrow-level migrationは行わない。Prototype-only migration 001/002をactive bootstrapから除外し、canonical migration 003〜016を番号変更せずfresh DBへ適用する。既存Prototype DBを新runtimeでsilent利用せずfail-fastで拒否し、Sample Rawは保持する。**

主な確定事項:

1. `001_initial.sql` / `002_knowledge_capture.sql`をactive production bootstrapへ適用しない。
2. 001/002をclean schemaへ書き換えず、歴史的実装はGit historyで確認する。
3. 003〜016をcanonical active migration chainとして維持する。
4. migration番号は振り直さず、future migrationは017以降とする。
5. 003〜016を巨大な新001へ手作業でsquashしない。
6. fresh canonical DBの`schema_migrations`は3〜16を持ち、1/2を持たない。
7. 001/002由来のPrototype table / FTS / benchmark tableをfresh DBへ作成しない。
8. Prototype DBは`schema_migrations`の1/2を検出してfail-fastし、自動DROPやin-place upgradeを行わない。
9. DB cleanupとRaw cleanupを分離し、`sample/` Web Capture corpusを保持する。
10. runtime DBの物理削除前にL-04 benchmark salvage gateを通す。
11. clean bootstrap実装ではSQLite integrity / foreign key / canonical workflow smoke / Prototype DB negative testを要求する。
12. 001/002除去、fail-fast guard、legacy test/code cleanup、clean bootstrap regressionの実装はL-05へ引き継ぐ。

### 10.1 pre-production限定の例外

今回のclean rebuildは、2026-10-14のruntime auditで**production Source / Evidence / Object Knowledgeが0件であることを確認できたため採用できる一度限りのreset**である。

production data蓄積開始後は、D-06のruntime data保全方針および通常のmigration / backup / restore / integrity verificationを適用する。

---

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

L-04は同時に、evaluation / upgrade等のruntime DBを物理削除する前の**benchmark salvage gate**とする。保存価値がある情報がDBにしか存在しない場合は、DB全体ではなく必要最小限の結果・条件・manifestのみをarchiveする。

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

L-05ではL-01/L-02/L-03のDecisionを実装へ反映し、001/002のactive bootstrap除去、Prototype DB fail-fast guard、Fragment / Final code・Prompt・CLI・Repository surface、legacy tests / scriptsを整理する。

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
- [x] L-02で旧Final Document資産を削除しcanonical Markdown RendererをKeepする方針を確定した。
- [x] L-03でPrototype DB migrationを行わず003〜016からclean rebuildする方式を確定した。

**Phase Lは進行中であり、L-04へ移行可能である。**

---

## 15. Phase L実施原則

1. production移行対象データがないという2026-10-14のruntime auditをclean rebuildの前提とする。
2. 既存Prototype / evaluation DBをcanonical data sourceとしてmigrationしない。
3. `sample/` Raw corpusは保持し、DB削除と分離する。
4. clean rebuild後のactive DBにlegacy Fragment / Final / benchmark tableを残さない。
5. active bootstrapは003〜016とし、001/002を再導入しない。
6. Prototype DBを新runtimeでsilent利用せずfail-fastする。
7. canonical Source/Evidence、Object、Version、Search、MCPの現行semanticsは変更しない。
8. structural cleanupとbehavior cleanupを可能な限り分離する。
9. 「将来使うかもしれない」だけではlegacy runtime assetの保持理由にしない。

次Task:

```text
L-04 [P1] 旧benchmarkをarchive / deleteする
```
