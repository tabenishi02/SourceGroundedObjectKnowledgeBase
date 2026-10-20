# N-04G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis

更新日: 2026-10-20

- Status: **Complete / desk replay PASS with residual-atomicity risk retained**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Source Gold: `benchmark/n04g23a-atomicity-role-gold-v1.json`
- Source Gold SHA-256: `347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687`
- E1 mapping: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
- E2 boundary: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- E3 contract: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- E4 matrix: `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- E5 plan: `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`
- Machine-readable replay: `benchmark/n04g23ae-v4-gate-desk-replay-v1.json`
- Frozen Gold labels / required / critical flags changed: **0**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E7 acceptance**

---

## 1. Purpose

E1〜E5で設計したv4 V2 Gateを、実装・classifier精度を仮定せずFrozen 47 Goldへ机上適用する。

本Taskの目的は、次を確認することである。

1. 47/47 caseにv4 authority pathを割り当てられるか。
2. critical invalid caseがV3+ support/derivationへ誤って進む設計穴がないか。
3. broad joint Atomicity/Role Judgeへの依存がどの程度縮小したか。
4. deterministic化で消えた責務と、Residual classifierへ残る責務を区別できるか。
5. E7でG-23Bをunblockしてよい設計成熟度に達したかを判断する材料を作る。

このDesk Replayは**classifier性能試験ではない**。

各Residual結果はFrozen Goldをoracleとして「正しいclassifierならどのrouteになるべきか」を記述する。従って、以下を証明しない。

- V2-R-A production classifierが実際にzero critical false-passを達成すること
- V2-R-C production classifierが実際にzero critical false-passを達成すること
- Stage 1 generatorがnon-atomic candidateを生成しなくなること
- N-04 formal acceptanceがPASSすること

---

## 2. Replay assumptions

v4 Gate orderはE5に従う。

```text
Candidate
  ↓
V2-S schema / construction
  ↓
V2-P application-owned provenance
  ↓
V2-D deterministic compatibility
  ↓ PASS only
V2-R-A residual atomicity if required
  ↓ ATOMIC only
V2-R-C content-only classification if required
  ↓ compatible only
V3/V4 support / derivation
```

Frozen v3 Goldはv4 schemaそのものではないため、Desk Replayでは各fixtureの**historical generation slot / declared role / presentation intent**から対応するv4 pathを仮定する。

この仮定はgenerator-declared roleをproduction authorityへ戻すことを意味しない。production v4ではE4どおりapplication-owned pathがauthorityである。

Short-circuit rule:

- V2-D FAILならV2-Rを呼ばない。
- V2-R-A `NON_ATOMIC/AMBIGUOUS`ならV2-R-Cを呼ばない。
- earlier FAIL/INDETERMINATEをlater Gateがoverrideしない。

---

## 3. Aggregate result

### 3.1 Total 47

```text
Total cases                              47
Required                                 41
Optional                                  6
Critical                                 33

V2-D deterministic POLICY_FAIL            5
V2-D PASS -> V2-R-A                       42

V2-R-A expected ATOMIC                    11
V2-R-A expected NON_ATOMIC                27
V2-R-A expected AMBIGUOUS                  4

V2-R-C invoked                            11
V2-R-C compatible                          8
V2-R-C semantic mismatch                   3

Expected V2 PASS                           8
Expected V2 FAIL                          35
Expected V2 INDETERMINATE                  4
```

### 3.2 Required 41

```text
Required V2 PASS                           8
Required V2 FAIL                          33
Required V2 INDETERMINATE                  0
```

The 8 V2 PASS cases are valid semantic-shape controls and still require applicable downstream support/derivation validation.

### 3.3 Critical 33

```text
Critical total                            33
V2-D deterministic reject                  5
V2-R-A NON_ATOMIC reject                  25
V2-R-C content mismatch reject             3
Critical without pre-V3 fail path          0
```

Thus all **33/33 critical invalid fixtures have a fail-closed V2 route before V3/V4 support or derivation can grant PASS**, assuming the bounded Residual classifiers produce the Frozen-Gold-expected verdict.

This is architecture coverage, not measured classifier performance.

---

## 4. Responsibility reduction

### 4.1 Broad joint Judge

v3/G-23A style:

```text
47 cases
  -> broad Atomicity + Role semantic judgment
```

v4 design:

```text
47
  ├─ 5 deterministic policy rejects
  └─ 42 narrow Atomicity residual checks
       ├─ 31 stop at Atomicity
       └─ 11 narrow Content-Type checks
