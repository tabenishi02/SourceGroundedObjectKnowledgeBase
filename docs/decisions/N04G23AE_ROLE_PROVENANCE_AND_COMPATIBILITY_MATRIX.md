# N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design

更新日: 2026-10-20

- Status: **Complete / deterministic matrix fixed for E5-E7**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Predecessors:
  - `N-04G-23A-E1 — 47-Gold Responsibility Mapping` Complete
  - `N-04G-23A-E2 — v4 V2 Responsibility Boundary Design` Complete
  - `N-04G-23A-E3 — Structured Proposition Contract Design` Complete
- Authority:
  - `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`
  - `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
  - `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
  - `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
  - `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
  - `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- Machine-readable companion: `benchmark/n04g23ae-role-compatibility-v1.json`
- Frozen 47 Gold remains unchanged.
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E7 acceptance**

---

## 1. Decision summary

v4では、modelが自由に宣言する`semantic_role`をpolicy authorityとして使用しない。

normalized roleは、applicationが所有する`stage/path provenance`から決定論的に導出する。

```text
application-owned path
        ↓
V2-P role provenance normalization
        ↓
normalized_role
        ↓
V2-D deterministic compatibility matrix
        ↓
PASS | POLICY_FAIL
        ↓ PASS only
V2-R residual semantic validation when required
```

主要Decision:

1. model-authored `semantic_role` fieldをrole authorityとして使用しない。
2. provider/modelが`path_provenance`を自由生成しない。application/orchestrationが出力slotまたはconstruction pathから付与する。
3. pathごとにnormalized roleを一意に固定する。
4. purpose / presentation / support binding / premise binding / ownershipの既知不整合はV2-Dでdeterministic hard failとする。
5. V2-DのPASSは「自然言語contentが本当にそのroleである」ことを証明しない。model-authored contentは必要に応じV2-Rを通す。
6. `creative_addition`は`creative` purposeだけで許可する。
7. `source_fact`は3用途すべてで許可する。
8. `interpretation`は`comparison` / `creative`で通常許可し、`roleplay`でもG-02の限定的interpretationを完全禁止にはしない。ただしmodel-authored interpretationは全purposeでV2-R必須とする。
9. `context_limit`は3用途すべてで許可するが、system/application-owned pathだけに限定し、normal materialと同時presentしない。
10. v3で禁止したmodel-authored `stylistic_expression`はv4でも再導入しない。
11. Stage 1 fact candidateはintermediate artifactであり、presentation roleを持たない。
12. Certified factをStage 2へ渡す場合、modelがsource fact textを再発明するpathを作らず、application-owned certified materializationを第一候補とする。
13. unknown / forged / unresolved pathはfail-closedで`UNRESOLVED_PROVENANCE`とする。
14. Policy failureはV2-R、V3、MiniCheck、Fact Judge、derivation judge等でoverride不可。

---

## 2. Why path provenance is the role authority

G-23A / G-23A-Rでは、自然言語content、declared role、purpose、presentationを汎用LLM Judgeへ同時に渡した結果、次の問題が確認された。

- metadataだけで確定できるrole/purpose mismatchまでLLMがfalse-passした。
- atomicity問題をrole問題としてrejectする等、直交軸が干渉した。
- model familyを変更してもzero-tolerance Gateを満たす候補が得られなかった。

一方、v4ではG-23の2段階architectureにより、生成経路自体が意味責務を持つ。

```text
Stage 1 fact planner slot
  -> source fact candidateを作るためのpath

Stage 2 interpretation slot
  -> validated premiseからinterpretation candidateを作るpath

Stage 2 creative slot
  -> creative purposeで新規contentを作るpath

System context-limit path
  -> supplied context不足をapplicationが表すpath
