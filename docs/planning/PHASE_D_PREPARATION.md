# Source Grounded Object Knowledge Base — Phase D Preparation

更新日: 2026-10-12

- Target: `Phase D — Repository / Git / フォルダ構造再編`
- Status: In progress — D-01〜D-05 complete
- Active redesign branch: `integration/knowledge-base-redesign`
- Next task: `D-06 [P1] local/generated/exchangeのGit除外方針を更新する`

## 1. 目的

本書は、Phase C完了後にPhase Dへ安全に移行するための開始条件・現行Git状態・入力文書・禁止事項を整理する。

Phase Dの設計判断は対応Taskで確定してから実施する。D-01の長期branch戦略とD-04の`src/sgokb`責務別構造は確定済みであり、実ファイルの大量move、既存moduleのrename、不要branch削除等は、それぞれD-05 / D-07の決定前に先行実施しない。

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

Phase D準備時点では`main`のみ、open PR 0件、`main` branch protectionは`protected: false`だった。

D-01開始時に再確認した結果:

- branch: `main`のみ
- `main` head before D-01 docs update: `7ab2093655687878e1406fd97d88c648b5ffd27d`
- open Pull Request: 0件
- `main` branch protection: GitHub API上 `protected: false`

未統合feature branchやopen PRの救済は不要だった。D-01では、Decision文書を`main`へ反映したcommitを起点として`integration/knowledge-base-redesign`を作成する方針を採用した。

以降、`main`はstable baseline、integration branchは再設計の正規作業基盤とする。

---

## 4. Phase D Taskの現在状態

`docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`を正本とする。

```text
D-01 [P0] 再設計用長期ブランチ戦略を決定する        完了
D-02 [P0] 旧Prototype文書の扱いを決める            完了
D-03 [P0] 新しいdocs構造を決定する                 完了
D-04 [P0] src/sgokbの責務別再編を設計する          完了
D-05 [P1] 既存モジュール移動方針を決める           完了
D-06 [P1] local/generated/exchangeのGit除外方針     未完了 ← 次
D-07 [P1] 旧branch / PR / tag / release整理ルール   未完了
```

D-02 / D-03をやり直さず、既決事項をD-04以降の入力として利用する。

---

## 5. D-01で決定した事項

D-01では次を確定した。

1. `main`直上で大規模再設計を進めず、長期integration branchを設ける。
2. branch名は`integration/knowledge-base-redesign`とする。
3. D-01文書反映commitをbranch作成起点とし、O-04で`main`へ統合する。
4. code / migration / module move / schema等は原則`task/<task-id>-<slug>`短命branch + PRでintegrationへ統合する。
5. 小規模docs-only進捗更新はintegrationへ直接commit可能とし、Decision変更はPRを優先する。
6. `main`はstable baselineとして維持し、再設計外fixが入った場合は速やかにintegrationへmergeする。
7. branch protectionはD-01では変更せず、CI整備後かつ遅くともO-04前に再評価する。
8. Phase E開始時の正規実装基盤は`integration/knowledge-base-redesign`とする。
9. move / renameとbehavior changeは別PRへ分離する。

正本: `docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md`

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

## 7. D-04決定結果 / D-05への設計入力

D-04で次の責務別構造を確定した。

```text
src/sgokb/
├─ domain/
├─ ingestion/
├─ storage/
├─ retrieval/
├─ exchange/
├─ rendering/
├─ application/
├─ cli/
├─ mcp/
└─ _legacy/   # Phase Lまでの一時隔離領域
```

既存`repository.py / domain.py / providers.py`は複数責務を持つため単純moveではなくsplit対象とする。`capture.py / final.py / knowledge_repository.py`の旧Fragment / Final責務は新標準layerへ混ぜず、replacement完了までlegacy境界として扱う。

D-05ではD-04の責務構造を維持し、moduleをdirect move / package conversion / split / legacyの4分類へ整理した。旧top-level importは一時的な明示re-export shimで互換維持し、新規codeはcanonical pathのみを使用する。実移動はPhase E〜Lでstructural PRとbehavior PRを分離して段階実施する。

正本:

- `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
- `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`

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

## 10. Phase D継続時の指示文

別チャットでD-06から開始する場合は、次を使用できる。

```text
Source Grounded Object Knowledge BaseのKnowledge Base再設計を続けます。
Phase A〜Cは完了し、Phase DはD-01〜D-05まで完了しています。

再設計の正規作業基盤はintegration/knowledge-base-redesignです。
まず以下を確認してください。
- docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md
- docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md
- docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md
- docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md
- docs/planning/PHASE_D_PREPARATION.md

今回実施するタスク:
D-06 [P1] .local / generated / Google Drive exchangeデータのGit除外方針を更新する

D-04 / D-05で確定したcode責務・段階移行方針とruntime data配置を混同せず、canonical DB、Raw Source、generated index、Evidence Package / Result、backup、secret等の物理配置とGit管理対象/除外対象を決定してください。Schema / sample / fixture等、意図的にGit管理する資産との境界も明記してください。
```
