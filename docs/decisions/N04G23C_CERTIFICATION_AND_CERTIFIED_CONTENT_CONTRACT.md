# N-04G-23C — Certification / Certified Content Contract

更新日: 2026-10-21

- Status: **Complete / Contract Accepted**
- Parent: `N-04G-23 — Two-Stage Grounded Generation Architecture`
- Predecessor: `N-04G-23B — Complete / Contract Accepted`
- Next: `N-04G-23D — Stage 2 Presentation Generator Contract`
- N-04: **Failed / not Complete**
- N-05: **blocked**

Authority:

- `docs/decisions/N04G23B_STAGE1_GROUNDED_CONTENT_PLANNER_CONTRACT.md`
- `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
- `docs/decisions/N04G23AE_INTEGRATION_AND_G23B_UNBLOCK_DECISION.md`
- `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- `docs/decisions/N04G16_SEMANTIC_VALIDATION_ARCHITECTURE_REDESIGN.md`

---

## 1. Decision summary

v4のCertificationは、Stage 1 model outputを修正・再生成する工程ではない。

**immutable Stage 1 Structured Proposition Candidate**と、application/validator-ownedの**immutable Validation Record**がrequired GateをすべてPASSした場合に限り、applicationが新しい**Certified Fact**を発行する工程とする。

Normative flow:

```text
Stage 1 model payload
  ↓
Application-owned Structured Proposition Candidate
  ↓ immutable
Reference integrity / V2 / V3 / V4 validation
  ↓
Validation Record
  ↓ required PASS only
Application certification
  ↓
Certified Fact
  ↓
Certified Content artifact
  ↓
Stage 2 Presentation Generator
```

Artifact boundary:

```text
Candidate artifact
  != Validation Record
  != Certified Fact
  != Certified Content container
```

Certificationは新しいsemantic judgeではない。Certificationは既存authorityのPASS evidenceを検証し、candidate contentを変更せず次段へfreezeするapplication-owned boundaryである。

G-23Cで次を固定する。

1. certification eligibility condition。
2. Validation Record / Certified Fact / Certified Content separation。
3. `certified_fact_id` ownershipとscope。
4. immutable Stage 1 candidateへのbinding。
5. certified `claim_text` / `support_refs` exact-copy rule。
6. validation evidence identity / digest chain。
7. request / context / retry lineage。
8. duplicate handlingのdeterministic minimum policy。
9. Certified Content version / digest / replay identity。
10. Stage 2 factual-input boundary。
11. non-certification / empty certification semantics。
12. G-23D/G-23E/G-26向けevidence requirements。

Residual Atomicity / Content-Type classifierの具体model/checkpoint/thresholdは本Taskでは選定しない。`N-04G-25A`の責務である。

---

## 2. Protected authority boundary

Certificationへ次のauthorityを新設してはならない。

```text
model-owned certification status
model-owned support / entailment PASS
generator-declared semantic_role authority
certification-time semantic rewrite
certification-time post-hoc atomization
new source-world fact generation during certification
certification-time use of model memory / Web / uncited raw context
```

禁止する解釈:

```text
candidate exists
-> certified

support_refs exist
-> certified

V2 PASS only
-> certified

certification process rewrote a failed candidate into a valid one
-> certified
```

すべて誤りである。

Certificationはfail-closedであり、required evidenceが欠損・不整合・INDETERMINATE・UNAVAILABLEの場合はCertified Factを発行しない。

---

## 3. Certification eligibility

G-23Cの対象はStage 1 path:

```text
stage1_fact_candidate
  -> normalized role = source_fact
```

のみである。

一つのcandidateからCertified Factを発行できるのは、少なくとも次をすべて満たす場合だけとする。

```text
1. Candidate contract / identity binding valid
2. Reference integrity PASS
3. V2 aggregate PASS
4. Source-support aggregate PASS
5. Candidate digest and Validation Record binding match
6. No unresolved FAIL / INDETERMINATE / UNAVAILABLE remains
```

