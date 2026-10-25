# O-06 — Release / Tag / Breaking Change Policy

Updated: 2026-10-25

- Decision: **Accepted**
- Task: `O-06 [P1] Release / Tag policy、Prototypeと新KBの境界、Breaking Change記録`
- Scope: version numbering, Git tag, GitHub Release, Prototype/new-SGOKB boundary, Breaking Change recording
- Depends on:
  - `docs/decisions/SGOKB_GIT_HISTORY_CLEANUP_POLICY.md`
  - `docs/evaluation/PHASE_N_CLOSURE_AUDIT.md`
  - `docs/design/SGOKB_CURRENT_ARCHITECTURE.md`
  - `docs/planning/phases/O/PHASE_O_STATUS.md`

## 1. Decision summary

SGOKBの正式Release境界を次のように固定する。

```text
Legacy line      = Prototype 0.2.x
Current line     = SGOKB 1.x
First release    = 1.0.0
Git tag          = v1.0.0
Package version  = 1.0.0
Tag target       = O-06 closure完了後のmain HEAD
```

Prototype 0.2は正式tag / GitHub Releaseを作らず、既存のarchive文書とGit historyをhistorical authorityとして保持する。

新SGOKBの最初の正式versionは`1.0.0`とする。理由は、Prototype 0.2からKnowledge Model、DB schema、CLI、検索、AI integration、MCP境界まで非互換な全面再設計であり、Phase N acceptanceとPhase O documentation / Git cleanupを完了して正式なcurrent baselineとして扱えるためである。

## 2. Versioning policy

Semantic Versioning形式を使用する。

```text
MAJOR.MINOR.PATCH
```

### MAJOR

次のいずれかを満たす互換性破壊を含む場合に上げる。

- canonical DB / accepted Knowledge schemaの非互換変更
- public CLI contractの非互換変更
- MCP public tool contractの非互換変更
- Package / Structured Result public exchange contractの非互換変更
- stable Object identity / Version semanticsの非互換変更
- documented migrationなしでは既存利用者が継続利用できない変更

### MINOR

後方互換な機能追加。

例:

- 新しいread-only MCP tool
- optional provider / adapter
- 新しい検索modeやFacet機能を既存contractを壊さず追加
- 新Class / Registry capabilityの後方互換追加

### PATCH

後方互換な修正。

例:

- bug fix
- documentation correction
- acceptance evidence correction
- internal refactor
- ranking / recovery implementationのcontract-preserving fix

## 3. Tag policy

正式version tagは次の形式とする。

```text
v<MAJOR>.<MINOR>.<PATCH>
```

例:

```text
v1.0.0
v1.1.0
v1.1.1
```

原則:

1. tagは`main`上の正式Release commitだけへ付与する。
2. 公開・共有済みtagはimmutable history markerとして扱う。
3. tagを別commitへsilent moveしない。
4. 同名tagを削除して再利用しない。
5. Task / Phaseごとにはtagを作らない。
6. acceptance途中のcommitには正式tagを付与しない。
7. package metadata versionはtagから先頭`v`を除いた値と一致させる。
8. tag作成前にRelease Noteとversion metadataを`main`へ含める。

## 4. Prototype 0.2 boundary

### 4.1 Retroactive Prototype tagは作らない

D-07実査時点でもO-06開始時点でも既存tag / GitHub Releaseは0件だった。

したがって、過去commitへ`v0.2.0`等のtagを後付けしない。過去に存在しなかったrelease boundaryを後から作ると、当時正式Releaseされていたかのような誤認を生むためである。

Prototype 0.2のhistorical authorityは次とする。

- `docs/archive/prototype-0.2/`
- Prototype期のGit commit / PR history
- archive内のbenchmark / design / evaluation記録

### 4.2 新旧境界

新設計との正式な境界は`v1.0.0`で示す。

```text
Before v1.0.0
  historical Prototype / redesign development history

v1.0.0 and later
  current Source Grounded Object Knowledge Base release line
```

`v1.0.0`より前の任意commitを「supported Prototype release」とみなさない。

## 5. First release decision — v1.0.0

`v1.0.0`採用理由:

- Phase A〜Mで再設計・実装を完了した。
- Phase Nはformal closure auditでComplete / PASSとなった。
- N07-R01を含むfailure / recovery acceptanceを完了した。
- O-01でroot READMEをcurrent SGOKBへ更新した。
- O-02でcurrent architecture / operations authorityを統合した。
- O-03でPrototype 0.2文書をArchived / Legacyとして明示した。
- O-04で全remote branch historyを`main`へ統合した。
- O-05で不要remote branchを削除し`main`のみへ整理した。
- Prototype 0.2からpublic contractが全面的に非互換である。

`0.3.0`等のPrototype継続番号ではなく`1.0.0`を使用することで、旧Fragment / Final Document中心Prototypeと現行Object Knowledge Baseの境界をversion番号だけでも識別可能にする。

## 6. Release policy

GitHub Releaseは「ユーザーが再現可能なversion boundary」に限定する。

正式Releaseの前提:

1. target commitが`main`に存在する。
2. package versionとtagが一致する。
3. Release Noteがrepositoryに保存されている。
4. current README / design authorityがそのversionと矛盾しない。
5. relevant acceptance / migration / known limitationが記録されている。
6. release対象に未解決のP0 blockerがない。

