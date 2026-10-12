# Knowledge Base Redesign Branch Strategy

更新日: 2026-10-12

- Decision: Accepted
- Task: `D-01 [P0] 再設計用長期ブランチ戦略を決定する`
- Long-lived integration branch: `integration/knowledge-base-redesign`
- Stable baseline branch: `main`

## 1. 目的

Source Grounded Object Knowledge Baseの大規模再設計を、`main`の動作可能性とGit履歴の追跡可能性を維持しながら段階的に統合するbranch / PR / merge方針を定義する。

本DecisionはPhase D以降のRepository再編、Object Knowledgeデータモデル、Evidence Pipeline、Exchange、Import、Retrieval、MCP、Legacy移行、CLI、Acceptanceまでの再設計作業に適用する。

## 2. 決定

再設計期間中は次の3層を使用する。

```text
main
  └─ integration/knowledge-base-redesign
       ├─ task/d04-...
       ├─ task/e01-...
       ├─ task/f01-...
       └─ ...
```

### 2.1 `main`

`main`は常時、現在の動作可能な基準点として保持する。

原則として、未完成の再設計実装、途中状態のschema migration、大量rename / move、旧Prototypeを破壊する変更を直接入れない。

再設計期間中に`main`へ入れてよい変更は、原則として次に限定する。

- 再設計branch開始前に確定させるDecision / Handoff等のdocs-only変更
- 現行`main`に対する緊急bug fix / security fix
- 再設計実装と独立して安全に適用できる小規模保守

### 2.2 `integration/knowledge-base-redesign`

再設計全体の統合先として長期integration branchを1本だけ使用する。

このbranchは永久的なdevelopment branchではなく、今回のKnowledge Base再設計専用の一時branchとする。

開始点は、D-01のDecisionと進捗文書を`main`へ反映したcommitとする。

D-04以降の再設計作業は原則としてこのbranchを正規作業基盤とする。

最終的にはPhase Oの`O-04 再設計branchをmainへ統合する`で`main`へmergeし、その後O-05で削除対象とする。

### 2.3 短命task branch

code / migration / module move / dependency / schema / CLI等の実装変更は、原則としてintegration branchから短命branchを作成する。

命名規則:

```text
task/<task-id>-<short-slug>
```

例:

```text
task/d04-src-layout
task/e01-object-schema
task/f01-evidence-pipeline
task/j01-retrieval-mcp-boundary
```

短命branchのbase / merge先は原則として`integration/knowledge-base-redesign`とする。

## 3. PRを必須とする変更

次の変更は短命branch + PRを原則必須とする。

- `src/`のmodule再配置
- 大量rename / move
- import path変更
- DB schema / migration
- canonical dataの意味を変える変更
- package / result / Evidence / Version contract変更
- dependency追加・削除
- CLI behavior変更
- MCP contract変更
- Legacy code削除
- 複数責務へ影響する横断変更

一方、誤記修正やTask state更新等の小規模docs-only変更はintegration branchへ直接commitしてよい。ただし、設計Decisionそのものを変更する場合はPRを優先する。

## 4. moveとbehavior changeの分離

大量rename / moveとbehavior changeを同一PRへ混在させない。

原則順序:

```text
1. move / rename only
2. import / test / path repair
3. behavior change
```

同じTaskで必要であっても、差分が大きい場合は別PRへ分割する。

これにより、Git historyとreviewで「配置変更」と「意味変更」を識別可能にする。

## 5. integration branchへのmerge条件

短命branchをintegrationへmergeする最低条件:

1. Task scopeが明示されている。
2. unrelated changeを含まない。
3. 対象変更に対応するtestを追加・更新している。
4. 既存testを実行し、意図しないfailureがない。
5. generated / local / secret / canonical runtime dataをcommitしていない。
6. move-only PRではbehavior changeを混入させない。
7. docs / schema / migrationの必要な追従変更を含む。
8. 未解決の破壊的変更がある場合はTask / Handoffへ明記する。

## 6. `main`との同期方針

長期branchの過度な乖離を防ぐため、`main`へ再設計外のfixが入った場合は、可能な限り早く`main`をintegration branchへ取り込む。

標準:

```text
main update
   ↓
merge main -> integration/knowledge-base-redesign
   ↓
conflict解消
   ↓
full test
```

原則として同じfixをintegration側へ別実装しない。不要なcherry-pickの重複履歴も避ける。

少なくとも各Phase終了時、および大規模module move / migration開始前には`main`との差分と同期状態を確認する。

## 7. `main`への最終merge条件

`integration/knowledge-base-redesign`を`main`へmergeするのはO-04で行う。

最低条件:

- Phase D〜Nの必須Taskが完了している。
- Acceptance / recovery testが完了している。
- 現行docsが新SGOKBを正本として説明している。
- migration / rollback / backup / restore手順が必要範囲で確認されている。
- generated / local / exchange / secretがGit管理対象へ混入していない。
- `main`の最新変更をintegrationへ取り込み済みである。
- integration headでfull testが成功している。
- `main...integration`の最終差分をレビューしている。

最終mergeは履歴を残すため通常のmerge commitを基本とする。短命task PRは1 Task = 1論理変更になる場合、squash mergeを使用してよい。

## 8. Phase E開始時の正規実装基盤

Phase E開始時の正規実装branchは`integration/knowledge-base-redesign`とする。

Phase E以降の別チャットやCodex作業では、明示的な理由がない限り`main`ではなくintegration branchを起点とする。

Task branchを作る場合もintegration branchから作成する。

## 9. branch protection

D-01時点で`main`はGitHub上`protected: false`であり、RepositoryにはGitHub Actions CIも存在しない。

そのためD-01ではserver-side branch protectionを新規設定しない。

理由:

- 現時点ではrequired status checkとして利用できるCIがない。
- solo developmentでrequired reviewを強制すると運用コストが大きい。
- D-01の主目的は再設計移行戦略の確定であり、Repository administration policyの整備とは分離できる。

ただし、これは`main`への無制限な直接commitを許容するという意味ではない。本Decisionの運用ルールで`main`を論理的に保護する。

CIが整備された後、遅くともO-04前にbranch protection / ruleset導入を再評価する。

## 10. docs-only変更の扱い

D-01 Decision自体と、integration branchの存在を知らせるためのTask master / Handoff / Documentation Index更新は`main`へ反映してからintegration branchを作成する。

これにより`main`を見た場合でも、再設計の作業先がintegration branchであることを判断できる。

integration branch作成後の再設計進捗は原則としてintegration側のTask master / Handoffを更新する。

## 11. 禁止事項

- 未完成の再設計codeを`main`へ直接積み上げない。
- Task branchを`main`から作り、再設計変更をintegrationを経由せずmergeしない。
- 長期integration branchを複数並行で作らない。
- moveとbehavior changeを巨大な単一PRへ混在させない。
- `main`のfixをintegration側でsilent再実装しない。
- Phase EのDB schemaをD-01のbranch都合で先取り確定しない。

## 12. D-01完了条件

- [x] `main`をstable baselineとする方針を確定した。
- [x] 長期integration branch名を`integration/knowledge-base-redesign`と確定した。
- [x] 作成起点と寿命を確定した。
- [x] task branch / PR基準を確定した。
- [x] docs-onlyとcode/migrationの運用差を確定した。
- [x] `main`同期方針を確定した。
- [x] Phase E開始時の正規branchを確定した。
- [x] branch protectionをD-01では変更せずO-04前に再評価する方針を確定した。

次Taskは`D-04 [P0] src/sgokbの責務別再編を設計する`とする。D-02 / D-03は既に完了済みであり、再実施しない。
