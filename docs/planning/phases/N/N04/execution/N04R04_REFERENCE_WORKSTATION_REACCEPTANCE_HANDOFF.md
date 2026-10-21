# N-04R-04 Reference Workstation Re-Acceptance Handoff

更新日: 2026-10-22

- Parent: `N-04 [P0]`
- Previous: `N-04R-03 — Harness Reconstruction` — **Complete**
- Current task: `N-04R-04 — Reference Workstation Re-Acceptance`
- Repository authority: GitHub `main`

## 1. Read first

1. `docs/decisions/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION.md`
2. `docs/decisions/N04R03_KNOWLEDGE_ACCESS_HARNESS_FREEZE.md`
3. `docs/evaluation/N04_AI_USE_CASE_ACCEPTANCE.md`
4. `benchmark/n04-knowledge-access-cases-v1.json`
5. `benchmark/n04-knowledge-access-formal-harness-v1.json`
6. `benchmark/tools/n04r03_harness_preflight.py`
7. `benchmark/tools/n04r04_evaluate_evidence.py`
8. `docs/planning/phases/N/N04/N04_RESPONSIBILITY_BOUNDARY_RECONSTRUCTION_TASKS.md`

Historical G-12/G-22/G-25 assets are evidence only. Do not use them as current formal Gate.

## 2. Formal scope

Formal N-04 ends at:

```text
SGOKB → Retrieval / Similarity → Context Builder → MCP public read → Consumer boundary
```

Do not run or require:

```text
LLM generator
Atomicity classifier
Content-Type classifier
Source Fact verifier
Interpretation verifier
Grounded Generation v3/v4
Frozen 47
```

Reference Consumer Demonstration is optional and non-gating.

## 3. Mandatory preflight

On the Reference Workstation, from current clean `main`:

```powershell
python benchmark/tools/n04r03_harness_preflight.py
python -m pytest -q tests/test_n04r03_knowledge_access_harness.py tests/test_n04r04_evidence_evaluator.py tests/test_j04_context_builder.py tests/test_j06_mcp_client_acceptance.py
python -m pytest -q
python -m ruff check .
git diff --check
```

All must PASS before formal re-acceptance.

If a preflight failure is caused by the reconstructed Harness implementation, return to R-03 repair. Do not weaken the Gate.

## 4. Runtime inputs

Use:

```text
Evaluation DB: .local/n03/sgokb-n03.sqlite
N-04P-06 accepted semantic / Qdrant runtime
Transport: local MCP stdio
MCP contract: sgokb.mcp-read-tools.v1
Context contract: sgokb.context-builder.v1
```

Use the accepted J-06 MCP SDK v2 stdio composition and P-06 real-data derived-search configuration. Consumer-side direct SQLite reads are prohibited when creating case Context.

## 5. Evidence root

Create:

```text
.local/n04r04/<run_id>/
```

Use the file layout in `benchmark/n04-knowledge-access-formal-harness-v1.json`.

Before the first formal MCP case call, save:

```text
environment.json
mcp-tools.json
canonical-before.json
```

After all cases, save:

```text
canonical-after.json
integrity.json
regression.json
focused-pytest.log
full-pytest.log
```

`regression.json` must record exit codes for at least:

```json
{
  "return_codes": {
    "focused_pytest": 0,
    "full_pytest": 0,
    "ruff": 0,
    "diff_check": 0
  }
}
```

Canonical before / after must cover Object IDs, current Version IDs, accepted Knowledge, Facet / Statement / Attribute / Relation, Source / Snapshot / Evidence, Statement-Evidence grounding, and provenance. Use the same deterministic snapshot procedure before and after so exact JSON equality is meaningful.

## 6. Case 1 — Saber / roleplay boundary

Call only the public MCP Tool:

```json
{
  "tool": "build_context",
  "arguments": {
    "object_ids": ["326a97cf-47aa-4760-a7f1-07bfe639fcf0"],
    "purpose": "roleplay",
    "max_characters": 12000,
    "include_attributes": true,
    "include_relations": true,
    "include_evidence_refs": false
  }
}
```

Save request / raw Context under `case-1-roleplay/`.

Required:

- public boundary
- Saber stable ID
- current accepted resolved Version
- purpose `roleplay`
- requested include options preserved
- valid Context contract
- used characters within budget
- omission / truncation semantics valid
- version traceability
- Evidence refs omitted from Consumer Context

Do not score a Roleplay answer.

## 7. Case 2 — Similar Work / comparison boundary

First call:

```json
{
  "tool": "find_similar_objects",
  "arguments": {
    "object_id": "d5824d33-7008-4121-9cfe-1f95a19667fd",
    "cross_class": false,
    "include_archived": false,
    "limit": 5
  }
}
```

Select the highest-ranked returned **current Work** candidate from the actual response.

Then call `build_context` with:

```text
object_ids = [Fate/stay night ID, actual returned candidate ID]
purpose = comparison
max_characters = 24000
include_attributes = true
include_relations = false
include_evidence_refs = true
```

Do not replace the returned candidate with the known BLEACH ID. BLEACH may be recorded as an observation if it is actually returned.

Required:

- actual Similarity public path
- top returned candidate present
- returned candidate ID is exactly the ID used for Context
- candidate resolves as current through the Context path
- both current Work Versions in Context
- Evidence refs preserved through public contract
- budget / traceability PASS

Do not score semantic ranking quality; that belongs to N-06.

## 8. Case 3 — Concept combination / creative boundary

Call:

```json
{
  "tool": "build_context",
  "arguments": {
    "object_ids": [
      "8c83f986-f491-41a8-8645-9f71dd5874b9",
      "fee32007-0f92-449a-ba21-4ec2f78d1cd4"
    ],
    "purpose": "creative",
    "max_characters": 24000,
    "include_attributes": true,
    "include_relations": true,
    "include_evidence_refs": false
  }
}
```

Required:

- both stable Concept IDs
- both current accepted Versions
- purpose `creative`
- requested include options preserved
- both Object boundaries visible in Context
- valid budget / traceability
- Evidence refs omitted from Consumer Context

Do not score generated Character quality or creative labeling.

## 9. Deterministic formal evaluation

After the required evidence and regression metadata are saved, run:

```powershell
python benchmark/tools/n04r04_evaluate_evidence.py `
  --run-root .local/n04r04/<run_id>
```

This writes:

```text
overall-evaluation.json
```

Exit code:

```text
0 = PASS
1 = FAIL
2 = BLOCKED
```

The evaluator reads only SGOKB boundary evidence. It does not read or score Consumer AI output.

For audit readability, copy each case's relevant subset from `overall-evaluation.json` to the corresponding `evaluation.json`, or generate equivalent case evaluation files without changing the formal verdict.

## 10. Formal result

Each case:

```text
PASS / FAIL / BLOCKED
```

Overall PASS only if all 3 cases and all global Gates PASS.

`FAIL` must identify an SGOKB responsibility defect. A Consumer model failure is not a formal N-04 failure.

Missing/unreadable formal evidence is `BLOCKED`, because no SGOKB defect has been established.

## 11. Completion action

If formal result is PASS:

```text
N-04R-04 = Complete
N-04 = Complete
```

Then continue to N-04R-05 only for Grounded Generation asset disposition; R-05 must not reopen the N-04 acceptance result unless it discovers an actual SGOKB Knowledge Access defect.

If FAIL:

- preserve evidence;
- classify the exact SGOKB boundary defect;
- do not reintroduce Consumer generation Gates.

If BLOCKED:

- preserve evidence;
- repair only the unavailable required SGOKB runtime / environment / evidence procedure;
- do not treat BLOCKED as model-quality failure.
