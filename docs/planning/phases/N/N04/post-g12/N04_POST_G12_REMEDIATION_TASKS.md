# N-04 Post-G12 Grounded Generation Remediation Tasks — Historical Record

更新日: 2026-10-22

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent: `N-04 [P0]`
- Status: **Historical / Superseded as N-04 completion path**
- Superseding decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Current N-04 tasks: `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`

## 1. Why this document is now historical

G-12 formal v2 re-acceptanceで0/3 Case PASSとなった後、当時のN-04仕様はConsumer AIの生成品質までSGOKB formal Completion Gateへ含めていた。

そのため、Context外claim / semantic false acceptance / creative boundary failureをSGOKB側で防止する目的でGrounded Generation remediationを開始した。

2026-10-22の責務境界再確認により、次を正式決定した。

```text
SGOKB formal N-04 responsibility
  = correct Knowledge Access Boundaryまで

External Consumer inference / generation
  = Consumer側 responsibility
```

したがってG-13〜G-25は有効な研究・実装履歴として保持するが、**N-04 Completion prerequisiteではない。**

## 2. Historical trigger

```text
G-12 formal v2 re-acceptance
run_id: 20261018T213810+0900
result: 0 / 3 Case PASS
```

観測された主なConsumer output failure:

- unsupported material claims
- multi-proposition false acceptance
- semantic-role escape
- unsupported interpretation premises
- creative / grounded boundary presentation failure

同runではcanonical / MCP / Retrieval / Context Builderにこれらの直接原因となるproduction defectを確認しなかった。

## 3. Historical remediation chain

| Task | Historical status | Purpose |
|---|---|---|
| N-04G-13 | Complete | Root-cause / desk review / external research |
| N-04G-14 | Complete | Atomic claim / semantic-role boundary redesign |
| N-04G-15 | Complete | Output schema / presentation / renderer hardening |
| N-04G-16 | Complete | Semantic validation architecture redesign |
| N-04G-17 | Complete | Material sufficiency / terminal / render gate redesign |
| N-04G-18 | Complete / Frozen | v3 Design Freeze |
| N-04G-19 | Complete | Frozen v3 implementation |
| N-04G-20 | Complete / historical Gate FAIL | Adversarial / verifier benchmark |
| N-04G-20R | Complete / PASS | Engineering Gate remediation |
| N-04G-21 | Complete / Frozen | v3 acceptance / harness freeze |
| N-04G-21V | Complete | Verifier candidate selection |
| N-04G-21R | Complete / PASS | Selected verifier offline proof |
| N-04G-22 | Complete / valid formal FAIL | Formal v3 re-acceptance, 0/3 PASS |
| N-04G-23A〜F | Complete | v4 architecture redesign / freeze |
| N-04G-24 | Complete | v4 implementation |
| N-04G-25A | VALID_FAIL_NO_SELECTION | Residual classifier benchmark / selection |

これらのstatusを取り消さない。

## 4. Historical v3 / v4 assets

このchainで追加・評価した主な資産:

- Grounded Generation output contracts
- deterministic support checks
- source-fact verifier adapter
- bounded semantic judge
- atomicity / semantic-role validation
- material / terminal / render gates
- v4 Stage 1 / Stage 2 architecture
- Certified Content
- residual Atomicity classifier design
- residual Content-Type classifier design
- development corpora / Frozen 47 evaluation assets

これらはN-04 formal read-boundary acceptanceに必須ではない。

## 5. G-25A historical result

G-25AではResidual classifier候補をdevelopment corpusで評価したが、mandatory zero-error Gatesを満たす候補を選択できなかった。

```text
status: VALID_FAIL_NO_SELECTION
```

この結果は次を意味する。

> 当時定義したResidual Atomicity / Content-Type classifier方式とGateでは、selection可能な候補が得られなかった。

次を意味しない。

> SGOKB Knowledge Access Boundaryが不成立である。

また、新N-04完了のためFrozen 47を実行しない。

## 6. Current disposition

現時点ではcode / benchmark / docsを削除しない。

N-04R-05で次の分類を行う。

```text
KEEP_CORE
KEEP_EXPERIMENTAL
MOVE_CONSUMER_SIDE
RETIRE
```

判断対象には次を含む。

- `src/sgokb/application_grounding_v4.py`
- `src/sgokb/grounding/v4_*`
- Grounded Generation v3 assets
- classifier corpora / benchmark harnesses
- verifier model profiles
- Frozen 47 gold
- G-13〜G-25 decision / evaluation docs

## 7. Rules until disposition

- historical evidenceを削除・上書きしない。
- G-13〜G-25をcurrent N-04 Completion Gateとして参照しない。
- Grounded Generation codeをN-04のために追加修正しない。
- classifier threshold / taxonomy / Gate tuningをN-04のために継続しない。
- Frozen 47をN-04再受入のために実行しない。
- SGOKB core read pathへ不要なGrounded Generation dependencyを追加しない。

## 8. Current N-04 path

```text
N-04R-01 Responsibility Boundary Decision       Complete
N-04R-02 Documentation Reconstruction            Active
N-04R-03 Formal Harness Reconstruction           Pending
N-04R-04 Reference Workstation Re-Acceptance     Pending
N-04R-05 Grounded Generation Asset Disposition   Pending
```

Current authority:

- `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
