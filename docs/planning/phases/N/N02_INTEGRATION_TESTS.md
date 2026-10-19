# N-02 Integration Test Plan / Implementation

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-02 [P0] Integration Testを追加する`
- Base: N-01 completed commit `fa031720aa1d52a752f87c2aa31a45446fc35a75`
- Branch: `phase-n/n02-integration-tests`
- Status: **Complete (2026-10-16)**

## 1. 目的

N-02では、個別Unit Testで確認済みのdomain contractを、canonical workflowをまたぐIntegrationとして固定する。

M-03のpublic CLI 1 Object happy pathを複製するのではなく、N-02 Task masterで要求された次のcross-domain chainを直接検証する。

```text
Capture → Evidence → Package
Result → Validate → Import → Version
Import → Object / Facet / Statement Representation → Embed → Vector Index → Search
same representation hash → Embedding / Vector reuse
Version change → current / historical scope isolation
MCP Adapter → KnowledgeReadApplication → Retrieval Core
```

Integration Testはdeterministic / offlineを基本とし、実Embeddingモデル・production Qdrant・外部AI品質はN-06/N-04へ分離する。

## 2. 追加test

`tests/test_n02_integration.py` に3本のIntegration Testを追加する。

### 2.1 Capture → Evidence → Package → Result → Version

`test_capture_evidence_package_result_validate_import_version_chain`

実Web Capture fixtureをcanonical ingestionへ投入し、以下を一続きで確認する。

```text
.webcapture.zip
→ Application.import_source_path
→ Application.process_source_snapshot
→ confirmed Source/Object association
→ Object Evidence Package build/stage/export
→ Object Result receive/validate/import
→ accepted current Version
```

追加で、Packageへ含まれたEvidenceが元のSource / Snapshot / Normalization Runへ遡れることを確認する。

### 2.2 Import → Representation → Embedding → Vector → Search

`test_import_to_embedding_index_search_reuses_representation_and_isolates_versions`

1回目のResult Import後に、

```text
SearchRepresentationBuilder
→ deterministic Embedding
→ Exact Vector Index rebuild
→ semantic Object Search
```

を実行する。

その後、同一Knowledge内容で2回目のVersion Importを行い、次を確認する。

- `base_version_id` が前Versionを指す。
- semantic contentが同一ならSearch Representation IDが再利用される。
- 既存RepresentationのEmbedding rowが再利用され、重複Embeddingを作らない。
- Vector pointはRepresentationではなくmembership単位なので、old/current Versionの双方を保持する。
- 通常Semantic Searchはcurrent Versionだけを返す。
- `version_id`明示filterではhistorical accepted Versionを検索できる。

Vector backendには`ExactVectorIndexAdapter`、Embeddingには3次元のdeterministic fixture providerを使用する。これはN-02 wiring検証用であり、ANN品質・実モデル品質の評価ではない。

### 2.3 MCP → Application → Retrieval Core

`test_mcp_adapter_reaches_real_application_and_retrieval_core`

fake Applicationではなく実`KnowledgeReadApplication`を`MCPReadAdapter`へ接続し、

- `get_object`
- `search_objects`（lexical）

をMCP Tool contract経由で呼び出す。

これにより、

```text
MCP Tool validation / serialization
→ KnowledgeReadApplication
→ Object reader / HybridObjectSearch
→ canonical Repository
```

の実chainを固定する。

MCP SDK / stdio transportそのものはM-03 / J-06で受入済みのため、N-02ではadapter/application/retrieval integrationへ焦点を置く。

## 3. 既存testとの役割分担

| Test | 主責務 |
|---|---|
| `test_canonical_ingestion.py` | Capture / Source / Evidenceのdomain correctness |
| `test_phase_g_roundtrip.py` | Package / Result routingの初期roundtrip |
| `test_result_validation.py` | Result Validationの詳細contract |
| `test_object_version_import.py` | Import atomicity / stale / duplicate / full Knowledge |
| `test_search_representation.py` | Representation単体contract / reuse |
| `test_hybrid_search.py` | Search / Vector / filter単体contract |
| `test_j01_*`〜`test_j06_*` | Application / MCP各boundary |
| `test_m03_standard_workflow.py` | public CLI / stdio MCPの1 Object受入 |
| `test_n02_integration.py` | 上記domain間のcanonical cross-domain wiring |

N-02は既存testを置き換えない。既存の詳細Unit Testを維持したまま、domain間の接続退行を検出する層を追加する。

## 4. Scope外

N-02では次を合否判定しない。

- 実Webデータ品質: N-03
- AI出力品質: N-04
- 処理性能: N-05
- production Embeddingモデル / ANN Vector品質: N-06
- process kill / disk full / backup restore等: N-07

## 5. Reference Workstation verification

ローカル環境で次を実行する。

```powershell
python -m pytest tests/test_n02_integration.py -q
python -m pytest -q
python -m ruff check tests/test_n02_integration.py
python -m ruff format --check tests/test_n02_integration.py

