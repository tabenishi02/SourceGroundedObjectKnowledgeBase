# P-RUNTIME-04 — GitHub Actions Billing Blocker / Deferred Verification

Date: 2026-10-31
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
PR: `#81 P-RUNTIME-04 remediate native Windows crash recovery`

## Status

Hosted Windows CI is blocked before runner assignment by the GitHub account billing / spending-limit state, not by the SGOKB product or test suite.

Observed workflow evidence:

```text
run      = 41115542118
attempt  = 2
job      = acceptance
status   = completed
result   = failure
runner   = none
steps    = []
```

GitHub CLI reported:

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings
```

The job executed no workflow step. The failure is therefore neither product/test failure nor CI acceptance evidence.

## Independent acceptance evidence

P-RUNTIME-04 already has stronger direct Windows evidence for the supported deployment:

```text
reference-host reboot/sign-in auto-start                 = PASS
reference-host forced qdrant.exe crash recovery          = PASS
reference-host recovered /readyz                         = HTTP 200
reference-host SGOKB qdrant health                       = healthy / ready=true / 1.19.2
local disposable Task Scheduler recovery smoke           = PASS
local crash recovery PID                                 = 38356 -> 42796
manual restart after local crash                         = none
PowerShell parser validation                             = PASS
focused P-RUNTIME                                        = 9 passed / 0 failed
Ruff                                                     = PASS
full repository regression                               = 858 passed / 0 failed
production Qdrant after local validation                 = unchanged / ready
```

The local validation also verified cleanup and that production Task/config/canonical DB content remained unchanged.

## Closure decision

The authoritative Phase P task definition for P-RUNTIME-04 requires that after Windows restart/login, Qdrant reaches ready without additional manual operation, including unexpected-stop recovery verification. It does not require GitHub-hosted Windows CI as a mandatory completion condition.

The hosted remediation CI gate was an additional verification gate introduced during remediation. Because:

1. the supported reference host passed the actual lifecycle acceptance;
2. an isolated local Windows test reproduced the hosted workflow's dynamic crash-recovery smoke;
3. focused tests, Ruff and full regression all passed locally;
4. hosted jobs are prevented from starting solely by an external billing/spending constraint;
5. no hosted workflow step has produced contradictory product evidence;

the hosted Windows run is reclassified as **non-blocking deferred verification debt**.

Formal disposition:

```text
reference-host acceptance      = Complete / Accepted
local remediation validation   = PASS
GitHub Actions remediation CI  = Deferred / billing-spending external constraint
P-RUNTIME-04 overall           = Complete / Accepted
P-RUNTIME-05                   = Unblocked / Ready
```

This is not a CI PASS claim. Hosted CI remains unexecuted for the remediation HEAD.

## Deferred verification

When GitHub Actions billing/spending capacity becomes available, run the P-RUNTIME-04 Windows workflow and record:

- PowerShell asset parse validation;
- disposable dynamic scheduled-task crash recovery;
- focused P-RUNTIME tests;
- Ruff;
- full repository regression.

A later hosted PASS closes this verification debt only; it is not required to reopen or block P-RUNTIME-05.

If a later hosted run reveals a genuine product or portability regression, treat that result as new remediation work and update the acceptance record accordingly.

## Closure effect

PR #81 may merge on the accepted reference-host and local validation evidence. P-RUNTIME-04 is closed as `Complete / Accepted`, with hosted CI explicitly deferred rather than waived or reported as successful.
