# SGOKB Documentation

`docs/` はSource Grounded Object Knowledge Baseの要件・設計・Decision・評価・計画・運用資料を用途別に管理します。

## Current status

現在は **Phase N — Test / Evaluation / Acceptance** を進行中です。

N-04 Grounded Generationは、G-22 Formal v3 Re-Acceptanceを実行済みで、結果は`0 / 3 Case PASS`のvalid formal FAILです。N-04はFailed / not Complete、N-05はblockedです。

現在のplanning入口は [`planning/README.md`](planning/README.md) を使用してください。

## Documentation map

### [`requirements/`](requirements/)
現在有効な要件定義。

主な内容:

- SGOKBの目的・責務
- Object / Class / Facet
- Source / Evidence / Provenance
- Search / Retrieval
- SGOKB ↔ UPDS境界
- Workflow / 非機能要件

### [`decisions/`](decisions/)
Architecture Decision、Design Freeze、運用上の固定方針。

変更理由や「なぜこの設計になったか」を確認するときに使用します。

### [`design/`](design/)
確定したデータモデル、pipeline、検索、交換形式、実装設計。

### [`evaluation/`](evaluation/)
試験結果、benchmark、formal acceptance、failure analysis。

現在のN-04については次を参照してください。

- [`N04G22_FORMAL_V3_REACCEPTANCE.md`](evaluation/N04G22_FORMAL_V3_REACCEPTANCE.md)
- [`N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md`](evaluation/N04G22_FAILURE_ROOT_CAUSE_INVESTIGATION.md)

### [`planning/`](planning/)
タスク、Phase preparation / closure、handoff、実行計画。

文書数が増えたため、Phase・Task単位のサブディレクトリへ整理しています。詳細な構成と現在地は [`planning/README.md`](planning/README.md) を正本とします。

主要入口:

- [`planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md`](planning/project/KNOWLEDGE_BASE_REDESIGN_TASKS.md) — 全体タスク
- [`planning/project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`](planning/project/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md) — 全体handoff
- [`planning/phases/N/PHASE_N_PREPARATION.md`](planning/phases/N/PHASE_N_PREPARATION.md) — Phase N
- [`planning/phases/N/N04/`](planning/phases/N/N04/) — N-04関連

### [`reference/`](reference/)
設計時の調査資料、inventory、gold casesなどの参照資料。

### [`operations/`](operations/)
実運用手順。

### [`archive/`](archive/)
旧Prototypeや完了済みmigration/renameなどの歴史資料。

Archiveは現行仕様の正本として使用しません。

## Recommended reading order

現在のシステム全体を把握する場合:

1. [`requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`](requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md)
2. [`requirements/OBJECT_REQUIREMENTS.md`](requirements/OBJECT_REQUIREMENTS.md)
3. [`requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`](requirements/SOURCE_EVIDENCE_REQUIREMENTS.md)
4. [`requirements/SEARCH_REQUIREMENTS.md`](requirements/SEARCH_REQUIREMENTS.md)
5. [`decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`](decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md)
6. [`planning/README.md`](planning/README.md)

現在の作業だけを追う場合は、`planning/README.md`から対象Phase / Taskへ進んでください。

## Placement rules

新規文書は内容に応じて配置します。

```text
requirement       -> docs/requirements/
architecture ADR -> docs/decisions/
design            -> docs/design/
test / research   -> docs/evaluation/
plan / handoff    -> docs/planning/
reference         -> docs/reference/
operation         -> docs/operations/
historical        -> docs/archive/
```

Planning文書は`docs/planning/`直下へ増やさず、原則として`project/`または`phases/<Phase>/...`へ配置します。
