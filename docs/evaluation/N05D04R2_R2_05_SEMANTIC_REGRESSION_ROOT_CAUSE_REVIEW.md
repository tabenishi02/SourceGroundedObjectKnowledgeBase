# N05D-04R2 / R2-05 — Semantic Regression Root-Cause / Remediation Review

Updated: 2026-10-24

Status: **Local causal proof and bounded ablation complete / R2-05 Semantic remediation verified**

Scope: the R2-08 Object Semantic Search regression only. The two Overall Object
Similarity regressions belong to R2-06 and are intentionally out of scope here.
R2-09 remains prohibited.

## 1. Trigger

R2-08 Reference Workstation acceptance returned **FAIL / Not Complete** although
the automatic gate passed. The fixed runtime was:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
runtime: CUDA / bfloat16
dimension: 1024
truncation: none
```

Object Semantic Search changed from the accepted Phase-I observation:

```text
MRR       1.000000 -> 0.972222
Recall@1  0.854167 -> 0.812500
nDCG@10   0.993083 -> 0.972250
Recall@10 1.000000 -> 1.000000
```

The case-level failure is:

```text
case: short_japanese_love
query: 愛
expected: obj:mika / 水城ミカ
Phase-I rank: 1
R2 rank: 3
classification: UNINTENDED_REGRESSION
```

The frozen gold grounds the query in Mika's `compassion` Statement:

```text
慈愛を行動原理とし、弱い立場の人へ先に手を差し伸べる。
```

Reference review reported that the Statement and Facet channels support Mika,
but adding the overview channel to RRF reverses the final Object ordering.

## 2. What changed in R2

R2 deliberately replaced the Phase-I broad Object representation:

```text
object_overall
```

with:

```text
object_overview + facet + statement
```

This is not a rename. `object_overview` is a compact broad-discovery anchor. It
contains Object-level context such as name, aliases, class, Facet inventory,
facet-less summaries, searchable Attributes and Relations, while **content-Facet
Statement bodies are intentionally excluded**.

Therefore the semantic role of the Object-level representation changed
materially: the old broad representation contained detailed Knowledge that the
new overview intentionally delegates to Facet/Statement representations.

## 3. Current R2-05 fusion path

The R2 wrapper independently retrieves:

```text
semantic_object_overview
semantic_facet
semantic_statement
```

Each Vector search returns representation-level `source_rank` and cosine score.
The inherited Phase-I aggregator then performs two stages.

### 3.1 Channel-local bounded Object aggregation

For each channel, hits are grouped by Object/Version. The channel-local value is:

```text
channel_contribution(object)
  = sum(1 / (60 + source_rank(hit)))
    over the best bounded hits for that object
```

Caps remain:

```text
overview  = 1
facet     = 2
statement = 3
```

The implementation uses this contribution only to convert each channel into an
Object rank list.

### 3.2 Cross-channel Object-rank RRF

The numeric channel contribution is then discarded. Final fusion is:

```text
fused_score(object)
  = sum(1 / (60 + channel_object_rank))
