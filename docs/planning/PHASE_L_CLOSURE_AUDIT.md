# Phase L Closure Audit

更新日: 2026-10-15

- Status: **Complete**
- Baseline: `c5c00f19c729ebeb426f153357d167811b1ca30a`
- Working branch: `main`
- Scope: L-01〜L-05 — 旧Prototype runtimeの撤去とcanonical-only bootstrap
- Next: `M-01 [P0] 新しいObject中心CLIを設計する`（未着手）

## 1. Completion

| Task | Status | 正本 / 結果 |
|---|---|---|
| L-01 | Complete | [Fragment Retirement](../decisions/L01_FRAGMENT_RETIREMENT_POLICY.md) |
| L-02 | Complete | [Final Document Retirement](../decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md) |
| L-03 | Complete | [Canonical DB Clean Rebuild](../decisions/L03_CANONICAL_DB_CLEAN_REBUILD_POLICY.md)、L-05で実装 |
| L-04 | Complete | [Legacy Benchmark Retirement](../decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md)、tracked inputs/scriptsとlocal旧DB削除済み |
| L-05 | Complete | [Legacy Compatibility Cleanup](../decisions/L05_LEGACY_COMPATIBILITY_CLEANUP_POLICY.md)、本監査で検証 |

L-01〜L-04のretirement方針をL-05で実装した。旧code / migrationの追加Archive copyは作らず、Git historyを歴史的実装の正本とする。既存`docs/archive/prototype-0.2/`の判断根拠は保持した。

## 2. Legacy runtime absence

以下をactive runtimeから除去した。

- Fragment / old Final / old benchmark / Prototype Search module・prompts・生成LLM provider。
- Prototype Application methodsとLLM/prompt/reranker field、旧Repository API・KnowledgeRepository継承。
- 旧Entity・embed/search・Fragment/Final/benchmark CLI、旧alias・`--legacy`・page_contexts専用context command。
- top-level ingestion re-export shimsとshim-only / deleted-preflight / legacy-only tests。
- migration001/002。canonical migration003〜016は番号・内容とも変更していない。

残存した共通primitive7件は`domain/primitives.py`へAST内容不変で移設した。`validate_vectors`とEmbedding providerは現行Search/Evidenceの用途があるためKeepした。`page_contexts`のDB APIはcanonical runtime利用がなく削除し、canonical ingestionのcontext解析実装は保持した。base / optional dependenciesは削減していない。

削除・退役path（24件、共通primitiveの移設元を含む）:

- `scripts/Use-Strata.ps1`
- `src/sgokb/benchmark.py`
- `src/sgokb/capture.py`
- `src/sgokb/context.py`
- `src/sgokb/domain/_prototype.py`
- `src/sgokb/extraction.py`
- `src/sgokb/final.py`
- `src/sgokb/importer.py`
- `src/sgokb/knowledge_repository.py`
- `src/sgokb/migrations/001_initial.sql`
- `src/sgokb/migrations/002_knowledge_capture.sql`
- `src/sgokb/prompts/final_document.md`
- `src/sgokb/prompts/final_document.schema.json`
- `src/sgokb/prompts/final_order.md`
- `src/sgokb/prompts/final_order.schema.json`
- `src/sgokb/prompts/fragment_extraction.md`
- `src/sgokb/prompts/fragment_extraction.schema.json`
- `src/sgokb/prompts/high_recall.md`
- `src/sgokb/prompts/high_recall.schema.json`
- `src/sgokb/search.py`
- `tests/test_ingestion_import_compatibility.py`
- `tests/test_speed_preflight.py`
- `tests/test_strata_speed_preflight.py`
- `tests/test_upgrade.py`

主な変更先: `application.py`、`repository.py`、`cli.py`、`providers.py`、`domain/__init__.py`、`domain/primitives.py`、Embeddingのprimitive import、canonical ingestion / schema / F-02 / F-03 / Versioning tests。

runtime stale-reference scanはERROR **0件**。廃止名はnegative tests・retirement Decisions・過去Phaseの記録だけに残る。`sgokb.context-builder.v1`の3ヒットは現行MCP context contractであり、旧`sgokb.context` importではない。F-02の保持方針は[Standard Pipeline Boundary](../design/STANDARD_PIPELINE_BOUNDARY.md)でHistoricalと現行境界を区別した。

## 3. Fresh DB / rejection audit

