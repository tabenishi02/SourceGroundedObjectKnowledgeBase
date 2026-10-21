# N-04G-25A — Historical Handoff

更新日: 2026-10-22

- Project: `Source Grounded Object Knowledge Base (SGOKB)`
- Historical task: `N-04G-25A — Residual Classifier Benchmark / Selection`
- Historical result: **VALID_FAIL_NO_SELECTION**
- Current status: **Superseded as N-04 completion path**
- Superseding decision: `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
- Current N-04 next task: **N-04R-03 — Formal Harness Reconstruction**

## 1. Historical result retained

G-25A evaluated concrete Residual classifiers for two independent tasks defined by the former v4 Grounded Generation architecture.

```text
V2-R-A — Atomicity
  ATOMIC
  NON_ATOMIC
  AMBIGUOUS

V2-R-C — Content Type
  SOURCE_FACT_CONTENT
  INTERPRETATION_CONTENT
  CREATIVE_CONTENT
  CONTEXT_LIMIT_CONTENT
  MIXED_CONTENT
  AMBIGUOUS
```

Development benchmark completed validly, but no candidate met all mandatory selection Gates.

```text
G-25A = VALID_FAIL_NO_SELECTION
V2-R-A selected classifier = none
V2-R-C selected classifier = none
Frozen 47 final confirmation = not started
```

This result remains valid historical research evidence.

## 2. Why G-25A is no longer the current N-04 path

G-25A existed because old N-04 treated Consumer-generated text grounding as SGOKB formal responsibility.

2026-10-22 responsibility reconstruction established:

```text
SGOKB formal N-04 responsibility
  ends at public Knowledge Access Boundary

Consumer inference / generation
  is external responsibility
```

Therefore N-04 does not require SGOKB to classify or certify arbitrary Consumer-generated text.

G-25A success is no longer an N-04 Completion prerequisite.

## 3. Do not continue classifier selection for N-04

For current N-04 work:

- do not add new Atomicity candidates;
- do not add new Content-Type candidates;
- do not tune thresholds / taxonomy / abstention policy;
- do not run Frozen 47;
- do not weaken historical Gates to obtain a winner;
- do not modify Grounded Generation production code to unblock N-04.

Any future classifier research must be explicitly authorized as a separate research / Consumer-side task.

## 4. Historical evidence summary

Mandatory Reference Workstation preflight passed before the valid development selection run.

Development corpora, split manifests, candidate revisions, run manifests, benchmark results and repeatability evidence remain part of the repository history.

Observed high-level result:

- some candidates allowed unsafe false acceptance;
- safer thresholds rejected valid inputs;
- Content-Type boundaries exposed taxonomy / identifiability problems;
- no candidate satisfied the pre-frozen zero-error selection policy.

These findings should be preserved for N-04R-05 asset disposition and any future grounded-generation research.

## 5. Frozen 47 handling

Frozen 47 remains untouched by G-25A final confirmation.

Under the current N-04 responsibility boundary it must not be run merely to complete N-04.

If Grounded Generation research is resumed in the future, its use requires a separately defined evaluation protocol.

## 6. Current authority

Read instead:

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
3. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`
4. `docs/planning/phases/N/N04/post-g12/N04_POST_G12_CHAT_HANDOFF.md`

Current chain:

```text
N-04R-01 Complete
N-04R-02 Documentation Reconstruction
N-04R-03 Formal Harness Reconstruction
N-04R-04 Reference Workstation Re-Acceptance
N-04R-05 Grounded Generation Asset Disposition
```
