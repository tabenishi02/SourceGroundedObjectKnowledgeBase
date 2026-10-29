# Phase P — GUI / RAW Grounding / Runtime Modernization Status

Updated: 2026-10-30

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Status: **In Progress**
- Previous phase: `Phase O — Documentation / Release / Git cleanup` — **Complete**
- Current released baseline: `v1.1.0`
- Planning authority: [`PHASE_P_MODERNIZATION_PLAN.md`](PHASE_P_MODERNIZATION_PLAN.md)
- Task authority: [`PHASE_P_TASKS.md`](PHASE_P_TASKS.md)

## Accepted modernization direction

```text
Priority 1: GUI
Priority 2: RAW Grounding
Priority 3: Runtime / Qdrant auto-start
```

## Current task state

| Workstream | Task | Status | Summary |
|---|---|---|---|
| GUI | P-GUI-01 | **Complete / Accepted** | GUI requirements / compatibility contract |
| GUI | P-GUI-02 | **Complete / Accepted** | PySide6 architecture / packaging / license |
| GUI | P-GUI-03 | **Complete / Accepted** | Transport-neutral Application boundary audit / refactor plan |
| GUI | P-GUI-03R | **Complete / Accepted** | Shared Application/operator boundary refactor; R9 regression PASS |
| GUI | P-GUI-04 | **Complete / Accepted** | GUI shell / Workspace / navigation foundation |
| GUI | P-GUI-05 | **Complete / Accepted** | Object / Source / Evidence / Association GUI |
| GUI | P-GUI-06 | **Complete / Accepted** | Search / Similarity / Registry / Version GUI; Attempt 09 + interactive PASS |
| GUI | P-GUI-07 | **Complete / Accepted** | Progress / error / safety / audit UX; automated + interactive PASS |
| GUI | P-GUI-08 | Blocked by P-RAW | Package / Result GUI |
| GUI | P-GUI-09 | Not Started | System / Maintenance / MCP / Advanced GUI |
| GUI | P-GUI-10 | Not Started | GUI parity / regression acceptance |
| RAW | P-RAW-01 | **Complete / Accepted** | Current Evidence Package / Result impact survey |
| RAW | P-RAW-02 | **Complete / Accepted** | Deterministic Evidence -> Raw Artifact provenance resolution contract |
| RAW | P-RAW-03 | **Complete / Accepted** | Versioned RAW-bearing Package v2 design |
| RAW | P-RAW-04 | **Complete / Accepted** | Raw-grounded Object Result v2 design |
| RAW | P-RAW-05 | **Implementation Complete / Automated Verification Pending** | Resolver -> Package v2 -> Result v2 -> Raw provenance implementation |
| RAW | P-RAW-06 | Blocked by P-RAW-05 verification | RAW Grounding acceptance / compatibility / documentation |
| Runtime | P-RUNTIME-01..06 | Not Started | Windows Qdrant auto-start / health / GUI integration |
| Closure | P-CLOSE-01 | Not Started | Full regression / docs / release integration |

## GUI baseline

```text
Framework             = PySide6 / Qt Widgets
CLI/GUI boundary      = shared Application / Service layer
GUI backend           = QObject worker on dedicated QThread
SQLite                = Repository per operation in worker thread
Backend concurrency   = serialized per Workspace initially
Windows deployment    = pyside6-deploy / Nuitka standalone directory
Qt linking            = dynamic / separate shared libraries
```

GUI is not a CLI subprocess wrapper. Qdrant remains an independent shared runtime.

## P-GUI-01..07 accepted baseline

```text
P-GUI-01..03R = Complete / Accepted
P-GUI-04      = Complete / Accepted
P-GUI-05      = Complete / Accepted
P-GUI-06      = Complete / Accepted
P-GUI-07      = Complete / Accepted
```

P-GUI-06 final evidence:

```text
focused regression = 29 / 29 PASS
Ruff               = PASS
full regression    = 818 / 818 PASS
warnings           = 2 known local-Qdrant warnings
interactive smoke  = PASS in accepted scope
```

P-GUI-07 final evidence:

```text
focused GUI gate = 34 / 34 PASS
Ruff             = PASS
full regression  = 823 / 823 PASS
warnings         = 2 known local-Qdrant warnings
interactive smoke = PASS in accepted scope
```

Final GUI authority includes:

- `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`
- `docs/evaluation/P_GUI_06_FINAL_INTERACTIVE_ACCEPTANCE.md`
- `docs/evaluation/P_GUI_07_DYNAMIC_VERIFICATION_ATTEMPT_01.md`
- `docs/evaluation/P_GUI_07_FINAL_INTERACTIVE_ACCEPTANCE.md`

## P-RAW-01 accepted impact survey

Authority:

- `docs/evaluation/P_RAW_01_CURRENT_EVIDENCE_PACKAGE_RESULT_IMPACT_SURVEY.md`

The survey confirms that Raw Grounding impact is concentrated at the external exchange / grounding boundary rather than the core accepted Knowledge model.

