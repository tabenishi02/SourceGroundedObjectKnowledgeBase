# SGOKB Runtime Data / Git Exclusion Policy

更新日: 2026-10-12

- Decision: Accepted
- Task: `D-06 [P1] .local/ / generated / Google Drive exchangeデータのGit除外方針を更新する`
- Depends on:
  - `docs/decisions/SGOKB_MODULE_RESPONSIBILITY_DESIGN.md`
  - `docs/decisions/SGOKB_MODULE_MIGRATION_POLICY.md`
  - `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
  - `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
- Scope: runtime data placement / Git tracking boundary / external exchange safety
- Out of scope: DB schema, backup implementation, Google Drive API, exact CLI/config key names

## 1. 目的

SGOKBのsource code / schema / documentationと、実ユーザーdata・生成物・外部交換dataをGit上で明確に分離する。

D-06では、次を誤ってRepositoryへcommitしないことを主目的とする。

- canonical SQLite DB
- Raw Source / Capture Artifact
- imported Result artifact / provenance-bearing runtime artifact
- Search Representation / Embedding / Vector Index
- rendered Markdown等のderived artifact
- Object Evidence Package
- ChatGPTから戻る`result.json`
- Google Drive同期対象data
- backup generation
- credential / secret
- log / temporary runtime data

同時に、Git管理すべきschema / migration / synthetic fixture / sample configuration等まで一律除外しない境界を定義する。

## 2. 基本原則

### 2.1 Git管理可否とData criticalityは別概念

`.gitignore`されていることは「消してよい」という意味ではない。

特にcanonical DB、Raw Artifact、accepted Versionへ紐づくResult provenanceはGit管理外であっても重要な保全対象であり、backup / restore対象となる。

```text
Git ignored
  != disposable
  != cache
```

Gitはsource code / schema / deterministic definition / synthetic fixtureのversion管理に使用し、ユーザーKnowledgeそのもののbackupとして使用しない。

### 2.2 Runtime dataをRepository historyへ入れない

実ユーザーdataは通常、次の理由からGit管理しない。

- 容量が大きく増える。
- Raw / Resultに著作物・個人情報・認証済みcontentが含まれ得る。
- SQLite / Index / Packageは頻繁に更新されdiffが不適切。
- Git historyから完全削除するコストが高い。
- backup / retention / restore要件とGit historyの意味が異なる。

### 2.3 Canonical / derived / transient / exchange / backupを物理的に区別する

同じdirectoryに混在させない。

D-06ではRepository内でruntime pathを使う場合の論理標準を次とする。

```text
.local/
├─ canonical/
│  ├─ db/
│  ├─ raw/
│  └─ result-artifacts/
└─ transient/
   ├─ cache/
   ├─ logs/
   └─ tmp/

generated/
├─ search-representations/
├─ embeddings/
├─ vector-index/
└─ rendered/

exchange/
├─ staging/
├─ incoming/
└─ processed/

backups/
└─ ...   # local/dev safety root only。production backupの推奨先ではない
```

これはpath responsibilityの契約であり、D-06で空directoryをGit管理することは要求しない。

## 3. `.local/`の責務

`.local/`はRepository working tree内で使用する**Git管理外runtime root**とする。

### 3.1 `.local/canonical/`

Git管理外だが、消失するとrestoreが必要になるdataを置く候補とする。

代表例:

- active SQLite DB
- Raw Capture / Raw Artifact
- accepted Knowledge Versionへ必要なoriginal Result artifact
- file-backed provenance artifact

`.local/canonical/`はcacheではない。

Production運用ではruntime data rootをRepository外へ変更可能にすることを推奨する。最終config key / Windows既定pathは後続運用設計で決定する。

### 3.2 `.local/transient/`

再実行・cleanup可能なruntime dataを置く。

代表例:

- temporary file
- process log
- PID / lock補助file
- one-off diagnostic output
- local cache

canonical dataを`.local/transient/`へ置かない。

### 3.3 既存`.local/`資産

現Repositoryではすでに`.local/`にevaluation DB、log、probe、one-off script等が多数存在する。

D-06実施時点で`.local/`は既にGit ignoreされており、tracked runtime-like fileは確認されなかった。

既存Prototypeの`.local/`をD-06で一括移動・削除しない。新設計runtimeの実装時に上記subdirectory contractへ段階移行する。

## 4. `generated/`の責務

`generated/`は**rebuildable derived artifact専用root**とする。

対象:

- Search Representation
- Embedding cache / export
- Vector Index data
- rendered Markdown
- derived report / view
- rebuild可能な補助index

禁止:

- canonical SQLite DB
- Raw Artifact
- accepted Resultの唯一の保存copy
- secret

`generated/`全体をGit管理外とする。

