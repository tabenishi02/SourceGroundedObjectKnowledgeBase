# N-04G-23A-E5 — Residual Classifier Scope / Evaluation Design

更新日: 2026-10-20

- Status: **Complete / evaluation design fixed**
- Parent: `N-04G-23A-E — Atomicity / Role Gate Responsibility Decomposition`
- Predecessors:
  - `N-04G-23A-E1 — 47-Gold Responsibility Mapping` Complete
  - `N-04G-23A-E2 — v4 V2 Responsibility Boundary Design` Complete
  - `N-04G-23A-E3 — Structured Proposition Contract Design` Complete
  - `N-04G-23A-E4 — Role Provenance / Compatibility Matrix Design` Complete
- Authority:
  - `docs/evaluation/N04G23AE_47_GOLD_RESPONSIBILITY_MAP.md`
  - `docs/decisions/N04G23AE_V4_V2_RESPONSIBILITY_BOUNDARY.md`
  - `docs/decisions/N04G23AE_STRUCTURED_PROPOSITION_CONTRACT.md`
  - `docs/decisions/N04G23AE_ROLE_PROVENANCE_AND_COMPATIBILITY_MATRIX.md`
  - `benchmark/n04g23ae-role-compatibility-v1.json`
- Frozen G-23A 47 Gold labels / required / critical flags remain unchanged.
- N-04: **Failed / not Complete**
- N-05: **blocked**
- G-23B: **blocked until G-23A-E7 acceptance**

---

## 1. Decision summary

V2-Rは、E1〜E4でstructural / deterministicへ移せなかった**自然言語の残余意味判定だけ**を担当する。

v4では、G-23A/G-23A-Rで失敗したjoint Atomicity/Role Judgeへ戻らない。

Residual classifierを次の2つの独立taskへ分離する。

```text
V2-R-A  Residual Atomicity Classifier
V2-R-C  Residual Content-Type Classifier
```

両taskを1つのjoint classifierへ統合しない。

理由:

1. G-23A/G-23A-RではAtomicity問題がRole判定へ干渉し、逆方向の干渉も確認された。
2. SGOKB Atomicityは「1文か」ではなく「独立したgrounding verdictを持ち得るmaterial propositionが複数あるか」という固有taskである。
3. content typeはAtomicityと別軸であり、`NON_ATOMIC + ROLE_VALID`が正規のGoldとして多数存在する。
4. deterministic metadata違反はE4 V2-Dで既に処理するため、classifierへ再度purpose/presentation policyを判断させる必要がない。

Normative flow:

```text
Candidate
  ↓
V2-S schema/construction
  ↓
V2-P application-owned role provenance
  ↓
V2-D deterministic compatibility
  ↓ PASS only
V2-R-A residual atomicity if required
  ↓ ATOMIC only
V2-R-C content-only classification if required
  ↓
application compares observed content class
with E4 normalized expected role
  ↓ compatible only
V3/V4 support or derivation
```

V2-S/V2-P/V2-D failureはV2-Rでoverride不可。

---

## 2. Exact V2-R scope

### 2.1 V2-R-A — Residual Atomicity

対象:

- E3で`REVIEW_REQUIRED`となるmodel-authored free-text proposition。
- structural schemaはvalidだがsemantic Atomicityをconstructionだけでは証明できないcandidate。
- E1 `COMBINED` / `OPTIONAL_AMBIGUOUS`のうちdesk replay上Atomicity residual確認が必要なcase。

判定taxonomy:

```text
ATOMIC
NON_ATOMIC
AMBIGUOUS
```

`AMBIGUOUS`はproduction aggregateでは`INDETERMINATE`へ正規化しfail-closed。

V2-R-Aが判定しないもの:

- truth / factual correctness
- Context support
- semantic role
- purpose compatibility
- presentation compatibility
- derivation quality

### 2.2 V2-R-C — Residual Content Type

対象:

- E1 `RESIDUAL_SEMANTIC` 11件。
- E1 `COMBINED` 5件のsemantic側。
- E4でmetadata policyはPASSしたが、model-authored textの実content classをconstructionだけでは証明できないcandidate。

Content taxonomy:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
```

Production compatibility mapping:

```text
expected source_fact
  accepts SOURCE_FACT_CONTENT only

expected interpretation
  accepts INTERPRETATION_CONTENT only

expected creative_addition
  accepts CREATIVE_CONTENT only

expected context_limit
  accepts CONTEXT_LIMIT_CONTENT only
