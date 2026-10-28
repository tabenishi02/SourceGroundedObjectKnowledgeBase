# SGOKB Happy-Path Operational Acceptance — Final Result

Status: **FULL SGOKB PASS**  
Date: **2026-10-28**  
Scope: SGOKB v1.0.0 current accepted architecture / manual happy-path operational acceptance

This document records the completed acceptance run defined by:

- `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PLAN.md`
- `docs/operations/SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md`

The run completed the normal operator workflow without direct SQLite manipulation or acceptance-boundary bypass.

## Final verdict

```text
T-01 Full normal operational chain = COMPLETE / PASS
Core SGOKB Acceptance             = PASS
Full SGOKB Acceptance             = PASS
Overall                           = FULL SGOKB PASS
```

All applicable sections A-T passed. Section P completed as **PASS after remediation** using a valid same-primary-class similarity fixture created through the normal production workflow.

## Execution identity

Operator-reported execution repository identity:

```text
HEAD:         5eba4629b12cc071dab33d04faa7521a361d6977
git describe: v1.0.0-22-g5eba462
worktree:     clean
```

Acceptance DB:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\sgokb-happy-path.sqlite
```

The acceptance DB is an isolated test DB and is not the production DB.

## Semantic runtime identity

```text
Provider:             sentence-transformers
Model:                microsoft/harrier-oss-v1-0.6b
Revision:             f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
Embedding dimension:  1024
Embedding Space ID:   832920052e1d1a6d3bbe2a5ef9d3b0d09785b0e0f26bf3081b8728de2897d591
Qdrant:               1.19.2
Qdrant HTTP:          127.0.0.1:6333
Qdrant gRPC:          127.0.0.1:6334
```

The recurring Hugging Face unauthenticated-request warning was non-fatal. Semantic commands completed successfully with no SGOKB degradation warnings.

## Acceptance dataset identities

Main established objects used across A-S:

| Logical fixture | Object | Object ID | Current accepted Version |
|---|---|---|---|
| OBJ-A | 孫悟空(ドラゴンボール) | `96e987d4-8f71-4f6d-887d-9d63b44df48e` | `ca4741fd-1a50-4ffb-b318-bf097b2dc5be` |
| OBJ-B | ドラゴンボール | `5c07e8c8-1298-402f-b750-2d8b58fb9fad` | `d2e8d178-4439-43b7-8368-bb562247a394` |
| OBJ-C | ツンデレ | `c02d3ed1-1844-419b-a74b-893671a2a141` | `7bc55d1b-e511-427c-861f-dd552ef25e56` |
| OBJ-D | ベジータ(ドラゴンボール) | `8655f9ac-af89-48d7-afc1-56ed4f9cffb9` | `eee8745b-c2a0-4dbb-9e44-9e082917676e` |

OBJ-D was added through the normal workflow to remediate the original P-01 fixture deficiency and provide a valid same-primary-class similarity candidate.

## T-01 fresh end-to-end object

T-01 used a new Object and a new capture bundle rather than reusing only the earlier fixtures.

```text
Object name:        フリーザ
Object ID:          ca96ae90-3ff6-4c62-83ea-7d1d7c41439a
Primary Class:      character
Accepted Version:   7d7b594b-aea7-45e6-95c5-5f388503568c
```

Fresh capture:

```text
20261028T061026466Z_95676ff1-bad1-4570-ae98-5e5432989500.webcapture.zip
```

Source chain:

```text
Source ID:       ea6f3526-87ca-48a8-b8f3-222636517d55
Snapshot ID:     95676ff1-bad1-4570-ae98-5e5432989500
Process Run ID:  6e539e83-cc45-4d6a-bcb7-9e045f30b2d5
Processed:       134 blocks / 89 evidence items
```

The Source was associated with the T Object using `status=confirmed` before Evidence selection.

## T-01 Evidence Package / Result identity chain

Evidence selection:

```text
Candidates:             334
Selected:               8
Omitted:                326
Estimated token usage:  11678 / 12000
Bytes:                  39443 / 65536
Items:                  8 / 64
Sources represented:    7
```

Package:

```text
Package ID:       pkg_c48cc2ef-7333-44af-91d3-e700e7fff0ef
Manifest SHA-256: 8c65fba61743872969d2045d930da16249c97f4d0c641f76ac1522d0aa9b1be9
Evidence count:   8
Source generations: 7
Base Version:     none
```

Package preflight returned `allow` with no reasons, warnings, or credential findings. Export was explicit and recorded by audit event `3694e33a-7d83-473e-b9ef-c6b6e0ad6064`.

External ChatGPT analysis used the exported Package and `instructions.md` as the authoritative analysis instruction. The returned Structured Object Result was saved exactly as `result.json` before SGOKB intake.

Result chain:

```text
Result SHA-256: 3e16f6300a7d350ca046de4c1f6e8ac7790dd5983dd38cce943a1c48c088120e
Receipt ID:     0a6d27c6-2c60-497c-bf9f-f3a5ec4a3baa
Import ID:      caa40fc5-8d12-43d4-bbbc-c90ccfa39820
Version ID:     7d7b594b-aea7-45e6-95c5-5f388503568c
```

The Result passed `detect -> receive -> validate -> review -> explicit import` in order. Validation completed with no findings. Review reported `ready_to_import`, no blocking reasons, no destructive omissions, 3 summary additions, 11 facet additions, and no Attribute or Relation changes.

The Result contained no Registry Proposal, so T-01 step 19 was **not applicable / satisfied**. It also contained no supported Relation to apply, so T-01 step 21 was **not applicable / satisfied**. No proposal or Relation was fabricated merely to satisfy the test sequence.

## T-01 read-surface consistency

After import, `object show --knowledge` resolved the T Object to:

```text
Object ID:            ca96ae90-3ff6-4c62-83ea-7d1d7c41439a
Resolved Version ID:  7d7b594b-aea7-45e6-95c5-5f388503568c
is_current:           true
version_number:       1
```

Render:

```text
renderer_version:     1.0
byte_count:           19077
sha256:               e870fd1bc65d9f29fb66040b4c10e252b9013702859471585a5d67a125b148be
derived_state_update: ready
```

Lexical read after non-semantic derived sync:

```text
Query:      ゴールデンフリーザ
Rank 1:     フリーザ
Object ID:  ca96ae90-3ff6-4c62-83ea-7d1d7c41439a
Version ID: 7d7b594b-aea7-45e6-95c5-5f388503568c
```

Semantic read after semantic-runtime derived sync:

```text
Query: 不老不死を求めてナメック星でドラゴンボールを集め、悟空と戦った宇宙の強敵
Rank 1: フリーザ
Object ID:  ca96ae90-3ff6-4c62-83ea-7d1d7c41439a
Version ID: 7d7b594b-aea7-45e6-95c5-5f388503568c
Degraded channels: none
```

Hybrid read with full runtime also returned フリーザ at rank 1 with the same current Version and no degraded channel.

Similarity used the default same-primary-class contract (`cross_class=false`):

| Rank | Object | Score |
|---|---|---:|
| 1 | ベジータ(ドラゴンボール) | 0.7779713869 |
| 2 | 孫悟空(ドラゴンボール) | 0.7161518335 |

The source Object itself was excluded from candidates.

## MCP read boundary

The acceptance MCP server was configured against the acceptance DB. The three T-01 MCP operations passed:

```text
get_object     = PASS
search_objects = PASS
build_context  = PASS
```

`get_object` and `build_context` both resolved to Version `7d7b594b-aea7-45e6-95c5-5f388503568c`.

`search_objects` used the same semantic query and returned フリーザ at rank 1 with the same Object/Version identity.

`build_context` reported:

```text
purpose:          general
max_characters:   12000
used_characters:  4232
truncated:        false
omitted_items:    0
warnings:         none
```

This confirms consistency across CLI lexical/semantic/hybrid/similarity, render, and MCP read surfaces for the T Object/current Version.

## Backup and final integrity

T-01 backup created after the completed workflow:

```text
C:\codex\SourceGroundedObjectKnowledgeBase\.local\acceptance\backups\sgokb-20261028T065846Z.sqlite
byte_count: 20332544
integrity:  ok
exists:     true
```

Final `system integrity`:

```text
ok:                     true
sqlite_integrity:       [ok]
foreign_key_violations: []
warnings:               []
```

## Section verdicts

| Section | Verdict |
|---|---|
| A — Environment / CLI | PASS |
| B — Object Registry | PASS |
| C — Source / Snapshot / Raw | PASS |
| D — Association | PASS |
| E — Evidence / Provenance | PASS |
| F — Evidence Package | PASS |
| G — External semantic integration | PASS |
| H — Result intake / validation / review / import | PASS |
| I — Registry Proposal | PASS |
| J — Versioning | PASS |
| K — Relation | PASS |
| L — Render | PASS |
| M — Lexical Search | PASS |
| N — Semantic Search | PASS |
| O — Hybrid Search | PASS |
| P — Similarity | PASS after remediation |
| Q — MCP Read Boundary | PASS |
| R — Derived Index | PASS |
| S — Backup / Restore Happy Path | PASS |
| T — Final uninterrupted end-to-end run | PASS |

## Acceptance conclusion

The acceptance criteria defined by the current happy-path procedure are satisfied:

- normal operator workflow completed without manual canonical SQLite edits;
- explicit export and external Package-based semantic integration completed;
- Result validation and human review preceded explicit import;
- no Registry Proposal was silently applied;
- accepted Knowledge remained Versioned;
- Knowledge lexical read followed Search Representation derived sync;
- semantic/hybrid/similarity reads followed configured semantic derived sync;
- Evidence/raw lineage remained available through the tested workflow;
- lexical, semantic, hybrid, similarity, render, and MCP surfaces resolved consistently to the same canonical Object/current Version semantics;
- completed workflow backup creation succeeded;
- final system integrity succeeded.

Therefore the formal happy-path operational acceptance verdict is:

> **Source Grounded Object Knowledge Base — FULL SGOKB PASS**

## Scope note

This result is a normal/happy-path operational acceptance result. It does not replace the separate Phase N failure/recovery, adversarial, performance, ANN-quality, or production-scale evaluation records. Historical FAIL/BLOCKED evidence remains valid historical evidence and is not overwritten by this result.
