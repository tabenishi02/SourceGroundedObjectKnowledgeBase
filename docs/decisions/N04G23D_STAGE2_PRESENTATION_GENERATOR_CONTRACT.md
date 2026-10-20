# N-04G-23D — Stage 2 Presentation Generator Contract

更新日: 2026-10-21

- Status: **Complete / Contract Accepted**
- Parent: `N-04G-23 — Two-Stage Grounded Generation Architecture`
- Predecessor: `N-04G-23C — Complete / Contract Accepted`
- Next: `N-04G-23E — Provider Schema + Stage-local Retry Design`
- N-04: **Failed / not Complete**
- N-05: **blocked**

Authority:

- `docs/decisions/N04G23C_CERTIFICATION_AND_CERTIFIED_CONTENT_CONTRACT.md`
- `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
- `docs/decisions/N04G02_CLAIM_TAXONOMY_AND_USE_CASE_BOUNDARIES.md`

---

## 1. Decision summary

v4 Stage 2 Presentation Generatorは、**Certified Contentをprimary factual authorityとして、許可されたpresentation planだけを生成する**。

Stage 2は「何がsource factとして正しいか」を再決定しない。

Normative flow:

```text
Certified Content
  ↓
Application-owned Stage 2 request / minimal projection
  ↓
Stage 2 model
  ↓
Presentation plan
  ├─ Certified Fact references only
  ├─ Interpretation candidates
  └─ Creative candidates where purpose permits
  ↓
Application path assignment / deterministic materialization
  ↓
Final V2 / V4I / binding / presentation validation
  ↓ PASS only
Material Requirement
  ↓
Terminal / Render authorization
```

G-23Dで次を固定する。

1. Stage 2 request ownershipとlogical contract。
2. minimal model-facing Certified Content projection。
3. source-fact presentationをCertified Fact ID reference + application materializationに限定する。
4. Stage 2 modelによるsource-fact rewriteを禁止する。
5. interpretation candidate contractとpremise binding。
6. creative candidate contractとpurpose restriction。
7. ordered presentation block contract。
8. output slotからapplication-owned pathを導出する規則。
9. purpose別allowed block policy。
10. presentation-role cardinality / separation invariants。
11. Stage 2 outputからfinal validationへのhandoff。
12. evidence / replay requirements。

Provider-specific JSON Schema feature support、exact schema dialect、stage-local retry message layout、cross-attempt salvageはG-23Eでfreezeする。

Residual Atomicity / Content-Type classifierの具体model/checkpoint/thresholdは引き続きG-25Aの責務である。

---

## 2. Protected authority boundary

Stage 2 modelへ次のauthorityを与えない。

```text
generator-owned authoritative semantic_role
model-owned source-fact certification
model-owned support / entailment PASS
model-owned validation status
model-owned context_limit authority
raw Grounded Context as new factual authority
uncertified Stage 1 candidate as factual authority
model-memory factual supplementation
free paraphrase of Certified Fact with inherited certification
```

禁止する解釈:

```text
model cites CF1
-> any rewritten factual sentence is certified

model places text in a main block
-> source_fact role is valid

model labels text interpretation
-> derivation is valid

model places source-world fact in creative block
-> creative content is valid
```

すべて誤りである。

Application-owned path provenance、deterministic compatibility、Residual Content-Type、support/derivation validationは維持する。

---

## 3. Stage 2 request contract

Stage 2 request envelopeはapplication-ownedである。

Logical form:

```json
{
  "request_contract_version": "sgokb.stage2-presentation-request.v1",
  "stage2_request_id": "S2R...",
  "source_request_id": "R...",
  "certified_content_id": "CC...",
  "certified_content_digest": "...",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "stage": "stage2",
  "attempt": 1,
  "allowed_output_kinds": ["certified_fact", "interpretation"],
  "presentation_instruction": "...",
  "certified_facts": [
    {
      "certified_fact_id": "CF1",
      "claim_text": "..."
    }
  ]
}
```

これはlogical contractでありprovider-specific schemaではない。

### 3.1 Application-owned fields

次はmodelにauthority fieldとして生成させない。

```text
request_contract_version
stage2_request_id
source_request_id
certified_content_id
certified_content_digest
context_fingerprint
purpose
stage
attempt
allowed_output_kinds
retry lineage
```

### 3.2 `presentation_instruction`

`presentation_instruction`はユーザー要求・use-case objective・format要求をStage 2へ伝えるために使用できる。

ただし、そこに含まれるsource-world factual assertionを新しいfactual authorityとして使用してはならない。

Normative rule:

```text
presentation_instruction
  -> controls task/style/selection intent
  -> does NOT certify new source-world facts
