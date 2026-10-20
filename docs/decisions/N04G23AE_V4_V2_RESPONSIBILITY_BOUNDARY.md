# N-04G-23A-E2 — v4 V2 Responsibility Boundary Design

更新日: 2026-10-20

- Status: **Complete / design boundary fixed for E3-E6**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Predecessor: `N-04G-23A-E1 — 47-Gold Responsibility Mapping` Complete
- Authority:
  - `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
  - `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
  - `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Frozen Gold remains unchanged: `benchmark/n04g23a-atomicity-role-gold-v1.json`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E7 acceptance**

---

## 1. Decision summary

v4 V2は、v3の`Atomicity + Role`を一つのgeneral-purpose LLM Judgeへ委ねる方式を採用しない。

V2を次の独立authorityへ分解する。

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

全体順序:

```text
Structured Proposition Candidate
        ↓
V2-S Structural Proposition Gate
        ↓ PASS / REVIEW_REQUIRED only
V2-P Role Provenance Normalization
        ↓
V2-D Deterministic Compatibility Gate
        ↓ PASS only
V2-R Residual Semantic Gate
        ↓ PASS or NOT_REQUIRED only
V3+ Support / Derivation validation
```

V2の最終PASS条件:

```text
V2-S = PASS
AND
V2-P = RESOLVED
AND
V2-D = PASS
AND
V2-R in {PASS, NOT_REQUIRED}
```

以下はV2 PASSにならない。

```text
STRUCTURAL_FAIL
POLICY_FAIL
SEMANTIC_FAIL
INDETERMINATE
MIXED_CONTENT
UNRESOLVED_PROVENANCE
```

後段のV3/V4/V5、MiniCheck、Fact Judge、derivation judge等は、V2のFAIL/INDETERMINATEをoverrideできない。

---

## 2. Why this boundary is required

E1では47 Goldを次に分類した。

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
```

この結果から、全件を同一LLM Judgeへ送る設計は責務過多である。

特に:

- 20件はAtomicityをStructured Proposition contract側へ移すべきである。
- 5件は既知metadataだけでpolicy mismatchを確定できる。
- 11件のみがcontent-first semantic classificationをprimary responsibilityとして必要とする。
- 5件はstructural failureとsemantic/policy failureを独立して保持すべきである。
- 6件はFrozen Gold自身がoptional ambiguousであり、無理にhard-labelしない。

従ってv4は、確率的Judgeの精度を上げるより前に、判定authorityを分ける。

---

## 3. Normative authority model

### 3.1 V2-S — Structural Proposition Gate

**Authority owner:** application validator + E3で定義するStructured Proposition contract。

責務:

- required proposition fields / schema shape
- proposition identity
- stage/path binding presence
- source/premise reference shape
- one validation recordが一つのpropositionとして構成されていること
- incompatible proposition kindsを一recordへ構造的に混在させないこと
- E3で定義するconstruction proof / proposition representation invariants

V2-Sは、自然言語textだけを見て一般的なLLM Judgeへ「atomicか」と聞くGateではない。

ただしE3が採用するschemaがfree-text意味内容を完全には拘束できない場合、V2-Sはその事実を隠して`PASS`を与えてはならない。その場合はcompound-risk / unresolved semantic atomicityを検知して`REVIEW_REQUIRED`へ送る。

### 3.2 V2-P — Role Provenance Normalization

**Authority owner:** application orchestration / stage path。

Generatorが自由に宣言した`semantic_role`はpolicy authorityではない。

最低限、次の生成経路からapplicationがrole provenanceを導出する方向を固定する。

```text
stage1_fact_candidate           -> source_fact candidate
stage2_interpretation_candidate -> interpretation candidate
stage2_creative_candidate       -> creative_addition candidate
system_context_limit            -> context_limit
```

正確なfield/schemaはE3/E4で確定する。

V2-Pでprovenanceを一意に解決できない場合:

```text
UNRESOLVED_PROVENANCE
```

としてfail-closedにする。

### 3.3 V2-D — Deterministic Compatibility Gate

**Authority owner:** application policy matrix。

既にstructured inputとして存在する情報だけで違反を判定できるものは、Residual classifierへ委譲しない。

最低限判定対象:

```text
normalized role
stage/path
purpose
presentation_role
support requirement
premise requirement
```

例:

```text
creative_addition + non-creative purpose -> POLICY_FAIL
interpretation + main presentation        -> POLICY_FAIL
source_fact + interpretation presentation -> POLICY_FAIL
interpretation missing premise binding    -> POLICY_FAIL
context_limit in source-world-only slot   -> POLICY_FAIL
```

V2-D FAIL後にResidual classifierを呼び、その結果で救済してはならない。

### 3.4 V2-R — Residual Semantic Gate

**Authority owner:** E5で選定するbounded semantic classifier / classifier cascade。

