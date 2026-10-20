# N-04G-23A-E1 — 47-Gold Responsibility Mapping

更新日: 2026-10-20

- Status: **Complete**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Source Gold: `benchmark/n04g23a-atomicity-role-gold-v1.json`
- Source Gold SHA-256: `347e39f5108ed920847ce717cf98571a5137c48e348aba7af7e5aa50679a4687`
- Gold labels changed: **0**
- Required: **41**
- Optional: **6**
- Critical for safety: **33**
- Critical case without owner: **0**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E acceptance**

## 1. Purpose

G-23A/G-23A-Rで使用した47 Goldを、v4 Gateのどの責務が扱うべきか全件分類する。本TaskではGold label、required/critical flag、Acceptance Gateを変更しない。

分類は次の5種類。

- `STRUCTURAL`: proposition-record構造とAtomicity invariantがprimary authority。
- `DETERMINISTIC_POLICY`: stage/path provenance、purpose、presentation等の既知metadataだけで判定可能。
- `RESIDUAL_SEMANTIC`: content-firstな意味分類が必要。
- `COMBINED`: structuralとsemantic/policyの独立違反を両方保持する必要がある。
- `OPTIONAL_AMBIGUOUS`: Frozen Gold自身が意図的に曖昧。force-labelしない。

## 2. Result summary

| Primary owner | Cases | Meaning |
|---|---:|---|
| STRUCTURAL | **20** | Atomicityを主にStructured Proposition contractへ移す |
| DETERMINISTIC_POLICY | **5** | LLM不要のpolicy mismatchをapplication側でreject |
| RESIDUAL_SEMANTIC | **11** | content type判定だけをbounded classifierへ残す |
| COMBINED | **5** | structuralとsemantic/policyを別authorityで独立判定 |
| OPTIONAL_AMBIGUOUS | **6** | hard acceptanceから外し、audit/coverageとして保持 |
| **Total** | **47** | 41 required / 6 optional |

Required 41件のうちowner未指定は0件。Critical 33件のうちowner未指定も0件。

## 3. Mapping rules

### 3.1 STRUCTURAL

`NON_ATOMIC + ROLE_VALID`を中心に、role自体は正しいが1 recordに複数の独立grounding propositionが入るcase。v4では「生成後の全件LLM Atomicity判定」をprimary authorityにせず、Structured Proposition recordとStage契約で防ぐ。

Secondary guardとしてcompound-risk detectionは残せるが、句読点や`and`だけで`NON_ATOMIC`を確定してはならない。

### 3.2 DETERMINISTIC_POLICY

既に存在するmetadataから違反が決まるcase。代表例:

```text
creative_addition + roleplay
source_fact + interpretation presentation
interpretation + main presentation
```

この種のcaseはLLM呼び出し前にrejectできる。Residual classifierはaudit用secondary guardであり、deterministic violationをoverrideしない。

### 3.3 RESIDUAL_SEMANTIC

metadataだけでは判定できず、実際のtext content typeを見る必要があるcase。代表例:

```text
interpretation text mislabeled as source_fact
new creative content mislabeled as source_fact
source-world fact smuggled as creative_addition
```

v4ではclassifierにgenerator-declared roleをauthorityとして与えず、content-first classificationを行い、application-owned provenanceと比較する。

### 3.4 COMBINED

Atomicity violationとsemantic-role violationが同時にあるcase。一つのjoint verdictへ圧縮せず、structural authorityとsemantic/policy authorityを独立させる。片方がPASSでももう片方を救済しない。

### 3.5 OPTIONAL_AMBIGUOUS

6件はFrozen Goldで`required=false`。AtomicityまたはRole granularity自体に意図的なambiguityがある。E1ではforce-labelせず、そのままE2/E5の設計検討用fixtureとして保持する。

## 4. 47-case mapping

Legend: `R`=required、`O`=optional、`C`=critical for safety、Semantic `Y`=自然言語の意味理解が必要。Secondary guardはprimary ownerをoverrideしない。

