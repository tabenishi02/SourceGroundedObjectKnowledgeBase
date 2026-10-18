# N-04 Post-G12 Grounded Generation Remediation Tasks

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Formal run: `20261018T213810+0900`
- Branch: `phase-n/n04-prerequisite-derived-search`
- G-12 result: `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
- Root-cause / desk review / research: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- Current parent state: **N-04 Failed / N-05 blocked**

---

## 1. Purpose

G-12で確認されたfailureを、単なるmodel retryやrubric緩和で回避せず、grounded-generation contract / validation / terminal gateを再点検して修正する。

今回のformal runでは次が正常だった。

- MCP public read boundary
- current Version resolution
- Context Builder / Grounded Context projection
- Similarity retrieval
- canonical read-only safety
- integrity
- focused/full regression

したがって本remediationでは、具体的failure evidenceがない限りRetrieval / MCP / canonical schemaを変更しない。

重点対象は次である。

```text
generation output contract
atomicity
semantic-role boundary
support / premise validation
semantic verifier
retry feedback
material sufficiency
terminal outcome
renderer
adversarial tests
formal harness
```

---

## 2. G-12 failure summary

### Case 1 — Roleplay

```text
Machine terminal: ACCEPTED
Formal verdict: FAIL
Retry: 0
```

- K5でsupportされる内容とsupportされないHoly Grail War claimが同一unitに混在した。
- semantic validatorがunit全体を`entailed`と誤判定した。
- material relationship claimが`stylistic_expression`として`role_valid`を通過した。
- unsupported contentがrendered responseへ到達した。

これは最優先のfalse-acceptanceである。

### Case 2 — Comparison

```text
Machine terminal: REJECTED
Formal verdict: FAIL
Retry: 1
```

- Attempt 1でunsupported claim。
- Attempt 2でsupport refs欠落。
- interpretationのmaterial premiseがKに存在しないにもかかわらず、別unitで`derived_supported`相当の誤判定が観測された。

fail-closed terminalは機能したが、semantic validation / premise semanticsは不十分である。

### Case 3 — Creative

```text
Machine terminal: REJECTED
Formal verdict: FAIL
Retry: 1
```

- `creative` blockの`label=null`が2 attempt連続。
- providerへ渡すJSON Schemaでは`label=null`が許可される一方、Python parserはcreative / interpretationでnon-empty labelを追加要求していた。
- retry feedbackは`missing_presentation_label`を返したが、schema自体は同じnull許容のままだった。

これはgenerator qualityだけでなくcontract表現の不一致である。

---

## 3. Remediation principles

1. **G-12 failed evidenceを削除・上書きしない。**
2. **N-04をCompleteへ変更しない。**
3. **N-05をblockedのまま維持する。**
4. **v1 / v2 failed acceptance specを履歴として保持する。**
5. **同じ条件での単純再試行をしない。**
6. **rubricを緩和してPASSさせない。**
7. **untrusted generatorというG-01原則を維持する。**
8. **semantic verifierもuntrusted / fallible componentとして扱う。**
9. **構造で防げるfailureをLLM judgeへ委ねない。**
10. **最終renderへ到達する文字列は全てvalidatorまたはdeterministic rendererの管理下に置く。**
11. **claim-level / premise-level fail-closedを優先する。**
12. **外部libraryは設計参考またはbenchmark candidateとして評価し、即production dependency化しない。**

---

## 4. Task list

| Task | Priority | Status | Purpose |
|---|---|---|---|
| N-04G-13 | P0 | **Complete (2026-10-18)** | G-12 root-cause、横断desk review、外部repo/library調査、remediation scope定義 |
| N-04G-14 | P0 | Pending | Atomic claim / semantic-role boundaryを再設計する |
| N-04G-15 | P0 | Pending | Output schema / presentation / deterministic rendering contractをhardeningする |
| N-04G-16 | P0 | Pending | Source-fact / interpretation semantic validation architectureを再設計する |
| N-04G-17 | P0 | Pending | Material sufficiency / use-case completion / terminal-render gateを再設計する |
| N-04G-18 | P0 | Pending | G-14〜G-17を統合してPost-G12 Design Freezeを行う |
| N-04G-19 | P0 | Pending | Frozen remediation designを実装する |
| N-04G-20 | P0 | Pending | Adversarial / replay / regression testを追加し実施する |
| N-04G-21 | P0 | Pending | v3 acceptance spec / Reference Workstation harnessをfreezeする |
| N-04G-22 | P0 | Pending | Reference Workstationでformal v3 re-acceptanceを実施する |

N-04 CompleteはN-04G-22で全Gate PASS後のみ可能とする。

---

## 5. N-04G-13 [P0] — Root-cause / Desk Review / External Research

**Status: Complete (2026-10-18)**

正本:

```text
docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
```

実施内容:

- G-12 3 failureを再分類。
- `context.py / request.py / output.py / validation.py / failure.py / render.py / evidence.py / application_grounding.py`を横断レビュー。
- `tests/test_n04_grounded_generation.py`をadversarial coverage観点でレビュー。
- G-04 / G-05 Decisionと実装の差分を確認。
- LM Studio Structured Output、JSON Schema / python-jsonschema、FActScore、Ragas、RAGChecker、MiniCheck、AlignScore、DeepEvalを調査。
- 問題をP0/P1へ分類し、G-14〜G-22へ割当。

---

## 6. N-04G-14 [P0] — Atomic claim / semantic-role boundary redesign

### Goal

Case 1型の「supported clause + unsupported clause」を1 verdictでPASSさせない。

### Required decisions

- material unitを**1 atomic proposition**へ限定するnormative ruleを強化する。
- generatorが非atomic unitを返した場合のdeterministic / semantic detection方法を決める。
- atomizerによるsilent post-hoc分割を唯一のgrounding proofにしない。
- `stylistic_expression`へmaterial source-world propositionを逃がせないようにする。
- `context_limit`へsource-world factを混在させない。
- `creative_addition`でsource Object / Conceptについて新たなfactを説明しない境界を強化する。
- 必要なら`stylistic_expression`をN-04 formal baselineで禁止または極小化する。

### Candidate direction

```text
Generator atomic unit
   ↓
