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
| `1.0.0` | `v1.0.0` | Tag publication pending | [Release Note](v1.0.0.md) |

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
