# P-RAW-01 — Current Evidence Package / Result Impact Survey

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-RAW-01 [P0] Current Evidence Package / Result impact survey`
- Status: **Complete / Accepted**
- Released baseline: `v1.1.0`
- Current Package contract: `sgokb.object-evidence-package/1.0`
- Scope: survey only; no runtime/schema/storage implementation changes in this task
- Next: `P-RAW-02 — Evidence -> Raw Artifact provenance resolution contract`

## 1. Purpose

P-RAW changes the external-analysis boundary from reconstructed Evidence Markdown to Raw Artifacts traced through provenance.

This survey identifies where the current Evidence-oriented Package / Result pipeline is:

```text
BREAKING
MIGRATION-REQUIRED
COMPATIBLE
```

The survey covers:

- Package Builder;
- Package manifest/schema and integrity;
- analysis instructions;
- Object Result schema;
- Result validation;
- review / diff;
- receive / import / Version creation;
- Evidence Link / accepted Knowledge provenance;
- tests / benchmark fixtures;
- operator / acceptance documentation.

This task does **not** choose the final Package v2 schema, Raw resolver algorithm, physical DB migration, or v1/v2 support lifetime. Those decisions belong to P-RAW-02..05.

---

## 2. Current v1 exchange flow

The current external-analysis path is:

```text
Source / Snapshot / Raw Artifact
        ↓ normalization
Evidence
        ↓ retrieval / selection
ObjectEvidencePackageBuilder
        ↓
manifest.json
instructions.md
schema/object-result-v1.schema.json
current_object.json              (update Package only)
evidence/source_*.md             (semantic material for external AI)
        ↓ external AI
result.json
        ↓ receive
validate against Package membership
        ↓ review / diff
import
        ↓
accepted Knowledge Version
        ↓
evidence_links.evidence_id
```

The important current identity chain is therefore:

```text
selected Evidence ID
  -> Package evidence membership
  -> Evidence Markdown semantic material
  -> Result grounding Evidence ID
  -> validation against included_evidence_ids
  -> evidence_links.evidence_id
```

P-RAW intentionally changes the middle of this chain: the external AI should consume source Raw material rather than reconstructed Evidence Markdown.

---

## 3. Current contract findings

### 3.1 Package manifest v1 is Evidence-membership-centric

`src/sgokb/exchange/package_manifest.py` fixes the Package contract at:

```text
PACKAGE_SCHEMA_VERSION = sgokb.object-evidence-package/1.0
schema                  = object-evidence-package-v1.schema.json
```

Its semantic validation requires, among other things:

- `evidence.items` identity/order to match `included_evidence_ids` exactly;
- Evidence items to bind to Source / Snapshot / normalization run;
- Evidence membership to match `source_generations`;
- Evidence files to match `source_generations.file_path`;
- Evidence files to use Markdown media type;
- selection counts / token and byte budget to be expressed around selected Evidence.

This is more than a presentation detail. Evidence identity is part of Package integrity and semantic validity.

### 3.2 Package Builder exports reconstructed Evidence material

The current `ObjectEvidencePackageBuilder` uses selected/protected Evidence as the external semantic payload and emits Evidence-oriented package artifacts.

Evidence selection already carries useful Source / Snapshot / normalization-run lineage, but the Package does not yet make the underlying Raw Artifact membership the authoritative external grounding set.

For update Packages, protected historical Evidence can be carried forward even after a newer Source generation becomes effective. This protects accepted historical grounding and is an important semantic property that P-RAW must preserve in a Raw-aware form.

### 3.3 Instructions explicitly require Evidence-ID grounding

The current object-analysis instructions treat Package Evidence IDs as the only legal grounding references. The tests explicitly require wording equivalent to:

```text
Never cite an Evidence ID that is not in that list.
```

The instruction contract also preserves important semantics that are independent from grounding identity:

- Package binding;
- Object identity;
- Class / Facet / Attribute / Relation registry constraints;
- new vs full-snapshot update mode;
- no web browsing / no external model-memory evidence;
- derivation kinds;
- unresolved object-reference handling;
- no invented persistent IDs.

### 3.4 Object Result grounding is Evidence-ID based

The current Structured Object Result schema binds statement / attribute / relation grounding to Evidence IDs.

Core semantic Knowledge fields are separable from this grounding representation. In particular, the following concepts do not inherently require Evidence IDs:

- statement text and local identity;
- Facet assignment;
- structured Attribute value;
- Relation semantics;
- derivation kind;
- attribution;
- temporal semantics;
- target Object / Class binding.

### 3.5 Result validation uses Package Evidence membership as the authority

Current validation does not merely test that an Evidence ID exists in canonical storage. It requires a grounding Evidence ID to be a member of the exact Package identified by the Result binding.

Therefore an otherwise valid canonical Evidence ID is rejected when it was not in that Package's `included_evidence_ids`.

This Package-membership rule is correct and must survive P-RAW, but its authoritative grounding set must change from Evidence-only membership to the versioned Raw-grounding contract.

### 3.6 Review / diff is only partly grounding-dependent

The semantic review/diff machinery compares accepted/candidate Knowledge content and can continue to operate on statements, attributes, relations and Version state.

However, any review surface that displays or reasons about grounding references must become Raw-aware and must not present an Evidence ID as though it were the material actually read by the external AI.

### 3.7 Import keeps Knowledge content separate from grounding persistence

The current import path can create the accepted Knowledge Version independently from the Evidence link rows, but grounding persistence is ultimately written to Evidence-oriented links (`evidence_links.evidence_id`).

This is the principal canonical-persistence impact:

```text
Knowledge content model       -> mostly reusable
Grounding/provenance identity -> requires extension/redesign
```

P-RAW-01 does not decide whether the final implementation adds new Raw-grounding tables, extends existing link structures, or stores a composed trace. That physical design is deferred to P-RAW-04/05.

### 3.8 Package exchange audit is Evidence-oriented

Current exchange audit/storage records Package identity, transfer state and Evidence membership, but it does not provide a complete Raw membership / Raw hash / Evidence-to-Raw trace sufficient for the proposed v2 semantics.

The logical audit contract therefore requires extension even if some current transfer-state tables and receipt lifecycle can remain reusable.

### 3.9 Result receipt lifecycle is largely version-neutral

The receive/pending/validation workflow can remain structurally useful:

```text
detect / receive
  -> pending validation
  -> validate
  -> review
  -> import
