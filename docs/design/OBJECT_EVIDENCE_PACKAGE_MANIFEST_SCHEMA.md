# Source Grounded Object Knowledge Base — Object Evidence Package Manifest Schema

更新日: 2026-10-13

- Task: `G-02 [P0] manifest.json schemaを定義する`
- Status: Complete
- Parent: Phase G — Google Drive / ChatGPT交換ワークフロー
- Prerequisites:
  - `docs/design/OBJECT_EVIDENCE_PACKAGE_FORMAT.md`
  - `docs/design/OBJECT_RESULT_JSON_SCHEMA.md`
  - `docs/design/EVIDENCE_SELECTION_BUDGET.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Canonical Schema: `src/sgokb/exchange/schemas/object-evidence-package-v1.schema.json`
- Validation helper: `src/sgokb/exchange/package_manifest.py`
- Follow-up:
  - G-03 `instructions.md`
  - G-04 local Package staging / Google Drive export
  - G-05 Result受け取り運用

---

## 1. 目的

`manifest.json`はObject Evidence Packageのmachine-readableなindex、Package membershipの正本、Object Result bindingの起点である。

G-02ではG-01で決定したPackage layoutを機械検証可能な契約へ固定する。

`manifest.json`は次を答えられなければならない。

- どのPackageか。
- どのObjectを対象にしたか。
- どのObject Classificationを前提にしたか。
- どのcurrent Knowledge Versionをbaseとしたか。
- どのResult Schema / instructionsを期待するか。
- どのSource generation / EvidenceをChatGPTへ渡したか。
- 各EvidenceがPackage内のどのfileに入っているか。
- なぜそのEvidenceがPackageへ入ったか。
- Evidence Selection budgetをどのように使用したか。
- Package fileが改変されていないか。
- External Export前にreview / block理由があるか。

Package directoryやGoogle Drive pathそのものをIdentityにはしない。

---

## 2. Schema identity

Package manifest v1を次で固定する。

```text
schema_version = sgokb.object-evidence-package/1.0
JSON Schema $id = urn:sgokb:schema:object-evidence-package:1.0
JSON Schema dialect = Draft 2020-12
```

Canonical Schemaは次の1ファイルとする。

```text
src/sgokb/exchange/schemas/object-evidence-package-v1.schema.json
```

`additionalProperties: false`を基本とし、ChatGPT / local tool / future adapterが未知fieldを追加してもsilentに受理しない。

E-05でObject Result bindingの仮値として使われていたPackage schema versionは、G-02以降この`sgokb.object-evidence-package/1.0`を正式値とする。

---

## 3. Package identity

### 3.1 `package_id`

初期Package IDは次の形式とする。

```text
pkg_<UUIDv4>
```

例:

```text
pkg_123e4567-e89b-42d3-a456-426614174000
```

Package IDは次から独立する。

- Object ID
- directory path
- Google Drive path
- manifest hash
- Evidence hash
- created timestamp

同じObject /同じEvidence集合から再buildしても、新しいfinalized Packageは新しい`package_id`を持つ。

`package_id`は内容同一性hashではなく、1回のPackage build artifactを追跡するstable exchange identityである。

### 3.2 `created_at` / `extracted_at`

時間概念を次のように分離する。

- `extracted_at`: canonical DB / Evidence StoreからPackage入力snapshotを取得した時点。
- `created_at`: manifest / filesをfinalizeしPackage artifactを成立させた時点。

Source publication time、Snapshot capture time、Evidence generation timeとは別概念である。

---

## 4. Top-level schema

Manifest v1のtop-level構造を次とする。

```text
manifest.json
├─ schema_version
├─ package_id
├─ created_at
├─ extracted_at
├─ target
├─ binding
├─ artifacts
├─ evidence
├─ selection
├─ files
├─ warnings
├─ export_preflight
└─ integrity
```

すべてのtop-level fieldを必須とする。

空でよいcollectionもfieldを省略せず、`warnings: []`等として明示する。

---

## 5. `target`

`target`は分析対象ObjectのPackage作成時点snapshotである。

```json
{
  "object_id": "...",
  "primary_class_id": "class:character",
  "additional_class_ids": ["class:fictional_entity"],
  "name": "...",
  "aliases": ["..."]
}
```

### 5.1 Identity / Classification

次を必須とする。

- `object_id`
- `primary_class_id`
- `additional_class_ids`

ResultはこのClassification snapshotをechoし、H-01でPackage / current Registryと照合する。

### 5.2 `name` / `aliases`

`name` / `aliases`はChatGPTの検索・同定contextとして含める。

ただしResultが返した文字列でObject Registryを自動更新しない。変更候補はE-05の`registry_proposals`契約を使う。

---

## 6. `binding`

```text
binding
├─ base_version_id
├─ expected_result_schema_version
└─ instructions_version
```

### 6.1 `base_version_id`

更新Packageではcurrent accepted Knowledge Version IDを入れる。

初回Knowledge生成では`null`とする。

```text
base_version_id = null
  -> initial Package