```

Consequently, after channel-local ranking, `semantic_object_overview`,
`semantic_facet`, and `semantic_statement` are co-equal final RRF voters. A
rank-1 overview Object contributes the same final vote as a rank-1 Statement
Object, despite their different R2 semantic roles.

The `1 / 2 / 3` contribution caps affect ordering *inside* each channel, but do
not encode the different semantic authority of overview versus detail at the
cross-channel fusion stage.

## 4. Root cause

### 4.1 Primary root cause

**R2 changed the semantic role of the Object-level representation but retained
the Phase-I flat, co-equal cross-channel fusion semantics.**

That inheritance was a reasonable R2-02 starting baseline and was explicitly
subject to R2-08 quality acceptance. R2-08 has now provided the evidence that the
baseline is not valid without revision.

For `short_japanese_love`, the relevant concept is present in detailed Knowledge
(`慈愛` in the Statement and the derived Facet representation) but is
intentionally absent from `object_overview`. The overview channel therefore acts
as a broad/noisy ranking signal for this query, yet its final RRF vote has the
same authority as each detailed semantic channel. This allows overview ordering
to overturn the correct detailed evidence.

### 4.2 Why this is not a Harrier/runtime problem

The regression was reproduced with the frozen Harrier model/revision, fixed
Embedding Space, CUDA/bfloat16/1024 dimensions, and no truncation or runtime
substitution. Statement retrieval is case-level identical to Phase I, Facet
Similarity remains perfect, generation isolation passes, and active
`object_overall` leakage is zero.

The evidence therefore points to R2 Object-level semantic aggregation, not model
selection, runtime configuration, generation mixing, or canonical Knowledge.

### 4.3 Why changing `object_overview` content is not the first remedy

Copying detailed Facet Statement bodies back into `object_overview` would recreate
the duplication/resource architecture that R2 was introduced to remove. It would
also violate the frozen overview semantic contract. The regression must be fixed
at aggregation/fusion unless new evidence proves the representation contract
itself is insufficient.

## 5. Remediation options

### Option A — Numeric overview down-weight in the existing flat RRF

Concept:

```text
score = w_overview * RRF(overview_rank)
      + RRF(facet_rank)
      + RRF(statement_rank)

0 < w_overview < 1
```

Advantages:

- smallest implementation change;
- keeps overview available for broad discovery;
- does not compare BM25 and cosine directly;
- directly addresses the observed over-authority of overview.

Disadvantages:

- a scalar value can become benchmark tuning unless selected by an explicit
  stability rule;
- the architecture remains flat even though R2 representations are hierarchical;
- correlated semantic families still appear as independent top-level voters.

Verdict: **acceptable fallback, not preferred architecture by itself**.

### Option B — Overview candidate-only / final tie-break

Concept: overview retrieves candidates but Facet/Statement detail determines the
primary semantic order; overview only breaks detail ties or supplies fallback
results.

Advantages:

- strongly prevents broad overview noise from overruling detailed Knowledge;
- matches the phrase "broad discovery anchor" literally.

Disadvantages:

- overview owns legitimate searchable semantics that may not exist in content
  Facets/Statements, especially Attributes, Relations and facet-less summaries;
- a broad query could be unfairly demoted merely because it is overview-owned;
- requires a potentially brittle definition of when fallback is allowed.

Verdict: **rejected as the default R2-05 remedy**.

### Option C — R2 semantic sub-aggregation, then outer Hybrid fusion

Concept: treat overview/Facet/Statement as one correlated Semantic subsystem.
Build one bounded Object semantic ranking first, preserving representation-level
explainability. Hybrid then fuses that one semantic Object ranking with Registry
and Knowledge lexical rankings.

Required invariant:

```text
Object overview = auxiliary broad signal
Facet/Statement = detailed semantic evidence
```

The inner Semantic aggregator must therefore be role-aware; it must not simply
reproduce the current equal three-vote RRF under another name.

Advantages:

- reflects the R2 representation hierarchy explicitly;
- prevents three correlated representation granularities from being treated as
  three unrelated top-level retrieval systems;
- keeps lexical-vs-semantic outer RRF, where rank fusion across heterogeneous
  score systems is useful;
- can preserve overview-owned discovery while bounding its authority;
- creates a clear place for future semantic-fusion quality tests.

Disadvantages:

- larger change than a one-line weight adjustment;
- the inner role-aware rule must be selected and regression-tested;
- changing semantic top-level participation can affect currently perfect Hybrid
  metrics and must therefore be validated against all frozen cases.

Verdict: **preferred architectural direction**.

### Option D — Raw-cosine summation / max across all semantic families

Because all three families use one Embedding Space, raw cosine is technically
available across them. However representation granularity and text structure can
shift score distributions even in one Embedding Space.

Advantages:

- strongest matching detailed representation can dominate naturally;
- no second rank normalization.

Disadvantages:

- assumes cross-family score calibration that has not been established;
- max-only can overreact to one spurious hit; sum can reintroduce count bias;
- more sensitive to embedding distribution changes than rank-based fusion.

Verdict: **do not adopt without separate calibration evidence**.

## 6. Selected remediation direction

Select **Option C: a dedicated R2 semantic sub-aggregation layer**, with a
role-aware inner RRF rule. Do not modify `object_overview` content, the embedding
model, runtime, or canonical Knowledge.

The exact inner rule is **not frozen from desk review alone**. Before code design
is finalized, the Reference Workstation must expose the actual channel-level
ranks/contributions for the failed case and run bounded ablations.

The preferred first candidate for that ablation is a weighted rank rule rather
than raw-cosine fusion:

```text
inner_semantic_score =
    w_overview * 1/(60 + overview_object_rank)
  + w_facet    * 1/(60 + facet_object_rank)
  + w_statement* 1/(60 + statement_object_rank)

