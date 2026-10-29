# P-GUI-06 — Final Interactive Acceptance

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Complete / Accepted**
- Automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_09.md`

## Acceptance evidence

Automated verification after the final Search mode / Semantic runtime coupling remediation:

```text
focused regression = 29 / 29 PASS
Ruff               = PASS
full regression    = 818 / 818 PASS
warnings           = 2 known local-Qdrant warnings
```

Interactive verification then confirmed that the previously reported Search failures were resolved.

The operator confirmed:

```text
Semantic Search issue = resolved
Hybrid Search issue   = resolved
checked GUI functions = no problems in the verified scope
```

The interactive acceptance is intentionally scoped to the functions exercised during the P-GUI-06 smoke sequence. It does not claim exhaustive manual coverage beyond that checked scope; broader regression coverage is provided by Attempt 09.

## Accepted final Search behavior

```text
Lexical
  Semantic runtime = OFF / disabled

Semantic
  Semantic runtime = ON / disabled
  runtime is requested automatically

Hybrid
  Semantic runtime = ON by default
  explicit operator opt-out remains available
```

The experimental From/To date range filter remains removed from the GUI. Canonical temporal-scope data and the existing non-GUI single-point `valid_at` / `knowledge_valid_at` contract remain unchanged.

The GUI main-thread native preload remediation remains active, and the previously observed process crash is no longer reproduced in the accepted smoke path.

## Final disposition

```text
operation wiring                        = 14 / 14
automated verification                  = PASS
interactive smoke                       = PASS
From/To GUI range filter                = Removed by operator decision
semantic native preload                 = Accepted
Search mode / Semantic runtime coupling = Accepted
```

Therefore:

```text
P-GUI-06 = Complete / Accepted
```

Next task:

```text
P-GUI-07 — Progress / error / safety / audit UX
```
