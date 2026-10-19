# N-04G-21V Source-Fact Verifier Candidate Evaluation Plan

更新日: 2026-10-19

- Status: **Planned / Decision criteria frozen before execution**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04G-21 [P0] v3 Acceptance / Reference Workstation Harness Freeze`
- Purpose: G-21 final Freeze前に、specialized source-fact verifierの候補をSGOKB固有failure patternで比較し、正式採用候補を選定する。
- Design authority: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Existing baseline evidence: `docs/evaluation/N04G20_ADVERSARIAL_REPLAY_VERIFIER_BENCHMARK_REGRESSION.md`

---

## 1. Decision context

G-12 formal v2 re-acceptanceでは、汎用semantic judgeだけでは`unsupported but plausible`なmaterial claimをfalse positiveで通すことが確認された。

G-18ではこのfailureに対して、source factを次の多段構成で検証することをFrozen semanticsとした。

```text
V3 deterministic exact/structured support
  ↓ unresolved only
specialized source-fact verifier
  ↓ supported candidate only
independent bounded source-fact judge
  ↓ ENTAILED only
supported
```

ここでFrozenなのは**specialized verifierを独立componentとして置き、negative / disagreement / indeterminateをfail-closedにすること**である。

特定製品としてMiniCheckを永久固定すること自体はG-18の意味設計ではない。G-19もadapter boundaryを設け、verifier implementationを交換可能にしている。

したがってG-21 final Freeze前に、2026年時点の候補を同一SGOKB corpusで比較することは、G-18を再設計する行為ではなく、Frozen interfaceに対するimplementation candidate selectionである。

---

## 2. Why a specialized verifier is still required

MiniCheck自体は必須ではないが、その役割は必要である。

Deterministic supportだけでは、次のようなparaphraseや高重複overclaimを十分に扱えない。

```text
Evidence:
Saber is contracted to Shirou.

Supported paraphrase:
Saber serves Shirou as his contracted Servant.

