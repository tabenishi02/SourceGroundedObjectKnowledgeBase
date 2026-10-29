# P-RAW-02 — Evidence -> Raw Artifact Provenance Resolution Contract

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-RAW-02 [P0] Evidence -> Raw Artifact provenance resolution contract`
- Status: **Complete / Accepted**
- Released baseline: `v1.1.0`
- Depends on: `P-RAW-01 — Current Evidence Package / Result impact survey`
- Scope: design / resolution contract only; no Package v2, Result v2, DB migration, or runtime implementation in this task
- Next: `P-RAW-03 — RAW-bearing Package v2 design`

## 1. Purpose

P-RAW-02 defines the deterministic rule that turns operator-selected Evidence into the Raw Artifact set that is eligible to become authoritative semantic material in a future Raw-bearing Object Evidence Package.

The contract must preserve the canonical provenance chain already present in SGOKB while avoiding false precision.

The required traversal is:

```text
selected Evidence
    ↓
Evidence.normalization_run_id
    ↓
Normalization Run
    ↓
normalization_run_artifacts
    ↓
Raw Artifact input set
    ↓
snapshot / source consistency verification
    ↓
physical bytes / size / hash verification
    ↓
resolved Raw grounding set
```

This task answers only **which canonical Raw Artifacts belong to the provenance of selected Evidence and when that resolution is valid**.

It deliberately does not yet define:

- Package v2 directory layout;
- Package v2 manifest JSON shape;
- external-AI-facing Raw locator syntax;
- Result v2 grounding JSON shape;
- physical DB migration / new provenance tables;
- media conversion / rendering rules;
- external egress secret scanning implementation.

Those belong to P-RAW-03..05.

---

## 2. Current canonical facts

The current Source repository already records the following identities:

```text
Source
  └─ Snapshot
      ├─ Raw Artifact(s)
      └─ Normalization Run
           ├─ normalization_run_artifacts -> input Raw Artifact(s)
           └─ Evidence item(s)
```

A Raw Artifact record carries canonical material metadata including:

```text
artifact_id
snapshot_id
artifact_kind
storage_path
sha256
byte_size
logical_path
media_type
charset
```

A Normalization Run is created with one or more input Raw Artifact IDs. The repository verifies at run creation that those Raw Artifacts belong to the same Snapshot and persists the run-to-artifact membership in `normalization_run_artifacts`.

An Evidence item is bound to one Normalization Run.

The important limitation is that the current schema does **not** record an exact per-Evidence subset, byte range, DOM node range, or Raw locator within the run's input artifacts.

Therefore the strongest currently supportable statement is:

> An Evidence item was produced by a Normalization Run whose complete canonical input set is the Raw Artifact set recorded in `normalization_run_artifacts`.

It is **not** currently supportable to assert that one particular Raw Artifact, byte span, or logical fragment alone produced that Evidence unless a future contract records that additional provenance explicitly.

---

## 3. Core decision — normalization-run input covering set

P-RAW-02 adopts the following baseline:

```text
Raw provenance resolution scope = normalization_run_inputs
```

For every selected Evidence item, the resolver MUST return **all canonical Raw Artifacts recorded as inputs to that Evidence item's own Normalization Run**.

This set is called the:

```text
Raw Input Covering Set
```

The covering set is provenance-complete for the information currently stored by SGOKB. It intentionally does not claim finer-grained provenance than the canonical database can prove.

### 3.1 Consequences

If one run has one Raw input:

```text
Evidence E1
  -> Run R1
  -> Raw A1

resolution(E1) = {A1}
```

If one run has multiple Raw inputs:

```text
Evidence E1
  -> Run R1
  -> Raw A1, A2, A3

resolution(E1) = {A1, A2, A3}
```

The resolver MUST NOT heuristically choose only A1 because its `artifact_kind`, `logical_path`, media type, filename, or content appears more likely to contain the Evidence text.

If multiple Evidence items share the same run:

```text
E1 -> R1 -> A1, A2
E2 -> R1 -> A1, A2
```

then both Evidence items resolve to the same covering set. Package-level Raw material may be deduplicated by canonical `artifact_id`, but both provenance edges remain explicit.

---

## 4. Resolution identity model

P-RAW-02 defines a logical resolution record. This is a design contract, not yet a committed Python class or persisted schema.

Conceptually:

```text
EvidenceRawResolution
  evidence_id
  source_id
  snapshot_id
  normalization_run_id
  resolution_scope = "normalization_run_inputs"
  raw_artifacts[]