base_version_id = <version-id>
  -> update Package
```

### 6.2 `expected_result_schema_version`

G-02時点では次に固定する。

```text
sgokb.object-result/1.0
```

ChatGPT Resultの`schema_version`とは別に、Resultの`binding.package_schema_version`には本Packageの`schema_version`をechoさせる。

### 6.3 `instructions_version`

G-03で確定するPackage-local instructions contract versionを記録する。

G-02ではnon-empty stringを要求し、具体値はG-03へ残す。

---

## 7. `artifacts`

Package v1の固定artifact pathをmanifestへ明示する。

```json
{
  "instructions_path": "instructions.md",
  "result_schema_path": "schema/object-result-v1.schema.json",
  "current_object_path": null
}
```

更新Packageでは:

```json
{
  "current_object_path": "current_object.json"
}
```

### 7.1 initial / update invariant

Cross-field contractとして次を必須とする。

```text
base_version_id == null
  -> current_object_path == null
  -> files[]にcurrent_object roleを含めない

base_version_id != null
  -> current_object_path == "current_object.json"
  -> files[]にcurrent_object roleをちょうど1件含める
```

JSON Schemaだけではなく`validate_package_manifest()`でこのcross-field invariantを検証する。

---

## 8. Evidence membership

`evidence`は当該PackageでChatGPTが引用可能なEvidence集合の正本である。

```text
evidence
├─ included_source_ids[]
├─ included_evidence_ids[]
├─ source_generations[]
└─ items[]
```

### 8.1 `included_evidence_ids`

この配列に存在するEvidenceだけを標準Resultのgrounding対象とする。

DBに存在していてもPackageに含まれないEvidenceは、当該Resultから引用してはならない。

`included_evidence_ids`は`items[].evidence_id`と**順序を含め完全一致**させる。

この順序はPackage selection / serializationの再現に利用する。

### 8.2 `included_source_ids`

`items[]`のfirst-seen Source順と一致させる。

Source数を真実性・Source trustのscoreとはみなさない。

### 8.3 omitted Evidenceをmanifestへ列挙しない

F-03 candidateだったがF-04でbudget / duplicate / overlap等により除外されたEvidenceの詳細は、local audit側に保持する。

External Package manifestには、次だけを置く。

- included Evidence
- candidate / selected / omittedの件数
- selection budget / usage

omitされたEvidence IDをmanifestへ大量に載せ、「Package membership」と誤認できる形式にはしない。

---

## 9. Source generation mapping

G-01どおりEvidence payload fileのgrouping keyを次とする。

```text
(source_id, snapshot_id, normalization_run_id)
```

`source_generations[]`はこのgroupとPackage fileを対応付ける。

```json
{
  "source_id": "...",
  "snapshot_id": "...",
  "normalization_run_id": "...",
  "file_path": "evidence/source_001.md",
  "evidence_ids": ["..."]
}
```

同じEvidence IDを複数generationへ所属させない。

`items[]`のSource / Snapshot / Run / file mappingと`source_generations[]`が完全一致することをapplication-level validationで確認する。

---

## 10. Evidence item selection provenance

各Evidence itemには少なくとも次を保持する。

```text
evidence_id
source_id
snapshot_id
normalization_run_id
file_path
selected_by
package_roles[]
retrieval_reasons[]
related_selected_evidence_ids[]
```

### 10.1 `selected_by`

F-04のselection stageをそのまま保持する。

```text
protected
source_diversity
relevance_fill
```

### 10.2 `package_roles`

Packageへ入る理由を、F-03 retrieval reasonと分離する。

```text
carry_forward
manual_include
retrieved
```

1 Evidenceは複数roleを同時に持てる。

例:

```text
[carry_forward, retrieved]
```

### 10.3 protected invariant

次を含むEvidenceは`selected_by = protected`でなければならない。

- `carry_forward`
- `manual_include`

これによりG-01の「旧Knowledge grounding / manual includeをbudget理由でsilent omissionしない」契約をmanifest上から監査できる。

### 10.4 `retrieval_reasons`

F-03で確定したchannelを保持する。

```text
explicit_association
name
alias
source_metadata
lexical
semantic
manual
```

carry-forward historical Evidence等、retrieval channelを持たない場合は空arrayを許容する。

`retrieval_score`自体はPackage外へ必須出力しない。ranking scoreをtruth / confidenceと誤認させないためである。

---

## 11. Evidence Selection budget

F-04のbudget contractをmanifestへそのまま記録する。

```text
selection
├─ token_estimator
├─ budget
│  ├─ max_estimated_tokens
│  ├─ max_bytes
│  └─ max_items
├─ usage
│  ├─ estimated_tokens
│  ├─ bytes
│  ├─ items
│  └─ sources
├─ candidate_count
├─ selected_count
└─ omitted_count
```

`token_estimator` v1は次で固定する。

```text
ascii_div4_plus_non_ascii_v1
```

G-02で新しいPackage全体budgetを重ねて定義しない。

`selection`はF-04 Evidence payload budgetを表し、`instructions.md` / `current_object.json` / Result Schema等のoverheadは`files[].size_bytes`で別途追跡する。

G-03 / G-04でChatGPT投入全体のtoken preflightが必要になった場合も、F-04 Evidence budgetの意味を変更しない。

Cross-field validationとして次を確認する。

```text
selected_count == len(evidence.items)
usage.items == len(evidence.items)
usage.sources == unique included Source count
```

---

## 12. `files[]`とArtifact integrity

`files[]`は`manifest.json`自身を除くPackage artifact一覧とする。

```text
files[]
  path
  role
  media_type
  size_bytes
  sha256
