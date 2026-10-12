# SGOKB Module Migration Policy

更新日: 2026-10-12

- Decision: Accepted
- Task: `D-05 [P1] 既存モジュール移動方針を決める`
- Depends on: `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
- Scope: move / split / compatibility / PR sequence
- Out of scope: production DB schema, Object behavior, actual bulk move

## 1. 目的

D-04で確定した責務別構造へ、現行`src/sgokb`をGit履歴と動作可能性を保ちながら段階移行する方針を定義する。

D-05は「どこへ移すか」だけでなく、次を固定する。

- move-onlyとbehavior changeの分離方法
- 既存import pathを壊さないcompatibility方針
- 単純move可能moduleとsplit必須moduleの区別
- package名と既存`.py`名が衝突するmoduleの移行方法
- migration / prompt等package dataの扱い
- 各Phaseで実施する移動wave
- 各PRの検証条件

実ファイルの大量moveは本Taskでは実施しない。移動は後続Task / Phaseで本方針に従って行う。

## 2. 基本原則

### 2.1 Big Bang migrationを行わない

`src/sgokb`全体を一度に新構造へ移さない。

理由:

- 現行moduleは複数責務を持ち、1対1 renameできない。
- tests / scripts / CLI entrypointが旧import pathへ依存している。
- `repository.py`, `domain.py`, `providers.py`はsplitが必要である。
- 旧Fragment / Final workflowは新実装成立前に消せない。

### 2.2 structural changeとsemantic changeを分離する

標準順序:

```text
A. move / package conversion
        ↓
B. import path / package-data / test path repair
        ↓
C. behavior / schema / workflow change
```

A+Bは同一PR内で扱ってよいが、commitは可能な限り分離する。

- Commit 1: `git mv`中心。内容変更・整形をしない。
- Commit 2: import path、`__init__.py`、package-data、test/script pathの修正。
- Commit 3以降: 原則禁止。behavior変更が必要なら別PRへ送る。

PR最終HEADはtestが通る状態でなければならない。途中commitが一時的にimport errorを持つことは許容するが、review時にmove差分とrepair差分を分離できることを優先する。

### 2.3 move時にformat / rename / cleanupを混ぜない

move-only PRでは次を同時に行わない。

- function / class rename
- algorithm変更
- SQL変更
- schema変更
- logging変更
- exception type変更
- typing全面追加
- formatterによる全行書換え
- コメント・docstringの大規模書換え

これらは後続behavior PRへ分離する。

### 2.4 `git mv`を基本とする

Gitは内容類似度からrename検出できるが、作業時は原則`git mv`を使用する。

split対象では、まず元moduleを可能な限り保持したまま責務単位で抽出し、同じcommitで無関係なrewritingを行わない。

履歴確認には`git log --follow -- <path>`を使用できる状態を維持する。

## 3. Compatibility import方針

### 3.1 旧top-level importを即時破壊しない

現行tests / scriptsは次のようなimportを使用している。

```python
from sgokb.repository import Repository
from sgokb.domain import SearchFilter
from sgokb.importer import WebCaptureImporter
from sgokb.extraction import GenericExtractor
from sgokb.search import merge_candidates
from sgokb.providers import CompatibleEmbedder
```

新canonical pathへ移した後も、必要期間は旧pathをcompatibility surfaceとして残す。

### 3.2 shimはロジックを持たない

旧top-level moduleをshimとして残す場合、責務は明示的re-exportだけに限定する。

例:

```python
# sgokb/importer.py
from .ingestion.importer import WebCaptureImporter, classify

