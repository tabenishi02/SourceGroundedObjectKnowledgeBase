# N05D-01 — Qdrant storage/path diagnosis

更新日: 2026-10-22

- Parent: `N-05 [P0] — Performance`
- Task: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **Active — diagnostic harness implemented / local comparative execution pending**
- Formal N-05 run: `20261022T130413+0900`
- Formal run HEAD: `a7147f9842f94e96944bc7f67b4c3986970462b0`
- N-05 formal verdict: **BLOCKED / performance target not judgeable**

## 1. Diagnostic question

Standard profileの23 sampleすべてを停止させたQdrant storage/gridstore path errorが、次のどこに属するかを確定する。

```text
QDRANT_ENVIRONMENT_DEFECT
SGOKB_ADAPTER_DEFECT
BENCHMARK_RUNNER_DEFECT
BACKEND_PRODUCT_DEFECT
OTHER_IDENTIFIED_CAUSE
```

N05D-01の診断値はN-05 formal performance sampleへ混ぜない。

## 2. Known local evidence before N05D-01

N-04P-06ではReference Workstation上で次のruntimeが成立していた。

```text
OS: Windows 11
Qdrant server: 1.19.2 native qdrant.exe
qdrant-client: 1.19.1
HTTP: localhost:6333
gRPC: localhost:6334
storage: .local/n04p06/qdrant/
vector points: 24
```

このsmall real-data acceptanceではEmbedding / Vector sync、semantic search、SimilarityがPASSした。

一方、N-05 formal runではStandard profile 23/23 sampleがDerived Search sync中のQdrant collection / payload-index preparationで停止した。観測errorはgridstoreの保存先pathが見つからない旨を示した。

したがって現時点では、Qdrant自体が常に起動不能なのではなく、**N-05負荷・server lifecycle・payload-index storage pathの組み合わせで発生するdefect**を優先して疑う。

## 3. SGOKB adapter desk review

`QdrantVectorIndexAdapter._ensure_collection()`は次の順で処理する。

```text
create_collection
→ configured payload indexesをcreate_payload_index(wait=True)で作成
→ upsert時にpoint upload
```

この順序はQdrantの一般的な推奨である「既知のpayload fieldはupload前にindex作成」と矛盾しない。

N05D-01では同じpayload schemaを、SGOKB adapterを通さないdirect qdrant-clientでも作成する。direct pathでも同じerrorが再現すれば、SGOKB adapterをprimary triggerから外せる。

## 4. External research

2026-10-22時点でQdrant upstreamにはWindows / payload-index / filesystem interactionに関する重要な既知事象がある。

### Qdrant issue #10806

Open / `bug` / `parked`のissueで、native `qdrant.exe` 1.19.1 / 1.19.2をWindows 11上で利用し、複数payload indexを持つloadでfilesystem operationが失敗する再現報告がある。

報告者側の追加調査では、Microsoft Defender for Endpoint (`MsSense.exe`) がsegment/index fileを読み取るタイミングとQdrant側renameが競合し、`Access is denied (os error 5)`が発生したとされる。

このupstream issueは今回の「gridstore path not found」と**完全一致するerrorではない**。したがって現時点ではroot causeと断定しない。ただし、

```text
Windows 11
native qdrant.exe 1.19.2
payload indexes
Gridstore / filesystem operations
```

という条件が強く重なるため、重要なupstream candidateとして扱う。

### Qdrant filesystem guidance

Qdrantはpersistent storageについてfilesystem semanticsを重要視しており、Windows上のDocker/WSL bind mount等について互換性注意を明示している。

今回のReference Workstationはnative `qdrant.exe` + local storageであり、Docker bind mount問題と同一ではない。ただしstorage path / filesystem / file-filter interactionを診断対象に含める根拠になる。

## 5. Diagnostic harness

追加した資産:

```text
benchmark/tools/n05d01_qdrant_storage_diagnosis.py
benchmark/tools/n05d01_run_qdrant_diagnosis.ps1
tests/test_n05d01_qdrant_storage_diagnosis.py
```

