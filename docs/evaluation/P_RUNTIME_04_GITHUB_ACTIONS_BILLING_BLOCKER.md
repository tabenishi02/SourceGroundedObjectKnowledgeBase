# P-RUNTIME-04 — GitHub Actions Billing Blocker

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
PR: `#81 P-RUNTIME-04 remediate native Windows crash recovery`

## Status

The remaining hosted Windows CI gate is blocked before runner assignment by GitHub account billing / spending-limit state, not by the SGOKB product or test suite.

Observed workflow:

```text
run      = 41115542118
attempt  = 2
job      = acceptance
status   = completed
result   = failure
runner   = none
steps    = []
```

GitHub CLI reported the job annotation:

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings
```

The job therefore did not execute any workflow step. This failure must not be classified as a product/test failure and must not be counted as CI acceptance.

## Acceptance impact

Independent validation already establishes:

```text
reference-host acceptance      = Complete / Accepted
local remediation validation   = PASS
GitHub Actions remediation CI  = Pending / billing-spending blocker
P-RUNTIME-04 overall           = In Progress / Repository CI Pending
P-RUNTIME-05                   = Blocked / Not Started
```

Local validation on Windows 11 / PowerShell 7.6.9 passed the disposable scheduled-task crash-recovery smoke, focused P-RUNTIME tests, Ruff, full repository regression, and production-Qdrant post-test safety checks. Local PASS does not substitute for hosted CI.

## Required operator action

Resolve the GitHub account billing condition before retrying the workflow. Depending on the account state, this means one or both of:

1. update or repair the GitHub payment method / outstanding payment state;
2. increase or create an Actions budget/spending allowance sufficient to start hosted Windows jobs.

After billing is unblocked, rerun the failed workflow and require an actual Windows runner plus executed steps before changing repository acceptance.

## Closure requirement

P-RUNTIME-04 may close only after a hosted workflow execution actually runs and passes:

- PowerShell asset parse validation;
- disposable dynamic scheduled-task crash recovery;
- focused P-RUNTIME tests;
- Ruff;
- full repository regression.

Until then PR #81 remains open and unmerged.
