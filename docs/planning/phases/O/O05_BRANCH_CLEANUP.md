# O-05 — Branch Cleanup

Updated: 2026-10-25

- Task: `O-05 [P1] 不要branchを削除する`
- Status: **BLOCKED — deletion safety verified, remote ref deletion unavailable in current execution environment**
- Repository: `tabenishi02/SourceGroundedObjectKnowledgeBase`
- Current authority branch: `main`
- Audit starting `main`: `fd73101532e8903ce568e4299d8966743a61595a`

## Purpose

O-04で全remote branch historyを`main`へ統合した後、不要なremote branchを削除してrepositoryのactive branch surfaceを`main`中心へ整理する。

削除は履歴を失わないことを最優先とし、branch名だけを根拠に実施しない。

## Live branch inventory

2026-10-25のlive GitHub inventoryではremote branchは **36本**。

- keep: `main`
- cleanup candidate: **35本**
- protected candidate branch: **0本**
- open pull request: **0件**

Cleanup candidate:

```text
docs/planning-structure-reorganization
n06-retrieval-vector-quality
n07-failure-recovery
n07-r01-composite-backup-restore
phase-n/n04g14-atomic-role-boundary
phase-n/n04g16-semantic-validation
phase-n/n04g18-post-g12-design-freeze
phase-n/n04g19-v3-grounding-implementation
phase-n/n04g20-adversarial-verifier-regression
phase-n/n04g20r-ruff-baseline
phase-n/n04g21-v3-acceptance-harness-freeze
phase-n/n04g21r-offline-proof
phase-n/n04g21v-verifier-benchmark
phase-n/n04g21v-verifier-candidate-evaluation-plan
phase-n/n04g22-failure-investigation
phase-n/n04g22-formal-reacceptance
phase-n/n04g23-two-stage-generation-design
phase-n/n04g23a-atomicity-role-gold-benchmark
phase-n/n04g23ae1-47-gold-responsibility-map
phase-n/n04g23ae2-v4-v2-responsibility-boundary
phase-n/n04g23ae3-structured-proposition-contract
phase-n/n04g23ae4-role-provenance-matrix
phase-n/n04g23ae5-residual-classifier-design
phase-n/n04g23ae6-47-gold-desk-replay
phase-n/n04g23ae7-integration-unblock
phase-n/n04g23ae-gate-responsibility-decomposition
phase-n/n04g23ar-judge-candidate-evaluation
phase-n/n04g23b-next-chat-handoff
phase-n/n04g25a-development-classifier-benchmark
phase-n-closure-audit
r2-05-semantic-regression-review
r2-06-similarity-regression-review
r2-07-implementation
r2-08-search-quality
r2-09-runner-wiring-remediation
```

## Safety verification

O-04では全remote branch historyを`main`へ統合し、最終統合commit `77d79ccac1017f167736c742ac199858a3a010a7`を作成した。現在のbranch inventoryはO-04時点のcleanup対象集合から新規branchが増えていない。

O-05開始時に独立系列の代表tipをlive GitHub compareで再確認した。

| Branch | HEAD | Compare to current `main` | Merge base |
|---|---|---|---|
| `docs/planning-structure-reorganization` | `0f07fd4b02e98bf07497d445199a3f89975f1d0f` | `behind_by=0`; main ahead 345 | branch HEAD itself |
| `phase-n-closure-audit` | `fa15e29a58a91cd5104025f0fdcc7d28f394c830` | `behind_by=0`; main ahead 20 | branch HEAD itself |
| `n07-r01-composite-backup-restore` | `9cda43e9303488d2b0905f61fa3dbbed4f03a4fb` | `behind_by=0`; main ahead 26 | branch HEAD itself |
| `n06-retrieval-vector-quality` | `394db948b97d5396222cf157600da45c28a6c505` | `behind_by=0`; main ahead 41 | branch HEAD itself |
| `r2-09-runner-wiring-remediation` | `30f6bba79d2447d0708fa21f3313239d971bc4d6` | `behind_by=0`; main ahead 60 | branch HEAD itself |
| `phase-n/n04g25a-development-classifier-benchmark` | `f3b400c8106fc1d5d6db1808f3d7502ea98d3696` | `behind_by=0`; main ahead 275 | branch HEAD itself |

これらはplanning再編、Phase N closure、N07、N06、R2、N04の各独立系列のtipを代表する。O-04の全branch統合確認と合わせ、35本すべてについて削除後に失われる未統合historyはないと判定する。

## Deletion policy

削除対象は上記35本すべて。

次は削除しない。

- `main`
- 今後O-05完了前に新規作成されたbranch（再監査が必要）
- future auditで`main`に含まれないunique commitが検出されたbranch

削除後もcommit objectと`main`側の統合historyは保持される。historical FAIL / BLOCKED evidenceはbranchではなく`main`上のcommit / document / benchmark resultで保持する。

## Execution blocker

現在このChatGPT sessionに接続されているGitHub action setには、branchの検索・作成・ref更新はあるが、**remote branch / Git refを削除するmutationが提供されていない**。

そのため、安全性監査は完了したが、35本のremote ref削除そのものはこのsessionから実行できない。branchを`main`へforce-moveして削除済みと扱うことはしない。

O-05は削除が実行されるまで **Completeにしない**。

## Required final action

branch/ref deletionが可能なGitHub API / Git client環境で、上記35本を削除する。その直後にlive branch inventoryを再取得し、次を確認する。

```text
remote branches = 1
remaining branch = main
open PR = 0
main history unchanged
```

削除後に本書と`PHASE_O_STATUS.md`を`Complete`へ更新し、NextをO-06へ進める。
