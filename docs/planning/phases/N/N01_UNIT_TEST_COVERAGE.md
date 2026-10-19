# N-01 Unit Test Coverage Audit

更新日: 2026-10-16

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-01 [P0] Unit Testを新ドメインへ更新する`
- Baseline: `eecbe5d2f47017c3e7c35157d2851c58c1c6a4ef`
- Scope: canonical domain coverage audit / missing Unit Test補完 / known baseline failure処遇
- Runtime verification: **PASS (2026-10-16)**
- Status: **Complete (2026-10-16)**

## 1. 方針

N-01ではhistorical Phase名を持つtestを機械的にrenameしない。
現行canonical semanticsを直接検証しているtestは再利用し、domain coverageの欠落だけを補完する。

評価単位は次とする。

1. Object Registry / Classification
2. Facet / Attribute / Relation
3. Source / Snapshot / Evidence / Provenance
4. Object Result Schema / Validation
5. Version lifecycle / stale / rollback / immutability
6. Evidence Package / Export / Result Receipt
7. Retrieval
8. Embedding Space / Representation / Vector lifecycle
9. MCP read boundary
10. CLI contract boundary

## 2. Coverage matrix

| Canonical domain | 主な既存test | N-01判定 |
|---|---|---|
| Object Registry / Classification | `test_object_schema.py`, `test_class_facet_gold_cases.py` | Covered |
| Facet / Attribute | `test_semantic_facet_schema.py`, `test_class_facet_gold_cases.py` | Covered |
| Relation | `test_object_schema.py`, `test_semantic_facet_schema.py`, `test_result_validation.py` | **補完** |
| Source / Snapshot / Evidence / Provenance | `test_source_evidence_schema.py`, `test_canonical_ingestion.py`, `test_f03_object_evidence_retrieval.py` | Covered |
| Object Result Schema / Validation | `test_object_result_schema.py`, `test_result_validation.py` | Covered |
| Version lifecycle / stale / rollback / immutability | `test_versioning.py`, `test_object_version_import.py` | Covered |
| Package / Export / Result Receipt | `test_package_manifest.py`, `test_package_transfer.py`, `test_result_receipt.py` | **既知failure修正** |
| Lexical / Semantic / Hybrid Retrieval | `test_hybrid_search.py`, `test_search_quality_gold.py` | Covered |
| Similarity / Evidence Search | `test_object_similarity.py`, `test_j02_evidence_search.py` | Covered |
| Embedding Space / Representation / Vector | `test_embedding_space.py`, `test_search_representation.py`, `test_vector_index.py` | Covered |
| MCP read adapter / server | `test_j01_*`, `test_j02_mcp_read_tools.py`, `test_j03_mcp_resources.py`, `test_j04_context_builder.py`, `test_j05_mcp_write_separation.py`, `test_j06_mcp_client_acceptance.py` | Covered |
| CLI boundary | `test_m01_cli.py`, `test_m01_registry_proposals.py`, `test_m03_standard_workflow.py` | Covered |

## 3. N-01で補完したRelation Unit Test

既存testではRelationについて、Registry分離、Version scope、temporal scope、
Result referential validation等は確認済みだった。

一方、Version acceptance境界に対する次の2点を直接固定するtestが不足していた。

- EvidenceのないRelationを含むcandidateをacceptedへ昇格できないこと。
- accepted Versionに属するRelationをupdate / deleteできないこと。

`tests/test_n01_domain_contracts.py`を追加し、この2点をcanonical regressionとして固定する。

これによりRelationについて、

```text
Relation Registry
→ Version-scoped Relation
→ Evidence grounding
→ acceptance gate
→ terminal immutability
```

のdomain-level boundaryをUnit Testで明示的に追跡できる。

## 4. Package Transfer known baseline failureの処遇

対象:

```text
tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch
```

原因はproduction implementationではなくfixture設計だった。

元testはmanifest上の`size_bytes`と`sha256`の両方が変化する内容へfileを改変しながら、
`SHA-256 mismatch`だけを期待していた。

実装は次の順序で検証する。

```text
scope
→ size
→ SHA-256
→ package contract
→ credential material
```

size mismatchを先にrejectすることはintegrity contractとして妥当であり、
hash検証順序を変更する必要はない。

N-01ではtamper内容を元の`Evidence text`と同じ13 bytesの`Tampered text`へ変更する。
これによりsize gateを通過させ、SHA-256 mismatch branchそのものを検証する。

Decision:

- production validation order: **変更しない**
- testのmessage期待値: **維持**
- test fixture: **同一size tamperへ修正**
- xfail / skip: **使用しない**

## 5. Legacy / misleading test audit

historical Phase名を持つ次のtest群は、名称だけを理由に削除・renameしない。

```text
test_f02_standard_pipeline.py
test_f03_object_evidence_retrieval.py
test_f04_evidence_selection.py
test_f05_association_controls.py
test_j01_*.py
test_j02_*.py
test_j03_*.py
test_j04_*.py
test_j05_*.py
test_j06_*.py
test_k02_*.py
test_k03_*.py
test_l05_*.py
test_m01_*.py
test_m03_standard_workflow.py
```

これらは現在もcanonical domain boundaryまたはregressionを検証しており、
現時点でlegacy-onlyと判定できない。

Phase N中に意味が失われたtestが判明した場合は、単なる名称整理ではなく
replacement coverageを用意した上で個別にretireする。

## 6. Verification gate

N-01を正式にCompleteへ更新する前にReference Workstationで次を実行する。

```powershell
python -m pytest tests/test_package_transfer.py tests/test_n01_domain_contracts.py -q
python -m pytest -q
python -m ruff check tests/test_package_transfer.py tests/test_n01_domain_contracts.py
```

必須条件:

- Package Transfer既知failureが解消している。
- N-01 Relation追加testがPASSする。
- full suiteに新規regressionがない。
- RuffがPASSする。

Reference Workstationで全必須verificationがPASSしたため、Task masterのN-01を`[x]`へ更新した。

## 7. N-01 completion decision

**Complete (2026-10-16)**。Code / test designとReference Workstationでのruntime verificationが完了した。N-02 Integration Testへ移行可能。N-02以降の実装は今回行っていない。


## 8. Reference Workstation runtime verification

- 実施日: 2026-10-16 JST
- 環境: Windows 11 build 26300 / PowerShell / Python 3.10.6、通常の`.venv`。pytest 9.1.1 / Ruff 0.17.0 / MCP SDK 2.3.0。
- branch: `phase-n/n01-unit-test-update` / PR #36
- 検証基準: main `eecbe5d2f47017c3e7c35157d2851c58c1c6a4ef`、PR実装 `68ecbfbb62c47e8605d35b26b1fa3543a3374006`。今回の追加差分はtest整形と完了記録のみ。

通常venvのPython（`.venv/Scripts/python.exe`）で次を実行した。

| Command | 結果 |
|---|---|
| `python -m pytest tests/test_package_transfer.py tests/test_n01_domain_contracts.py -q` | **11 passed / 0 failed**（整形後4.01秒） |
| `python -m pytest -q` | **304 passed / 3 skipped / 0 failed**（113.56s (0:01:53)） |
| `python -m ruff check tests/test_package_transfer.py tests/test_n01_domain_contracts.py` | **PASS** |
| `python -m ruff format --check tests/test_package_transfer.py tests/test_n01_domain_contracts.py` | **PASS**（2 files） |
| `git diff --check` | **PASS** |

既知のPackage Transfer baseline failureは解消した。同一13 bytesの`Evidence text`から`Tampered text`への改変によりsize gateを通過し、期待どおりSHA-256 mismatchを検出する。production側のvalidation order・assertionは変更していない。

追加Relation test 2件はいずれもPASS。migration007のacceptance triggerによるEvidence必須条件、accepted VersionのRelation update/delete禁止と一致する。Evidenceなしcandidateの昇格失敗後もcurrent Versionが未設定であり、拒否されたRelation変更後も元のsubject/target/current Versionが維持されることを確認した。

発見・修正: 指定Ruffで`test_package_transfer.py`の既存長行2件（E501）を検出したため、同ファイルをformatした。test fixtureや期待値、production実装、migration、repository、domain modelの追加修正は不要だった。整形後に対象testとfull suiteを実行し、新規regressionはなかった。今回skip / xfailを追加していない。full suiteの既存skipはoptional runtime条件によるもので、N-01対象11件はskipなし。

ローカル証跡（Git管理外）: `.local/n01/focused.log` / `.local/n01/full.log`。ログ、DB、端末固有設定はcommit対象外。Phase N全体は継続中で、次TaskはN-02。