対象は、V2-S/V2-Dでは判定できないcontent-first semantic boundaryだけに限定する。

候補taxonomy:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

このtaxonomy名自体はE5で最終確定する。

Residual classifierは原則としてgenerator-declared `semantic_role`をauthority inputとして使用しない。自然言語contentを分類し、その結果をapplication-owned provenanceと比較する。

Truth/support/entailment/retrieval correctnessはV2-Rの責務ではない。

---

## 4. Exact validation order

v4 V2のnormative orderを次に固定する。

### Step 0 — envelope / reference precondition

V2へ入る前に、V0/V1相当のschema/reference integrity preconditionを満たしていること。

欠損したID、壊れたreference、未知schema等をV2-Rへ送らない。

### Step 1 — structural schema validation

```text
input shape
required IDs
stage/path provenance field presence
support/premise reference shape
record cardinality / allowed field combinations
```

明示的なschema/contract違反は`STRUCTURAL_FAIL`。

### Step 2 — proposition construction validation

E3で定義するStructured Proposition contractに基づいて、recordが一つのvalidation propositionとして構成されているか確認する。

結果:

```text
PASS
REVIEW_REQUIRED
FAIL
```

- `FAIL`: 構造上明確な複合/不正record。
- `REVIEW_REQUIRED`: schemaだけではsemantic atomicityを証明できず追加判定が必要。
- `PASS`: E3 contractが定めるconstruction invariantを満たす。

### Step 3 — role provenance normalization

application/stage pathからexpected normalized roleを求める。

結果:

```text
RESOLVED(role)
UNRESOLVED_PROVENANCE
```

Generatorの自由ラベルを根拠にRESOLVEDへ昇格しない。

### Step 4 — deterministic compatibility

resolved roleとpurpose/presentation/premise/support/stageをpolicy matrixへ照合する。

結果:

```text
PASS
POLICY_FAIL
```

`POLICY_FAIL`はhard fail。

### Step 5 — residual semantic dispatch decision

Step 2の状態、content origin、role pathに基づいてResidual classifierが必要か決定する。

```text
REQUIRED
NOT_REQUIRED
```

具体的dispatch ruleはSection 7で固定する。

### Step 6 — residual semantic classification

必要なcaseのみ実行する。

結果:

```text
PASS
SEMANTIC_FAIL
INDETERMINATE
MIXED_CONTENT
```

`INDETERMINATE`と`MIXED_CONTENT`はgrounded PASSへ進めない。

### Step 7 — V2 aggregate

```text
PASS
FAIL
INDETERMINATE
```

V2 PASSのみV3以降へ進む。

---

## 5. Hard deterministic reject boundary

次の種類はclassifier結果を待たずhard rejectできる。

### 5.1 Schema / reference-shape violation

例:

- proposition_id欠損/重複
- stage provenance欠損
- forbidden field combination
- interpretation pathなのにrequired premise binding fieldが欠損
- source fact pathなのにE3 contract上必須なsource/support binding shapeが欠損

正確なfield requirementはE3/E4で確定する。

### 5.2 Stage/path vs purpose violation

例:

```text
stage2_creative_candidate + roleplay purpose
```

のようにpolicy tableで禁止されるもの。

### 5.3 Role vs presentation violation

例:

```text
source_fact + interpretation presentation
interpretation + main presentation
```

### 5.4 Required binding violation

例:

```text
interpretation candidate without premise_fact_ids
```

### 5.5 System-owned path violation

system-only `context_limit` pathをmodel-authored source-world slotへ混入する等、path ownershipを破るもの。

Hard rejectは後続classifier/support PASSでoverride不可。

---

## 6. Compound-risk is not itself a verdict

次は**risk signal**として扱い、単独で`NON_ATOMIC`を確定しない。

候補:

- multiple sentence boundaries
- causal connectors (`because`, equivalent structures)
- contrastive connectors (`but`, `although`, etc.)
- multiple finite-clause heads
- multiple source entities/predicates
- premise + conclusion linguistic patterns
- source-world statement + context availability phrase
- long creative narrative containing multiple event/state transitions

G-14の規則どおり、句読点・`and`・文数だけをAtomicity authorityにしない。

Risk signalの用途:

```text
risk absent
  -> E3 construction proofが十分ならV2-S PASS候補

risk present
  -> REVIEW_REQUIRED
  -> residual atomicity/content review or retry
```

E3/E5はfalse-negative riskを考慮して、どのconstruction pathならrisk detectorなしでPASS可能かを明示しなければならない。

---

## 7. Residual classifier invocation conditions

### 7.1 Mandatory invocation

少なくとも次はV2-Rを必要とする。