```

ユーザー入力由来の新しいfactをsource factual materialとして利用する必要がある将来caseでは、別のgrounding/certification pathが必要である。

---

## 4. Minimal model-facing Certified Content projection

Stage 2 modelへ渡すfactual projectionは必要最小限とする。

v1 minimum:

```json
{
  "certified_fact_id": "CF1",
  "claim_text": "exact certified text"
}
```

Model-facing projectionへ原則渡さない:

```text
raw Grounded Context
K support text
support verifier scores
Atomicity classifier verdict/scores
Content-Type classifier verdict/scores
validation_record internals
critical/required labels
canonical DB direct access
```

理由:

- Stage 1 / Certification boundaryを迂回したnew source fact generationを防ぐ。
- validator verdictによるgeneration primingを減らす。
- Stage 2 failureをselection / interpretation / creative / presentationへ局所化する。

`certified_fact_id`と`claim_text`以外のapplication-owned grouping metadataが将来必要になった場合、G-23F以降でfailure evidenceに基づき追加する。G-23D v1では新しいsemantic metadata体系を導入しない。

---

## 5. Stage 2 model response contract

Stage 2 model responseは、**ordered presentation blocks**を生成する。

Logical form:

```json
{
  "blocks": [
    {
      "block_kind": "main",
      "certified_fact_ids": ["CF1", "CF2"]
    },
    {
      "block_kind": "interpretation",
      "candidates": [
        {
          "claim_text": "...",
          "premise_fact_ids": ["CF1", "CF2"]
        }
      ]
    },
    {
      "block_kind": "creative",
      "candidates": [
        {
          "claim_text": "..."
        }
      ]
    }
  ]
}
```

`block_kind`はmodelによるsemantic-role自己証明ではない。

Applicationはparsed output slotからpathを割り当てる。

```text
main.certified_fact_ids[]
  -> certified_fact_materialization
  -> normalized role source_fact

interpretation.candidates[]
  -> stage2_interpretation_candidate
  -> normalized role interpretation

creative.candidates[]
  -> stage2_creative_candidate
  -> normalized role creative_addition
```

各model-authored free textは、slot metadataだけでsemantic PASSにならない。

---

## 6. Source-fact presentation path

### 6.1 Model selects IDs; application owns text

Stage 2 modelがsource factual materialについて選択できるのは原則`certified_fact_id`だけとする。

```text
model output: CF1
  ↓
application resolves CF1 in active Certified Content
  ↓