Python diagnosticは同一Qdrant serverに対して次を順に実行する。

```text
A. direct qdrant-client / payload indexesなし
B. direct qdrant-client / SGOKBと同じpayload indexesあり
C. SGOKB QdrantVectorIndexAdapter / indexesなし
D. SGOKB QdrantVectorIndexAdapter / indexesあり
E. direct indexed pathの連続create/upload/query/delete
```

成功したdiagnostic collectionは削除する。失敗したcollectionはserver-side inspectionのため残す。

canonical SQLite DBは開かない。

## 6. Existing server vs isolated server

PowerShell runnerは2条件を比較する。

### Existing server

```text
localhost:6333 / 6334
```

現在N-05が利用しているserverに対してminimal probeを行い、process path / command lineと既知storage candidateの存在・writeabilityを保存する。

### Isolated server

同じnative `qdrant.exe`を別port:

```text
HTTP 6433
gRPC 6434
```

で起動し、run固有のabsolute pathを明示する。

```text
.local/n05d01/<run_id>/isolated-qdrant/storage
.local/n05d01/<run_id>/isolated-qdrant/snapshots
.local/n05d01/<run_id>/isolated-qdrant/temp
```

既存Qdrant processは停止・変更しない。

これにより、

```text
existing serverだけFAIL / isolated PASS
  → stale storage path / server lifecycle / local configurationを強く疑う

existing + isolatedのdirect indexed pathが同じFAIL
  → Windows/Qdrant backendまたはfilesystem/security-filter interactionを強く疑う

direct indexed PASS / adapter indexed FAIL
  → SGOKB_ADAPTER_DEFECT

全てPASS
  → original failure条件を追加で縮退再現する
```

という切り分けが可能になる。

## 7. Current hypotheses

| Hypothesis | Current assessment | Reason |
|---|---|---|
| Existing Qdrant storage root / lifecycle defect | **High priority** | N-04P-06のtemporary evaluation storageを継続利用していたため、実path・process/configの再確認が必要 |
| Native Windows Qdrant/Gridstore/filesystem interaction | **Credible upstream candidate** | Qdrant 1.19.1/1.19.2 + Windows + payload indexの既知issueが存在 |
| SGOKB adapter defect | **Unproven / lower confidence** | adapter operation order自体は通常形。direct comparison未実行 |
| N-05 benchmark runner defect | **Possible** | sample-specific collection lifecycleと既存server lifecycleの相互作用をまだ分離できていない |

## 8. Local execution requirement

Root-cause classificationをCompleteにするにはReference Workstationで次を実行する必要がある。

```powershell
powershell -ExecutionPolicy Bypass -File benchmark/tools/n05d01_run_qdrant_diagnosis.ps1
```

raw evidence:

```text
.local/n05d01/<run_id>/run-meta.json
.local/n05d01/<run_id>/current-server.json
.local/n05d01/<run_id>/current-server.log
.local/n05d01/<run_id>/isolated-server.json
.local/n05d01/<run_id>/isolated-server.log
.local/n05d01/<run_id>/isolated-qdrant.stdout.log
.local/n05d01/<run_id>/isolated-qdrant.stderr.log
.local/n05d01/<run_id>/summary.json
```

必要ならProcess Monitor / Defender/EDR evidenceを追加する。

## 9. Exit condition

N05D-01をCompleteにできるのは、local comparative runとserver/storage evidenceから次のいずれかを確定し、修復後のminimal real-Qdrant smokeを繰り返しPASSさせた場合だけである。

```text
QDRANT_ENVIRONMENT_DEFECT
SGOKB_ADAPTER_DEFECT
BENCHMARK_RUNNER_DEFECT
BACKEND_PRODUCT_DEFECT
OTHER_IDENTIFIED_CAUSE
```

現時点ではdiagnostic harnessとdesk reviewは完了したが、Reference Workstation command executionをこのChatGPT sessionから利用できないため、**N05D-01自体はまだCompleteではない**。
