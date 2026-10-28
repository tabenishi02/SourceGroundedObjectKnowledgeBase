# SGOKB Releases

This directory stores repository-side Release Notes for Source Grounded Object Knowledge Base.

## Current release line

```text
Prototype 0.2.x = Archived / Legacy historical line
SGOKB 1.x       = Current formal release line
```

Prototype 0.2 does not receive a retroactive Git tag or GitHub Release. Its historical authority remains `docs/archive/prototype-0.2/` and Git history.

## Releases

| Version | Tag | Status | Notes |
|---|---|---|---|
| `1.1.0` | `v1.1.0` | Published tag verified / GitHub Release published | [Release Note](v1.1.0.md) |
| `1.0.0` | `v1.0.0` | Published tag verified | [Release Note](v1.0.0.md) |

`v1.0.0` is an annotated tag whose tag object is `a418096b5139027cd9ccaaf47fb99a4309cb4b1e` and whose target commit is `0e1a8464e9db98b4e99169cae6292821f3fd410c`.

`v1.1.0` is an annotated tag whose tag object is `fc764cdc497637bfa8fa03f262903959e579267b` and whose target commit is `7e56080fc63e711e276d8b97d29a88aa9da0a455`.

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
