# N-04G-16 Semantic Validation Architecture Redesign

更新日: 2026-10-19

- Status: **Complete (design)**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger: N-04G-12 formal v2 re-acceptance `0 / 3 Case PASS`
- Root cause: `docs/evaluation/N04G13_FAILURE_ROOT_CAUSE_DESK_REVIEW_AND_EXTERNAL_RESEARCH.md`
- Atomicity / role boundary: `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
- Output / presentation hardening: `docs/decisions/N04G15_OUTPUT_SCHEMA_PRESENTATION_RENDERER_HARDENING.md`
- Existing validation design: `docs/decisions/N04G05_GROUNDING_VALIDATION_DESIGN.md`
- Previous design freeze: `docs/decisions/N04G07_END_TO_END_GROUNDED_GENERATION_DESIGN_FREEZE.md`
- Remediation task master: `docs/planning/N04_POST_G12_REMEDIATION_TASKS.md`

---

## 1. Decision

N-04 post-G12 remediationでは、旧G-05のHybrid validation方針を維持しつつ、V4の単一general-purpose semantic judgeを廃止し、**source fact verificationとinterpretation derivation verificationを別pipelineへ分離する**。

主要Decisionは次である。

1. G-14のAtomicity / Role Boundary Gateをsemantic verificationより前のhard Gateとして維持する。
2. V3 deterministic supportで安全に確定できる`source_fact`はmodel verifierを使わずsupport確定してよい。
3. V3 unresolved `source_fact`は、document-claim supportへ特化した**specialized source-fact verifier**へ渡す。
4. specialized verifierのprimary candidateは**MiniCheck family**とする。AlignScoreはsecondary benchmark candidateとする。
5. N-04 v3 formal baselineでは、semantic-only `source_fact`を1 verifierのpositive判定だけでPASSさせない。specialized verifierのpositive candidateに対して、独立したbounded LLM judgeのagreementを要求する方向を採用する。
6. verifier disagreement / ambiguous score / runtime unavailableをPASSへ倒さない。
7. general LLM judgeはspecialized verifierのnegative verdictを`entailed`で救済できない。
8. `interpretation`はK refを直接semantic judgeへ渡す方式を廃止し、**既にvalidated `source_fact` unitをpremiseとして参照する**。
9. v3 interpretation unitは`premise_unit_ids[]`を持つ。旧来のK `support_refs[]`をinterpretationのgrounding proofとして使用しない。
10. interpretation validatorはpremise supportを再判定せず、**「このatomic conclusionが、このvalidated premise集合だけからreasonableに導けるか」**のみを判定する。
11. interpretationにunsupported / non-source-fact / unresolved premiseが1件でもあればderivation judgeへ進めない。
12. hidden external premiseを必要とするconclusionは`derived_supported`へ昇格させない。
13. semantic verifierの各判定は、verifier identity / version / settings / raw verdict / score / threshold profileをaudit evidenceとして保存可能にする。
14. MiniCheck等のscoreは校正済み確率とみなさず、SGOKB replay/adversarial setでthresholdをfreezeする。
15. verifier model / thresholdの**最終production採用はoffline benchmark成功後のみ**とする。G-16ではarchitectureとcandidate policyをfreezeし、実model benchmarkはG-19/G-20の実装・adversarial工程で必須preconditionとして実施する。
16. N-04 v3 formal harnessでは採用済みverifier runtime/model/settings/thresholdをG-21でfreezeし、caseごとに変更しない。

Target flow:

```text
V0  Output contract / schema
  ↓
V1  Reference integrity
  ↓
V2  Atomicity / role / scope
  ↓
V3  Deterministic support
  ├─ source_fact deterministic_supported -> supported
  └─ unresolved
         ↓
V4F Source Fact Verification
  specialized fact verifier
         ↓ positive candidate only
  independent bounded LLM judge
         ↓
  composition / disagreement policy
         ↓
  supported | unsupported | contradictory | indeterminate

Interpretation path:
validated source_fact units
         ↓
premise_unit_ids deterministic integrity gate
         ↓
