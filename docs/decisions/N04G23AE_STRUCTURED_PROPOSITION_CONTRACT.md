# N-04G-23A-E3 — Structured Proposition Contract Design

更新日: 2026-10-20

- Status: **Complete / Option B selected**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Predecessors:
  - `N-04G-23A-E1 — 47-Gold Responsibility Mapping` Complete
  - `N-04G-23A-E2 — v4 V2 Responsibility Boundary Design` Complete
- Authority:
  - `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
  - `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`
  - `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
  - `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
  - `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
- Historical v3 output implementation remains unchanged: `src/sgokb/grounding/output.py`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E7 acceptance**

---

## 1. Decision summary

v4のStructured Proposition intermediate contractには、比較した3案のうち **Option B — Semi-structured proposition record** を採用する。

ただし、単なる `id + text + refs` ではなく、次の原則を持つ **application-owned envelope + path-discriminated proposition record** とする。

```text
Application-owned envelope
  ├─ contract/version identity
  ├─ context fingerprint
  ├─ purpose
  ├─ stage / path provenance
  ├─ attempt / retry lineage
  └─ application-assigned proposition identity
        ↓
Path-specific proposition payload
  ├─ one authoritative proposition text
  ├─ optional semantic anchors / hints
  └─ role-specific bindings
        ├─ source support refs
        ├─ certified premise ids
        └─ no-grounding-ref creative/system paths where allowed
```

重要なDecision:

1. `semantic_role`をmodel-authored authority fieldとしてStructured Propositionへ持ち込まない。
2. stage/path provenance、purpose、context fingerprint、attempt、proposition identityはapplication-ownedとする。
3. modelはproposition contentと許可されたreference selectionだけを生成する。
4. validation/certification statusをmodel outputへ含めない。validator-owned別recordに分離する。
5. source fact / interpretation / creative / context-limitでbinding shapeを分ける。
6. `support_refs[]`と`premise_fact_ids[]`を同一recordで混在させない。
7. Structured Proposition contractは「1 record = 1 candidate proposition」を必須にするが、model-authored free textのsemantic atomicityをschemaだけで証明したと偽装しない。
8. application/systemが意味内容までdeterministicに構成したrecordのみ、construction aloneでV2-S PASS候補になれる。
9. model-authored propositionは、E3 contractだけでsemantic atomicityを証明できない場合 `REVIEW_REQUIRED` とし、E5で設計するbounded residual atomicity/semantic checkへ送る。
10. post-hoc atomizerで元textを分割して一部だけcertifyし、元の未分割textをrenderする方式は禁止を維持する。
11. certified source factは将来 `certified_fact_id` を持ち、Stage 2はそのIDを参照する。詳細はG-23Cで確定する。
12. final human-facing text contractは本TaskでFreezeしない。G-23DでStage 2 contractとして設計する。

---

## 2. Compared options

### Option A — Minimal proposition record

概念:

```text
id + provenance + text + refs
```

#### 利点

- schemaが単純。
- arbitrary natural-language contentを失わない。
- Stage 1 modelに要求するstructured output負荷が低い。

#### 欠点

- v3 `unit_id + text + refs` と本質的差が小さい。
- path/role misuse以外のAtomicity問題を構造的に減らしにくい。
- semantic understandingが必要なcaseをほぼすべて後段classifierへ残す。
- E1 `STRUCTURAL` 20件に対するarchitecture改善が弱い。

#### Decision

**不採用。**

Backward-compatibleではあるが、G-23A/G-23A-Rで確認した責務過多を十分減らせない。

---

### Option B — Semi-structured proposition record

概念:

```text
application-owned identity/provenance
+ one proposition text
+ path-specific reference binding
+ optional subject/entity/predicate anchors
```

#### 利点

- arbitrary textを保持し、Interpretation / Creativeを無理にRDF-like tupleへ押し込まない。
- application-owned pathとrole-specific binding shapeを使ってmixed-policy recordを減らせる。
- Stage 1 / Certification / Stage 2を同一proposition identityで接続しやすい。
- support refsとpremise idsをschema上分離できる。
- model-authored role自己申告をauthorityから外せる。
- optional anchorsをdiagnostic / risk detection / future deterministic handlingに使える。
- schemaだけでは証明できないAtomicityを`REVIEW_REQUIRED`として正直に残せる。

