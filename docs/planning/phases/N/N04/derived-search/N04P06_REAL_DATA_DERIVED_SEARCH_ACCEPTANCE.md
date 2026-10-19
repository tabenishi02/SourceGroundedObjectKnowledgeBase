# N-04P-06 Real-data Derived Search Acceptance

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04P-06 [P0] N-03実データでDerived Search Gateを受入する`
- Parent: `docs/planning/N04_PREREQUISITE_DERIVED_SEARCH_PIPELINE.md`
- Dataset: `benchmark/n03-real-data-vertical-slice-v1.json`
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`
- Branch: `phase-n/n04-prerequisite-derived-search`
- Status: **Complete (2026-10-18)**

## 1. Purpose

N-03では6 Objectのcanonical Vertical Sliceは成立したが、Search Representationが未生成だったため内容語Lexical Searchが未成立だった。

N-04P-02〜P-05で次を実装済みである。

```text
accepted Object Version
  ↓
Search Representation sync
  ↓
Embedding sync
  ↓
Vector Index sync / rebuild
  ↓
public CLI: system derived status / sync
```

P-06ではこのpipelineをN-03の実データ評価DBへpublic CLIだけで適用し、Lexical / Semantic / Similarityの利用可能性とcanonical Knowledge不変性を受け入れる。

検索順位、Recall、NDCG等の正式な品質判定はN-06へ送る。P-06では「derived artifact不足のため利用できない」状態を解消したかを判定する。

## 2. Source of truth

評価対象を手作業で再定義しない。

次を正本とする。

```text
benchmark/n03-real-data-vertical-slice-v1.json
```

このbenchmarkに記録された6 Objectについて、最低限以下をDB実体と照合する。

- stable Object ID
- canonical name / aliases
- accepted current Version ID
- Source / Snapshot / Evidence provenance
- N-03 lexical smoke query
- similarity rationale

対象はN-03で確定した次の6 Objectである。

```text
Character:
- Saber
- Ichigo Kurosaki

Work:
- Fate/stay night
- BLEACH

Concept:
- Tsundere
- Hero's Journey
```

## 3. Safety boundary

この受入は評価専用DBだけを変更する。

```text
.local/n03/sgokb-n03.sqlite
```

production DBを変更してはならない。

受入前に次を保存する。

1. DB backup
2. `system integrity`
3. `system derived status`
4. 6 ObjectのObject ID / current Version ID
5. canonical Knowledge / Evidence / provenanceの比較用snapshot

受入で変更を許容するのはderived artifactである。

```text
search_representations
knowledge_search_representation_memberships
search_embedding_spaces
search_representation_embeddings
object_derived_states
外部Vector backend collection / points
```

canonical Object / Version / Statement / Evidence / provenanceの意味内容を変更してはならない。

## 4. Semantic runtime

P-06はfake provider / fake Vector backendではなく標準local semantic runtimeを使う。

Frozen Embedding profile:

```text
model: microsoft/harrier-oss-v1-0.6b
revision: f9b9dc8d367d443f2479d27aa5d8d2850c0774ee
dimension: 1024
provider: sentence-transformers
output dtype: float32
model load dtype: bfloat16
```

Vector backend:

```text
Qdrant
default URL: http://localhost:6333
default gRPC port: 6334
```

必須原則:

- cloud inferenceへfallbackしない。
- provider / model / revision / Embedding Space IDを記録する。
- Qdrant server versionとcollection名を記録する。
- 実行時の環境変数を記録する。
- model artifact downloadが必要な場合、それはlocal runtime準備として記録し、cloud inferenceとは区別する。
- 可能ならmodelを一度cacheした後、`SGOKB_MODEL_LOCAL_ONLY=1`で本受入を再実行する。

QdrantがReference Workstation上に存在しない場合、production実装をfake/local-modeへ変更してGateを通してはならない。既存Qdrant service / executable / approved temporary local serverを使用する。runtimeを用意できない場合はP-06をBlockedとして記録し、Completeにしない。

## 5. Acceptance sequence

### A. Baseline integrity / dataset identity

1. branch / head / working treeを記録する。
2. `.local/n03/sgokb-n03.sqlite`の存在を確認する。
3. benchmark JSONとDBの6 Object stable IDを照合する。
4. benchmark記録のaccepted current Version IDとDBを照合する。
5. canonical Knowledge / Evidence / provenance snapshotを保存する。
6. `sgokb system integrity`を実行しPASSを確認する。
7. runtime-free `sgokb system derived status`を保存する。