application materializes exact Certified Fact claim_text
```

Model responseにsource-fact `claim_text`を再出力させない。

### 6.2 `certified_fact_materialization`

E4 reserved pathを正式採用する。

```text
path = certified_fact_materialization
owner = application
normalized_role = source_fact
presentation = main
model-authored factual text = no
```

Materialized source factはactive Certified Contentのexact logical string valueを使用する。

```text
rendered source fact content == Certified Fact claim_text
```

G-23Dではmodel-authored paraphraseを許可しない。

### 6.3 Deterministic surface wrappers

Applicationはcontent propositionを変えないdeterministic wrapperを使用してよい。

例:

- fixed heading
- bullet marker
- numbering
- fixed separator
- source/interpretation/creative section marker

Wrapperはsource fact textへ語句を追加して新しいpropositionを作ってはならない。

自由な言い換え、代名詞変換、first-person/third-person変換はdeterministic wrapperには含めない。

Purpose-specific natural wordingが必要な場合は、Stage 1がpurpose-awareに生成・certifyしたclaim textを利用する。

---

## 7. Interpretation candidate contract

Interpretation output slotのcandidateは次だけをmodel生成する。

```json
{
  "claim_text": "...",
  "premise_fact_ids": ["CF1", "CF2"]
}
```

Required:

```text
claim_text
premise_fact_ids[] >= 1
```

Forbidden:

```text
support_refs[]
semantic_role
validation_status
derivation_status
certification_status
presentation_role
raw K IDs as premise proof
```

### 7.1 Premise integrity

すべての`premise_fact_ids[]`はactive Certified Content artifact内で解決できなければならない。

Unknown / stale / cross-artifact IDはdeterministic fail。

Interpretation candidateはuncertified candidate、raw K、model memory、raw Grounded Contextをpremise authorityとして使用しない。

### 7.2 Interpretation validation

Applicationがoutput slotから:

```text
path_provenance = stage2_interpretation_candidate
```

を付与する。

その後、少なくとも:

```text
V2-S
V2-P
V2-D
V2-R-A
V2-R-C
V4I derivation validation
```

をrequired policyに従い通過する。

Premise bindingがvalidでもderivation PASSではない。

Interpretationの`claim_text`はmodel-authoredなので、failed textをsilent rewriteしてPASSへ変換しない。

---

## 8. Creative candidate contract

Creative output slotのcandidateは次だけをmodel生成する。

```json
{
  "claim_text": "..."
}
```

Required:

```text
claim_text
```

Forbidden:

```text
support_refs[]
premise_fact_ids[] as grounding proof
semantic_role
validation_status
certification_status
presentation_role
```

Applicationがoutput slotから:

```text
path_provenance = stage2_creative_candidate
```

を付与する。

### 8.1 Purpose restriction

Creative candidateは`purpose = creative`の場合のみ許可する。

```text
creative + creative purpose   -> deterministic policy may continue
creative + roleplay purpose   -> POLICY_FAIL
creative + comparison purpose -> POLICY_FAIL
```

Semantic classifierへ送ってrescueしない。

### 8.2 Source-world fact smuggling

Creative slotへsource Concept / Work / Characterについてのfactual assertionを入れてもcreativeとして自動許可しない。

Model-authored creative textはV2-R-A / V2-R-C required policyへ従う。

Observed contentがsource fact / mixed / ambiguousならfail-closed。

---

## 9. Purpose-specific allowed output kinds

E4 purpose compatibilityをStage 2 requestへ投影する。

| Purpose | Certified source facts | Interpretation | Creative addition |
|---|---:|---:|---:|
| `roleplay` | ALLOW | ALLOW* | DENY |
| `comparison` | ALLOW | ALLOW* | DENY |
| `creative` | ALLOW | ALLOW* | ALLOW* |

`ALLOW*`はsemantic/derivation validation不要を意味しない。

Roleplay interpretationは、G-02/E4の限定範囲を維持し、canonical trait / hidden backstory / stable motive等へ昇格するcontentを許可しない。

Stage 2 v4ではmodel-authored `stylistic_expression`専用pathを再導入しない。

`context_limit`もStage 2 model output kindではない。必要な場合はapplication/system-owned `system_context_limit` pathを使用する。

---

## 10. Presentation block invariants

### 10.1 Allowed block kinds

v1 Stage 2 normal outputで許可するblock kind:

```text
main
interpretation
creative
```

`context_limit`はmodel response blockとして許可しない。

### 10.2 Cardinality

Logical acceptance rule:

```text
0 or 1 main block
0 or 1 interpretation block
0 or 1 creative block
```

同一`block_kind`の重複はdeterministic presentation failureとする。

```text
duplicate main
-> FAIL

duplicate interpretation
-> FAIL

