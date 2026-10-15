# L-04 Legacy Benchmark Retirement Policy

更新日: 2026-10-15

- Status: Accepted
- Task: `L-04 [P1] 旧benchmarkをarchive / deleteする`
- Baseline: `9e71ac58f52726ffe2d4d7a094f8c9fa290b39f4`
- Related:
  - `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`
  - `docs/decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md`
  - `docs/decisions/L03_CANONICAL_DB_CLEAN_REBUILD_POLICY.md`
  - `docs/planning/PHASE_L_PREPARATION.md`
  - `docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md`

---

## 1. Decision

旧PrototypeのFragment / Final Document / local generative LLM比較benchmarkは、現行SGOKBのAcceptance基準から退役させる。

> **現行Object / Evidence / Search / Similarityに直接利用するbenchmarkだけをactive treeにKeepする。旧Fragment / Final用manifest・example label・evaluation/preflight scriptはDeleteする。歴史的結果は既存`docs/archive/prototype-0.2/`文書をArchive正本とし、runtime SQLite DBや個別run rowを追加archiveしない。**

L-01/L-02でFragment / Final自体がDelete対象となり、L-03でPrototype DBをcanonical data sourceとしてmigrationしないことを確定したため、旧benchmark runtimeを維持する理由はない。

---

## 2. Keep — current benchmark

次は現行SGOKBのSearch / Similarity / Vector品質を検証するactive benchmarkとして保持する。

```text
benchmark/search-quality-gold-v1.json
scripts/run_search_quality_gold.py
scripts/run_vector_backend_benchmark.py
scripts/run_search_gold_reranker_benchmark.py
docs/design/SEARCH_QUALITY_GOLD_BACKEND_BENCHMARK.md
```

これらはFragment / Final Documentを評価対象とせず、canonical Object Knowledge / Evidence / Search Representationを対象とする。

関連するPhase IのEmbedding / Vector / Similarity設計・結果文書も現行資産としてKeepする。

---

## 3. Archive — historical result only

旧Prototype benchmarkの歴史的価値は、すでに`docs/archive/prototype-0.2/`へ保存されている文書で十分と判断する。

代表的な既存Archive:

```text
docs/archive/prototype-0.2/AI_CAPABILITY_BENCHMARK.md
docs/archive/prototype-0.2/MODEL_COMPARISON_PLAN.md
docs/archive/prototype-0.2/MODEL_SPEED_PREFLIGHT_PLAN.md
docs/archive/prototype-0.2/MODEL_SPEED_PREFLIGHT_RESULTS.md
docs/archive/prototype-0.2/OPERATION_TIME_ESTIMATE.md
docs/archive/prototype-0.2/PROCESSING_BOTTLENECK_REVIEW.md
docs/archive/prototype-0.2/KNOWLEDGE_PIPELINE_EFFICIENCY_REDESIGN.md
```

Archiveの目的は過去の判断根拠を確認できることであり、旧runtimeを再実行可能に保つことではない。

そのため次は新たにArchiveしない。

- old benchmark SQLite DB本体
- Fragment / Finalの個別run rows
- AI runの全Prompt / output row
- 旧benchmark manifestのactive copy
- example human-label file
- 旧benchmark実行script一式

必要な旧実装はGit historyから復元できる。

---

## 4. Delete — tracked legacy benchmark inputs

active treeから次を削除する。

```text
benchmark/sample-v1.json
benchmark/configurations.example.json
benchmark/labels.example.json
```

理由:

- Fragment / Retrieval / Finalを一括比較するPrototype manifestである。
- current Search goldとは別資産である。
- L-01/L-02で退役したworkflowを前提とする。
- 歴史確認にはGit historyと既存Archive文書で足りる。

---

## 5. Delete — standalone legacy benchmark scripts

active treeから次を削除する。

