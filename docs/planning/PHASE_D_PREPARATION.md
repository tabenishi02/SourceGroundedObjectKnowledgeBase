# Source Grounded Object Knowledge Base — Phase D Preparation

更新日: 2026-10-12

- Target: `Phase D — Repository / Git / フォルダ構造再編`
- Status: Ready to start
- Next task: `D-01 [P0] 再設計用長期ブランチ戦略を決定する`

## 1. 目的

本書は、Phase C完了後にPhase Dへ安全に移行するための開始条件・現行Git状態・入力文書・禁止事項を整理する。

Phase Dの設計判断そのものは本書では先取りしない。特に、長期branchの作成、`src/sgokb`の大量move、既存moduleのrename、不要branch削除等は、それぞれD-01 / D-04 / D-05 / D-07で決定してから実施する。

---

## 2. Phase C完了確認

Phase Cの全Taskは完了している。

- [x] C-01 SGOKBをWorld / Object Knowledge Layerとして定義
- [x] C-02 UPDSをPersonal Inference Layerとして定義
- [x] C-03 Conceptの所有境界を確定
- [x] C-04 SGOKB → UPDS連携契約を定義

Phase Cの正本成果物:

- `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

これにより、Phase D開始前に必要だった「SGOKBとUPDSの責務・所有・参照境界」は確定済みである。

---

## 3. Phase D開始時のGit現況

2026-10-12時点のGitHub上の確認結果:

- branch: `main`のみ
- current `main` head at preparation check: `44dd9a703e354023ff476e2a488aeddb603feba4`
- open Pull Request: 0件
- `main` branch protection: GitHub API上 `protected: false`

したがってD-01開始時点では、未統合feature branchやopen PRを先に救済・整理する必要はない。

ただし、この状態はD-01実施時に再確認する。特に`main` headやbranch protectionは時間とともに変化し得るため、本書のSHAを将来の固定前提にしてはならない。

---

## 4. Phase D Taskの現在状態

`docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`を正本とする。

```text
D-01 [P0] 再設計用長期ブランチ戦略を決定する        未完了 ← 次
D-02 [P0] 旧Prototype文書の扱いを決める            完了
D-03 [P0] 新しいdocs構造を決定する                 完了
D-04 [P0] src/sgokbの責務別再編を設計する          未完了
D-05 [P1] 既存モジュール移動方針を決める           未完了
D-06 [P1] local/generated/exchangeのGit除外方針     未完了
D-07 [P1] 旧branch / PR / tag / release整理ルール   未完了
```

D-02 / D-03をやり直さず、既決事項をD-04以降の入力として利用する。

---

## 5. D-01で決定すべき事項

D-01では少なくとも次を決定する。

1. 大規模再設計を`main`直上で進めるか、長期integration branchを設けるか。
2. 長期branchを設ける場合の名称・作成起点・merge条件。
3. D-04以降のsubtaskを短命branch + PRへ分割する基準。
4. docs-only変更とcode/migration変更でbranch運用を分けるか。
5. `main`を常時動作可能基準点として維持するための最低条件。
6. branch protectionを今回の再設計範囲で扱うか、GitHub運用上の別Taskとするか。
7. 長期branchへ変更が蓄積し過ぎることを防ぐ同期・review方針。
8. Phase E開始時にどのbranchを正規実装基盤とするか。

D-01では「例として`feature/knowledge-base-redesign`」という既存Task記述を、そのまま確定名称とみなさない。

---

## 6. Phase Dで維持する既決事項

### 6.1 moveとbehavior changeを分離する

大量rename / moveとロジック変更を同一commitへ混在させない。

原則:

```text
move / rename only
        ↓
import / test / path修正
        ↓
behavior change
```

### 6.2 Archiveを現行仕様へ戻さない

`docs/archive/prototype-0.2/`および`docs/archive/rename-2026-10/`は歴史資料であり、現行仕様の正本として再利用しない。

### 6.3 現行requirementsを物理再編の入力とする

Phase B / Cで確定した要件を、Repository構造変更によって意味的に変更してはならない。

特に次を維持する。

- SGOKB = World / Object Knowledge Layer
- UPDS = Personal Inference Layer
- Concept canonical ownership = SGOKB
- SGOKB → UPDS standard read path = Retrieval/Application Core → MCP
- SQLite = canonical Knowledge Store方針
- Search Representation / Embedding / Vector Index = rebuildable derived layer
- Google Drive = exchange領域であり正本ではない

### 6.4 物理DB schemaをPhase Dで先取りしない

Phase DはRepository / Git / module配置の責務を扱う。

Object / Version / Relation / Facet等の具体的な本番DB schemaはPhase Eで確定するため、module配置の都合だけでschemaを固定しない。

---

## 7. D-04以降への設計入力

現時点の責務別code構造候補:

```text
src/sgokb/
├─ domain/        # Object / Relation / Facet / Version
├─ ingestion/     # Capture / Import / Normalize / Evidence
├─ storage/       # SQLite repository / migration
├─ retrieval/     # FTS / vector / hybrid / similarity
├─ exchange/      # Evidence Package / Result Import
├─ rendering/     # JSON -> Markdown等
├─ mcp/           # MCP adapter
├─ cli/           # CLI adapter
└─ application/   # use cases / orchestration
```

これはD-04で検証・確定する候補であり、まだ確定済み物理構造ではない。

D-04では既存`src/sgokb`実装を実際に棚卸しし、単純な理想構造への全面moveではなく、再利用可能なmoduleと依存方向を確認してから配置を決める。

---

## 8. Phase D開始前に読んでおく文書

最低限:

1. `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
2. `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
3. `docs/planning/PHASE_D_PREPARATION.md`
4. `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
5. `docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`

責務境界確認が必要な場合:

- `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
- `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
- `docs/requirements/CONCEPT_OWNERSHIP_BOUNDARY_REQUIREMENTS.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`

---

## 9. Definition of Ready

Phase Dへ移行する条件を次とする。

- [x] Phase A完了
- [x] Phase B完了
- [x] Phase C C-01〜C-04完了
- [x] Phase C正本文書がDocumentation Indexから参照可能
- [x] 再設計Task masterがPhase C完了を示している
- [x] 現行HandoffをPhase C完了状態へ更新する作業を実施
- [x] 現在のbranch / open PR状態を確認
- [x] D-02 / D-03が既に完了していることを確認
- [x] D-01を次Taskとして特定

以上により、Phase Dは開始可能である。

---

## 10. Phase D開始時の指示文

別チャットでD-01から開始する場合は、次を使用できる。

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。
Phase A〜Cは完了しています。

まず以下を確認し、既決事項と現在のRepository / Git状態を把握してください。
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md
- docs/planning/PHASE_D_PREPARATION.md

今回実施するタスク:
D-01 [P0] 再設計用長期ブランチ戦略を決定する

現在のGit状態を再確認したうえで、mainを動作可能な基準点として維持しつつ、Phase D以降の大規模再設計を安全に進めるbranch / PR / merge方針を決定し、ドキュメントへ反映してください。
まだD-04以降の大量ファイル移動やbehavior changeは実施しないでください。
```