Derived artifactの生成手順・schema・template・builder codeはGit管理するが、生成結果そのものは原則commitしない。

## 5. `exchange/`の責務

`exchange/`は**local external-exchange workflow用のGit管理外root**とする。

```text
exchange/
├─ staging/    # local Package build完了後、まだ外部送信していないdata
├─ incoming/   # 人間が戻したResult等
└─ processed/  # Import済み等のworkflow上の一時保持
```

### 5.1 Package stagingは正本ではない

Evidence PackageはSQLite / Evidence Storeから再構築可能な交換用derived artifactである。

Package payload directory自体をKnowledge正本にしない。

package identity / hash / included Evidence ID等のaudit metadataはcanonical DB側で追跡可能にする。

### 5.2 Result incomingとaccepted provenanceを分離する

`exchange/incoming/`へ置かれた`result.json`はまだcanonical Knowledgeではない。

Validation / explicit Import後、accepted Versionのprovenanceとして保持すべきoriginal Resultは、必要に応じて`.local/canonical/result-artifacts/`等の保全領域へ不変copy / content-addressed保存する。

incoming copyを唯一の監査artifactにしない。

### 5.3 `exchange/`をGit ignoreする

PackageやResultにはSource本文・Knowledge本文が含まれるため、path単位で全体をGit管理外とする。

## 6. Google Drive exchange方針

### 6.1 Google DriveはRepositoryの一部にしない

Google Drive同期directoryは**原則としてGit working treeの外部path**を使用する。

理由:

- DriveはExternal Export boundaryである。
- Git trackingとcloud syncを同じdirectoryへ重ねる必要がない。
- accidental add / rename / delete propagationを減らせる。
- Repository cloneだけでexternal exchange dataを復元すべきではない。

具体的なDrive destination pathはPhase Gで設定として確定する。

### 6.2 Drive同期directoryへのwriteはExternal Export

B-06どおり、Google Drive同期directoryへfileを書き込むこと自体をExternal Exportとして扱う。

```text
exchange/staging/       # local only
        ↓ explicit export
Google Drive directory  # external egress
```

Package build時に直接Google Driveへ生成することを標準にしない。

### 6.3 Repository内Drive syncは推奨しない

何らかの理由でRepository working tree内に同期directoryを置く場合でも、必ずGit ignoreされた`exchange/`配下等に限定する。

ただし、初期標準運用はRepository外のDrive pathを推奨する。

## 7. `backups/`の責務

`backups/`は誤commit防止のためrootごとGit ignoreする。

ただし、Repository直下`backups/`をproduction backupの唯一の保存先としてはならない。

B-07の要件どおり、backupはactive data directoryと分離し、可能なら別physical device / NAS等へのcopyを持てる設計とする。

Repository内`backups/`は次の用途に限定できる。

- development restore test
- temporary manual backup
- migration dry-runの作業copy

Production backup destinationはRepository外pathを設定可能にし、RPO / retention / restore検証は後続運用実装で扱う。

## 8. Git管理するもの

次は原則Git管理対象とする。

### 8.1 Source code / deterministic definitions

- `src/`
- `extensions/`
- migration SQL
- JSON Schema
- template / prompt definition（現行仕様として必要なもの）
- deterministic registry seed
- config schema
- `.env.example`等のsecretを含まないtemplate

### 8.2 Documentation

- `README.md`
- `docs/`
- current architecture / requirement / decision / operation documentation
- archiveとして意図的に残す歴史資料

### 8.3 Synthetic fixture / test data

Git管理するfixtureは次の条件を満たすものに限定する。

- syntheticまたは再配布権が明確
- secret / token / cookie /個人情報を含まない
- 小容量
- deterministic testに必要
- purposeがtestから明確

推奨配置:

```text
tests/fixtures/
examples/
benchmark/*.example.json
```

実ユーザーSource corpusをfixtureという名前だけでGit管理へ昇格させない。

## 9. root `sample/`の扱い

現行root `sample/`は実験・評価用の大容量local corpusを含み、すでにGit ignoreされている。

D-06ではこの扱いを維持する。

今後Git管理が必要な小さなsynthetic sampleを追加する場合は、root `sample/`をunignoreするのではなく、`tests/fixtures/`または`examples/`へ明示的に作成する。

これにより、実データと公開可能test fixtureを物理的に分離する。

## 10. Secret / local configuration

### 10.1 Git管理禁止

少なくとも次をGit管理しない。

- `.env`
- `.env.*` local variant
- `.secrets/`
- local credential file
- API key / OAuth token / refresh token
- browser cookie / session material
- private key

`.env.example`はsecret valueを含まない場合のみGit管理可能とする。

### 10.2 `.gitignore`はsecret protectionの唯一の防御ではない

