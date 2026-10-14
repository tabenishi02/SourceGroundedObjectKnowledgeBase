# Source Grounded Object Knowledge Base — Phase K Closure Audit

更新日: 2026-10-14

- Status: **Complete**
- Phase: `Phase K — SGOKB / UPDS連携試験`
- Scope: K-01〜K-04の完了状態、SGOKB→UPDS契約、Phase Lへの引継ぎ
- Previous phase: `Phase J — MCP Knowledge Access Layer`
- Next phase: `Phase L — 旧Prototype移行・削除`
- Next task: `L-01 [P0] Fragment table / code / CLIの移行方針を確定する`

---

## 1. 結論

Phase KのTask master、decision文書、自動試験結果を再監査した結果、**未完了Taskは0件**だった。

```text
K-01 UPDS Object参照最小ユースケース             Complete
K-02 Stable Object ID / Version参照検証          Complete
K-03 Semantic Index / inference ownership境界    Complete
K-04 UPDS専用Context/Profile必要性評価           Complete
```

Phase Kを **Complete / Closed** とし、Phase Lへ移行可能と判定する。

---

## 2. Task別監査

| Task | Status | 主な成果物 |
|---|---|---|
| K-01 | Complete | `docs/decisions/K01_UPDS_OBJECT_REFERENCE_USE_CASE.md` |
| K-02 | Complete | `docs/decisions/K02_STABLE_OBJECT_ID_REFERENCE_VERIFICATION.md`, `tests/test_k02_stable_object_reference.py` |
| K-03 | Complete | `docs/decisions/K03_SEMANTIC_INDEX_OWNERSHIP_VERIFICATION.md`, `tests/test_k03_semantic_index_boundary.py` |
| K-04 | Complete | `docs/decisions/K04_UPDS_CONTEXT_PROFILE_EVALUATION.md` |

---

## 3. Phase K完了条件の確認

Phase Kの完了条件は次である。

> UPDSがSGOKB Knowledgeを再解析せず再利用でき、SGOKBはUPDSなしでも独立している。

K-01〜K-04により次の境界が成立した。

```text
SGOKB canonical World / Object Knowledge
        ↓ stable read contract
MCP get_objects / optional build_context
        ↓
UPDS Personal Inference Consumer
        ↓
Selection Event / Semantic Observation / Pattern / Preference Hypothesis
```

SGOKB側はUPDS Personal Inferenceを正本Knowledgeへ取り込まず、UPDS側はSGOKB Object Knowledgeを第二正本化しない。

したがってPhase K完了条件を満たす。

---

## 4. Phase Kで固定した主要契約

### Identity / Version

- 長期Identityはstable `object_id`。
- 推論時に使用したaccepted Knowledgeは`resolved_version_id`で記録する。
- current取得は新accepted Versionへ進む。
- pinned取得では過去accepted Versionを再取得できる。
- Object表示名変更で`object_id`参照を壊さない。
- 新Version発生で過去UPDS参照をsilent rewriteしない。

### 最小UPDS read path

```text
get_objects(
  object_ids=[...],
  facets=["values", "personality", "themes"],
  include_relations=False,
  include_evidence_refs=False,
)
```

Relation / Evidence / Search / Similarityは必要時の追加取得とし、最小ケースへ含めない。

### Semantic ownership

```text
SGOKB
  Object / Facet / Statement / Evidence retrieval index

UPDS
  Selection Event / Observation / Pattern / Preference inference
```

物理Vector backendを同じ製品にすること自体は禁じないが、collection / namespace / metadata ownership / rebuild authority / score semanticsを分離する。

### Context/Profile

現時点ではUPDS専用Context/Profileを追加しない。

- structured Knowledge取得は`get_objects`を標準とする。
- `build_context`はLLM投入時の任意のdeterministic selection layerとする。
- 実UPDS workloadで具体的不足が実証された場合のみ専用Profileを再評価する。

---

## 5. Verification summary

Phase Kで実施した主な検証:

```text
K-02 related regression: 24 passed
K-03 focused: 6 passed
K-03 + Search / Similarity / MCP regression: 38 passed, 2 skipped
K-04 Context Builder / MCP read regression: 14 passed
```

K-02時点のrepository-wide pytestでは次を確認した。

```text
313 passed
4 skipped
1 failed
```

唯一の失敗は既知の`tests/test_package_transfer.py::test_stage_rejects_unexpected_files_and_hash_mismatch`で、期待する`SHA-256 mismatch`より先にsize mismatchを検出するメッセージ差である。Phase K機能とは独立しており、Phase K blockerとはしない。

---

## 6. UPDS未実装に関する扱い

2026-10-14時点の`tabenishi02/UserPreferenceDiscoverySystem`は構想・要件検討段階であり、実runtime / DB schema / MCP consumerはまだ存在しない。

したがってPhase KではSGOKB側のconsumer-shaped contract testをStage Aとして完了した。

将来UPDS runtime実装後に行うcross-repository E2Eは、Phase Kを未完了へ戻す条件ではない。必要になった時点でUPDS側integration acceptanceとして追加する。

---

## 7. Non-blocking follow-up

次はPhase K blockerではない。

- 実UPDS runtimeからのcross-repository MCP E2E。
- `get_objects`へ汎用`include_attributes` optionを追加するかの評価。
- Context Builderへ汎用`include_summary` optionを追加するかの評価。
- 実workloadでpayload / latencyを計測した後のUPDS専用Profile再評価。
- 既知のPackage Transfer test expectation差の修正。

これらを理由にPhase Kを再Openしない。

---

## 8. Phase Lへの引継ぎ

Phase LではSGOKB / UPDS契約を再設計しない。

Phase Lの目的は、A〜Kで新standard workflowが成立した後も残っている旧Prototype資産を安全に整理し、通常運用から高コストなFragment / Final Document生成経路を除去することである。

正本準備資料:

`docs/planning/PHASE_L_PREPARATION.md`

次Task:

```text
L-01 [P0] Fragment table / code / CLIの移行方針を確定する
```
