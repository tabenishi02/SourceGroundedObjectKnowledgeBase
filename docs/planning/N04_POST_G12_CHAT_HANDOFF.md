# N-04 Post-G12 Chat Handoff

更新日: 2026-10-19

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record: `main`
- Branch state: **Phase M / Phase N task work integrated into main; G-14/G-15 design documentation is based on main**
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Completed remediation task: **N-04G-15 [P0] Output schema / presentation / renderer hardening**
- Next task: **N-04G-16 [P0] Semantic validation architecture redesign**

---

## 1. このhandoffの目的

別チャットでN-04 post-G12 remediationを継続するための開始点を固定する。

新しいチャットでは、過去のPhase N stacked branchを再利用せず`main`を正本として確認する。

---

## 2. Branch / PR統合状態

2026-10-18、Phase N stacked PRを依存順にmainへ統合した。

```text
PR #36 N-01 -> main
PR #37 N-02 -> main
PR #38 N-03 -> main
PR #39 N-04 / post-G12 analysis -> main
```

merge commits:

```text
PR #36 -> 89d5614afa848e04d66ea2a96a6d82ea4220a9ec
PR #37 -> 7c1789c9dcb971f980e28c625f7dd4abde51a7d8
PR #38 -> 4e8c2ef0676ca588838a5effd2030796a99cb02b
PR #39 -> dd7fd60fc8f30059803652b25fc22186ad9101bf
```

Phase M branchesはPR #32〜#35ですでにmainへmerge済みだった。古いbranch refが残っていても、再mergeしない。

G-14/G-15作業はこの統合済み`main`を正本として実施した。

---

## 3. N-04 formal v2 result

Formal run:

```text
run_id: 20261018T213810+0900
Reference Workstation: Windows 11 / Python 3.10.6 / RTX 4090 24GB
Generator: sgokb-n04-mistral32
Semantic validator: sgokb-n04-phi4
```

結果:

| Case | Machine terminal | Formal verdict | Retry |
|---|---|---|---|
| Saber Roleplay | ACCEPTED | FAIL | 0 |
| Similar Work Comparison | REJECTED | FAIL | 1 |
| Concept Combination Creative | REJECTED | FAIL | 1 |

Overall:

```text
0 / 3 Case PASS
N-04 = Failed
N-05 = blocked
```

Safety / regressionは正常。

```text
canonical SHA-256 before == after
integrity before / after = PASS / PASS
focused grounding = 21 passed
focused read-path = 27 passed
full pytest = 382 passed / 0 skipped / 0 failed
Ruff = PASS
git diff --check = PASS
```

したがって、Retrieval / MCP / Context Builder / canonical safetyを今回のfailure原因として扱わない。

---

## 4. G-12で確認した主要failure

### Case 1 — false acceptance

- supported clauseとunsupported Holy Grail War claimが同一unitに混在。
- semantic validatorがunit全体を`entailed`と判定。
- material relationship claimが`stylistic_expression`として`role_valid`を通過。
- unsupported contentが`ACCEPTED`後にrenderされた。

### Case 2 — interpretation / support failure

- Attempt 1 unsupported claim。
- Attempt 2 support refs欠落。
- interpretationにunsupported premiseがあるのにsemantic judgeでderived-supported相当へ進み得ることを確認。

### Case 3 — presentation contract mismatch

- creative blockの`label=null`が2 attempt連続。
- provider JSON Schemaはnullを許可する一方、Python parserはcreative / interpretation labelを必須化。
- schemaとapplication contractが不一致。

---

## 5. G-13 desk reviewで追加確認した問題

最低限、次をG-14以降で扱う。

1. Atomic semantic unitが実装上強制されていない。
2. `stylistic_expression`がmaterial claimのescape hatchになり得る。
3. interpretationのpremise support / derivation supportが一段のsemantic verdictへ圧縮されている。
4. JSON Schemaとparserのpresentation ruleが不一致。
5. model-generated `label`がunit validation外のままrendererへ表示され得る。
6. V0 retry feedbackがblock/path/detailを十分保持しない。
7. material sufficiency fallbackが「material roleが1つでもある」で弱い。
8. rendererがterminal `ACCEPTED`へbindされていない。
9. multi-object use-case coverageをcore machine Gateで保証していない。
10. focused testsにreal-model false-positive型adversarial caseが不足。

正本:

```text
docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
```

---

## 6. N-04G-14で確定した設計

正本:

```text
docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
```

主要Decision:

1. `1 validation unit = 1 atomic semantic proposition`を必須invariantとした。
2. 部分ごとに異なるgrounding verdictを持ち得るunitは`NON_ATOMIC`とする。
3. `ATOMIC`だけがsupport / derivation validationへ進める。`NON_ATOMIC / INDETERMINATE`はgrounded PASS不可。
4. content materiality / role boundary判定をmodel-declared `semantic_role`より優先する。
5. mixed-role unitを禁止する。
6. role mismatchをsilent reclassificationで救済しない。
7. post-hoc atomizerを唯一のgrounding authorityにしない。
8. N-04 v3 formal baselineではmodel-authored `stylistic_expression`を禁止する。
9. `context_limit`をsupplied Contextの可用性に関するmeta / epistemic propositionへ限定する。
10. `creative_addition`にsource Object / Concept等のfactを混在させない。
11. `interpretation`はconclusion-onlyとし、premiseは別validated source-fact unitとして扱う方向を固定した。物理参照方式はG-16で決める。
12. Atomicity / role-boundary failureは後段semantic verifierのpositive verdictでoverrideできない。

