# P-01 Similarity Acceptance Fixture Remediation Notes

## Purpose

This note records the P-01 same-class similarity acceptance-fixture remediation and the separate Object Evidence Package selection-quality finding discovered while preparing that fixture.

The original P-01 blocker was the absence of another accepted `class:character` Object. P-01 default similarity is intentionally same-primary-class (`cross_class = false`), so the original acceptance dataset containing only OBJ-A / `character`, OBJ-B / `work`, and OBJ-C / `concept` could not satisfy the P-01 PASS condition without weakening the test to cross-class similarity.

The remediation preserved the production similarity contract: a second accepted Character Object was created through the normal production workflow and synchronized into the configured semantic runtime/index.

## P-01 fixture remediation

The added same-class fixture is:

- OBJ-D: `ベジータ(ドラゴンボール)`
- Object ID: `8655f9ac-af89-48d7-afc1-56ed4f9cffb9`
- Primary Class: `class:character`
- Accepted Knowledge V1: `eee8745b-c2a0-4dbb-9e44-9e082917676e`

OBJ-D was not inserted by direct SQLite mutation. It went through the normal workflow:

1. Object Registry creation.
2. Source import / process.
3. confirmed Source/Object association.
4. Evidence retrieval and selection.
5. Object Evidence Package build / stage / preflight / export.
6. external structured analysis under the Package `instructions.md` and schema.
7. Result detect / receive / validate / human review.
8. explicit Result Import with required review acknowledgement.
9. current accepted Knowledge verification.
10. semantic derived synchronization through the frozen local Embedding runtime and Qdrant.

The accepted OBJ-D V1 derived sync completed with:

- 37 Search Representations,
- 37 newly created embeddings,
- 37 Qdrant vector points,
- all stages `ready`,
- no SGOKB warnings.

The unauthenticated Hugging Face Hub message observed during local model loading is a rate-limit / download-speed warning and was not an acceptance failure.

## P-01 rerun result

After OBJ-D became current accepted Knowledge and its semantic derived state was synchronized, the original P-01 command was rerun without `--cross-class`:

```powershell
sgokb --db $Db similar --object $ObjectAId --limit 10
```

Observed result:

- source: OBJ-A `孫悟空(ドラゴンボール)` / `character`
- `cross_class = false`
- rank 1: OBJ-D `ベジータ(ドラゴンボール)` / `character`
- cosine similarity: `0.7640100717544556`
- warnings: none

Therefore the original P-01 fixture blocker is resolved without weakening same-class similarity semantics.

Formal classification:

```text
P01-R01 Remediation : COMPLETE / PASS
P-01 Object similarity : PASS after remediation
```

## Section P follow-on results

The same remediated fixture also supported the remaining Similarity acceptance checks:

- P-02 Facet-specific similarity: PASS using Facet key `relationships`; OBJ-D returned rank 1 with `matched_facet = relationships`, score `0.79454505443573`.
- P-04 Current / historical similarity: PASS; default scope resolved OBJ-A V2 `ca4741fd-1a50-4ffb-b318-bf097b2dc5be`, while explicit `--version` resolved historical OBJ-A V1 `b21556b2-ffb6-4baa-82e4-dc9a34d4bceb`.
- P-05 Cross-class similarity: PASS; cross-class ranking returned OBJ-B `ドラゴンボール` / `work` rank 1 (`0.796532392501831`), OBJ-D / `character` rank 2 (`0.7640100717544556`), and OBJ-C `ツンデレ` / `concept` rank 3 (`0.5426591634750366`).
- Human sanity review: PASS; the observed ordering was operationally plausible for this intentionally small acceptance dataset.

The acceptance procedure is updated separately so that:

- P-01 explicitly requires a same-primary-class current accepted comparison Object and must not be satisfied by adding `--cross-class`;
- P-02 names the CLI argument as a Facet **key**, not a generic Facet ref;
- P-03 evaluates the same-class P-01/P-02 ranking against the known same-class fixture;
- P-05 owns cross-class ranking and its OBJ-B/OBJ-C sanity check.

Section P can therefore be recorded as:

```text
Section P Similarity : COMPLETE / PASS after remediation
```

## Observed Package selection weakness

During creation of OBJ-D, a separate weakness was observed in Object Evidence Package candidate selection. This finding is **not** itself a P-01 similarity-engine defect and remains a follow-up item independent of the completed similarity acceptance remediation.

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

For the completed P-01 fixture remediation, the following workaround was used without changing production selection semantics:

1. Keep normal high-recall Evidence retrieval.
2. Audit clearly suspicious retrieved Evidence manually.
3. Exclude individually justified low-quality Evidence when necessary.
4. Use `evidence search --mode semantic --semantic-runtime --object <OBJ-D> --association-status confirmed` to rank the confirmed-source Evidence with the frozen local semantic runtime.
5. Select a small, semantically useful set covering the Character's core aspects.
6. Pass those Evidence IDs to `package build` through repeated `--include-evidence` arguments so they are protected/manual-included in the Package build.
7. Keep normal Package budget checks and normal validation/review/import workflow.

This workaround was acceptance-fixture preparation only. It must not be interpreted as a change to the frozen production Package-selection contract.

## Important runtime distinction discovered

`evidence select --semantic` and `evidence search --semantic-runtime` do not currently use the same composition root.

- `evidence select --semantic` uses the environment-driven `embedder_from_env()` path and requires `SGOKB_EMBED_MODEL`.
- Search / Similarity acceptance uses the frozen local semantic runtime built from the configured SGOKB embedding profile.
- `package build` currently invokes Object Evidence retrieval with semantic selection disabled.

For acceptance work, a separate embedding profile should not be introduced merely to improve Package selection. The OBJ-D remediation therefore used the existing frozen runtime only for read-side Evidence ranking, then froze the selected Evidence through the supported manual-include Package path.

## Follow-up improvement task

Evaluate a dedicated remediation for Object Evidence Package selection quality. The investigation should at minimum consider:

- whether `explicit_association` should remain a dominant binary boost or be combined with stronger within-Source quality/ranking signals;
- whether source diversity should require a minimum content-quality threshold before forcing a Source representative;
- whether heading-only, reference, footnote, navigation, or other low-information chunks should be down-ranked or classified before Package selection;
- whether the Package Builder should support the same frozen semantic runtime used by canonical Search / Similarity;
- whether semantic selection should be deterministic and reproducible through the Package manifest;
- whether tie-breaking among equal association scores should prefer substantive content rather than Evidence ID order;
- whether tests should explicitly cover confirmed Sources containing both high-value and low-value Evidence chunks.

The remediation must preserve the existing high-recall retrieval principle: useful cross-Source Evidence must not be removed merely because it lacks an explicit Source/Object association.

## Final acceptance classification

- P-01 blocker: **resolved** by adding a same-class accepted comparison Object through the normal workflow.
- P01-R01 remediation: **COMPLETE / PASS**.
- P-01 Object similarity: **PASS after remediation**.
- Section P Similarity: **COMPLETE / PASS after remediation**.
- Package selection weakness: **separate follow-up improvement; unresolved by design in this remediation**.
- Similarity engine: **no failure established**.