0 < w_overview < w_facet <= w_statement
```

This is a *semantic-role contract*, not permission to tune arbitrary numbers to
one case. The final values must satisfy the selection rules below.

Once the inner score creates one Semantic Object rank, outer Hybrid fusion uses
that single Semantic rank plus the existing lexical channels. Exact identity
priority remains unchanged.

## 7. Parameter-selection rules

Do not choose a weight only because it moves Mika from rank 3 to rank 1. The
selected rule must satisfy all of the following:

1. `short_japanese_love` returns Mika at the accepted rank without weakening the
   gold judgement.
2. All 24 frozen Object Search queries are rerun in Semantic and Hybrid modes.
3. No currently passing Semantic/Hybrid case becomes an unexplained regression.
4. Exact identity, filters, current/history, temporal/derivation, one-Object
   result and generation isolation remain unchanged.
5. Add targeted overview-owned probes for:
   - Structured Attribute semantics;
   - Relation semantics;
   - facet-less Summary semantics;
   so down-weighting overview cannot silently destroy its intended role.
6. Prefer the **largest overview authority** that satisfies the complete gate and
   remains stable under adjacent candidate settings. Do not choose a knife-edge
   value that passes only one exact scalar.
7. Harrier 0.6B/revision/runtime/Embedding Space remain fixed.

A small bounded sweep such as overview weights `0.25 / 0.50 / 0.75`, with the
detail channels fixed by the proposed role ordering, is an experiment for
choosing a contract—not a license for unrestricted hyperparameter search.

If no stable role-aware weighted rule satisfies both the existing gold and the
new overview-owned probes, stop and review a non-weighted inner aggregation rule.
Do not hide the failure by changing the model.

## 8. Required diagnostic before implementation freeze

For `short_japanese_love`, record for Mika and every Object ranked above it:

```text
overview:
  representation/member identity
  raw cosine
  representation source rank
  channel-local Object contribution
  channel-local Object rank

facet:
  same fields for bounded contributing hits

statement:
  same fields for bounded contributing hits

