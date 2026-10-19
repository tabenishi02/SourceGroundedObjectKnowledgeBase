# N-04G-21R Selected Verifier Runtime Preparation / Local Proof

更新日: 2026-10-19

- Status: **Prepared / awaiting Reference Workstation offline execution**
- Parent: `N-04G-21 [P0] v3 Acceptance / Reference Workstation Harness Freeze`
- Selected verifier: `MiniCheck RoBERTa-large`
- Selection evidence: `docs/evaluation/N04G21V_VERIFIER_CANDIDATE_EVALUATION.md`
- Execution handoff: `docs/planning/N04G21R_CODEX_OFFLINE_PROOF_HANDOFF.md`
- Offline runner: `benchmark/tools/n04g21r_minicheck_offline_proof.py`

## Decision

G-21VでMiniCheckが事前固定Gate/tie-breakにより選定されたため、G-21Rではcandidate selectionを再実施しない。

G-21Rの目的は次の2点に限定する。

1. selected MiniCheck runtimeをReference Workstation上でexact revision/package/cache identityとして固定する。
2. preparation完了後、network-independent状態でG-20 source-fact verifier corpusを再生し、frozen threshold 0.50のGateを再現する。

G-18 semantics、corpus label、threshold、Material/terminal/render policy、Phi-4 compositionは変更しない。

## Formal MiniCheck identity

```text
source repository: Liyan06/MiniCheck
source revision: b58b9fa69acbd1015ec970fa65dd752413a053d2
model repository: lytang/MiniCheck-RoBERTa-Large
model revision: 74c8919647e61ed0f71bc177d94f10930f090068
threshold: >= 0.50
max_model_length: 512
chunk_size: 400
batch_size: 16
device: cuda:0
formal network policy: offline/local-files-only
```

## Runtime isolation

Formal verifier runtime is separate from the standard SGOKB venv.

```text
.local/n04-v3/runtime/verifier/
```

Standard SGOKB venv package inventory must remain unchanged before/after G-21R.

## Offline boundary

Preparation and proof are distinct phases.

Preparation may materialize exact required artifacts. After the offline boundary is declared:

- no download;
- no package install/update;
- no revision/ref change;
- no threshold change;
- no corpus/test edit;
- no alternate runtime/model substitution.

The proof process sets Hugging Face/Transformers/Datasets offline environment variables and blocks Python socket connections. Any required artifact unavailable at that point is a BLOCKED/FAIL condition, not a reason to fetch it during proof.

## MiniCheck proof Gate

Required:

```text
exact source revision                         PASS
source checkout clean                        PASS
HF refs/main == exact model revision         PASS
exact snapshot locally present               PASS
NLTK punkt / punkt_tab locally present       PASS
Python socket network attempts               0
required negative false-positive             0
required positive supported                  2 / 2
threshold                                    0.50 unchanged
standard SGOKB venv                          unchanged
```

The G-21V comparison is recorded but not itself a formal Gate. Verdict/score divergence from G-21V must be investigated and documented; it must not be manually overwritten.

## G-21R outcomes

### A. MiniCheck offline proof FAIL/BLOCKED

```text
G-21R = BLOCKED or FAIL
G-21 = Prepared / BLOCKED before final Freeze
G-22 = blocked
N-04 = Failed / not Complete
N-05 = blocked
```

Do not relax any Gate. Preserve failure evidence.

### B. MiniCheck offline proof PASS, other G-21 preflight FAIL

```text
G-21R = Complete / PASS
G-21 = still BLOCKED with exact remaining preflight blocker
G-22 = blocked
```

MiniCheck proof need not be discarded, but G-21 cannot be Frozen.

### C. MiniCheck offline proof PASS and all remaining G-21 preflight/engineering Gates PASS

Update the freeze candidate consistently:

```text
G-21R = Complete / PASS
G-21 = Complete / Frozen
G-22 = NEXT / unblocked
N-04 = Failed / not Complete
N-05 = blocked
```

Freeze update must include exact Reference Workstation runtime lock, local reproduction evidence, resolved candidate file hashes, and empty `unresolved_before_freeze`.

## Remaining G-21 preflight after verifier proof

- generator/Phi-4 neutral structured-output smoke;
- MCP/Harrier/Qdrant identity and integrity;
- MCP stdio initialization;
- tracked freeze file/schema identities;
- evaluation DB/N-03 object identity;
- focused grounding/replay tests;
- G-21/G-21R contract tests;
- full pytest;
- repository-wide Ruff;
- `git diff --check`.

## Historical evidence retention

G-12, G-20/G-20R, G-21V, prior G-21 BLOCKED evidence, and failed G-21R attempts are immutable historical evidence and must not be deleted or overwritten.