V4I bounded derivation judge
         ↓
derived_supported | unsupported | contradictory | indeterminate

V5 Grounding Aggregate
```

本Decisionはproduction codeを変更しない。実装はN-04G-19で行う。

---

## 2. Why G-05 must be reopened

G-05はsemantic validatorもfallible componentと定義していたが、current implementationではV3 unresolved unitについて実質的に:

```text
unit.text
+ cited K units
→ one general semantic validator
→ one verdict
```

で最終grounding dispositionが決まる。

G-12でこの構造のfalse-positiveが実証された。

### Case 1

- U2はK5でsupportされるclauseとunsupported Holy Grail War claimを同一unitに含んだ。
- Phi-4はunit全体を`entailed`と判定した。
- U3はmaterial relationship / duty / loyalty claimを`stylistic_expression`として出し、Phi-4が`role_valid`と判定した。

G-14によりU2/U3はsemantic verifierへ到達する前にfail-closedになる。

### Case 2

- interpretation U7のdestiny / personal-growth / linear-narrative premiseがK5/K10に存在しない。
- current machine validationでは`derived_supported`相当へ進み得た。
- G-05 intended designの「premise support → derivation support」が実装では一段判定へ圧縮されていた。

したがってG-16では、general semantic verdictの精度向上だけでなく**validator責務そのものを分離する**。

---

## 3. Validation stage redesign

G-16後の論理stageを次とする。

### V0 — Structural Contract

G-15のv2 output schema候補を検査する。

担当:

- contract version
- role-specific block/unit shape
- required fields
- field cardinality
- IDs
- provider/application schema一致

semantic support判定は行わない。

### V1 — Reference Integrity

担当:

- context fingerprint
- K namespace
- canonical mapping integrity
- source_fact `support_refs`の存在 / resolution
- interpretation `premise_unit_ids`のunit-local resolution

### V2 — Atomicity / Semantic Role / Scope

G-14を適用する。

担当:

- `ATOMIC / NON_ATOMIC / INDETERMINATE`
- content-first role boundary
- role escape
- mixed-role unit
- creative/context-limit scope

`NON_ATOMIC / ROLE_VIOLATION / INDETERMINATE`はV4へ進めない。

### V3 — Deterministic Source Support

安全に機械確定できるsource factだけを判定する。

結果:

```text
deterministic_supported
deterministic_contradictory
unresolved
```

`deterministic_supported`はsemantic verifier不要。

### V4F — Source Fact Verification

V3 unresolvedのatomic `source_fact`専用。

general derivation judgeとは分離する。

### V4I — Interpretation Derivation Verification

validated source fact premiseを参照するatomic interpretation専用。

source factのtruth/supportをこのstageで再評価しない。

### V5 — Grounding Aggregate

全material unitが:

```text
source_fact -> supported
interpretation -> derived_supported
creative_addition/context_limit -> role-valid / not_applicable
```

を満たす場合だけGrounding PASS候補にする。

use-case completion / material sufficiencyはG-17で別Gateとする。

---

## 4. Source fact verifier contract

### 4.1 Input

Source fact verifierへ渡す情報は最小化する。

```text
claim_text
cited_support_units[]
source_kind / structured metadata where needed
context_fingerprint
```

原則渡さない:

```text
Web
external retrieval
generator conversation
other uncited K units
franchise/world knowledge
user profile
```

目的は:

> claimが世界一般で真か

ではなく:

> supplied cited supportだけでclaimがsupportされるか

である。

### 4.2 Logical verdict

specialized verifier adapterは最低限次へ正規化する。

```text
SUPPORTED_CANDIDATE
UNSUPPORTED
INDETERMINATE
UNAVAILABLE
```

contradictionを直接分類できるverifierでは:

```text
CONTRADICTORY
```

も許容する。

score型verifierはraw scoreを保持するが、score自体をgrounding dispositionとして扱わない。

---

## 5. Specialized verifier candidate decision

### 5.1 Primary candidate — MiniCheck family

G-13調査に基づき、MiniCheckをprimary candidateとする。

理由:

- document → claim support問題へ直接特化している。
- general chat modelと異なるfailure modeを期待できる。
- local execution可能。
- atomic sentence / claimとの相性がよい。
- SGOKBの`K support units -> atomic source_fact`構造と直接対応する。

ただし、G-16時点では特定checkpointをproduction採用としてfreezeしない。

候補例:

```text
MiniCheck Flan-T5-Large family
Bespoke-MiniCheck family
```

最終checkpointは:

- local-only実行可能
- license確認
- pinned revision/cache
- Reference Workstationで再現可能
- replay/adversarial false-positive基準を満たす

ものから選ぶ。

### 5.2 Secondary candidate — AlignScore

AlignScoreはsecondary benchmark candidateとする。

primaryにしない理由:

- integration/dependency compatibility確認コストがMiniCheckより高い。
- SGOKB用途でthreshold calibrationが必要。

MiniCheck candidateがrequired benchmarkを満たさない場合の比較対象として保持する。

### 5.3 General LLM-only verifier

単独authorityとして不採用。

G-12でgeneral LLM judge単独のfalse acceptanceが観測されたため、modelを入れ替えるだけではarchitecture remediationにならない。

---

## 6. Source fact composition policy

N-04 v3 formal baselineでは、V3 unresolved atomic source factについて次のconservative compositionを採用する。

```text
Specialized verifier
  ↓