```text
scripts/export_upgrade_review.py
scripts/run_evaluation.py
scripts/run_speed_preflight.py
scripts/run_strata_preflight.py
scripts/run_strata_speed_preflight.py
scripts/run_upgrade_evaluation.py
```

これらは旧Prototype Source/Entity/Fragment/Final、High Recall Prompt、local generative LLM比較、または`upgrade.sqlite`を前提とする実験用scriptであり、canonical standard workflowの運用scriptではない。

`scripts/inventory_samples.py`はSample Raw corpusの非破壊inventory用途を持つためKeepする。

---

## 6. L-05へ引き渡すruntime compatibility cleanup

次はbenchmark資産ではあるが、CLI / provider / Repository compatibilityと結合しているためL-04単独で削除しない。

```text
src/sgokb/benchmark.py
CLI: legacy-benchmark / benchmark alias / benchmark-score
Repository: benchmark_runs / benchmark_cases accessors
migration 002: benchmark_runs / benchmark_cases
scripts/Use-Strata.ps1
legacy Generative LLM provider surface
legacy benchmark tests / compatibility assertions
```

これらはL-05でFragment / Final / generative provider / compatibility layerと一緒に削除し、full regressionを実行する。

`Use-Strata.ps1`は旧local generative LLM benchmark用途以外の現行standard use caseがない場合にDeleteする。

---

## 7. Runtime SQLite benchmark data

2026-10-14のruntime auditで確認した次のDBはproduction canonical dataではない。

```text
.local/sgokb.sqlite
.local/evaluation.sqlite
.local/extraction-fix-verification.sqlite
.local/upgrade.sqlite
.local/sgokb-capture-acceptance.sqlite
.local/i07-search-gold.sqlite
.local/i03_backend_work/sqlite_vec.sqlite
.local/i03_backend_work/sqlite_vector.sqlite
sample/配下のevaluation / probe SQLite DB
```

L-04では、これらのDB全体または個別rowを歴史資料として保存する具体的用途はないと判断する。

理由:

1. production Knowledgeを保持していない。
2. 旧Fragment / Final評価結果の主要な判断根拠は既存Archive文書へ残っている。
3. current Search benchmarkはtracked gold / harnessから再生成可能である。
4. `sample/` Raw Capture corpus自体は別資産として保持する。
5. 将来利用する可能性だけを理由に数百MB〜GB級DBを保全しない。

したがって、local checkoutではこれらSQLite DBおよび対応する`-wal` / `-shm`を削除してよい。

ただし、`sample/**/*.webcapture.zip`は削除しない。

---

## 8. `benchmark/README.md` policy

active `benchmark/README.md`はcurrent Search benchmarkのみを説明する文書へ縮小する。

旧Fragment / Final / model comparisonの実行手順、`upgrade.sqlite`、`legacy-benchmark`、`benchmark-score`の説明は削除する。

歴史資料への参照だけを残し、active benchmarkとPrototype benchmarkを混在させない。

---

## 9. Acceptance criteria

L-04完了条件:

- [x] current Search quality goldをKeep対象として明示した。
- [x] current Vector backend / Reranker benchmarkをKeep対象として明示した。
- [x] 旧benchmark結果のArchive正本を既存Prototype文書へ限定した。
- [x] old benchmark DB全体をArchiveしないと決定した。
- [x] old Fragment / Final manifest・example labelsをDelete対象とした。
- [x] standalone legacy evaluation / preflight scriptsをDelete対象とした。
- [x] Sample Raw corpusをKeepした。
- [x] runtime-coupled benchmark code / CLI cleanupをL-05へ分離した。

ローカルignored DBの物理削除と、L-05へ跨るruntime code削除はlocal checkout上で実行・検証する。

---

## 10. Next task

```text
L-05 [P0] 不要依存関係・compatibility layerを削除する
```

L-05ではL-01〜L-04でDelete対象と確定したFragment / Final / benchmark / generative LLM / compatibility surfaceをactive packageから削除し、canonical workflow regressionを行う。
