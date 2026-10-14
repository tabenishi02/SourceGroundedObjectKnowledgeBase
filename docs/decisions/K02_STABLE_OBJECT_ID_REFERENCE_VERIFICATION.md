# K-02 Stable Object ID Reference Verification

更新日: 2026-10-14

Status: Accepted

対象Task: `K-02 [P1] Stable Object ID参照を検証する`

関連正本:

- `docs/decisions/K01_UPDS_OBJECT_REFERENCE_USE_CASE.md`
- `docs/requirements/SGOKB_UPDS_INTEGRATION_CONTRACT_REQUIREMENTS.md`
- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`
- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`
- `docs/planning/PHASE_K_PREPARATION.md`

---

## 1. 結論

K-01で定義したUPDS最小ユースケースに対して、SGOKBのstable Object ID / Knowledge Version参照契約を実装レベルで検証した。

検証結果:

> **同一Objectへ新しいaccepted Knowledge Versionを追加しても`object_id`は不変であり、current取得は新Versionへ進み、保存済みVersionを指定したpinned取得は旧Versionを再取得できる。Object表示名を変更しても`object_id`参照は壊れない。したがって、UPDSが`object_id + resolved_version_id`を記録するK-01契約は現行SGOKB実装で成立する。**

K-02ではUPDS runtimeを実装せず、SGOKB repository内にUPDS-shaped referenceを持つcontract-level integration testを追加した。

成果物:

```text
tests/test_k02_stable_object_reference.py
```

---

## 2. 検証対象の意味境界

K-02では次の2概念を明確に分離して検証する。

```text
object_id
= Object Identity
= Version更新や表示名変更をまたいで維持するstable reference

knowledge_version_id / resolved_version_id
= 特定時点のaccepted Object Knowledge snapshot
= immutableで再取得可能なrevision reference
```

UPDSが長期的に「どのCharacterを選択したか」を追跡する軸は`object_id`である。

一方、特定のSemantic Observation / Pattern / Preference Hypothesisを再現するために「その時点でどのKnowledgeを利用したか」を追跡する軸は`resolved_version_id`である。

---

## 3. 検証シナリオ

K-01から引き継いだacceptance scenarioを次の実テストへ落とした。

```text
1. Character Aをstable object_idで作成する。
2. Character Aのvalues / personality / themesを持つaccepted Version v1を作成する。
3. MCP get_objectsでVersion指定なしのcurrent取得を行う。
4. responseのobject_id + resolved_version_id(v1)をUPDS-shaped referenceへ保存する。
5. 同じCharacter Aへaccepted Version v2を追加する。
6. 同じobject_idをcurrent取得し、v2へ解決されることを確認する。
7. version_idsでv1を指定してpinned取得し、v1を再取得できることを確認する。
8. 保存済みUPDS-shaped referenceがv2追加によって書き換わらないことを確認する。
9. Object表示名を変更する。
10. 同じobject_idでcurrent v2 / pinned v1の双方を取得できることを確認する。
11. v1 / v2の両accepted Versionが同じobject_idへ所属し続けることを確認する。
```

---

## 4. 使用したK-01 request

検証ではK-01で決定した主経路をそのまま使用した。

```json
{
  "object_ids": ["object:k02:character-a"],
  "facets": ["values", "personality", "themes"],
  "include_relations": false,
  "include_evidence_refs": false
}
```

Transport境界は実際の`MCPReadAdapter.call_tool("get_objects", ...)`を通した。

したがって、単なるRepository direct testではなく次の経路を検証している。

```text
UPDS-shaped request
        ↓
MCPReadAdapter
        ↓
KnowledgeReadApplication.get_objects()
        ↓
ObjectKnowledgeReader
        ↓
Canonical Object / Version Store
```

UPDSからSQLiteへdirect accessする経路は使用していない。

---

## 5. v1 current取得

初期状態:

```text
object_id = object:k02:character-a
current_version = version:k02:character-a:v1
```

current requestではVersionを指定しない。

受入条件:

```text
object_id == object:k02:character-a
requested_version_id == null
resolved_version_id == version:k02:character-a:v1
is_current == true
requested_scope.facets == [values, personality, themes]
```

さらに3 FacetのKnowledge本文がv1内容として取得できることを確認した。

---

## 6. UPDS-shaped reference

K-02ではUPDS物理schemaを決めず、K-01で要求した参照情報を単純なconsumer-shaped dictionaryとして保存した。

```text
selection_event_id
sgokb_object_id
sgokb_version_id
requested_facets
mcp_tool_contract_version
application_contract_version
```

v1取得後の概念状態:

```text
selection_event_id = selection:k02:1
sgokb_object_id = object:k02:character-a
sgokb_version_id = version:k02:character-a:v1
```

v2が追加された後も、この保存済みreferenceを変更しないことをtestで確認した。

これはC-04 / K-01の次の原則を実装上確認する。

> 新Version発生は過去のUPDS推論をsilent rewriteしない。

---

## 7. v2追加後のcurrent取得

同じ`object_id`へv2を追加した。

```text
object_id = object:k02:character-a
v1 = accepted
v2 = accepted + current
```

Version指定なしで再度取得すると:

```text
object_id == object:k02:character-a
resolved_version_id == version:k02:character-a:v2
is_current == true
```

となることを確認した。

つまり、Identityは変えずにcurrent Knowledgeだけを進められる。

---

## 8. pinned v1再取得

過去推論の再現を模擬し、次を指定した。

```json
{
  "version_ids": {
    "object:k02:character-a": "version:k02:character-a:v1"
  }
}
```

受入条件:

```text
object_id == object:k02:character-a
requested_version_id == version:k02:character-a:v1
resolved_version_id == version:k02:character-a:v1
is_current == false
```

さらに、Facet本文がv2ではなくv1の内容であることも確認した。

これにより、単にVersion IDが返るだけではなく、immutable Knowledge snapshotとして旧内容を再読できることを確認した。

---

## 9. 表示名変更とIdentity

v2作成後にObject Registry上の表示名を次のように変更した。

```text
Character A
→ Character A Renamed
```

旧名称`Character A`はaliasとして追加した。

その後も:

```text
current取得 → same object_id + v2
pinned取得  → same object_id + v1
```

が成立した。

したがって、UPDS参照をdisplay nameへ依存させないC-04契約は妥当である。

### 9.1 注意: nameはVersion snapshotではない

現行`ObjectKnowledgeReader`は`name` / `aliases`を現在のObject Registryから取得し、Knowledge本文・classification snapshotを指定Versionから取得する。

そのため、v1をpinned取得しても表示名は現在の`Character A Renamed`となる。

これはK-02では許容する。

理由:

- `object_id`がIdentityの正本である。
- Knowledge Versionの再現性はFacet / Statement / Attribute / Relation等のaccepted Knowledge snapshotについて保証する。
- display nameの過去時点表示までをKnowledge Versionの一部として要求する契約にはしていない。

将来「過去時点のObject Registry labelそのもの」の完全再現が必要になった場合は、別要件として扱う。

---

## 10. Version ownership確認

最後にObjectへ属するVersion列を確認した。

```text
version:k02:character-a:v1 → object:k02:character-a / accepted
version:k02:character-a:v2 → object:k02:character-a / accepted
```

v2追加時にv1が別Objectへ移動したり、v1がinvalid化されたりしない。

これはstaleとinvalidを分離するIntegration Contractとも一致する。

---

## 11. 自動試験結果

### 11.1 K-02 focused test

```text
python -m pytest tests/test_k02_stable_object_reference.py -q
1 passed
```

```text
python -m ruff check tests/test_k02_stable_object_reference.py
All checks passed!
```

### 11.2 関連Regression

対象:

```text
tests/test_k02_stable_object_reference.py
tests/test_j01_retrieval_mcp_boundary.py
tests/test_j02_mcp_read_tools.py
tests/test_versioning.py
```

結果:

```text
24 passed
```

これによりK-02だけでなく、Application/MCP read boundaryとVersion lifecycleの既存契約も維持されていることを確認した。

### 11.3 全pytest

```text
313 passed
4 skipped
1 failed
```

唯一のfailure:

```text
tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch
```

失敗内容:

```text
Expected: SHA-256 mismatch
Actual:   Package file size mismatch: evidence/source_001.md
```

これはPackage Transferの既存テスト期待値と検証順序の差であり、K-02で追加・変更したObject ID / Version / MCP read処理とは無関係である。

### 11.4 全Repository Ruff

Repository全体では既存101件のlint違反が存在するためpassしない。

主な既存箇所:

```text
extensions/web-page-capture/...
src/sgokb/exchange/...
tests/test_package_transfer.py
```

K-02追加ファイル単体ではRuff passを確認済みである。

K-02では既存lint debtを無関係な変更として修正しない。

---

## 12. K-02 acceptance判定

| Acceptance | Result |
|---|---|
| stable `object_id`がv1→v2で変化しない | Pass |
| current取得がv2へ更新される | Pass |
| pinned取得でv1を再取得できる | Pass |
| v1のKnowledge本文が保持される | Pass |
| UPDS-shaped referenceがsilent rewriteされない | Pass |
| display name変更後も`object_id`参照が成立する | Pass |
| v1 / v2が同一Objectにacceptedとして残る | Pass |
| MCP/Application contract versionを確認できる | Pass |
| SGOKB SQLite direct fallbackを使用しない | Pass |

**K-02 Acceptance: PASS**

---

## 13. K-03への引き継ぎ

次Task:

```text
K-03 [P1] SGOKBとUPDSのSemantic Indexを混同しないことを確認する
```

K-03ではK-02で使用したconsumer-shaped境界を維持したまま、次を確認する。

```text
SGOKB semantic/retrieval ownership
  = Object / Facet / Statement / Evidence

UPDS semantic/inference ownership
  = Selection Event / Semantic Observation / Pattern / Preference Hypothesis
```

特に次を禁止条件として自動試験またはstatic boundary testへ落とす。

- UPDS Personal InferenceをSGOKB canonical Knowledgeへwrite-backしない。
- Preference HypothesisをSGOKB Search Representation / Embeddingへ混入しない。
- SGOKB Similarity scoreをPreference probabilityへ変換しない。
- UPDS ConsumerがSGOKB SQLite / internal search tableを直接参照しない。
- SGOKB Object retrievalをUser Profileでpersonalizeしない。

---

## 14. Definition of Done

- [x] K-01のstable Object ID / Version scenarioを実テストへ落とした。
- [x] current v1取得を確認した。
- [x] 同一Objectへのv2追加後も`object_id`が維持されることを確認した。
- [x] current取得がv2へ進むことを確認した。
- [x] pinned取得でv1を再取得できることを確認した。
- [x] v1 Knowledgeがimmutable snapshotとして残ることを確認した。
- [x] UPDS-shaped referenceがsilent rewriteされないことを確認した。
- [x] 表示名変更後も`object_id`参照が壊れないことを確認した。
- [x] MCP `get_objects`経由で検証した。
- [x] focused / related regression testが成功した。
- [x] 全pytestの既存failureをK-02から分離して記録した。
- [x] K-03へ責務分離検証を引き継げる状態にした。

**K-02は完了。**