### 3.1 V2 requirement

E2〜E7で定義したV2 authority/orderをそのまま使用する。

```text
V2-S
  ↓
V2-P
  ↓
V2-D
  ↓
V2-R-A when required
  ↓
V2-R-C when required
  ↓
aggregate V2 PASS only
```

Stage 1のmodel-authored free textについて、schema validityだけでResidual Atomicity / Content-Type判定を省略しない。

G-23CはV2 sub-verdictの意味を再定義しない。Certificationが見るnormative conditionは、E2〜E7に従って**aggregate V2がPASSとして確定していること**である。

### 3.2 Source-support requirement

Source fact supportはG-16系authorityを継承する。

安全にdeterministic supportが確定できるcandidateは、frozen policyに従うV3 deterministic support PASSでsource-support aggregateを満たせる。

V3でunresolvedとなるcandidateは、required V4F source-fact verificationを通過し、最終source-support aggregateがPASS / supportedで確定した場合のみcertification可能とする。

Certification自身はsupportを再判定しない。

### 3.3 Earlier failure cannot be rescued

```text
V2 FAIL / INDETERMINATE
+ V4 support positive
-> NOT CERTIFIABLE
```

```text
V2 PASS
+ support unresolved / unavailable
-> NOT CERTIFIABLE
```

後段positive verdictによるearlier failure救済は禁止を維持する。

---

## 4. Validation Record contract boundary

Validation Recordはcandidateとは別のapplication/validator-owned immutable artifactとする。

最低限、Certificationが参照できるlogical fields:

```text
validation_contract_version
validation_record_id
source_proposition_id
source_candidate_digest
context_fingerprint
reference_integrity_result
v2_aggregate_result
source_support_aggregate_result
component_evidence_refs[]
validation_record_digest
```

実装上、V2-S/P/D/R-A/R-CやV3/V4Fの詳細sub-resultをValidation Record内部へ保持してよい。

ただしCertified Fact側へ全sub-verdictを複製して第二のauthority recordを作らない。

### 4.1 Component evidence chain

Validation Recordは必要なcomponent evidenceへのID/digest bindingを持つ。

例:

```text
reference integrity evidence
V2 structural/provenance/policy evidence
Residual Atomicity evidence
Residual Content-Type evidence
V3 deterministic-support evidence
V4F verifier/judge evidence when invoked
```

Certificationはこれらのraw verdictを再解釈せず、frozen validation policyによるaggregate resultとidentity bindingを確認する。

### 4.2 Validation Record immutability

一度validation evidenceとして保存したrecordを書き換えてPASSへ変更しない。

再validationが必要な場合:

```text
new Validation Record identity
+ explicit lineage to prior record if needed
```

とする。

Exact serialization / hash implementationはG-23E/G-24で固定する。

---

## 5. Certified Fact contract

Certified Factはapplicationが発行するsource-fact runtime/evidence artifactであり、canonical Knowledge DBへ新しいFact entityを追加するものではない。

Logical form:

```json
{
  "certified_fact_id": "CF1",
  "source_proposition_id": "P...",
  "source_candidate_digest": "...",
  "claim_text": "...",
  "support_refs": ["K3"],
  "validation_record_id": "VR...",
  "validation_record_digest": "...",
  "request_id": "R...",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "source_attempt": 1,
  "source_candidate_index": 0
}
```

これはlogical contract例であり、provider-facing schemaではない。

### 5.1 `certified_fact_id`

`certified_fact_id`はapplication-ownedである。

Normative semantics:

- modelが生成しない。
- Certified Content artifact内でunique。
- そのartifactがimmutableである限りstable。
- Stage 2がpremise/source-materialを参照するjoin keyとして使用する。
- canonical DBのObject/Statement/Relation identityではない。
- repository-global permanent Fact IDではない。
- 別Certification runで同じID文字列が現れても、`certified_content_id`との組でscopeを解決する。
- 一度あるcontentへ割り当てたIDを、同じartifact内で別contentへ再利用しない。

