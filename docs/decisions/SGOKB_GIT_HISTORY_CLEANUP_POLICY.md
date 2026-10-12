# SGOKB Git History / Branch / PR / Tag / Release Cleanup Policy

更新日: 2026-10-12

- Decision: Accepted
- Task: `D-07 [P1] 旧branch / PR / tag / releaseの整理ルールを決める`
- Depends on:
  - `docs/decisions/KNOWLEDGE_BASE_REDESIGN_BRANCH_STRATEGY.md`
  - `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
  - `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`
- Scope: branch / PR / tag / release history retention and cleanup
- Out of scope: Phase O final release version number, branch protection/ruleset implementation

## 1. 目的

再設計期間中に増えるtask branchと、旧Prototype由来のbranch / PR / tag / releaseを整理し、次を同時に満たす。

- 未統合commitを誤って失わない。
- merge済み短命branchを恒久的に残さない。
- PR review / decision historyを失わない。
- squash merge時の誤判定を避ける。
- Prototypeと新SGOKBのrelease境界を後から説明できる。
- `main`と`integration/knowledge-base-redesign`の役割をD-01どおり維持する。

D-07はGit履歴を「きれいに見せる」ことより、**到達可能性・救済可能性・監査可能性**を優先する。

## 2. D-07実施時点の実査結果

2026-10-12時点で確認した状態を基準記録とする。

### 2.1 GitHub branch

```text
main
integration/knowledge-base-redesign
task/d04-src-layout
task/d05-module-move-policy
task/d06-runtime-git-policy
```

`main` / integration / task branchのいずれもGitHub上branch protectionは設定されていない。

### 2.2 Local-only / historical branch

```text
archive/pre-rename-local-main
feature/cpc-prototype
feature/cpc-prototype-upgrade
```

調査結果:

- `feature/cpc-prototype`はintegrationに対してunique commit 0。
- `feature/cpc-prototype-upgrade`もintegrationに対してunique commit 0。
- `archive/pre-rename-local-main`はintegrationに存在しないunique commitを11件持つ。
- `git cherry`でも11件すべてpatch-equivalent未統合として`+`判定だった。

したがって、前者2本はmerge済み履歴の冗長branch、`archive/pre-rename-local-main`は削除禁止のhistorical safety branchと判定する。

### 2.3 Pull Request

GitHub PR #1〜#9はすべてmerged済みで、open PRは0件だった。

再設計task branchとの対応:

```text
PR #7  task/d04-src-layout           -> integration
PR #8  task/d05-module-move-policy   -> integration
PR #9  task/d06-runtime-git-policy   -> integration
```

### 2.4 Tag / Release

D-07実施時点ではGit tagは0件、GitHub Releaseも0件である。

したがって、削除すべき既存tag / releaseは存在しない。

## 3. Branch分類

branchを次の4種類に分類する。

### 3.1 Stable branch

```text
main
```

- 削除しない。
- force pushしないことを原則とする。
- 再設計完了前はstable baselineを維持する。
- O-04でintegrationを通常merge commitにより統合する。

### 3.2 Temporary integration branch

```text
integration/knowledge-base-redesign
```

- 再設計期間中は削除しない。
- D-04〜O-04の正規統合先とする。
- O-04でmainへmergeし、O-05のcleanup確認後に削除する。
- permanent `develop` branchへ昇格させない。

### 3.3 Short-lived task branch

```text
task/<task-id>-<slug>
```

PRが完了したら恒久保存しない。

削除条件はSection 4で定義する。

### 3.4 Historical archive branch

```text
archive/<purpose>
```

現行設計へ直接mergeするためのbranchではなく、未救済の歴史commitを一時保全する。

archive branchは「古いから削除対象」ではない。unique commitの処遇が決まるまで保持する。

## 4. Task branch削除条件

短命task branchは次をすべて満たす場合、local / remoteとも削除してよい。

1. 対応PRがGitHub上`merged=true`である。
2. branch head SHAがPRのhead SHAと一致する、またはPR merge後に追加commitがないことを確認した。
3. PR baseが意図したbranchである。
4. merge後のbase branchで必要test / validationが成立している。
5. branch上にPRへ含まれなかった追加commitがない。
6. recovery目的でbranch名自体を保持する必要がない。

### 4.1 Squash mergeでは`git branch --merged`だけを使わない

短命PRをsquash mergeすると、元task branchのcommit SHAはintegrationの祖先にならない。

この場合、

```text
git branch --merged
```

だけでは「未merge」と誤判定できる。

D-07以降は、削除判断を次の組み合わせで行う。

- GitHub PRの`merged`状態
- PR head branch / head SHA
- PR base branch
- branch tipにmerge後追加commitがないこと
- 必要に応じdiff / patch内容

Git ancestryは補助情報とし、唯一の判定根拠にしない。

### 4.2 Merge済みtask branchは早期削除してよい

O-05まで全task branchを残す必要はない。

PR mergeと検証完了後に短命branchを削除し、active branch一覧を小さく保つ。

GitHub PRそのものがmerge元branch名・head SHA・diffを履歴として保持するため、branch pointerの恒久保存は不要である。

## 5. 未統合branchの救済手順

削除候補branchにunique commitが存在する場合、削除を停止する。

最低確認:

```text
git rev-list --left-right --count <base>...<branch>
git log <branch> --not <base>
git cherry <base> <branch>
git diff <base>...<branch>
```

処遇は次のいずれかとする。

### A. 現行設計へ必要

必要commitだけを新しいtask branchへcherry-pick /再実装し、通常PRでintegrationへ統合する。

旧branchをそのままbulk mergeしない。

### B. 歴史資料として必要

`archive/<purpose>`へ保存し、現行branchへmergeしない。

必要に応じremoteへpushし、単一PC上のlocal refだけに依存しない。

### C. 完全に不要

内容が別commit / archive docs / release artifact等で保全済みであることを確認後に削除する。

「古い」「名前が違う」だけでは不要判定にしない。

## 6. `archive/pre-rename-local-main`の扱い

D-07で11件のunique commitを確認したため、削除しない。

このbranchは旧Prototype後期のKnowledge Pipeline効率化、Fragment後段比較、Support review、View policy等の実験・評価commitを含む。

新SGOKBへそのままmergeすると、旧`src/cpc`責務や廃止予定Fragment中心設計を再流入させるため、通常mergeは禁止する。

方針:

1. `archive/pre-rename-local-main`としてhistorical branchを維持する。
2. local-onlyで失われないようremote archive branchとしても保全する。
3. Phase L / Oで旧Prototype資産を最終整理するとき、必要な知見・文書・testだけを選別する。
4. 現行設計へ再利用する場合は新taskとして移植し、archive branch自体をmergeしない。
5. 全unique commitの処遇が文書化されるまで削除しない。

## 7. 旧Prototype feature branchの扱い

`feature/cpc-prototype`と`feature/cpc-prototype-upgrade`はD-07実査でintegrationにunique commitを持たない。

対応PR #4 / #5もmerged済みであるため、local branch pointerを削除してよい。

過去PR、commit object、main/integrationの履歴に内容が保持されているため、local branch名の保存価値は低い。

今後も同様のfeature branchは、merge済みかつunique commit 0を確認後に削除する。

## 8. Pull Request retention policy

### 8.1 PRは履歴として保持する

merged / closed PRは削除対象と考えない。

PRには次が残る。

- intent / scope
- source / target branch
- head SHA
- review / discussion
- diff
- merge時刻
- validation記録

branchを削除してもPR historyは残るため、短命branch保存の代替となる。

### 8.2 Closed-unmerged PR

将来closed-unmerged PRが発生した場合、head branch削除前にunique commitを調査する。

- 不要と確認済み -> branch削除可
- 再利用候補 -> archiveまたは新taskへ救済
- 判断不能 -> branchを保持

### 8.3 Stale open PR

長期間放置されているだけで自動closeしない。

Task master /現行設計と照合し、supersededであることを明記してcloseする。

## 9. Tag policy

### 9.1 Tagはimmutable history markerとして扱う

公開済み・共有済みtagは原則として削除・移動・同名再利用しない。

誤tagが必要な場合でも、既存tagをsilentに別commitへ付け替えず、新tagまたは明示的な訂正手順を使用する。

### 9.2 Prototype tag

既存Prototype tagがある場合は歴史として保持する。

D-07時点ではtagが存在しないため、D-07で過去commitへretroactive tagを新規作成しない。

Prototype /新SGOKBのversion境界を新たにtagで表現する必要がある場合は、O-06でcommit境界と命名を確定する。

### 9.3 Task / Phase完了をtag乱用しない

D-04、D-05等のTaskごとにtagを作らない。

Task historyはPR / commit / Task masterで追跡する。

## 10. Release policy

### 10.1 Releaseはユーザー利用可能なversion境界に限定する

設計Task完了やintegration途中状態ごとにGitHub Releaseを作らない。

Release candidate / public versionとして意味がある境界だけRelease化する。

### 10.2 再設計期間中に新SGOKB releaseを作らない

新SGOKBの最初のreleaseは、少なくとも次を満たした後にO-06で判断する。

- O-04でintegrationがmainへ統合済み。
- Phase N Acceptanceが完了。
- migration / backup / restore上の重大未解決事項がない。
- README / current docsが新SGOKBを正本としている。

version番号・tag名はD-07では固定しない。

### 10.3 既存Releaseは削除しない

将来既存Releaseが存在する状態で再設計しても、古いReleaseを「古い仕様だから」という理由で削除しない。

必要ならRelease NoteにLegacy / Prototypeを明記する。

D-07時点ではGitHub Releaseは0件である。

## 11. Cleanup実施順序

branch cleanupは次の順序で行う。

```text
1. fetch / pruneで最新remote状態を取得
2. open PR確認
3. branch一覧取得
4. branchごとのunique commit確認
5. merged PRとのhead SHA照合
6. unique commitがあればrescue / archive
7. merge済み短命branchをremote削除
8. merge済み短命branchをlocal削除
9. fetch --prune
10. final branch / tag / release inventoryを記録
```

remoteを先に削除した後でもlocal branchは復旧手段になるため、local削除はremote削除確認後に行う。

## 12. D-07実施時のcleanup対象

### 削除可能

```text
local:
  feature/cpc-prototype
  feature/cpc-prototype-upgrade
  task/d04-src-layout
  task/d05-module-move-policy
  task/d06-runtime-git-policy

