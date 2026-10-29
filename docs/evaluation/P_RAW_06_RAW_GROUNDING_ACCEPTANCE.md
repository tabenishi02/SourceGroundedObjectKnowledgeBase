# P-RAW-06 — RAW Grounding Acceptance / Compatibility / Documentation

Updated: 2026-10-30

- Task: `P-RAW-06 [P0] RAW Grounding acceptance / compatibility / documentation`
- Verification branch: `p-raw-06-acceptance`
- Verified branch source: `5e4c8729f8d79c3f3fa956af9208aae98b1a2a48`
- PR synthetic merge ref tested by Actions: `0e037d4b69dcefad46ef88900dcaa98c32559247`
- GitHub Actions run: `40937273709` (`P-RAW-06 Acceptance`, run #6)
- Reference environment: Windows Server 2025 / Python 3.10.11
- Runner image: `windows-2025-vs2026` / `20261021.278.1`
- Disposition: **PASS / Complete / Accepted**
- Next: **P-GUI-08 — Package / Result GUI**

## 1. Final gate

P-RAW-06 executed an independent acceptance gate on top of the accepted P-RAW-05 implementation.

Final results:

```text
P-RAW-06 focused acceptance       = 6 / 6 PASS
P-RAW / legacy v1 exchange gate   = 91 / 91 PASS
Ruff src/tests                    = PASS
full repository regression        = 833 / 833 PASS
warnings                          = 2 known local-Qdrant warnings
```

Durations recorded by the accepted run:

```text
focused acceptance = 29.61 s
exchange regression = 123.11 s
full regression = 1142.89 s
```

The two warnings are the existing accepted local-Qdrant limitations:

- payload indexes have no effect in local Qdrant except supported text-index behavior;
- local-mode exact search ignores `search_params` except `idf`.

No warning is a P-RAW-06 failure.

## 2. Acceptance coverage

The focused suite is `tests/test_p_raw_06_acceptance.py`.

### A1 — deterministic Evidence -> Raw resolution

PASS.

The test creates two Evidence records that resolve through one Normalization Run and confirms that input order and repeated Evidence selection do not change the final Raw membership set.

### A2 — duplicate identity semantics

PASS.

The test confirms both sides of the P-RAW-02 identity rule:

```text
same raw_artifact_id reached repeatedly -> one Package Raw identity
same SHA-256 with distinct raw_artifact_id values -> distinct Raw identities remain distinct
```

Hash equality is therefore not used as an identity-collapse heuristic.

### A3 — missing / modified Raw fail closed

PASS.

The resolver succeeds with the canonical bytes, rejects a missing physical Raw file, succeeds again after exact restoration, and rejects modified bytes whose canonical metadata no longer matches.

No Evidence-Markdown fallback is used.

### A4 — Package v2 integrity / preflight / egress safety

PASS.

The acceptance path covers:

- valid Package v2 manifest;
- normal stage / preflight / export;
- unsafe nested destination rejection;
- manifest tamper rejection;
- Raw payload hash tamper rejection;
- unexpected file rejection;
- absence of generated `evidence/` semantic payload.

### A5 — Result v2 membership / grounding-set validation

PASS.

Validation rejects:

- a canonical-looking `raw_artifact_id` that is outside the audited Package Raw set;
- a Result whose `grounding_set_sha256` differs from the Package binding.

This confirms that canonical database existence is not enough: claim grounding must belong to the exact audited Package instance.

### A6 — Raw Package -> external Result -> accepted Version end-to-end

PASS.

The test uses the actual Repository/Application exchange stack rather than mocked exchange services:

```text
Object
  -> Source / Snapshot / Raw / Evidence
  -> Package v2 build
  -> stage
  -> export
  -> external-boundary Raw read
  -> Result v2
  -> receive
  -> validate
  -> review
  -> import
  -> accepted Version read
```

The external-boundary simulation reads semantic content from the exported Raw payload and returns a Result v2 grounded by `raw_artifact_id` with a mechanically verifiable `text_quote` locator.

Post-import assertions prove:

```text
current Version = imported v2 Version
grounding_kind = raw
raw_grounding_links = present
fabricated evidence_links for v2 = 0
accepted read exposes Raw grounding
```

This satisfies the P-RAW-06 real Object lifecycle requirement using a concrete Character Object in a real temporary SGOKB database and the production Application/Repository code path.

## 3. v1 / v2 compatibility acceptance

PASS.

The focused compatibility cycle demonstrates:

```text
no-option package build before Raw current Version = v1 compatibility behavior retained
v1 Package -> Result v1 -> accepted Version = PASS
v1 accepted Version -> Package v2 = PASS
historical Evidence selection lineage carried into v2 Package = PASS
Package v2 -> Result v2 -> accepted Version = PASS
v2 accepted Version -> Package v1 downgrade = BLOCKED as designed
```

The accepted compatibility matrix is therefore:

| Current / input state | Operation | Accepted disposition |
|---|---|---|
| no current Version | Package v1 | supported legacy path |
| no current Version | Package v2 | supported Raw path |
| v1 accepted Version | v1 update | supported legacy path |
| v1 accepted Version | v2 update | supported migration path |
| v2 accepted Version | v2 update | supported normal Raw path |
| v2 accepted Version | v1 update | blocked by default |
| Result v1 | audited v1 validation/import | supported |
| Result v2 | audited v2 validation/import | supported |
| Result v2 Raw grounding | synthesize Evidence claim links | forbidden |

## 4. Cutover disposition

P-RAW-06 formally accepts Package v2 / Result v2 as the Raw-grounded external AI boundary.

For Phase P Raw-grounded development and operations, the operator must explicitly request:

```text
--package-version v2
```

The no-option CLI/Application default intentionally remains `v1` during the unreleased Phase P integration window.

Reasons:

1. released baseline remains `v1.1.0`;
2. P-GUI-08 and Runtime work remain incomplete;
3. silently changing existing automation before a release boundary would create an avoidable compatibility break;
4. explicit version routing already provides a safe accepted v2 path.

`P-CLOSE-01` owns the final release-default decision and must pair any default change with release notes and compatibility review.

## 5. Documentation acceptance

P-RAW-06 adds and accepts the following Phase P authorities:

- requirements: `docs/requirements/RAW_GROUNDING_REQUIREMENTS.md`
- cutover / compatibility decision: `docs/decisions/P_RAW_06_RAW_GROUNDING_CUTOVER_DECISION.md`
- integrated design: `docs/design/P_RAW_06_ACCEPTED_EXTERNAL_AI_BOUNDARY.md`
- operator workflow: `docs/operations/P_RAW_06_RAW_GROUNDING_WORKFLOW.md`
- acceptance evidence: this document

Together they establish the accepted boundary:

```text
Evidence = selection / provenance lineage
Raw Artifact = Result v2 claim-grounding identity
Package v2 = exact verified Raw exchange boundary
Result v2 = Raw-grounded structured result
Import v2 = raw_grounding_links
```

## 6. Historical diagnostic run

The first focused execution exposed four failures while constructing the new acceptance fixture:

- the fixture attempted two identical Raw canonical identities in one Snapshot and therefore hit the existing `raw_artifacts_unique` constraint;
- three Result inputs were not named the required canonical `result.json`.

These were acceptance-fixture errors, not product defects. The fixture was corrected to create distinct canonical Raw Artifact identities with identical bytes and to obey the standard Result artifact filename contract.

No failure was waived. The final run then reached 6 / 6 focused PASS and the complete 833 / 833 repository PASS.

## 7. Closure

The P-RAW-01..06 workstream now has an accepted operational boundary and full regression evidence.

Therefore:

```text
P-RAW-06 = Complete / Accepted
P-RAW workstream = Complete / Accepted for Phase P
P-GUI-08 = Unblocked / Next
```

P-GUI-08 may now implement Package / Result GUI behavior against the accepted v2 Raw-grounded contract while preserving explicit v1 compatibility routing.