このscopeにより、N-04 remediation目的で新しいcanonical Fact identity体系を導入しない。

### 5.2 Source candidate binding

Certified Factは必ず一つのimmutable Stage 1 proposition candidateへ直接bindする。

最低限:

```text
source_proposition_id
source_candidate_digest
```

を保持する。

Candidate text/supportを変更した場合、digest mismatchとなり同じCertified Factとして扱えない。

---

## 6. Certified claim text semantics

Certification時の`claim_text`はStage 1 candidateの`claim_text`を**そのままコピー**する。

Normative rule:

```text
certified.claim_text == candidate.payload.claim_text
```

Certificationで禁止:

- trimによる意味/証跡差分の隠蔽
- punctuation repair
- paraphrase
- shortening
- explanation追加
- clause split
- clause merge
- canonical-looking factual補完

実装上のJSON encoding差は許容されるが、parse後のlogical string valueは一致しなければならない。

Candidateが不適切ならCertificationで修正せず、non-certification / retryへ戻す。

---

## 7. Certified support binding semantics

`support_refs[]`もStage 1 candidateからexact-copyする。

```text
certified.support_refs == candidate.payload.support_refs
```

Certification時に次を行わない。

```text
add support ref
drop support ref
merge refs from another candidate
replace with "better" support
fetch new K item
```

Support validityはValidation RecordにbindされたV1/V3/V4 evidenceで証明する。

Certified Factの`support_refs[]`自体はsupport PASS authorityではない。

---

## 8. Certified Content container

複数Certified FactをStage 2へ渡すapplication-owned containerとして、次のlogical contractを採用する。

```json
{
  "certified_content_contract_version": "sgokb.certified-content.v1",
  "certified_content_id": "CC...",
  "request_id": "R...",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "facts": [
    {
      "certified_fact_id": "CF1",
      "source_proposition_id": "P1",
      "source_candidate_digest": "...",
      "claim_text": "...",
      "support_refs": ["K3"],
      "validation_record_id": "VR1",
      "validation_record_digest": "...",
      "source_attempt": 1,
      "source_candidate_index": 0
    }
  ]
}
```

### 8.1 Container ownership

すべてapplication-owned assemblyである。

Modelに次を生成させない。

```text
certified_content_id
certified_fact_id
certification status
validation evidence identity
source candidate identity
```

### 8.2 Context isolation

一つのCertified Content artifactへ異なる`context_fingerprint`のfactを混在させない。

Cross-context mergeが必要な将来use caseは別contract/versionで設計する。

### 8.3 Purpose lineage

`purpose`はrequest lineageとして保持する。

Certified Factのtruth/roleをpurposeが決定するわけではない。

Stage 2 policy compatibilityの入力としてapplicationが使用できる。

---

## 9. Multiple facts and ordering semantics

`facts[]`のarray orderは次を意味しない。

```text
presentation order
importance
confidence
support strength
semantic grouping
```

Replayのためapplicationはdeterministic orderを使用する。

推奨canonical ordering key:

```text
source_attempt
source_candidate_index
source_proposition_id
```

Exact serialization / tie-break ruleはG-23E/G-24でfreezeする。

Stage 2はarray orderをpresentation authorityとして使用しない。

---

## 10. Duplicate handling

Certificationでsemantic equivalence判定を新しいLLM authorityとして導入しない。

### 10.1 Exact duplicate minimum rule

次がすべて同一のeligible candidateはdeterministic exact duplicateとして扱える。

```text
same context_fingerprint
same logical claim_text
same support_refs sequence/set under frozen canonicalization
```

同一Certification set内でexact duplicateが検出された場合、後続duplicate candidateから別Certified Factを発行せず、application-owned non-certification reason:

```text
NOT_CERTIFIED_EXACT_DUPLICATE
```

とし、既存Certified Fact IDへのreferenceをevidenceとして保持してよい。

これにより単純duplicateによるMaterial count水増しを防ぐ。