current final RRF contribution per channel
current final rank
```

Also record the same decomposition for the Phase-I `object_overall` baseline if
available from the saved fixture/Embedding Space. This proves exactly where the
rank reversal enters the pipeline and avoids repairing the wrong stage.

## 9. Implementation boundary after local ablation

If the selected Option-C candidate passes the local diagnostic/ablation gate,
R2-05 remediation implementation should:

- remain generation-scoped;
- preserve representation-level `ObjectSearchMatch` evidence;
- keep `semantic_object_overview`, `semantic_facet`, and
  `semantic_statement` explainability;
- produce one internal Semantic Object ranking for outer Hybrid fusion;
- keep exact name > exact alias > non-exact;
- preserve Facet-scoped no-overview/no-fallback semantics;
- preserve Statement-only temporal/derivation filters;
- keep one Object = one result;
- add regression coverage for the failed case and overview-owned probes;
- leave R2-06 Similarity code untouched.

The result DTO need not expose a new public synthetic `semantic_r2` channel if
that would weaken explainability; the single semantic rank may remain an internal
fusion concept while matches retain their actual representation channels.

## 10. Acceptance after remediation

R2-05 remediation is not accepted from the failed case alone. Re-run the full
R2-08 Search-quality acceptance unchanged after implementation.

Minimum gate:

```text
short_japanese_love unintended regression       resolved
Semantic Phase-I comparable metrics             no unexplained regression
Hybrid Phase-I comparable metrics               no unexplained regression
Statement retrieval                             preserved
Facet search / Facet Similarity                  preserved
5 search contracts                              5/5 PASS
Evidence Search                                 preserved
active object_overall leakage                   0
focused regression                              PASS
Windows full pytest                             PASS
R1 preserved assets                             SHA-256 unchanged
Harrier/runtime                                 unchanged
```

The two R2-06 Overall Similarity regressions remain separate. Even if Semantic
Search is repaired, **R2-08 remains FAIL / Not Complete** until the R2-06
regressions are also remediated and the complete acceptance gate passes.

R2-09 must not start.

## 11. Review conclusion

The R2-05 failure is an **aggregation-contract mismatch**, not a failure of the
R2 representation split itself:

```text
semantic role changed:
  detailed object_overall -> compact object_overview

but fusion authority stayed flat:
  overview == facet == statement final RRF vote