ResolvedRawArtifact
  artifact_id
  snapshot_id
  artifact_kind
  storage_path
  logical_path
  media_type
  charset
  byte_size
  sha256
```

The minimum authoritative identities are:

```text
Evidence ID
Normalization Run ID
Snapshot ID
Source ID
Raw Artifact ID
Raw Artifact SHA-256
```

`logical_path`, `media_type`, `charset`, `artifact_kind`, `storage_path`, and `byte_size` are material metadata, but none of them replaces `artifact_id` as canonical Raw identity.

### 4.1 Hash does not replace identity

Two distinct Raw Artifact records may contain identical bytes and therefore share a SHA-256.

The resolver MUST NOT collapse canonical provenance solely by hash.

```text
artifact_id = provenance identity
sha256      = content-integrity identity
```

Byte-level deduplication may later be considered by Package v2, but only if every original `artifact_id` mapping remains recoverable. P-RAW-02 does not authorize such collapsing.

---

## 5. Deterministic resolution algorithm

For each selected Evidence ID, the future resolver MUST perform the following logical algorithm.

### Step 1 — Load the canonical Evidence item

Require the Evidence item to exist.

Obtain its canonical `normalization_run_id`.

Failure:

```text
Evidence missing -> BLOCKED / fail closed
run ID missing   -> BLOCKED / fail closed
```

The resolver MUST NOT reconstruct a run identity from Evidence text, Evidence metadata, Source association, or current effective state.

### Step 2 — Load the Evidence's own Normalization Run

Require the referenced Normalization Run to exist.

Capture the run's canonical `snapshot_id`.

Failure:

```text
Normalization Run missing -> BLOCKED / fail closed
snapshot binding missing   -> BLOCKED / fail closed
```

### Step 3 — Resolve run input membership

Read every `artifact_id` from `normalization_run_artifacts` for that run.

The set MUST be non-empty.

No input ordering has semantic precedence. For deterministic serialization / diagnostics, artifact IDs MUST be normalized to a stable lexical `artifact_id` order unless a later persisted ordinal contract is explicitly introduced.

Failure:

```text
zero Raw inputs -> BLOCKED / fail closed
```

### Step 4 — Load and verify every Raw Artifact record

For every run input artifact:

- the Raw Artifact record MUST exist;
- its `snapshot_id` MUST equal the Normalization Run's `snapshot_id`;
- its parent Snapshot MUST exist;
- the Snapshot's Source MUST exist.

All Raw inputs of one run therefore bind to one Source generation through the same Snapshot.

Failure examples:

```text
run membership points to missing Raw Artifact
Raw Artifact belongs to different Snapshot
Snapshot is missing
Source is missing
```

All are `BLOCKED / fail closed`.

The resolver MUST NOT silently discard the inconsistent Raw input and continue with the remaining artifacts.

### Step 5 — Verify physical material

A resolution is not export-safe merely because SQLite metadata exists.

Before a Raw Artifact can be declared materializable for a Raw-bearing Package, SGOKB MUST verify the bytes referenced by canonical storage metadata:

1. storage target exists and is readable;
2. measured byte size equals canonical `byte_size`;
3. calculated SHA-256 equals canonical `sha256`.

Any mismatch is fail-closed.

```text
missing bytes      -> BLOCKED
unreadable bytes   -> BLOCKED
byte-size mismatch -> BLOCKED
SHA-256 mismatch   -> BLOCKED
```

There is no fallback to reconstructed Evidence Markdown and no substitution from a newer Snapshot.

P-RAW-03/05 will determine the exact API and timing of this physical verification, but Package build/export MUST NOT cross the egress boundary without it.

### Step 6 — Return the complete Raw Input Covering Set

Only after the provenance graph is internally consistent may the resolver return success for that Evidence.

The returned set contains **every** run input Raw Artifact.

No artifact-kind ranking or content similarity step is part of provenance resolution.

---

## 6. Multiple Evidence and Package-level deduplication

Resolution is first performed per Evidence, not directly per Package.

For selected Evidence:

```text
selected = [E1, E2, E3]
```

resolve independently:

```text
E1 -> {A1, A2}
E2 -> {A2, A3}
E3 -> {A1}
```

Package-level Raw identity union is:

```text
included Raw = {A1, A2, A3}
```

but traceability MUST preserve:

```text
E1 -> A1, A2
E2 -> A2, A3
E3 -> A1
```

### 6.1 Dedup key

Canonical deduplication key:

```text
artifact_id
```

Not:

```text
sha256
storage_path
logical_path
filename
artifact_kind
```

This protects provenance identity even when two artifacts have identical bytes or similar paths.

### 6.2 Deterministic package union

P-RAW-03 will define manifest serialization, but the resolution contract requires the union to be deterministic. A conforming implementation can obtain this by stable lexical ordering of canonical `artifact_id` after identity deduplication.

Evidence-to-Raw mappings remain independently serialized / inspectable and MUST NOT be lost as a side effect of Raw deduplication.

---

## 7. Multiple Raw Artifact selection rule

When one Normalization Run has multiple input Raw Artifacts, P-RAW-02 makes a deliberate no-heuristic decision:

```text
ALL run inputs are provenance-required.
```

Reasons:

1. the current canonical schema records run-level inputs, not per-Evidence exact origin;
2. selecting a subset would assert provenance precision that SGOKB does not possess;
3. artifact kind and path are not a canonical statement that an input was irrelevant to a particular Evidence item;
4. historical reproducibility is stronger when the complete normalizer input set is retained.

Therefore:

```text
1 run input  -> include 1
N run inputs -> include N
```

If one required input cannot be verified or cannot safely be packaged, the resolver/package operation MUST report the problem rather than quietly degrade to a partial covering set.

---

## 8. Auxiliary artifact inclusion policy

P-RAW-02 distinguishes **normalization inputs** from **Snapshot siblings**.

### 8.1 Required

Every Raw Artifact explicitly referenced by `normalization_run_artifacts` for the selected Evidence's run is required provenance material.

A Raw input MUST NOT be omitted merely because it looks auxiliary, for example because of:

- `artifact_kind`;
- non-primary-looking `logical_path`;
- media type;
- filename;
- apparent duplication of content.

Those fields do not prove irrelevance.

### 8.2 Excluded by default

A Raw Artifact that belongs to the same Snapshot but is **not** an input of the Evidence's Normalization Run is not part of the P-RAW-02 provenance covering set.

The resolver MUST NOT auto-include Snapshot siblings just because they share:

- Source;
- Snapshot;
- path prefix;
- hash;
- media type;
- artifact kind.

### 8.3 Future explicit auxiliary inclusion

P-RAW-03 may define explicitly requested Package support artifacts outside the grounding covering set, for example operator-visible or processing-support material.

If such a feature is introduced, it MUST remain distinguishable from provenance-required Raw inputs and MUST NOT become an eligible Result grounding target merely by being present in the Package.

P-RAW-02 therefore freezes this distinction:

```text
provenance-required Raw != optional Package auxiliary artifact
```

---

## 9. Historical carry-forward contract

Historical accepted grounding MUST remain bound to the generation that actually produced the accepted Evidence.

Suppose:

```text
Source S
  Snapshot S1 / Run R1 / Evidence E1 / Raw A1   <- accepted historical grounding
  Snapshot S2 / Run R2 / Evidence E2 / Raw A2   <- currently effective generation