negative -> no PASS
positive candidate -> bounded independent LLM judge
  ↓
positive agreement -> supported
negative/disagreement/indeterminate -> no PASS
```

### 6.1 Positive agreement

最終`supported`条件:

```text
specialized verifier = SUPPORTED_CANDIDATE
AND
independent bounded LLM judge = ENTAILED
AND
no contradiction signal
```

### 6.2 Specialized negative cannot be rescued

```text
specialized = UNSUPPORTED
LLM = ENTAILED
```

でも`supported`へ昇格させない。

結果は原則:

```text
UNSUPPORTED
```

またはbenchmark policy上の`INDETERMINATE`とする。

G-18でfailure taxonomyとの最終mappingを統合する。

### 6.3 Disagreement

例:

```text
specialized = SUPPORTED_CANDIDATE
LLM = UNSUPPORTED
```

```text
specialized = SUPPORTED_CANDIDATE
LLM = INDETERMINATE
```

結果:

```text
INDETERMINATE
```

**disagreementをPASSへ倒さない。**

### 6.4 Runtime unavailable

formal runtimeでrequired verifierがunavailableの場合:

```text
SYSTEM / VALIDATOR UNAVAILABLE
-> no grounded PASS
```

別modelへsilent fallbackしない。

---

## 7. Bounded independent LLM judge

specialized verifierのpositive candidateを確認するsecond opinionとして使用する。

### Input

```text
atomic source_fact claim
exact cited support units only
minimal instruction:
  decide whether cited material entails the claim
```

禁止:

- Web
- uncited context
- model memoryを根拠とした補完
- generator conversation

### Output

最低限:

```text
ENTAILED
UNSUPPORTED
CONTRADICTORY
INDETERMINATE
```

`role_valid`や`reasonable_derivation`等、別責務のverdictをsource fact pathへ混ぜない。

### Independence

formal v3ではgeneratorと同一modelを唯一のjudgeにしない。

G-21でvalidator identity/runtimeをfreezeする。

---

## 8. Threshold policy

MiniCheck等のscoreを、そのまま「support確率」と解釈しない。

thresholdはSGOKB-specific benchmarkから決める。

必要な最低bucket:

```text
supported paraphrase
unsupported detail
compound/partial-support adversarial
contradiction
near-overlap but unsupported
```

threshold profileはverifier model/versionとセットでidentityを持つ。

例:

```text
verifier_profile_id
model_id
revision
supported_threshold
indeterminate_band
benchmark_hash
```

値はG-19/G-20のoffline benchmarkで決定する。

---

## 9. Offline verifier benchmark gate

G-13が要求したoffline benchmarkは**final verifier adoptionの必須Gate**とする。

G-16では実runtime modelをproduction採用として宣言しない。

実行時期:

```text
G-19 implementation candidate integration
  ↓