`.gitignore`は誤commit防止策であり、すでにtrackedになったsecretを保護しない。

secretを誤commitした場合は、ignore追加だけで完了とせずcredential revoke / rotationと履歴対応を行う。

## 11. SQLite / DB file

DB filenameに依存せずruntime DBをGit管理外とするため、次をignoreする。

- `*.sqlite*`
- `*.db`
- `*.db-wal`
- `*.db-shm`
- `*.db-journal`

DB schemaそのものはmigration SQL / schema definitionとしてGit管理する。

TestにSQLite binary fixtureがどうしても必要な場合はglobal ignoreを解除せず、具体的なfixture pathを個別レビューして例外追加する。

## 12. `.gitignore`の確定ルール

D-06でroot `.gitignore`に少なくとも次を明示する。

```gitignore
# Historical / local corpora
old/
sample/

# Runtime / private state
.local/
/generated/
/exchange/
/backups/

# Python local environment / cache
.venv/
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/

# Secrets / local overrides
.env
.env.*
!.env.example
.secrets/
config.local.*
credentials.local.*

# Runtime databases / SQLite journals
*.sqlite*
*.db
*.db-wal
*.db-shm
*.db-journal

# Build artifacts
dist/
build/
```

Path rootを明示した`/generated/`等は、source package内部に将来同名moduleができた場合まで誤ってignoreしないためroot限定とする。

## 13. 既にtrackedされたfileへの注意

`.gitignore`はすでにGit indexへ登録済みのfileを自動的にuntrackしない。

runtime dataが誤ってtrackedされた場合は、内容と履歴影響を確認してから`git rm --cached`等を使用する。

D-06実施時点のauditでは、`.local / generated / exchange / backup / runtime DB`に該当するtracked fileは確認されなかったため、既存tracked dataの削除操作は行わない。

## 14. Commit前Guard

今後の大規模実装PRでは少なくとも次を確認する。

```text
git status --short
git diff --cached --name-only
```

特に次のpath / extensionがstageされていないことを確認する。

- `.local/`
- `generated/`
- `exchange/`
- `backups/`
- `*.sqlite*`
- `*.db*`
- `.env*`（`.env.example`を除く）

将来CI / pre-commitを導入する場合はruntime path検出を機械的Guardへ追加できる。

## 15. D-06で実施する変更

D-06では次を行う。

1. Runtime data / Git exclusion Decisionを本書へ固定する。
2. root `.gitignore`へ`/generated/`, `/exchange/`, `/backups/`等を追加する。
3. `.env.*` / `.secrets/` / local overrideを追加保護する。
4. SQLite journal fileの除外を明確化する。
5. Documentation Index / Task master / Handoff / Phase D preparationを更新する。
6. Runtime dataの実移動は行わない。
7. Google Driveへの実file exportは行わない。
8. backup generationを新規作成・削除しない。

## 16. 後続Phaseへの引き継ぎ

### Phase E / F

- active DB / Raw Artifact pathは本方針に従いGit管理外とする。
- production runtime data rootをRepository外へ置く場合のconfigを実装時に具体化する。

### Phase G

- `exchange/staging`とGoogle Drive destinationを分離する。
- Google Drive pathを明示configにする。
- export操作がexternal egressであることを維持する。
- `exchange/incoming` / Result受付pathを具体化する。

### Phase H

- accepted Result original artifactのcanonical/provenance-retained保存先を具体化する。
- incoming Result cleanupと監査artifact保全を分離する。

### Phase I

- Search Representation / Embedding / Vector Indexを`generated/`相当のrebuildable rootへ置く。
- Vector backendのdata directoryをcanonical DB pathと混同しない。

### Phase N

- production DB / Raw storeを直接test対象へ書き込まない。
- test fixtureはisolated temp directoryまたは`tests/fixtures/`のsynthetic dataを使用する。
- backup restore / index rebuild試験でruntime path separationを検証する。

## 17. D-06完了条件

- [x] `.local/`のruntime責務を定義した。
- [x] canonical / transient / generated / exchange / backupを物理的に区別した。
- [x] Google Drive destinationをRepository外pathとする標準方針を定義した。
- [x] Package / Result / DB / Raw / Vector Index / backupのGit管理境界を定義した。
- [x] root `sample/`をlocal corpusとしてignore維持し、Git管理fixtureとの境界を定義した。
- [x] secret / local configの除外方針を定義した。
- [x] `.gitignore`更新内容を確定した。
- [x] 既存tracked runtime dataがないことを確認した。
- [x] runtime dataの実移動やexternal exportを行っていない。

次Taskは`D-07 [P1] 旧branch / PR / tag / releaseの整理ルールを決める`とする。