remote:
  task/d04-src-layout
  task/d05-module-move-policy
  task/d06-runtime-git-policy
```

理由:

- feature 2本はintegrationにunique commit 0。
- task 3本はPR #7〜#9のmerged headで、merge後追加commitなし。

D-07実施時に上記cleanupを実行済み。remoteでは`task/d04-src-layout` / `task/d05-module-move-policy` / `task/d06-runtime-git-policy`を削除し、localではこれら3本に加えて`feature/cpc-prototype` / `feature/cpc-prototype-upgrade`を削除した。

### 保持

```text
main
integration/knowledge-base-redesign
archive/pre-rename-local-main
```

archive branchは11 unique commitを持つためremoteにも保全する。D-07実施時に`archive/pre-rename-local-main`を`origin/archive/pre-rename-local-main`へpushし、local / remote双方で保全済み。

### D-07自身のbranch

`task/d07-git-cleanup-policy`もPR merge後、このPolicyに従いlocal / remoteから削除する。

## 13. O-05 / O-06への引き継ぎ

### O-05

- O-04 merge完了後に`integration/knowledge-base-redesign`を削除する。
- その時点の残存task branchを再監査する。
- `archive/pre-rename-local-main`はPhase L / Oでunique commit処遇が完了していなければ保持する。

### O-06

- 新SGOKBのversion番号を決定する。
- Prototypeと新SGOKBのtag境界を必要なら明示する。
- Release Noteにbreaking changes / migration / legacy statusを記載する。
- 既存tagを移動して新境界を表現しない。

## 14. 禁止事項

- `git branch --merged`だけでsquash-merged task branchを未merge / merge済み判定しない。
- unique commit未確認のbranchを一括削除しない。
- archive branchを現行設計へそのままmergeしない。
- PRをbranch整理のために削除対象と考えない。
- 既存tagを別commitへsilent moveしない。
- integration途中commitから正式Releaseを作らない。
- release versionをD-07で先取り固定しない。
- branch名だけを根拠に「不要」と判断しない。

## 15. 完了条件

D-07は次を満たした時点で完了とする。

- [x] 現在のlocal / remote branchを棚卸しした。
- [x] PR #1〜#9の状態を確認した。
- [x] open PR 0件を確認した。
- [x] tag 0件、Release 0件を確認した。
- [x] squash mergeを含むtask branch削除判定を定義した。
- [x] unique commitを持つarchive branchの保全方針を定義した。
- [x] Prototype feature branchの削除可否を確認した。
- [x] tag / releaseのimmutable history方針を定義した。
- [x] O-05 / O-06へのcleanup / release境界を引き継いだ。

D-07完了によりPhase Dは完了する。次Taskは`E-01 [P0] Object schemaを設計する`とする。
