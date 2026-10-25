# O-06 — v1.0.0 Release Publication

Updated: 2026-10-25

- Task: `O-06 [P1] Release / Tag policy、Prototypeと新KBの境界、Breaking Change記録`
- Repository: `tabenishi02/SourceGroundedObjectKnowledgeBase`
- Release: `1.0.0`
- Tag: `v1.0.0`
- Frozen release commit: `0e1a8464e9db98b4e99169cae6292821f3fd410c`
- Publication state: **Tag pending**

## Frozen release payload

`v1.0.0`は次のcommitへ固定する。

```text
0e1a8464e9db98b4e99169cae6292821f3fd410c
```

このcommitはO-05完了時のbaseline `22d521da1b0f9b3d5bcf6fc0559eb2ccbeffe31d`に対して、O-06 release payloadとして次の8ファイルだけを変更している。

```text
README.md
docs/README.md
docs/decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md
docs/planning/README.md
docs/planning/phases/O/PHASE_O_STATUS.md
docs/releases/README.md
docs/releases/v1.0.0.md
pyproject.toml
```

Release commit上の`pyproject.toml`は次を確認済み。

```text
version = "1.0.0"
description = "Source-grounded, provenance-aware object knowledge base"
```

## Why tag this commit instead of later `main` HEAD

このpublication文書やtag確認後のPhase O Complete更新はrelease payloadそのものではない。

したがって、`v1.0.0`は最新`main`へ追従させず、上記frozen release commitへ固定する。

```text
0e1a846...  <- v1.0.0
    |
    +-- later planning/status bookkeeping commits on main
```

公開後に`v1.0.0`を後続commitへ移動してはならない。

## Pre-publication check

PowerShell / Git clientで次を実行する。

```powershell
git fetch origin --prune
git show --no-patch --oneline 0e1a8464e9db98b4e99169cae6292821f3fd410c
git ls-remote --tags origin refs/tags/v1.0.0
```

最後のコマンドが空であることを確認する。既に`v1.0.0`が存在する場合は新規作成せず、targetを調査する。

## Create annotated tag

```powershell
git tag -a v1.0.0 0e1a8464e9db98b4e99169cae6292821f3fd410c -m "SGOKB v1.0.0"
git push origin v1.0.0
```

`HEAD`や`main`という可変refをtag targetに使用せず、上記SHAを明示する。

## Local verification

```powershell
git rev-list -n 1 v1.0.0
```

期待値:

```text
0e1a8464e9db98b4e99169cae6292821f3fd410c
```

annotated tag object自体のSHAとcommit SHAは異なるため、`git rev-list -n 1`でpeeled commitを確認する。

## Remote verification

```powershell
git ls-remote --tags origin refs/tags/v1.0.0 refs/tags/v1.0.0^{}
```

annotated tagでは通常、tag objectとpeeled commitの2行が表示される。`refs/tags/v1.0.0^{}`側がfrozen release commitを指すことを確認する。

## GitHub Release

O-06の必須境界はGit tagである。GitHub Release UI publicationはRelease policy上の配布surfaceであり、tag boundary成立後に必要に応じて実施できる。

GitHub Releaseを作成する場合:

- tag: `v1.0.0`
- title: `SGOKB v1.0.0`
- body: `docs/releases/v1.0.0.md`と意味内容を一致させる
- Breaking Changes / migration guidanceを省略しない

## Completion gate

O-06は次がlive GitHubで確認できた時点でCompleteとする。

```text
tag exists = true
tag name = v1.0.0
peeled target = 0e1a8464e9db98b4e99169cae6292821f3fd410c
package version at target = 1.0.0
```

確認後、`PHASE_O_STATUS.md` / Planning Index / root READMEをPhase O Completeへ更新する。このbookkeeping updateのために`v1.0.0` tagを移動しない。