Breaking contracts:

```text
Evidence-Markdown external semantic payload
Evidence-only Package grounding membership
Evidence-ID-only analysis grounding instructions
Evidence-ID-only Result grounding representation
Evidence-only Result membership validation
```

Migration-required contracts:

```text
Evidence -> Raw provenance resolution
Package audit / Raw membership trace
Package budget / preflight / egress coverage
review grounding presentation
import grounding persistence / accepted provenance
v1/v2 receive and validation routing
tests / fixtures / grounded-generation benchmarks
operator / acceptance documentation
```

P-RAW-01 requires richer provenance logically but deliberately does not select a physical DB schema migration. That is deferred to P-RAW-04/05.

Therefore:

```text
P-RAW-01 = Complete / Accepted
```

## P-RAW-02 accepted provenance resolution contract

Authority:

- `docs/design/P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`

P-RAW-02 freezes the deterministic Raw resolution scope at the complete input set of the Evidence's own Normalization Run:

```text
resolution scope = normalization_run_inputs
```

For each selected or protected Evidence:

```text
Evidence
  -> its own Normalization Run
  -> ALL normalization_run_artifacts
  -> exact Snapshot / Source generation
  -> physical byte-size / SHA-256 verification before egress
```

The current schema does not store an exact per-Evidence Raw subset or byte range. Therefore P-RAW-02 deliberately avoids invented precision and treats the run input set as a provenance-complete Raw Input Covering Set.

Key rules:

1. every run input Raw Artifact is provenance-required;
2. same-Snapshot artifacts not used by the run are excluded by default;
3. multiple Evidence pointing to one Raw Artifact are deduplicated by `artifact_id` at Package identity level while every Evidence -> Raw edge is preserved;
4. distinct artifact IDs are never collapsed merely because SHA-256 matches;
5. historical carry-forward Evidence resolves through its original historical run, never the currently effective generation;
6. artifact kind, path, filename, media type or content similarity are not provenance-selection heuristics;
7. missing Raw, missing provenance, Snapshot mismatch, byte-size mismatch or hash mismatch fail closed;
8. there is no Evidence-Markdown fallback and no partial covering set may be presented as complete;
9. optional Package auxiliary artifacts remain separate from provenance-required grounding material.

The resolver contract is intentionally separated from Package v2 materialization policy. P-RAW-03 may block an otherwise valid provenance set because of media, budget, privacy, secret or egress rules, but it must not silently alter provenance to make packaging succeed.

No source code, runtime behavior, Package schema, Result schema, or DB schema changed in P-RAW-02. It is a design-contract task, so the regression suite was not rerun.

Therefore:

```text
P-RAW-02 = Complete / Accepted
```

## P-RAW-03 accepted RAW-bearing Package v2 design

Authority:

- `docs/design/P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`

Package v2 is explicitly versioned rather than redefining v1:

```text
Package schema     = sgokb.object-evidence-package/2.0
schema ID          = urn:sgokb:schema:object-evidence-package:2.0
instructions       = sgokb.object-analysis/2.0
expected Result    = sgokb.object-result/2.0
Raw grounding      = sgokb.raw-grounding/1.0
resolver contract  = sgokb.evidence-to-raw/1.0
```

The authoritative semantic payload changes from generated Evidence Markdown to exact Raw bytes:

```text
v1: evidence/source_*.md
v2: raw/artifact_NNNN/payload
```

Evidence remains present as selection/provenance metadata, but grounding membership authority becomes:

```text
manifest.raw_grounding.included_raw_artifact_ids
```

Accepted v2 invariants include:

1. one direct Evidence -> Raw binding exists for every selected Evidence;
2. every binding contains the complete P-RAW-02 Raw Input Covering Set;
3. physical Raw payload is deduplicated by `artifact_id`, while all Evidence -> Raw edges remain;
4. distinct artifact IDs remain distinct even when hashes match;
5. local `storage_path` is never exported; safe deterministic Package paths are allocated independently;
6. Raw bytes are copied exactly without normalization, conversion, truncation or Evidence-Markdown fallback;
7. Evidence selection budget and Raw materialization budget are separate;
8. unsupported media, Raw budget overflow, credential/secret policy, missing or modified Raw can block materialization/export but cannot rewrite provenance;
9. `files[]` remains the exhaustive transport/hash inventory and adds role `raw_grounding`;
10. `manifest_sha256` identifies one Package instance while `raw_grounding.integrity.grounding_set_sha256` provides a stable Raw provenance/material fingerprint;
11. historical carry-forward resolves and packages the original historical Raw generation;
12. v1 and v2 are explicitly dispatched and are never silently reinterpreted or downgraded.

Baseline v2 layout:

```text
manifest.json
instructions.md
current_object.json                    # update Package only
schema/object-result-v2.schema.json
raw/artifact_0001/payload
raw/artifact_0002/payload
...
```

P-RAW-03 reserves `sgokb.object-result/2.0` only as the expected Result family. P-RAW-04 owns the exact statement/attribute/relation Raw grounding reference schema, locator semantics, accepted provenance persistence design, and v1/v2 Result coexistence rules.