```

But v1 and v2 artifacts must be dispatched by explicit schema/package version. A v1 Result must never be silently interpreted under v2 Raw-grounding rules.

---

## 4. Impact matrix

| Area | Current contract | Classification | Required change | Deferred task |
|---|---|---|---|---|
| Evidence retrieval / selection | Evidence is retrieval and operator-selection unit | **COMPATIBLE** | Retain Evidence as upstream selection intent | P-RAW-02 |
| Source / Snapshot / Raw capture | Raw Artifacts already canonical upstream material | **COMPATIBLE** | Reuse canonical Raw identity and integrity data | P-RAW-02 |
| Evidence -> provenance lineage | Evidence has Source / Snapshot / normalization-run lineage | **MIGRATION-REQUIRED** | Define deterministic Evidence -> Raw resolution | P-RAW-02 |
| Package Builder semantic payload | Exports reconstructed Evidence Markdown | **BREAKING** | Package authoritative semantic material becomes Raw-bearing | P-RAW-03/05 |
| Package layout | `evidence/source_*.md` is external semantic material | **BREAKING** | Introduce versioned Raw directory/artifact layout | P-RAW-03 |
| Package schema version | `sgokb.object-evidence-package/1.0` | **BREAKING / VERSIONED** | Define Package v2; do not mutate v1 semantics in place | P-RAW-03 |
| Manifest Evidence membership | `included_evidence_ids` is authoritative grounding membership | **BREAKING** | Add authoritative Raw membership and Evidence<->Raw trace | P-RAW-03 |
| Manifest Source-generation mapping | Evidence items map to Source/Snapshot/run/file | **MIGRATION-REQUIRED** | Preserve lineage while binding included Raw artifacts directly | P-RAW-02/03 |
| Package integrity | File hashes + manifest hash | **COMPATIBLE CONCEPT / MIGRATION-REQUIRED SHAPE** | Continue fail-closed hashing over new Raw files and entries | P-RAW-03 |
| Package budget | Evidence token/byte usage drives selection budget | **MIGRATION-REQUIRED** | Redefine/augment byte/media/token budget for Raw payload | P-RAW-03 |
| Preflight / egress | Package files undergo transfer/preflight checks | **COMPATIBLE CONCEPT / MIGRATION-REQUIRED COVERAGE** | Apply safety checks to Raw files/media/size/secrets | P-RAW-03/05 |
| Analysis instructions | Evidence list is sole allowed evidence source | **BREAKING** | Explain Raw-grounding target and permitted references | P-RAW-03/04 |
| Prompt-injection / no-web rules | Package data untrusted; external knowledge forbidden | **COMPATIBLE** | Preserve unchanged in spirit | P-RAW-03 |
| Result schema binding | Result binds exact Package/schema/instructions | **COMPATIBLE CONCEPT / VERSIONED** | Keep exact binding; add v2 schema dispatch | P-RAW-04 |
| Statement grounding | Evidence IDs | **BREAKING** | Define Raw-grounding reference representation | P-RAW-04 |
| Attribute grounding | Evidence IDs | **BREAKING** | Define Raw-grounding reference representation | P-RAW-04 |
| Relation grounding | Evidence IDs | **BREAKING** | Define Raw-grounding reference representation | P-RAW-04 |
| Result derivation kind | direct_statement/synthesis/interpretation/reported_view | **COMPATIBLE** | Preserve | P-RAW-04 |
| Attribution / temporal semantics | Canonical semantic fields | **COMPATIBLE** | Preserve | P-RAW-04 |
| Package-membership validation | Grounding must belong to exact Package Evidence set | **BREAKING IMPLEMENTATION / COMPATIBLE PRINCIPLE** | Validate against exact v2 Raw-grounding membership | P-RAW-04/05 |
| Result receipt lifecycle | receive -> pending -> validate | **COMPATIBLE** | Add explicit v1/v2 schema routing | P-RAW-05 |
| Review / semantic diff | Compares Knowledge content | **COMPATIBLE CORE** | Add Raw-grounding display / diagnostics | P-RAW-04/05 |
| Version creation/current Version | Accepted Knowledge Version mechanics | **COMPATIBLE** | Reuse if semantic payload stays canonical-compatible | P-RAW-05 |
| Evidence Link persistence | `evidence_links.evidence_id` records grounding | **MIGRATION-REQUIRED** | Preserve Evidence selection trace while persisting actual Raw grounding | P-RAW-04/05 |
| Accepted Knowledge provenance | Grounding interpreted through Evidence link | **MIGRATION-REQUIRED** | Extend provenance so Raw identity/hash/lineage remains recoverable | P-RAW-04/05 |
| Package exchange audit | Stores Evidence-oriented Package membership/state | **MIGRATION-REQUIRED** | Record/version Raw membership and traceability | P-RAW-03/05 |
| Search / Similarity / derived indexes | Built from accepted Knowledge | **COMPATIBLE** | Regression test only if imported Knowledge representation unchanged | P-RAW-05/06 |
| Object Registry / Association | Independent canonical identity/configuration | **COMPATIBLE** | No Raw-specific redesign expected | P-RAW-05/06 |
| CLI/Application workflow boundary | build/stage/preflight/export/receive/validate/review/import operations | **COMPATIBLE CONCEPT** | Preserve operations where practical; version artifact semantics internally | P-RAW-05 |
| GUI Package/Result | P-GUI-08 intentionally blocked | **MIGRATION-REQUIRED / DEFERRED** | Implement only after P-RAW contract accepted | P-GUI-08 |

---

## 5. Breaking changes that must be versioned

The following cannot safely be changed in place under the v1 meaning:

1. **Package semantic payload identity**
   - v1: Evidence Markdown is the material provided to the external AI.
   - v2: Raw Artifact material becomes authoritative external semantic input.

2. **Package membership contract**
   - `included_evidence_ids` alone cannot describe the actual external grounding set.

3. **Analysis grounding instruction**
   - Evidence-ID-only citation rules are no longer truthful when the AI reads Raw material.

4. **Structured Object Result grounding representation**
   - statement / attribute / relation grounding must represent what the AI actually read.

5. **Result Package-membership validation**
   - Evidence-only membership checks cannot certify Raw-grounded Results.

6. **Version interpretation of exchange artifacts**
   - a v1 Package/Result must remain v1;
   - a v2 parser must not silently reinterpret v1 grounding as Raw grounding.

Required compatibility rule:

```text
schema version determines semantics
not merely parser acceptance
```

---

## 6. Compatible contracts to preserve

P-RAW should deliberately preserve the following unless a later design task finds a concrete blocker:

- Evidence as retrieval / human-selection unit;
- Source / Snapshot / normalization / Raw Artifact canonical storage;
- Object identity and Class assignment;
- Association workflow;
- target Object and Package binding discipline;
- exact Package hash/binding verification principle;
- external AI no-web / no-unpackaged-knowledge rule;
- derivation-kind taxonomy;
- attribution and temporal semantics;
- allowed Facet / Attribute / Relation registry boundaries;
- full-snapshot update semantics and omission-as-deletion warning;
- Result receive / validate / review / import state machine;
- accepted Knowledge Version creation/current-version semantics;
- semantic Knowledge diff core;
- downstream retrieval/search/indexing from accepted Knowledge.

These are compatibility targets, not permission to bypass v2 grounding validation.

---

## 7. Migration-required contracts

### 7.1 Evidence selection -> Raw resolution

P-RAW-02 must define a deterministic traversal from selected/protected Evidence to the Raw Artifact(s) that are permitted to leave the local boundary.

At minimum the later contract must resolve:

- Source / Snapshot / normalization-run identity;
- normalization-run input Raw membership;
- multiple Evidence -> same Raw deduplication;
- one run -> multiple Raw inputs;
- auxiliary artifacts;
- logical path / media type / byte size / hash;
- missing or changed artifact behavior;
- traceability back to the Evidence selection decision.

### 7.2 Historical carry-forward

The current update Package protects historical grounding Evidence even if a newer Source generation becomes effective.

Raw-grounded v2 must not accidentally discard that property. The later design must distinguish:

```text
current effective Source material
vs
Raw material required to preserve accepted historical grounding
```

### 7.3 Persistence / provenance

The logical persistence contract must be able to answer at least:

```text
Which Package was analyzed?
Which Raw Artifact(s) were actually included?
What immutable identity/hash did each included Raw have?
Which selected/protected Evidence decision caused that Raw to be included?
Which statement/attribute/relation grounding refers to which Raw material?
Which Source/Snapshot/run lineage produced that material?
```

P-RAW-01 intentionally does not select the table layout.

### 7.4 Review and operator UX

Review must expose enough information to distinguish:

- semantic Knowledge change;
- Raw grounding change;
- stale/missing/modified Raw failure;
- v1 Evidence-grounded artifact vs v2 Raw-grounded artifact.

P-GUI-08 must consume this accepted contract rather than invent a GUI-only interpretation.

---

## 8. Tests / benchmark / fixture impact

### 8.1 Directly breaking/update-required tests

At minimum these families encode the v1 exchange contract and require v2 coverage or versioned parallel fixtures:

```text
tests/test_package_manifest.py
tests/test_package_transfer.py
tests/test_object_result_schema.py
tests/test_result_validation.py
tests/test_result_receipt.py
tests/test_object_analysis_instructions.py
tests/test_phase_g_roundtrip.py
tests/test_object_version_import.py
```

Specific v1 assumptions include:

- `evidence/source_*.md` package artifacts;
- exact `included_evidence_ids` membership;
- Evidence-ID-only grounding;
- protected historical Evidence carry-forward;
- current-object Evidence references;
- Evidence-link persistence after import.

### 8.2 Review/diff tests

`tests/test_diff_review.py` and Markdown review tests are mostly reusable for semantic Knowledge changes, but new assertions are required for Raw-grounding references and v1/v2 distinction.

### 8.3 Grounded-generation / benchmark fixtures

Phase N grounded-generation and adversarial fixtures that construct Package/Result payloads must be surveyed during P-RAW-05/06 for hard-coded v1 Evidence assumptions.

Their quality criteria should remain reusable where they evaluate semantic-role atomicity, derivation, or groundedness independent of storage identity. Input fixtures and validators may require v2 adaptation.

### 8.4 Regression-preservation tests

The following should remain regression gates rather than be redesigned merely because P-RAW exists:

- Object / Version semantics;
- Registry constraints;
- Source ingestion and Raw preservation;
- Search representation/indexing;
- retrieval / similarity;
- MCP read separation;
- CLI/Application transport-neutral behavior.

---

## 9. Operations / documentation impact

The following documentation families require revision when v2 is designed/implemented:

- `docs/operations/OBJECT_STANDARD_WORKFLOW.md`;
- `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md`;
- `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md`;
- package/result sections in requirements, decisions, design, reference, and release documentation;
- external-AI handoff instructions and acceptance examples.

Required operator changes include:

- Package contents must describe Raw files rather than implying Evidence Markdown is the analyzed source;
- preflight/egress must show Raw identities, media types, sizes and integrity;
- external AI instructions must identify the authoritative Raw grounding mechanism;
- receive/validate/review must display artifact schema version;
- failures for missing/modified/hash-mismatched Raw must be fail-closed and operator-visible;
- legacy v1 artifacts must be clearly labeled as Evidence-grounded.

---

## 10. Compatibility constraints for P-RAW-02..06

The survey establishes the following constraints for later design:

### C1 — Evidence remains selection intent

P-RAW does not remove Evidence from retrieval, operator review or selection.

### C2 — Raw becomes authoritative external semantic material

A v2 Result must not claim grounding in reconstructed Evidence text when the external AI actually read Raw artifacts.

### C3 — Exact Package membership remains mandatory

Grounding may only refer to material that the bound Package actually contained.

### C4 — Evidence <-> Raw trace must be preserved

The system must retain why a Raw artifact was included and which Evidence selection/protected-grounding decision led to it.

### C5 — Historical grounding protection remains fail-closed

Update Packages must not silently lose grounding required by accepted Knowledge merely because effective Source generations have advanced.

### C6 — v1 and v2 semantics must not be conflated

Compatibility may mean versioned support for both formats. It does not mean accepting a v1 Evidence-grounded Result as though it were v2 Raw-grounded.

### C7 — Canonical Knowledge meaning should remain stable where possible

P-RAW should avoid redesigning statements, attributes, relations, derivation, temporal semantics, Version lifecycle, retrieval or indexing unless Raw grounding creates a demonstrated requirement.

### C8 — Physical storage design is deferred

P-RAW-01 requires richer provenance persistence logically, but does not mandate a specific table/schema migration strategy.

---

## 11. P-RAW-01 non-goals

Not decided here:

- exact Evidence -> Raw traversal algorithm;
- which Raw artifact kinds are eligible;
- whether all normalization-run inputs or a subset are exported;
- auxiliary-artifact policy;
- Package v2 directory names / JSON field names;
- Object Result v2 grounding JSON shape;
- DB table migration or compatibility-view design;
- v1 deprecation lifetime;
- GUI implementation.

These remain explicit work for P-RAW-02..05.

---

## 12. Completion assessment

The required impact survey is complete.

```text
Package Builder                 = surveyed
manifest schema / integrity     = surveyed
instructions                    = surveyed
Object Result schema            = surveyed
Result Validation               = surveyed
Review / Diff                   = surveyed
Import / Version / EvidenceLink = surveyed
accepted Knowledge provenance   = surveyed
tests / benchmark               = surveyed
operations / docs               = surveyed
```

Disposition:

```text
BREAKING
  - v1 Evidence-Markdown external semantic payload
  - Evidence-only Package grounding membership
  - Evidence-ID-only analysis grounding instructions
  - Evidence-ID-only Result grounding representation
  - Evidence-only Result membership validation

MIGRATION-REQUIRED
  - Evidence -> Raw provenance resolution
  - Package audit/raw membership trace
  - preflight/budget/egress coverage
  - review grounding presentation
  - import grounding persistence / accepted provenance
  - v1/v2 receipt and validation routing
  - tests, fixtures, benchmarks and operations docs

COMPATIBLE TARGETS
  - Evidence retrieval/selection intent
  - Source/Snapshot/Raw canonical storage
  - Object/Registry/Association semantics
  - core Knowledge semantic fields
  - Version lifecycle
  - semantic diff core
  - downstream Search/Similarity/indexing
```

Therefore:

```text
P-RAW-01 = Complete / Accepted
Next     = P-RAW-02 — Evidence -> Raw Artifact provenance resolution contract
```

No source code was changed and no regression suite was rerun for this documentation-only survey.