```

If E1 is protected / carried forward into an update Package:

```text
resolution(E1) = R1 -> A1
```

It MUST NOT become:

```text
E1 -> current effective R2 -> A2
```

Current effective Snapshot / Run state may be exposed as diagnostic context, but it is not a provenance substitution rule.

This preserves the distinction between:

```text
historical origin provenance
current effective Source generation
```

The resolver therefore follows the Evidence's immutable origin run, not the Source's current selected run.

---

## 10. Snapshot / Source binding rules

For one EvidenceRawResolution:

```text
Evidence.normalization_run_id
  -> Run.snapshot_id
  -> Snapshot.source_id
```

Every resolved Raw Artifact MUST have:

```text
RawArtifact.snapshot_id == Run.snapshot_id
```

The Source identity is obtained through that exact Snapshot.

The resolver MUST NOT use Object association or Source title/locator matching to infer Source identity.

Object association determines relevance / selection upstream; it does not rewrite provenance.

---

## 11. Logical path / media type / byte size / hash semantics

### `logical_path`

- descriptive locator within the captured material;
- retained for operator / Package diagnostics;
- not canonical identity;
- not a selection priority;
- duplicate or missing logical-path values do not justify dropping an artifact.

### `media_type`

- describes material format;
- retained for Package policy and external-AI handling;
- not used by the provenance resolver to rank inputs;
- unsupported media is a downstream Package-materialization/preflight problem, not permission to pretend the Raw input never existed.

### `byte_size`

- canonical expected byte count;
- must be compared against physical material before egress;
- mismatch blocks successful materialization.

### `sha256`

- canonical expected content digest;
- must be recomputed before egress;
- mismatch blocks successful materialization;
- cannot replace `artifact_id` as provenance identity.

### `storage_path`

- points to canonical stored material under the current implementation;
- is an implementation/storage locator, not a portable external grounding identity;
- Package v2 MUST not require external AI to understand canonical host filesystem paths.

---

## 12. Fail-closed matrix

| Condition | Resolver outcome | Silent fallback allowed? |
|---|---|---|
| Evidence does not exist | BLOCKED | No |
| Evidence has no resolvable run | BLOCKED | No |
| Normalization Run does not exist | BLOCKED | No |
| Run has zero Raw inputs | BLOCKED | No |
| Run membership references missing Raw row | BLOCKED | No |
| Raw belongs to different Snapshot than run | BLOCKED | No |
| Snapshot missing | BLOCKED | No |
| Source missing | BLOCKED | No |
| Physical Raw bytes missing | BLOCKED | No |
| Raw unreadable | BLOCKED | No |
| Byte size differs from canonical metadata | BLOCKED | No |
| SHA-256 differs from canonical metadata | BLOCKED | No |
| Multiple run inputs | RESOLVE ALL | Subset heuristic prohibited |
| Multiple Evidence point to same Raw ID | RESOLVE + DEDUP PACKAGE IDENTITY | Mapping must be retained |
| Same hash under different Raw IDs | KEEP BOTH IDENTITIES | Hash-only collapse prohibited |
| Same-Snapshot Raw not used by run | EXCLUDE BY DEFAULT | No auto-include |
| Historical Evidence has newer effective generation | USE HISTORICAL ORIGIN RUN | No rebasing |
| Unsupported / unsafe media for egress | provenance remains known; Package build/preflight BLOCKS unless later explicit policy handles it | No omission disguised as successful grounding |

The key safety invariant is:

```text
Partial provenance must never be presented as complete provenance.
```

---

## 13. No-fallback / no-guess rules

A conforming resolver MUST NOT:

- search Raw files for the Evidence text and pick the best match;
- choose a Raw Artifact by filename resemblance;
- prefer `rendered_dom`, `html`, `text`, or another artifact kind by hard-coded heuristic;
- switch to the current effective Snapshot / Run;
- include arbitrary same-Snapshot artifacts as grounding;
- omit an input because its media type is inconvenient;
- use Evidence Markdown as a fallback Raw substitute;
- treat SHA equality as canonical artifact identity equality;
- infer per-Evidence byte ranges not recorded in canonical provenance.

If SGOKB later needs exact Evidence-to-Raw spans, that capability requires new explicit canonical provenance data rather than a resolver heuristic.

---

## 14. Resolution vs Package materialization boundary

P-RAW-02 separates two responsibilities.

### Provenance resolution

Answers:

```text
Which Raw Artifact identities form the complete currently provable input covering set for this Evidence?
```

This task owns that answer.

### Package materialization / egress

Answers:

```text
How are those Raw bytes represented in Package v2?
Which media are allowed?
How are budgets applied?
What secret / privacy checks run?
What external locator does Result v2 cite?
```

Those are P-RAW-03/04/05 concerns.

A Package policy may block an otherwise valid provenance resolution, but it MUST NOT silently alter the provenance result to make packaging easier.

---

## 15. Traceability invariants for P-RAW-03

P-RAW-03 MUST be able to serialize enough information to prove at least these relations:

```text
selected Evidence ID
  -> normalization_run_id
  -> snapshot_id
  -> source_id
  -> included Raw Artifact ID(s)
  -> expected SHA-256 / byte size