N-03由来DBであることを確認できない場合は中止する。

### B. Search Representation acceptance

public CLIのみを使う。

```text
sgokb --db .local/n03/sgokb-n03.sqlite system derived sync
```

semantic runtimeは付けない。

Gate:

- 6 Objectすべて`search_representation = ready`
- `embedding` / `vector_index`はこの段階で勝手にreadyへ進まない
- canonical Knowledge不変

### C. Lexical re-check

N-03 benchmarkに記録されたlexical smoke queryを再実行する。

特にN-03で内容語由来の未ヒットとなったqueryを再評価する。

判定:

- 「Search Representation未生成」が原因の未ヒットが0件になること。
- canonical name / aliasの既存rank-1成立を壊さないこと。
- 正式なranking quality合否はN-06へ送る。

queryごとに次を記録する。

```text
query
target object
target found
target rank
search channel
N-03 result
P-06 result
```

### D. Real semantic runtime preflight

1. `local-embedding` / `vector-qdrant` dependency確認。
2. frozen model revisionをload可能か確認。
3. Qdrantへ接続できることを確認。
4. `system derived status --semantic-runtime`を実行。
5. active Embedding Space ID / model / revision / Qdrant metadataを記録。

このpreflightはstatusなのでDBのderived/canonical dataを変更しないことを確認する。

### E. Embedding + Vector acceptance

public CLIのみを使う。

```text
sgokb --db .local/n03/sgokb-n03.sqlite system derived sync --semantic-runtime
```

Gate:

- 6 Objectすべて`search_representation = ready`
- 6 Objectすべて評価Spaceで`embedding = ready`
- 6 Objectすべて対象backendで`vector_index = ready`
- status上`missing_embedding_count = 0`
- partial=false / exit 0
- cloud fallbackなし

実行後に同じcommandを再実行し、Embedding reuse / lifecycle idempotencyも確認する。

### F. Semantic search smoke

6 Objectについて少なくとも1 queryずつsemantic searchを実行する。

queryはbenchmarkのexpected search query / grounded contentから選ぶ。

P-06のGateは品質順位そのものではなく、次である。

- semantic channelがdegradedせず実行できる。
- Vector backendからcurrent Object resultが返る。
- target Objectが合理的なcandidate集合に入る。
- current/historical scopeが破壊されていない。

詳細ranking qualityはN-06で評価する。

### G. Work Similarity smoke

N-04 case 2の前提として、少なくとも次を実行する。

```text
Fate/stay night → similar objects
BLEACH → similar objects
```

確認事項:

- Similarity operationがruntime errorなしで成立する。
- score typeは既存contractどおりsemantic similarityである。
- Work class / cross-class optionの既存contractに従う。
- 取得結果を保存する。

「Fate/stay nightとBLEACHが必ず相互rank 1」はP-06 Gateにしない。順位・品質はN-06で判定する。

### H. Canonical invariance

受入後、事前snapshotと比較する。

次が不変であること。

```text
Object stable IDs
current Version IDs
accepted Version content
Facet / Statement / Attribute / Relation canonical Knowledge
Source / Snapshot / Evidence
Statement-Evidence grounding
provenance
```

Search Representation / Embedding / Vector derived artifactの追加は許容する。

### I. Final system gate

```text
sgokb system integrity
python -m pytest -q
```

Gate:

- integrity PASS
- full suite 0 failed
- 新規skip / xfailなし
- working tree clean（受入記録更新前の意図したdoc差分を除く）

## 6. Completion Gate

N-04P-06をCompleteにできるのは、すべて満たす場合だけである。

- benchmarkと評価DBの6 Object identity整合。
- 6 Objectすべて`search_representation = ready`。
- frozen評価Spaceについて6 Objectすべて`embedding = ready`。
- 実Qdrant backendについて6 Objectすべて`vector_index = ready`。
- `missing_embedding_count = 0`。
- N-03内容語queryでRepresentation未生成原因の未ヒット0件。
- semantic search smokeが実runtimeで成立。
- Work Similarity経路が実runtimeで成立。
- canonical Knowledge / Version / Evidence provenance不変。
- `system integrity` PASS。
- full pytest 0 failed。

