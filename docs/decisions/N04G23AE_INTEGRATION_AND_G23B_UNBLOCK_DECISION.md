# N-04G-23A-E7 — Integration Decision / G-23B Unblock Review

更新日: 2026-10-21

- Status: **Complete / Architecture Accepted / G-23B Unblocked**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Trigger: `N-04G-23A-R` valid FAIL / no judge candidate selected
- Predecessors:
  - `N-04G-23A-E1 — 47-Gold Responsibility Mapping` Complete
  - `N-04G-23A-E2 — v4 V2 Responsibility Boundary Design` Complete
  - `N-04G-23A-E3 — Structured Proposition Contract Design` Complete
  - `N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design` Complete
  - `N-04G-23A-E5 — Residual Classifier Scope / Evaluation Design` Complete
  - `N-04G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis` Complete
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **NEXT**

---

## 1. Decision

`N-04G-23A-E`を **Complete / Architecture Accepted** とする。

`N-04G-23B — Stage 1 Grounded Content Planner Contract`を**unblockし、NEXT**とする。

E6で残ったResidual Atomicity依存は、現時点では**architecture blockerではなく、bounded implementation / benchmark risk**として扱う。

ただし、これはproduction classifierが既に選定済み・検証済みであることを意味しない。

v4をReference Workstation freeze / formal re-acceptanceへ進める前に、後続`N-04G-25A`でResidual classifierを実測選定し、zero-tolerance GateをPASSすることを必須とする。

```text
G-23A-E Architecture Accepted
  ↓
G-23B-F v4 contracts / Design Freeze
  ↓
G-24 implementation
  ↓
G-25A Residual Classifier Benchmark / Selection
  ↓ PASS only
G-25B Integrated v4 Adversarial Regression
  ↓ PASS only
G-26 Reference Workstation Freeze
```

`G-25A = VALID_FAIL_NO_SELECTION`の場合、G-26へ進めない。Gateを緩めずexplicit escalationへ戻す。

---

## 2. Why residual Atomicity is not an architecture blocker

E6では次が残っている。

```text
V2-R-A invoked                    42 / 47
critical invalid depending on A   25 / 33
```

従ってAtomicity risk自体は大きい。

しかしarchitecture blockerかどうかは「問題が未解決か」ではなく、**責務・interface・failure semanticsが設計として未確定か**で判断する。

E1〜E6で以下は既に固定済みである。

1. AtomicityとContent Typeは別authorityである。
2. model-authored free textをschema-validだけでAtomic PASSにしない。
3. V2-R-A taxonomyは`ATOMIC / NON_ATOMIC / AMBIGUOUS`。
4. `AMBIGUOUS / unavailable / malformed`はfail-closed。
5. critical false-pass = 0をselection Gateとする。
6. classifierはearlier structural/policy failureをoverrideできない。
7. classifier implementation family / checkpointはpluggable componentとして後段benchmarkで選定可能。
8. classifierが存在しない、または選定に失敗しても、architecture上はunsafe PASSではなくterminal failureになる。

つまり未確定なのは**contractではなくcomponent performance / concrete implementation**である。

そのためG-23B〜G-23Fのcontract設計を止める理由にはしない。

---

## 3. Why this is not a safety waiver

Architecture Acceptedは次を意味しない。

```text
Atomicity classifier accuracy is assumed.
25 critical cases are considered solved.
A best-available classifier may be used.
Formal acceptance may proceed without classifier proof.
```

正しくは:

```text
architecture owns the failure path
+
component selection remains mandatory
+
selection failure blocks downstream freeze
```

E6の33 critical caseについては、正しいcomponent verdictが得られれば全件pre-V3 fail-closed routeを持つ。

しかしE6はclassifier性能試験ではないため、G-25Aで実測証明するまでproduction readinessとはみなさない。

---

## 4. Integrated v4 V2 contract

E7時点でG-23B以降が参照する統合V2 contractを次で固定する。

```text
Candidate
  ↓
V2-S Structural Proposition Gate
  ↓
V2-P Application-owned Role Provenance
  ↓
V2-D Deterministic Compatibility Gate
  ↓ PASS only
V2-R-A Residual Atomicity if required
  ↓ ATOMIC only
V2-R-C Residual Content Type if required
  ↓ compatible only
V3/V4 Support / Derivation
```

### V2-S

- Semi-structured proposition contract。
- one authoritative `claim_text`。
- model-authored free textは原則`REVIEW_REQUIRED`。
- silent post-hoc atomization禁止。

### V2-P

Application-owned pathからnormalized roleを決める。

```text
stage1_fact_candidate             -> source_fact
certified_fact_materialization    -> source_fact
stage2_interpretation_candidate   -> interpretation
stage2_creative_candidate         -> creative_addition
system_context_limit              -> context_limit
```

Model-declared `semantic_role`はauthorityではない。

### V2-D

Known metadata violationはdeterministic hard fail。

対象:

- path / owner / stage mismatch
- purpose incompatibility
- presentation mismatch
- missing/forbidden support binding
- missing/forbidden premise binding
- model-authored context-limit
- context-limit coexistence
- model-authored stylistic-expression

### V2-R-A

```text
ATOMIC
NON_ATOMIC
AMBIGUOUS
```

Atomicity以外を判定しない。

### V2-R-C

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