__all__ = ["WebCaptureImporter", "classify"]
```

禁止:

- shim独自ロジック
- duplicate implementation
- shim側だけのbug fix
- wildcard exportによる暗黙API拡大
- shimから新moduleとlegacy moduleを混在呼び出しすること

### 3.3 新規codeは旧shimをimportしない

compatibility shim導入後、新規codeは必ずcanonical pathを使用する。

```text
old consumer -> compatibility shim -> canonical implementation
new consumer -----------------------> canonical implementation
```

新moduleから旧top-level shimへ逆依存しない。

### 3.4 deprecation warningは初期移動PRでは出さない

import時のwarning追加はobservable behavior changeなのでmove-only PRへ入れない。

旧pathのdeprecated表示が必要ならPhase M / Lで別変更として扱う。

### 3.5 shim削除条件

shimは次をすべて満たした後に削除可能とする。

1. repository内のproduction codeが旧pathを参照していない。
2. tests / scriptsの現行系がcanonical pathへ移行済み。
3. CLI / package entrypointが新pathで動作する。
4. legacy read-only用途に必要な参照が整理済み。
5. full testが成功する。
6. documentationに旧path依存が残っていない。

残存shimの最終cleanupはPhase L-05を基本とし、CLI互換はM-02の判断を優先する。O-04前に不要shimが残っていないことを再確認する。

## 4. moduleの移動分類

### 4.1 Group A — 比較的安全なdirect move候補

次は責務が比較的明確で、behaviorを変えずに新packageへ移しやすい。

| 現行 | canonical path候補 | 方針 |
|---|---|---|
| `importer.py` | `ingestion/importer.py` | `git mv` + root shim |
| `extraction.py` | `ingestion/extraction.py` | `git mv` + root shim |
| `context.py` | `ingestion/context.py` | `git mv` + root shim |
| `search.py` | `retrieval/search.py` | `git mv` + root shim |

ただし現状ではこれらも`domain.py`のsymbolへ依存しているため、move後すぐにdomain symbol再配置まで同一PRで行わない。

canonical path変更とdomain splitは別PRにする。

### 4.2 Group B — module → package conversionが必要

D-04の最終構造では次の名前がpackageになるが、現在は同名`.py` moduleである。

- `domain.py` → `domain/`
- `application.py` → `application/`
- `cli.py` → `cli/`

これらは「旧`.py`を残したまま同名packageへ段階移行」しない。Python import解決を曖昧にしないため、1つのstructural PRでpackage conversionする。

#### `domain.py`

Phase E開始前にpackage conversionを行う。

推奨初期形:

```text
sgokb/domain/
├─ __init__.py       # 既存import互換の明示re-export
└─ _prototype.py     # 旧domain.pyを内容変更せず移した一時module
```

`from sgokb.domain import SearchFilter`等のimport pathは維持する。

Phase E以降、新Object domainを`domain/`内へ追加し、旧symbolを責務別packageへ段階的に抜き出す。

`_prototype.py`を新Object domainの依存先にしない。

#### `application.py`

新application use caseを初めて追加するPhaseでpackage conversionする。

```text
sgokb/application/
├─ __init__.py
└─ _prototype.py
```

既存`Application`を一時re-exportできるが、新use caseは旧`Application`を継承・拡張してFragment中心workflowを延命しない。

#### `cli.py`

Phase M-01でpackage conversionする。

```text
sgokb/cli/
├─ __init__.py       # mainをre-export
└─ _prototype.py
```

`pyproject.toml`のentrypoint `sgokb = "sgokb.cli:main"`はこの構成でも維持できるため、不要にentrypoint文字列を変更しない。

### 4.3 Group C — split必須。wholesale move禁止

#### `repository.py`

`repository.py`は以下を混在させている。

- SQLite connection / migration
- Source / Snapshot / Evidence
- Entity / Relation / Evidence Link
- Fragment
- Search / Embedding
- Document

したがって、`storage/repository.py`へ丸ごとmoveしない。

方針:

1. 現行`Repository`を互換façadeとして一時維持する。
2. Phase E/Fで新`storage/`実装を責務単位に追加する。
3. 既存Source/Evidence persistenceをbehavior-preservingに抽出する。
4. 新Object persistenceはPhase E schemaに従い別実装する。
5. root `Repository`は必要期間、新実装へのdelegation façadeとする。
6. Fragment / Document系methodを新storage contractへ持ち込まない。
7. Phase Lでlegacy method利用がなくなった後にfaçadeを縮小・削除する。

`repository.py`のsplitとObject schema導入を同一「move-only」PRにしてはならない。

#### `providers.py`

Embedding providerとGenerative LLM providerを分離する。

方針:

- Embedding側はPhase Iで`retrieval`へ抽出する。
- Generative LLM側は新standard runtimeへ移さない。
- legacy/research用途の最終配置はPhase Lで決める。
- root `providers.py`は移行期間中re-export façadeにできる。

Embedding抽出PRでLLM adapterの動作変更・削除を行わない。

### 4.4 Group D — replacement成立後にlegacy隔離

次は直ちに`_legacy/`へmoveしない。

- `capture.py`
- `final.py`
- `knowledge_repository.py`
- Fragment/Final中心の`benchmark.py`
- Fragment/Final用prompt群

理由は、現行test / script / Prototype互換経路が依存しているためである。

移動条件:

- 新standard workflowが当該機能を参照しないことを確認済み。
- 代替機能が必要な場合はreplacementが成立済み。
- legacy read / evaluation用途を保持するか削除するかがPhase Lで明確。

legacy移動時は旧top-level pathへshimを置くことができるが、新standard moduleから`_legacy`へimportしてはならない。

## 5. `migrations/`の移動方針

現行:

```text
sgokb/migrations/
├─ 001_initial.sql
└─ 002_knowledge_capture.sql
```

migration履歴は既存DB再現・upgradeに必要なので、見た目を整えるためだけに早期移動しない。

最終的には`storage/migrations/`が自然だが、次を同一structural PRで満たせる時点まで現位置を維持する。

- migration loader pathを更新できる。
- `pyproject.toml` package-dataを更新できる。
- wheel/editable installの双方でSQL fileを取得できる。
- 既存migration version番号・内容を変更しない。
- 既存DBからmigration履歴を継続できる。

SQL内容変更や新Object schema migration追加は、directory moveとは別commit / 別PRにする。

## 6. `prompts/`の移動方針

現行promptは主にFragment / Final生成用であり、新standard workflowのprompt正本とはみなさない。

D-05では移動しない。

Phase Lでlegacy処遇を確定する際、必要なら`_legacy/prompts/`へ移す。

新しいEvidence Packageの`instructions.md`等は`exchange`契約として別設計し、旧`prompts/`をrenameして流用しない。

package-data変更はprompt moveと同じstructural PRで実施する。

## 7. 実施Wave

### Wave 0 — D-05

今回。

- migration policy確定
- actual source moveなし
- behavior changeなし

### Wave 1 — Phase E開始前 / E-01冒頭

**Implementation status: Complete (2026-10-12, PR #11).**

目的: 新Object domainを置ける物理空間を作る。

- `domain.py`を`domain/_prototype.py`へ`git mv`
- `domain/__init__.py`で現行public symbolを明示re-export
- import compatibility test
- behavior / schema変更なし

このstructural PRをE-01のschema/domain実装PRと分離する。

### Wave 2 — Phase F-01前後

**Implementation status: Complete (2026-10-12, Phase F preparation).**

目的: Keep対象のingestion基盤を正規配置へ移す。

- `importer.py` → `ingestion/importer.py`
- `extraction.py` → `ingestion/extraction.py`
- `context.py` → `ingestion/context.py`
- root compatibility shim
- production code /対象testの現行系importをcanonical pathへ更新
- old / canonical import identityをcompatibility testで固定

Source schema適応やEvidence behavior変更はこのstructural moveへ混在させず、F-01へ分離した。Phase F開始時点の差分と実装順序は`docs/planning/PHASE_F_PREPARATION.md`を参照する。

### Wave 3 — Phase E/Fのstorage再構成

目的: 巨大`Repository`からcanonical persistenceを分離する。

- `storage/`へconnection / migration runner / Source-Evidence persistenceを段階抽出
- Object repositoryはPhase E schemaに基づき新設
- root `Repository`は一時façade

これは単純moveではなくbehavior-preserving refactorと新schema実装を別PRへ分ける。

### Wave 4 — Phase I

目的: retrieval responsibilityを正規配置へ移す。

- `search.py` → `retrieval/search.py`
- Embedding contracts / providersを`domain.py` / `providers.py`から抽出
- root compatibility shim

candidate model / ranking / Vector backend変更はstructural移動後の別PRとする。

### Wave 5 — Phase G/H

目的: 新use case orchestrationをpackage化する。

- `application.py`をpackage conversion
- 旧`Application`を一時compatibility export
- 新Evidence Package / Result Import use caseは新moduleへ実装

旧Fragment methodを新application APIとして持ち込まない。

### Wave 6 — Phase M

目的: CLI adapterをpackage化する。

- `cli.py`をpackage conversion
- entrypoint compatibility維持
- Object中心CLIを別behavior PRで実装

### Wave 7 — Phase L

目的: legacy隔離・削除判断。

- `capture.py`
- `final.py`
- `knowledge_repository.py`
- legacy benchmark
- legacy prompts
- Generative LLM adapters
- 不要compatibility shim

を、L-01〜L-05の決定に従って隔離・archive・削除する。

## 8. tests / scripts移行方針

### 8.1 tests

move PRでは2種類のtestを区別する。

1. **compatibility test**: 旧import pathがまだ必要な期間、shimが同じsymbolを返すことを確認。
2. **canonical test**: 新責務のtestはcanonical pathからimportする。

既存testを一度に全てcanonical pathへ書き換えて履歴を見えにくくしない。移動対象moduleに対応するtestから段階更新する。

### 8.2 scripts

`scripts/run_*evaluation.py`等Prototype評価scriptはlegacy依存が強いため、standard code移行のためだけに全面rewriteしない。

- standard運用で残すscriptはcanonical importへ更新。
- Prototype評価専用scriptはPhase Lでarchive / research-only処遇を決める。

## 9. PR分割ルール

1 PRの対象は原則1 responsibility groupまたは1 package conversionとする。

推奨例:

```text
PR A: convert domain.py to domain package (structural only)
PR B: add Object domain contracts (behavior/design implementation)

