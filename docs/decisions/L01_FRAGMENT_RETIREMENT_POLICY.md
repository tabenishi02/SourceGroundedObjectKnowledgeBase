# L-01 Fragment Retirement Policy

更新日: 2026-10-14

Status: Accepted — Revised

対象Task: `L-01 [P0] Fragment table / code / CLIの移行方針を確定する`

Baseline: `15d35013591bd70563e69a2672d716d44b7684d9`

関連正本:

- `docs/planning/PHASE_L_PREPARATION.md`
- `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
- `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
- `docs/design/STANDARD_PIPELINE_BOUNDARY.md`
- `src/sgokb/migrations/001_initial.sql`
- `src/sgokb/migrations/002_knowledge_capture.sql`

---

## 1. Revised Decision

L-01の初回Decisionでは既存Fragment rowsのread-only保全、その後の改定ではactive DBからの削除を方針化した。

2026-10-14に実runtime dataを追加調査した結果、さらに前提を単純化できることを確認した。

- 既定DB `.local/sgokb.sqlite` は業務・本番データを保持しておらず、主要tableは0件だった。
- 大容量のPrototype DBは `sample/` corpus、evaluation、upgrade、acceptance、synthetic search gold等の試験用途だった。
- canonical DBは現行schemaから新規生成できることを一時DBで確認した。
- 現時点で移行すべきproduction Source / Evidence / Object Knowledgeは存在しない。
- `sample/` のRaw Capture corpusはExtractor回帰試験等に価値があるため保持する。

したがってL-01の最終方針を次のように改定する。

> **既存Prototype/runtime DBの内容はcanonical DBへデータmigrationせず、旧DBを破棄してcanonical schemaからclean rebuildする。Fragment関連table / row / search item / embeddingは新DBへ持ち込まない。Sample RawはDBとは独立した試験corpusとして保持する。**

研究・履歴確認はGit履歴と設計資料で行い、不要なlegacy runtime dataを保全理由なく維持しない。

---

## 2. Fragment資産の最終分類

| Asset | Final Decision |
|---|---|
| `fragment_runs` | Delete |
| `fragments` | Delete |
| `fragment_evidence` | Delete |
| Fragment専用`extraction_jobs` / `extraction_batches` / `evidence_assessments`等 | Delete（他用途がないもの） |
| Fragment generation write path | Delete |
| Fragment read path | Delete |
| `capture.py` | Delete from active package |
| `validate_fragments` | Delete |
| Fragment prompt群 | Delete from active package data |
| `legacy-fragment` CLI | Delete |
| `fragment` alias | Delete |
| `search_items(kind='fragment')` | Delete |
| Fragment由来embedding | Delete |
| Fragment専用tests / scripts | Delete from active suite |
| Fragment research runtime | Do not preserve |
| Historical implementation | Git historyのみを正とする |

---

## 3. 削除してよい理由

### 3.1 canonical workflowがFragment非依存で成立している

標準Pipelineは次で完結する。

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

Fragmentはこの経路に存在しない。

### 3.2 SearchがFragmentを必要としない

現行Searchはcanonical Evidence / Object / Facet / Statement等を対象として成立している。

旧Prototypeの`search_items(kind='fragment')`とFragment embeddingを新Searchへ持ち込む必要はない。

### 3.3 MCP / SGOKB-UPDS連携もFragment非依存である

MCP read contractとUPDS連携はaccepted Object Knowledgeを参照し、Fragmentを中間表現として必要としない。

### 3.4 Fragmentはcanonical Knowledgeではない

旧Fragmentは過去の生成LLM処理の出力であり、現在のObject Result validation / Versioningを経ていない。

そのため、Fragmentを将来利用する可能性を理由にlive DBへ残す価値は低い。

### 3.5 「監査できるかもしれない」だけでは保持理由にしない

初回DecisionではFragment provenanceを監査用途として残すことを理由にread-only保全した。

しかし現時点では、Fragment監査を必要とする運用・受入要件・障害対応要件は存在しない。

不要なlegacy schemaを恒久維持すると、次のコストが発生する。

- schema理解コスト
- migration複雑化
- Repository APIの残存
- CLI / test compatibility維持
- 誤って旧workflowを利用する余地
- 「どれが正本か」の認知負荷