Expected roleをclassifierへ見せず、content-only resultをE4 normalized roleとapplicationが比較する。

---

## 5. G-23B consumption contract

G-23BはE3/E4/E7をそのまま消費でき、duplicate role authorityを新設してはならない。

Stage 1 Plannerのcandidate pathは原則:

```text
stage1_fact_candidate
```

G-23Bが設計すべきもの:

- Stage 1 request schema
- Stage 1 output candidate schema
- application-owned envelope construction
- `claim_text`
- `support_refs[] >= 1`
- candidate identity / retry lineage
- conservative Stage 1 prompt policy
- provider schemaで保証可能なstructural constraints

G-23Bが**設計してはいけないauthority**:

```text
generator-owned authoritative semantic_role
model-owned validation status
model-owned certification status
model-owned Atomicity PASS
model-owned support/entailment PASS
presentation role on stage1_fact_candidate
free-form context_limit slot
```

G-23Bは「1 candidateに1 propositionを生成する」ことをprompt/schemaで促進するが、model-authored free textのsemantic Atomicityを自己証明しない。

その最終authorityはV2-R-Aである。

---

## 6. Residual classifier execution home

E5で設計したclassifier評価を、実行責務として`N-04G-25A`へ固定する。

### G-25A — Residual Classifier Benchmark / Selection

最低限:

1. Atomicity development corpusをE5 policyで構築する。
2. Content-Type development corpusをE5 policyで構築する。
3. pattern-family / lineage splitをfreezeする。
4. candidate familyを比較する。
5. threshold / abstention policyをdevelopment dataだけでfreezeする。
6. Frozen 47 Goldをfinal confirmationとして使用する。
7. Reference Workstationで再現性・latency・VRAMを測定する。
8. concrete V2-R-A / V2-R-C componentを選定する。

Mandatory selection Gate:

```text
Atomicity critical false-pass = 0
Content critical wrong-compatible false-pass = 0
required-valid false reject target = 0
repeatability = exact / 100% as applicable
AMBIGUOUS / UNAVAILABLE = fail-closed
```

All candidate failure:

```text
VALID_FAIL_NO_SELECTION
```

を正式結果とし、G-26をblockする。

### G-25B — Integrated v4 Adversarial Regression

G-25A選定componentを実装済みv4 pipelineへ接続し、少なくとも次を測る。

```text
critical Atomicity false-pass = 0
critical content-role false-pass = 0
unsupported rendered material claim = 0
accepted role escape = 0
invalid certified binding = 0
invalid interpretation premise acceptance = 0
creative scope violation acceptance = 0
```

PASSした場合のみG-26へ進める。

---

## 7. E7 acceptance checklist

- [x] 47/47 responsibility mapping complete
- [x] v4 V2 authority/order fixed
- [x] Structured Proposition contract selected
- [x] role provenance model selected
- [x] deterministic compatibility matrix fixed
- [x] residual classifier scope bounded
- [x] 47-Gold desk replay complete
- [x] every critical case has fail-closed authority path in desk replay
- [x] G-14 no-silent-post-hoc-atomization preserved
- [x] zero-tolerance critical false-pass policy preserved
- [x] historical evidence unchanged
- [x] residual Atomicity dependency classified as bounded implementation/benchmark risk
- [x] G-23B can consume E3/E4/E7 without duplicate role authority
- [x] classifier benchmark/selection has explicit execution home before Reference Workstation freeze
- [x] all-candidate classifier failure blocks G-26

Result:

```text
N-04G-23A-E  Complete / Architecture Accepted
N-04G-23B    NEXT
N-04         Failed / not Complete
N-05         blocked
```

---

## 8. Conditions that would reopen architecture

G-23A-Eを再度architecture escalationへ戻すのは、後続evidenceが次のいずれかを示した場合に限定する。

1. E5 narrow classifier task自体がzero-critical-FPを原理的/実測的に満たせない。
2. G-23B Stage 1 contractではnon-atomic generation surfaceを十分に抑制できず、classifier負荷が実用不能になる。
3. content-only classifierでは必要なrole boundaryを判定不能で、expected-role primingを戻さないと成立しない。
4. application-owned provenanceでは実際のStage 2 routeを一意に表現できない。
5. E6 mappingに未covered critical familyが発見される。
6. fail-closed運用によりMaterial yieldが実用上成立しないことが測定される。

上記がなければ、component failureはまずimplementation/benchmark remediationとして扱う。

---

## 9. Protected boundaries

E7は以下を変更しない。

- Frozen 47 Gold labels / required / critical flags
- G-23A/G-23A-R historical results
- G-14 safety intent
- G-23 two-stage architecture
- MiniCheck selection / threshold
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered material claim prohibition
- role escape prohibition
- fail-closed acceptance

---

## 10. Final decision

G-23A/G-23A-Rで失敗した「広範な汎用LLM JudgeへAtomicityとRoleを同時に委ねる」設計は採用しない。

E1〜E7で、責務を以下へ分解した。

```text
structure
+ application-owned provenance
+ deterministic policy
+ narrow Atomicity classification
+ narrow content-type classification
```

残るclassifier riskは大きいが、interface・taxonomy・failure semantics・selection Gateが固定されたため、architecture設計を進めるための未決事項ではない。

従ってG-23A-Eを**Architecture Accepted**として完了し、G-23Bを開始する。
