# N-04 Post-G12 Chat Handoff

更新日: 2026-10-18

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Current branch of record: `main`
- Branch state: **Phase M / Phase N task work merged into main; open PR = 0**
- Parent task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Current N-04 state: **Failed / not Complete**
- N-05: **blocked**
- Next task: **N-04G-14 [P0] Atomic claim / semantic-role boundary redesign**

---

## 1. このhandoffの目的

別チャットでN-04 post-G12 remediationを継続するための開始点を固定する。

新しいチャットでは、過去のstacked branchを再利用せず`main`を正本として確認する。

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

統合後、open PRは0件。

今後の作業は`main`から開始する。

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

最重要問題。

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

詳細:

```text
docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
```

---

## 6. 外部調査の主要結論

G-13では次を参考にした。

```text
FActScore
Ragas Faithfulness
Amazon RAGChecker
MiniCheck
AlignScore
DeepEval
LM Studio Structured Output
JSON Schema Draft 2020-12 / python-jsonschema
```

共通して有力な方向:

- whole-responseではなくatomic claim / statement単位で検証する。
- claimとsupplied contextのentailmentを個別評価する。
- retrieval failureとgeneration / faithfulness failureを分離する。
- structured outputはsyntax/shape enforcementでありsemantic groundingの代替ではない。

MiniCheckはsource-fact verifier候補としてG-16でoffline benchmark候補とする。

---

## 7. Post-G12 remediation task chain

正本:

```text
docs/planning/N04_POST_G12_REMEDIATION_TASKS.md
```

Task:

```text
N-04G-13  Root-cause / desk review / research       Complete
N-04G-14  Atomic claim / semantic-role redesign     Pending
N-04G-15  Output / presentation contract hardening  Pending
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

## 8. 次のTask — N-04G-14

目的:

```text
supported clause + unsupported clause
```

を1 verdictでfalse acceptしないatomic claim / semantic-role boundaryへ再設計する。

最低検討事項:

- material unitを1 atomic propositionへ限定するmachine-checkable invariant。
- non-atomic / ambiguous unitの扱いをRetry / INDETERMINATEへ倒す条件。
- post-hoc atomizerを唯一のgrounding authorityにしない。
- `stylistic_expression`へmaterial factを逃がさない。
- `context_limit`へのsource-world fact混在を防ぐ。
- `creative_addition`がsource Concept/Objectについてunsupported factを説明しない境界。
- v3 formal baselineで`stylistic_expression`を禁止または極小化する案の比較。
- G-12 Case 1保存evidenceを新設計へ当てた机上判定。

このTaskは設計Taskであり、先にproduction codeを変更しない。

---

## 9. 変更してはいけない境界

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

## 10. 新チャットで最初に確認する文書

優先順:

1. `docs/planning/N04_POST_G12_CHAT_HANDOFF.md`
2. `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`
3. `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
4. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
5. `docs/decisions/N04G04_GENERATION_OUTPUT_CONTRACT.md`
6. `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
7. `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
8. `src/sgokb/grounding/output.py`
9. `src/sgokb/grounding/validation.py`
10. `tests/test_n04_grounded_generation.py`

---

## 11. 新チャット開始用prompt

```text
SourceGroundedObjectKnowledgeBaseのPhase N / N-04 post-G12 remediationをこのチャットへ引き継ぎます。

まずmainブランチの以下を確認してください。

- docs/planning/N04_POST_G12_CHAT_HANDOFF.md
- docs/planning/N04_POST_G12_REMEDIATION_TASKS.md
- docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md
- docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md

現在、N-04G-13までComplete、N-04はFailed、N-05はblockedです。

次Taskは:
N-04G-14 [P0] Atomic claim / semantic-role boundaryを再設計する

です。

G-12保存evidenceとG-13 desk reviewを前提に、まずG-14で決定が必要な論点を整理してください。設計Taskなので、私が実装を指示するまではproduction codeを変更しないでください。
```