よって、具体的な現在用途がないlegacy dataは削除する。

---

## 4. DB削除・clean rebuild方針

### 4.1 existing DBのデータmigrationを行わない

現時点のruntime inventoryでは、canonical DBへ引き継ぐ必要があるproduction dataは確認されなかった。

したがってL-03では、旧Prototype DBについて次のmapping/importを行わない。

```text
legacy sources / snapshots / evidence / fragments / documents
  -> canonical tables
```

旧DBはmigration sourceではなく、削除可能なdevelopment / evaluation runtime artifactとして扱う。

### 4.2 clean canonical DBを新規構築する

L-03の最終状態は次とする。

```text
old runtime DBs
  -> delete

canonical schema baseline
  -> create new empty DB
  -> canonical Source / Evidence / Object / Version / Search tables only
```

新DBにはFragment table、Fragment search representation、Fragment embedding、Fragment専用ledgerを作成しない。

### 4.3 historical migration compatibilityを要件としない

`001_initial.sql` / `002_knowledge_capture.sql`はPrototype schemaを生成するため、単純に001から全migrationを再実行するだけではclean rebuildにならない。

production dataのupgrade compatibilityが不要であることを今回確認したため、L-03では**active migration chain / canonical baselineを整理し、fresh DBの最終schemaからlegacy Prototype tableを排除する**。

過去migrationの履歴情報を残す場合も、active DB bootstrapがそれらへ依存する必要はない。具体的なbaseline化・archive方法はL-03で確定する。

### 4.4 Sample Rawは保持する

`sample/`配下のWeb Capture BundleはDBとは別資産であり、Extractor / ingestion / regression試験に利用価値があるため削除しない。

Sample Rawをcanonical production DBへ常時importしておく必要もない。試験時にisolated DBへ必要分だけimportする。

### 4.5 Fragment専用補助資産も新DBへ持ち込まない

Fragment / High Recall workflow専用で、canonical用途がないtableはclean baselineから除外する。

例:

```text
fragment_runs
fragments
fragment_evidence
extraction_jobs
extraction_batches
evidence_assessments
entity_candidates
```

Final Document / benchmark関連tableはL-02 / L-04のDecisionに従って同様に整理する。

---

## 5. FragmentからObject Knowledgeを移行しない

Fragmentはcanonical migration sourceとして利用しない。

禁止:

```text
legacy Fragment
  → automatic synthesis / conversion
  → accepted Object Knowledge Version
```

必要なKnowledgeはcanonical Evidence Package / Object Result workflowを通して作成する。

したがってFragment削除によってObject Knowledgeの欠損補完処理を自動実行しない。

---

## 6. Code削除方針

### 6.1 `capture.py`

`src/sgokb/capture.py`はactive packageから削除する。

`_legacy/`へ移して実行可能状態を維持する方式は採用しない。

### 6.2 Application compatibility methods

以下は削除対象とする。

```text
legacy_capture_fragments()
capture_fragments()
legacy_fragment()
fragment()
```

### 6.3 Fragment persistence / search methods

Repository / `knowledge_repository.py`等の以下を削除する。

```text
Fragment write
Fragment promotion
Fragment lookup
Fragment-only search
Fragment provenance lookup
```

ただしL-03のruntime inventory / clean rebuild検証で旧tableを確認する必要がある場合、一時的helperを検証完了までのみ保持してよい。既存rowsをcanonicalへ移送するdata migration helperとして恒久化しない。

### 6.4 `validate_fragments`

`domain/_prototype.py::validate_fragments`は削除する。

canonical Object Result validationへ流用しない。

---

## 7. Prompt削除方針

Fragment generation専用promptはactive package dataから削除する。

対象例:

```text
fragment_extraction.*
high_recall.*
```

新Object Result promptへrenameして再利用しない。

必要になった場合はGit履歴から当時の実装と組み合わせて参照する。

---

## 8. CLI削除方針

次をstandard CLIから削除する。

```text
legacy-fragment
fragment
```

read-only inspection commandも残さない。

L-03の削除対象inventory確認でFragment rowの確認が必要な場合は、一時的なSQL / inspection testを用いる。

Phase MはFragment commandを再導入しない。

---

## 9. Search / Embedding削除方針

旧`search_items(kind='fragment')`と、それに紐づくFragment embeddingは削除する。