No source code, runtime behavior, implemented Package/Result schema, or DB schema changed in P-RAW-03. It is a design task, so the regression suite was not rerun.

Therefore:

```text
P-RAW-03 = Complete / Accepted
```

## P-RAW-04 accepted Raw-grounded Object Result v2 design

Authority:

- `docs/design/P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`

Result v2 is explicitly versioned:

```text
Result schema       = sgokb.object-result/2.0
schema ID           = urn:sgokb:schema:object-result:2.0
Package schema      = sgokb.object-evidence-package/2.0
instructions        = sgokb.object-analysis/2.0
grounding contract  = sgokb.raw-grounding/1.0
```

The Result grounding target becomes the exact Package-member `raw_artifact_id`. The v1 `evidence[]` field is replaced by v2 `grounding[]`; Result v2 contains no Evidence IDs for claim grounding.

Baseline Raw reference:

```json
{
  "raw_artifact_id": "raw-...",
  "role": "supports"
}
```

Optional locator precision supports only mechanically verifiable baseline kinds:

```text
byte_range   zero-based half-open [start,end) over exact Raw bytes
text_quote   exact decoded Raw text with optional prefix/suffix disambiguation
```

An invalid asserted locator is a validation error; producers may omit locator rather than invent precision.

Package/Result binding additionally includes:

```text
grounding_contract
grounding_set_sha256
```

so a Result is bound to the exact Raw membership/material fingerprint.

Accepted persistence boundary:

```text
v1 claim grounding -> evidence_links
v2 claim grounding -> new raw_grounding_links family
```

A v2 import MUST NOT synthesize Evidence links by mapping Raw references back through Package Evidence selection metadata. Evidence remains selection lineage, not claim grounding.

P-RAW-04 also fixes the post-v2 historical carry-forward rule. For a v2 current Version, SGOKB collects accepted Raw grounding IDs, reopens the originating Package Evidence->Raw bindings, conservatively recovers every matching Evidence as carry-forward **selection lineage**, and resolves those Evidence records through their original historical runs under P-RAW-02. This preserves historical Raw provenance without claiming the AI cited those Evidence records.

Compatibility direction is therefore:

```text
v1 accepted Version -> v2 update = supported
v2 accepted Version -> v1 update = blocked by default
```

Review/diff must separate semantic Knowledge changes from grounding changes so an Evidence-v1 -> Raw-v2 grounding-model transition is not itself treated as destructive Knowledge deletion.

No source code, runtime behavior, implemented JSON Schema, or DB schema changed in P-RAW-04. It is a design-only task, so the regression suite was not rerun.

Therefore:

```text
P-RAW-04 = Complete / Accepted
```

## P-RAW-05 implementation state

Authority:

- `docs/evaluation/P_RAW_05_RAW_GROUNDING_IMPLEMENTATION.md`

The accepted P-RAW-02..04 contracts are now implemented as an additive v2 exchange path.

Implemented areas:

```text
migration 019 Raw grounding persistence
Evidence -> Raw resolver with exact byte/hash verification
Package v2 schema / builder / instructions / transfer / preflight
Package Raw membership and Evidence -> Raw audit
Result v2 schema / validation / locator verification
version-dispatched Result validation / review / import
Raw-aware content-vs-grounding diff
raw_grounding_links accepted provenance
historical carry-forward selection-lineage recovery
Raw-aware accepted Object / Version reads
Package v1 / Result v1 compatibility path retained
v2 current -> legacy v1 Package build blocked
CLI --package-version v1|v2
focused P-RAW-05 regression coverage
```

During this implementation gate the CLI default intentionally remains `v1`. P-RAW-06 acceptance decides the release/cutover disposition; no script is silently switched before the v2 boundary is verified.

No automated PASS is claimed yet.

Therefore:

```text
P-RAW-05 = Implementation Complete / Automated Verification Pending
P-RAW-06 = Blocked by P-RAW-05 verification
```

## Sequencing

```text
P-GUI-01..07 Complete / Accepted
        ↓
P-RAW-01..04 Complete / Accepted
        ↓
P-RAW-05 implementation complete
        ↓
P-RAW-05 focused + Ruff + full regression   <- CURRENT GATE
        ↓
P-RAW-06 RAW Grounding acceptance
        ↓
P-GUI-08 Package / Result GUI
```

`P-GUI-08` remains blocked until `P-RAW-01..P-RAW-06` complete. `P-GUI-09` also depends on `P-RUNTIME-03`.

## Current authority boundary

Phase P remains in development. Released system semantics continue to be governed by current architecture/decision/operations documents and release `v1.1.0`.

P-GUI-01 through P-GUI-07 and P-RAW-01 through P-RAW-04 are accepted baselines. P-RAW-05 implementation exists on `main` but is not accepted until its automated verification gate passes.

## Next

```text
P-RAW-05 automated verification — focused exchange/Raw gate + Ruff + full regression
```
