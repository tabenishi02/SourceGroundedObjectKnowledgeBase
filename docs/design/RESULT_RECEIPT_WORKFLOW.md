# Source Grounded Object Knowledge Base — Result Receipt Workflow

更新日: 2026-10-13

- Task: `G-05 [P1] Result受け取り運用を定義する`
- Status: Complete
- Parent: Phase G — Google Drive / ChatGPT交換ワークフロー
- Prerequisites:
  - `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md`
  - `docs/design/OBJECT_EVIDENCE_PACKAGE_MANIFEST_SCHEMA.md`
  - `docs/design/OBJECT_ANALYSIS_INSTRUCTIONS.md`
  - `docs/design/PACKAGE_STAGING_DRIVE_EXPORT.md`
  - `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`
  - `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
  - `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Implementation:
  - `src/sgokb/exchange/result_receipt.py`
  - `src/sgokb/storage/exchange_repository.py`
  - `src/sgokb/migrations/011_result_receipts.sql`
  - `src/sgokb/package_cli.py`
- Focused tests: `tests/test_result_receipt.py`
- Follow-up:
  - H-01 Result JSON Validator
  - H-02 Object Version Import

---

## 1. 目的

G-05は、Google Drive / ChatGPTの手動工程から戻ってきたObject Resultを、SGOKBへ**受領しただけのartifact**として安全に保持し、H-01 Validationへ渡すまでの運用を確定する。

最重要境界は次である。

```text
Result detected
  != Result validated
  != Knowledge imported
```

標準Workflow:

```text
finalized / exported Package
        ↓ human uses ChatGPT
ChatGPT returns result.json
        ↓ human returns file
exchange/incoming/drop/<package_id>/result.json
        ↓ detect / receive
exchange/incoming/received/<package_id>/<receipt_id>/result.json
        ↓ validation_state = pending
H-01 Validation / Diff
        ↓ human explicit Import
H-02 Version Import
```

Resultを検出・受領しただけでは、Object Knowledge Versionを作成せず、`current_version`も変更しない。

---

## 2. `result.json`を唯一の標準Result artifactとする

標準受領artifactはexact filename:

```text
result.json
```

とする。

ChatGPTがMarkdown summary、説明文、`result.md`等を追加で生成しても、それらをKnowledge交換正本にはしない。

```text
result.json  = machine exchange source
Markdown     = optional human-facing side artifact
```

G-05のstandard receipt operationは`result.json`だけを受け取る。
Markdownを保存したい場合は別のhuman artifactとして扱い、H-01/H-02のValidation / Import入力には使用しない。

---

## 3. exported Package directoryへResultを書き込まない

G-04でfinalized Packageはimmutableとした。

したがって、Google Drive上の

```text
<external-root>/<package_id>/
```

へ`result.json`を追加してはならない。

Packageへfileを追加すると、G-04の「manifestで宣言されたfile集合とactual file集合が一致する」integrity contractを壊すためである。

ResultはPackageとは独立したincoming artifactとして返す。

推奨手動配置場所:

```text
exchange/incoming/drop/<package_id>/result.json
```

環境変数:

```text
SGOKB_EXCHANGE_INCOMING
```

既定root:

```text
exchange/incoming
```

ユーザーがDownloads等の別pathへ`result.json`を保存した場合も、`receive` commandへそのfileを直接指定できる。

---

## 4. Detection

read-only detection command:

```text
sgokb-package detect
```

`detect`は次のpatternだけを候補として列挙する。

```text
<incoming-root>/drop/<package_id>/result.json
```

表示項目:

```text
package_hint
path
byte_count
result_sha256
package_known
already_received
```

Detectionはfileをmove / copy / deleteせず、DBにもreceiptを作成しない。

このためfilesystem watcherを将来追加しても、Detectionそのものは安全なread operationとして利用できる。

---

## 5. Receipt

標準受領command:

```text
sgokb-package receive <path-to-result.json> --package-id <package_id>
```

例:

```text
sgokb-package receive \
  exchange/incoming/drop/pkg_xxx/result.json \
  --package-id pkg_xxx
```

`receive`は指定PackageがG-04でstaged / auditedされていることを要求する。

受領後のimmutable local path:

```text
exchange/incoming/received/<package_id>/<receipt_id>/result.json
```

`receipt_id`は1回の受領attemptを識別するlocal UUIDであり、Object Version IDではない。

### 5.1 raw bytesを保持する

`receive`はResultを整形・Schema修正・JSON再serializeせず、受け取ったbytesをそのままcopyする。

保持するaudit metadata:

```text
receipt_id
package_id
result_sha256
byte_count
storage_ref
intake_state
intake_findings
parsed routing fields
validation_state
validation_requested_at
received_at
```

Result hashはbyte-level SHA-256とする。

### 5.2 atomic receipt

copyは一時directoryへ書き込み、hashを再確認してからfinal receipt directoryへ`os.replace()`する。

途中fileをvalid receiptとして見せない。

### 5.3 duplicate / retry

同一Package + 同一Result SHA-256を再度receiveした場合、新しいreceiptを増やさずidempotent再実行として扱う。

同一Packageから異なるResult bytesが戻った場合は別receiptとして保持する。

```text
Package A
├─ Receipt 1 / result.json
├─ Receipt 2 / result.json
└─ Receipt 3 / result.json
```

これによりChatGPT再試行結果を上書きしない。

---

## 6. Intake checkとH-01 Validationを分離する

G-05の`receive`は**H-01 Validatorではない**。

G-05で行うのはrouting / intakeに必要な軽量checkだけである。

可能な場合、受領Resultから次を読み、G-04 audit / staged manifestと比較する。

```text
schema_version
target.object_id
target.primary_class_id
target.additional_class_ids
binding.package_id
binding.package_schema_version
binding.manifest_sha256
binding.package_created_at
binding.base_version_id
generation.instructions_version
```

これは「このResultがどのPackageの返却物として見えるか」を早期確認するためであり、Resultがauthoritativeにvalidであることを意味しない。

H-01では改めて次を完全検証する。

- JSON syntax / canonical Schema
- Package binding
- base Version / stale precondition
- Object / Class / Facet / Attribute / Relation ID
- Evidence existence / Package membership
- Grounding / Provenance
- domain contract

G-05のintake checkをH-01の代用にしない。

---

## 7. malformed / mismatched Resultも原則保存する

ChatGPT返却物がJSON syntax error等を含む場合、受領artifactそのものを失うべきではない。

G-05では次を区別する。

### `ready_for_validation`

routing上の明白な異常が見つからなかった。

これはH-01 validation成功を意味しない。

### `needs_review`

例:

- invalid UTF-8
- invalid JSON
- top-levelがJSON objectではない
- Package binding routing mismatch
- staged manifestが確認できない / hash不一致
- Package export auditが存在しない

`needs_review`でもartifactはimmutable receiptとして保存し、`validation_state=pending`とする。

H-01はsyntax errorを含め正式なValidation Resultを生成できる。

---

## 8. Validation trigger

Receipt作成成功時、Migration 011の`package_result_receipts`へ次を記録する。

```text
validation_state = pending
validation_requested_at = <receipt time>
```

これをH-01のValidation trigger contractとする。

確認command:

```text
sgokb-package pending-validation
```

H-01実装後は、

- `receive`直後に同期Validationする
- local workerがpending receiptを処理する
- filesystem watcherがdetect → receive → Validationする

のいずれも実装可能である。

ただし、どの方式でもValidation完了をauthoritative Import triggerにしない。

---

## 9. Import boundary

Result receipt tableの`validation_state`は、Knowledge lifecycle stateではない。

```text
receipt pending
  ↓ H-01
valid / invalid
  ↓ user review / explicit command
H-02 Import
```

標準初期Workflowでは、`valid`になっても自動で次を実行しない。

- Version ID発行
- Object Version作成
- `current_version`切替
- Registry proposal適用
- Search / Embedding更新

