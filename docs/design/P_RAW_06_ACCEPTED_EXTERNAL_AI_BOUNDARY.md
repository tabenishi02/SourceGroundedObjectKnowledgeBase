# P-RAW-06 — Accepted Raw External AI Boundary

Updated: 2026-10-30

- Task: `P-RAW-06 [P0] RAW Grounding acceptance / compatibility / documentation`
- Status: **Design integration complete; final acceptance depends on verification gate**
- Inputs:
  - `P_RAW_02_EVIDENCE_TO_RAW_PROVENANCE_RESOLUTION_CONTRACT.md`
  - `P_RAW_03_RAW_BEARING_PACKAGE_V2_DESIGN.md`
  - `P_RAW_04_RAW_GROUNDED_OBJECT_RESULT_V2_DESIGN.md`

## 1. Integrated boundary

P-RAW-06 does not redesign P-RAW-02..04. It integrates the three accepted contracts into one operational external-AI boundary:

```text
selected Evidence
  -> original Normalization Run
  -> complete Raw input covering set
  -> exact verified Raw bytes
  -> Package v2
  -> external AI
  -> Result v2 raw_artifact_id grounding
  -> validation / review
  -> import
  -> raw_grounding_links
  -> accepted Version
```

The contract boundary is versioned rather than retroactively changing v1.

## 2. Identity model

The identities have different responsibilities:

```text
Evidence ID       selection / provenance lineage
Raw Artifact ID   claim grounding identity in v2
Package ID        one exchange instance
manifest SHA      Package instance integrity
Raw-set SHA       Raw grounding membership/material fingerprint
Version ID        accepted Knowledge identity
```

No identity may be substituted for another merely because the content is related.

In particular:

- same Raw Artifact ID reached by multiple Evidence items is one Package payload identity;
- different Raw Artifact IDs remain different identities even if SHA-256 is identical;
- Result v2 references Raw Artifact IDs, not Evidence IDs;
- accepted v2 claim provenance remains Raw provenance.

## 3. Semantic and transport separation

`files[]` is transport authority. `raw_grounding.included_raw_artifact_ids` is Raw semantic grounding membership authority. `evidence.items` and `evidence_bindings` are lineage metadata.

These sets are related but are not interchangeable.

A Package may contain instructions, schema, current Object context and Raw payloads. Only the Raw membership set authorizes new source-grounded claims.

## 4. Fail-closed boundaries

The system fails closed at four independent boundaries:

### Resolution

Failure examples:

- Evidence provenance missing;
- run input set inconsistent;
- Snapshot/Source mismatch;
- Raw physical bytes unavailable;
- byte-size/SHA mismatch.

### Materialization / egress

Failure examples:

- unsupported media;
- Raw count/size budget exceeded;
- unsafe Package layout;
- missing/unexpected file;
- file hash mismatch;
- credential material detection;
- unsafe destination or conflicting Package identity.

### Result validation

Failure examples:

- Result Raw ID outside Package membership;
- Package/Result grounding-set mismatch;
- canonical/audited Raw provenance mismatch;
- staged Raw payload changed;
- locator cannot be mechanically verified;
- stale package/base-version binding.

### Import

Failure examples:

- validation not successful;
- review blocked or acknowledgement missing;
- current Version changed after analysis;
- downgrade would lose Raw grounding semantics.

No failure boundary may be bypassed by silently replacing Raw with Evidence Markdown or synthesizing Evidence claim grounding.

## 5. Version coexistence

The exchange families coexist as explicit versions:

```text
v1 = Evidence-Markdown / Evidence-ID grounding legacy family
v2 = exact Raw / raw_artifact_id grounding Raw family
```

Routers select validation/review/import behavior from the audited Package schema version. A v1 artifact is never interpreted using v2 semantics and vice versa.

Transition rules:

```text
v1 -> v2 = supported
v2 -> v2 = supported
v2 -> v1 = blocked by default
```

## 6. Historical carry-forward

Raw-grounded accepted Knowledge does not make Evidence irrelevant. Evidence remains the stable selection lineage needed to rebuild later Packages.

When a v2 current Version is updated:

1. collect its accepted Raw grounding identities;
2. reopen the originating Package Evidence->Raw bindings;
3. recover matching Evidence as conservative carry-forward selection lineage;
4. resolve each recovered Evidence through its original historical run;
5. materialize the resulting complete Raw covering set again under current Package v2 safety checks.

This is selection recovery, not reverse synthesis of claim grounding.

## 7. Operator-facing version selection

During Phase P integration the Raw workflow is explicit:

```text
--package-version v2
```

The v1 no-option default is retained until Phase P closure to avoid a silent behavioral change before the release boundary. `P-CLOSE-01` owns the release-default decision.

## 8. Acceptance mapping

P-RAW-06 verification maps directly to this design:

| Acceptance area | Design property |
|---|---|
| deterministic resolution | complete run-input covering set |
| duplicate handling | same-ID dedup / distinct-ID preservation |
| missing/modified Raw | exact-byte fail closed |
| manifest/package integrity | transport + Package identity integrity |
| preflight/egress | materialization safety boundary |
| Result membership | Raw semantic membership authority |
| grounding-set binding | exact Raw-set fingerprint |
| v1/v2 transition | explicit version coexistence |
| end-to-end import | Raw provenance survives through accepted Version |

The final PASS record is `docs/evaluation/P_RAW_06_RAW_GROUNDING_ACCEPTANCE.md`.