受入中にproduction defectが見つかった場合はP-06 scopeで修正し、P-02〜P-05回帰とfull suiteを再実行する。

環境不足だけの場合はproduction contractを弱めず、Blockedとして環境条件を記録する。

## 7. Evidence to record

Complete時はこの文書へ少なくとも以下を追記する。

```text
Reference Workstation OS / Python / GPU
branch / start head / final head
DB path / backup path / DB hash before-after
6 Object ID / current Version verification
initial/final derived states
representation counts per Object
Embedding model / exact revision / space_id
Embedding count / reuse count
Qdrant server/client version / collection
Vector point count
lexical query before/after table
semantic smoke result table
Work Similarity result
canonical invariance comparison
system integrity result
full pytest result
Ruff / diff-check if code changes occurred
issues / fixes / blockers
```

Local runtime logs belong under `.local/n04p06/` and are not committed unless intentionally converted into summarized acceptance evidence.

## 8. Completion transition

PASS後:

```text
N-04P-01 Complete
N-04P-02 Complete
N-04P-03 Complete
N-04P-04 Complete
N-04P-05 Complete
N-04P-06 Complete
```

としてN-04 prerequisite全体をCompleteにする。

次TaskはPhase N本体の:

```text
N-04 [P0] 3つの代表AI利用ケースを受入試験する
```

PR #39は今回Draftを維持する。Ready化・stacked PR統合は別途判断する。PR #36〜#39を勝手にmergeしない。


## 9. Reference Workstation acceptance — 2026-10-18

### Environment / dataset / backup

- Windows 11 Home 10.0.26300、Python 3.10.6、GPU: NVIDIA GeForce RTX 4090（実runはCUDA device 0）、Quadro P1000。
- Start head: `3abc52a060f881bb5dbe65fbace6beeab25eb3b3`。branchは本書冒頭の指定branchを維持した。
- Evaluation DB: `.local/n03/sgokb-n03.sqlite`。production DBを開く操作は実施していない。
- public CLI `system backup create --output .local/n04p06/sgokb-n03-before.sqlite`でbackupした。backupの`PRAGMA integrity_check=ok`、`foreign_key_check`違反0件。
- benchmarkとのObject ID / name / class / aliases / accepted current Version照合6/6 PASS。Source / Snapshot / Normalization Run / Evidence ID集合とcount、confirmed association、Raw Capture hashを照合した。expected queryはbenchmarkのN-03 smoke記録と対応する。

| Object | Stable Object ID | Accepted current Version ID |
|---|---|---|
| Saber | `326a97cf-47aa-4760-a7f1-07bfe639fcf0` | `fb0ab12a-5e11-4df7-983a-925da458a129` |
| Ichigo Kurosaki | `3aec055e-e9f3-445d-a7a3-adb2b5864c6f` | `50ca186c-80a5-4447-bf71-216bbad8f1d6` |
| Fate/stay night | `d5824d33-7008-4121-9cfe-1f95a19667fd` | `47f2b146-20a6-4d06-957f-904cc5ef39a9` |
| BLEACH | `57db855c-574a-4b38-b474-421c165894f1` | `6e75aa45-9c13-42ef-87b4-923beac43bef` |
| Tsundere | `8c83f986-f491-41a8-8645-9f71dd5874b9` | `98c16da1-a5a6-4d73-b919-bcadcc3df08f` |
| Hero's Journey | `fee32007-0f92-449a-ba21-4ec2f78d1cd4` | `31e52190-fdb2-42da-8860-d4e0bbaa4de6` |

DB file hashはderived変更により一致しない。WALの物理表現に依存しないcanonical比較を正式Gateとする。

- `sgokb-n03.sqlite` SHA-256: `0e4760d46105efeb6d46729c513493d9ee816282cc8d0c283fed60de568eab3d`
- `sgokb-n03-before.sqlite` SHA-256: `0850591afeda1ed1e50f38c3d75322dc374c49d4da4475ad5fd6b098cc3599d8`

### Search Representation / canonical state

初期6/6のSearch Representation / Embedding / Vector / renderingはpending。public CLI `system derived sync`（semantic runtimeなし）はexit 0 / partial=false / completed 6を返した。6/6のSearch Representationだけがreadyとなり、Embedding / Vector / renderingはpendingを維持した。