```

role:

```text
instructions
current_object
result_schema
evidence
```

### 12.1 manifest自身を`files[]`へ含めない

`manifest.json`自身をper-file hash listへ入れるとself-referenceが発生するため、manifestは`files[]`へ含めない。

Manifest integrityは後述`manifest_sha256`で独立して検証する。

### 12.2 relative safe pathのみ許可する

Package file pathはPOSIX-style Package-relative pathとして扱う。

次を拒否する。

- absolute path
- `..` traversal
- Windows `\\` separator
- Package root外参照

Local absolute DB / Raw pathをmanifestへ出力しない。

### 12.3 per-file SHA-256

各fileの実byte列についてSHA-256を保存する。

これによりGoogle Drive同期・手動copy後も、Package artifactの改変・欠損を検出できる。

---

## 13. Manifest hash / canonicalization

### 13.1 問題

`manifest_sha256`をmanifest自身の通常byte列から計算すると、hash値を書き込むことでbyte列が変わりself-referenceになる。

### 13.2 採用方式

SGOKB独自の最小canonicalization profileを次で固定する。

```text
sgokb-json-c14n-v1
```

Hash projection:

1. Manifest objectをdeep copyする。
2. `integrity.manifest_sha256`だけを除去する。
3. 残りをJSONとしてserializationする。
4. UTF-8 byte列にする。
5. SHA-256を計算する。

Serialization条件:

```text
sort_keys = true
ensure_ascii = false
separators = (",", ":")
allow_nan = false
```

Array orderは保持する。

この方式はRFC 8785等の外部canonicalization standardを名乗らず、SGOKB v1内部contractとして固定する。

### 13.3 manifest hashがbindする範囲

Manifestには各Package fileのSHA-256が含まれるため、`manifest_sha256`は間接的に次をbindする。

- target Object / Classification
- base Version
- instructions version
- included Evidence membership
- Source generation mapping
- Evidence selection provenance
- budget / usage
- file path / size / SHA-256
- warnings / preflight state

したがってE-05 Object Resultの`binding.manifest_sha256`を、Package→Resultの主要immutability preconditionとして利用できる。

---

## 14. Object Result bindingとの接続

Object Result v1のbindingは次を要求する。

```text
package_id
package_schema_version
manifest_sha256
package_created_at
base_version_id
```

G-02 Manifestとの対応は次で固定する。

| Object Result | manifest.json |
|---|---|
| `package_id` | `package_id` |
| `package_schema_version` | `schema_version` |
| `manifest_sha256` | `integrity.manifest_sha256` |
| `package_created_at` | `created_at` |
| `base_version_id` | `binding.base_version_id` |

H-01はこの5項目をPackageとResult間で完全一致させる。

Target Object / Classification、Evidence membershipも別途照合する。

---

## 15. warnings / export preflight

### 15.1 `warnings[]`

Package Build時の非fatal / review情報を構造化する。

```text
code
severity
message
```

severity:

```text
info
warning
review_required
blocking
```

全文Evidenceやsecretをwarning messageへ複製しない。

### 15.2 `export_preflight`

B-07の3状態を採用する。

```text
allow
review_required
blocked
```

`review_required` / `blocked`ではreasonを1件以上必須とする。

### 15.3 credential assertion

標準Packageはcredential / secretを含めてはならないため、Manifest contractは次を要求する。

```json
"credential_material_included": false
```

これは「scannerが絶対に見落とさない」という意味ではなく、Package Builderが標準Packageとしてfinalizeする際に満たすべきassertionである。

具体的secret scan / policy判定はG-04へ残す。

### 15.4 destinationをmanifestへ書かない

PackageはExternal Export前にfinalizeされimmutableとなる。

そのため次はmanifestへ書き込まない。

- Google Drive destination
- export timestamp
- export outcome

これらはG-04のPackage Export audit metadataとしてlocal側へ記録する。

Destinationを変えるたびにPackage manifestを書き換えてhashを壊す設計にはしない。

---

## 16. Structural validationとDomain contract validation

G-02では2段階validationを採用する。

### 16.1 JSON Schema validation

Canonical JSON Schemaで次を検証する。

- required field
- type
- closed object / unknown field rejection
- enum / const
- UUIDv4 Package ID pattern
- RFC 3339 date-time format
- SHA-256 hex形式
- Evidence file名pattern
- minItems / uniqueItems

### 16.2 Cross-field contract validation

`validate_package_manifest()`で次を検証する。

- initial / updateと`current_object.json`整合。
- required singleton fileの存在。
- safe relative path。
- `included_evidence_ids`と`items[]`の完全一致。
- `included_source_ids`とEvidence item Source集合の整合。
- Source generation mapping。
- Evidence payload file存在。
- carry-forward / manual includeのprotected状態。
- selection count / usage count整合。
- review / block reason存在。
- `manifest_sha256`整合。

DB上のObject / Version / Evidence存在確認やProvenance integrity確認はPackage Builder / H-01 storage validation側で行う。

G-02 exchange layerへSQLite依存を持ち込まない。

---

## 17. Example

概略例:

```json
{
  "schema_version": "sgokb.object-evidence-package/1.0",
  "package_id": "pkg_123e4567-e89b-42d3-a456-426614174000",
  "created_at": "2026-10-13T00:00:10Z",
  "extracted_at": "2026-10-13T00:00:00Z",
  "target": {
    "object_id": "object-1",
    "primary_class_id": "class:character",
    "additional_class_ids": [],
    "name": "Character A",
    "aliases": []
  },
  "binding": {
    "base_version_id": null,
    "expected_result_schema_version": "sgokb.object-result/1.0",
    "instructions_version": "sgokb.object-analysis/1.0"
  },
  "artifacts": {
    "instructions_path": "instructions.md",
    "result_schema_path": "schema/object-result-v1.schema.json",
    "current_object_path": null
  },
  "evidence": {
    "included_source_ids": ["source-1"],
    "included_evidence_ids": ["evidence-1"],
    "source_generations": [
      {
        "source_id": "source-1",
        "snapshot_id": "snapshot-1",
        "normalization_run_id": "run-1",
        "file_path": "evidence/source_001.md",
        "evidence_ids": ["evidence-1"]
      }
    ],
    "items": [
      {
        "evidence_id": "evidence-1",
        "source_id": "source-1",
        "snapshot_id": "snapshot-1",
        "normalization_run_id": "run-1",
        "file_path": "evidence/source_001.md",
        "selected_by": "relevance_fill",
        "package_roles": ["retrieved"],
        "retrieval_reasons": ["lexical"],
        "related_selected_evidence_ids": []
      }
    ]
  },
  "selection": {
    "token_estimator": "ascii_div4_plus_non_ascii_v1",
    "budget": {
      "max_estimated_tokens": 12000,
      "max_bytes": 65536,
      "max_items": 64
    },
    "usage": {
      "estimated_tokens": 100,
      "bytes": 1000,
      "items": 1,
      "sources": 1
    },
    "candidate_count": 1,
    "selected_count": 1,
    "omitted_count": 0
  },
  "files": [],
  "warnings": [],
  "export_preflight": {
    "disposition": "allow",
    "reasons": [],
    "credential_material_included": false
  },
  "integrity": {
    "hash_algorithm": "sha256",
    "canonicalization": "sgokb-json-c14n-v1",
    "manifest_sha256": "<64 lowercase hex>"
  }
}
```

上記は説明用の省略例であり、実manifestでは`files[]`へinstructions / Result Schema / Evidence payloadの全artifactを列挙する。

---

## 18. 実装

G-02で追加した実装:

```text
src/sgokb/exchange/schemas/object-evidence-package-v1.schema.json
src/sgokb/exchange/package_manifest.py
tests/test_package_manifest.py
```

`package_manifest.py`は少なくとも次を提供する。

- `PACKAGE_SCHEMA_VERSION`
- `PACKAGE_SCHEMA_ID`
- `MANIFEST_CANONICALIZATION`
- `load_package_manifest_schema()`
- `new_package_id()`
- `canonical_manifest_bytes()`
- `calculate_manifest_sha256()`
- `with_manifest_sha256()`
- `validate_package_manifest()`

Schemaは`pyproject.toml`の既存`exchange/schemas/*.json` package-data設定によりdistributionへ含まれる。

---

## 19. G-03 / G-04 / H-01への引き継ぎ

### G-03

- `instructions_version`の初期正式値を確定する。
- ChatGPTへmanifest / current Object / Evidence / Result Schemaの読み方を指示する。
- `package_id / schema_version / manifest_sha256 / created_at / base_version_id`をResult bindingへ正確にechoさせる。
- manifest外Evidence IDをgroundingに使用させない。

### G-04

- Manifest生成前にPackage filesをstagingする。
- 各fileのSHA-256 / sizeを計算する。
- Manifest hashをfinalizeする。
- temporary directoryからfinalized Packageへatomicに切り替える。
- secret / sensitivity / rights等のpreflightを実装する。
- destination / export timestamp / outcomeをPackage外audit metadataとして記録する。

### H-01

- Result binding 5項目をmanifestと照合する。
- Resultの全Evidence IDが`included_evidence_ids`に存在することを確認する。
- Object / Classification / base Versionをcanonical storeとも照合する。
- manifest/file hash不一致を正常ResultとしてImportしない。

---

## 20. 完了条件

G-02は次を満たして完了とする。

1. Package schema versionを`sgokb.object-evidence-package/1.0`へ固定した。
2. Package IDをpath非依存のUUIDv4 identityとして定義した。
3. Object / Classification / base Version / instructions / Result Schema bindingを定義した。
4. included Source / Evidence membershipを機械表現した。
5. Source generationとEvidence payload file mappingを定義した。
6. carry-forward / manual include / retrievalのPackage roleを分離した。
7. F-03 retrieval reasonとF-04 selected-byを保持した。
8. F-04 budget / usage / countをmanifestへ記録した。
9. 全Package artifactのsize / SHA-256を記録する契約を定義した。
10. self-referenceしないdeterministic manifest hash方式を定義した。
11. E-05 Object Result bindingとのfield対応を固定した。
12. `allow / review_required / blocked` preflightとcredential非包含assertionを定義した。
13. External destinationをimmutable manifestから分離した。
14. JSON Schema + cross-field validatorを実装した。
15. 回帰テストを追加した。

**Status: Complete (2026-10-13)**
