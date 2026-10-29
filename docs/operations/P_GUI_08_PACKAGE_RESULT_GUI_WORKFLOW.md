# P-GUI-08 — Package / Result GUI Workflow

Status: **Complete / Accepted**

Date: 2026-10-30

## Purpose

This runbook describes the Phase P desktop workflow for the accepted Raw-grounded Package v2 / Result v2 external-AI boundary.

The GUI uses the same canonical Application operations as the CLI. It does not bypass Package integrity, Result validation, review, or import controls.

## Package workflow

### 1. Select the Object

Open `Packages` and select the target Object.

### 2. Select the Package contract

For the Phase P Raw-grounded workflow, use:

```text
v2 — Raw grounded (Phase P accepted)
```

Use v1 only when a legacy Evidence-grounded compatibility Package is intentionally required.

The GUI always submits the selected version explicitly. The shared no-option Application/CLI default remains v1 until P-CLOSE-01 decides the release default.

### 3. Select Evidence and budgets

Review or set:

- manual Evidence include IDs;
- manual Evidence exclude IDs;
- candidate / selection / token / Evidence-byte budgets;
- Raw Artifact count budget;
- total Raw-byte budget;
- single Raw-byte budget;
- Knowledge language.

### 4. Build / Resolve Raw

Run `Build / Resolve Raw`.

For v2, inspect:

- included Raw Artifact IDs;
- media type and byte count;
- SHA-256;
- deterministic Package path;
- Evidence -> Raw bindings;
- Package binding and selection summary;
- `grounding_set_sha256`;
- manifest integrity information.

If any build input changes after a build, the GUI marks the flow stale. Rebuild before continuing.

### 5. Stage

Run `Stage`.

Staging reuses the canonical Package transfer / integrity boundary.

### 6. Choose destination and preflight

Choose the external destination and run `Preflight`.

Interpret the disposition as follows:

```text
allow            -> eligible for acknowledged export
review_required  -> inspect the reported condition before acknowledged export
blocked          -> do not export; correct the failure and rerun preflight
```

Changing the destination makes the previous preflight stale.

### 7. Confirm Raw inclusion and export

Before export:

1. inspect the Raw inclusion list;
2. inspect the current preflight result;
3. check the explicit egress acknowledgement;
4. execute `Export`.

If confirmation dialogs are enabled, the existing P-GUI-07 EXTERNAL-operation confirmation also applies.

## Result workflow

### 1. Detect the external Result

Open `Results`, select the incoming root, and run `Detect`.

Select the expected `result.json` from the detected files.

### 2. Receive

Supply the bound Package ID and run `Receive`.

The Result is copied into the immutable receipt boundary before validation/review.

### 3. Validate

Run `Validate`.

Validation checks the versioned Result contract, Package binding, grounding membership, locator rules, and other canonical validation conditions.

A blocked or invalid Result must not proceed to import.

### 4. Review current Knowledge and grounding

Run `Review / Diff`.

Inspect:

- current Knowledge changes;
- validation / review state;
- grounding reference diff;
- v2 Raw Artifact references.

Possible operator-relevant states include:

```text
blocked
review_required
ready_to_import
imported
```

### 5. Import

For `review_required`, explicitly acknowledge the reviewed changes.

Run `Import accepted Knowledge Version`.

The canonical import path persists version-specific grounding:

```text
Result v1 -> evidence_links
Result v2 -> raw_grounding_links
```

Result v2 does not synthesize Evidence claim links.

## Recovery rules

### Package build input changed

Rebuild. Do not reuse the prior staged Package or preflight state.

### Export destination changed

Rerun preflight and repeat explicit acknowledgement.

### Preflight blocked

Correct the reported Package/security/integrity problem and rerun the Package flow. Do not bypass the gate.

### Result invalid or blocked

Correct or regenerate the external Result. Do not import it with an acknowledgement override.

### Result review_required

Inspect the Knowledge and Raw grounding diff. Acknowledge only after accepting the displayed changes.

## Compatibility boundary

During Phase P development:

```text
new Raw-grounded GUI operation  -> explicitly select v2
legacy compatibility operation  -> explicitly select v1
shared omitted-version default  -> remains v1
```

P-CLOSE-01 owns any release-level change to the shared default.
