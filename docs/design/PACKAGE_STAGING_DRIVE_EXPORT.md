# Source Grounded Object Knowledge Base — Package Staging / Google Drive Export

更新日: 2026-10-13

- Task: `G-04 [P0] Local Package staging / Google Drive export方式を実装する`
- Status: Complete
- Parent: Phase G — Google Drive / ChatGPT交換ワークフロー
- Prerequisites:
  - `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md`
  - `docs/design/OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`
  - `docs/design/OBJECT_ANALYSIS_INSTRUCTIONS.md`
  - `docs/decisions/SGOKB_RUNTIME_DATA_GIT_POLICY.md`
  - `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
  - `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Implementation:
  - `src/sgokb/exchange/package_transfer.py`
  - `src/sgokb/storage/exchange_repository.py`
  - `src/sgokb/migrations/010_package_exchange_audit.sql`
  - `src/sgokb/package_cli.py`
- CLI: `sgokb-package`
- Focused tests: `tests/test_package_transfer.py`
- Follow-up: G-05 Result受け取り運用

---

## 1. 目的

G-04はObject Evidence Packageの**local build/finalization**と**external export**を明確に分離する。

標準flowは次とする。

```text
Package build workspace
        ↓ validate / finalize
exchange/staging/<package_id>/
        ↓ preflight
explicit export operation
        ↓ atomic copy
Google Drive sync directory/<package_id>/
```

Package build時にGoogle Drive同期directoryへ直接書き込まない。
Google Drive同期directoryへのwriteは、Drive desktop clientがまだcloud uploadを開始していなくてもExternal Exportとして扱う。

---

## 2. 初期版ではGoogle Drive APIへ依存しない

初期標準実装はGoogle Drive API / OAuth / SDKを使用しない。

ユーザーがGoogle Drive for desktop等の同期対象directoryを`--destination`へ明示指定し、SGOKBは通常のlocal filesystem copyとしてPackageをexportする。

この方式を採用する理由:

- SGOKB本体へGoogle固有API依存を入れない。
- OAuth token / refresh token等のcredential管理をSGOKBへ持ち込まない。
- local stagingとexternal egressの境界を明確に保てる。
- Drive以外の共有directory / removable media等にも同じexport契約を再利用できる。
- 後でGoogle Drive API adapterを追加してもPackage contract自体を変更しなくてよい。

Google Drive API連携を将来追加する場合も、`PackageTransferService`のexternal destination adapterとして扱い、Package Buildと混在させない。

---

## 3. Local staging

標準staging root:

```text
exchange/staging/
```

環境変数:

```text
SGOKB_EXCHANGE_STAGING
```

finalized Package path:

```text
<staging-root>/<package_id>/
```

Object IDやObject名をfilesystem identityには使用しない。

### 3.1 build workspace

`stage`入力は、G-01〜G-03契約に従うPackage build directoryとする。

少なくとも次を含む。

```text
manifest.json
instructions.md
schema/object-result-v1.schema.json
evidence/source_NNN.md
current_object.json      # update Packageのみ
```

workspace内のfile集合は`manifest.files`と完全一致しなければならない。
未宣言fileを単に無視せず、stagingを拒否する。

これはaccidental secret / debug file /不要artifactの外部送信を防ぐためである。

### 3.2 finalize順序

`PackageTransferService.stage_from_directory()`は次を行う。

1. `manifest.json`をloadする。
2. G-02 canonicalization規則で`manifest_sha256`を再計算する。
3. manifest schema / cross-field contractを検証する。
4. workspace file集合と`manifest.files`を照合する。
5. 各fileのsize / SHA-256を照合する。
6. Result Schema snapshotがcanonical E-05 Schemaと一致することを確認する。
7. `instructions.md`のInstructions versionを確認する。
8. high-confidence credential / private-key patternを検査する。
9. staging root内の一時directoryへ全fileを書き込む。
10. `manifest.json`をfinalized値で書き込む。
11. 一時directory全体を再検証する。
12. `os.replace()`で`<package_id>/`へrenameする。

final pathはStep 12まで出現しないため、途中まで生成されたPackageを正常なfinalized Packageとして扱わない。

---

## 4. finalized Package immutability

finalized Packageは論理的にimmutableである。

同一`package_id`のstaging directoryがすでに存在する場合:

- manifest hashが同一かつintegrityが正常ならidempotentな再実行として扱える。
- 内容が異なる場合はPackage ID collisionとして拒否する。

既存Packageをin-place修正して再利用しない。
変更が必要なら新Package IDでbuildする。

filesystem permissionだけをimmutabilityの根拠にはしない。export前にhash / membership / contractを毎回再検証する。

---

## 5. Preflight

`inspect_package()` / `PackageTransferService.preflight()`はexternal export前に次を表示可能なmachine-readable summaryを返す。

```text
package_id
manifest_sha256
target_object_id
target_name
base_version_id
schema_version
evidence_count
source_count
file_count
total_bytes
destination
manifest_disposition
effective disposition
reasons
warnings
credential_findings
```

このsummaryにより、B-06で要求した次の確認項目をoperatorへ提示できる。

- Package identity
- target Object
- base Version
- file / Evidence scope
- warnings
- destination
- export decision

---

## 6. export disposition

最終dispositionは次の3値とする。

### `allow`

通常export可能。

### `review_required`

自動/暗黙exportしない。

CLIでは次の明示acknowledgementが必要。