| # | case_id | Req | Crit | Gold Atomicity | Gold Role | Primary owner | Secondary guard | Semantic |
|---:|---|:---:|:---:|---|---|---|---|:---:|
| 1 | `direct-source-fact-contract` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 2 | `faithful-source-fact-paraphrase` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 3 | `unsupported-source-fact-still-role-valid` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 4 | `negated-source-fact-still-role-valid` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 5 | `concept-source-fact` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 6 | `neutral-atomic-object-property` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 7 | `neutral-nonatomic-conjunction` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 8 | `source-fact-plus-extra-duty` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 9 | `fact-plus-causal-explanation` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 10 | `mixed-source-fact-and-context-limit` | R | C | NON_ATOMIC | ROLE_VIOLATION | **COMBINED** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 11 | `valid-interpretation` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 12 | `interpretation-mislabeled-source-fact` | R | C | ATOMIC | ROLE_VIOLATION | **RESIDUAL_SEMANTIC** | DETERMINISTIC_COMPATIBILITY | Y |
| 13 | `valid-creative-addition` | R | - | ATOMIC | ROLE_VALID | **RESIDUAL_SEMANTIC** | STRUCTURAL_SCHEMA,DETERMINISTIC_COMPATIBILITY | Y |
| 14 | `creative-invention-mislabeled-source-fact` | R | C | ATOMIC | ROLE_VIOLATION | **RESIDUAL_SEMANTIC** | DETERMINISTIC_COMPATIBILITY | Y |
| 15 | `source-fact-smuggled-as-creative` | R | C | ATOMIC | ROLE_VIOLATION | **RESIDUAL_SEMANTIC** | DETERMINISTIC_COMPATIBILITY | Y |
| 16 | `creative-role-disallowed-purpose` | R | C | ATOMIC | ROLE_VIOLATION | **DETERMINISTIC_POLICY** | STRUCTURAL_SCHEMA,RESIDUAL_SEMANTIC_AUDIT | N |
| 17 | `source-fact-in-interpretation-block` | R | C | ATOMIC | ROLE_VIOLATION | **DETERMINISTIC_POLICY** | STRUCTURAL_SCHEMA,RESIDUAL_SEMANTIC_AUDIT | N |
| 18 | `interpretation-in-main-block` | R | C | ATOMIC | ROLE_VIOLATION | **DETERMINISTIC_POLICY** | STRUCTURAL_SCHEMA,RESIDUAL_SEMANTIC_AUDIT | N |
| 19 | `non-atomic-interpretation-with-premise-restatement` | R | C | NON_ATOMIC | ROLE_VIOLATION | **COMBINED** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 20 | `non-atomic-creative-two-events` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 21 | `g22-case1-attempt1-u1` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 22 | `g22-case1-attempt1-u2` | O | - | NON_ATOMIC | INDETERMINATE | **OPTIONAL_AMBIGUOUS** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 23 | `g22-case1-attempt1-u3` | R | C | NON_ATOMIC | ROLE_VIOLATION | **DETERMINISTIC_POLICY** | STRUCTURAL,RESIDUAL_SEMANTIC_AUDIT | Y |
| 24 | `g22-case1-attempt2-u1` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 25 | `g22-case1-attempt2-u2` | R | C | NON_ATOMIC | ROLE_VIOLATION | **COMBINED** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 26 | `g22-case1-attempt2-u3` | R | C | NON_ATOMIC | ROLE_VIOLATION | **DETERMINISTIC_POLICY** | STRUCTURAL,RESIDUAL_SEMANTIC_AUDIT | Y |
| 27 | `g22-case2-attempt1-u1` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 28 | `g22-case2-attempt1-u2` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 29 | `g22-case2-attempt1-u3` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 30 | `g22-case2-attempt1-u4` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 31 | `g22-case2-attempt1-u5` | R | C | NON_ATOMIC | ROLE_VIOLATION | **COMBINED** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 32 | `g22-case2-attempt2-u1` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 33 | `g22-case2-attempt2-u2` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 34 | `g22-case2-attempt2-u3` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 35 | `g22-case2-attempt2-u4` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 36 | `g22-case2-attempt2-u5` | R | C | NON_ATOMIC | ROLE_VIOLATION | **COMBINED** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 37 | `g22-case3-attempt1-u1` | O | - | INDETERMINATE | ROLE_VALID | **OPTIONAL_AMBIGUOUS** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 38 | `g22-case3-attempt1-u4` | O | - | INDETERMINATE | ROLE_VALID | **OPTIONAL_AMBIGUOUS** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 39 | `g22-case3-attempt2-u6` | O | - | INDETERMINATE | ROLE_VALID | **OPTIONAL_AMBIGUOUS** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 40 | `g22-case3-attempt2-u9` | O | - | INDETERMINATE | ROLE_VALID | **OPTIONAL_AMBIGUOUS** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |
| 41 | `g22-case3-attempt1-u2` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 42 | `g22-case3-attempt1-u3` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 43 | `g22-case3-attempt1-u5` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 44 | `g22-case3-attempt2-u7` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 45 | `g22-case3-attempt2-u8` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 46 | `g22-case3-attempt2-u10` | R | C | NON_ATOMIC | ROLE_VALID | **STRUCTURAL** | RESIDUAL_COMPOUND_RISK | N |
| 47 | `g22-case3-attempt2-u11` | O | - | NON_ATOMIC | INDETERMINATE | **OPTIONAL_AMBIGUOUS** | STRUCTURAL,RESIDUAL_SEMANTIC | Y |