#### 欠点

- free text内のsame-role multi-proposition compressionはschemaだけでは完全に防げない。
- residual atomicity checkは依然必要。
- optional anchorがmodel-authoredの場合、それ自体をgrounding authorityにできない。

#### Decision

**採用。**

表現力を維持しながら、deterministic/structural authorityを増やせる最もバランスのよい案である。

---

### Option C — Fully normalized predicate/value record

概念:

```text
subject + predicate + object/value + qualifiers
```

#### 利点

- source factの一部は非常にmachine-checkしやすい。
- proposition boundaryをschemaへ強く押し込める。
- equality / duplicate / relation cardinality等をdeterministicに扱いやすい。

#### 欠点

- arbitrary narrative fact、modal claim、temporal/event relation、comparison conclusion、creative propositionをlosslessに表現するにはpredicate ontologyが急速に膨張する。
- SGOKB canonical object modelとは別に、generation専用semantic ontologyを実質的に新設することになる。
- normalized tupleとhuman meaningのずれを再検証する必要が生じる。
- modelが誤ったpredicate/value decompositionを出す新しいfailure modeが増える。
- G-23の目的はgrounded generation remediationであり、汎用knowledge representation redesignではない。

#### Decision

**不採用。**

一部source fact path向けの将来最適化として再検討可能だが、v4共通contractには採用しない。

---

## 3. Contract layers

v4ではCandidate、Validation、Certificationを別artifactとして扱う。

```text
Structured Proposition Candidate
        ↓ immutable candidate content
V2/V3/V4 validation evidence
        ↓
Proposition Validation Record
        ↓ PASS only
Certified Content Record
        ↓
Stage 2 references certified IDs
```

Modelがvalidation resultやcertification statusを自己申告しない。

### 3.1 Candidate artifact

Model/systemから得た「検証対象」を保持する。

最低限:

```text
proposition_id
path_provenance
claim_text or system-owned canonical payload
binding payload
candidate identity / digest
```

### 3.2 Validation artifact

Application/validatorが所有する。

例:

```text
v2_structural_result
v2_provenance_result
v2_policy_result
v2_residual_result
v3_support_result
v4 verifier evidence
failure codes / retry evidence
```

Candidate payloadを書き換えてPASSへ変換しない。

### 3.3 Certified Content artifact

全required Gateを通過したcandidateだけからapplicationが作る。

source factについては将来:

```text
certified_fact_id
source proposition identity
validated claim text
validated support binding
context fingerprint
validation evidence identity
```

を持つ方向とする。

正確なschemaはG-23Cで確定する。

---

## 4. Application-owned envelope

次のfieldはmodelに自由生成させない。

```text
contract_version
context_fingerprint
purpose
stage
path_provenance
attempt
proposition_id
retry_parent_id / retry lineage
request identity / context binding
```

Logical candidate envelope:

```json
{
  "contract_version": "sgokb.structured-proposition.v1-candidate",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "stage": "stage1",
  "attempt": 1,
  "propositions": [
    {
      "proposition_id": "P1",
      "path_provenance": "stage1_fact_candidate",
      "payload": {
        "claim_text": "...",
        "support_refs": ["K3"]
      }
    }
  ]
}
```

これはlogical contract例であり、provider-facing JSON SchemaそのものはG-23B/G-23FでFreezeする。

### Ownership

| Field | Owner | Model authority? |
|---|---|---:|
| contract_version | application | No |
| context_fingerprint | application | No |
| purpose | application/request | No |
| stage | application | No |
| path_provenance | application/orchestration | No |
| attempt | application | No |
| proposition_id | application | No |
| retry lineage | application | No |
| claim_text | model or system by path | Yes, content only |
| support_refs | model selection, validator checks | Limited |
| premise_fact_ids | model selection from allowed certified IDs, validator checks | Limited |
| subject/entity hints | model optional diagnostic | No grounding authority |
| predicate hints | model optional diagnostic | No grounding authority |
| validation disposition | validator | No |
| certification status | application/validator | No |