```

従って、role metadataをmodelへ自己申告させてから別Judgeが検証するより、application-owned pathからexpected roleを導く方が安全で再現可能である。

ただしpath provenanceは**content semantic proofではない**。

```text
stage1_fact_candidate
```

にsource-world fact以外の内容がmodelから入った場合、path metadataが正しいという理由だけでROLE_VALIDにしてはならない。その残余境界はV2-Rの責務である。

---

## 3. Normative path taxonomy

v4 E4では次のpathを固定する。

### 3.1 `stage1_fact_candidate`

- Owner: application orchestration + Stage 1 model content
- Stage: `stage1`
- Normalized role: `source_fact`
- Model-authored content: yes
- Final presentation role: **none / forbidden at this intermediate stage**
- Allowed purpose: `roleplay`, `comparison`, `creative`
- Required binding: `support_refs[] >= 1`
- Forbidden binding: `premise_fact_ids[]`
- V2-R: required unless a later construction-specific exemption is explicitly frozen

### 3.2 `certified_fact_materialization`

Application-owned path for carrying an already Certified source fact toward Stage 2/final presentation without asking the model to regenerate factual content.

- Owner: application
- Stage: `certified_content / presentation materialization`
- Normalized role: `source_fact`
- Model-authored content: no
- Final presentation role: `main`
- Allowed purpose: `roleplay`, `comparison`, `creative`
- Support binding: inherited from Certified Content record
- `premise_fact_ids[]`: forbidden as role proof
- V2-R: `NOT_REQUIRED` only when the materialized claim text/content is exactly application-owned Certified Content or deterministic canonical rendering of it

Exact Certified Content schema is G-23C authority. Exact Stage 2 use is G-23D authority. E4 fixes only the policy direction: **no new model-authored source fact text is justified merely by citing a certified ID**.

### 3.3 `stage2_interpretation_candidate`

- Owner: application orchestration + Stage 2 model content
- Stage: `stage2`
- Normalized role: `interpretation`
- Model-authored content: yes
- Presentation role: `interpretation`
- Allowed purpose: `roleplay`, `comparison`, `creative`
- Required binding: `premise_fact_ids[] >= 1`
- Forbidden binding: raw `support_refs[]` as interpretation proof
- V2-R: required
- V4I derivation validation: required after V2 PASS

`roleplay`でのinterpretationはG-02の「ごく限定的な一時的判断・推論」を保持するためdeterministic hard-banにはしない。canonical trait / hidden backstory / stable motive等へ見えるcontentはV2-R/V4Iでfail-closedに判定する。

### 3.4 `stage2_creative_candidate`

- Owner: application orchestration + Stage 2 model content
- Stage: `stage2`
- Normalized role: `creative_addition`
- Model-authored content: yes
- Presentation role: `creative`
- Allowed purpose: **`creative` only**
- `support_refs[]`: forbidden
- `premise_fact_ids[]`: forbidden as grounding proof
- V2-R: required

source Concept / Work / Characterのfactをcreative contentとして偽装した場合、metadata compatibilityがPASSでもV2-Rで`SEMANTIC_FAIL`または`MIXED_CONTENT`にする。

### 3.5 `system_context_limit`

- Owner: application/system only
- Stage: `system`
- Normalized role: `context_limit`
- Model-authored content: no
- Presentation role: `context_limit`
- Allowed purpose: `roleplay`, `comparison`, `creative`
- `support_refs[]`: forbidden
- `premise_fact_ids[]`: forbidden
- Normal materialとのcoexistence: forbidden for the same terminal response envelope
- V2-R: `NOT_REQUIRED` when canonical application-owned reason code/payload is used

Modelのfree-form proseから`context_limit`へ自己昇格するpathは作らない。

---

## 4. Normative role provenance table

| Path provenance | Owner | Stage | Normalized role | Model text | Presentation | Residual semantic |
|---|---|---|---|---:|---|---|
| `stage1_fact_candidate` | app + model content | stage1 | `source_fact` | Yes | none | REQUIRED |
| `certified_fact_materialization` | application | certified/presentation | `source_fact` | No | `main` | NOT_REQUIRED when deterministic |
| `stage2_interpretation_candidate` | app + model content | stage2 | `interpretation` | Yes | `interpretation` | REQUIRED |
| `stage2_creative_candidate` | app + model content | stage2 | `creative_addition` | Yes | `creative` | REQUIRED |
| `system_context_limit` | application/system | system | `context_limit` | No | `context_limit` | NOT_REQUIRED when canonical |

Unknown path:

```text
V2-P = UNRESOLVED_PROVENANCE
aggregate V2 != PASS
```

Generator-declared labels never repair unknown provenance.

---

## 5. Purpose compatibility matrix

Legend:

```text
ALLOW       -> deterministic purpose compatibility PASS
ALLOW*      -> deterministic PASS, but semantic/derivation restrictions remain mandatory
DENY        -> deterministic POLICY_FAIL
```

| Normalized role | Roleplay | Comparison | Creative |
|---|---:|---:|---:|
| `source_fact` | ALLOW | ALLOW | ALLOW |
| `interpretation` | ALLOW* | ALLOW* | ALLOW* |
| `creative_addition` | **DENY** | **DENY** | ALLOW* |
| `context_limit` | ALLOW | ALLOW | ALLOW |

`ALLOW*`はsupport不要を意味しない。

- interpretationはvalidated premiseとV4I derivation PASSが必要。
- creative additionはsource knowledgeを偽装していないことをV2-Rで確認する。
- Roleplay interpretationはG-02の限定範囲を超えるcanonical-looking claimを許さない。

`creative_addition + roleplay/comparison`はsemantic classifierへ送って救済せず、V2-Dで即`POLICY_FAIL`とする。

---

## 6. Presentation compatibility matrix

Presentation roleは最終/Stage 2 presentation artifactでのみ意味を持つ。Stage 1 candidateへpresentationを混入しない。

| Path / normalized role | Required presentation | Other presentation |
|---|---|---|
| `stage1_fact_candidate` / source_fact | `none` | POLICY_FAIL |
| `certified_fact_materialization` / source_fact | `main` | POLICY_FAIL |
| `stage2_interpretation_candidate` / interpretation | `interpretation` | POLICY_FAIL |
| `stage2_creative_candidate` / creative_addition | `creative` | POLICY_FAIL |
| `system_context_limit` / context_limit | `context_limit` | POLICY_FAIL |

従って、次はLLM Judge不要でrejectできる。

```text
source_fact materialization + interpretation presentation
interpretation + main presentation
creative_addition + main presentation
context_limit + normal material presentation
stage1 candidate carrying final presentation metadata
```

### Context-limit exclusivity

`system_context_limit`をterminal responseとしてmaterializeする場合、同じresponse envelope内へnormal material blockを併存させない。

```text
context_limit + main
context_limit + interpretation
context_limit + creative
```

はdeterministic failure。

---

## 7. Binding compatibility matrix

### 7.1 Source fact candidate

`stage1_fact_candidate`:

```text
support_refs[]      REQUIRED, min 1
premise_fact_ids[]  FORBIDDEN
```

support refの存在はsupport correctnessを意味しない。resolutionはV1/V3以降で検査する。

### 7.2 Certified fact materialization

```text
new model support_refs[]      FORBIDDEN
new model premise_fact_ids[]  FORBIDDEN
```

support provenanceはCertified Contentからapplicationが継承する。

### 7.3 Interpretation

```text
premise_fact_ids[]  REQUIRED, min 1
support_refs[]      FORBIDDEN as derivation proof
```

premise IDはG-23Cで定義するCertified Fact IDだけを参照する。

### 7.4 Creative addition

```text
support_refs[]      FORBIDDEN
premise_fact_ids[]  FORBIDDEN as grounding proof
```

創作contentがsource fact supportを必要とする形なら、そもそもcreative pathへ置いてはならない。

### 7.5 Context limit

```text
support_refs[]      FORBIDDEN
premise_fact_ids[]  FORBIDDEN
```

application-owned reason/material-requirement identityを使用する。

---

## 8. V2-P normalization algorithm

Logical algorithm:

```text
input candidate
  ↓