Unsupported overclaim:
Saber is contracted to Shirou and protects him throughout the Holy Grail War.
```

また、Phi-4等の汎用LLM judge単独へ戻すことは、G-12で実証されたfalse acceptance failureを再導入するため禁止する。

必要なのは、`evidence + atomic claim -> semantic support verdict`を、generatorおよびindependent LLM judgeとは異なるcomponentで判定することである。

---

## 3. Research summary

### 3.1 MiniCheck

MiniCheckはdocument-grounded fact checking向けに設計された2024年系の専用モデル群で、documentとclaimからsupport prediction / scoreを返す。

G-20では`lytang/MiniCheck-RoBERTa-Large`をthreshold 0.50でscreeningし、SGOKBのrequired negative/replay false-positive 0、required positive 2/2を満たした。

長所:

- SGOKB G-20 corpusで既にcandidate evidenceがある。
- 非生成型RoBERTa classifierで、汎用LLM judgeと性質を分離しやすい。
- claim-level verifierとしてG-18のadapterへ自然に接続できる。

懸念:

- 設計世代が2024年であり、2026年のspan-level hallucination detectorと比較して情報量が少ない。
- Reference Workstationには現時点でMiniCheck/NLTKおよび指定model snapshotが未配置。
- source/model revisionと依存packageを新規にformal runtimeへ固定する必要がある。

Reference:

- https://github.com/Liyan06/MiniCheck

### 3.2 LettuceDetect v2 mmBERT

`KRLabsOrg/lettucedect-v2-mmbert-base`は2026年に公開された約0.3Bのencoder型token classifierで、context/question/answerを入力し、answer中のunsupported spanをtoken単位で検出する。

公式model cardでは、single forward pass、binary supported/unsupported span、prose/code/tool-output対応が説明されている。

SGOKBにとって重要なのは、G-12型の`supported clause + unsupported addition`をclaim全体の単一scoreだけでなく、unsupported spanとして局所化できる可能性がある点である。

長所:

- 非生成型encoderで、first-stage specialized verifierに適する。
- unsupported spanを直接返せる。
- 小型でRTX 4090に対するruntime負荷が低いと期待できる。
- Apache 2.0。

懸念:

- 公開benchmarkの優位性はSGOKB固有corpusでの優位性を保証しない。
- code-agent等の公開結果はSGOKBのprose groundingにそのまま外挿できない。
- current Reference Workstationの標準Transformers環境とdependency rangeが競合する可能性があり、専用venvが望ましい。

References:

- https://huggingface.co/KRLabsOrg/lettucedect-v2-mmbert-base
- https://github.com/KRLabsOrg/LettuceDetect

### 3.3 LettuceDetect v2 Qwen 2B

`KRLabsOrg/lettucedect-v2-qwen-2b`はQwen3.5-2Bを基盤とするgenerative hallucination span detectorで、unsupported spanにcategory/subcategoryを付与してstructured JSONを返す。

長所:

- binary verdictだけでなく、unsupported_addition / contradiction等のtypeを返せる。
- span localizationとtyped outputを一度に得られる。
- 公式RAGTruth系結果ではmmBERT baseより高いexample-level performanceが報告されている。

懸念:

- 生成型であるため、MiniCheck/mmBERTよりdeterminism・output parsing・runtime complexityが高い。
- SGOKBは既にPhi-4というgenerative bounded judgeをsecond stageに持つため、first-stageまで生成型にするとcomponent diversityが低下する。
- 採用時はtemperature 0、strict structured output、repeatability testを追加条件とする。

Reference:

- https://huggingface.co/KRLabsOrg/lettucedect-v2-qwen-2b

### 3.4 Granite Guardian 4.1 8B

IBM Granite Guardian 4.1 8Bは2026年のgroundedness / hallucination / BYOC judgeである。

ただしSGOKBの今回の比較では初期3候補に入れない。

理由:

- 8B generative judgeであり、軽量specialized first-stage verifierよりPhi-4側のindependent judge代替候補に近い。
- current G-18 architectureではfirst-stage verifierとsecond-stage bounded judgeの性質を分けることに価値がある。
- 3候補すべてがGateを満たさない場合のsecond-line research candidateとして保持する。

Reference:

- https://github.com/ibm-granite/granite-guardian

---

## 4. Candidates to benchmark

Initial comparison set:

```text
A. MiniCheck RoBERTa-large
B. LettuceDetect v2 mmBERT-base
C. LettuceDetect v2 Qwen-2B
```

Granite Guardian等は初回比較の結果が不十分な場合にのみ追加調査する。

この比較でG-18 Frozen semantics、Material requirements、terminal policy、renderer policy、Phi-4 bounded judge contractは変更しない。

---

## 5. Benchmark principle

一般公開benchmarkの順位ではなく、SGOKB固有のfailure costを優先する。

最重要failureは:

```text
unsupported claim -> supported candidate
```

である。

したがってselection priorityは次の順とする。

1. critical negative / G-12 replay false-positive = 0
2. high-overlap unsupported additionをrejectできる
3. negation / wrong predicate / causal-temporal overclaimをrejectできる
4. faithful paraphraseをacceptできる
5. required positive casesを維持できる
6. positive recall
7. offline reproducibility / exact revision pinning
8. dependency isolation
9. latency / VRAM / operational complexity
10. diagnostic usefulness（span localization等）

平均F1が高くてもcritical false-positiveを出すcandidateは採用しない。

---

## 6. Evaluation corpus

最低限、既存G-20 corpusを変更せずbaselineとして使用する。

```text
benchmark/n04g20-source-fact-verifier-v1.json
```

既存required Gate:

```text
required negative/replay false-positive = 0
required positive supported = 2 / 2
```

追加caseを作る場合は、少なくとも以下を含める。

- supported faithful paraphrase
- lexical overlapが高いunsupported extra detail
- wrong predicate
- negation flip
- temporal / causal overclaim
- concept説明への余分な理論追加
- atomic claim内部のpartially supported wording
- entity/relationship substitution

既存G-20 corpusのlabelをcandidate結果を見て変更してはならない。

---

## 7. Candidate-specific initial decision surfaces

結果を見た後に都合よくthresholdを選ばないため、初回比較のdecision surfaceを事前固定する。

### MiniCheck

```text
score >= 0.50 -> SUPPORTED_CANDIDATE
score < 0.50  -> no PASS
```

G-20の既存candidate thresholdを維持する。

### LettuceDetect v2 mmBERT

初回比較ではnative token classificationを使用する。

```text
unsupported/hallucinated answer token spanが1つ以上 -> no PASS
unsupported spanなし                            -> SUPPORTED_CANDIDATE
```

追加confidence thresholdは初回Gate結果を見て後付けしない。

### LettuceDetect v2 Qwen 2B

```text
hallucinated_spansが1件以上 -> no PASS
hallucinated_spansが空      -> SUPPORTED_CANDIDATE
```

temperature 0、固定prompt、strict JSON解析、同一input repeatabilityを必須とする。

---

## 8. Threshold calibration rule

Candidate固有threshold調整が必要になった場合、formal Gate corpusそのものへfitさせてはならない。

threshold tuningを行う場合は:

```text
calibration/dev set
  ↓ threshold decision freeze