```

After Package-level deduplication it MUST still be possible to answer:

```text
Which selected Evidence caused Raw A to be included?
Which Raw inputs cover selected Evidence E?
Which historical Source generation produced E?
What canonical hash was verified before egress?
```

The future manifest may choose a normalized graph or per-Evidence mapping structure, but it must preserve these answers exactly.

---

## 16. Determinism requirements

For the same canonical database state and the same selected Evidence IDs, the Raw resolver MUST produce the same identity graph.

Determinism requires:

1. traversal only through canonical IDs / foreign-key relations;
2. no content-similarity or filename heuristics;
3. full run-input inclusion;
4. deduplication by `artifact_id` only;
5. stable ordering for serialized outputs;
6. no dependence on current effective generation except optional diagnostics;
7. no dependence on filesystem enumeration order.

Physical byte verification may change a successful resolution into BLOCKED if stored material has changed or disappeared. That is intentional integrity behavior, not nondeterministic selection.

---

## 17. Compatibility with current Evidence role

P-RAW-02 does not remove Evidence.

Evidence remains:

```text
retrieval unit
human selection unit
budget/manual include-exclude intent
historical accepted-provenance anchor
bridge from semantic extraction back to Source generation
```

Raw Artifact becomes the material external AI will read, while Evidence remains the upstream selector that determines which provenance chain to traverse.

This preserves the Phase P architecture:

```text
Evidence Retrieval / Selection
        ↓