1. E1 `RESIDUAL_SEMANTIC` primary casesに相当するmodel-authored content。
2. E1 `COMBINED` casesのsemantic側判定。
3. V2-Sが`REVIEW_REQUIRED`を返し、自然言語semantic atomicity/content mixingの解決が必要なcase。
4. content typeとapplication-owned provenanceの一致がstructured metadataだけでは証明できないmodel-authored material。
5. source-world fact / interpretation / creative / context-limitの混在疑いがあるcase。

### 7.2 Invocation not required for immediate rejection

次はclassifier不要でFAILにできる。

- V2-S hard structural FAIL
- V2-P unresolved provenance
- V2-D deterministic POLICY_FAIL

Optional auditとしてclassifierを実行してもよいが、production verdictを変更してはならない。

### 7.3 Invocation may be NOT_REQUIRED for acceptance

Residual classifierを省略してPASS可能なのは、E3/E4で**construction semanticsがapplication-ownedにより十分拘束されているpath**だけとする。

例候補:

- application自身が生成する固定`context_limit` record
- certified fact IDからapplicationがdeterministic materializeするsource_fact surface
- schema/field semanticsがcontent typeを一意に決め、model free-textがrole authorityを持たないrecord

この範囲はE3/E4で明示的に列挙する。単に「metadataが整合している」だけを理由に`NOT_REQUIRED`にしてはならない。

---

## 8. `MIXED_CONTENT` / `AMBIGUOUS` semantics

### 8.1 MIXED_CONTENT

一つのrecord/textに異なるgrounding policyを必要とするmaterial contentが混在する場合。

例:

```text
source fact + interpretation conclusion
source fact + context limit
creative content + source Concept factual assertion
```

結果:

```text
V2 = FAIL
retryable candidate = yes
```

silent splitして一部だけ救済しない。

### 8.2 AMBIGUOUS / INDETERMINATE

安全にcontent type/atomicityを決められない場合。

結果:

```text
V2 = INDETERMINATE
render authorization = prohibited
support validation = prohibited
retryable candidate = yes, bounded by retry policy
```

retry上限後も曖昧ならterminal fail-closedへ進む。

### 8.3 Frozen optional ambiguous Gold

E1の6 optional ambiguous caseは、E2でhard-labelへ変更しない。

これらはE5/E6で:

- ambiguity fixture
- classifier abstention fixture
- coverage audit

として扱う。

---

## 9. Independent verdict dimensions

v4では、一つのjoint labelだけに圧縮しない。

Candidate internal result shape:

```text
structural_result
  PASS | FAIL | REVIEW_REQUIRED

provenance_result
  RESOLVED | UNRESOLVED

deterministic_policy_result
  PASS | FAIL

residual_semantic_result
  PASS | FAIL | INDETERMINATE | MIXED_CONTENT | NOT_REQUIRED

aggregate_v2_result
  PASS | FAIL | INDETERMINATE
```

これによりE1 `COMBINED` caseで:

```text
structural_result = FAIL
semantic_result   = FAIL
```

を同時に保持できる。

診断目的で複数failureを収集してもよいが、最初のhard failureを後段がoverrideしない。

---

## 10. Authority precedence

precedenceは次に固定する。

```text
1. schema/reference contract
2. structural proposition contract
3. application-owned role provenance
4. deterministic compatibility policy
5. residual semantic classifier
6. support / derivation verifier
7. material / terminal / renderer
```

重要規則:

- higher-number authorityはlower-number authorityのFAILをPASSへ変更できない。
- supportされているからrole violationを救済、は禁止。
- semantic classifierがROLE_VALID相当でもdeterministic policy violationを救済、は禁止。
- downstream rendererは未認証unitをmaterializeしない。

---

## 11. Support / derivation boundary

V2はtruth/supportを判定しない。

例:

```text
Saber is Shirou's sibling.
```

がcontent typeとしてsource factでatomicなら、V2はROLE_VALID/atomic pathを通過可能である。unsupportedかどうかはV3+の責務である。

従ってResidual classifierへ次を要求しない。

- factual correctness
- entailment
- source support
- retrieval relevance
- confidence as calibrated truth probability

この分離はG-23A Goldの`unsupported-source-fact-still-role-valid`等を保護する。

---

## 12. Stage-local failure evidence contract

E2ではretryへ渡す最低限のfailure envelopeを固定する。field名の最終schemaはE3/E4/E5で調整可能だが、意味責務は変更しない。

最低限:

```text
failed_stage
failed_gate
failure_authority
failure_code
proposition_id
unit_text_or_proposition_text
stage_path
normalized_expected_role
observed_content_class (if available)
purpose
presentation_role
support_refs / premise_ids (if applicable)
risk_signals
expected_rule
repair_directive
```

原則:

- Structural failureはStage 1/2の該当propositionだけを修正対象にする。
- deterministic policy failureはrole/purpose/presentation/pathを修正対象にする。
- semantic failureはfailed textとexpected/observed classを返す。
- Stage 2 failureでCertified Contentを無条件再生成しない。
- Stage 1 failureでStage 2を開始しない。
- retry feedbackは失敗した本文を含める。unit IDだけにしない。