```text
--acknowledge-review
```

### `blocked`

acknowledgementの有無に関係なくexport禁止。

次はmanifest policyが`allow`でもruntime preflightで`blocked`へ昇格する。

- manifest schema / binding不整合
- file不足 /未宣言file
- size / SHA-256 mismatch
- symlink / path escape
- Result Schema snapshot mismatch
- Instructions version mismatch
- high-confidence credential / private-key検出
- blocking warning
- destination Package ID collision

`review_required`や`blocked`をsilentに`allow`へdowngradeしない。

---

## 7. Credential / secret境界

G-02 manifestでは`credential_material_included=false`が必須である。

G-04では追加Guardとして、standard Packageのfile path / contentに対してhigh-confidence scanを行う。

対象例:

- private key PEM block
- OpenAI-style API key
- GitHub token
- AWS access key ID
- Google API key
- `.env`, `credentials.json`, private key file等のsensitive filename

このscanは完全なDLPではない。
「scanを通過したのでsecretが存在しない」と保証するものではなく、標準Packageにcredentialを入れない設計規則の追加防御である。

検出した場合はstaging finalization自体を拒否する。

---

## 8. Explicit External Export

export API:

```text
PackageTransferService.export()
```

CLI:

```text
sgokb-package export <staged-package> --destination <external-root>
```

Drive同期directoryを利用する例:

```text
sgokb-package export exchange/staging/pkg_xxx \
  --destination "G:/My Drive/SGOKB Exchange"
```

Windows上で実際のDrive同期pathが別drive letter / user pathの場合はそのpathを指定する。
SGOKBはdestination名からGoogle Driveかどうかを判定しない。

### 8.1 atomic export

exportはdestination rootへ直接fileを逐次生成しない。

```text
<destination>/.<package_id>.exporting-<uuid>/
        ↓ full copy + verify
<destination>/<package_id>/
```

一時directoryのcopy完了後、全hashを再検証してからrenameする。
同期clientが監視するfinal Package directoryはfinalize後にのみ成立する。

同期clientがtemporary directoryもuploadする可能性はあるため、Drive側の「外部に一切見えないatomic transaction」を保証するものではない。ただしSGOKBのworkflow上はtemporary directoryをvalid Packageとして扱わない。

---

## 9. Existing destination

`<destination>/<package_id>`が既に存在する場合:

- 同じmanifest hashでintegrity正常: idempotentなalready-presentとして扱う。
- hash不一致 / unreadable / integrity failure: export拒否。

既存外部Packageを上書きしない。

---

## 10. Audit persistence

Migration 010で次を追加した。

```text
package_exchange_records
package_export_events
```

### `package_exchange_records`

local staging時点のbinding metadataを保持する。

- package_id
- schema_version
- manifest_sha256
- object_id
- base_version_id
- package created/extracted time
- included Evidence IDs
- staging path
- preflight disposition / summary
- staged timestamp

### `package_export_events`

external exportをappend-only eventとして保持する。

- package_id
- destination root
- exported path
- manifest hash
- review acknowledgement有無
- already-present判定
- export timestamp

Package directoryが後でcleanupされても、最低限のbinding / export auditをSQLite側へ残せる。

---

## 11. CLI

G-04では既存legacy/canonical CLIが大きくなることを避け、exchange専用の小さなentrypointを追加する。

```text
sgokb-package stage <build-directory> [--staging-root ...]
sgokb-package preflight <staged-package> [--destination ...]
sgokb-package export <staged-package> --destination ... [--acknowledge-review]
```

`stage`と`export`はcanonical SQLite auditへ記録するため`--db`を受け取る。

`preflight`はread-onlyでありDBを変更しない。

将来Phase MでCLI全面整理を行う場合、これらをmain `sgokb package ...` treeへ統合できる。

---

## 12. Google Drive APIを追加する場合の境界

将来Google Drive API adapterを追加する場合も次を維持する。

```text
Local Package Build
    ↓
Finalized local staging
    ↓ explicit operator action
External Export Adapter
    ├─ filesystem / Drive sync folder   # G-04 initial
    └─ Google Drive API                 # optional future adapter
```

API adapterがPackage内容を再生成・再要約・変更してはならない。
manifest hash / per-file hashを維持し、upload後の確認情報をexport auditへ追加する。

---

## 13. G-04で実装したもの

1. atomic local staging。
2. finalized Package再検証。
3. machine-readable preflight。
4. `allow / review_required / blocked`処理。
5. explicit review acknowledgement。
6. credential / secret Guard。
7. atomic filesystem export。
8. Drive同期folderをExternal Export destinationとして利用可能。
9. existing destination collision / idempotency判定。
10. package staging / export audit DB。
11. dedicated `sgokb-package` CLI。
12. focused test。

---

## 14. G-04完了条件

G-04は次を満たしたためCompleteとする。

- Package BuildとExternal Exportが別操作である。
- local stagingが標準経路である。
- partial Packageをfinal pathへ露出させない。
- export前にidentity / target / Evidence / warning / destination / dispositionを確認できる。
- `review_required`は明示acknowledgementなしにexportできない。
- `blocked`はexportできない。
- credential / secretをstandard Packageへ含める防御がある。
- Drive同期directoryへのwriteを明示External Exportとして実行できる。
- Google Drive API依存を初期標準へ導入していない。
- audit metadataがSQLiteへ残る。

次のTaskはG-05 `Result受け取り運用を定義する` とする。