最終状態は6/6のSearch Representation / Embedding / Vectorがready、renderingはpending（Search Gate対象外）。

| Object | Memberships | Unique representations | Embeddings (active Space) | Missing |
|---|---:|---:|---:|---:|
| Saber | 4 | 4 | 4 | 0 |
| Ichigo Kurosaki | 4 | 4 | 4 | 0 |
| BLEACH | 4 | 4 | 4 | 0 |
| Tsundere | 4 | 4 | 4 | 0 |
| Fate/stay night | 4 | 4 | 4 | 0 |
| Hero's Journey | 4 | 4 | 4 | 0 |

### Lexical before / after

全20 queryをpublic CLI `search <query> --mode lexical --limit 10`で再実行した。N-03の10/20 hitから18/20 hitへ改善し、既存identity queryはrank 1を維持した。

| Object | Query | N-03 rank | P-06 rank | Classification |
|---|---|---:|---:|---|
| Saber | Saber | 1 | 1 | hit |
| Saber | Artoria Pendragon | 1 | 1 | hit |
| Saber | King of Knights | — | — | B: Knowledge coverage / N-06 |
| Ichigo Kurosaki | Ichigo Kurosaki | 1 | 1 | hit |
| Ichigo Kurosaki | Substitute Soul Reaper | — | 1 | hit |
| Ichigo Kurosaki | Zangetsu | — | 1 | hit |
| Fate/stay night | Fate/stay night | 1 | 1 | hit |
| Fate/stay night | Fate/Stay Night | 1 | 1 | hit |
| Fate/stay night | Holy Grail War | — | 1 | hit |
| Fate/stay night | visual novel | — | 1 | hit |
| BLEACH | BLEACH | 1 | 1 | hit |
| BLEACH | Bleach | 1 | 1 | hit |
| BLEACH | Soul Reaper | — | 1 | hit |
| BLEACH | Tite Kubo | — | 1 | hit |
| Tsundere | Tsundere | 1 | 1 | hit |
| Tsundere | harsh personality warmer side | — | 1 | hit |
| Tsundere | character archetype | — | — | B: Knowledge coverage / N-06 |
| Hero's Journey | Hero's Journey | 1 | 1 | hit |
| Hero's Journey | Monomyth | 1 | 1 | hit |
| Hero's Journey | narrative pattern | — | 1 | hit |

未hitの`King of Knights`と`character archetype`はcurrent accepted Knowledge / Representationに必要な内容が採用されていない分類Bで、N-06のKnowledge coverage課題へ引き渡す。Representationに情報があるのに検索不能という分類Aは0件。

別途、6 ObjectごとにRepresentationへ実在するgrounded内容語（Servant contracted to Shirou / Substitute Soul Reaper / Holy Grail War / confronts Hollows / associated with aloofness / decisive crisis）を選び、全6件がLexical rank 1でhitした。

### Real runtime / Embedding / Vector

- Frozen model: `microsoft/harrier-oss-v1-0.6b`、revision `f9b9dc8d367d443f2479d27aa5d8d2850c0774ee`、dimension `1024`、provider `sentence-transformers`。
- Embedding Space ID: `23027d8fcb47c6ffb9e95681742e4c0aa8d14b301b642a974159f05883204bbf`。
- local model artifact downloadを1回実施した。cacheは`.local/models`。cloud inferenceは実施していない。
- 最終runは`SGOKB_MODEL_LOCAL_ONLY=1`、`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`。設定はGit管理外`runtime-environment.json`へ保存した。
- Dependencies: torch 2.6.0+cu124, torchvision 0.21.0+cu124, torchaudio 2.6.0+cu124, sentence-transformers 6.1.0, transformers 5.20.1, qdrant-client 1.19.1。
- 実Qdrant server 1.19.2、backend `qdrant`。既存`.local/qdrant-1.19.2/qdrant.exe`をlocalhost限定・telemetry無効で起動した。HTTP 6333 / gRPC 6334、prefer gRPC=1。
- Collection: `sgokb_n03_eval_23027d8fcb47c6ffb9e95681`。prefix `sgokb_n03_eval`で評価用collectionを分離した。Qdrant dataは`.local/n04p06/qdrant/`。
- `system derived status --semantic-runtime`前後のSQLite全table dumpは完全一致した。未作成collectionの診断を返しつつstatusは成功した。
- `system derived sync --semantic-runtime`はexit 0 / partial=false / completed 6。全6 Objectが3段階ready、missing Embedding=0。
- Embedding rows `24`、Vector membership points `24`。同じsyncを再実行してexit 0、created Embedding=0、Embedding row全内容・Vector ID/payload/vector・canonical Knowledge/current Version・derived revision/stateは不変。確認時刻更新と再upsertは既存契約どおり許容した。

