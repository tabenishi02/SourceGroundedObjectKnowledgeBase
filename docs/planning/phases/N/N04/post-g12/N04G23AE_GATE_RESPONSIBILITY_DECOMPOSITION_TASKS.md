# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition Tasks

更新日: 2026-10-20

- Parent: `N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition`
- Decision proposal: `docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md`
- Trigger: `N-04G-23A-R` Complete / valid FAIL / no candidate selected
- Priority: **P0**
- Status: **Planned / NEXT**
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E acceptance**

---

## 1. Goal

G-23A / G-23A-Rで明らかになったAtomicity / Role Judgeの不安定性に対し、Judge model追加ではなく**責務境界そのものを再設計**する。

設計作業の完了条件は、次をv4向けに明文化すること。

1. 47 Gold各caseの責務owner
2. Atomicityのstructural authorityとresidual checkの境界
3. Structured Proposition intermediate contract
4. application-owned role provenance
5. deterministic role/purpose/presentation compatibility matrix
6. residual semantic classifierの必要範囲
7. 47 Goldを使ったdesk replayによる設計妥当性確認
8. G-23Bが参照できる統合Decision

本Taskではproduction実装を行わない。

---

## 2. Task chain

```text
G-23A-E1 47-Gold Responsibility Mapping
  ↓
G-23A-E2 v4 V2 Responsibility Boundary Design
  ↓
G-23A-E3 Structured Proposition Contract Design
  ↓
G-23A-E4 Role Provenance / Compatibility Matrix Design
  ↓
G-23A-E5 Residual Classifier Scope / Evaluation Design
  ↓
G-23A-E6 47-Gold Desk Replay / Coverage Analysis
  ↓
G-23A-E7 Integration Decision / G-23B Unblock Review
```

E1〜E6の結果を見て設計を後付けで緩めない。必要な設計変更が生じた場合は、変更理由と影響する前工程を明記して再レビューする。

---

## 3. G-23A-E1 — 47-Gold Responsibility Mapping

### Purpose

`benchmark/n04g23a-atomicity-role-gold-v1.json` の全47 caseを、新v4 Gateのどのcomponentが扱うべきか分類する。

### Required classification

各caseへ最低限以下を付与する。

```text
STRUCTURAL
DETERMINISTIC_POLICY
RESIDUAL_SEMANTIC
COMBINED
OPTIONAL_AMBIGUOUS
```

複数責務に跨る場合はprimary owner / secondary guardを分ける。

### Required fields per case

- case_id
- required / optional
- critical_for_safety
- current atomicity Gold
- current role Gold
- v3 failure mode / observed judge issue
- proposed primary owner
- optional secondary guard
- deterministic inputs available or not
- semantic understanding required or not
- expected v4 action
- still-needed regression assertion

### Deliverable

```text
docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md
```

Optionally add a machine-readable projection if useful:

```text
benchmark/n04g23ae-47-gold-responsibility-map-v1.json
```

### Gate

- 47 / 47 cases mapped
- no critical case left with unspecified owner
- optional ambiguous cases remain explicitly ambiguous rather than force-labeled
- no Gold label change inside this task

---

## 4. G-23A-E2 — v4 V2 Responsibility Boundary Design

### Purpose

Current all-in-one LLM Judge responsibilityを、structural / deterministic / residual semanticへ分割し、validation順序とauthorityを固定する。

### Required design questions

1. Which checks run before any semantic classifier?
2. Which checks are hard deterministic rejects?
3. Which checks only raise compound-risk and require residual review?
4. What is the authoritative source of role provenance?
5. When is a residual classifier invoked?
6. How is `AMBIGUOUS` / `MIXED_CONTENT` treated?
7. Can downstream support validation override earlier failure? Expected answer: no.
8. How does retry receive stage-local evidence?

### Target flow to validate

```text
Structured Proposition
  ↓
Structural validation
  ↓
Role provenance normalization
  ↓
Deterministic compatibility
  ↓
Residual semantic classification if needed
  ↓
Support / derivation validation
```

### Deliverable

```text
docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md
```

### Gate

Every verdict source must have one unambiguous authority. A later probabilistic component must not silently override an earlier deterministic violation.

---

## 5. G-23A-E3 — Structured Proposition Contract Design

### Purpose

Atomicityを「自然言語生成後に全件LLM判定」する方式から、**generation intermediate contractで一部保証する方式**へ移すためのschemaを設計する。

### Required topics

- proposition_id lifetime / uniqueness
- stage/path provenance
- proposition text
- support_refs
- premise_fact_ids
- purpose binding
- object/context fingerprint binding
- certification status field ownership
- retry identity
- representation of rejected / ambiguous proposition
- renderingとの分離
- schema versioning

### Explicit design comparison

少なくとも次を比較する。

#### Option A — Minimal proposition record

```text
id + provenance + text + refs
```

#### Option B — Semi-structured proposition record

```text
id + subject/entity refs + relation/predicate hints + text + refs
```

#### Option C — Fully normalized predicate/value record

```text
subject + predicate + object/value + qualifiers
```

Option Cを採用する場合、任意のSGOKB contentをsemantic lossなく表現できる証拠が必要。単にmachine-checkしやすいという理由だけでrigid ontologyへ固定しない。

### Deliverable

```text
docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md
```

### Gate

