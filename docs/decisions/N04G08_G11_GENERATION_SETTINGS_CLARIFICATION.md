# N-04G-08 / G-11 Generation Settings Clarification

更新日: 2026-10-18

- Status: **Accepted / Binding clarification**
- Applies to: `docs/decisions/N04G08_N04_V2_ACCEPTANCE_SPEC_FREEZE.md`
- Machine spec: `benchmark/n04-ai-use-cases-v2.json`
- Formal harness: `benchmark/n04-v2-formal-harness-v1.json`
- Reason: G-11 formal harness consistency review

## Clarification

G-08 prose and the v2 machine spec contain wording that can be read as requiring identical `temperature` / `max_tokens` across all three cases. However, the same frozen v2 machine spec explicitly defines different case-specific values:

```text
Case 1: temperature=0.2 / max_tokens=700
Case 2: temperature=0.0 / max_tokens=900
Case 3: temperature=0.2 / max_tokens=1100
```

The case-specific numeric values are normative. The phrase "same generation settings" is therefore clarified as follows.

1. One generator model / runtime / endpoint / quantization / context-load profile is frozen across all three cases.
2. Each case uses the `temperature` / `max_tokens` values already frozen in `benchmark/n04-ai-use-cases-v2.json`.
3. Within a case, Attempt 1 and Attempt 2 must use exactly the same inference settings, including `temperature`, `max_tokens`, and seed policy.
4. Case results must not be used to make ad-hoc parameter changes.
5. Retry may add only structured validation feedback, per G-06/G-07.

## Why G-07 is not reopened

G-07 freezes generation settings across the retry boundary for one grounded-generation run. It does not require the three different benchmark use cases to share identical `temperature` / `max_tokens` values.

This clarification therefore resolves an acceptance-spec wording conflict without changing:

- claim taxonomy,
- Grounded Context semantics,
- generation output contract,
- validation semantics,
- retry count,
- retry invariants,
- case identity,
- case-specific numeric generation parameters,
- PASS / FAIL rubric,
- critical failure criteria.

## Formal interpretation

For N-04G-12, `benchmark/n04-v2-formal-harness-v1.json` is the normative operational interpretation of this point.
