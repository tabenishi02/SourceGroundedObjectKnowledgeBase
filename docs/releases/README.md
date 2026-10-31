# SGOKB Releases

This directory stores repository-side Release Notes for Source Grounded Object Knowledge Base.

## Current release state

```text
Prototype 0.2.x = Archived / Legacy historical line
SGOKB 1.x       = Current published release line
SGOKB 2.0.0     = Phase P release candidate / tag pending P-CLOSE-01
```

Prototype 0.2 does not receive a retroactive Git tag or GitHub Release. Its historical authority remains `docs/archive/prototype-0.2/` and Git history.

## Releases

| Version | Tag | Status | Notes |
|---|---|---|---|
| `2.0.0` | pending | P-CLOSE-01 release candidate; final regression/main freeze pending | [Release Note](v2.0.0.md) |
| `1.1.0` | `v1.1.0` | Published tag verified / GitHub Release published | [Release Note](v1.1.0.md) |
| `1.0.0` | `v1.0.0` | Published tag verified | [Release Note](v1.0.0.md) |

`v1.0.0` is an annotated tag whose tag object is `a418096b5139027cd9ccaaf47fb99a4309cb4b1e` and whose target commit is `0e1a8464e9db98b4e99169cae6292821f3fd410c`.

`v1.1.0` is an annotated tag whose tag object is `fc764cdc497637bfa8fa03f262903959e579267b` and whose target commit is `7e56080fc63e711e276d8b97d29a88aa9da0a455`.

## 2.0.0 release boundary

`2.0.0` is a MAJOR release candidate because the no-option Package build changes from legacy Package v1 semantics to Raw-grounded Package v2 / Result v2 semantics. Explicit `--package-version v1` compatibility remains available.

The source/repository release includes the PySide6 GUI implementation but does not certify/publish a standalone GUI binary artifact; project-license selection and artifact-specific Qt/PySide6 redistribution auditing remain separate gates.

Formal `v2.0.0` tagging is allowed only after `docs/evaluation/P_CLOSE_01_PHASE_P_CLOSURE_ACCEPTANCE.md` is closed on merged `main`.

## Policy

Release / Tag / Breaking Change policy is defined in:

- `docs/decisions/O06_RELEASE_TAG_AND_BREAKING_CHANGE_POLICY.md`

Rules in brief:

- Semantic Versioning is used.
- Formal tags use `vMAJOR.MINOR.PATCH`.
- package version equals tag without the leading `v`.
- published tags are immutable and are not silently moved or reused.
- Task / Phase completion does not create a tag by itself.
- Breaking Changes and migration guidance are recorded in the repository-side Release Note.
- GitHub Release text must preserve the same material compatibility information as the repository-side note.