```

The broad joint Atomicity/Role Judge is no longer an authority anywhere in the replay.

### 4.2 Content-role probabilistic scope

V2-R-C is invoked for only:

```text
11 / 47 = 23.4%
```

Thus content-role semantic classification is removed from:

```text
36 / 47 = 76.6%
```

of Frozen fixtures.

For critical invalid fixtures:

```text
V2-R-C required: 3 / 33 = 9.1%
V2-R-C not required: 30 / 33 = 90.9%
```

### 4.3 Atomicity probabilistic scope remains large

V2-R-A is still invoked for:

```text
42 / 47 = 89.4%
```

of Frozen fixtures because E3 correctly refuses to treat schema-valid model-authored free text as proof of semantic Atomicity.

Critical invalid cases still depending on V2-R-A:

```text
25 / 33 = 75.8%
```

Therefore E6 **does not claim Atomicity risk has been eliminated**.

The redesign changes the problem from:

```text
one broad joint LLM Judge deciding multiple coupled axes
```

to:

```text
structural + deterministic policy first
then a narrow Atomicity classifier
then, only when Atomicity passes, a narrow content-type classifier
```

This is a material responsibility reduction, but V2-R-A remains a P0 implementation/benchmark risk.

---

## 5. 47-case replay

Legend:

- `D-FAIL`: V2-D deterministic policy failure; Residual not called.
- `A-FAIL`: V2-R-A expected `NON_ATOMIC`; V2-R-C not called.
- `A-IND`: V2-R-A expected `AMBIGUOUS`; fail-closed / V2 INDETERMINATE.
- `C-PASS`: Atomicity passes; V2-R-C content class matches E4 expected role.
- `C-FAIL`: Atomicity passes; V2-R-C content class mismatches E4 expected role.
- `latent`: a second semantic defect may exist but is not evaluated after earlier fail.

| # | case_id | Req | Crit | E1 owner | V2-D | V2-R-A | V2-R-C | Expected V2 | Historical error prevented / isolated |
|---:|---|:---:|:---:|---|---|---|---|---|---|
| 1 | `direct-source-fact-contract` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / match | PASS | role/content check isolated from support |
| 2 | `faithful-source-fact-paraphrase` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / match | PASS | paraphrase role does not depend on truth judge |
| 3 | `unsupported-source-fact-still-role-valid` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / match | PASS | unsupported fact remains role-valid; support deferred |
| 4 | `negated-source-fact-still-role-valid` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / match | PASS | negation does not become role violation |
| 5 | `concept-source-fact` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / match | PASS | role/content separated from support |
| 6 | `neutral-atomic-object-property` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / match | PASS | narrow content classification only |
| 7 | `neutral-nonatomic-conjunction` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | Atomicity blocks before support |
| 8 | `source-fact-plus-extra-duty` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | added duty cannot ride supported clause |
| 9 | `fact-plus-causal-explanation` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | fact/explanation compression blocked |
| 10 | `mixed-source-fact-and-context-limit` | R | C | COMBINED | PASS | NON_ATOMIC | latent MIXED | FAIL | mixed policy cannot reach support |
| 11 | `valid-interpretation` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | INTERPRETATION / match | PASS | derivation deferred to V4I |
| 12 | `interpretation-mislabeled-source-fact` | R | C | RESIDUAL_SEMANTIC | PASS | ATOMIC | INTERPRETATION / mismatch | FAIL | content-only classifier catches role escape |
| 13 | `valid-creative-addition` | R | - | RESIDUAL_SEMANTIC | PASS | ATOMIC | CREATIVE / match | PASS | creative content accepted only in creative path |
| 14 | `creative-invention-mislabeled-source-fact` | R | C | RESIDUAL_SEMANTIC | PASS | ATOMIC | CREATIVE / mismatch | FAIL | invention cannot masquerade as source fact |
| 15 | `source-fact-smuggled-as-creative` | R | C | RESIDUAL_SEMANTIC | PASS | ATOMIC | SOURCE_FACT / mismatch | FAIL | source-world fact cannot escape as creative |
| 16 | `creative-role-disallowed-purpose` | R | C | DETERMINISTIC_POLICY | **FAIL** | not called | not called | FAIL | purpose mismatch removed from classifier |
| 17 | `source-fact-in-interpretation-block` | R | C | DETERMINISTIC_POLICY | **FAIL** | not called | not called | FAIL | path/presentation mismatch deterministic |
| 18 | `interpretation-in-main-block` | R | C | DETERMINISTIC_POLICY | **FAIL** | not called | not called | FAIL | path/presentation mismatch deterministic |
| 19 | `non-atomic-interpretation-with-premise-restatement` | R | C | COMBINED | PASS | NON_ATOMIC | latent semantic | FAIL | premise restatement blocked before derivation |
| 20 | `non-atomic-creative-two-events` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | multiple creative events cannot share one proposition |
| 21 | `g22-case1-attempt1-u1` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | historical multi-proposition failure isolated to Atomicity |
| 22 | `g22-case1-attempt1-u2` | O | - | OPTIONAL_AMBIGUOUS | PASS | NON_ATOMIC | not reached | FAIL | optional role ambiguity unnecessary after Atomicity fail |
| 23 | `g22-case1-attempt1-u3` | R | C | DETERMINISTIC_POLICY | **FAIL** | not called | not called | FAIL | known metadata policy violation short-circuits |
| 24 | `g22-case1-attempt2-u1` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | historical compound candidate cannot reach support |
| 25 | `g22-case1-attempt2-u2` | R | C | COMBINED | PASS | NON_ATOMIC | latent semantic | FAIL | Atomicity fail cannot be rescued by role verdict |
| 26 | `g22-case1-attempt2-u3` | R | C | DETERMINISTIC_POLICY | **FAIL** | not called | not called | FAIL | known metadata policy violation short-circuits |
| 27 | `g22-case2-attempt1-u1` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 28 | `g22-case2-attempt1-u2` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 29 | `g22-case2-attempt1-u3` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 30 | `g22-case2-attempt1-u4` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 31 | `g22-case2-attempt1-u5` | R | C | COMBINED | PASS | NON_ATOMIC | latent semantic | FAIL | mixed comparison premise blocked at Atomicity |
| 32 | `g22-case2-attempt2-u1` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 33 | `g22-case2-attempt2-u2` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 34 | `g22-case2-attempt2-u3` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 35 | `g22-case2-attempt2-u4` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | source-fact compression blocked |
| 36 | `g22-case2-attempt2-u5` | R | C | COMBINED | PASS | NON_ATOMIC | latent semantic | FAIL | mixed comparison premise blocked at Atomicity |
| 37 | `g22-case3-attempt1-u1` | O | - | OPTIONAL_AMBIGUOUS | PASS | AMBIGUOUS | not reached | INDETERMINATE | optional ambiguity preserved; no forced PASS |
| 38 | `g22-case3-attempt1-u4` | O | - | OPTIONAL_AMBIGUOUS | PASS | AMBIGUOUS | not reached | INDETERMINATE | optional ambiguity preserved; no forced PASS |
| 39 | `g22-case3-attempt2-u6` | O | - | OPTIONAL_AMBIGUOUS | PASS | AMBIGUOUS | not reached | INDETERMINATE | optional ambiguity preserved; no forced PASS |
| 40 | `g22-case3-attempt2-u9` | O | - | OPTIONAL_AMBIGUOUS | PASS | AMBIGUOUS | not reached | INDETERMINATE | optional ambiguity preserved; no forced PASS |
| 41 | `g22-case3-attempt1-u2` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | creative multi-proposition content blocked |
| 42 | `g22-case3-attempt1-u3` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | creative multi-proposition content blocked |
| 43 | `g22-case3-attempt1-u5` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | creative multi-proposition content blocked |
| 44 | `g22-case3-attempt2-u7` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | creative multi-proposition content blocked |
| 45 | `g22-case3-attempt2-u8` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | creative multi-proposition content blocked |
| 46 | `g22-case3-attempt2-u10` | R | C | STRUCTURAL | PASS | NON_ATOMIC | not reached | FAIL | creative multi-proposition content blocked |
| 47 | `g22-case3-attempt2-u11` | O | - | OPTIONAL_AMBIGUOUS | PASS | NON_ATOMIC | not reached | FAIL | optional role ambiguity unnecessary after Atomicity fail |

---

## 6. What is prevented by construction vs only detected later

E6 distinguishes three levels.

### 6.1 Deterministically prevented/rejected

5 cases are rejected from known structured metadata at V2-D.

```text
16, 17, 18, 23, 26
```

These no longer depend on a semantic classifier at all.

### 6.2 Not prevented, but fail-closed by narrow Atomicity authority

27 fixtures are expected `NON_ATOMIC` and 4 are expected `AMBIGUOUS` at V2-R-A.

This is an improvement over a joint Judge because the classifier has one narrow task and cannot reinterpret purpose/role policy.

However, generation of the bad candidate itself is **not structurally impossible** under E3's semi-structured free-text contract.

Therefore claims such as:

```text
"20 STRUCTURAL cases are solved by schema alone"
```

would be false.

The architecture only guarantees they cannot legally reach V3+ without explicit Atomicity PASS.

### 6.3 Residual semantic mismatch

3 required critical cases reach V2-R-C and need content-first semantic classification:

```text
12 interpretation-mislabeled-source-fact
14 creative-invention-mislabeled-source-fact
15 source-fact-smuggled-as-creative
```

These are the irreducible role/content boundary examples identified by E1.

---

## 7. Coverage analysis against E1 owners

| E1 owner | Cases | v4 primary handling | Desk replay result |
|---|---:|---|---|
| STRUCTURAL | 20 | V2-R-A after schema/policy | 20 expected NON_ATOMIC FAIL |
| DETERMINISTIC_POLICY | 5 | V2-D | 5 deterministic FAIL |
| RESIDUAL_SEMANTIC | 11 | V2-R-A then V2-R-C | 8 PASS controls, 3 semantic mismatch FAIL |
| COMBINED | 5 | V2-R-A first; semantic side latent if Atomicity fails | 5 expected NON_ATOMIC FAIL |
| OPTIONAL_AMBIGUOUS | 6 | V2-R-A fail-closed | 2 NON_ATOMIC FAIL, 4 INDETERMINATE |

47/47 have an explicit owner and route.

---

## 8. E6 Gate evaluation

E6 Gate from task plan:

> demonstrate material reduction in critical decisions delegated to a broad probabilistic judge.

Result: **PASS, with explicit residual Atomicity risk.**

Evidence:

1. Broad joint Atomicity/Role Judge is eliminated from all 47 routes.
2. 5/33 critical failures are deterministic before any classifier.
3. 25/33 critical failures are isolated to Atomicity-only classification.
4. Only 3/33 critical failures require content-type semantic classification.
5. All 33/33 critical invalid cases have a pre-V3 fail route.
6. No role/purpose/presentation policy decision is delegated back to a probabilistic classifier.
7. Optional ambiguity remains fail-closed instead of being force-labeled to improve coverage.

Residual concern:

```text
25 / 33 critical invalid fixtures
still require correct V2-R-A NON_ATOMIC detection.
```

Therefore E6 does **not** justify skipping the E5 classifier benchmark or weakening its zero-critical-false-pass Gate.

---

## 9. Implications for G-23A-E7

E6 provides enough architecture evidence for E7 to perform the integration/unblock review, but does not pre-decide its outcome.

E7 must explicitly review at least:

1. whether G-23B can consume E3/E4 contracts without duplicate role authority;
2. whether Stage 1 prompt/schema can target one-proposition candidates without claiming schema proves Atomicity;
3. whether V2-R-A/V2-R-C benchmark work has a clear later execution home before formal v4 acceptance;
4. whether G-23C/D can preserve certified-content binding without reintroducing free-form source-fact regeneration;
5. whether the remaining V2-R-A dependency is acceptable as a bounded implementation risk rather than an architecture blocker.

If E7 accepts the architecture, that acceptance must not be described as classifier selection or formal N-04 acceptance.

---

## 10. Protected historical state

Unchanged:

- Frozen 47 Gold labels / required / critical flags
- G-23A / G-23A-R benchmark results
- G-14 safety intent
- G-23 two-stage architecture
- E2 authority order
- E3 Semi-structured proposition contract
- E4 role compatibility matrix
- E5 classifier evaluation Gate
- MiniCheck threshold/profile
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary

N-04 remains **Failed / not Complete** and N-05 remains **blocked**.

---

## 11. Conclusion

`N-04G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis` is **Complete**.

Desk replay result:

```text
47/47 routed
33/33 critical invalid cases have pre-V3 fail path
5 deterministic critical rejects
25 Atomicity-only critical rejects
3 Content-Type critical rejects
0 critical case without owner/path
```

E6 Gate: **PASS with residual Atomicity classifier risk retained**.

Next task:

`N-04G-23A-E7 — Integration Decision / G-23B Unblock Review`
