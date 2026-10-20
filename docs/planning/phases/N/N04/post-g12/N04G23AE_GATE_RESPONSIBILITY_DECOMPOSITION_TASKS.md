# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition Tasks

更新日: 2026-10-20

- Parent: `N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition`
- Decision proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Trigger: `N-04G-23A-R` Complete / valid FAIL / no candidate selected
- Priority: **P0**
- Status: **In Progress**
- Completed: **G-23A-E1, G-23A-E2**
- Current task: **G-23A-E3 — Structured Proposition Contract Design**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E acceptance**

## 1. Goal

G-23A / G-23A-Rで明らかになったAtomicity / Role Judgeの不安定性に対し、Judge model追加ではなく責務境界そのものを再設計する。

設計作業の完了条件:

1. 47 Gold各caseの責務owner
2. Atomicityのstructural authorityとresidual checkの境界
3. Structured Proposition intermediate contract
4. application-owned role provenance
5. deterministic role/purpose/presentation compatibility matrix
6. residual semantic classifierの必要範囲
7. 47 Gold desk replay
8. G-23Bが参照できる統合Decision

本Taskではproduction実装を行わない。

## 2. Task chain

```text
G-23A-E1 47-Gold Responsibility Mapping                 Complete
  ↓
G-23A-E2 v4 V2 Responsibility Boundary Design           Complete
  ↓
G-23A-E3 Structured Proposition Contract Design          NEXT
  ↓
G-23A-E4 Role Provenance / Compatibility Matrix Design
  ↓
G-23A-E5 Residual Classifier Scope / Evaluation Design
  ↓
G-23A-E6 47-Gold Desk Replay / Coverage Analysis
  ↓
G-23A-E7 Integration Decision / G-23B Unblock Review
```

E1〜E6の結果を見て設計を後付けで緩めない。必要な設計変更が生じた場合は変更理由と影響する前工程を明記して再レビューする。

## 3. G-23A-E1 — 47-Gold Responsibility Mapping

Status: **Complete**

Deliverable:

`docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`

Result:

```text
Total                  47
Required               41
Optional                6
Critical               33
Critical without owner  0
Gold label changes      0
```

Primary owner distribution:

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
```

Decision carried forward:

```text
STRUCTURAL
  -> Structured Proposition contract primary
  -> compound-risk guard secondary

DETERMINISTIC_POLICY
  -> application policy matrix primary
  -> no LLM required for reject

RESIDUAL_SEMANTIC
  -> narrow content-type classifier after deterministic checks

COMBINED
  -> structural and semantic/policy verdicts independent

OPTIONAL_AMBIGUOUS
  -> preserve ambiguity; audit/coverage only
```

## 4. G-23A-E2 — v4 V2 Responsibility Boundary Design

Status: **Complete**

Deliverable:

`docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

Normative decomposition:

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

Normative order:

```text
Structured Proposition Candidate
  ↓
V2-S Structural Proposition Gate
  ↓
V2-P Role Provenance Normalization
  ↓
V2-D Deterministic Compatibility Gate
  ↓
V2-R Residual Semantic Gate if required
  ↓
V3+ Support / Derivation
```

Key decisions:

- V2-S/V2-D hard failureはV2-RやV3+でoverride不可。
- Generator-declared `semantic_role`はauthorityではない。
- role provenanceはapplication/stage pathがauthority。
- known purpose/presentation/premise/support mismatchはdeterministic hard reject。
- compound-risk signal自体は`NON_ATOMIC` verdictではない。
- model-authored content typeがstructured metadataだけで証明できない場合はV2-R必須。
- `MIXED_CONTENT`はFAIL、`AMBIGUOUS/INDETERMINATE`はfail-closed。
- V2はtruth/support/entailmentを判定しない。
- retry feedbackはfailed text、authority、expected/observed class、risk signalを含むstage-local envelopeにする。
- Stage 2 failureでCertified Contentを無条件再生成しない。

E2 Gate: **PASS**

- semantic classifier前checks fixed
- hard deterministic reject boundary fixed
- compound-risk separated from verdict
- role provenance authority fixed
- residual invocation boundary fixed
- mixed/ambiguous fail-closed fixed
- downstream override prohibited
- stage-local failure evidence fixed at semantic level

