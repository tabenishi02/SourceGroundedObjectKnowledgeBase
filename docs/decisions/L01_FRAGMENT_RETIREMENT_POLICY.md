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

L-01の初回Decisionでは、既存Fragment rowsをlegacy read-onlyとして保全する方針を採用した。

その後、Phase Lの目的と現在のcanonical workflowを再確認した結果、**現在の標準運用・Search・MCP・SGOKB/UPDS連携のいずれにもFragmentデータを必要とする具体的用途は存在しない**と判断した。

したがってL-01の最終方針を次のように改定する。

> **Fragment関連資産は、現時点で必要な具体的用途が存在しないため、active DB・active package・standard CLIから完全に削除する。既存Fragment rowsをread-only archiveとして恒久保持しない。必要な歴史的実装情報はGit履歴と必要最小限の設計資料で確認する。**

この方針は「今すぐ無条件にDROPする」という意味ではない。既存DBを破損させないため、物理削除はL-03/L-05でmigration・依存除去を順序立てて実施する。

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

## 4. DB削除方針

### 4.1 canonical schemaへFragment tableを持ち込まない

次のtableはcanonical schemaの構成要素ではない。

```text
fragment_runs
fragments
fragment_evidence
```

新しいcanonical Fragment tableは作成しない。

### 4.2 existing DBでも最終的に削除する

L-03では既存Prototype DBについて、Fragment関連rowを新schemaへ移送しない。

最終結果は以下とする。

```text
legacy Fragment rows
  → canonical migration対象外
  → dependency確認
  → new migrationでdrop
```

Fragment rowの内容を外部archiveへ退避することも標準要件としない。

ただし削除直前には、migration失敗時に元DBへ戻せる通常のbackup / rollback手順を用意する。

これはFragmentを長期保存するためではなく、破壊的migrationの安全策である。

### 4.3 migration 001/002は書き換えない

`001_initial.sql` / `002_knowledge_capture.sql`は過去migration履歴なので編集しない。

Fragment tableの削除は新規migrationとして実施する。

これによりfresh DBとexisting DBのupgrade pathを明示する。

### 4.4 Fragment専用補助tableも削除候補とする

以下はFragment / High Recall workflow専用であることをL-03で最終確認し、他のcanonical用途がなければ削除する。

```text
extraction_jobs
extraction_batches
evidence_assessments
entity_candidates
```

`page_contexts`や`ai_runs`等、Fragment以外にも再利用可能性があるtableは一括削除せず、個別に用途を確認する。

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

ただしL-03 migration実装中に旧tableを読む必要がある一時的helperは、migration完了までのみ保持してよい。

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

L-03 migration検証でFragment rowの確認が必要な場合は、一時的なSQL / migration testを用いる。

Phase MはFragment commandを再導入しない。

---

## 9. Search / Embedding削除方針

旧`search_items(kind='fragment')`と、それに紐づくFragment embeddingは削除する。

- canonical Searchへ移送しない。
- new embeddingを生成しない。
- legacy DB migration時に削除する。
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
- legacy DB cleanup migration test: L-03で追加
- Fragment benchmark / speed script: L-04でarchiveまたはDeleteを判断

L-05でcodeを削除する前にactive test / scriptからFragment import依存を除去する。

---

## 12. 後続Taskへの拘束条件

### L-02

Final Documentの処遇を決める際、Fragmentを保持理由にしてはならない。

Fragmentは削除前提である。

### L-03

既存Prototype DB migrationは次を満たす。

- Fragment rowsをcanonical schemaへ移行しない。
- Fragment rowsを外部archiveすることを必須にしない。
- Fragment tableを新migrationで削除する。
- Fragment専用補助tableも他用途がなければ削除する。
- migration前backup / rollbackを用意する。
- migration後にFragment table / Fragment search item / Fragment embeddingが残っていないことを検証する。
- Source / Snapshot / Raw Artifact / Evidence等、保持対象のlegacy dataを巻き込んで削除しない。

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

## 13. 削除前の安全条件

Fragment資産は不要と判断したが、既存DBの破損を避けるため、実削除時には次を満たす。

1. canonical Source / Evidence migrationとFragment cleanupを区別する。
2. Fragment tableを参照するFK / trigger / search row / embeddingを先に特定する。
3. backup / rollback手順を用意する。
4. migration後にfresh DBとexisting DBの双方でtestする。
5. Fragment削除によってcanonical Search / MCP / Object workflowが変化しないことを確認する。

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