immutable holdout Gate
```

へ分離する。

holdout結果を見てthresholdを再調整した場合、そのholdoutは以後formal holdoutとして使用しない。

---

## 9. Success scenarios and predetermined handling

### S1 — MiniCheckが明確に勝つ

条件例:

- critical false-positive = 0
- required positives PASS
- 他候補よりpositive recall / reproducibilityで同等以上
- Reference Workstationでexact runtime固定可能

処理:

1. MiniCheckを正式specialized verifierに選定。
2. G-21VをComplete。
3. G-21Rで専用verifier runtime / source / model snapshot / dependency lockを構築。
4. Reference Workstation offline replayを実施。
5. PASS後にG-21をComplete / Frozenへ移行。

これは最小変更経路である。

### S2 — LettuceDetect v2 mmBERTが明確に勝つ

条件例:

- critical false-positive = 0
- required positives PASS
- MiniCheckよりSGOKB adversarial caseで良好
- offline exact revision固定可能

処理:

1. `SourceFactVerifierAdapter`の実装candidateをmmBERTへ変更。
2. G-18 semanticsは変更しない。
3. verifier profile / benchmark result / testsを更新。
4. G-20 replayを新candidateで再run。
5. G-21Rで隔離runtimeを固定。
6. local proof PASS後にG-21 Freeze。

### S3 — LettuceDetect v2 Qwen 2Bだけが安全Gateを満たす

処理:

自動採用しない。追加条件を満たす場合のみ採用する。

追加条件:

- temperature 0でrepeatability PASS
- strict output schema / parser mismatchなし
- same-input複数runでverdict安定
- critical false-positive = 0
- required positives PASS
- runtimeがRTX 4090上で運用可能

すべて満たすならgenerative verifierとして採用可能とする。満たさない場合はG-21Vをblockedのまま追加candidate調査へ進める。

### S4 — MiniCheckとmmBERTが安全性で同率

Tie-break order:

1. higher positive recall
2. fewer indeterminate/runtime failures
3. exact offline pinningの容易さ
4. dependency isolationの容易さ
5. lower latency / VRAM
6. なお同等なら既存evidenceが多く変更量の少ないMiniCheck

「新しいモデルだから」という理由だけでは切り替えない。

### S5 — 複数candidateがPASSし、片方がspan diagnosticで優れる

原則として正式verifierは1つにする。

span情報に運用価値があっても、安全Gateが同等ならdiagnostic用途とformal authorityを分離できる。

例:

```text
formal verdict: MiniCheck
optional diagnostics: LettuceDetect span output
```

ただしformal decision pathへ2モデルensembleを追加する場合はcomplexity増加として別decisionを要求する。

---

## 10. Failure scenarios and predetermined handling

### F1 — 全candidateがcritical false-positiveを1件以上出す

処理:

- threshold / rubricをその場で緩めない。
- G-21V = BLOCKED。
- G-21 / G-22もblocked維持。
- failure categoryを分析し、追加candidateを調査する。
- 必要ならGranite Guardian等をsecond-line candidateとして評価する。
- deterministic decompositionで防げるfailureならV3/V4境界の実装改善を検討するが、G-18 semantic changeが必要なら明示的にreopenする。

### F2 — false-positiveは0だがpositiveをほぼrejectする

これは安全だが実用性不足である。

処理:

- required positive Gateを満たさないcandidateは採用しない。
- formal N-04でMaterial不足を大量発生させるcandidateを「安全だから」と採用しない。
- calibrationが妥当ならdev/holdout分離の上で検討し、Gate corpusへ直接threshold fitしない。

### F3 — Public benchmarkでは良いがSGOKB corpusではMiniCheckより悪い

処理:

SGOKB corpusを優先する。

公開benchmarkは参考情報であり、SGOKBのcritical failure costを上書きしない。

### F4 — Reference Workstationでdependency conflictが発生する

処理:

標準venvを変更しない。

正式verifier専用runtimeを隔離する。

```text
.local/n04-v3/runtime/verifier/
  venv/
  source/
  models/
  hf-cache/
  lock/