read application-owned path_provenance
  ↓
known path?
  ├─ No  -> UNRESOLVED_PROVENANCE
  └─ Yes -> lookup normalized role / owner / stage
              ↓
           path owner consistent?
              ├─ No  -> UNRESOLVED_PROVENANCE or POLICY_FAIL
              └─ Yes -> RESOLVED(normalized_role)
```

禁止:

```text
unknown path
+ generator says semantic_role=source_fact
-> RESOLVED
```

Generator labelはdiagnosticに保存してもよいが、V2-P authorityにしない。

---

## 9. V2-D deterministic algorithm

V2-PがRESOLVEDしたcandidateだけをV2-Dへ送る。

```text
1. purpose allowed for normalized role/path?
   No -> POLICY_FAIL

2. stage/path ownership valid?
   No -> POLICY_FAIL

3. presentation state valid for this stage/path?
   No -> POLICY_FAIL

4. required binding present?
   No -> POLICY_FAIL

5. forbidden binding absent?
   No -> POLICY_FAIL

6. context-limit exclusivity / system-only ownership satisfied?
   No -> POLICY_FAIL

7. otherwise -> PASS
```

V2-Dは次を判定しない。

```text
claim truth
support entailment
interpretation derivability
creative textが実際にsource factをsmuggleしていないか
same-role free textがsemantic atomicか
```

これらはV2-R/V3/V4の責務。

---

## 10. Required deterministic failure codes

実装では少なくとも次をmachine-addressableにする。

```text
unknown_path_provenance
path_owner_mismatch
path_stage_mismatch
purpose_role_incompatible
presentation_role_incompatible
unexpected_presentation_on_intermediate
missing_support_binding
forbidden_support_binding
missing_premise_binding
forbidden_premise_binding
model_authored_context_limit_forbidden
context_limit_not_exclusive
model_authored_stylistic_expression_forbidden
```

failure evidenceにはE2で固定したstage-local fieldsを保持する。

---

## 11. `stylistic_expression` policy

G-14 v3 formal baselineで禁止したmodel-authored `stylistic_expression`をv4でも再導入しない。

理由:

- G-12でsource-world material claimのescape hatchとして実際に悪用された。
- Roleplay surface styleはsupported/certified source factのpresentationとして扱える。
- deterministic rendererが追加できる固定heading/separator等はsemantic propositionではない。

従って:

```text
path -> normalized_role = stylistic_expression
```

となるmodel-authored pathをE4 matrixへ定義しない。

provider outputにlegacy `semantic_role=stylistic_expression`が現れてもrole authorityとして採用しない。

---

## 12. Residual Semantic interaction

Deterministic matrixはsemantic classifierを完全に置換しない。

### V2-R REQUIRED

少なくとも:

- `stage1_fact_candidate` model-authored claim
- `stage2_interpretation_candidate`
- `stage2_creative_candidate`
- E3 V2-S `REVIEW_REQUIRED`
- mixed-content疑い

ではV2-Rが必要。

### V2-R NOT_REQUIRED候補

- application-owned `certified_fact_materialization`で、validated/certified claim textを変更せずmaterializeする場合
- application-owned `system_context_limit` canonical payload

ここでもV2-S/V2-D failureがあればNOT_REQUIREDによる救済はしない。

E5でclassifier taxonomy / dataset / evaluation planを確定する。

---

## 13. Relationship to Stage 1 / Certification / Stage 2

### Stage 1

Stage 1 modelはfact candidate payloadを生成するが、roleを選ばない。

```text
Stage 1 fact output slot
   ↓ application wraps