G-20 replay/adversarial benchmark
  ↓
verifier + threshold adoption
  ↓
G-21 formal harness freeze
```

最低dataset:

### Positive

- direct exact support
- safe normalized support
- faithful paraphrase
- one proposition supported by multiple K units

### Negative

- G-12 unsupported Holy Grail War detailをatomic化したclaim
- G-12 Case 2 unsupported fantasy / destiny / personal-growth premise
- synthetic unsupported relation
- synthetic unsupported event/backstory
- contradiction

### Adversarial

- high lexical overlap but material extra detail
- supported subject + unsupported predicate
- cited Kと同じentityだが別relation
- negation flip
- temporal / causal embellishment

Acceptance principle:

- false-positiveを最優先で抑える。
- required negative/replay caseを1件でもsupport扱いするprofileをformal baselineへ採用しない。
- false-negativeは記録するが、grounded PASS安全性を優先する。

---

## 10. G-12 Case 1 impact

G-12 Case 1 U2/U3はG-14によりV4Fへ到達しない。

### U2

```text
supported K5 content
+
unsupported Holy Grail War claim
```

→ `NON_ATOMIC`

→ no source fact verifier invocation

→ no grounded PASS

### U3

material duty/loyalty claim declared as `stylistic_expression`

→ v3 schema/role boundaryでinvalid

→ no source fact verifier invocation

→ no grounded PASS

したがってG-16 architectureは、G-12 Case 1 false acceptanceをsemantic verifier accuracyだけに依存して防ぐ設計ではない。

一方、U2のunsupported clauseをatomic source factとして再生成した場合はV4F対象となり、specialized verifier + independent agreement policyで検証する。

---

## 11. Interpretation contract redesign

### 11.1 K refs直接方式を廃止

旧:

```json
{
  "unit_id": "U7",
  "semantic_role": "interpretation",
  "text": "...",
  "support_refs": ["K5", "K10"]
}
```

では、K contentのどのpremiseを使ったかが不明で、hidden external premiseが混入し得る。

v3では次へ変更する。

```json
{
  "unit_id": "U7",
  "semantic_role": "interpretation",
  "text": "...atomic conclusion...",
  "premise_unit_ids": ["U2", "U5"]
}
```

`U2` / `U5`は既にvalidated `source_fact`である。

### 11.2 `support_refs` policy

v3 baselineではinterpretation unitにK `support_refs`を要求しない。

Normative grounding chain:

```text
interpretation U7
  ↓ premise_unit_ids
source_fact U2/U5
  ↓ support_refs
