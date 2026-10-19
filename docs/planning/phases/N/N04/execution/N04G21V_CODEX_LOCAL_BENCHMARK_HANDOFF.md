# N-04G-21V Codex Local Benchmark Handoff

更新日: 2026-10-19

- Task: `N-04G-21V [P0] Specialized Source-Fact Verifier Candidate Evaluation`
- Branch: `phase-n/n04g21v-verifier-benchmark`
- Purpose: Reference Workstation RTX 4090上で3候補を同一SGOKB corpusに対して実測し、事前固定済みdecision ruleでG-21Rへ渡す正式候補を選ぶ。
- Decision authority: `docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md`
- Corpus: `benchmark/n04g20-source-fact-verifier-v1.json`
- Runner: `benchmark/tools/n04g21v_verifier_benchmark.py`
- Comparator: `benchmark/tools/n04g21v_compare_results.py`

## 1. Non-negotiable rules

1. G-20 corpusのlabel / required flagを変更しない。
2. MiniCheck threshold `0.50`を変更しない。
3. mmBERTはnative binary token verdictをそのまま使用し、後付けconfidence thresholdを加えない。
4. Qwen 2Bは`hallucinated_spans`の有無をそのまま使用し、temperature 0相当のgreedy decode、固定prompt、同一input 3回repeatabilityを使う。
5. candidate結果を見てからdecision surfaceを変更しない。
6. SGOKB標準venvを変更しない。比較用venv/cacheは`.local/n04-v3/runtime/g21v/`以下へ隔離する。
7. benchmark中にmodel repo `main`が変化した場合、当該runを無効として再実行する。MiniCheck runnerは前後revision一致をmachine-checkする。
8. Webの作品知識や外部retrievalをverdictへ追加しない。
9. benchmark failureをPASSへするためのmanual verdict overrideは禁止。
10. `.local`の生証跡を保持し、tracked resultにはrunnerが生成したJSONをそのまま使用する。

## 2. Candidates

```text
A. minicheck-roberta-large
   repo: lytang/MiniCheck-RoBERTa-Large
   source: Liyan06/MiniCheck
   source revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
   decision: support_probability >= 0.50

B. lettucedect-v2-mmbert-base
   repo: KRLabsOrg/lettucedect-v2-mmbert-base
   decision: unsupported answer-token span >= 1 -> UNSUPPORTED

C. lettucedect-v2-qwen-2b
   repo: KRLabsOrg/lettucedect-v2-qwen-2b
   decision: hallucinated_spans >= 1 -> UNSUPPORTED
   repeatability: same input x3
```

Hugging Face revisionはrun開始時にAPIからfull SHAを解決し、そのrunではSHA pinして読み込む。MiniCheck packageだけはupstream sourceが`revision='main'`を内部指定するため、run前後のmain SHA一致を必須とし、最終offline pinningはG-21Rで行う。

## 3. Environment isolation

Reference WorkstationのSGOKB checkoutを最新化し、このbranchをcheckoutする。

比較用runtimeの推奨配置:

```text
.local/n04-v3/runtime/g21v/
  venv/
  hf-cache/
  nltk-data/
  runs/<run_id>/
```

SGOKB標準venvへMiniCheck/NLTK/モデル依存を追加しない。

現在確認済みReference Workstation baseline:

```text
Python            3.10.6
PyTorch           2.6.0+cu124
CUDA build        12.4
Transformers      5.20.1
huggingface_hub   1.33.0
tokenizers        0.23.3
GPU               RTX 4090 24GB
```

新規benchmark venvでは、可能な限りこのbaselineを再現する。MiniCheckに必要な`minicheck` exact source commit、NLTK、必要ならaccelerate等を追加する。依存解決で上記baselineを変更する必要がある場合は勝手に標準venvを変更せず、benchmark venv内だけで解決し、exact package lockを保存する。

LettuceDetect READMEの`transformers<5`注意書きはEuroBERT remote-code models向けであり、今回のv2 mmBERTにそのまま適用しない。v2 mmBERT model configはTransformers 5系で生成されている。Qwen 2BもTransformers 5系model card例を持つ。実際のcompatibilityはこのbenchmark venvで確認する。

## 4. Required setup evidence

run root例:

```text
.local/n04-v3/runtime/g21v/runs/<run_id>/
```

最低限保存:

```text
pip-freeze.txt
python-version.txt
nvidia-smi.txt
git-start.txt
minicheck-roberta-large.json
lettucedect-v2-mmbert-base.json
lettucedect-v2-qwen-2b.json
comparison.json
```

可能ならmodel cache snapshot/revision一覧も保存する。

## 5. NLTK setup

MiniCheck sourceは`nltk.tokenize.sent_tokenize`を使用するため、benchmark venvにNLTKと必要tokenizer dataを用意する。

NLTK versionとdownloaded resource名を証跡へ記録する。ネットワーク利用はG-21V candidate selectionでは許容する。G-21R final proofでは選定candidateを事前配置し、offline/local-files-onlyへ切り替える。

## 6. Benchmark execution

