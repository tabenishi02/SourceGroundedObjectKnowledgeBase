# L-01 Fragment Retirement Policy

更新日: 2026-10-14

Status: Accepted

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

## 1. Decision

Phase L以降のFragment資産は、単一の扱いに統一せず、**永続データと実行可能な生成機能を分離して退役させる**。

最終方針は次のとおりとする。

> **既存Fragmentデータはlegacy read-onlyとして保全し、新規Fragment生成write pathは完全に退役させる。Fragment generation code / prompt / CLIをresearch-only runtimeとして現行packageに残さない。研究再現性はGit履歴・固定baseline・archive資料で確保する。**

したがって、L-01の分類は以下となる。

| Asset | Decision |
|---|---|
| 既存`fragment_runs / fragments / fragment_evidence` rows | Legacy read-onlyとして保全 |
| Fragment generation write path | Retire |
| `capture.py` / Fragment validation / persistence write code | Active packageからRetire |
| Fragment prompt群 | Active package dataからRetire |
| `legacy-fragment` CLI | Retire |
| `fragment` alias | Retire |
| Fragment search representation / Prototype embedding | Current SearchからRetire、legacy DB内では移行完了まで保全 |
| Fragment provenance | Audit可能性を保全。ただしstandard runtime APIとして恒久保証しない |
| Fragment専用tests / scripts | Active acceptance suiteからRetire。必要な履歴はarchive / Gitで再現 |

このDecisionは物理削除そのものを実施しない。実DB migrationはL-03、benchmark/archive整理はL-04、code / dependency / compatibility cleanupはL-05で実施する。

---

## 2. なぜ完全削除ではなくdata read-onlyなのか

既存schemaではFragmentは単なる生成テキストではなく、次の履歴へ接続されている。

```text
normalized_runs
  -> fragment_runs
      -> ai_runs
      -> fragments
          -> fragment_evidence
              -> evidence
```

さらにHigh Recall系では次の実行ledgerが存在する。

```text
extraction_jobs
  -> extraction_batches
  -> evidence_assessments
  -> entity_candidates
  -> fragment_run
```

これらを即時削除すると、過去のPrototype処理について「どのEvidenceから、どのmodel / prompt / runで、どのFragmentが生成されたか」を追跡できなくなる。

一方、canonical Object KnowledgeはすでにFragment非依存で成立しているため、これらを新canonical schemaへ第一級資産として移植する必要もない。

よって、既存データは**legacy provenance / audit資産**としてのみ扱う。

---

## 3. Fragment table方針

### 3.1 canonical schemaへFragment tableを持ち込まない

次のtableをcanonical Object Knowledge schemaの構成要素として維持しない。

```text
fragment_runs
fragments
fragment_evidence
```

新しいcanonical Fragment tableは作成しない。

L-03までは既存DB compatibilityのため旧tableを残す。L-03では、既存DBについて次のどちらかを満たすmigrationを設計する。

1. legacy archive領域としてread-only保全する。
2. DB外archiveへ完全性情報付きで退避した後、active schemaから除去する。

どちらを採る場合も、legacy ID、Evidence参照、AI run参照、row count等の監査可能性を失わないことを必須とする。

### 3.2 FragmentからObject Knowledgeを自動生成しない

既存Fragmentはcanonical Knowledgeへのmigration sourceとはみなさない。

禁止:

```text
legacy Fragment
  -> automatic synthesis
  -> accepted Object Knowledge Version
```

必要なKnowledgeはcanonical Evidence Package / Object Result workflowを通して生成する。

### 3.3 write pathは停止する

Phase L完了時点では、通常配布packageから新規Fragment rowを生成できない状態にする。

対象には少なくとも以下を含む。

```text
fragment_runsへの新規write
fragmentsへの新規write
fragment_evidenceへの新規write
High Recall extraction jobからFragmentをpromoteするwrite
classic Fragment extractor write
```

---

## 4. Fragment code方針

### 4.1 `capture.py`

`src/sgokb/capture.py`は**active packageからRetire**する。

`_legacy`へ移して実行可能状態を維持する方式は採用しない。

理由:

- standard workflowから完全に不要である。
- Generative LLM provider、Prompt、Prototype Entity/Evidence persistenceを同時に維持する必要が生じる。
- research-only runtimeを維持すると、Phase L完了後も旧write pathの保守責任が残る。
- Git履歴により当時の実装を正確に復元できる。

削除実施はL-05とし、必要な歴史資料のarchive判断はL-04と連携する。

### 4.2 Application compatibility methods

以下はRetire対象とする。

```text
legacy_capture_fragments()
capture_fragments()
legacy_fragment()
fragment()
```

新standard application serviceからFragment implementationを参照しない。

### 4.3 Fragment persistence / search methods

`knowledge_repository.py`等に残るFragment write / promotion / Fragment search専用methodはRetire対象とする。

ただし、L-03完了まで既存DB調査・migration検証に必要なread helperを一時保持してよい。

その場合も条件は次のとおり。

- writeしない。
- standard application pathから呼ばない。
- canonical storage contractへFragment APIを追加しない。
- L-03完了後にL-05で再評価する。

### 4.4 `validate_fragments`

`domain/_prototype.py::validate_fragments`はcanonical domain contractではない。

Fragment生成codeとともにRetire対象とする。canonical Object Result validationへ流用しない。