PR C: move ingestion modules + import repair
PR D: adapt ingestion to new Source/Evidence schema

PR E: move search.py to retrieval
PR F: change Object candidate / ranking behavior
```

禁止例:

```text
move importer + rewrite extraction + add Object schema
+ remove Fragment + change CLI + reformat all files
```

## 10. 検証Gate

各structural PRの最低Gate:

- `git diff --check`
- `python -m pytest -q`
- `python -m compileall -q src`
- `python -m sgokb --help`（CLIを触る場合）
- old import compatibility smoke test（shimを置く場合）
- canonical import smoke test
- package dataを動かす場合はinstalled packageから対象fileを取得できること
- DB migration pathを触る場合は既存DB / fresh DB双方のmigration smoke test

追加確認:

- `git diff --name-status`でrename / copy / modifyの意図を確認する。
- move-only commitで大規模line rewriteが発生していないことを確認する。
- repository-wide searchで新codeが旧shimへ依存していないことを確認する。

## 11. rollback方針

structural PRで問題が起きた場合、behavior migrationを巻き戻すのではなく、そのstructural PR単位でrevert可能にする。

そのため、各move PRは独立してtest可能な小さい単位を維持する。

DB schema migrationとfile moveを同一rollback単位にしない。

## 12. D-05で固定しない事項

次は後続Phaseで決定する。

- Object domain class / dataclassの具体名
- storage repository classの最終分割数
- migration fileの新規version番号
- Retrieval内部file名の最終細分化
- compatibility warningの表示方式
- legacy codeの削除時期の最終判断
- CLI command互換期間

## 13. D-05完了条件

- [x] direct move / package conversion / split / legacyの4分類を定義した。
- [x] move-onlyとbehavior changeのPR分離方法を定義した。
- [x] compatibility shimの責務と削除条件を定義した。
- [x] `domain.py` / `application.py` / `cli.py`のpackage conversion方式を定義した。
- [x] `repository.py` / `providers.py`のsplit方針を定義した。
- [x] migrations / promptsの移動条件を定義した。
- [x] Phase E〜Lへまたがる移動Waveを定義した。
- [x] test / script / package-dataの移行方針を定義した。
- [x] structural PRの検証Gateを定義した。
- [x] 実ファイルの大量moveやbehavior changeを実施していない。

次Taskは`D-06 [P1] .local / generated / Google Drive exchangeデータのGit除外方針を更新する`とする。