path = stage1_fact_candidate
   ↓
normalized_role = source_fact
```

### Certification

V2/V3/V4を通過したsource factだけがG-23C Certified Contentへ進む。

### Stage 2

Stage 2は:

- Certified factをID/recordとして参照
- interpretation slotで新しいinterpretationだけを生成
- creative purposeの場合だけcreative slotを利用

する方向を維持する。

Stage 2に自由な`source_fact`生成slotを再設置しない。

source factのhuman-facing materializationは`certified_fact_materialization`のapplication-owned pathを第一候補とする。最終契約はG-23Dで確定する。

---

## 14. Retry implications

Policy failureは「roleを別ラベルへ付け替える」retryを許さない。

例:

```text
stage2_creative_candidate
purpose = roleplay
```

に対して:

```text
semantic_roleをsource_factに変えて再利用
```

のようなsilent salvageは禁止。

正しいrepairはpath/stage requirementに従う。

- Stage 1 source factが必要ならStage 1 pathで新candidateを作る。
- interpretationならCertified premiseを与えStage 2 interpretation pathで再生成する。
- creativeがpurpose不一致ならcreative content自体を削除/再計画する。
- failed candidate identityは保持し、新candidateへretry lineageを張る。

---

## 15. 47-Gold coverage expectation

E1で`DETERMINISTIC_POLICY` primaryとなった5件、および`COMBINED`のpolicy側は、本MatrixでLLM Judgeなしに処理できることをE6でdesk replayする。

代表例:

```text
creative_addition + roleplay
source_fact + interpretation presentation
interpretation + main presentation
interpretation without premise binding
context_limit mixed with source-world output
```

E4ではGold labelを変更しない。E6でcaseごとにmatrix coverageを照合する。

---

## 16. Protected boundaries

E4では変更しない。

- G-23A frozen 47 Gold labels / required / critical flags
- G-23A-R historical benchmark result
- G-14 one material proposition / fail-closed intent
- G-16 source-fact / interpretation verifier separation
- G-23 two-stage generation decision
- E2 authority order
- E3 Semi-structured proposition decision
- MiniCheck threshold
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition

---

## 17. E4 completion gate

- [x] application-owned role provenance authority fixed
- [x] minimum stage/path taxonomy fixed
- [x] normalized role per path fixed
- [x] purpose compatibility matrix fixed
- [x] presentation compatibility matrix fixed
- [x] support/premise binding matrix fixed
- [x] context-limit system ownership/exclusivity fixed
- [x] stylistic-expression non-reintroduction fixed
- [x] deterministic failure categories fixed
- [x] policy PASS separated from semantic role proof
- [x] V2-R required/not-required interaction documented
- [x] G-23C/G-23D future boundary preserved

G-23A-E4を**Complete**とする。

次Task:

```text
N-04G-23A-E5 — Residual Classifier Scope / Evaluation Design
```