PowerShell例。実際のvenv Python pathはCodexが作成したものへ置き換える。

```powershell
$Py = ".local\n04-v3\runtime\g21v\venv\Scripts\python.exe"
$Corpus = "benchmark\n04g20-source-fact-verifier-v1.json"
$Run = ".local\n04-v3\runtime\g21v\runs\<run_id>"
$Cache = ".local\n04-v3\runtime\g21v\hf-cache"

& $Py benchmark\tools\n04g21v_verifier_benchmark.py `
  --candidate minicheck-roberta-large `
  --corpus $Corpus `
  --cache-dir $Cache `
  --output "$Run\minicheck-roberta-large.json"

& $Py benchmark\tools\n04g21v_verifier_benchmark.py `
  --candidate lettucedect-v2-mmbert-base `
  --corpus $Corpus `
  --cache-dir $Cache `
  --output "$Run\lettucedect-v2-mmbert-base.json"

& $Py benchmark\tools\n04g21v_verifier_benchmark.py `
  --candidate lettucedect-v2-qwen-2b `
  --qwen-repeats 3 `
  --corpus $Corpus `
  --cache-dir $Cache `
  --output "$Run\lettucedect-v2-qwen-2b.json"

& $Py benchmark\tools\n04g21v_compare_results.py `
  --results `
    "$Run\minicheck-roberta-large.json" `
    "$Run\lettucedect-v2-mmbert-base.json" `
    "$Run\lettucedect-v2-qwen-2b.json" `
  --output "$Run\comparison.json"
```

各candidateは別processで実行し、前candidateのVRAM allocationが次candidateのpeak measurementへ混入しないようにする。

## 7. Required Gate

全candidate共通:

```text
required negative / G-12 replay false-positive = 0
required positive supported                 = 2 / 2
indeterminate                               = 0
```

Qwen 2B追加Gate:

```text
all same-input x3 outputs structurally identical = true
JSON/schema parse failure                       = 0
```

一つでもrequired negativeをSUPPORTEDにしたcandidateは、平均性能が高くても不採用。

## 8. Result handling

Comparatorの`selected_candidate_for_g21r`を機械的な第一候補とするが、以下をCodexがclaim-levelで確認する。

- false-positive IDが本当に0か。
- required positive 2件が両方SUPPORTEDか。
- positive recall / negative specificityの計算がraw casesと一致するか。
- Qwenの場合、3回出力が一致しているか。
- resolved model revisionが各runに記録されているか。
- runtime/package/GPU identityが記録されているか。

比較結果が事前decision matrixと矛盾する場合、Comparatorを都合よく変更せずG-21VをBLOCKEDとして報告する。

## 9. Expected dispositions

### 1候補以上がGate PASS

- comparatorのtie-break順でG-21R candidateを1つ選ぶ。
- `N-04G-21V = Complete / candidate selected`へ更新する。
- `N-04G-21R = NEXT`へ更新する。
- G-21自体はまだ`Prepared / BLOCKED before final Freeze`のまま。
- G-22もblockedのまま。

### 0候補がGate PASS

- `N-04G-21V = BLOCKED / no eligible candidate`。
- threshold、corpus label、required Gateを緩めない。
- Granite Guardian等のsecond-line候補調査へ進むためのfailure evidenceを保存する。

## 10. Persistent repository evidence after run

生証跡は`.local`に残す。

tracked evidenceとして以下を追加する。

```text
benchmark/results/n04g21v-minicheck-roberta-large-reference-workstation.json
benchmark/results/n04g21v-lettucedect-v2-mmbert-base-reference-workstation.json
benchmark/results/n04g21v-lettucedect-v2-qwen-2b-reference-workstation.json
benchmark/results/n04g21v-verifier-comparison-reference-workstation.json
docs/evaluation/N04G21V_VERIFIER_CANDIDATE_EVALUATION.md
```

`docs/evaluation/N04G21V_VERIFIER_CANDIDATE_EVALUATION.md`には、各candidateのrevision、Gate結果、positive recall、negative specificity、elapsed time、peak VRAM、runtime/package lock要約、selected candidate、selection理由を記録する。

## 11. Regression after evidence integration

結果をtracked evidenceへ反映した後、最低限:

```text
python -m pytest tests/test_n04g20_adversarial_regression.py -q
python -m pytest tests/test_n04g21_harness_freeze_candidate.py -q
python -m pytest -q
python -m ruff check .
git diff --check
```

を実行する。

G-21Vの比較結果を理由にG-18 Frozen semantics、Material Gate、terminal/render policyを変更しない。

## 12. Final Codex report

最後に以下を報告する。

1. 3candidateのexact model revision。
2. runtime/package versions。
3. candidateごとのrequired negative FP / required positive / recall / specificity。
4. candidateごとのelapsed time / peak VRAM。
5. Qwen repeatability / parser result。
6. selected candidateまたは`no eligible candidate`。
7. decision matrixに照らした選定理由。
8. G-21V/G-21R/G-21/G-22/N-04/N-05の最終状態。
9. commit / PR / main反映状況。