```

本体runtimeとverifier runtimeのdependencyを分離する。

### F5 — exact source/model revisionを取得・固定できない

処理:

- `main`やlatestへのsilent substitution禁止。
- 別revisionを使う場合は新candidateとして再評価。
- offline proof不能ならG-21 Freeze禁止。

### F6 — GitHub ActionsとReference Workstationで結果が異なる

処理:

Reference Workstation formal proofをauthorityとする。

差異原因を以下で調査する。

- source revision
- model snapshot
- PyTorch/CUDA
- Transformers/tokenizer
- preprocessing/chunking
- precision/device
- random/generative settings

一致しないままFreezeしない。

### F7 — Candidate benchmarkはPASSしたがG-22 formal use caseで再びunsupported claimがrenderされる

処理:

- G-22 FAIL evidenceを保存。
- N-04をCompleteにしない。
- rubricを緩めない。
- failureがverifier由来ならG-21V/G-21Rへ戻る。
- failureがatomicity/role/material等の別stage由来なら該当stageを明示的にreopenする。

### F8 — span detectorがatomic claimの一部だけunsupportedとする

処理:

partial salvageは禁止する。

```text
atomic unit内にunsupported spanあり -> unit全体 no PASS
```

G-18のatomic-unit fail-closed方針を維持する。

### F9 — Model output/parser mismatchが発生する

処理:

- parser側で推測補完しない。
- schema mismatch / malformed outputはno PASSまたはSYSTEM_FAILURE。
- Qwen等generative candidateではstructured-output preflightを正式Gateにする。

### F10 — どのcandidateも決定的に優位でない

処理:

無理にwinnerを選ばない。

1. critical safety Gateを満たすcandidateだけを残す。
2. positive recall / reproducibility / complexityで追加差分testを行う。
3. それでも同等なら最小変更candidateを選ぶ。
4. safety Gate自体で同率FAILならG-21Vをblockedとする。

---

## 11. Runtime preparation policy after winner selection

Winner選定後にのみG-21Rを実施する。

G-21Rでは:

1. exact source revision取得。
2. exact model snapshot取得。
3. dedicated venv構築。
4. dependency lock保存。
5. network-enabled preparation完了。
6. その後network-independent / local-files-only modeでformal replay。

「準備時のdownload」と「formal proof時のoffline execution」を明確に分離する。

preparation前に存在していなかったこと自体はfailureではない。重要なのは、formal runtimeが固定され、offline再現できることである。

---

## 12. Exit criteria

G-21V Complete条件:

```text
candidate comparison executed
+ critical negative/replay false-positive = 0 for selected candidate
+ required positive Gate PASS
+ winner selection rationale recorded
+ exact source/model identity selected
+ candidate-specific decision surface frozen
+ no post-result rubric relaxation
```

G-21V完了だけではG-21はFrozenにならない。

次にG-21RでReference Workstation runtimeを準備し、offline local proofを取得する。

---

## 13. Updated dependency chain

```text
G-20R Complete / PASS
  ↓
G-21 freeze candidate Prepared
  ↓
G-21V Verifier Candidate Evaluation
  ↓ winner selected
G-21R Reference Workstation verifier runtime preparation + offline proof
  ↓ PASS only
G-21 Complete / Frozen
  ↓
G-22 Formal v3 Re-Acceptance
  ↓
N-04 Complete only if 3/3 formal PASS
  ↓
N-05
```

---

## 14. Protected boundaries

G-21Vでは次を変更しない。

- canonical 52-table model
- Object ID / Version identity
- Source / Evidence / Provenance
- MCP read-only boundary
- Context Builder budget / purpose selection
- Similarity ranking algorithm
- N-03 fixed dataset
- N-06 retrieval-quality metrics
- G-12 historical failed evidence
- G-18 Frozen grounded-generation semantics
- Material requirements
- retry / terminal / renderer semantics
- G-20/G-20R historical evidence

Verifier candidate selectionのために既存failure evidenceやGateを弱めてはならない。