Atomicity / proposition-risk gate
   ├─ clearly atomic -> support validation
   └─ multiple material propositions / ambiguous -> retry or INDETERMINATE
```

post-hoc LLM atomizerはdebug / audit用途には使用可能だが、claim omissionの可能性があるため単独authorityにしない。

### Completion condition

- [ ] atomicityのmachine-checkable invariantを定義。
- [ ] material propositionのrole逃避対策を定義。
- [ ] G-05 `all material proposition supported`を物理実装可能な形へ具体化。
- [ ] Case 1保存evidenceで新設計ならFAILになることを机上確認。

---

## 7. N-04G-15 [P0] — Output schema / presentation / renderer hardening

### Goal

Case 3型のschema/parser mismatchをなくし、presentation metadataからsemantic contentがvalidation bypassしないようにする。

### Required decisions

- model-generated `label`をnormative contentから外すか、固定enum / constへ限定する。
- rendererのheadingは`presentation_role`から**deterministically**生成する。
- interpretation / creative separationをmodel任意labelに依存させない。
- block roleとunit semantic roleの整合を可能な範囲でJSON Schemaへencodeする。
- role別`support_refs` cardinalityも可能な範囲でschemaへencodeする。
- LM Studioが使用可能なschema subsetをpreflightで検証する。
- advanced conditional schemaへ依存しすぎず、必要ならcontract shape自体を単純化する。

### Required invariant

```text
rendered semantic content
  = validated unit.text
  + SGOKB deterministic fixed headings/separators only
```

LLM-generated arbitrary labelをrenderしない。

### Completion condition

- [ ] Case 3 `label=null`がgeneration-time constraintまたはdeterministic rendererで安全に処理される。
- [ ] arbitrary label textがrendered factual content bypassにならない。
- [ ] schema / parser / rendererのruleが単一正本から導出される。

---

## 8. N-04G-16 [P0] — Semantic validation architecture redesign

### Goal

Phi-4単独judgeのfalse acceptanceを最終grounding proofにしない。

### Source fact

候補:

```text
V3 deterministic exact support
  ↓ unresolved
specialized grounded fact-checker
  ↓
independent bounded LLM judge（必要時）
  ↓
agreement / disagreement policy
```

検討candidate:

- MiniCheck
- AlignScore
- frozen independent LLM judge

最終採用前にG-12保存claim/K pairを使ったoffline benchmarkを実施する。

### Interpretation

G-05で本来定義した二段階を実装可能なcontractへする。

```text
1. premise units are already validated source facts
2. interpretation references premise unit IDs
3. validator judges only whether conclusion reasonably follows
```

K refを直接並べて1回の`reasonable_derivation`判定だけで済ませない。

Comparisonでは少なくとも両Object由来premiseが必要な比較claimについて、object coverageをdeterministically検査する。

### Completion condition

- [ ] G-12 Case 1 U2/U3をfalse acceptしないcandidateを選定。
- [ ] G-12 Case 2 unsupported interpretationをderived_supportedへ昇格しない。
- [ ] validator disagreementをPASSへ倒さない。
- [ ] local-only / frozen model policyを維持可能。

---

## 9. N-04G-17 [P0] — Material sufficiency / terminal / render gate redesign

### Goal

`validation PASS`と`use-caseを実際に完遂した`を分離し、Machine `ACCEPTED`が過度に広くならないようにする。

現在のfallback material sufficiencyは、material roleが1 unitでもあればtrueになり得る。

### Required decisions

- `MaterialRequirementGate`または同等componentを導入する。
- generic purpose invariantとbenchmark-specific acceptance requirementを分離する。
- comparisonの両Object coverage。
- creativeの両Concept source grounding + creative addition存在。
- roleplayの必要grounded fact数等、formal case-specific requirementはharnessから明示する。
- rendererをterminal decisionへbindする。

推奨:

```text
Grounding PASS
   ↓
