# N-04G-25A — Residual Classifier Benchmark Execution Plan

更新日: 2026-10-21

- Task: `N-04G-25A — Residual Classifier Benchmark / Selection`
- GitHub `main` authority at plan creation: `cd745c5edd3c63ccebaa802d321e6e882cb466ea`
- Mandatory Reference Workstation preflight: **PASS**
- Classifier benchmark: **READY / not started**
- Frozen 47 final confirmation: **not started**
- G-25A: **not Complete**
- G-25B/G-26: **blocked**
- N-04: **Failed / not Complete**
- N-05: **blocked**

## 1. Purpose

Select concrete production components for the two frozen residual tasks without reopening G-23F:

```text
V2-R-A Residual Atomicity
  input: claim_text only
  output: ATOMIC / NON_ATOMIC / AMBIGUOUS

V2-R-C Residual Content Type
  input: claim_text only
  output:
    SOURCE_FACT_CONTENT
    INTERPRETATION_CONTENT
    CREATIVE_CONTENT
    CONTEXT_LIMIT_CONTENT
    MIXED_CONTENT
    AMBIGUOUS
```

Atomicity and Content Type remain independent tasks/components. Expected semantic role, purpose, presentation role, support verdict, support text and Frozen 47 labels must not be model inputs.

## 2. Non-negotiable evaluation order

```text
Reference Workstation preflight                  PASS
  ↓
Development corpus design + generation
  ↓
Corpus/split validation
  ↓
Corpus + split manifest freeze commit/hash
  ↓
Candidate acquisition + revision/artifact freeze
  ↓
Training/tuning on train + dev only
  ↓
Threshold/abstention freeze on dev only
  ↓
Development selection-set evaluation
  ↓ PASS candidates only
Candidate selection + checkpoint/policy freeze
  ↓
Frozen 47 final confirmation exactly once
  ↓ PASS only
G-25A PASS / selected V2-R-A and V2-R-C
```

Frozen 47 must not be loaded by the development corpus generator, training scripts, threshold tuner or candidate-selection code before the final-confirmation command.

## 3. Development corpus architecture

Create two independent committed corpora:

```text
benchmark/n04g25a-atomicity-development-v1.jsonl
benchmark/n04g25a-content-type-development-v1.jsonl
```

and manifests:

```text
benchmark/n04g25a-development-manifest-v1.json
benchmark/n04g25a-split-manifest-v1.json
```

Minimum target before benchmark:

```text
Atomicity non-ambiguous >= 400
Content Type non-ambiguous >= 500
Atomicity ambiguous controls >= 50 where feasible
Content Type ambiguous controls >= 50 where feasible
```

The minimum row count is not acceptance evidence. Family coverage and leakage-resistant grouping are mandatory.

### 3.1 Row identity

Each row must contain at least:

```text
case_id
text
label
family_id
lineage_id
split_group
source = synthetic_design_family | independent_seed
required
critical_for_safety
rationale
```

Content-Type rows additionally carry evaluation-only compatibility metadata where applicable:

```text
compatible_expected_roles[]
critical_incompatible_expected_roles[]
```

These role lists are never provided to the classifier.

### 3.2 Label authority

Do not create one row and automatically inherit its label across arbitrary transformations.

Instead:

1. define each semantic/template family explicitly;
2. assign that family's label from E5/G-23F semantics;
3. record a family-level rationale;
4. generate lexical/entity variants only inside that reviewed family;
5. validate generated rows against family invariants before freeze.

The manifest must enumerate every family, task, label and rationale.

### 3.3 Atomicity families

Required coverage includes at least:

```text
ATOMIC
- single direct property
- single relation
- negated single proposition
- one event with modifier
- one concept/general proposition
- one interpretation conclusion
- one creative event/state
- one context-availability proposition
- compound noun/phrase that remains one proposition
- one proposition with multiple references/participants

NON_ATOMIC
- independent factual conjunction
- fact + causal/explanatory proposition
- factual premise(s) + interpretation conclusion
- multiple independent events/state changes
- source-world fact + context-limit proposition
- source-world fact + creative addition
- interpretation + extra factual assertion
- sequential events that can receive different verdicts
- two relations/properties with independent verdicts
- cross-grounding-policy mixed proposition

AMBIGUOUS_CONTROL
- coordination-scope ambiguity
- relative/appositive clause with unclear material independence
- elliptical coordination
- borderline explanatory modifier
```

### 3.4 Content-Type families

Required coverage includes at least:

```text
SOURCE_FACT_CONTENT
- direct source-world fact
- negated fact
- concept/general fact
- unsupported-looking but still factual content
- relation/state/event fact

INTERPRETATION_CONTENT
- comparison/synthesis conclusion
- causal interpretation
- evaluative inference
- abstract conclusion from premises without restating them

CREATIVE_CONTENT
- invented entity
- invented state
- invented event
- hypothetical continuation/addition presented as newly invented material

CONTEXT_LIMIT_CONTENT
- supplied context lacks a property
- available evidence/context does not identify an answer
- bounded context cannot support a requested material item

MIXED_CONTENT
- source fact + interpretation
- source fact + creative content
- source fact + context-limit
- interpretation + creative content
- interpretation + context-limit
- creative content + context-limit

AMBIGUOUS_CONTROL
- meta-language whose subject can be read as world or context
- hypothetical statement without clear asserted/invented status
- borderline evaluative factual language
```

Use neutral independent domains and entities; do not build the development corpus by paraphrasing Frozen 47 rows.

## 4. Leakage-resistant split

Use group-level splits, never random row split as selection authority.

Required partitions:

```text
train
validation
selection
```

Rules:

- same `family_id` must belong to one partition only;
- same `lineage_id` must belong to one partition only;
- entity/lexical variants from one template family stay together;
- minimal-pair siblings stay together unless they were independently authored as separate semantic families;
- split manifest is frozen before model training;
- development selection rows are not used for threshold tuning.

Target proportions may be approximately 60/20/20, but family coverage takes precedence over exact percentages.

## 5. Candidate families

Benchmark Atomicity and Content Type separately.

### C0 — Historical bounded-LLM baseline

Use existing G-23A/G-23A-R evidence as a historical baseline only.

Do not reuse historical joint Atomicity/Role verdicts as training labels and do not treat the historical joint judge as a selectable v4 component.

### C1A — ModernBERT sequence classifier

Base:

```text
answerdotai/ModernBERT-base
```

Train separate `AutoModelForSequenceClassification` checkpoints for Atomicity and Content Type.

### C1B — DeBERTa-v3 sequence classifier

Base:

```text
microsoft/deberta-v3-base
```

Train separate task checkpoints. This is an independent encoder baseline and may be selected if it beats C1A under the frozen safety Gate.

### C2 — Cross-encoder / class-definition pair classifier

Base:

```text
cross-encoder/nli-deberta-v3-base
```

Input pair:

```text
(claim_text, frozen class definition)
```

Score all classes using the same frozen class definitions. Do not place expected application role in the definition.

Evaluate both:

```text
zero-shot NLI scoring baseline
optional development-only pair fine-tune
```

If pair fine-tuning is used, training data must come only from the frozen development train partition.

### C3 — SetFit lightweight/few-shot classifier

Base body:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Use SetFit with its standard logistic-regression head unless a predeclared alternative is added before benchmark results are inspected.

Train Atomicity and Content Type independently.

## 6. Dependency/runtime isolation

Do not change production project dependencies merely to run G-25A.

Use a dedicated ignored benchmark environment/work area under `.local/n04-v4/g25a/` or another explicitly isolated local environment.

Record exact versions of:

```text
Python
PyTorch
CUDA build/runtime identity
transformers
sentence-transformers
setfit
scikit-learn
datasets
accelerate
numpy
```

Model downloads are allowed during candidate preparation. Before evaluation, capture repository/model revision and SHA-256 for locally persisted model/checkpoint artifacts where practical.

## 7. Training and threshold policy

### 7.1 Training

For trainable candidates:

- fixed seed declared before training;
- class mapping frozen;
- max length frozen;
- optimizer/lr/epochs/batch size recorded;
- checkpoint selection may use validation partition only;
- selection partition must not drive epoch/threshold/hyperparameter changes.

### 7.2 Abstention

Production adapters may emit `AMBIGUOUS` for uncertain output.

Candidate policy must be frozen before selection evaluation using validation-only evidence. A generic permitted policy is:

```text
if max_probability < min_confidence -> AMBIGUOUS
or top1_minus_top2 < min_margin -> AMBIGUOUS
else -> top1 class
```

`min_confidence` and `min_margin` must be selected from validation only and recorded in the candidate manifest.

Do not choose a threshold after inspecting Frozen 47.

## 8. Development selection Gate

### Atomicity hard Gate

```text
critical NON_ATOMIC predicted ATOMIC = 0
required ATOMIC predicted NON_ATOMIC/AMBIGUOUS = 0
required repeatability failures = 0
```

Also record:

```text
NON_ATOMIC recall
ATOMIC recall
macro F1
AMBIGUOUS rate
confusion matrix by family
latency
peak VRAM
```

### Content-Type hard Gate

Evaluate raw class accuracy plus deterministic role compatibility.

For every row, classifier receives `text` only. Application-side evaluation compares the predicted class to compatibility metadata.

Hard Gate:

```text
critical incompatible-role false-compatible = 0
required valid-compatible false-reject = 0
required repeatability failures = 0
```

Also record:

```text
per-class recall
macro F1
MIXED detection
AMBIGUOUS rate
compatibility confusion by family
latency
peak VRAM
```

`MIXED_CONTENT`, `AMBIGUOUS` and unavailable/malformed output remain fail-closed.

## 9. Repeatability

For each frozen checkpoint/policy on the development selection partition:

- run inference at least 3 times;
- identical normalized labels are required for every required/critical row;
- record any non-determinism as a repeatability failure.

Training-seed sensitivity may be recorded as a secondary diagnostic but does not replace same-checkpoint inference repeatability.

## 10. Candidate selection

A candidate that fails any task hard Gate is non-selectable for that task.

Atomicity and Content Type may select different families/checkpoints.

If multiple candidates pass a task Gate:

1. prefer lower critical/required errors (all must already be zero under the hard Gate);
2. prefer lower ambiguous rate on non-ambiguous selection rows;
3. prefer higher macro F1 / class recall;
4. if performance is effectively tied, prefer lower median latency;
5. then prefer lower peak VRAM / artifact size;
6. record deterministic tie-break reasoning.

If no candidate passes either task:

```text
VALID_FAIL_NO_SELECTION
```

Do not weaken the Gate.

## 11. Freeze before Frozen 47

Before any final-confirmation request, create a selection-freeze artifact containing at least:

```text
selected Atomicity candidate/checkpoint/revision/hash
selected Content-Type candidate/checkpoint/revision/hash
class mappings
threshold/abstention policies
training dataset manifest/hash
split manifest/hash
training configuration
runtime/library identity
selection metrics
repeatability metrics
```

Commit the freeze document/manifest before Frozen 47 execution.

## 12. Frozen 47 final confirmation

Authority:

```text
benchmark/n04g23a-atomicity-role-gold-v1.json
```

Frozen 47 is loaded only after Section 11 freeze.

Map historical Gold to the v4 residual tasks without changing its bytes/labels/flags:

- Atomicity uses frozen `gold.atomicity`.
- Content Type derives the content-only expected class from the frozen semantic/rationale mapping defined by E1/E4/E5; expected role/purpose/presentation are not classifier inputs.
- application-side compatibility is evaluated separately.

Run each selected frozen checkpoint/policy without tuning.

If Frozen 47 reveals a failure:

```text
G-25A = VALID_FAIL_NO_SELECTION or explicit escalation
```

Do not retune and rerun the same confirmation set as valid selection evidence.

## 13. Required outputs

Commit after development benchmark/selection:

```text
benchmark/n04g25a-atomicity-development-v1.jsonl
benchmark/n04g25a-content-type-development-v1.jsonl
benchmark/n04g25a-development-manifest-v1.json
benchmark/n04g25a-split-manifest-v1.json
benchmark/n04g25a-candidate-manifest-v1.json
benchmark/results/n04g25a-development-selection-reference-workstation.json
```

Before Frozen 47:

```text
docs/evaluation/N04G25A_DEVELOPMENT_CLASSIFIER_SELECTION.md
benchmark/n04g25a-selection-freeze-v1.json
```

After Frozen 47 final confirmation:

```text
benchmark/results/n04g25a-frozen47-final-confirmation-reference-workstation.json
docs/evaluation/N04G25A_RESIDUAL_CLASSIFIER_BENCHMARK_AND_SELECTION.md
```

If no candidate is selected, still commit complete failure evidence and explicitly retain G-25B/G-26 blocked.

## 14. Protected boundaries

Do not modify:

- G-23F frozen architecture;
- Reference Integrity ordering;
- V2-S/P/D authority;
- Atomicity / Content-Type separation;
- classifier `claim_text`-only input;
- application-owned expected role;
- Frozen 47 bytes/labels/required/critical flags;
- Certification exact-copy semantics;
- Certified Content Stage 2 boundary;
- exact Certified Fact materialization;
- retry semantics;
- context-limit ownership;
- Retrieval / Similarity / Context Builder;
- canonical DB / Source / Evidence / Provenance / Object identity / MCP boundary.