```

`MIXED_CONTENT` -> semantic FAIL。
`AMBIGUOUS` -> INDETERMINATE / fail-closed。

### 2.3 What V2-R-C must not infer

V2-R-Cは次を判定しない。

```text
whether a source fact is true
whether it is supported by supplied Context
whether an interpretation is logically derived from premises
whether creative content is good/useful
whether a context limit is factually correct about all SGOKB knowledge
```

これらはV3/V4/Material等の別authorityである。

従って、例えばContextでunsupportedでもsource-world factとして読めるtextは:

```text
SOURCE_FACT_CONTENT
```

であり、Role/content classifier上のFAILではない。

---

## 3. Classifier input isolation

### 3.1 Atomicity input

V2-R-Aへのprimary inputは原則:

```text
claim_text
```

のみ。

必要なtask definition/versionはclassifier configuration側で固定する。

原則渡さない:

```text
expected semantic role
purpose
presentation_role
support verdict
support text
premise text
historical model verdict
critical/required flag
```

これによりAtomicity classifierがRole/policy/safety labelへanchoringされることを防ぐ。

### 3.2 Content-type input

V2-R-Cへのprimary inputも原則:

```text
claim_text
```

のみ。

**application-owned expected roleをclassifierへ入力しない。**

正しい順序:

```text
claim_text
  ↓ classifier
observed_content_class
  ↓ deterministic comparison
E4 normalized expected role
  ↓
compatible / semantic mismatch
```

禁止:

```text
"This should be source_fact. Is it source_fact?"
```

のようなexpected-role priming。

### 3.3 Optional controlled context

純粋text-onlyでは分類不能なfixtureがE6/Evaluationで確認された場合のみ、次を**別experiment arm**として評価可能とする。

```text
minimal local proposition neighborhood
or
explicit source/creative subject identity markers
```

ただしpurpose/presentation/declared roleを混入させず、base armと結果を混ぜない。

---

## 4. Residual dispatch / skip policy

V2-Rを呼ばないこと自体にもauthorityが必要である。

### 4.1 V2-R-A NOT_REQUIRED

次のみ候補:

- `system_context_limit`のapplication-owned canonical payload。
- `certified_fact_materialization`でCertified Contentのexact contentまたはdeterministic canonical materializationを使う場合。
- 将来、G-23B/G-23Dでmeaning contentまでapplication-owned deterministic constructionと証明されたpath。

model-authored free textをschema validという理由だけで`NOT_REQUIRED`にしない。

### 4.2 V2-R-C NOT_REQUIRED

次のみ候補:

- `system_context_limit` canonical payload。
- `certified_fact_materialization` exact/deterministic materialization。
- role/content typeまでapplication-owned constructionで固定できる将来path。

### 4.3 Fail closed

```text
classifier unavailable
classifier output malformed
unknown label
score/decision threshold unresolved
model/checkpoint mismatch
AMBIGUOUS
```

はすべてgrounded PASS不可。

---

## 5. Dataset architecture

47 Goldは**evaluation seed / historical control**として保持するが、classifierのtraining corpusそのものとして使い切らない。

### 5.1 Two datasets

別datasetとして作る。

```text
Dataset A: Atomicity
Dataset C: Content Type
```

同じtextが両datasetへ存在してもよいが、label taskを混ぜない。

### 5.2 Atomicity dataset labels

```text
ATOMIC
NON_ATOMIC
AMBIGUOUS_CONTROL
```

`AMBIGUOUS_CONTROL`は原則training targetに使わず、abstention/uncertainty evaluation用controlとする。

### 5.3 Content dataset labels

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS_CONTROL
```

`AMBIGUOUS_CONTROL`はhard supervised targetへ強制変換しない。

### 5.4 Dataset expansion sources

Frozen Goldを直接大量paraphraseしてランダムsplitするだけの方式は禁止する。

拡張は最低限次のfamilyを持つ。

Atomicity families:

```text
single direct proposition
faithful paraphrase
coordinated independent facts
fact + unsupported/additional proposition shape
fact + causal/explanatory conclusion
premise restatement + interpretation
multiple creative events/state changes
context-limit + source-world fact
same proposition with compound noun/phrase but still atomic
multi-reference one-proposition cases
```

Content families:

```text
direct source-world fact
negated source-world fact
unsupported-looking but still source-fact content
interpretive conclusion
source premise embedded in interpretation
new creative entity/state/event
source-world fact disguised as creative
context availability statement
context-limit mixed with source-world assertion
cross-role mixed content
```

### 5.5 Transformation families

各semantic patternから次を作れる。

```text
paraphrase
lexical substitution
entity substitution
minimal clause addition/removal
compound -> split pair
split -> compound pair
role/content swap
creative/source-world subject swap
context-limit/source-world minimal pair
negation pair
premise-restatement pair
```

ただし、変換後labelは自動継承せずhuman/design reviewで確定する。

### 5.6 Dataset size target

E5では絶対件数をAcceptance authorityにしないが、benchmark開始前のcandidate targetを次とする。