### Semantic / Similarity smoke

各queryはgrounded contentから選び、public CLI `search <query> --mode semantic --semantic-runtime --require-full-runtime --limit 10`で実行した。全6件で実Qdrant semantic channelが成功し、degraded channelなし。全candidateはaccepted current Versionだった。

| Target | Query | Target rank | Candidate count | Degraded |
|---|---|---:|---:|---|
| Saber | Servant contracted to Shirou | 1 | 6 | none |
| Ichigo Kurosaki | Substitute Soul Reaper | 1 | 6 | none |
| Fate/stay night | Holy Grail War | 1 | 6 | none |
| BLEACH | confronts Hollows | 1 | 6 | none |
| Tsundere | associated with aloofness | 1 | 6 | none |
| Hero's Journey | decisive crisis | 1 | 6 | none |

返却candidate一覧はGit管理外`semantic-smoke.json`へ保存した。順位は今回のsmoke観測値であり、Recall / NDCGや正式ranking quality合格を意味しない。

public CLI `similar --object <Work ID> --limit 10`の両方向実測:

- Fate/stay night → BLEACH (rank 1, cosine_similarity=0.646960)
- BLEACH → Fate/stay night (rank 1, cosine_similarity=0.646960)

全resultで`score_type=cosine_similarity`、class `work`、accepted current Version、cross_class=falseを確認した。相互rank 1をGateにはしていない。

### Integrity / regression / issues

canonical 52 table（Object / accepted Version / Facet / Statement / Attribute / Relation / Source / Snapshot / Evidence / grounding / provenanceを含む）は受入前後で完全一致。変更許容tableはSearch Representation / membership / FTS、Embedding Space / Embedding、object_derived_statesだけとして明示分類した。`canonical-before.json` / `canonical-after.json` / `canonical-comparison.json`を保存した。`system integrity`は前後ともPASS。

| Verification | Result |
|---|---|
| Embedding provider focused + P-02〜P-05 regression | 55 passed / 0 failed |
| `python -m pytest -q` (runtime dependencies installed, after fix) | 361 passed / 0 skipped / 0 failed (158.28s) |
| Ruff check / format on changed Python | PASS |
| `git diff --check` | PASS |

full suiteの2 warningは既存Qdrant local-mode unit testのexact search診断で、実Qdrant受入をfakeへ置換したものではない。新規skip / xfailは追加していない。正式な検索品質、AI use-case品質、performance / recoveryは今回へ含めない。

発見した問題:

1. F: 既存venv PyTorch 2.4.1は導入されたTransformersの要件を満たさなかった。このvenv内だけCUDA PyTorch 2.6.0 / torchvision 0.21.0 / torchaudio 2.6.0へ更新した。system-wide packageを変更していない。既存の無関係なiopaint / huggingface-hub制約競合は環境ログへ記録し、iopaintの変更は行っていない。
2. B: providerが固定revision / local-onlyをmodel_kwargsにだけ渡し、SentenceTransformer本体のconfig / tokenizer / module解決へ伝播していなかった。top-level revision / local_files_onlyも渡す最小修正を行い、offline fake encoder testと実pinned modelで確認した。モデルprofileやcanonical schemaは変更していない。
3. 一時受入scriptのWindows文字コード・import漏れ・public class key（work）と内部IDの区別を補正した。production contractを弱める変更は行っていない。
4. G: 上記2 queryのKnowledge coverageと正式ranking qualityはN-06へ引き渡す。

### Completion decision

全Gate PASSにより **N-04P-06 Complete (2026-10-18)**、**N-04 prerequisite Complete**。次Taskは **N-04 [P0] 3つの代表AI利用ケースを受入試験する**。

証跡は`.local/n04p06/`、Raw / 評価DB / Qdrant data / model cacheはGit管理外。PR #39はDraft維持、PR #36〜#39はmergeしていない。