---

## 5. Proposition identity and retry identity

### 5.1 proposition_id

`proposition_id`はapplicationが割り当てる。

性質:

- one generation attempt内でunique。
- providerが任意IDを発行する必要はない。
- validation / failure / audit evidenceのjoin keyとなる。
- Stage 2へ直接渡す长期IDではない。

### 5.2 Candidate digest

Candidate contentにはcanonical digestを持てる。

Digest input候補:

```text
context_fingerprint
purpose
stage/path provenance
attempt
claim_text/canonical payload
binding payload
```

Exact serializationはimplementation taskで固定する。

### 5.3 Retry

Retryで新しいcandidateを生成した場合、同じ`proposition_id`を無理に再利用しない。

代わりにapplication-owned lineage:

```text
retry_parent_id
failure_source_proposition_id
retry_attempt
```

を保持する。

これにより「失敗したtextを別textへ置換したのに同一propositionとして扱う」identity混同を防ぐ。

---

## 6. Path-discriminated payloads

E3では少なくとも次のlogical pathを想定する。

```text
stage1_fact_candidate
stage2_interpretation_candidate
stage2_creative_candidate
system_context_limit
```

normalized roleとの最終対応表はE4で固定する。

### 6.1 Stage 1 fact candidate

Required candidate content:

```text
claim_text
support_refs[]
```

Optional diagnostic anchors:

```text
subject_refs[]
predicate_hint
object_refs[]
```

Rules:

- `support_refs[]`は1件以上。
- `premise_fact_ids[]`を持たない。
- creative payload fieldを持たない。
- anchorsはsupport/truth authorityではない。
- one recordにone candidate propositionを要求する。

### 6.2 Stage 2 interpretation candidate

Required candidate content:

```text
claim_text
premise_fact_ids[]
```

Rules:

- premiseはG-23Cで定義するcertified fact IDだけを参照する。
- raw K refsをinterpretation derivation proofとして直接使わない。
- `support_refs[]`を持たない。
- premise factual textをinterpretation claim本文へ再埋込して複合化しない。

G-16のpremise separationを継承する。

### 6.3 Stage 2 creative candidate

Required candidate content:

```text
claim_text
```

Optional source-reference metadataはE4/G-23Dで必要性を判断する。

Rules:

- source fact support bindingを持たない。
- `premise_fact_ids[]`をinterpretation proofとして持たない。
- source Concept/Work/Characterのfactをcreative contentとして偽装しない。
- one recordに複数invented events/state transitionsを圧縮しない。

### 6.4 system_context_limit

Application/system-owned only。

Model自由textによるcontext-limit自己申告をauthorityにしない。

候補:

```text
limit_code
material requirement identity
context fingerprint
```

必要ならapplicationがcanonical display textを後段でmaterializeする。

---

## 7. Structured Proposition text policy

### 7.1 Exactly one authoritative proposition content field

Model-authoredcandidateは原則1つの`claim_text`を持つ。

`summary`, `explanation`, `rationale`, `final_text`等の別content fieldを同一candidateにmodel生成させない。

理由:

- validation対象が複数になり同期問題が再発する。
- unsupported contentの別field escapeを作る。

### 7.2 claim_text is immutable during validation

Validatorは`claim_text`をsilent rewriteしない。

non-atomicなら:

```text
reject / review-required
→ retry
→ new candidate
```

とする。

### 7.3 Stage 2 final presentationとの分離

E3 candidate textをそのまま最終render sourceとするか、certified IDからStage 2が別presentation recordを作るかはG-23Dで確定する。

ただしStage 2がsource factを新しく発明してよい、という意味ではない。

---

## 8. Semi-structured anchors

Option Bでは次のanchorを許可候補とする。

```text
subject_refs[]
predicate_hint
object_refs[]
```

### Purpose

- duplicate / mixed-entity risk検出
- relation/predicate family別のbenchmark分析
- Stage 1 promptのdecomposition補助
- retry feedbackの具体化
- future structured optimization

### Non-authority rule