- G-23B Content Plannerが出力可能
- G-23C Certificationが消費可能
- G-23D Presentationがcertified IDsを参照可能
- G-14 silent post-hoc atomization prohibitionと矛盾しない

---

## 6. G-23A-E4 — Role Provenance / Compatibility Matrix Design

### Purpose

Generator-declared `semantic_role`をpolicy authorityとして扱わず、stage/path provenanceとdeterministic policy matrixからnormalized roleを導けるようにする。

### Required outputs

#### 6.1 Provenance model

最低限次のpathを検討する。

```text
stage1_fact_candidate
stage2_interpretation_candidate
stage2_creative_candidate
system_context_limit
```

#### 6.2 Compatibility matrix

最低限次元:

```text
normalized role
stage/path
purpose
presentation_role
premise requirement
support requirement
```

#### 6.3 Deterministic violations

例:

- creative content outside creative purpose
- interpretation in main/source-fact presentation
- source fact in interpretation presentation
- interpretation without required premise binding
- context-limit meta claim in source-world fact slot

### Deliverable

```text
docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md
```

Machine-readable policy artifact candidate:

```text
benchmark/n04g23ae-role-compatibility-v1.json
```

### Gate

All policy checks whose required inputs are already structured must be deterministic; they must not be delegated to the residual semantic classifier merely for convenience.

---

## 7. G-23A-E5 — Residual Classifier Scope / Evaluation Design

### Purpose

Deterministic/structural handling後にも残る自然言語意味境界のみを分類対象として定義する。

### Candidate taxonomy

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

Taxonomy名称はこのTaskで確定する。

### Required comparison

少なくとも以下を比較する。

1. narrow bounded local LLM classifier
2. encoder / sequence classifier
3. cross-encoder style classifier
4. deterministic-first cascade + classifier only for unresolved cases

### Dataset design

47 Goldだけでtraining accuracyを評価しない。

追加候補:

- semantic-role swaps
- purpose swaps
- presentation swaps
- source-world / invented minimal pairs
- interpretation-only vs premise+interpretation mixed pairs
- atomic / minimally compounded pairs
- context-limit / source-world mixed pairs

### Split policy

Random row splitだけではなく、**pattern-family holdout**を必須候補とする。

### Evaluation metrics

- critical false-pass
- required false-reject
- ambiguous rate
- repeatability
- family-holdout generalization
- latency / VRAM

### Deliverable

```text
docs/planning/phases/N/N04/post-g12/N04G23AE_RESIDUAL_CLASSIFIER_EVALUATION_PLAN.md
```

This task designs the evaluation; actual model benchmark may become a follow-up execution task if local inference/training is required.

---

## 8. G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis

### Purpose

New responsibility modelを実装前に47 Goldへ適用し、どのhistorical failureがarchitecture上消えるか、どれがresidual classifierへ残るかを確認する。

### Required per-case analysis

For each case:

```text
input metadata available?
structural violation detectable?
deterministic role violation detectable?
residual semantic classifier required?
expected fail/pass path
historical model error prevented by construction?
remaining uncertainty
```

### Required aggregate summary

At minimum:

- cases handled fully structurally
- cases handled fully deterministic-policy
- cases requiring residual semantics
- combined cases
- optional ambiguous cases
- critical cases no longer dependent on probabilistic judge
- critical cases still dependent on residual semantic classifier

### Deliverable

```text
docs/evaluation/N04G23AE_V4_GATE_DESK_REPLAY.md
```

### Gate

The design must demonstrate a material reduction in critical decisions delegated to a probabilistic general-purpose judge. If most critical cases still require the same broad semantic decision as v3, redesign is incomplete.

---

## 9. G-23A-E7 — Integration Decision / G-23B Unblock Review

### Purpose

E1〜E6を統合し、G-23A-Eを正式にAcceptedとするか判定する。

### Acceptance checklist

- [ ] 47/47 responsibility mapping complete
- [ ] v4 V2 authority/order fixed
- [ ] Structured Proposition contract selected
- [ ] role provenance model selected
- [ ] deterministic compatibility matrix fixed
- [ ] residual classifier scope bounded
- [ ] 47-Gold desk replay complete
- [ ] G-14 invariants preserved
- [ ] zero-tolerance critical false-pass policy preserved
- [ ] historical evidence unchanged
- [ ] no silent post-hoc atomization
- [ ] G-23B can consume the new contract without duplicate role authority

### Completion state

If accepted:

```text
N-04G-23A-E = Complete / Architecture Accepted
N-04G-23B   = NEXT
N-04        = Failed / not Complete
N-05        = blocked
```

If rejected/incomplete:

```text
N-04G-23A-E = In Progress / redesign required
N-04G-23B   = blocked
N-04        = Failed / not Complete
N-05        = blocked
```

### Deliverable

Update:

```text
docs/decisions/N04G23AE_ATOMICITY_ROLE_GATE_RESPONSIBILITY_DECOMPOSITION.md
docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_REMEDIATION_TASKS.md
docs/planning/phases/N/N04/post-g12/N04_POST_G22_TWO_STAGE_CHAT_HANDOFF.md
```

---

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

---

## 11. Immediate next task

**N-04G-23A-E1 — 47-Gold Responsibility Mapping**

理由:

新しい責務境界を先に抽象設計すると、都合の良いcaseだけを想定する危険がある。まず既存47 Goldを全件分類し、どのcaseがstructural / deterministic / residual semanticへ属するかを明示してから、E2以降のv4 V2設計へ進む。