duplicate creative
-> FAIL
```

Provider schemaで直接強制できるかはG-23Eでprobeする。Providerが強制できなくてもapplication validatorでruleを維持する。

### 10.3 Block order

`blocks[]`の順序はpresentation orderとして扱う。

ただしblock orderはsemantic role authorityではない。

Block kindと内容のpath assignmentはslot discriminatorから決定する。

### 10.4 Empty blocks

空blockは生成しない。

```text
main.certified_fact_ids[] >= 1
interpretation.candidates[] >= 1
creative.candidates[] >= 1
```

Stage 2全体として安全なpresentation proposalがない場合、`blocks: []`を許可できる。

これは`context_limit` verdictではない。

Applicationがretry / Material Requirement / terminal policyを判断する。

---

## 11. Presentation separation

Final materialはsource fact / interpretation / creativeを構造上区別可能でなければならない。

Application rendererはvalidated block roleを保持する。

Minimum invariant:

```text
main material
!= interpretation material
!= creative material
```

Interpretationやcreative textをmain/source-fact surfaceへsilent mergeしない。

Creative/interpretation separationを人間が認識可能にするexact label/templateはrenderer contractでdeterministicに固定する方向とし、G-23Fで統合確認する。

Modelが自由なheading文を生成し、それをrole authorityにしない。

---

## 12. No-new-source-fact rule after certification

Stage 2以降、source-world factual materialとしてrender可能なのは原則:

```text
active Certified Content fact
  ↓ exact application-owned materialization
```

だけである。

次は禁止:

- Certified Factのmodel paraphraseをsource_factとしてrender
- interpretationから新しいfactual clauseを切り出してsource_factへ昇格
- creative text内のsource-world assertionをmainへ昇格
- user instruction中のfactを未certifiedのままmainへ出力
- raw Grounded Contextを再読して新規source fact生成

新しいsource factが必要ならStage 1 / validation / certificationへ戻す。

---

## 13. Candidate identities after Stage 2 parse

Applicationはmodel-authored interpretation / creative itemへ新しいproposition identityを割り当てる。

Logical envelope:

```text
stage2_request_id
certified_content_id / digest
context_fingerprint
purpose
stage = stage2
attempt
path_provenance
proposition_id
block index
candidate index
claim_text
premise_fact_ids[] where applicable
```

Modelに`proposition_id`や`path_provenance`を生成させない。

Failed Stage 2 candidateはimmutableとする。

Retryで修正する場合は新しいidentityを発行し、lineageをapplicationが保持する。Exact retry policyはG-23Eでfreezeする。

---

## 14. Stage 2 validation handoff

### 14.1 Main/source facts

Main blockの`certified_fact_ids[]`はapplicationがdeterministicに解決する。

Required checks:

```text
ID exists in active Certified Content
no duplicate ID within main block unless explicitly allowed later
Certified Content digest binding matches Stage 2 request
materialized content exact-match
```

Exact materialization pathはE4 `certified_fact_materialization`なので、meaning contentがapplication-owned exact materializationである限りResidual semantic classificationはE5 policy上`NOT_REQUIRED`候補である。

### 14.2 Interpretation

Interpretation candidateはV2 + V4Iを通す。

V4Iはpremise fact supportを再判定せず、Certified Fact premise集合だけからclaimがreasonableに導けるかを判定する。

### 14.3 Creative

Creative candidateはV2 role/content boundaryを通す。

Creative qualityそのものをgrounding authorityとして判定しないが、source-world fact smuggling / mixed content / forbidden purposeはrejectする。

### 14.4 Aggregate

Earlier FAIL / INDETERMINATEは後続positive verdictでoverride不可。

Final grounding/presentation PASSのみMaterial Requirementへ進む。

---

## 15. Material Requirement interaction

Stage 2 contractはMaterial Requirement rubricを緩和しない。

Applicationはvalidated Stage 2 resultからMaterial Requirementを評価する。

例方向:

```text
roleplay:
  required certified factual material exists and is presented

comparison:
  required factual material from comparison targets is present
  + required interpretation/contrast requirement is satisfied

creative:
  required source Concept certified material is present
  + required creative material is present