これらはH-02以降のexplicit Import boundaryで行う。

---

## 10. Failure / retry operation

### 10.1 ChatGPTからResultが返らない

SGOKB側ではreceiptを作らない。

Package audit / export historyは残るため、同じPackageを再度ChatGPTへ渡してよい。

Source / current Knowledgeが変化した場合は同じPackageを使わず、新Packageをbuildする。

### 10.2 JSONが壊れている

`needs_review` receiptとして保持する。
H-01でinvalidとして扱い、必要なら同じPackageから再生成する。

### 10.3 Package ID / manifest hashが違う

artifactは保持するが`needs_review`とする。

SGOKBが推測で別Packageへrebindしない。
正しいPackage IDを確認し、必要なら正しいResultを再返却する。

### 10.4 stale Result

G-05ではstaleかどうかを確定しない。
H-01がcurrent/base Version preconditionを検証し、staleなら通常Importをblockする。

### 10.5 同じPackageから複数Resultが返る

別hashなら別receiptとして保持する。
H-02ではユーザーが明示的に選んだvalidated receiptだけをImport対象とする。

### 10.6 Resultを手で修正した

bytesが変わるため別Result artifact /別receiptとする。
過去receiptをin-place編集しない。

---

## 11. Result size / untrusted input

Resultはexternal AIから戻るuntrusted inputである。

初期実装では1 Result artifactの上限を次とする。

```text
16 MiB
```

標準receiptでは次を拒否する。

- `result.json`以外のfilename
- symlink
- regular fileでない入力
- size上限超過
- 未知 /未staged Package ID

JSON内容自体をcommand、path、filesystem instructionとして実行しない。

H-01 ValidatorもResult contentをuntrusted dataとして扱う。

---

## 12. Audit schema

Migration:

```text
src/sgokb/migrations/011_result_receipts.sql
```

主要table:

```text
package_result_receipts
```

1 row = 1 immutable Result receipt attempt。

`UNIQUE(package_id, result_sha256)`により同一artifactの重複受領を抑制する。

`validation_state`はH-01とのhandoff用に次を予約する。

```text
pending
running
valid
invalid
error
```

G-05自身はreceipt作成時に`pending`を設定するところまでを担当する。

---

## 13. CLI

Phase Gのexchange CLIを次へ拡張する。

```text
sgokb-package stage
sgokb-package preflight
sgokb-package export
sgokb-package detect
sgokb-package receive
sgokb-package receipts
sgokb-package pending-validation
```

### standard round trip

```text
1. sgokb-package stage ...
2. sgokb-package preflight ...
3. sgokb-package export ...
4. Human: ChatGPTへPackageを渡す
5. Human: result.jsonを取得
6. result.jsonを exchange/incoming/drop/<package_id>/ に置く
7. sgokb-package detect
8. sgokb-package receive ... --package-id ...
9. sgokb-package pending-validation
10. H-01 Validation
11. Human explicit Import
12. H-02 Import
```

G-05時点ではStep 10以降を実行しない。

---

## 14. G-05完了条件

G-05は次を満たしたためCompleteとする。

1. `result.json`を唯一の標準Result artifactとした。
2. exported PackageとResult返却場所を分離した。
3. manual drop directoryを定義した。
4. read-only Result detectionを定義・実装した。
5. immutable / hash付きreceiptを定義・実装した。
6. 同一Result retryをidempotent化した。
7. 同一Packageの複数Result attemptを保持可能にした。
8. intake routing checkとH-01 Validationを分離した。
9. malformed Resultも監査可能な形で保持する方針を確定した。
10. `validation_state=pending`をH-01 trigger contractとして確定した。
11. Result検出 / receipt / Validation成功がauthoritative Importを起動しないことを固定した。
12. Google Drive / ChatGPT手動工程の開始・返却・失敗 / retry運用を1 Object / 1 Package単位で定義した。

これによりPhase Gの標準Human-in-the-loop round tripは、H-01/H-02の実装前でも責務境界まで確定した。