```text
Atomicity labeled non-ambiguous: >= 400
Content labeled non-ambiguous:   >= 500
Ambiguous/control:                >= 50 per task where feasible
```

これは最低件数そのものを品質証明とはみなさない。重要なのはpattern coverageとfamily holdoutである。

---

## 6. Leakage-resistant split policy

ランダムrow splitをproduction-selection authorityにしない。

### 6.1 Pattern-family holdout

同一semantic/template familyはtrain/dev/testへ跨がせない。

例:

```text
"X is A and B"
"Y is C and D"
```

のような表層entity置換だけのfixtureを別splitへ分けない。

### 6.2 Source lineage grouping

以下は同一groupとして扱う。

```text
original
paraphrases
minimal pairs derived from it
role/content swaps
entity substitutions from same template
```

group単位でsplitする。

### 6.3 Frozen critical/adversarial holdout

G-23A frozen required/critical setは、training済みclassifierのproduction selection時には**最終holdout control**として扱う。

- threshold/model選択の反復調整に使い回さない。
- training dataへ直接複製しない。
- same template paraphraseをtrainingへ大量投入しない。

開発中は別development corpusで調整し、Frozen Goldは最終confirmationへ残す。

---

## 7. Candidate implementation families

E5では特定production modelを採用しない。後続benchmarkで最低限次を比較する。

### C0 — Historical bounded LLM baseline

G-23A/G-23A-R結果をhistorical baselineとして使用する。

新しい汎用LLMを無制限に追加することはprimary strategyにしない。

用途:

- improvement baseline
- error-family comparison

### C1 — Encoder sequence classifier

Encoder + classification headで各taskを個別fine-tuneする。

候補family例:

```text
ModernBERT-class encoder
DeBERTa-v3-class encoder
comparable current encoder checkpoint
```

Atomicity用とContent Type用は別head / 別checkpointを第一候補とする。

### C2 — Cross-encoder / pair classifier

`claim_text`と固定class definition / rule descriptionをpairとしてscoreする方式を評価する。

例:

```text
(claim_text, ATOMIC definition)
(claim_text, NON_ATOMIC definition)
```

またはcontent class定義とのpair scoring。

Cross-encoderはsentence pair分類を直接扱えるため候補とするが、class score calibration / abstention policyを別途freezeする。

### C3 — Few-shot / lightweight classifier

SetFit等の少量ラベル向けencoder classificationをefficiency baselineとして評価可能。

ただしcritical false-pass Gateを満たさない場合、軽量であることを理由に採用しない。

### C4 — Deterministic-first cascade

Production architectureとしてはE2-E4のdeterministic-first cascadeを常に比較対象の外枠とする。

```text
V2-S/V2-P/V2-D
  ↓ only unresolved model-authored semantics
V2-R-A / V2-R-C
```

これはclassifier candidateではなく**mandatory architecture baseline**である。

---

## 8. Training / evaluation reproducibility

Reference Workstation: Windows 11 / RTX 4090をprimary benchmark environmentとする。

各trained/evaluated candidateについて最低限保存する。

```text
base model repository + revision
model/config SHA or artifact SHA-256
training code commit
training dataset manifest/hash
split manifest/hash
seed(s)
hyperparameters
library versions
Python/PyTorch/CUDA identity
max length
device
threshold / abstention policy
class mapping
```

ネットワーク取得はpreparation時に許容できるが、formal replay/freeze時はG21R同様にlocal-only再現性を要求する方向とする。

Final freeze条件はG-23F/G-26で確定する。

---

## 9. Metrics

Accuracy単独をselection authorityにしない。

### 9.1 Atomicity

最低限:

```text
critical NON_ATOMIC false-pass count
required ATOMIC false-reject count
NON_ATOMIC recall
ATOMIC recall
macro F1
AMBIGUOUS abstention behavior
family-holdout confusion matrix
repeatability
latency
VRAM
```

最重要:

```text
critical false-pass = 0
```

### 9.2 Content Type

最低限:

```text
critical wrong-compatible false-pass count
valid required false-reject count
per-class precision/recall/F1
MIXED_CONTENT recall
SOURCE_FACT <-> CREATIVE confusion
SOURCE_FACT <-> INTERPRETATION confusion
AMBIGUOUS abstention behavior
family-holdout confusion matrix
repeatability
latency
VRAM
```

`wrong-compatible false-pass`とは、本来expected roleと非互換なcontentをclassifierがexpected-compatible classへ誤分類し、V2 PASS候補へしてしまうerrorを指す。

---

## 10. Selection Gate

Production候補は**Atomicity classifierとContent-Type classifierを別々に選定可能**とする。

同一model familyである必要はない。

### 10.1 Safety Gate — mandatory

