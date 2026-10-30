# P-RUNTIME-04 — Windows login auto-start implementation status

Date: 2026-10-30
Task: `P-RUNTIME-04 [P1] Windows login auto-start integration`
Disposition: **Implementation verified / formal physical acceptance pending**

## Implemented boundary

P-RUNTIME-04 preserves the accepted P-RUNTIME-01 lifecycle:

```text
Windows sign-in
  -> Docker Desktop sign-in auto-start
  -> Docker Engine ready
  -> persisted Qdrant container returns under restart: unless-stopped
  -> Qdrant /readyz returns 200
```

Repository additions:

- `runtime/qdrant/windows/Invoke-PRuntime04Acceptance.ps1`
- `docs/operations/P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md`
- `tests/test_p_runtime_04_windows_login_autostart.py`

The harness is observer-only for login recovery. It does not issue Docker Desktop/Qdrant start or reconcile commands during `VerifyAfterLogin`.

## Safety properties

```text
Docker Desktop lifecycle owner        = Docker Desktop / external operator setting
Qdrant lifecycle owner                = Docker Engine restart policy
SGOKB automatic start/restart action  = none
Docker settings-store mutation        = none
Task Scheduler / service wrapper      = none
Startup-folder launcher               = none
accepted restart policy               = unless-stopped
accepted readiness authority          = /readyz
```

The only intentionally disruptive action in the harness is `docker kill` in `ExerciseUnexpectedStop`. It is a formal recovery test, not a runtime supervisor. PASS requires Docker to recover the same container through its existing restart policy without a start command from the harness.

## Hosted Windows implementation verification

Temporary workflow:

```text
.github/workflows/p-runtime-04-implementation.yml
```

### Attempt 1 — harness syntax defect

GitHub Actions run:

```text
run = 41071478644 (#1)
```

The run stopped at the PowerShell parser gate. The defect was limited to one interpolated error string using `$exitCode:`; PowerShell interpreted the colon as part of a drive-qualified variable reference. It was corrected to `${exitCode}:`.

No runtime lifecycle contract or product behavior was changed by the remediation.

### Attempt 2 — implementation gate PASS

Final implementation gate:

```text
GitHub Actions run          = 41071898853 (#2)
runner                      = Microsoft Windows Server 2025
Python                      = 3.10.11
PowerShell                  = 7.6.7
verified branch source      = 726aaa2e71a578a7c6c672b6cbf969da1bac35d5
verified synthetic PR merge = 38188211976077ba60e56edda3d06d2a4db05539
PowerShell syntax           = PASS
focused P-RUNTIME-02/03/04  = 10 / 10 PASS
Ruff src/tests              = PASS
full repository regression  = 859 / 859 PASS
warnings                    = 2 known local-Qdrant warnings
```

The full repository regression completed in 608.93 seconds. The two warnings are the unchanged local-Qdrant warnings about local payload indexes and exact/brute-force search parameters.

This verifies the repository implementation and regression boundary. It does **not** substitute for a persistent Windows 11 reboot/login lifecycle.

## Formal physical acceptance still required

Hosted CI can verify script syntax, static safety contracts, Compose invariants, and repository regressions, but it cannot prove the task completion condition because GitHub-hosted Windows runners do not represent the user's persistent Windows 11 + Docker Desktop login lifecycle.

Formal acceptance requires a supported Windows 11 machine with Docker Desktop configured to start at sign-in.

Required sequence:

```powershell
pwsh -File .\runtime\qdrant\windows\Invoke-PRuntime04Acceptance.ps1 -Mode PrepareReboot -AsJson
# Restart Windows normally and sign in. Do not manually start Docker Desktop/Qdrant.
pwsh -File .\runtime\qdrant\windows\Invoke-PRuntime04Acceptance.ps1 -Mode VerifyAfterLogin -AsJson
pwsh -File .\runtime\qdrant\windows\Invoke-PRuntime04Acceptance.ps1 -Mode ExerciseUnexpectedStop -AsJson
```

The final acceptance record must include the post-login and unexpected-stop JSON outputs. Until that evidence exists:

```text
P-RUNTIME-04 = In Progress / physical acceptance pending
P-RUNTIME-05 = blocked by Phase P sequencing
PR #78       = open / not merge-ready for formal task closure
```

No `Complete / Accepted` claim is permitted from CI evidence alone.
