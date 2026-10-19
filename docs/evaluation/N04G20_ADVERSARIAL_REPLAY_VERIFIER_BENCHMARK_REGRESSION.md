# N-04G-20 Adversarial / Replay / Verifier Benchmark / Regression

更新日: 2026-10-19

- Status: **In Progress**
- Phase: `Phase N — Test / Evaluation / Acceptance`
- Parent Task: `N-04 [P0] 3つの代表AI利用ケースを受入試験する`
- Design Freeze: `docs/decisions/N04G18_POST_G12_GROUNDED_GENERATION_V3_DESIGN_FREEZE.md`
- Implementation: `docs/evaluation/N04G19_FROZEN_REMEDIATION_DESIGN_IMPLEMENTATION.md`
- Branch: `phase-n/n04g20-adversarial-verifier-regression`

## Scope

G-18 Frozen semantics / G-19 implementationについて以下をGateする。

- G-12 failure replay
- adversarial false-acceptance regression
- provider/application schema preflight
- source-fact specialized verifier candidate benchmark
- full pytest
- Ruff
- git diff --check

Verifier candidateのG-21必要条件は:

```text
required negative/replay false-positive = 0
```

である。G-20中に実装欠陥を修正してよいが、G-18 Frozen semanticsは緩和しない。

## Findings during preflight

G-19 output parserには、providerへ渡すJSON Schemaでは表現されていないcross-item uniqueness ruleが存在した。

```text
duplicate block_id
duplicate unit_id
duplicate presentation_role
```

このままではproviderが構造的に許容したoutputをapplication parserだけがrejectし得るため、G-12 Case 3と同型のprovider/parser hidden mismatch riskとなる。

G-20では意味制約を削除せず、これらをGrounding Validation `V0`の明示的SGOKB identity invariantへ移動した。

```text
provider JSON Schema == application parse surface
        ↓
V0 SGOKB cross-item identity validation
```

これによりprovider/parserの構造契約を一致させつつ、duplicate ID等は引き続きfail-closedでrejectする。

## Verifier benchmark corpus

`benchmark/n04g20-source-fact-verifier-v1.json`を追加した。

含むbucket:

- supported direct claim
- faithful paraphrase
- G-12 Case 1 unsupported atomic claims
- G-12 Case 2 unsupported atomic claims
- high lexical overlap + unsupported material detail
- supported subject + wrong predicate
- negation flip
- temporal/causal embellishment
- threshold probes

MiniCheck benchmark runner:

```text
benchmark/tools/n04g20_minicheck_benchmark.py
```

Exact checkpoint revision / threshold profileの最終FreezeはG-21で行う。

## Execution status

GitHub Actions一時workflowでengineering checksとMiniCheck RoBERTa-large diagnostic benchmarkを実行する。

Reference WorkstationへのRemote Desktop Commander経路は月次利用上限に達しているため、このチャットからReference Workstation固有のlocal runtime実行は利用できない。GitHub Actions上のverifier測定はcandidate screening evidenceとして扱い、local-only formal runtimeの証明とは扱わない。