---

## 13. Retryability matrix

E2のboundaryとして次を固定する。

| Failure | Retryable | Notes |
|---|---:|---|
| malformed schema / parser failure | Yes, bounded | same request/context; repair structure |
| structural proposition failure | Yes, bounded | regenerate/split at source stage; no silent post-hoc salvage |
| unresolved provenance | Yes, bounded | path/schema repair |
| deterministic policy violation | Yes, bounded | regenerate within allowed path/purpose/presentation |
| semantic content mismatch | Yes, bounded | rewrite/regenerate same intended role |
| MIXED_CONTENT | Yes, bounded | regenerate as separate legal proposition(s), not hidden split |
| INDETERMINATE | Yes, bounded | if still unresolved after max retries -> terminal fail-closed |
| support/derivation failure | existing later-stage policy | outside E2 responsibility |

Exact retry count remains governed by later integrated v4 retry design; E2 does not change historical v3 retry count.

---

## 14. E1 owner mapping to E2 routes

### STRUCTURAL — 20 cases

Primary route:

```text
V2-S
```

Secondary protection:

```text
compound-risk -> V2-R if construction proof is insufficient
```

Goal: natural sentence plausibility must no longer cause a broad Judge to false-pass a compound proposition.

### DETERMINISTIC_POLICY — 5 cases

Primary route:

```text
V2-P -> V2-D
```

Known policy mismatch is hard reject before V2-R.

### RESIDUAL_SEMANTIC — 11 cases

Primary route:

```text
V2-S -> V2-P -> V2-D -> V2-R
```

V2-R decides only content type/boundary, not support/truth.

### COMBINED — 5 cases

Routes remain independent:

```text
V2-S failure
+
V2-D or V2-R failure
```

One failure does not erase the other from diagnostic evidence.

### OPTIONAL_AMBIGUOUS — 6 cases

Route:

```text
V2-S/V2-R may abstain
-> INDETERMINATE is allowed as diagnostic outcome
-> never forced to PASS for acceptance convenience
```

---

## 15. What E2 intentionally does not decide

E2 fixes authority/order, not final schemas/models.

Deferred:

### E3

- exact Structured Proposition schema
- minimal vs semi-structured vs normalized representation
- construction proof details
- which paths can obtain `V2-R = NOT_REQUIRED` by construction

### E4

- exact role provenance field names
- full compatibility matrix
- exact purpose/presentation/premise/support policy table

### E5

- final residual taxonomy
- classifier architecture/model
- training/evaluation dataset
- thresholds / abstention mechanism
- latency/runtime profile

### E6

- desk replay of all 47 Gold against completed E3-E5 design

従ってE2は、将来の実装選択を先取りしてFreezeしない。

---

## 16. Protected invariants

E2は次を維持する。

1. `1 validation unit = 1 atomic semantic proposition`.
2. Atomicityはindependent grounding verdict split testに基づく。
3. semantic roleはgenerator declarationがauthorityではない。
4. source-world factをsupport-free roleへ逃がさない。
5. interpretationへsource factual premiseを埋め込まない。
6. non-atomic / ambiguous contentを後段support PASSで救済しない。
7. silent post-hoc atomization禁止。
8. `INDETERMINATE -> PASS`禁止。
9. frozen 47 Gold labels/flags不変。
10. zero-tolerance critical false-pass policy不変。
11. G-23 two-stage architecture不変。
12. historical G-22/G-23A/G-23A-R evidence不変。

---

## 17. Acceptance of E2

E2完了条件:

- [x] semantic classifierより前のchecksを定義
- [x] hard deterministic reject boundaryを定義
- [x] compound-riskとverdictを分離
- [x] role provenance authorityをapplication/stage pathへ固定
- [x] residual classifier invocation条件を定義
- [x] `MIXED_CONTENT` / `AMBIGUOUS` fail-closedを定義
- [x] downstream support override禁止を定義
- [x] stage-local failure evidenceを定義
- [x] E1の5 owner classをV2 routeへ接続
- [x] E3/E4/E5へのdeferred decisionを明示

Result:

```text
N-04G-23A-E2 = Complete
N-04G-23A-E3 = NEXT
N-04G-23A-E  = In Progress
N-04G-23B    = blocked
N-04         = Failed / not Complete
N-05         = blocked
```

---

## 18. Immediate next task

**N-04G-23A-E3 — Structured Proposition Contract Design**

E2でauthorityとvalidation orderは固定された。次はV2-Sが何を`PASS`、`REVIEW_REQUIRED`、`FAIL`として機械的に扱えるかを決めるため、Structured Proposition intermediate contractを設計する。
