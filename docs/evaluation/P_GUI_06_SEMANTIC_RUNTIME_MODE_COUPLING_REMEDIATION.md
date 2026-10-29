# P-GUI-06 — Semantic Runtime / Search Mode Coupling Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Trigger: interactive Search smoke after Attempt 08
- Status: **Implemented / Automated Verification Refresh Pending / Interactive Re-smoke Pending**

## Interactive symptom

The operator reported:

```text
mode=semantic
Search failed: [runtime/retrieval_runtime_unavailable]
Semantic search requires an EmbeddingProvider and VectorIndexAdapter

mode=hybrid
Degraded channels: semantic:RuntimeError
```

## Root cause

The GUI exposed Search mode and `Semantic runtime` as independent controls.

Before this remediation, `run_search()` transported:

```text
mode             = selected mode
semantic_runtime = checkbox state
```

This admitted contradictory requests such as:

```text
mode=semantic
semantic_runtime=false
```

The transport-neutral operator behaved correctly: `semantic_runtime=false` builds `KnowledgeReadApplication` without an EmbeddingProvider or VectorIndexAdapter. Pure Semantic Search then fails because those dependencies are mandatory, while Hybrid Search can degrade to its lexical channels.

Therefore the observed error did not demonstrate a failed Harrier/Qdrant construction. It demonstrated a GUI operator-contract defect: choosing Semantic did not itself request the Semantic runtime.

## Remediation

The GUI now couples Search mode and Semantic runtime explicitly.

```text
Lexical
  semantic runtime = OFF / disabled
  require full runtime = OFF / disabled

Semantic
  semantic runtime = ON / disabled
  require full runtime = OFF / disabled
  pure Semantic already fails explicitly when runtime is unavailable

Hybrid
  semantic runtime = ON by default
  operator may explicitly opt out for deliberate lexical-only degradation
  require full runtime is available only while semantic runtime is enabled
```

`run_search()` also enforces the contract defensively:

```text
mode=semantic -> semantic_runtime=true
mode=lexical  -> semantic_runtime=false
mode=hybrid   -> semantic_runtime=<Hybrid checkbox state>
```

Thus a programmatic UI desynchronization cannot send a pure Semantic request without the runtime.

## Scope boundary

This is a GUI contract correction only.

Unchanged:

- CLI explicit `--semantic-runtime` behavior;
- `RuntimeFactory` composition;
- Harrier EmbeddingProvider;
- Qdrant VectorIndexAdapter;
- local-only / no-cloud-fallback policy;
- main-thread native dependency preload;
- Hybrid degraded-channel semantics when the operator deliberately disables the Semantic runtime or the runtime actually fails.

## Regression coverage

`tests/test_p_gui_06_search_runtime_state.py` now verifies:

1. Hybrid default requests `semantic_runtime=True`;
2. Lexical forces runtime OFF;
3. Semantic forces runtime ON;
4. pure Semantic request construction remains ON even after programmatic checkbox desynchronization;
5. Hybrid explicit opt-out remains supported and disables `require_full_runtime`.

## Verification authority

Attempt 08 remains historical evidence for the From/To-removal baseline:

```text
focused = 28 / 28 PASS
Ruff    = PASS
full    = 817 / 817 PASS
```

Because GUI Search request construction changed after Attempt 08, those counts are not current closure authority.

Current disposition:

```text
semantic/runtime GUI contract = corrected
automated verification        = refresh pending
interactive Semantic re-smoke = pending
interactive Hybrid re-smoke   = pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