G-12 Case 1 desk replay:

```text
supported clause + unsupported clause
-> NON_ATOMIC
-> support validationへ進まない
-> no grounded PASS
```

```text
material claim disguised as stylistic_expression
-> v3 role自体がmodel output禁止
-> content-first role checkでもROLE_VIOLATION
-> no grounded PASS
```

G-14ではproduction codeを変更していない。

---

## 7. N-04G-15で確定した設計

正本:

```text
docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
```

主要Decision:

1. model-generated free-form `label`をv3 normative output contractから削除する。
2. `Interpretation` / `Creative addition` / `Context limit`等のheadingはtrusted rendererが`presentation_role`から決定論的に生成する。
3. rendererへ到達するLLM-authored semantic textをvalidated `unit.text`だけに限定する。
4. v3 baselineではblock role / unit semantic roleを原則1対1にする。
5. `source_fact`はsupport ref必須、`creative_addition` / `context_limit`はsupport refなしをschemaへencodeする方向を固定した。
6. G-14に従い`stylistic_expression`をv3 model output enumから除外する。
7. role-specific block schemaを第一候補とし、provider/application間のhidden conditional ruleを減らす。
8. providerへ渡すschemaとapplication parserを同一canonical logical schemaから導出する。
9. parser-local hidden structural ruleは禁止する。
10. provider structured-output capabilityはformal v3前にpreflightする。
11. schema failureは`json_path / block_id / unit_id / failure_detail / expected_rule`を保持可能にする。
12. breaking changeのため`sgokb.grounded-generation-output.v2`へのrevisionを予約し、最終version/shapeはG-18でfreezeする。

G-12 Case 3 desk replay:

```text
creative block + label=null
-> v3ではlabel field自体が存在しない
-> deterministic rendererがtrusted headingを生成
-> missing/null label retry loopの原因が消える
```

free-form label injectionについても:

```text
unknown label field
-> contract violation / additionalProperties=false
-> rendererへ到達しない
```

G-15ではproduction codeを変更していない。

---

## 8. Post-G12 remediation task chain

正本:

```text
docs/planning/N04_POST_G12_REMEDIATION_TASKS.md
```

Task:

```text
N-04G-13  Root-cause / desk review / research       Complete
N-04G-14  Atomic claim / semantic-role redesign     Complete
N-04G-15  Output / presentation contract hardening  Complete
N-04G-16  Semantic validation architecture          Pending
N-04G-17  Material / terminal / render gate         Pending
N-04G-18  Post-G12 Design Freeze                    Pending
N-04G-19  Implementation                            Pending
N-04G-20  Adversarial / replay regression           Pending
N-04G-21  v3 acceptance / harness freeze            Pending
N-04G-22  Formal v3 re-acceptance                   Pending
```

N-04 CompleteはG-22で3/3 Case PASS + safety/regression Gate全PASS後のみ。

---

## 9. 次のTask — N-04G-16

Task:

```text
N-04G-16 [P0]
Semantic validation architecture redesign
```

目的:

- Phi-4単独judgeのfalse acceptanceを最終grounding proofにしない。
- source fact verificationとinterpretation derivation verificationを分離する。
- G-14でconclusion-onlyとしたinterpretationを、validated premise unit参照で物理化する。

最低検討事項:

- source fact verifier candidate（MiniCheck / AlignScore / frozen independent LLM judge等）の比較。
- G-12保存claim/K pairを使ったoffline benchmark方針。
- deterministic exact support後のunresolved claimに対するverifier chain。
- verifier disagreement / indeterminateをPASSへ倒さないpolicy。
- interpretationの`premise_unit_ids`等の物理contract。
- premise unitが全てvalidated source factであることのdeterministic確認。
- comparisonで両Object premise coverageが必要なclaimの検査。
- hidden external premiseをderived-supportedへ昇格させない構造。
- atomicity classifierのsemantic componentをsource-fact verifierとどう分離するか。

G-16も設計Taskであり、G-18 Design Freeze前にproduction codeを変更しない。

---

## 10. 変更してはいけない境界

具体的failure evidenceがない限り次を変更しない。

```text
Object identity
current accepted Version semantics
Canonical Statement / Attribute / Relation
Evidence / Provenance
Version immutability
Retrieval / Similarity基本contract
MCP read boundary
Context Builder selection / budget
N-03 dataset
G-12 failed evidence
```

rubricを緩和してPASSさせない。

---

## 11. 新チャットで最初に確認する文書

優先順:

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
4. `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
5. `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
6. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
7. `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
8. `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
9. `src/sgokb/grounding/validation.py`
10. `tests/test_n04_grounded_generation.py`

---

## 12. 新チャット開始用prompt

```text
SourceGroundedObjectKnowledgeBaseのPhase N / N-04 post-G12 remediationをこのチャットへ引き継ぎます。

GitHubはmainを正本として確認してください。過去のPhase N stacked branchは使わないでください。

まず以下を確認してください。

- docs/planning/N04_POST_G12_CHAT_HANDOFF.md
- docs/planning/N04_POST_G12_REMEDIATION_TASKS.md
- docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md
- docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md
- docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
- docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md

現在、N-04G-15までComplete、N-04はFailed、N-05はblockedです。

次Taskは:
N-04G-16 [P0] Semantic validation architecture redesign

です。

G-14/G-15 DecisionとG-12 Case 1/2保存evidenceを前提に、G-16を実施してください。設計Taskなので、G-18 Design Freeze前にproduction codeを変更しないでください。
```