git diff --check
```

必須条件:

- N-02追加3 testがすべてPASS。
- full suite 0 failed。
- Ruff / format / `git diff --check`がPASS。
- testを通すためにproduction contractを弱めていない。
- optional external runtimeやnetworkに依存していない。

Failure時は単純なskip / xfailで隠さず、Integration wiringの欠陥かtest fixtureの誤りかを切り分ける。

## 6. Completion policy

Reference Workstation verificationが全PASSしたため、Task masterのN-02をCompleteへ変更した。

PASSに基づき次の更新を実施した。

- 本書を実測test結果へ更新する。
- `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md` のN-02をCompleteへ変更する。
- `docs/planning/PHASE_N_PREPARATION.md` を `N-02 Complete / N-03 Next` へ更新する。
- 次Taskを `N-03 [P0] real-data Vertical Slice` とする。

N-02完了後も、実データ・AI品質・performance・Vector quality・Failure/Recoveryは未評価であり、Phase N全体は継続する。


## 7. Reference Workstation実測結果 / completion decision

- 実行日: 2026-10-16 JST
- 環境: Windows 11 build 26300 / Python 3.10.6 / 通常の`.venv`、pytest 9.1.1 / Ruff 0.17.0。
- branch: `phase-n/n02-integration-tests` / PR #37（baseは`phase-n/n01-unit-test-update`）。
- 検証した実装: `f6e75517351c94d5ad7951b0537aca601f1ce1ca`に、下記のfixture/API使用修正とtest補強を適用。

通常venvのPython（`.venv/Scripts/python.exe`）で実行した。

| Command | 結果 |
|---|---|
| `python -m pytest tests/test_n02_integration.py -q` | **3 passed / 0 skipped / 0 failed**（修正後4.03秒） |
| `python -m pytest -q` | **307 passed / 3 skipped / 0 failed**（114.32s (0:01:54)） |
| `python -m ruff check tests/test_n02_integration.py` | **PASS** |
| `python -m ruff format --check tests/test_n02_integration.py` | **PASS** |
| `git diff --check` | **PASS** |

full suiteの3 skipは既存のoptional Qdrant runtime条件によるもの。今回skip / xfailやassertionの弱体化は行っていない。

### 確認結果

1. 実`.webcapture.zip`形式のsynthetic fixtureをimport / normalizeし、confirmed associationからPackage build/stage/export、Result receive/validate/import、accepted current Versionまで一続きでPASS。全included EvidenceのSource / Snapshot / Normalization RunへのProvenanceを確認した。
2. Import後のRepresentation → deterministic 3次元Embedding → Exact Vector Index → Semantic SearchがPASS。2回目の同一Knowledge importは前Versionをbaseとし、同じRepresentation IDとEmbedding rowsを再利用。Embedding providerのdocument生成件数は増えず、Vector point数はold/current双方のmembership数と一致。通常検索はcurrent、version_id filterはhistoricalを返した。
3. MCPReadAdapter → 実KnowledgeReadApplication → Retrieval Core → Repositoryのchainでget_object / lexical search_objectsがPASS。fake Applicationは使用していない。

### 発見した問題と修正

- **N-02 fixture / API使用方法の誤り**: Resultを`result-v1.json`等で作成していたため、3件ともreceive時に「Standard Result artifact must be named result.json」で失敗した。世代別directoryの`result.json`へ修正した。production Result intake contractは維持。
- 共通Result helperの要約が別Objectの内容だったため、Capture本文に一致するN02 Characterの文とPackage内Evidence参照に修正した。
- 既存test helperは保存rowの重複を防ぐ一方でproviderへ同じEmbeddingを再依頼していた。既存EmbeddingRepository APIで保存済みRepresentationを取得し、未生成分だけをproviderへ渡すようfixture処理を修正。provider呼出対象数とEmbedding rows不変を追加assertionで確認した。これはN-02 test構成の修正で、production自動更新pipeline全体の受入を意味しない。
- Provenance確認を先頭Evidenceだけから全included Evidenceへ補強。
- Ruff E501 2件とformat差異は同testファイルの整形で修正。

production implementation / migration / domain contractの変更は不要だった。修正後に対象3件とfull suiteを再実行し、全必須GateがPASSした。実Embeddingモデル、production Qdrant、外部AI、real-data品質、ANN品質、性能、recoveryは今回評価していない。

ローカル証跡（Git管理外）: `.local/n02/focused.log`（修正前）、`focused-final.log`、`full.log`。ログ・DB・実設定はcommit対象外。

**N-02 completion decision: Complete。次TaskはN-03 [P0] real-data Vertical Slice。Phase N全体は継続中。**