K units
```

これによりprovenance chainは維持される。

interpretation自身へK refsを二重に持たせない。

最終schemaはG-18でfreezeする。

---

## 12. Premise integrity gate

interpretationをderivation judgeへ渡す前にdeterministically次を確認する。

1. `premise_unit_ids`が1件以上ある。
2. 参照unitが同じoutput envelope内に存在する。
3. 参照unitは`source_fact`である。
4. 参照unitのgrounding dispositionは`supported`である。
5. premise unitが`unsupported / contradictory / indeterminate`でない。
6. self-referenceしない。
7. interpretation → interpretation chainをv3 baselineでは許可しない。
8. cyclic dependencyを許可しない。
9. premise ID重複を許可しない。

単純化のため、v3 baselineではpremiseは**source_factのみ**とする。

将来multi-hop interpretationを許可する場合は別contract revisionとする。

---

## 13. Interpretation derivation judge

### Input

```text
interpretation atomic conclusion
validated premise texts[]
minimal derivation rule
purpose
```

必要ならpremise provenance/object identity metadataを付与してよいが、uncited external knowledgeは渡さない。

### Output

```text
REASONABLE_DERIVATION
UNSUPPORTED_DERIVATION
CONTRADICTORY
INDETERMINATE
UNAVAILABLE
```

### Semantics

`REASONABLE_DERIVATION`:

- conclusionがpremise集合から合理的に導ける。
- external factual premiseを必要としない。
- stored canonical factであることを意味しない。

`UNSUPPORTED_DERIVATION`:

- premise集合だけではconclusionへ到達できない。
- hidden external premiseが必要。

---

## 14. Case 2 failure prevention

G-12 Case 2で問題となったdestiny / personal-growth / linear-narrative等のinterpretation premiseはK5/K10に存在しなかった。

v3では、generatorはまずsource factsとしてpremise unitを生成しなければならない。

unsupported premiseを作れば:

```text
source_fact premise
→ V3/V4F
→ unsupported / no PASS
```

そのunitを`premise_unit_ids`として使ってもPremise Integrity Gateで停止する。

premise unit自体を生成せずinterpretation textへhidden factを埋め込めば:

```text
G-14 conclusion-only / atomicity boundary
or
V4I derivation judge
```

でfail-closedにする。

したがって旧来の:

```text
K refs exist
+ general judge says reasonable_derivation
→ derived_supported
```

というsingle-hop positive pathを廃止する。

---

## 15. Interpretation judge composition

source fact verifierと異なり、MiniCheck等document-claim checkerをinterpretation conclusionへ直接適用しない。

理由:

- interpretationはentailmentだけでなくbounded reasoningを許す。
- canonical fact supportとderived conclusion validityは別意味である。

v3 baselineでは1つの**bounded derivation judge**を使用してよい。

ただし:

- premise integrityはdeterministicに先に保証する。
- judge inputをvalidated premiseへ限定する。
- `INDETERMINATE`をPASSへしない。
- judge identity/settingsをG-21でfreezeする。
- futureにdual-judgeを追加可能なadapter boundaryを設ける。

G-12 Case 2の主因はpremise validation欠落であり、source fact pathと同じspecialized fact-checkerを二重適用する必要はない。

---

## 16. Multi-object provenance

premise source object identityは各source factのK refsからdeterministically追跡可能である。

G-16ではvalidation resultへ最低限次を保持可能にする。

```text
premise_unit_ids
premise_object_ids
premise_support_refs
```

Comparison / Creative全体で両Object/Concept coverageが必要かという**use-case completion Gate**はG-17で扱う。

ただしderivation judgeへ渡すpremise provenanceはaudit可能でなければならない。

---

## 17. Verifier disagreement policy

### Source fact

```text
specialized positive + LLM entailed
  -> supported

specialized negative
  -> no PASS; LLM may not rescue

specialized positive + LLM negative/indeterminate
  -> INDETERMINATE

specialized unavailable
  -> INDETERMINATE / system failure path

LLM unavailable after required specialized positive
  -> INDETERMINATE / system failure path
```

### Interpretation

```text
premise integrity failure
  -> FAIL before judge

derivation judge = reasonable
  -> derived_supported

derivation judge = unsupported/contradictory
  -> FAIL

derivation judge = indeterminate/unavailable
  -> INDETERMINATE
```

共通:

> verifier disagreement / unavailability / ambiguityはgrounded PASSへ昇格させない。

---

## 18. Validation result audit contract

次期validation resultはunitごとに、役割に応じて最低限次を保存可能にする。

### Common

```text
unit_id
semantic_role
atomicity_verdict
role_boundary_verdict
final_grounding_disposition
validation_stage
```

### Source fact

```text
support_refs
deterministic_verdict
specialized_verifier_id
specialized_verifier_version
specialized_raw_score
threshold_profile_id
specialized_normalized_verdict
llm_judge_id
llm_judge_verdict
composition_verdict
```

### Interpretation

```text
premise_unit_ids
premise_object_ids
premise_support_refs
derivation_judge_id
derivation_verdict
```

verifier rationale全文をcanonical Knowledgeへ保存することは要求しない。

formal evidence treeには必要なraw request/responseをGit管理外で保存する。

---

## 19. Retry policy interaction

G-16ではmax retry回数自体は変更しない。

retryable candidate:

- unsupported claim generated by model
- invalid premise reference
- derivation unsupported due output choice

non-retry / system candidate:

- required verifier runtime unavailable
- verifier model/cache identity mismatch
- integrity failure

`INDETERMINATE`の細かなfailure-controller mappingはG-18統合時にG-06と再整合する。

---

## 20. Local-only / frozen model policy

既存N-04 local-only方針を維持する。

禁止:

- cloud verifier fallback
- Web fact checking
- online retrievalでsupport補完
- caseごとのverifier model cherry-pick

formal v3で使用するものはG-21前に:

```text
source fact verifier
checkpoint / revision
local cache identity
threshold profile
bounded LLM judge
derivation judge
runtime settings
```

をfreezeする。

---

## 21. G-14 / G-15 interaction

### G-14

G-16はatomicity/role boundaryをsemantic verifierに再委譲しない。

```text
NON_ATOMIC
ROLE_VIOLATION
INDETERMINATE atomicity
```

はV4へ進まない。

### G-15

v3 schemaへ次を反映する。

```text
source_fact unit:
  support_refs[]