### 10.2 Semantic-equivalent but non-identical content

次はG-23Cで自動mergeしない。

- paraphrase
- same claim with different support set
- partially overlapping proposition
- semantically similar but non-identical statement

これらをmergeするにはsemantic equivalence authorityが必要になるため、本Taskのscope外とする。

Material Requirement側でdistinctnessが必要な場合はG-23D/G-23Fで明示的に設計する。

---

## 11. Certified Content versioning / digest / replay identity

Contract version:

```text
sgokb.certified-content.v1
```

Certified Content artifactはimmutableとする。

次のいずれかが変わる場合、同じartifactを更新せず新しいidentity/digestを作る。

```text
fact membership
fact order under canonical form
claim_text
support_refs
source candidate binding
validation record binding
context_fingerprint
purpose/request lineage
contract semantics
```

Replay identityとして最低限次をbindする。

```text
certified_content_contract_version
certified_content_id
request_id
context_fingerprint
purpose
ordered certified_fact payloads
source_candidate_digest per fact
validation_record_digest per fact
```

各Certified Factにもcontent digestを持たせてよい。

Exact canonical JSON serialization / SHA-256 implementation / digest field placementはG-23E/G-24でfreezeする。ただしdigest計算でself-referential fieldを含めない。

---

## 12. Empty Certified Content

eligible factが0件の場合でも、audit/replay目的で空のCertified Content artifactを作成してよい。

```json
{
  "certified_content_contract_version": "sgokb.certified-content.v1",
  "certified_content_id": "CC...",
  "request_id": "R...",
  "context_fingerprint": "...",
  "purpose": "comparison",
  "facts": []
}
```

これは次を意味するだけである。

```text
No source-fact material was certified for this certification set.
```

これは`context_limit` verdictではない。

Stage 2実行可否、retry、Material Requirement、system-owned context-limit/terminal handlingは後続policyに従う。

---

## 13. Retry / cross-attempt boundary

G-23Cはindividual candidateのcertification eligibilityを定義するが、複数Stage 1 attemptからどのeligible factを最終Certified Content setへ採用するかという**cross-attempt salvage policyはfreezeしない**。

理由:

- Stage-local retry orchestrationはG-23E責務である。
- 旧partial-salvage prohibitionとの整合をG-23Eで明示する必要がある。

従ってG-23Cは以下だけを固定する。

- 各Certified Factはsource attempt / candidate identityを保持する。
- failed candidateをrewriteしてcertifyしない。
- retry candidateは新proposition identityを持つ。
- cross-attempt inclusion ruleはG-23Eでfreezeするまでimplicitに推測しない。

---

## 14. Stage 2 factual-input boundary

Stage 2のprimary factual authorityは**Certified Content**とする。

原則:

```text
Stage 2 model factual input
  = certified facts selected/projected from one Certified Content artifact
```

raw Grounded Context全文をStage 2へ再提示し、それを新規source fact生成authorityとして使用しない。

### 14.1 Certified source fact path

E4のreserved pathを維持する。

```text
certified_fact_materialization
  -> normalized role = source_fact
  -> application-owned
```

Stage 2でsource factを表示する場合、第一候補はapplicationがCertified Factのexact contentをmaterializeする方式である。

ModelがCertified Factを自由paraphraseして新しいsource fact textを発行する権限はG-23Cでは与えない。

Exact presentation assemblyはG-23Dでfreezeする。

### 14.2 Interpretation premise

Stage 2 interpretationは:

```text
premise_fact_ids[]
```

としてこのcontractの`certified_fact_id`のみを参照する。

raw K IDをinterpretation premise authorityとして直接再導入しない。

### 14.3 Model-facing projection

Full Certified Content artifactにはaudit用support/evidence metadataを保持するが、Stage 2 model-facing requestへ全validation evidenceを渡す必要はない。

G-23Dは少なくとも次を分離する。

```text
application/audit artifact
vs
minimal Stage 2 model-facing factual projection
```