## 5. G-23A-E3 — Structured Proposition Contract Design

Status: **NEXT**

Purpose: Atomicityを自然言語生成後の全件LLM判定からgeneration intermediate contractで一部保証する方式へ移す。

Required topics:

- proposition_id lifetime / uniqueness
- stage/path provenance
- proposition text
- support_refs
- premise_fact_ids
- purpose binding
- object/context fingerprint binding
- certification status ownership
- retry identity
- rejected / ambiguous representation
- rendering separation
- schema versioning
- E2 `V2-S PASS / REVIEW_REQUIRED / FAIL`をどの構造条件で決めるか
- E2 `V2-R = NOT_REQUIRED`を許可できるconstruction path

Compare:

```text
A Minimal: id + provenance + text + refs
B Semi-structured: id + subject/entity refs + predicate hints + text + refs
C Fully normalized: subject + predicate + object/value + qualifiers
```

Option C requires evidence that arbitrary SGOKB content can be represented without semantic loss.

Deliverable: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

## 6. G-23A-E4 — Role Provenance / Compatibility Matrix Design

Generator-declared `semantic_role`をpolicy authorityとして扱わず、stage/path provenanceとdeterministic policy matrixからnormalized roleを導く。

Minimum paths:

```text
stage1_fact_candidate
stage2_interpretation_candidate
stage2_creative_candidate
system_context_limit
```

Compatibility dimensions:

```text
normalized role
stage/path
purpose
presentation_role
premise requirement
support requirement
```

Known structured policy violations must be deterministic.

Deliverables:

- `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
- optional machine-readable `benchmark/n04g23ae-role-compatibility-v1.json`

## 7. G-23A-E5 — Residual Classifier Scope / Evaluation Design

Only natural-language semantic boundaries remaining after structural/deterministic handling are classifier scope candidates.

Candidate taxonomy:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

Compare at minimum:

1. bounded local LLM classifier
2. encoder / sequence classifier
3. cross-encoder style classifier
4. deterministic-first cascade + classifier only for unresolved cases

Dataset must extend beyond 47 Gold. Pattern-family holdout is required candidate policy.

Deliverable: `docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md`

## 8. G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis

Apply the new responsibility model to the same 47 Gold before implementation.

Per case record:

```text
input metadata available?
structural violation detectable?
deterministic role violation detectable?
residual semantic classifier required?
expected fail/pass path
historical model error prevented by construction?
remaining uncertainty
```

Deliverable: `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`

Gate: demonstrate material reduction in critical decisions delegated to a broad probabilistic judge.

## 9. G-23A-E7 — Integration Decision / G-23B Unblock Review

Acceptance checklist:

- [x] 47/47 responsibility mapping complete
- [x] v4 V2 authority/order fixed
- [ ] Structured Proposition contract selected
- [ ] role provenance model selected
- [ ] deterministic compatibility matrix fixed
- [ ] residual classifier scope bounded
- [ ] 47-Gold desk replay complete
- [x] G-14 invariants preserved at E2 boundary
- [x] zero-tolerance critical false-pass policy preserved at E2 boundary
- [x] historical evidence unchanged
- [x] no silent post-hoc atomization preserved
- [ ] G-23B can consume the new contract without duplicate role authority

If accepted:

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

Otherwise G-23B remains blocked.

## 10. Protected boundaries

G-23A-Eでは以下を変更しない。

- G-23A frozen 47 Gold labels/flags
- G-23A-R historical candidate results
- G-14 safety intent
- G-23 two-stage generation decision
- MiniCheck threshold without separate evidence
- Retrieval / Similarity / Context Builder
- canonical DB
- Source / Evidence / Provenance
- Object / Version identity
- MCP read-only boundary
- unsupported rendered claim prohibition
- fail-closed semantics

## 11. Immediate next task

**N-04G-23A-E3 — Structured Proposition Contract Design**

E2でauthority/order、hard fail、Residual dispatch、override禁止が固定されたため、次はV2-Sの入力契約とconstruction proofを具体化する。