`tests/test_l05_canonical_bootstrap.py`でfresh一時DBとreopenを実行した。

```text
schema_migrations = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
integrity_check = ok
foreign_key_check = 0 violations
```

必須canonical table11件（Object/Version、Source/Locator/Snapshot、Raw、Normalization、Evidence、Search representations/spaces/embeddings）を確認した。001/002由来の26 table / virtual table名はすべて不存在だった。

applied versions `(1)` / `(2)` / `(1,2)` / `(2,3)`のsynthetic Prototype DBはすべて`Prototype DB rejected`でfail-fastした。ファイルbytes、sentinel content、stable ID、applied versionsは不変。silent migration / DROP / upgradeは行わず、拒否時の接続解放も確認した。

canonical migration009のbackfillとpre-E-04 canonical DBのVersion backfillも003以降のchainで回帰確認した。future migration番号は017以降とする。

## 4. Regression / known unrelated failure

| Check | Result |
|---|---|
| `python -m pytest -q` | **283 passed / 3 skipped / 1 known unrelated failure**, collection errors 0 |
| L-05 bootstrap / rejection | 5 passed（full suiteに含む） |
| 直接関連canonical regression | 57 passed |
| Versioning regression | 11 passed |
| Python compile / syntax | 成功 |
| `ruff check src tests scripts` | 既存38件。変更ファイルの違反0 |
| `git diff --check` | 成功 |

既知failureは`tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch`。testがSHA-256 mismatchを期待する一方、実装は先にfile size mismatchを返す。L-04で既知であり、当該testとPackage Transfer実装はbaselineから未変更。今回のL-05起因failureではなく、指示どおり修正・xfail化していない。

L-04時点の削除済みpreflight scriptに起因する2 collection errorsはobsolete tests削除で解消した。38 lint violationsは変更対象外fileの既存違反で、無関係な一括修正は行っていない。

canonical import/Raw integrity/Normalize/Evidence、Source↔Object association、Evidence Retrieval/Selection、Package/Result/Versioning/Markdown、Search Representation/Embedding/Hybrid/Similarity/Evidence Search、MCP adapter/tools/resources、UPDS K-02/K-03の現行testを保持し、上記full suiteでL-05起因failureがないことを確認した。MCP SDK transport/client試験はoptional `mcp` extra不足でskipされるため、実クライアント受入の再実施を意味しない。Vector側にもoptional dependencyによるskipがある。

## 5. Current Search benchmark

frozen `benchmark/search-quality-gold-v1.json`と現行3 benchmark scriptsを内容不変で保持した。

- real canonical DBへgoldをpopulateし、Lexical Searchを全24 queryで実行した。
- Lexical contractは**4/4 passed**（current/historical、temporal scope）。
- Lexical MRR = 0.166667、Recall@10 = 0.145833。Semantic中心のqueryも含むgoldのLexical-only測定であり、全体Search品質合格や実モデルの性能比較とは扱わない。
- Search gold / Vector benchmarkの`--help`は成功した。
- `sentence_transformers`未導入のため、実Embeddingモデル・ANN/Rerankerを使う完全benchmarkは未実行。model download / GPU推論 / 任意依存の導入は行っていない。この環境制約はL-04時点と同じである。

詳細結果はGit管理外`.local/l05/search-gold-lexical.json`に保存した。

## 6. Sample Raw preservation

sample Web Captureは**106件**。L-04の記録とL-05前後で全SHA-256が一致し、mtimeも不変。Raw Captureを変更・削除せず、production canonical dataを自動生成・移送していない。

削除後の旧DBを再Archiveせず、今回のbootstrap/gold検証は一時DBまたは`.local/l05/`の独立DBを使用した。

## 7. Phase M readiness

Phase LはComplete。Phase M / M-01のObject中心CLI設計へ移行可能だが、今回実装は開始していない。

Phase Mへ残すもの:

- 新Object中心CLI / command taxonomy / package conversionと通常操作フロー。
- 一枚のObject標準手順と運用上のerror / recovery説明。
- 廃止CLIを再導入しない前提での互換性・移行説明。

既知Package Transfer failure、既存lint、任意MCP/Embedding/Vector dependencyと実クライアント・モデルbenchmark未再実施は独立した残存制約である。Phase L完了はrepository全体のCIがすべてgreenであることやPhase Nの全面Acceptance完了を意味しない。