```

R2-08 supplied the evidence that the inherited Phase-I flat fusion baseline must
now be revised, exactly as the R2-02 contract allowed when quality evidence
required it.

**Decision:** reopen R2-05 only for Semantic Object aggregation remediation.
Proceed to the bounded Reference Workstation diagnostic/ablation described in
this review. Do not change the model, overview content, R2-06, or R2-09.


## Reference Workstation remediation verification (2026-10-24)

R2-05 Semantic remediation: **Complete / verified on the remediation branch**.
R2-08 remains **FAIL / Not Complete** because the separate R2-06 Overall
Similarity regressions are unchanged. R2-09 remains blocked / Not Started.
No main merge, production cutover or Similarity remediation was performed.

Evidence: `benchmark/results/n05d04r2-r2-05-semantic-remediation.json`;
local raw evidence: `.local/r2-05-remediation/20261024T000056/`.
Execution baseline: `62c2748e7bdf552d5f7fd29bec817ffa5e04ceff`.

### Measured root cause

For `short_japanese_love` (`愛`), independent channel-local Object ranks were:

| Object | Overview | Facet | Statement | Old fused score | Old final rank |
|---|---:|---:|---:|---:|---:|
| Aoi | 1 | 4 | 2 | 0.04814747488101534 | 1 |
| Ash Garden | 2 | 2 | 3 | 0.048131080389144903 | 2 |
| Mika | 8 | 1 | 1 | 0.047492767598842814 | 3 |

Facet and Statement aggregation both correctly rank Mika first. The inversion
occurs at the inherited equal-channel final RRF, where compact overview has the
same authority as each detailed family. The machine-readable diagnostic retains
all contributing representation/membership IDs, Facet/Statement identities,
raw cosine, representation source ranks, admitted top-cap hits, local reciprocal
contributions, Object ranks and final RRF scores for these three Objects.
Current Version and generation scope are valid; active overall leakage is zero.

### Bounded ablation and selection

Each row evaluated all 24 frozen Object queries in Semantic and Hybrid modes.
Facet/Statement weights remain 1.0. No query, relevance or model was modified.

| Overview weight | Mika Semantic rank | Semantic MRR | Semantic nDCG@10 | Hybrid MRR / nDCG@10 | Negative case metrics vs Phase I |
|---|---:|---:|---:|---:|---|
| Control: old flat final RRF | 3 | 0.972222 | 0.972250 | 1.0 / 1.0 | love / Semantic |
| 0.25 | 1 | 1.0 | 0.993083 | 1.0 / 1.0 | none |
| 0.50 | 1 | 1.0 | 0.993083 | 1.0 / 1.0 | none |
| 0.75 | 3 | 0.972222 | 0.972250 | 1.0 / 1.0 | love / Semantic |

Selected **0.50**, the largest passing weight with adjacent tested 0.25 also
passing. Attribute, Relation and facet-less Summary probes passed at all three
weights (3/3 per weight), with a distinct target and distractor, actual frozen
Harrier embeddings and no decisive phrase in a content-Facet Statement.
Facet-less Summary may also legitimately have its own Statement representation;
no claim of exclusive overview storage is made. Independent overview retrieval
is additionally exercised by focused tests. These probes are separate from the
frozen Phase-I corpus.

R2 now computes bounded local family Object ranks as before, combines them with
weights overview=0.5 / Facet=1 / Statement=1 and k=60, and produces one Semantic
Object ranking. Only that ranking votes alongside Registry and Knowledge lexical
in outer Hybrid RRF. Raw cosine and lexical scores are never added.
Public match channels, exact identity priority, caps 1/2/3/3, hard filters and
request-scoped generation resolution are unchanged. v1/pre-cutover retains the
old flat RRF. Public fused scores consequently use one outer Semantic vote
(e.g. a sole semantic Object scores 1/61, retaining all three match identities).

### Production verification

The unchanged quality harness was run with `--local-files-only` and an existing
local cache. All 24 Semantic and Hybrid production rankings exactly match the
selected isolated ablation. Against the saved Phase-I result with the same
fixture hash and Embedding Space, no case has a negative comparable metric.
Non-relevant distractor reorderings are retained in the case-level result.

- Semantic: MRR=1.0, Recall@1=0.8541666666666666, Recall@10=1.0,
  nDCG@10=0.9930829680165895.
- Hybrid: MRR=1.0, Recall@1=0.8541666666666666, Recall@10=1.0, nDCG@10=1.0.
- Statement retrieval: 22 queries, unchanged MRR=1.0 / Recall@10=1.0 /
  nDCG@10=0.9927018899225625.
- Contracts 5/5 PASS; active-generation isolation PASS; active overall leakage=0;
  one Object/one result PASS. Facet-specific, temporal/derivation Statement-only,
  current/history, exact identity, degradation and CLI/MCP/Application contracts
  pass focused/full regression. Qdrant in-memory regression passes.
- Existing Overall Similarity losses remain; Evidence and Facet Similarity are
  unchanged. No R2-06 source was modified. Harness automatic PASS is not an
  R2-08 completion decision.
- Quality-harness workflow: 13.580s; CUDA peak allocated
  1338302464 bytes, reserved
  1430257664 bytes. These observations
  are not formal N-05 timing.

Commands/results:

```text
python -m pytest -q tests/test_hybrid_search.py tests/test_hybrid_search_r2.py tests/test_hybrid_search_r2_semantic_fusion.py
  39 passed
python -m pytest -q tests/test_n05d04r2_search_quality_acceptance.py
  6 passed
python scripts/run_n05d04r2_search_quality_acceptance.py --local-files-only --cache <existing-local-cache>
  automatic PASS; R2-08 remains FAIL after manual Similarity review
R2-08 focused set plus semantic fusion tests
  92 passed
python -m pytest -q
  647 passed, 0 failed, 0 skipped
python -m compileall -q src tests scripts
  PASS
python -m ruff check src tests scripts
  PASS
python -m ruff format --check <four changed Python files>
  PASS
git diff --check
  PASS
```

The pre-existing repository-wide E501 in
`benchmark/tools/n05_resource_preflight.py:69` was not modified.
Original-workspace R1 assets remain unstaged and all three before/after SHA-256
values match; exact hashes are recorded in the result. Canonical user data,
reference DB/active generation and production Qdrant were not written.

Next permitted review: separate R2-06 Overall Similarity remediation and then
R2-08 re-acceptance. Neither is started here. R2-09 must not start.