selected Evidence
        ↓
Raw provenance resolution
        ↓
Raw-bearing Package
```

---

## 18. Version compatibility

P-RAW-02 does not alter `sgokb.object-evidence-package/1.0`.

Current v1 semantics remain:

```text
Evidence Markdown external semantic payload
Evidence-ID grounding
```

The resolution contract becomes an input to Package v2 design only.

Therefore:

```text
v1 Package / Result -> existing v1 interpretation
v2 Package / Result -> future Raw-grounded interpretation
```

No v1 artifact may be retroactively treated as though the external AI had read Raw material.

---

## 19. Implementation obligations deferred to P-RAW-05

The future implementation must provide a transport-neutral resolver service callable by CLI and GUI/Application flows.

At minimum implementation tests will need to demonstrate:

1. one Evidence / one Raw resolves deterministically;
2. one Evidence / multiple run inputs resolves all inputs;
3. multiple Evidence / shared Raw deduplicates Package Raw identity while preserving mappings;
4. same-hash distinct artifact IDs remain distinct provenance identities;
5. same-Snapshot non-input artifact is excluded;
6. historical carry-forward resolves the historical origin run;
7. missing Raw fails closed;
8. size mismatch fails closed;
9. hash mismatch fails closed;
10. run/Raw Snapshot mismatch fails closed;
11. stable ordering does not depend on filesystem or DB incidental row order.

P-RAW-06 will provide formal acceptance for these behaviors.

---

## 20. Acceptance of P-RAW-02

The deterministic algorithm is frozen as:

```text
FOR EACH selected/protected Evidence E:
    load E
    load E.normalization_run
    load ALL normalization_run_artifacts for that run
    require non-empty input set
    require every Raw row to exist
    require every Raw.snapshot_id == run.snapshot_id
    bind Source through that exact Snapshot
    verify stored bytes / byte_size / sha256 before egress
    return ALL inputs as E's Raw Input Covering Set

FOR PACKAGE-LEVEL UNION:
    deduplicate by artifact_id
    retain every Evidence -> Raw mapping edge
    never deduplicate provenance identity by hash
    never substitute current effective generation
    never infer a smaller subset
```

Auxiliary rule:

```text
run input Raw        = provenance-required
same-Snapshot sibling = excluded by default
future optional Package auxiliary = separate, non-grounding category
```

Failure rule:

```text
missing / changed / inconsistent provenance or bytes
    -> fail closed
    -> no Evidence-Markdown fallback
    -> no newer-generation substitution
    -> no partial covering set presented as complete
```

Therefore:

```text
P-RAW-02 = Complete / Accepted
```

Next design task:

```text
P-RAW-03 — RAW-bearing Package v2 design
```
