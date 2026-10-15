# L-05 Legacy Compatibility Cleanup Policy

更新日: 2026-10-15

- Status: Accepted — implementation pending local regression
- Task: `L-05 [P0] 不要依存関係・compatibility layerを削除する`
- Baseline: `d17489ebc141579d27bb5cfab4483622393e2f56`
- Related:
  - `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`
  - `docs/decisions/L02_FINAL_DOCUMENT_RETIREMENT_POLICY.md`
  - `docs/decisions/L03_CANONICAL_DB_CLEAN_REBUILD_POLICY.md`
  - `docs/decisions/L04_LEGACY_BENCHMARK_RETIREMENT_POLICY.md`
  - `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
  - `docs/planning/PHASE_L_PREPARATION.md`

---

## 1. Decision

L-01〜L-04でDelete対象と確定した旧Prototype runtime surfaceをactive packageから削除する。

> **Fragment / old Final Document / old benchmark / local Generative LLM / Prototype DB compatibilityを標準runtimeから完全に外す。Embedding・canonical Source/Evidence・Object/Version・Search/Similarity・MCP・ObjectMarkdownRendererはKeepする。**

L-05では旧機能をresearch-only runtimeとして残さない。必要な旧実装はGit historyと`docs/archive/prototype-0.2/`で確認する。

CLIのObject中心再設計・package conversionはPhase Mの責務であり、L-05ではlegacy surfaceの削除に必要な最小変更だけを行う。

---

## 2. Delete — legacy standalone modules

active packageから次を削除する。

```text
src/sgokb/capture.py
src/sgokb/final.py
src/sgokb/benchmark.py
src/sgokb/search.py
```

`search.py`はPhase Iのcanonical `retrieval/hybrid_search.py`とは別のPrototype Search実装であり、old `search_items` / Fragment embedding pathへ依存する。

---

## 3. Delete — legacy prompts

次を削除する。

```text
src/sgokb/prompts/fragment_extraction.md
src/sgokb/prompts/fragment_extraction.schema.json
src/sgokb/prompts/high_recall.md
src/sgokb/prompts/high_recall.schema.json
src/sgokb/prompts/final_document.md
src/sgokb/prompts/final_document.schema.json
src/sgokb/prompts/final_order.md
src/sgokb/prompts/final_order.schema.json
```

次はcanonical Object Evidence Package / ChatGPT手動工程で使用するためKeepする。

```text
src/sgokb/prompts/object_analysis.md
```

---

## 4. Delete — Generative LLM provider surface

`src/sgokb/providers.py`から次を削除する。

```text
CompatibleLLM
StrataLLM
LMStudioLLM
llm_from_env
```

理由:

- standard Object Knowledge生成はPackage → ChatGPT手動工程 → Result Importであり、SGOKB runtime内で生成LLMを呼ばない。
- Fragment / Final / old benchmark以外に具体的な現行用途がない。
- L-04でlocal generative LLM benchmarkを退役済み。

次はSearch / Similarityで必要なためKeepする。

```text
CompatibleEmbedder
SentenceTransformerEmbedder
embedder_from_env
```

`httpx`はCompatible Embedding providerでも使用するためrequired dependencyから削除しない。

`scripts/Use-Strata.ps1`はGenerative LLM benchmark専用surfaceとして削除する。

---

## 5. Delete — Prototype ingestion/search/application compatibility

`Application`からPrototype-only use caseを削除する。

代表対象:

```text
import_path
process
prompt
call_llm
legacy_capture_fragments
legacy_build_document
legacy_fragment
capture_fragments
build_document
fragment
embed          # old search_items/embeddings path
search         # old src/sgokb/search.py path
legacy_generate
generate
legacy_render_document
```

canonicalでKeepする代表use case:

```text
import_source_path
process_source_snapshot
retrieve_object_evidence
select_object_evidence
list/set/clear/suggest_source_object_association
```

Embedding / Hybrid Object Searchの現行実装はPhase Iの`retrieval/*`およびread application側を正本とし、old `Application.embed/search`を互換目的で残さない。

---

## 6. Delete — Prototype Repository surface

`Repository` / legacy repository mixinから、001/002 schemaへ依存するPrototype APIを削除する。

代表対象:

```text
import_bundle
snapshot / snapshots
save_normalized / evidence
entity / add_entity / entities / relate / link_evidence
begin_ai / finish_ai / observe_ai
save_fragments / _insert_fragment_generation
start_extraction / extraction_job / assessments / record_batch / promote_extraction / coverage
related_fragments
candidates / lexical / save_embeddings / vector_rows
legacy provenance(fragment/document)
save_document / document
save_structured / structured_document
start_benchmark / benchmark_case / finish_benchmark
legacy status
```

`KnowledgeRepository`にlegacy処理しか残らない場合は継承自体を削除し、ファイルも削除する。

`page_contexts`関連helperは、repository-wide reference確認の結果canonical runtimeから未使用なら001/002とともに削除する。具体的な現行用途が確認できた場合だけ必要部分をcanonical storageへ移す。単に「将来使うかもしれない」ことは保持理由にしない。

---

## 7. Delete — active Prototype migrations and clean bootstrap

active migration directoryから次を削除する。

```text
src/sgokb/migrations/001_initial.sql
src/sgokb/migrations/002_knowledge_capture.sql
```

Git historyがhistorical migration archiveを担う。active treeへ別のlegacy migration copyを追加しない。

`Repository.migrate()`は次を満たすよう変更する。

1. `schema_migrations`を作成する。
2. 既存versionを確認する。
3. version `1`または`2`が存在するDBはPrototype DBとしてfail-fastする。
4. active migration `003`〜`016`だけを通常適用する。
5. fresh DBは`schema_migrations = 3..16`になる。
6. future migration番号は`017`以降を使用する。

003〜016をrenumber / squash / rewriteしない。

fresh DBで001/002由来のPrototype tableが生成されないことを自動試験する。

---

## 8. Delete — CLI compatibility surface

Phase MのCLI再設計は先取りしない。L-05では、削除済みschema/codeへ依存するcommand / option / aliasだけを削除する。

Delete対象:

```text
legacy-fragment
fragment alias
legacy-generate
generate alias
legacy-benchmark
benchmark alias
benchmark-score
coverage
legacy Entity command群
old embed/search command（Prototype search_items path）
legacy provenance fragment/document path
import/process の --legacy
status/snapshots の --legacy
legacy command alias normalization
Generative LLM provider initialization
```

`context` commandが001/002 `page_contexts`だけに依存しcanonical用途がない場合は削除する。

Keep対象:

```text
canonical import
canonical process
canonical status
canonical snapshots
association controls
canonical Evidence controls
separate package/result CLI
MCP runtime
```

L-05で新しいObject CLIを設計しない。Object中心CLIはPhase Mで実施する。

---

## 9. Delete — top-level compatibility shims

canonical pathへの移行が完了していることをrepository-wide grepで確認後、次のre-export shimを削除する。

```text
src/sgokb/importer.py
src/sgokb/extraction.py
src/sgokb/context.py
```

対応するshim-only testも削除する。

```text
tests/test_ingestion_import_compatibility.py
```

production/current testで旧path importが残っている場合はcanonical `sgokb.ingestion.*`へ置換してからshimを削除する。

---

## 10. Domain `_prototype.py` boundary

`src/sgokb/domain/_prototype.py`はファイル名だけを理由に一括削除しない。

現在ここには、legacy-only contractとcanonicalでも利用される共通primitiveが混在している。

legacy-only候補:

```text
LLM
old SearchFilter
old EmbeddingSpace
old VectorIndex
old Reranker
validate_fragments
```

Keep / canonical移設候補:

```text
Bundle
Block
digest
json_text
now
uid
validate_vectors   # 現行Embeddingでreferenceが残る場合
```

repository-wide referenceを確認し、legacy-only symbolは削除する。共通primitiveは必要ならcanonical moduleへ移すが、L-05を大規模domain再設計へ拡張しない。

`domain/__init__.py`の「prototype public import surfaceをpreserveする」目的のexportは削除し、現在必要なcontractだけを公開する。

---

## 11. Tests cleanup

Delete対象の代表:

```text
tests/test_speed_preflight.py
tests/test_strata_speed_preflight.py
tests/test_ingestion_import_compatibility.py
```

`tests/test_core.py` / `tests/test_upgrade.py`はPrototype Fragment / Final / benchmark / old Search / old migration試験が大部分を占めるため、current canonical regressionとして具体的価値があるcaseだけをcanonical testへ移すか保持し、legacy-only caseは削除する。

`tests/test_providers.py`はGenerative LLM provider試験を削除し、Embedding provider試験だけを残す。

`tests/test_f02_standard_pipeline.py`はlegacy availability / legacy table存在を確認するassertionを削除し、fresh canonical DBでlegacy table/commandが存在しないことを検証する方向へ更新する。

L-04後に発生しているdeleted preflight script参照による2 collection errorはL-05で解消する。

---

## 12. Required fresh-DB regression

L-05完了判定では、一時fresh SQLite DBを作成して少なくとも次を確認する。

### migrations

```text
schema_migrations == 3..16
1 / 2 は存在しない
```

### canonical schema

少なくとも次が存在することを確認する。

```text
objects
object_versions
source_records
source_locators
source_snapshots
raw_artifacts
normalization_runs
evidence_records
search_representations
search_embedding_spaces
search_representation_embeddings
```

### legacy schema

001/002由来のFragment / Final / benchmark / Prototype Source系tableが存在しないことを確認する。

### fail-fast

version 1または2を持つsynthetic Prototype DBを開いた場合、silent migration / DROP / upgradeせず明示errorにする。

---

## 13. Current capabilities that must not regress

L-05 cleanup後も次を維持する。

- Web Capture import / canonical Source resolution
- Snapshot / Raw Artifact保存
- Normalize → Evidence
- Source↔Object association controls
- Object Evidence Retrieval / Selection
- Package build / export contract
- Result receipt / validation / import / Versioning
- ObjectMarkdownRenderer
- Search Representation / Embedding
- Hybrid Object Search / Similarity / Evidence Search
- MCP read access
- UPDS integration contract
- current Search quality benchmark
- Sample Raw corpus

---

## 14. Dependency policy

現行`pyproject.toml`にはGenerative LLM専用SDK dependencyは存在しないため、LLM cleanupを理由にbase dependencyを機械的に削除しない。

Keep:

```text
beautifulsoup4
httpx
jsonschema
mcp optional dependency
Embedding / Vector optional dependencies
```

実際に未使用となったdependencyがある場合のみ、repository-wide importとtestを根拠に削除する。

---

## 15. Acceptance criteria

L-05完了条件:

- [ ] Fragment runtime module / prompt / Application / Repository / CLI surfaceがactive treeにない。
- [ ] old Final runtime module / prompt / Application / Repository / CLI surfaceがactive treeにない。
- [ ] old benchmark runtime module / CLI / Repository surfaceがactive treeにない。
- [ ] Generative LLM provider surfaceと`Use-Strata.ps1`がactive treeにない。
- [ ] 001/002がactive migration chainにない。
- [ ] fresh DBが003〜016だけから構築できる。
- [ ] Prototype DB version 1/2をfail-fastで拒否する。
- [ ] old top-level ingestion compatibility shimを必要性なしに残していない。
- [ ] deleted scriptを参照するobsolete testsがない。
- [ ] Embedding provider / canonical Search / MCPを維持している。
- [ ] `git diff --check`が成功する。
- [ ] Ruff結果を記録する。
- [ ] full pytest結果を記録し、L-05起因failure 0件である。
- [ ] current Search benchmark regressionを実行するか、実行不能理由を明示する。
- [ ] Sample Rawを変更していない。

---

## 16. Phase boundary

L-05ではcleanupのために必要な最小限のCLI修正だけを行う。

次Phaseの責務を先取りしない。

```text
Phase M: Object中心CLI / 操作フロー再設計
Phase N: 新ドメインの全面Test / Acceptance
Phase O: README / Release / final Git cleanup
```

L-05完了後、Phase L closure auditを作成してPhase Mへ移行可能か確認する。
