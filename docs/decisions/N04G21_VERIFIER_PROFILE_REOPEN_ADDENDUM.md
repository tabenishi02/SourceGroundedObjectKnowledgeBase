# N-04G-21 Verifier Profile Reopen Addendum

更新日: 2026-10-19

- Status: **Accepted addendum / G-21 remains BLOCKED**
- Applies to: `docs/decisions/N04G21_V3_ACCEPTANCE_REFERENCE_WORKSTATION_HARNESS_FREEZE.md`
- New verifier selection authority: `docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md`

---

## 1. Reason for addendum

G-21 freeze candidate作成後、Reference Workstationで実機inventoryを取得した結果、標準venvにはMiniCheck / NLTKが未導入であり、指定MiniCheck model snapshot / cache refも未配置であることが確認された。

したがって、旧G-21文書の「MiniCheck candidateを変更せずexact local proofへ進む」という想定は、そのままでは実行不能である。

さらに2026年時点のspecialized grounding verifierを再調査した結果、LettuceDetect v2 mmBERT / Qwen 2B等、G-20時点で比較していなかった新しいcandidateが存在することが確認された。

G-21はまだfinal Freeze前であり、G-18は特定製品ではなく`specialized source-fact verifier`というadapter roleとfail-closed compositionをFrozen semanticsとしている。

よって、formal runtimeを新規構築する前にcandidate selectionを再開する。

---

## 2. Superseded portions of the original G-21 candidate document

元文書の以下のMiniCheck-specific部分は、historical freeze-candidate proposalとして保持するが、**current execution instructionとしては本addendumとG-21V planが優先する**。

- Section 7: `Specialized source-fact verifier candidate`
- Section 8: MiniCheck固有のcomposition表記
- Section 14 items 9-13: MiniCheck固有preflight
- Section 16: `候補を変更せず`MiniCheck local proofへ進む指示
- Section 17: MiniCheck exact runtime verificationだけを残作業とするassessment

これらは削除しない。G-21 candidateがどのように準備されたかを示すhistorical design evidenceとして保持する。

---

## 3. Unchanged G-21 candidate portions

次は引き続き有効であり、G-21Vで変更しない。

- G-18 Frozen contracts / semantic roles
- stable Object IDs
- Material profiles
- generator profile candidate
- Phi-4 bounded semantic judges
- provider output-v2 schema / hash
- retry upper bound
- terminal policy
- renderer authorization
- evidence tree concept
- formal 3-case rubric
- canonical invariance / integrity requirements
- engineering Gates

---

## 4. Current verifier state

MiniCheck is now:

```text
provisional baseline candidate
not final frozen verifier
```

Initial comparison set:

```text
A. MiniCheck RoBERTa-large
B. LettuceDetect v2 mmBERT-base
C. LettuceDetect v2 Qwen-2B
```

Candidate result handling is frozen before execution in:

```text
docs/decisions/N04G21V_SOURCE_FACT_VERIFIER_CANDIDATE_EVALUATION_PLAN.md
```

---

## 5. Current task dependency

```text
G-21 freeze candidate Prepared / not Frozen
  ↓
G-21V verifier candidate evaluation
  ↓ winner selected
G-21R selected verifier runtime preparation + Reference Workstation offline proof
  ↓ PASS only
G-21 Complete / Frozen
  ↓
G-22 Formal v3 Re-Acceptance
```

Current status remains:

```text
N-04G-21  Prepared / BLOCKED before final Freeze
N-04G-21V Planned / NEXT
N-04G-21R Blocked by G-21V
N-04G-22  Blocked by G-21
N-04       Failed / not Complete
N-05       blocked
```

---

## 6. Non-relaxation rule

Verifier candidate再選定は既存Gateを弱めるために行うものではない。

Selected candidate must still satisfy:

```text
critical/G-12 replay false-positive = 0
required positive Gate PASS
fail-closed disagreement handling
offline exact-runtime proof on Reference Workstation
```

結果を見てrubric、required negatives、Material requirements、Reference Workstation proof requirementを緩めてはならない。