Model-authored anchorは次のauthorityではない。

```text
truth authority
support authority
semantic role authority
Atomicity PASS authority
```

例えば:

```text
predicate_hint = "developer"
claim_text = "Fate/stay night is a Japanese visual novel developed by Type-Moon."
```

なら、predicate_hintが1件だからといってATOMIC PASSにしてはならない。

---

## 9. V2-S construction states

E2の`PASS / REVIEW_REQUIRED / FAIL`をE3 contractへ具体化する。

### 9.1 Hard `FAIL`

最低限:

- unknown contract version
- missing application-owned identity/binding
- duplicate proposition_id within attempt
- missing path provenance
- path-specific required field missing
- forbidden binding combination
- `support_refs` + `premise_fact_ids` coexistence
- model-authored `system_context_limit`
- model attempts to supply validator-owned disposition/certification fields
- empty candidate content
- explicitly multiple proposition payload objects packed into one proposition record

### 9.2 `PASS_BY_CONSTRUCTION`

V2-S construction aloneでPASS候補にできるのは、application/systemがmeaning-bearing contentまでdeterministicに所有するpathに限定する。

候補:

- system-owned `context_limit`
- certified fact IDからapplicationがdeterministically materializeするsource-fact record
- future application-generated canonical record where no model free-text can add material proposition

この集合はE4/G-23C/G-23Dで明示的に列挙する。

### 9.3 `REVIEW_REQUIRED`

原則としてmodel-authored free-text propositionはここから開始する。

理由:

Semi-structured contractはboundary/bindingを強化するが、free textが本当に1 semantic propositionだけかをJSON Schema aloneでは証明できない。

`REVIEW_REQUIRED`はfailureではなく、residual atomicity reviewが必要という状態である。

---

## 10. Residual resolution of `REVIEW_REQUIRED`

E2のauthority modelと矛盾しないよう、次の二段構造とする。

```text
V2-S construction_result
  PASS_BY_CONSTRUCTION
  REVIEW_REQUIRED
  FAIL

if REVIEW_REQUIRED:
  residual_atomicity_result
    ATOMIC
    NON_ATOMIC
    INDETERMINATE
```

Aggregate structural result:

```text
PASS_BY_CONSTRUCTION                  -> V2-S PASS
REVIEW_REQUIRED + ATOMIC              -> V2-S PASS
REVIEW_REQUIRED + NON_ATOMIC          -> V2-S FAIL
REVIEW_REQUIRED + INDETERMINATE       -> V2-S INDETERMINATE
FAIL                                  -> V2-S FAIL
```

Residual componentはhard structural FAILをoverrideしない。

Residual atomicity mechanism/modelの選定はE5で設計する。

---

## 11. Separation from semantic-role classification

Atomicity resolutionとcontent-type classificationは別dimensionとして保持する。

例:

```text
atomicity_result = ATOMIC
content_type     = INTERPRETATION_CONTENT
```

または:

```text
atomicity_result = NON_ATOMIC
content_type     = SOURCE_FACT_CONTENT
```

を許す。

G-23A/G-23A-Rで発生した「bad unitだからwrong role」とするcouplingを再導入しない。

E5でclassifierを1 model callにまとめる場合でも、logical verdict fieldsと評価metricsは分離する。

---

## 12. Certification boundary

Structured Proposition Candidate自身に次を書かない。

```text
supported = true
atomic = true
role_valid = true
certified = true
confidence = 0.98
```

Certificationはvalidator/application authorityである。

Stage 1 source factの流れ:

```text
Structured Fact Candidate
  ↓ V2
Atomic / Role-valid
  ↓ V3/V4F
Supported
  ↓
Certified Fact
  ↓
certified_fact_id
```

Stage 2はraw Stage 1 candidate IDではなく、原則certified IDを参照する。

---

## 13. Rendering separation

E3 recordをFinal Output contractと同一視しない。

v4は2-stage architectureであるため、概念上:

```text
Stage 1 proposition candidate
  ↓
Certified Content
  ↓
Stage 2 presentation candidate
  ↓
Final validation / material / render
```

となる。

Requirements:

- Stage 2 source-fact presentationはcertified factとのbindingを失わない。
- Stage 2で新しいsource-world factを自由生成しない。
- final presentationのvalidated materialとrendered textの対応を保持する。
- v3の「別final responseだけにunsupported detailが入る」問題を再導入しない。

詳細はG-23D/G-23Eで確定する。

---

## 14. Versioning

Structured Proposition contractはv3 output contractとは別contract lineとする。

候補identity:

```text
sgokb.structured-proposition.v1
```

ただしE3時点ではlogical design identityであり、provider/application JSON Schema hashをFreezeしない。

Version rule:

- required field semantics変更 -> major contract revision
- optional diagnostic anchor追加 -> compatible minor extension候補
- application-owned fieldをmodel-ownedへ変更 -> incompatible revision
- path/binding semantics変更 -> incompatible revision

Formal version/hashはG-23F Design Freezeで確定する。

---

## 15. Mapping to E1 owner classes

### STRUCTURAL 20

改善点:

- proposition boundaryをrecordとして明示。
- path-specific binding混在をschemaで禁止。
- model free-textは`REVIEW_REQUIRED`となり、無条件ATOMIC PASSを防止。
- retryはfailed proposition単位で行える。

Same-role multi-proposition compressionはE5 residual atomicityに残るため、E6でcoverageを検証する。

### DETERMINISTIC_POLICY 5

E3は必要metadata/pathをapplication-owned envelopeへ固定し、E4 policy matrixがLLMなしで判定できる前提を提供する。

### RESIDUAL_SEMANTIC 11

E3はrole自己申告をauthorityから外し、content-only classifierへ渡せるcandidateを作る。

### COMBINED 5

同一candidateについて:

```text
structural result
policy/semantic result
```

を独立に保持できる。

### OPTIONAL_AMBIGUOUS 6

Schema都合でforce-labelしない。`REVIEW_REQUIRED / INDETERMINATE`経路を保持する。

---

## 16. Compatibility with G-14 / G-16 / G-23

### G-14

Preserved:

- one validation unit = one proposition invariant
- no punctuation-only Atomicity authority
- no silent post-hoc atomization
- INDETERMINATE cannot PASS
- model role declaration not authority

### G-16

Preserved:

- source fact support validation and interpretation derivation are separate
- interpretation references validated fact premises, not raw K refs as proof
- unresolved/unsupported premise cannot reach derivation PASS

### G-23

Preserved:

- Stage 1 determines what may be said
- Stage 2 determines how certified content is presented
- source factual freedom is constrained before presentation

---

## 17. What E3 does not decide

The following remain for later tasks.

### E4

- exact path -> normalized role mapping
- purpose/presentation compatibility matrix
- premise/support requirement matrix
- deterministic `POLICY_FAIL` codes

### E5

- residual atomicity mechanism
- residual content-type classifier taxonomy
- model/classifier selection methodology
- dataset expansion / holdout policy

### G-23B

- exact Stage 1 provider-facing schema
- Stage 1 prompt
- candidate count/budget
- generation settings

### G-23C

- exact Certified Content schema
- `certified_fact_id` lifecycle
- certification evidence binding

### G-23D

- Stage 2 presentation schema
- certified fact materialization rules
- interpretation/creative presentation contract

### G-23F

- final contract versions/hashes
- migration and Freeze

---

## 18. E3 completion gate

| Gate | Result |
|---|---|
| Compare Minimal / Semi-structured / Fully normalized | PASS |
| Select one contract family | **PASS — Semi-structured** |
| Stage 1 can produce candidate records | PASS |
| Certification can consume immutable candidate identity | PASS |
| Stage 2 can reference future certified IDs | PASS |
| G-14 silent post-hoc atomization prohibition preserved | PASS |
| role authority removed from generator self-declaration | PASS |
| support vs premise binding separated | PASS |
| arbitrary SGOKB semantics preserved without rigid ontology | PASS |
| free-text Atomicity limitation explicitly fail-closed | PASS |
| historical v3 evidence unchanged | PASS |

**N-04G-23A-E3 = Complete.**

Next: **N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design**.