Material Requirement PASS
   ↓
Terminal ACCEPTED
   ↓
Renderer
```

`validation PASS`だけではnormal responseをrenderしない。

### Completion condition

- [ ] ACCEPTED条件がG-06の意味と一致。
- [ ] materially insufficient outputをACCEPTEDにしない。
- [ ] REJECTED / SYSTEM_FAILUREはrender不能。
- [ ] INSUFFICIENT_CONTEXTはcontext-limit専用safe render pathのみ。

---

## 10. N-04G-18 [P0] — Post-G12 Design Freeze

G-14〜G-17を統合し、必要範囲でG-02/G-04/G-05/G-06/G-07の変更関係を明示する。

Silent design driftは禁止する。

Freeze対象:

- atomic claim contract
- role boundary
- structured output contract version
- deterministic presentation
- source-fact verifier policy
- interpretation premise policy
- validator disagreement policy
- material requirement gate
- terminal/render relationship
- retry feedback structure

---

## 11. N-04G-19 [P0] — Implementation

最低対象:

```text
src/sgokb/grounding/output.py
src/sgokb/grounding/request.py
src/sgokb/grounding/validation.py
src/sgokb/grounding/failure.py
src/sgokb/grounding/render.py
src/sgokb/application_grounding.py
```

必要に応じて新規:

```text
atomicity.py
material_gate.py
fact_checker.py / semantic_verifier.py
```

canonical DB / MCP ownershipは変更しない。

---

## 12. N-04G-20 [P0] — Adversarial / Replay / Regression

G-12 evidenceをgold regression fixtureへ変換可能な最小synthetic testcaseとして再現する。

必須test:

1. supported clause + unsupported clause in one unit -> no PASS
2. material fact disguised as stylistic_expression -> no PASS
3. context_limit with appended external fact -> no PASS
4. creative block containing source Concept claim -> role/scope failure
5. interpretation with unsupported premise -> no derived_supported
6. interpretation referencing only one side of a two-object comparison -> no comparison PASS
7. arbitrary model label cannot appear as unvalidated rendered content
8. null/missing presentation metadata cannot cause repeated useless retry under the new contract
9. schema error feedback contains path/detail sufficient for repair
10. materially incomplete but grounded response -> not ACCEPTED
11. validation PASS but terminal REJECTED/SYSTEM_FAILURE -> renderer refuses
12. source fact verifier disagreement -> INDETERMINATE/FAIL-CLOSED
13. G-12 Case 1/2/3 failure shapes all regress correctly
14. existing G-10 tests remain PASS or are deliberately migrated with documented reason

Full pytest / Ruff / diff check required。

---

## 13. N-04G-21 [P0] — v3 Acceptance / Harness Freeze

v2 Failed historyを保持し、新しいcontract / verifierを使うv3 acceptance specを作る。

Formal run前にfreeze:

- generator
- source-fact verifier
- interpretation validator
- runtime/settings
- structured-output mechanism
- retry policy
- evidence tree
- adversarial preflight
- formal rubric

G-12のFAILを「なかったこと」にしない。

---

## 14. N-04G-22 [P0] — Formal v3 Re-Acceptance

同じ3代表use caseを維持する。

N-04 Complete requires:

```text
3 / 3 formal Case PASS
+ no unsupported rendered material claim
+ no role escape
+ canonical invariance
+ integrity PASS
+ focused/adversarial regression PASS
+ full pytest 0 failed
```

---

## 15. Dependency

```text
G-12 valid formal FAIL
  ↓
G-13 Root-cause / Desk review / Research Complete
  ↓
G-14 Atomicity / Role Boundary
  ↓
G-15 Output / Presentation Contract
  ↓
G-16 Semantic Validation Architecture
  ↓
G-17 Material / Terminal / Render Gate
  ↓
G-18 Post-G12 Design Freeze
  ↓
G-19 Implementation
  ↓
G-20 Adversarial / Regression
  ↓
G-21 v3 Acceptance + Harness Freeze
  ↓
G-22 Formal v3 Re-Acceptance
  ↓
N-04 Complete only if PASS
  ↓
N-05
```

---

## 16. Explicit non-goals

本remediationだけを理由に次を変更しない。

- canonical 52-table model
- Object ID / Version identity
- Source / Evidence / Provenance
- MCP read-only boundary
- Context Builder budget / purpose selection
- Similarity ranking algorithm
- N-06 retrieval-quality metrics

これらに新しいfailure evidenceが出た場合のみ別Taskとして扱う。