```

Stage 2 model自身に`material_requirement_pass`を宣言させない。

Semantic distinctness / target coverageのexact machine policyは既存benchmark/material profileとG-23F統合時に確認する。

---

## 16. Evidence / reproducibility requirements

G-23E/G-23F/G-26でStage 2を独立replayできるよう、最低限保存する。

```text
Stage 2 request contract version
stage2_request_id
source request / Certified Content identity
Certified Content digest
minimal model-facing projection and digest
purpose / allowed output kinds
Stage 2 prompt artifact + hash
provider schema artifact + hash when frozen
model/runtime/settings identity
raw Stage 2 model output
parsed Stage 2 output
application-assigned path/proposition identities
source fact materialization map
Stage 2 candidate digests
V2/V4I/final validation records/evidence
retry feedback / lineage when invoked
rendered block plan / deterministic renderer identity
```

Raw Grounded ContextをStage 2 evidenceとしてfactual input扱いしない。

---

## 17. G-23D explicit decisions

### D1 — Source fact selection

**採用: model selects Certified Fact IDs; application materializes exact text.**

理由:

- presentation relevance/orderをmodelへ委ねられる。
- factual wording authorityをmodelへ戻さない。
- Certified Content boundaryを保つ。

Application-only fixed selectionは将来optimization可能だが、v4標準contractではmodelのID selectionを許可する。

### D2 — Model-facing fact projection

**採用: `certified_fact_id + exact claim_text` minimum.**

Validation/support internalsは通常渡さない。

### D3 — Output representation

**採用: ordered role-discriminated blocks.**

Role declarationそのものをauthorityにするのではなく、schema slotからapplication pathを導出する。

### D4 — Source fact rewriting

**不採用。**

Model-authored factual paraphraseはcertificationを継承しない。

### D5 — Interpretation

**採用: model `claim_text + premise_fact_ids[]`; Certified Fact IDs only.**

### D6 — Creative

**採用: model `claim_text` only; `creative` purpose only.**

### D7 — Context limit

**Stage 2 model outputとして不採用。**

Application/system-owned pathを維持する。

### D8 — Stylistic expression

**独立model-authored pathとして再導入しない。**

Source factual wordingのpurpose adaptationはStage 1でcertifyする。Presentation wrapperはapplication-owned deterministic surfaceに限定する。

---

## 18. What G-23D does not decide

G-23Dでは次をfreezeしない。

- LM Studio / llama.cpp等provider-specific schema dialect。
- `contains/minContains/maxContains`等のruntime support結果。
- provider message layout。
- exact retry count / retry feedback serialization。
- cross-attempt salvage policy。
- canonical JSON hashing implementation。
- concrete Residual Atomicity / Content-Type classifier。
- Stage 2 concrete generator model/checkpoint。
- final Reference Workstation runtime freeze。

これらはG-23E/G-23F/G-24/G-25/G-26へ残す。

---

## 19. Acceptance checklist

- [x] Certified Content is the Stage 2 primary factual authority.
- [x] Raw Grounded Context is not reopened as source-fact authority.
- [x] Source facts are model-selected by ID and application-materialized exactly.
- [x] Model-authored factual rewrite does not inherit certification.
- [x] Interpretation uses Certified Fact IDs only.
- [x] Creative output is creative-purpose only.
- [x] Model-authored context_limit authority is not introduced.
- [x] Model-authored stylistic_expression path is not reintroduced.
- [x] Output slot -> application-owned path provenance is fixed.
- [x] presentation role cardinality is deterministic and fail-closed.
- [x] interpretation / creative model text remains subject to semantic validation.
- [x] no-new-source-fact rule after certification is explicit.
- [x] evidence/replay requirements are defined.
- [x] provider schema/retry implementation details remain G-23E.
- [x] G-23C protected boundary remains unchanged.

Result:

```text
N-04G-23D = Complete / Contract Accepted
N-04G-23E = NEXT
N-04       = Failed / not Complete
N-05       = blocked
```
