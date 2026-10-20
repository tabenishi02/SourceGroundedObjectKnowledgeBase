# N-04G-23A-E Atomicity / Role Gate Responsibility Decomposition

更新日: 2026-10-20

- Status: **Proposed / design work required before adoption**
- Parent: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Trigger:
  - `N-04G-23A` — Phi-4 Atomicity / Role Gold Benchmark: tested joint/split formulations insufficient
  - `N-04G-23A-R` — Judge Candidate Evaluation: **Complete / valid FAIL / no candidate selected**
- Historical authority:
  - `docs/decisions/N04G14_ATOMIC_CLAIM_AND_SEMANTIC_ROLE_BOUNDARY_REDESIGN.md`
  - `docs/evaluation/N04G23A_ATOMICITY_ROLE_GOLD_BENCHMARK.md`
  - `docs/evaluation/N04G23AR_JUDGE_CANDIDATE_EVALUATION.md`
  - `benchmark/n04g23a-atomicity-role-gold-v1.json`
- Adopted higher-level architecture retained:
  - `docs/decisions/N04G23_TWO_STAGE_GROUNDED_GENERATION_ARCHITECTURE.md`
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E is accepted**

---

## 1. Problem statement

G-23A / G-23A-R established that the current v3-style Atomicity / Role Gate cannot be repaired reliably by prompt clarification, split calls, or straightforward substitution of several local general-purpose judge models while preserving the frozen zero-tolerance Gates.

Observed candidate behavior is not a simple model-size ordering:

- Gemma 4 12B reached zero Atomicity critical false-pass, but failed Role safety/validity and repeatability.
- Mistral Small 3.2 24B reached zero required Atomicity false-reject, but produced many Atomicity false-pass and Role errors.
- Ministral 3 8B failed both Atomicity and Role safety/validity.
- Qwen3.5 9B was runtime-incompatible under the frozen bounded structured-output contract before Gold execution.

Therefore the next remediation must not be "try more judge models under the same responsibility boundary" by default.

The core design problem is that the current Gate asks a probabilistic general-purpose LLM to enforce three qualitatively different classes of rule at once:

1. **Structural / proposition-boundary rule**
   - whether one validation record contains more than one independently judgeable material proposition;
2. **Deterministic policy compatibility**
   - whether a known role is allowed for the current purpose / presentation position;
3. **Residual semantic classification**
   - whether the actual text content is source-world factual content, interpretation, creative content, context-limit/meta content, or mixed/ambiguous.

These responsibilities must be separated before G-23B design proceeds.

---

## 2. Root-cause conclusion

### RC-1 — SGOKB Atomicity is a grounding invariant, not ordinary sentence-level "one fact"

G-14 defines Atomicity using an independent-grounding-verdict split test. A natural sentence such as:

```text
Fate/stay night is a Japanese visual novel developed by Type-Moon.
```

can be `NON_ATOMIC` because medium/origin/developer assertions may receive different grounding verdicts.

A text-only judge must infer hypothetical future support boundaries without seeing actual support decomposition. This is intrinsically harder and more SGOKB-specific than generic atomic-fact classification.

### RC-2 — Role Gate contains rules that should not be probabilistic

Examples such as:

```text
creative_addition + purpose=roleplay
interpretation + presentation_role=main
source_fact + presentation_role=interpretation
```

can be rejected from already-available metadata and policy tables. Asking an LLM to rediscover these constraints creates avoidable false-pass / false-reject risk.

### RC-3 — Generator-declared semantic_role is currently both an input and a subject of judgment

The generator declares a role, then another model decides whether the declaration matches the text. This creates an unnecessary self-report / verifier loop and risks anchoring on the declared label.

### RC-4 — Zero-tolerance policy enforcement is poorly matched to a fully probabilistic Gate

The frozen acceptance policy correctly requires zero critical false-pass and zero required-valid false-reject. The solution should preserve this strictness, but deterministic constraints should be enforced by deterministic code/schema rather than hoping a general-purpose LLM achieves zero error.

### RC-5 — The residual semantic problem is real but smaller than the current Gate

Some cases still require natural-language semantic analysis, e.g. an `interpretation` unit that embeds factual premises inside the conclusion text, or source-world content disguised as creative content. These should remain fail-closed, but only this residual subset should require a learned/LLM classifier.

---

## 3. Design objective

Replace the current conceptual model:

```text
untrusted natural-language unit
  ↓
LLM Atomicity Judge
  ↓
LLM Role Judge
```

with a responsibility-decomposed v4 design:

```text
Stage 1 / Stage 2 structured generation
  ↓
Structured Proposition Record
  ↓
Deterministic structural validation
  ↓
Application-owned role provenance
  ↓
Deterministic role / purpose / presentation compatibility
  ↓
Residual semantic classifier only where text semantics remain unresolved
  ↓
fail-closed result
```

The goal is not to eliminate all semantic models. The goal is to remove deterministic and structural policy enforcement from the probabilistic judge workload.

---

## 4. Proposed responsibility split

### 4.1 Structural responsibility

**Owner:** schema + application validator + Stage 1 contract.

Target responsibilities:

- one proposition record represents one validation proposition;
- proposition IDs are explicit;
- support references / premise references bind to that proposition record;
- one record does not represent both source fact and interpretation conclusion;
- composite-risk indicators can trigger fail-closed/retry;
- no silent post-hoc splitting followed by rendering the original unsplit text.

This is an evolution of G-14's existing invariant, not a relaxation.

### 4.2 Role provenance responsibility

**Owner:** application orchestration / generation path.

Preferred direction:

- Stage 1 fact-candidate path -> role provenance `source_fact_candidate`;
- Stage 2 interpretation path -> role provenance `interpretation_candidate`;
- Stage 2 creative path -> role provenance `creative_candidate`;
- system-generated availability/meta path -> role provenance `context_limit`.

`semantic_role` should no longer be treated as an unconstrained generator self-declaration that becomes authoritative merely because the model emitted the label.

The exact persisted field names remain to be designed in G-23A-E.

### 4.3 Deterministic compatibility responsibility

**Owner:** application policy table.

The design must define a machine-readable compatibility matrix over at least:

```text
role provenance / normalized role
purpose
presentation role
stage
```

Examples expected to be deterministic:

```text
creative_addition + non-creative purpose -> reject
interpretation + main presentation -> reject
source_fact + interpretation presentation -> reject
context_limit + source-world-only slot -> reject
```

No LLM call is required for these policy mismatches.

### 4.4 Residual semantic responsibility

**Owner:** bounded classifier, only after deterministic checks.

Target classifications should be narrower than the current all-in-one Role Judge. Candidate output taxonomy:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

The classifier should preferably see the natural-language content without the generator's declared semantic role, then application code compares classifier output with role provenance / allowed policy.

`MIXED_CONTENT` and `AMBIGUOUS` remain fail-closed.

### 4.5 Residual atomicity responsibility

Even with structured proposition records, free text may still smuggle multiple propositions into one record. Therefore v4 still requires a residual protection layer.

However it should be a **risk detector / residual semantic check**, not the primary authority for all Atomicity.

Candidate deterministic risk features include:

- multiple sentence boundaries;
- causal / contrastive connectors;
- multiple independent finite-clause heads;
- explicit factual-premise + conclusion patterns;
- multiple source entities/predicates where independent verdicts are plausible.

These signals must not directly convert every match into `NON_ATOMIC`; they trigger stricter validation/retry. G-14's prohibition on punctuation/conjunction-only Atomicity decisions remains protected.

---

## 5. Structured Proposition Record direction

G-23A-E must design a v4 intermediate record. The following is a **design target, not yet a Frozen schema**:

```json
{
  "proposition_id": "P1",
  "stage": "stage1",
  "provenance_kind": "fact_candidate",
  "text": "Saber is a Servant.",
  "support_refs": ["K5"],
  "premise_fact_ids": [],
  "purpose": "roleplay"
}
```

Key principles:

1. one record corresponds to one proposition intended for one grounding policy;
2. role provenance comes from the generation path / container, not unrestricted model self-labeling;
3. support/premise binding is explicit;
4. the record carries enough identity to produce stage-local retry feedback;
5. final presentation text is not itself the grounding authority;
6. a later Stage 2 source-fact rendering should preferably reference certified proposition/fact IDs rather than regenerate source-world facts freely.

Do not prematurely force all propositions into a rigid subject/predicate/object ontology unless G-23A-E proves that the ontology covers the required SGOKB content without semantic loss.

---

## 6. Compatibility matrix direction

G-23A-E must produce a normative table before implementation. Initial design direction:

| Normalized role | Stage/path | Allowed purpose | Expected presentation | Deterministic action |
|---|---|---|---|---|
| source_fact | Stage 1 fact / certified fact | roleplay, comparison, creative as applicable | main/source-fact surface | allow to support validation |
| interpretation | Stage 2 interpretation | comparison and explicitly allowed cases | interpretation | require premise binding |
| creative_addition | Stage 2 creative | creative only | creative | reject outside creative purpose |
| context_limit | system/meta path | explicitly allowed | dedicated/meta surface | never substitute for source fact |

This table is illustrative until G-23A-E task completion.

---

## 7. Residual classifier strategy

G-23A-E must decide whether the residual semantic classifier should use:

- a small fine-tuned classifier (e.g. encoder / cross-encoder style),
- a bounded local LLM classifier with a much narrower task,
- or a cascade where deterministic checks handle most cases and a model handles only unresolved semantic cases.

Preferred evaluation principles:

1. Do not train/evaluate on only the 47 frozen cases and claim generalization.
2. Expand training/dev material with minimal pairs:
   - same text, role/path swapped;
   - same role/path, source-world vs invented content;
   - interpretation conclusion alone vs premise+conclusion mixed text;
   - atomic vs minimally compounded variants;
   - purpose/presentation swaps.
3. Hold out pattern families, not merely random rows, to avoid template leakage.
4. Keep the original 47 Gold cases as an external protected regression set where appropriate.
5. Preserve fail-closed treatment of ambiguous/mixed content.

---

## 8. Expected v4 validation flow

Candidate architecture after this redesign:

```text
Grounded Context
  ↓
Stage 1: Grounded Content Planner
  ↓
Structured Proposition Records
  ↓
Structural invariant / compound-risk checks
  ↓
Application-owned role provenance
  ↓
Deterministic compatibility matrix
  ↓
Residual semantic classification if required
  ↓
Deterministic support / MiniCheck / Source Fact validation
  ↓
Certified Content
  ↓
Stage 2: Presentation Generator
  ├─ certified_fact_id references
  ├─ interpretation(premise_fact_ids)
  └─ creative path only where allowed
  ↓
Deterministic presentation compatibility / schema checks
  ↓
Residual semantic check only if required
  ↓
Material / Terminal / Render
```

The exact composition remains subject to G-23A-E design tasks and later G-23F Freeze.

---

## 9. Mapping the existing 47 Gold cases

Before adoption, every case in `benchmark/n04g23a-atomicity-role-gold-v1.json` must be assigned to one or more expected enforcement classes:

```text
STRUCTURAL
DETERMINISTIC_POLICY
RESIDUAL_SEMANTIC
COMBINED
OPTIONAL_AMBIGUOUS
```

For each case, record:

- current Gold labels;
- why the current v3-style LLM Judge was needed;
- which v4 component should own the decision;
- whether the failure would become impossible by construction;
- whether a semantic classifier is still necessary;
- whether the case remains useful unchanged as a v4 regression case.

This mapping is required before claiming the redesign solves G-23A/G-23A-R failures.

---

## 10. Acceptance principles for this redesign

G-23A-E design may be accepted only if all are true:

1. No G-14 safety invariant is weakened.
2. Zero-tolerance critical false-pass policy is retained.
3. No historical G-22/G-23A/G-23A-R evidence is rewritten.
4. Deterministic rules are moved out of LLM judgment where their inputs are already known.
5. Generator role self-report cannot bypass application policy.
6. Non-atomic text is not silently repaired and then rendered unchanged.
7. Residual semantic uncertainty remains fail-closed.
8. The 47-case responsibility map demonstrates how each case is handled.
9. G-23B can consume the resulting proposition/role boundary without inventing a second conflicting model.
10. G-23F can Freeze hashes/schema/policy/runtime without ambiguous ownership.

---

## 11. Explicit non-goals

G-23A-E does not:

- implement production code;
- relax G-23A Gold labels/Gates;
- add more general-purpose judge candidates under the same old contract;
- change MiniCheck threshold to improve acceptance;
- redesign Retrieval/Similarity/Context Builder;
- modify canonical DB or Source/Evidence/Provenance;
- reopen historical G-21/G-22 evidence;
- decide the final classifier model before responsibility decomposition is complete.

---

## 12. Relationship to existing tasks

This escalation is inserted between G-23A-R and G-23B:

```text
G-23A-R valid FAIL / no candidate selected
  ↓
G-23A-E Atomicity / Role Gate Responsibility Decomposition
  ↓ ACCEPTED
G-23B Stage 1 Grounded Content Planner contract
```

G-23B remains blocked until G-23A-E produces an accepted proposition contract and responsibility boundary.

G-23C/D/E/F must consume this new responsibility model rather than reintroduce the old all-in-one judge implicitly.

---

## 13. Recommended decision direction

Subject to completion of the design tasks, the recommended v4 direction is:

```text
Atomicity
  primary authority -> structured proposition invariant
  residual protection -> compound-risk / bounded semantic check

Semantic Role
  provenance -> application/stage-owned
  compatibility -> deterministic policy matrix
  residual content type -> narrow classifier

Uncertainty
  -> fail closed
```

This is the preferred remediation because it preserves SGOKB's strict safety boundary while reducing the amount of zero-error policy enforcement delegated to probabilistic general-purpose LLM judges.