- canonical Searchへ移送しない。
- new embeddingを生成しない。
- clean rebuild後のactive DBには存在させない。
- canonical Evidence / Object / Facet / Statement representationへ変換しない。

Embedding provider abstraction自体は現行Searchで必要なので保持する。

---

## 10. Research reproducibility方針

Fragment runtimeやFragment DB dataをlive systemに残して研究再現性を維持する方式は採用しない。

研究・履歴確認は次で行う。

1. Git履歴で旧code / prompt / tests / scriptsを確認する。
2. 必要であればbaseline commitから隔離環境を再構成する。
3. L-04ではcurrent repositoryに残す価値があるbenchmark資料だけを選別する。
4. 実DB内の過去Fragment rows自体は研究再現性の必須資産とはみなさない。

つまり、**コード履歴はGitに残すが、不要なruntime dataをDBに残さない。**

---

## 11. Tests / scripts方針

Fragment生成・Fragment永続化・Fragment検索を検証するtestはactive acceptance suiteから削除する。

分類:

- canonical Evidence / Search / Object workflowの回帰test: Keep
- Fragment生成test: Delete
- Fragment persistence/search test: Delete
- Fragment CLI test: Delete
- clean rebuild schema / bootstrap test: L-03で追加
- Fragment benchmark / speed script: L-04でarchiveまたはDeleteを判断

L-05でcodeを削除する前にactive test / scriptからFragment import依存を除去する。

---

## 12. 後続Taskへの拘束条件

### L-02

Final Documentの処遇を決める際、Fragmentを保持理由にしてはならない。

Fragmentは削除前提である。

### L-03

既存Prototype DBの**データmigrationは行わずclean rebuildを採用する**。

- production移行対象データは現時点で存在しない。
- old runtime DBは削除対象とする。
- Sample Raw corpusは保持する。
- canonical baselineから新しい空DBを構築する。
- Fragment table / Fragment search item / Fragment embeddingを新DBへ作成しない。
- legacy Prototype tableを再生成しないようactive migration chain / bootstrapを整理する。
- clean rebuild後にcanonical Source / Evidence / Object / Version / Search / MCP workflowが成立することをtestする。

### L-04

Fragment benchmarkはcurrent KPIから外す。

歴史資料として明確な価値があるものだけをarchiveし、それ以外は削除可能とする。

### L-05

以下を実際に削除する。

```text
Fragment generation code
Fragment prompt package data
Application Fragment compatibility methods
Repository Fragment read/write/search path
legacy-fragment command
fragment alias
Fragment-only tests / scripts
不要になったGenerative LLM compatibility surface
```

---

## 13. clean rebuild前の安全条件

今回のruntime inventoryにより、既存DBの内容を保全してdata migrationする必要はないと確認した。

L-03 / L-05では次を満たす。

1. 削除対象DBがdevelopment / evaluation / test用途であり、production正本を含まないことを再確認する。
2. `sample/` Raw corpusをDB削除へ巻き込まない。
3. canonical schemaから空DBを再生成できることをtestする。
4. 新DBにFragment / legacy Prototype tableが存在しないことをtestする。
5. canonical Search / MCP / Object workflowがclean DBで成立することを確認する。
6. 削除対象はruntime DBと不要derived dataに限定し、Sample RawやGit管理のschema/documentを誤削除しない。

---

## 14. Acceptance Criteria

L-01は改定後、以下を満たしたため完了とする。

- [x] Fragment tableを最終的に削除すると確定した。
- [x] 既存Fragment rowsを恒久read-only保全しないと確定した。
- [x] Fragment write/read pathを削除すると確定した。
- [x] `capture.py`を削除すると確定した。
- [x] Fragment promptを削除すると確定した。
- [x] `legacy-fragment`を削除すると確定した。
- [x] `fragment` aliasを削除すると確定した。
- [x] `search_items(kind='fragment')` / Fragment embeddingを削除すると確定した。
- [x] Fragment dataをObject Knowledgeへ自動変換しないと確定した。
- [x] 研究再現性はGit履歴を中心に確保すると確定した。
- [x] 実削除はL-03/L-05で安全に実施すると確定した。

**L-01: Complete (Revised).**

次Task:

```text
L-02 [P0] Final Document table / code / CLIの移行方針を確定する
```