Task完了や設計途中状態をGitHub Release化しない。

## 7. Pre-release policy

外部利用者による明示的なrelease candidate検証が必要な場合のみSemVer pre-releaseを使用できる。

```text
v1.1.0-rc.1
v2.0.0-rc.1
```

Phase番号やTask番号をtagとして代用しない。

```text
NG: phase-n-final
NG: o-06-complete
NG: n05-r2
```

これらはcommit / planning document / benchmark resultで追跡する。

## 8. Breaking Change policy

MAJOR releaseまたは既存consumerに実質的な移行を要求する変更では、Release Noteに`Breaking Changes`節を必須とする。

最低記録項目:

- 何が変わったか
- 影響を受けるsurface
- 旧挙動がなぜ継続できないか
- 移行手順
- 自動移行の有無
- rollback / backup上の注意
- deprecated / removed contract

「内部実装変更」のみでpublic contractが変わらない場合はBreaking Change扱いにしない。

## 9. v1.0.0 Breaking Changes

Prototype 0.2からv1.0.0への主要非互換点を次のように固定する。

### 9.1 Knowledge Model

旧:

```text
Raw -> Fragment -> Final Document
```

新:

```text
Source / Snapshot / Raw Artifact
  -> Evidence
  -> Object Evidence Package
  -> Structured Object Result
  -> accepted Object Knowledge Version
```

Fragment / Final Documentをcanonical Knowledgeとして扱うcontractは廃止した。

### 9.2 Canonical data / DB

Prototype DBはv1.0.0 canonical DBへin-place upgradeしない。

- legacy Fragment / Final Document tablesはactive schemaから除外。
- Prototype migration 001 / 002はactive bootstrapから除外。
- legacy Prototype DBはfail-fast対象。
- production data蓄積前の再設計であるため、Prototype DBからの自動data migrationは提供しない。

必要なRaw Captureは別途保持し、新canonical DBへ再importする。

### 9.3 CLI

public entrypointを`sgokb`へ統一した。

旧PrototypeのFragment / Final generation中心CLI、legacy compatibility command、旧package wrapperはcurrent contractではない。

Relation writeもdirect mutationではなくEvidence付きObject Result Import経由に限定する。

### 9.4 Search / Vector

current semantic retrievalはR2 hierarchical multi-vector contractを使用する。

```text
object_overview
facet
statement
```

Evidence Searchは別familyとして扱う。

旧PrototypeのFragment embedding /旧Vector indexをcurrent derived indexとして再利用しない。derived search indexはcurrent canonical Knowledgeからrebuildする。

### 9.5 External AI integration

旧方式の「全Evidenceを生成LLMへ通しFinal Documentを自動生成する」workflowを標準経路から廃止した。

current workflowはexplicit Human-in-the-loop boundaryを使用する。

```text
Evidence Package
  -> explicit external export
  -> ChatGPT / external AI
  -> Structured Object Result
  -> validate / review
  -> explicit import
```

ChatGPT APIはcanonical Knowledge成立の必須条件ではない。

### 9.6 MCP

v1.0.0 MCP surfaceはread-onlyを正式contractとする。

write toolはMVPに含めず、canonical direct mutationを許可しない。

### 9.7 SGOKB / UPDS boundary

SGOKBはWorld / Object Knowledgeを担当し、ユーザーのPreference / Personal InferenceはUPDSの責務とする。

旧Prototype由来の責務混同をcurrent contractへ持ち込まない。

## 10. Release Note authority

v1.0.0のrepository-side Release Noteは次を正本とする。

- `docs/releases/v1.0.0.md`

GitHub Releaseを公開する場合、その本文はrepository-side Release Noteの意味内容と一致させる。

GitHub UI側だけに重要なBreaking Change / migration情報を置かない。

## 11. Release publication sequence

正式Releaseは次の順序とする。

```text
1. Release policy / Release Noteをmainへcommit
2. package versionをrelease versionへ更新
3. O-06 / Phase O closure statusをmainへcommit
4. final main HEADを確認
5. annotated tag v1.0.0をfinal main HEADへ作成
6. tagをoriginへpush
7. tag targetをGitHub上で再確認
8. 必要ならGitHub Releaseをv1.0.0 tagから公開
```

Tag作成後にO-06内容を追加修正した場合、その修正を含む新しい正式Releaseが必要かを判断し、既存tagをsilent moveしない。

## 12. Future release checklist

- [ ] version numberをSemVerで決定
- [ ] package metadata更新
- [ ] Breaking Change有無を判定
- [ ] migration / backup note更新
- [ ] acceptance / test evidence確認
- [ ] repository Release Note作成
- [ ] README / current docs確認
- [ ] `main`へ統合
- [ ] tag target SHA確認
- [ ] immutable tag作成・push
- [ ] GitHub Release本文とrepository Release Noteの整合確認

## 13. O-06 completion boundary

Policy / Release Note / metadataのrepository作業が完了しても、`v1.0.0` tagが存在しない限り「Prototypeと新SGOKBの境界をtagで明示した」というO-06要件は未完了と扱う。

したがって、final O-06 commit作成後に`v1.0.0` tagをそのcommitへ付与し、live GitHubでtag targetを確認した時点でO-06をCompleteとする。
