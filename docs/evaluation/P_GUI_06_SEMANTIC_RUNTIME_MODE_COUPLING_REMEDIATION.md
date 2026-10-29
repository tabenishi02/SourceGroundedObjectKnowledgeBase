# P-GUI-06 — Semantic Runtime / Search Mode Coupling Remediation

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Trigger: interactive Search smoke after Attempt 08
- Status: **Implemented / Automated Verification PASS / Interactive Re-smoke Pending**
- Current automated authority: `docs/evaluation/P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`

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

`tests/test_p_gui_06_search_runtime_state.py` verifies:

1. Hybrid default requests `semantic_runtime=True`;
2. Lexical forces runtime OFF;
3. Semantic forces runtime ON;
4. pure Semantic request construction remains ON even after programmatic checkbox desynchronization;
5. Hybrid explicit opt-out remains supported and disables `require_full_runtime`.

## Verification authority

Attempt 09 is the current automated authority:

```text
focused = 29 / 29 PASS
Ruff    = PASS
full    = 818 / 818 PASS
warnings = 2 known local-Qdrant warnings
```

Attempt 08 remains historical evidence for the From/To-removal baseline and predates this remediation.

Current disposition:

```text
semantic/runtime GUI contract = corrected
automated verification        = PASS
interactive Semantic re-smoke = pending
interactive Hybrid re-smoke   = pending
```

Therefore:

```text
P-GUI-06 = Automated Verification PASS / Interactive Smoke Pending
```