## 5. v3 failure-mode interpretation by owner

### STRUCTURAL

G-23A/G-23A-Rでは、自然な一文として読める複合factを`ATOMIC`とするfalse-passが複数modelで残った。SGOKBのAtomicityは「sentence count」ではなく「部分ごとにgrounding verdictが変わり得るか」であるため、text-only汎用judgeをprimary authorityにする設計が不適切。

### DETERMINISTIC_POLICY

この5件は、少なくともprimary decisionについてsemantic inferenceを必要としない。既知のstage/path provenanceとpurpose/presentation policyで判定可能。zero-tolerance ruleに最も適した領域であり、LLM依存を除去する。

### RESIDUAL_SEMANTIC

11件はcontent typeを実際に読まないと決められない。ここだけがbounded semantic classifierの主要対象候補。ただしtruth/support判断は対象外であり、`unsupported source_fact`をrole violationにしてはならない。

### COMBINED

5件は一つのlabelに丸めると診断性を失う。v4では`structural_result`と`semantic_or_policy_result`を別々に保持し、どちらかFAILならfail-closedにする。

### OPTIONAL_AMBIGUOUS

6件はarchitecture benchmarkとして価値があるが、acceptance Gateを通すために無理にhard-labelしない。将来E5 classifier datasetへ含める場合も、train targetではなくambiguity/control setとして扱う方を第一候補とする。

## 6. Expected v4 authority

```text
STRUCTURAL
  -> Structured Proposition contract is primary.
  -> compound-risk detection is secondary.

DETERMINISTIC_POLICY
  -> application policy matrix is primary.
  -> no LLM required for rejection.

RESIDUAL_SEMANTIC
  -> narrow content-type classifier after deterministic checks.
  -> MIXED / AMBIGUOUS fail closed.

COMBINED
  -> independent structural + semantic/policy results.
  -> no later override.

OPTIONAL_AMBIGUOUS
  -> preserve ambiguity; audit/coverage only.
```

## 7. Regression assertions carried forward

1. Multi-proposition content may not reach support/derivation validation as one proposition.
2. Known purpose/presentation incompatibility must be rejected without LLM dependency.
3. Unsupported/false source_fact may still be semantically `source_fact`.
4. Content-first type must override model self-declaration.
5. Structural and semantic violations must remain independently observable.
6. No silent post-hoc split followed by rendering the original unsplit text.
7. Optional ambiguous cases must not be force-labeled to improve metrics.
8. Downstream support/derivation PASS may not override an earlier structural/policy/semantic failure.

## 8. Gate result

- 47 / 47 mapped: **PASS**
- no critical case without owner: **PASS**
- optional ambiguous cases remain explicit: **PASS**
- Gold label changes: **0 / PASS**
- required/critical flags changed: **0 / PASS**

Therefore:

```text
N-04G-23A-E1 = Complete
N-04G-23A-E2 = NEXT
N-04G-23A-E  = In Progress
G-23B        = blocked
N-04         = Failed / not Complete
N-05         = blocked
```

## 9. Next task

**N-04G-23A-E2 — v4 V2 Responsibility Boundary Design**

E2 must turn this mapping into an explicit validation order and authority model. In particular it must define structural hard-fail vs compound-risk escalation、application-owned role provenance、deterministic compatibility hard-fail order、residual classifier invocation conditions、`MIXED_CONTENT` / `AMBIGUOUS` handling、failure evidenceとstage-local retry handoff、downstream override禁止を確定する。
