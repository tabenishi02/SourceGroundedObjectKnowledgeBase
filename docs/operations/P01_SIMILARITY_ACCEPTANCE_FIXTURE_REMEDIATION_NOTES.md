# P-01 Similarity Acceptance Fixture Remediation Notes

## Purpose

This note records operational findings discovered while remediating the P-01 same-class similarity acceptance fixture.

The immediate P-01 blocker was the absence of another accepted `class:character` Object. During creation of OBJ-D, a separate weakness was observed in Object Evidence Package candidate selection. This finding is **not** itself a P-01 similarity-engine defect and should be tracked independently from the similarity acceptance remediation.

## Observed Package selection weakness

When an Object has one or more `confirmed` Source/Object associations, Object Evidence retrieval assigns the `explicit_association` reason to Evidence from those Sources. In the observed OBJ-D run, confirmed-association Evidence received the same effective score contribution (`50`), leaving a large set of otherwise very different Evidence chunks tied at the same score.

With non-semantic Package selection, this can make the final ordering depend heavily on deterministic tie-breakers such as Evidence ID ordering rather than semantic usefulness. As a result, low-value chunks can consume Package budget before more useful Evidence.

Observed examples included chunks whose useful content was effectively limited to:

- `参考文献`
- `脚注`
- long theme-song / song-list material
- heading-only content such as `他作品`
- heading-only content such as `テーマソング`

At the same time, high-value Character Evidence existed in the same confirmed Sources, including overview, personality, background, family relationships, rivalry, training, abilities, and transformations.

## Why this matters

The behavior is operationally significant because Object Evidence Package selection is budget constrained. If low-value tied chunks are selected early, they can consume token / byte / item budget and reduce the amount of useful grounding material available to the external analysis step.

This can lower Package grounding quality even though:

- Source ingestion is correct,
- Source/Object association is correct,
- Evidence extraction is correct,
- retrieval returns a high-recall candidate set,
- Package selection remains formally within configured budget.

Therefore this is primarily a **selection-quality / ranking-quality issue**, not an ingestion, provenance, or similarity failure.

## Related observation: cross-Source high-recall retrieval

During the same remediation, Evidence from a previously existing Source was retrieved because it contained the target Object name. This is not inherently incorrect: Object Evidence retrieval is intentionally high recall and may find useful cross-Source Evidence even without an explicit association.

The correct decision criterion is the Evidence content, not whether the Source was one of the newly added OBJ-D Sources.

One retrieved Evidence item from the existing Son Goku Pixiv Encyclopedia Source was audited and excluded because it came from a `pixivに投稿された小説` section dominated by derivative-fiction listings, `キャラ崩壊`, `捏造`, independent settings, and incidental Vegeta mentions. It was unsuitable for factual Character grounding. The exclusion was therefore content-based, not Source-ID-based.

## Current operational workaround used for OBJ-D

For the P-01 fixture remediation, the following workaround is used without changing production selection semantics:

1. Keep normal high-recall Evidence retrieval.
2. Audit clearly suspicious retrieved Evidence manually.
3. Exclude individually justified low-quality Evidence when necessary.
4. Use `evidence search --mode semantic --semantic-runtime --object <OBJ-D> --association-status confirmed` to rank the confirmed-source Evidence with the frozen local semantic runtime.
5. Select a small, semantically useful set covering the Character's core aspects.
6. Pass those Evidence IDs to `package build` through repeated `--include-evidence` arguments so they are protected/manual-included in the Package build.
7. Keep normal Package budget checks and normal validation/review/import workflow.

This workaround is acceptance-fixture preparation only. It must not be interpreted as a change to the frozen production Package-selection contract.

## Important runtime distinction discovered

`evidence select --semantic` and `evidence search --semantic-runtime` do not currently use the same composition root.

- `evidence select --semantic` uses the environment-driven `embedder_from_env()` path and requires `SGOKB_EMBED_MODEL`.
- Search / Similarity acceptance uses the frozen local semantic runtime built from the configured SGOKB embedding profile.
- `package build` currently invokes Object Evidence retrieval with semantic selection disabled.

For acceptance work, a separate embedding profile should not be introduced merely to improve Package selection. The OBJ-D remediation therefore uses the existing frozen runtime only for read-side Evidence ranking, then freezes the selected Evidence through the supported manual-include Package path.

## Follow-up improvement task

After P-01 acceptance is complete, evaluate a dedicated remediation for Object Evidence Package selection quality. The investigation should at minimum consider:

- whether `explicit_association` should remain a dominant binary boost or be combined with stronger within-Source quality/ranking signals;
- whether source diversity should require a minimum content-quality threshold before forcing a Source representative;
- whether heading-only, reference, footnote, navigation, or other low-information chunks should be down-ranked or classified before Package selection;
- whether the Package Builder should support the same frozen semantic runtime used by canonical Search / Similarity;
- whether semantic selection should be deterministic and reproducible through the Package manifest;
- whether tie-breaking among equal association scores should prefer substantive content rather than Evidence ID order;
- whether tests should explicitly cover confirmed Sources containing both high-value and low-value Evidence chunks.

The remediation must preserve the existing high-recall retrieval principle: useful cross-Source Evidence must not be removed merely because it lacks an explicit Source/Object association.

## Acceptance classification

This finding does **not** change the current P-01 blocker classification.

- P-01 blocker: missing same-class accepted comparison Object / acceptance fixture deficiency.
- Package selection weakness: separate follow-up improvement discovered while preparing OBJ-D.
- Similarity engine: no failure established by this finding.