interpretation unit:
  premise_unit_ids[]
  no direct K support_refs

creative_addition:
  no support/premise refs

context_limit:
  no support/premise refs
```

role-specific schema strategyと整合する。

final JSON Schema versionはG-18でfreezeする。

---

## 22. G-12 desk replay under G-16

### Case 1 U2

G-14:

```text
NON_ATOMIC
```

V4Fへ到達しない。

### Case 1 U3

G-14/G-15:

```text
stylistic_expression not allowed
+ material source-world content
-> role violation
```

V4Fへ到達しない。

### Case 2 Attempt 1 source fact

atomic unsupported claimであれば:

```text
V3 unresolved
→ specialized fact verifier
→ required replay benchmarkでunsupportedであることを確認
→ no PASS
```

### Case 2 U7 interpretation

旧:

```text
K5/K10
→ one reasonable_derivation verdict
→ derived_supported possible
```

新:

```text
explicit validated premise source_fact units
→ premise integrity
→ derivation judge only
```

unsupported premiseを明示unit化すればsource fact verificationで止まり、hidden premiseのままならderivation judgeでfail-closedにする。

---

## 23. Completion assessment

N-04G-16の設計完了条件を次の通り満たす。

- [x] source factとinterpretationのsemantic validation architectureを分離した。
- [x] single general-purpose LLM judgeを唯一のgrounding authorityにしない方針を確定した。
- [x] MiniCheck familyをprimary source-fact verifier benchmark candidateとした。
- [x] AlignScoreをsecondary benchmark candidateとした。
- [x] verifier disagreementをPASSへ倒さないcomposition policyを定義した。
- [x] interpretationをvalidated premise unit参照方式へ変更した。
- [x] interpretationでdirect K `support_refs`をgrounding proofとしない方針を確定した。
- [x] Case 2 unsupported premiseを`derived_supported`へ昇格しないGate順序を定義した。
- [x] G-12 Case 1 U2/U3がsemantic verifier accuracyに依存せずfail-closedになることを再確認した。
- [x] local-only / frozen verifier policyを維持した。
- [x] offline verifier benchmarkをfinal model/threshold adoptionの必須Gateとして定義した。
- [x] production codeは変更していない。

### Important empirical gate still pending

G-16はarchitecture design Taskであるため、MiniCheck/AlignScore checkpointの実測benchmark自体はまだ実行していない。

**特定checkpoint / thresholdをproduction採用したとは扱わない。**

G-19/G-20でReference Workstation上のG-12 replay/adversarial benchmarkを実施し、required negative caseをfalse-positiveするcandidate/profileは採用しない。

このempirical gateを満たす前にG-21 formal harness freezeへ進んではならない。

---

## 24. Next task

```text
N-04G-17 [P0]
Material sufficiency / terminal / render gate redesign
```

G-17では:

- Grounding PASSとuse-case completionを分離する。
- MaterialRequirementGateを設計する。
- comparison / creativeのmulti-object coverageを機械Gate化する。
- terminal ACCEPTED条件を強化する。
- rendererをterminal outcomeへbindする。

を扱う。