Frozen critical/adversarial confirmationで:

```text
Atomicity critical false-pass = 0
Content-type critical wrong-compatible false-pass = 0
```

どちらか1件でもあれば、そのcandidate/configurationはproduction不採用。

### 10.2 Required-valid Gate

Safety PASS後にrequired-valid false rejectを比較する。

目標:

```text
required-valid false reject = 0
```

0を満たさない場合は自動採用せず、error familyを分析してarchitecture/escalation reviewへ戻す。

### 10.3 Repeatability Gate

Deterministic encoder系はsame artifact/inputでexact label再現を要求する。

LLM系候補を再評価する場合もrequired casesでsame-input repeatability 100%を要求する。

### 10.4 Pattern stability

holdout familyと事前固定paraphrase/minimal-pair familyのcritical decision一致を確認する。

thresholdをFrozen Goldへ後付けfitしない。

### 10.5 No forced selection

全候補FAILなら:

```text
VALID_FAIL_NO_SELECTION
```

を正常な結果として許容する。

Gateを緩めてbest availableを採用しない。

---

## 11. Abstention / confidence policy

Model confidenceを校正済み確率と仮定しない。

Classifier adapterの論理出力は最低限:

Atomicity:

```text
ATOMIC
NON_ATOMIC
AMBIGUOUS
UNAVAILABLE
```

Content:

```text
SOURCE_FACT_CONTENT
INTERPRETATION_CONTENT
CREATIVE_CONTENT
CONTEXT_LIMIT_CONTENT
MIXED_CONTENT
AMBIGUOUS
UNAVAILABLE
```

Production aggregate:

```text
AMBIGUOUS -> fail-closed / no grounded PASS
UNAVAILABLE -> fail-closed / no grounded PASS
```

scoreを使う場合はraw score/logitをaudit保存するが、thresholdはdevelopment corpusでfreezeし、Frozen Gold confirmation後に変更しない。

---

## 12. Evaluation phases

### Phase A — Dataset design/freeze

1. atomicity/content datasetsを別々に作る。
2. pattern family IDを全fixtureへ付与。
3. lineage groupを付与。
4. train/dev/test/frozen-control split manifestを作る。
5. Gold derived fixtureのleakageを検査。

### Phase B — Candidate development

- C1 encoder
- C2 cross-encoder
- C3 lightweight/few-shot
- historical C0 baseline comparison

Model/hyperparameter/threshold selectionはdevelopment corpusのみで行う。

### Phase C — Family-holdout evaluation

未見pattern familyでSafety / Required-valid / ambiguity behaviorを評価する。

### Phase D — Frozen 47 Gold confirmation

G-23A Frozen Goldを最後に使用する。

Gold label/required/critical flagを変更しない。

### Phase E — Selection

Atomicity / Content classifierを独立選定し、組合せたcascadeについて47 Gold + additional adversarial fixtureでaggregate simulationを行う。

---

## 13. E6 handoff contract

E6はclassifier実測をまだ必要としない。

E6 desk replayでは47 Goldそれぞれについて:

```text
V2-S structural outcome
V2-P normalized role
V2-D deterministic outcome
V2-R-A required? expected Gold atomicity
V2-R-C required? expected Gold content class / compatibility
historical broad-judge decision removed?
remaining probabilistic decision?
```

を記録する。

E6の目的は「classifierがすでに高精度」と仮定することではなく、**broad joint Judgeへ委ねていたdecision surfaceをどこまで狭めたか**を測ることである。

---

## 14. Explicit non-decisions

E5ではまだ決めない。

- final production classifier model/checkpoint
- exact training corpus text
- exact hyperparameters
- final threshold numerical value
- final library choice
- final ONNX/TensorRT最適化
- production implementation

これらはE7 acceptance後、G-23B〜G-25/G-26で必要に応じて実装・benchmark・freezeする。

---

## 15. Completion Gate

E5をCompleteとする条件:

- [x] V2-R scopeがAtomicity / Content Typeへ分離された。
- [x] classifier taxonomyが固定された。
- [x] expected roleをclassifier inputから分離した。
- [x] deterministic Gate override禁止が維持された。
- [x] dataset expansion policyが固定された。
- [x] pattern-family / lineage holdoutが固定された。
- [x] candidate implementation familyが固定された。
- [x] zero-critical-FP Gateが維持された。
- [x] ambiguity/unavailable fail-closedが固定された。
- [x] no forced selectionが固定された。
- [x] Reference Workstation reproducibility evidence requirementsが定義された。
- [x] E6 desk replayに必要なclassification contractが定義された。

Result: **PASS / E5 Complete**

次Task:

`N-04G-23A-E6 — 47-Gold Desk Replay / Coverage Analysis`
