# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition Tasks

更新日: 2026-10-20

- Parent: `N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition`
- Decision proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Trigger: `N-04G-23A-R` Complete / valid FAIL / no candidate selected
- Priority: **P0**
- Status: **In Progress**
- Completed: **G-23A-E1, G-23A-E2, G-23A-E3**
- Current task: **G-23A-E4 — Role Provenance / Compatibility Matrix Design**
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
G-23A-E3 Structured Proposition Contract Design          Complete
  ↓
G-23A-E4 Role Provenance / Compatibility Matrix Design  NEXT
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

Deliverable: `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`

Result:

```text
STRUCTURAL              20
DETERMINISTIC_POLICY     5
RESIDUAL_SEMANTIC       11
COMBINED                 5
OPTIONAL_AMBIGUOUS       6
TOTAL                    47
Required                 41
Optional                  6
Critical                 33
Critical without owner    0
Gold label changes        0
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

Deliverable: `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`

Normative decomposition:

```text
V2-S  Structural Proposition Gate
V2-P  Role Provenance Normalization
V2-D  Deterministic Compatibility Gate
V2-R  Residual Semantic Gate
```

Key rules:

- V2-S/V2-D hard failureはV2-RやV3+でoverride不可。
- Generator-declared `semantic_role`はauthorityではない。
- role provenanceはapplication/stage pathがauthority。
- known purpose/presentation/premise/support mismatchはdeterministic hard reject。
- compound-risk signal自体は`NON_ATOMIC` verdictではない。
- model-authored content typeがstructured metadataだけで証明できない場合はV2-R必須。
- `MIXED_CONTENT`はFAIL、`AMBIGUOUS/INDETERMINATE`はfail-closed。
- retryはfailed proposition単位のstage-local evidenceを使う。

## 5. G-23A-E3 — Structured Proposition Contract Design

Status: **Complete / Option B selected**

Deliverable: `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`

Compared:

```text
A Minimal
  id + provenance + text + refs

B Semi-structured
  application-owned envelope
  + one proposition text
  + path-specific bindings
  + optional semantic anchors

C Fully normalized
  subject + predicate + object/value + qualifiers
```

Decision: **Option B — Semi-structured proposition record**.

Reason:

- Option Aはv3 unit構造との差が小さく、structural remediation効果が不足。
- Option Cはarbitrary SGOKB semantics、Interpretation、Creativeを表すためのontology肥大化とsemantic loss riskが大きい。
- Option Bは自然言語表現力を保ちながら、application-owned provenanceとpath-specific bindingをstructural authorityへ移せる。

Normative contract direction:

```text
Application-owned envelope
  ├─ contract version
  ├─ context fingerprint
  ├─ purpose
  ├─ stage/path provenance
  ├─ attempt/retry lineage
  └─ proposition identity
        ↓
Path-specific proposition payload
  ├─ one authoritative claim_text
  ├─ optional non-authoritative anchors
  └─ support_refs OR premise_fact_ids according to path
```

Ownership decisions:

- `semantic_role`をmodel authority fieldとして使用しない。
- proposition identity / stage / path / purpose / context / retry lineageはapplication-owned。
- validation/certification dispositionはCandidateとは別artifactでvalidator-owned。
- source fact `support_refs[]` と interpretation `premise_fact_ids[]` はmutually exclusive。
- certified source factは後続G-23Cで`certified_fact_id`を得てStage 2から参照される。
- model-authored free-text candidateはschema aloneでAtomicity PASSと偽装せず、原則`REVIEW_REQUIRED`から開始する。
- application/system-owned deterministic materializationだけが`PASS_BY_CONSTRUCTION`候補。
- no silent post-hoc atomizationを維持。

V2-S construction semantics:

```text
PASS_BY_CONSTRUCTION
REVIEW_REQUIRED
FAIL
```

For `REVIEW_REQUIRED`:

```text
ATOMIC        -> V2-S PASS
NON_ATOMIC    -> V2-S FAIL
INDETERMINATE -> V2-S INDETERMINATE
```

Residual atomicity mechanismはE5で設計する。

E3 Gate: **PASS**

- Minimal / Semi-structured / Fully normalized比較完了
- Semi-structured選定
- Stage 1 candidate / Certification / Stage 2 certified-ID参照へ接続可能
- role自己申告authorityを除去
- support/premise binding分離
- arbitrary semanticsをrigid ontologyへ固定しない
- free-text Atomicity limitationをfail-closedで保持

## 6. G-23A-E4 — Role Provenance / Compatibility Matrix Design

Status: **NEXT**

Purpose:

Generator-declared `semantic_role`をpolicy authorityとして扱わず、E3のapplication-owned `path_provenance`からnormalized roleを導き、structured metadataだけで判定できるpolicy violationを固定matrixでrejectする。

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
model/system ownership
```

Required decisions:

- exact path -> normalized role mapping
- allowed purpose per path/role
- allowed presentation role per path/role
- support_refs requirement/forbidden state
- premise_fact_ids requirement/forbidden state
- system-only path restrictions
- deterministic failure codes
- which application-owned construction paths may make V2-R `NOT_REQUIRED`

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

Deliverable: `docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md`

Gate: demonstrate material reduction in critical decisions delegated to a broad probabilistic judge.

## 9. G-23A-E7 — Integration Decision / G-23B Unblock Review

Acceptance checklist:

- [x] 47/47 responsibility mapping complete
- [x] v4 V2 authority/order fixed
- [x] Structured Proposition contract selected
- [ ] role provenance model selected
- [ ] deterministic compatibility matrix fixed
- [ ] residual classifier scope bounded
- [ ] 47-Gold desk replay complete
- [x] G-14 invariants preserved
- [x] zero-tolerance critical false-pass policy preserved
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

**N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design**

E3でcandidate structureとfield ownershipが固定されたため、次はapplication-owned `path_provenance`をnormalized roleへ写像し、purpose / presentation / binding requirementをdeterministic matrixとして確定する。