これによりvalidator verdictやsupport scoreをgeneration promptへ不要にprimingしない。

---

## 15. Non-certification semantics

Candidateがeligibilityを満たさない場合:

```text
Candidate artifact retained
Validation Record retained
Certified Fact not emitted
```

Non-certification reasonはapplication evidenceとしてmachine-addressableにする。

最低限のclass:

```text
NOT_CERTIFIED_REFERENCE_FAILURE
NOT_CERTIFIED_V2_FAILURE
NOT_CERTIFIED_SUPPORT_FAILURE
NOT_CERTIFIED_INDETERMINATE
NOT_CERTIFIED_VALIDATION_UNAVAILABLE
NOT_CERTIFIED_BINDING_MISMATCH
NOT_CERTIFIED_EXACT_DUPLICATE
```

これらはgenerator outputではない。

Certification failureを別LLMでrepairして同じcandidate identityへ上書きしない。

---

## 16. Evidence / reproducibility requirements

G-23D/G-23E/G-26でStage 1からStage 2までをreplayできるよう、最低限次を保存する。

```text
stage1 request identity / prompt identity
raw Stage 1 model output
parsed Stage 1 payload
application-owned candidate envelope
candidate digest
Validation Record
component evidence refs/digests
certification decision / non-certification reason
Certified Fact payload/digest
Certified Content payload/digest
contract/schema/prompt versions and hashes
context_fingerprint
request/purpose/attempt/retry lineage
```

Certified Contentだけを保存してValidation Recordを破棄してはならない。

逆に、Validation RecordだけからStage 2へmodel-authoredsource factを再生成させない。

---

## 17. What G-23C does not decide

本Taskでは次をfreezeしない。

- Stage 2 final output/block schema。
- Stage 2 interpretation / creative prompt details。
- presentation-role cardinality implementation。
- provider-specific Structured Output schema。
- exact retry message layout / retry count integration。
- exact canonical JSON hashing implementation。
- Residual Atomicity / Content-Type concrete classifier。
- Material Requirement distinctness/coverage policyの全面再設計。
- final terminal/render contract。

これらはG-23D/G-23E/G-23F/G-25Aの責務である。

---

## 18. Protected boundaries retained

G-23Cは次を変更しない。

- Frozen 47 Gold labels / required / critical flags。
- G-14 no-silent-post-hoc-atomization safety intent。
- G-23 two-stage architecture。
- E2 authority order。
- E3 Semi-structured Proposition contract。
- E4 application-owned role provenance / deterministic policy。
- E5 fail-closed residual classifier policy。
- G-23B minimal Stage 1 model payload / application envelope ownership。
- Retrieval / Similarity / Context Builder。
- canonical DB。
- Source / Evidence / Provenance。
- Object / Version identity。
- MCP read-only boundary。
- MiniCheck selection/threshold merely to improve acceptance。
- unsupported rendered material prohibition。
- fail-closed semantics。

---

## 19. Completion decision

G-23C completion conditions:

- [x] Candidate / Validation / Certification artifacts are separate.
- [x] Certification eligibility is fail-closed and requires V2 + source-support PASS.
- [x] `certified_fact_id` is application-owned and scoped to Certified Content runtime/evidence identity.
- [x] Certified claim/support are exact copies of the immutable Stage 1 candidate.
- [x] Candidate and Validation Record digests bind certification.
- [x] Certified Content cannot mix context fingerprints.
- [x] Stage 2 factual authority is Certified Content, not raw Grounded Context.
- [x] Interpretation premises reference Certified Fact IDs.
- [x] Certification creates no new model-owned semantic authority.
- [x] exact duplicate minimum policy avoids trivial material-count inflation.
- [x] cross-attempt salvage is explicitly deferred to G-23E.
- [x] classifier model selection remains G-25A.
- [x] protected historical/frozen evidence is unchanged.

Result:

```text
N-04G-23C = Complete / Contract Accepted
N-04G-23D = NEXT
N-04       = Failed / not Complete
N-05       = blocked
```