---

## 5. Prompt方針

Fragment generation専用promptはactive package dataからRetireする。

対象例:

```text
fragment_extraction.*
high_recall.*
```

これらを新Object Result promptへrenameして再利用しない。

研究再現性のために現行packageへ残す必要はない。再現時はbaseline commitまたはarchive manifestから、当時のPromptとSchemaを一体で復元する。

Prompt単体を更新し続けるresearch-only運用は採用しない。

---

## 6. CLI方針

### 6.1 `legacy-fragment`

`legacy-fragment`はPhase LでRetireする。

Phase L完了後のstandard CLIから新規Fragment生成を開始できてはならない。

### 6.2 `fragment` alias

`fragment` aliasもRetireする。

旧aliasだけを残すと、利用者から見るとFragment workflowが現行機能であるように見えるため、compatibility価値より誤操作リスクが大きい。

CLI package conversion自体はPhase Mの責務だが、Phase MはFragment commandを再導入しない。

### 6.3 read-only inspection

既存Fragment監査のために恒久的な`fragment` CLIを維持しない。

L-03 migration作業中にread-only inspectionが必要であれば、migration検証用script / SQL /一時helperを用いる。これはstandard user-facing CLI contractには含めない。

---

## 7. Search / Embedding方針

旧`search_items`は`kind IN ('evidence', 'fragment')`であり、Fragment embeddingも保持できる。

Phase L以降は次のように扱う。

```text
search_items(kind='fragment')
legacy fragment embeddings
```

- canonical Searchの入力にしない。
- canonical Search indexへ移送しない。
- new embeddingを生成しない。
- L-03 migration完了までlegacy DB内で保持してよい。
- canonical Evidence / Object / Facet / Statement representationと混在させない。

Embedding provider abstraction自体は現行Search資産なのでRetireしない。

---

## 8. Provenance / audit方針

Fragment自体は正本Knowledgeではないが、過去処理の監査可能性は保持する。

最低限追跡可能であるべき情報:

```text
legacy fragment_id
fragment_run id
normalized_run / snapshot
legacy entity id
Evidence IDs
AI run id
model / revision
prompt / prompt_version
configuration
created_at
```

ただし、これを理由に旧Fragment runtimeを恒久保守しない。

L-03でactive tableを削除する場合は、archive側に上記identity / referenceを保持し、migration前後の件数・参照整合性を検証する。

---

## 9. Research reproducibility方針

`research-only`として現行runtimeを維持する案は採用しない。

代わりに、研究再現性は次で確保する。

1. Git履歴で旧code / prompt / tests / scriptsを保持する。
2. 本Decisionのbaseline commitを旧Fragment runtimeの基準点として記録する。
3. L-04で旧benchmark資産を歴史資料としてarchiveする。
4. 必要であればarchive manifestに対象path / hash /実行条件を記録する。
5. 再実行が本当に必要になった場合は、現行standard packageへ戻すのではなく、historical commitから隔離環境を再構成する。

これにより研究再現性とproduction保守負担を分離する。

---

## 10. Tests / scripts方針

Fragment write pathを検証するtestは、Phase L完了後のactive acceptance suiteへ残さない。

分類:

- canonical Evidence / Search / Object workflowの回帰test: Keep
- Fragment生成そのもののtest: Retire / archive候補
- legacy DB migration integrity test: L-03で追加
- benchmark再現用test / script: L-04 archive候補

L-05でFragment codeを削除する前に、現行test / scriptからのimport依存を除去する。

---

## 11. 後続Taskへの拘束条件

### L-02

Final Documentの処遇を決める際、Fragment生成を再び必要条件にしてはならない。

### L-03

既存Prototype DB migrationは以下を満たす。

- Fragmentをcanonical Knowledgeへ昇格させない。
- existing Fragment dataをmigration完了前にdropしない。
- legacy Fragment ID / Evidence / AI run provenanceを追跡可能にする。
- migrationを再実行してduplicate archive/importを作らない。
- backup / rollback / integrity verificationを定義する。

### L-04

旧Fragment benchmarkはcurrent KPIから外す。再現価値のあるmanifest / expected result /実行条件は歴史資料としてarchiveできる。

### L-05

以下を削除・縮小する実装Taskとする。

```text
Fragment generation code
Fragment prompt package data
Application Fragment compatibility methods
Repository Fragment write path
legacy-fragment command
fragment alias
Fragment-only test / script dependencies
不要になったGenerative LLM compatibility surface
```

ただしL-03で必要なmigration read pathを先に壊さない。

---

## 12. Acceptance Criteria

L-01は以下を満たしたため完了とする。

- [x] Fragment tableの処遇を確定した。
- [x] 既存Fragment dataのread-only / audit方針を確定した。
- [x] Fragment write pathを退役させる方針を確定した。
- [x] `capture.py`の処遇を確定した。
- [x] Fragment promptの処遇を確定した。
- [x] `legacy-fragment`の処遇を確定した。
- [x] `fragment` aliasの処遇を確定した。
- [x] `search_items(kind='fragment')` / legacy embeddingの処遇を確定した。
- [x] Fragment provenanceの保全条件を確定した。
- [x] tests / scriptsの研究再現方針を確定した。

**L-01: Complete.**

次Task:

```text
L-02 [P0] Final Document table / code / CLIの移行方針を確定する
```
