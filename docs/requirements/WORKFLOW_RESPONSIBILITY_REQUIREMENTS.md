# Source Grounded Object Knowledge Base — 人間工程 / 自動工程 要件

更新日: 2026-10-11

- Task: `B-06 [P0] 人間工程と自動工程を要件として分離する`
- Status: Accepted
- Parent: Phase B — 要件定義の全面更新
- Inputs:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md`
- B-07 result: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`
- Next: `Phase C — SGOKB / UPDS責務境界`

---

## 1. 目的

本書は、SGOKBの標準Workflowについて、**人間が判断・開始・承認する工程**と、**SGOKBがローカルで自動実行する工程**を明確に分離する。

B-06では次を固定する。

- 「自動処理」の意味。
- 人間の明示判断を必須とする境界。
- Source選定、Object登録、Capture / Import、Evidence生成の責務。
- Object Evidence Packageのbuildとexternal exportの責務分離。
- Google Drive / ChatGPTを利用する標準Human-in-the-loop workflow。
- Object ResultのValidation / Import / Version promotion境界。
- partial / stale / Registry proposal等のreview要否。
- Import後のEmbedding / Search Index更新を自動化する範囲。
- 外部サービスへのdata egressをlocal処理と分離すること。
- 1 Objectあたり概ね10分以内という自動処理時間目標の計測範囲。
- CLI / GUIで人間の明示操作点を可視化すること。

本書はWorkflowの論理要件を定義する。具体的CLI command、GUI widget、Google Drive path、filesystem watcher、approval token、job queue、retry回数等は後続Phaseで決定する。

---

## 2. 結論

SGOKBでは、標準Workflowを次の4種類の責務へ分離する。

| 責務 | 意味 | 例 |
|---|---|---|
| Human Decision | 対象・Identity・外部送信・正本更新等を人間が明示判断する | Source採用、Object確定、Package export、Result import |
| Human-triggered Automation | 人間が開始した後、次の判断境界までSGOKBが自動処理する | Import→Normalize→Evidence、Package build、Result validation |
| Local Automatic Maintenance | 正本更新等を契機に、外部送信なしで再生成可能な派生物を自動更新する | Embedding、FTS、Vector Index、Markdown render |
| External Human-in-the-loop | SGOKB外のAI / Serviceを人間が明示的に利用する | DriveへPackage配置、ChatGPT分析、Result返却 |

最も重要な原則は次である。

> **SGOKBにおける「自動」は、外部送信・Identity決定・正本Knowledgeの意味判断までを無人化することを意味しない。人間が開始した処理を、次の明示的な判断境界まで安全に継続することを意味する。**

標準Object Knowledge生成flowは次とする。

```text
[Human] Source / Objectを選択・登録
        ↓
[Auto Local] Capture Bundle Import / Normalize / Evidence
        ↓
[Human] Knowledge生成対象Objectを指定
        ↓
[Auto Local] Evidence Retrieval / Package Build / Preflight
        ↓
[Human] External Exportを明示実行
        ↓
[External Manual] Google Drive / ChatGPTへ渡して分析
        ↓
[Human] result.jsonをSGOKBへ戻す
        ↓
[Auto Local] Validation / Diff / Review材料生成
        ↓
[Human] Importを明示実行
        ↓
[Auto Local] Version commit / current切替 / Search Representation / Embedding / Index更新
        ↓
[Auto Local] Search / MCPから利用可能
```

標準運用では、**Capture / Importした事実をexternal export permissionへ昇格させない。**

---

## 3. 「自動」の定義

### WF-01 — 自動処理と無人運用を同一視しない

SGOKBで自動処理と呼ぶものは、ユーザー操作や明示的policyをtriggerとして開始し、次のdecision boundaryまでプログラムが処理を継続することを指す。

例えば、ユーザーがCaptureしたBundleについて、明示設定されたincoming directoryからImport / Normalize / Evidence生成を自動実行することは許容する。

一方、次を自動処理の当然の延長として行ってはならない。

- Web全体から勝手にSourceを採用する。
- 未登録ObjectをAI判断だけで正式作成する。
- local Source / Evidenceを外部Serviceへ勝手に送信する。
- ChatGPT Resultを検出しただけで正本Knowledgeへsilent importする。
- Registry proposalを自動適用する。

### WF-02 — 標準Workflowはdecision boundaryで停止できること

自動処理は、人間判断が必要な状態へ到達した場合に、推測で先へ進まず停止または`requires_action`相当状態へ遷移できなければならない。

例:

- Source Identityが曖昧。
- Object Identityが曖昧。
- Package external export待ち。
- Resultがstale。
- partial Resultで削除影響がある。
- Registry proposalを含む。
- Unknown Relation / Class reviewが必要。

最終state名は実装Phaseで決定する。

### WF-03 — read-only retrievalは通常自動利用可能とする

ローカルKnowledgeに対する次の処理は、正本を書き換えない限り、通常のread operationとして人間の個別承認を毎回要求しない。

- Object lookup
- Lexical / Semantic / Hybrid Search
- Similarity Search
- Relation traversal
- Evidence Search
- Markdown / context rendering
- local MCP read

外部ClientへKnowledgeを送信する場合のlocal-only default、remote exposure、no-silent-egress等の非機能境界はB-07で確定済みであり、具体的authentication / scope / transportはPhase Jで設計する。

---

## 4. Source選定 / Capture / Import

### SRCWF-01 — Source採用の起点はCuratedな人間選定とする

SGOKB標準運用では、Knowledge Baseへ残すSourceをユーザーが選択する。

将来Source discovery機能が候補URL等を提示することは許容するが、候補提示だけで正式Sourceへ採用しない。

```text
Discovery Candidate
  ↓ human select / explicit import
Formal Source / Snapshot
```

無差別Crawlerによる自動採用を標準Workflowにしない。

### SRCWF-02 — Capture操作後のlocal processingは自動化可能とする

ユーザーがBrowser extension等で明示的にCaptureした後は、次を自動実行可能とする。

- Bundle integrity check
- Import
- Source / Snapshot登録
- duplicate candidate detection
- Normalize
- Evidence generation
- FTS / Evidence Embedding更新
- Page Context等のdeterministic / inferred metadata生成

ただし、Identity ambiguityやProvenance異常がある場合は人間判断へ戻す。

### SRCWF-03 — automatic ImportはSource選定を代替しない

incoming directory watcher等によるautomatic Importを実装してもよいが、そこへ入ったBundle自体がユーザーのCapture / 明示import操作から来たものであることを基本とする。

「自動Import可能」であることを、「任意Web Resourceを自動採用可能」と解釈しない。

### SRCWF-04 — Source Identity mergeの曖昧判断を自動確定しない

URL / title / hash等から既存Sourceと同一候補を検出することは自動化できる。

しかし、同一Sourceか別Sourceかが一意に決められない場合、heuristicだけで破壊的mergeしない。

confidenceの高低だけでIdentityを自動統合することを標準にしない。

### SRCWF-05 — Snapshot / Normalized Runの通常世代選択は規則化可能とする

明確なdeterministic policyで正常世代を選択できる場合は、effective Snapshot / Normalized Runの選択を自動化できる。

最新Captureがerror / incomplete / login failure等でpolicyを満たさない場合に、正常世代を破壊せずreview可能にする。

具体policyはPhase Fで決定する。

---

## 5. Object Identity / Registry

### OBJWF-01 — Persistent Object作成は人間の明示操作を起点とする

新しいObjectのstable identityを確定する処理は、標準Workflowでは人間の明示操作を必要とする。

AI / Search / ResultはObject candidateを提案できるが、Persistent `object_id`を自由に作成して正本登録してはならない。

SGOKBは人間がObject作成を承認した後、ID発行そのものを自動で行ってよい。

### OBJWF-02 — Object同定候補は自動生成可能とする

name / alias / Relation / Source context等から、既存Object候補を自動提示することは許容する。

ただし同名別Objectやcontinuity差等があるため、ambiguous matchを自動確定しない。

### OBJWF-03 — Source↔Object association候補を自動生成可能とする

B-03の`candidate / confirmed / excluded`契約を維持する。

Retrieval / Page Context等でcandidate associationを自動生成できる。

confirmedへの昇格は、次のいずれかを要求する。

- 人間の明示確認。
- Phase Fで定義された、意味が一意なdeterministic rule。

opaqueな生成AI判断だけでcandidateをconfirmedへ自動昇格しない。

### OBJWF-04 — Registry proposalは自動適用しない

Resultが次を提案しても、自動でObject Registryを書き換えない。

- name変更
- alias追加 / 削除
- Primary Class変更
- Additional Class変更
- Object merge候補
- Object split候補

Registry proposalはKnowledge Importと分離した人間review対象とする。

---

## 6. Object Evidence Retrieval / Package Build

### PKGWF-01 — Knowledge生成対象Objectは明示指定する

標準Workflowでは、どのObjectについてKnowledgeを新規生成 / 更新するかをユーザーが明示する。

SGOKBがSource追加だけを理由に、関連する全Objectを自動でChatGPT分析対象へ送らない。

将来「更新推奨Object」を候補表示することは許容する。

### PKGWF-02 — Package Buildはlocal automationとする

対象Objectが指定された後、次はSGOKBが自動実行できる。

- current accepted Knowledgeの取得
- current Knowledge grounding Evidenceのcarry-forward candidate取得
- explicit Source↔Object association利用
- Evidence Lexical / Semantic Retrieval
- duplicate / near-duplicate抑制
- Source diversity考慮
- token / size budget適用
- selection reason記録
- manifest生成
- instructions template生成
- local package directory生成
- package hash / binding metadata生成

Package Buildは生成LLMを必須にしない。

### PKGWF-03 — manual include / excludeを許容する

自動Package selection結果をユーザーが必要に応じて修正できることを要件とする。

少なくとも概念上次を許容する。

- Evidence manual include
- Evidence manual exclude
- Source manual include / exclude
- Package rebuild

手動overrideを行った場合、selection provenanceを失わない。

### PKGWF-04 — Package BuildとExternal Exportを別操作とする

SGOKBはPackageをまずlocal stagingへ生成できなければならない。

Packageが生成されたことを、Google Drive / ChatGPT / cloud storage等へ送信する許可とみなさない。

```text
Package Build
  = local derived artifact generation

Package Export
  = external data egress
```

両者を同一の暗黙操作へ統合しない。

### PKGWF-05 — Package preflightを外部送信前に実行可能にする

External Export前に少なくとも次を表示 / 検証可能にする。

- target Object
- package identity / hash
- included Source / Evidence数
- included file一覧
- current Knowledge同梱有無
- provenance / integrity warning
- external destination
- sensitivity / export warning（該当する場合）

B-07ではexport decisionを`allow / review_required / blocked`相当で扱う論理要件を定義した。具体schema /判定ruleはPhase Gで決定する。

---

## 7. External Export / Data Egress

### EXPWF-01 — Capture / Importをexternal export permissionとみなさない

B-03 SEC-01を標準Workflowとして確定する。

Source / Raw / Evidence / Object Knowledgeをローカルへ保存したことは、Google Drive、ChatGPT、外部API、remote MCP Client等へ送信してよいという許可を意味しない。

### EXPWF-02 — 標準Package Exportは人間の明示操作を要求する

初期標準Workflowでは、Object Evidence PackageをGoogle Drive等へexportする処理はユーザーの明示操作を要求する。

例えば、

```text
package build <object>
# local only

package export <package> --destination <configured-drive>
# external side effect
```

のように責務を分離する。実際のcommand名はPhase Mで決定する。

### EXPWF-03 — 同期directoryへの配置もExternal Exportとして扱う

Google Drive / OneDrive等の同期対象directoryへPackageを書き込む場合、そのfile writeが自動でcloudへ送信されるため、論理上External Exportとして扱う。

「ローカルpathへ書いただけ」という理由でexport確認を回避しない。

### EXPWF-04 — 明示設定したreusable export policyを将来許容できる

完全に毎回のconfirmationを強制することは将来の運用を不必要に制限し得る。

そのため、ユーザーがdestination、data scope、条件を明示してpersistent export policyを設定した場合に、そのpolicy内で自動exportする拡張は許容する。

ただし標準初期設定は外部exportを暗黙許可しない。

Capture / Import行為からreusable export policyを自動生成してはならない。

### EXPWF-05 — 外部Embedding / Reranker等もdata egressとして扱う

Embedding Provider、reranker、OCR、analysis等に外部cloud serviceを選択し、Source / Evidence / Knowledge textを外部へ送る場合もExternal Processingとして扱う。

標準local providerと外部providerを同一privacy semanticsで扱わない。

B-07ではlocal-only default、no-silent-cloud-fallback、secret非平文化を定義した。provider実装はPhase Iで具体化する。

### EXPWF-06 — export対象をPackage manifestから監査可能にする

標準ChatGPT workflowでは、外部へ送ったPackageのidentity / hash / included Evidence集合を後から確認できなければならない。

SGOKBは「何を送ったか不明なままResultだけ戻る」状態を標準にしない。

---

## 8. Google Drive / ChatGPT Human-in-the-loop

### AIWF-01 — ChatGPT Web/Desktop操作を正式な手動工程とする

標準Knowledge生成では、ユーザーがChatGPTへ明示的にPackage分析を依頼する。

この工程はSGOKB local automationの欠陥や暫定 workaroundではなく、正式Workflowの一部である。

### AIWF-02 — ChatGPT APIを標準自動Pipelineの必須要素にしない

SGOKB CoreはOpenAI API tokenや特定ChatGPT API modelがなくても成立しなければならない。

将来optional adapterとしてAPI自動化を追加することは妨げないが、標準要件をAPI availabilityへ依存させない。

### AIWF-03 — ChatGPTへの投入操作とResult返却は人間工程とする

標準Workflowでは次を人間操作時間として扱う。

- Drive上のPackage確認
- ChatGPTへ対象Packageを指定 / 添付 /参照させる
- 分析実行を依頼する
- 必要に応じてChatGPTとのやり取りを行う
- result.jsonを取得 / 保存する
- SGOKBのResult incoming areaへ戻す

この時間は1 Object自動処理10分目標から除外する。

### AIWF-04 — 外部AIが独自に取得したSourceを自動Evidence化しない

ChatGPTがPackage外URL、引用、追加資料を提示した場合、それをResultに混ぜて正式Evidenceとしない。

必要なら通常のSource Capture / Import工程へ戻し、新Packageで再分析する。

### AIWF-05 — Result provenanceを可能な範囲で保持する

ChatGPT Web/Desktopでは正確なmodel revision等が取得できない場合がある。

取得できた範囲でapplication / model label / timestamp / instructions version等を記録し、不明値を捏造しない。

---

## 9. Result受領 / Validation

### RESWF-01 — Resultファイル検出とValidationは自動化可能とする

ユーザーがresult.jsonを所定incoming areaへ置いた後、次を自動実行できる。

- parse
- schema validation
- package binding validation
- base Version precondition validation
- Referential validation
- Evidence / Package membership validation
- Domain contract validation
- Diff生成
- warning / review reason生成

filesystem watcherを使うか、明示`result validate`を使うかはPhase G / H / Mで決定する。

### RESWF-02 — Validation成功を自動Import許可と同一視しない

B-04 VAL-07をWorkflowへ反映する。

Validationは構造・参照・Provenance整合を確認するが、意味内容の正しさを保証しない。

標準初期Workflowでは、Validation成功したResultでも、**正本KnowledgeへImportする操作はユーザーが明示的に開始する。**

### RESWF-03 — normal ResultはImport開始後に追加承認を必須としない

ユーザーが`Import`を明示実行し、Resultが通常状態で全mandatory validationを通過している場合、次を別々のconfirmationへ分割することを必須としない。

- Version ID発行
- Object Knowledge Version保存
- `current_version`切替
- Derived Search Representation更新

つまり、人間のdecision boundaryは原則「このResultをImportする」にまとめる。

### RESWF-04 — stale Resultは通常Importをblockする

Resultのbase Version / package binding等が現在状態と一致しない場合、silent rebase / mergeしてImportしない。

標準処理は次のいずれかへ送る。

- Package再生成 / 再分析
- 明示的review workflow
- 将来定義されるrebase機能

stale Resultの自動current promotionは禁止する。

### RESWF-05 — partial / limited Resultはreview-requiredを既定とする

B-04で定義したpartial / limited analysis / insufficient evidenceを含むResultについて、full snapshot omissionによるdata lossを避けるため、normal Resultと同一の無警告Importを標準にしない。

少なくとも次を人間が確認できることを要件とする。

- partialである理由
- current Versionから消えるKnowledge
- insufficient evidence Facet
- unresolved conflict / reference
- Import後にcurrentへ昇格する影響

人間が明示的にacceptした場合にpartial VersionをImport / current化することは許容する。

### RESWF-06 — conflictを含むことだけをImport失敗としない

Evidence-grounded conflictを構造化して保持できることはSGOKBの機能である。

したがってconflict存在だけでResultをrejectする必要はない。

ただしconflict状態はDiff / Review表示で確認可能にする。

### RESWF-07 — unresolved referenceはRelation自動作成を行わない

ResultをImportしても、unresolved referenceを架空Object IDへ変換して確定Relationを作らない。

Knowledge Version内の管理情報として保持するか、別stagingへ送るかはE / Hで決定する。

### RESWF-08 — Registry proposalはKnowledge Importから独立してreviewする

Knowledge Result自体をImportできる場合でも、同梱されたRegistry proposalを同時自動適用しない。

例えば、

```text
Result Knowledge → Import accepted
Registry proposal → Pending review
```

を許容する。

---

## 10. Import / Versioning / Derived Index更新

### IMPWF-01 — 正本変更のtransaction boundaryはSGOKB Importerが管理する

ユーザーがImportを開始した後、Validation済みResultから新Object Knowledge Versionを保存する処理はSGOKBが自動実行する。

ChatGPT / Result JSONがDB transactionやVersion IDを制御しない。

### IMPWF-02 — Version commit後の派生処理は自動化する

新Versionがaccepted / currentへ昇格した後、少なくとも次を自動更新可能にする。

- Search Representation
- Lexical Index
- Object overall Embedding
- Facet Embedding
- Statement Embedding
- Vector Index membership
- Similarity用representation
- 人間向けMarkdown等のderived representation

これらをユーザーが毎回個別実行しなくてもよい標準Workflowを目指す。

### IMPWF-03 — Derived Index失敗で正本Knowledgeを失わない

Version commit後のEmbedding / Vector Index等は再生成可能な派生処理である。

派生Index更新が失敗しても、accepted Knowledge Versionを破壊・rollbackすることを標準にしない。

代わりに、Indexがstale / pending / failedであることを検出し、retry / rebuild可能にする。

検索時に古いVectorを新current KnowledgeのVectorとしてsilent利用しない。

B-07ではstale / pending / failedの検出、canonical保全、Lexical fallback、full rebuild要件を定義した。Phase I / Nで実装・検証する。

### IMPWF-04 — deterministic / idempotentな派生更新を優先する

同じaccepted Knowledge、同じRepresentation Builder、同じEmbedding Spaceから再実行した場合に、不要なKnowledge Versionを増やさずIndexを再構築できることを目指す。

representation hashによるVector reuse等はPhase E / Iで設計する。

---

## 11. Human Reviewの基本方針

### REV-01 — 全Knowledgeを人間が逐語reviewすることを必須にしない

SGOKBはHuman-in-the-loopだが、人間がChatGPT出力の全Statementを毎回逐語検証しないと利用不能なシステムにはしない。

標準Workflowでは、

- ChatGPTへの分析依頼
- Result Importの明示開始

を人間control pointとし、normal Resultのsemantic line-by-line reviewはoptionalとする。

### REV-02 — 高リスク / 曖昧状態ではreviewを要求可能にする

次は標準でreview-requiredまたはblock対象にできる。

- stale binding
- partial / limited Result
- Registry proposal
- Object Identity ambiguity
- Source Identity ambiguity
- unknown Class / Relation Type
- destructive omission / large Diff
- provenance integrity failure
- external export warning

具体的severity / thresholdは後続設計で決定する。

### REV-03 — Review結果を元データ上書きで表現しない

人間がAI出力を修正する場合も、原Result artifact / hashを失わない。

review後の修正をどのようにResult revision / manual edit provenanceとして保持するかはH-02 / H-04で設計する。

---

## 12. 1 Objectあたり自動処理時間の定義

### PERF-01 — 目標はSGOKB-controlled local automationで概ね10分以内

1 Objectの標準Knowledge生成 / 更新workflowについて、**SGOKBが制御できるlocal automatic processingの合計を概ね10分以内**とすることを目標とする。

B-07で非機能要件 / 測定条件を`NON_FUNCTIONAL_REQUIREMENTS.md`として具体化済みである。

### PERF-02 — 10分目標へ含める処理

少なくとも標準benchmarkでは次を含める。

#### Pre-analysis local segment

- Object Evidence Retrieval
- Package selection / budget処理
- Package manifest / instructions生成
- local Package build
- package preflight

#### Post-analysis local segment

- Result parse / Validation
- Diff生成
- Version Import transaction
- current promotion
- Object / Facet / Statement Search Representation生成
- incremental Embedding
- Vector / Lexical Index update
- standard derived rendering

複数回の自動retryが通常成功経路に含まれるなら、その時間も含める。

### PERF-03 — 10分目標から除外する処理

次はSGOKB側の1 Object local automatic processing目標から除外する。

- ユーザーがSourceを探す時間
- BrowserでSourceを読む / Capture対象を選ぶ時間
- Source Capture時のWeb/network待ち
- 初回Source Import / Normalizeを別途行う時間
- Package内容を人間がreview / editする時間
- Google Drive等external syncのnetwork待ち
- ChatGPTを開く / Packageを指定する時間
- ChatGPTの生成待ち時間
- ChatGPTとの追加対話時間
- result.jsonを取得してincomingへ戻す人間操作時間
- review-required Resultを人間が判断する時間

Source ingestion性能はB-07のObject workflow Acceptanceとは分離し、Phase Nで別metricとして測定可能とする。

### PERF-04 — 外部Service latencyをlocal benchmarkへ混ぜない

標準benchmarkはlocal Embedding Provider等、再現可能な環境条件で測る。

外部Embedding / Reranker等をoptional構成として使用する場合、そのnetwork/service latencyは別指標として記録し、local SGOKB処理性能と混同しない。

### PERF-05 — 10分は平均値だけで達成扱いにしない

B-07でObject規模、Evidence数、Statement数等のStandard / Large profileを定義済みであり、N-05で分離測定する。

B-07ではStandard Objectのp95 10分をAcceptance targetとし、Large profileはp95 20分targetとして別集計する。

---

## 13. UI / CLI要件

### UIWF-01 — 人間のdecision boundaryを操作名で明示する

UI / CLIは、read-only / local build / external export / authoritative importを利用者が区別できるようにする。

例えば概念上、次を同一の曖昧な「process」操作へまとめない。

- Build Package
- Export Package
- Validate Result
- Import Result
- Apply Registry Proposal

具体的command / button名はPhase Mで決定する。

### UIWF-02 — 外部side effectを表示する

Google Drive sync directoryへのwrite、cloud AI invocation、remote serviceへのEmbedding送信等、local machine外へdataが出る操作はUI / CLI上で識別可能にする。

### UIWF-03 — 状態と次の人間操作を表示可能にする

Object / Package / Result workflowについて、少なくとも論理上次のような状態を区別できることを目指す。

- local processing
- ready for export
- exported / awaiting external analysis
- result received
- validation failed
- review required
- ready to import
- imported
- derived index pending / failed / ready

最終state machineはPhase G / H / Mで決定する。

### UIWF-04 — dry-run / previewを許容する

外部exportやImport等のside effect前に、対象・変更・警告をpreviewできる設計を許容する。

少なくともPackage preflightとResult Diffは標準的なpreview材料とする。

---

## 14. Audit / Provenance of Operations

### AUD-01 — 重要操作の実行来歴を追跡可能にする

少なくとも次のeventを監査可能にすることを目指す。

- Source Import
- Package Build
- Package Export
- Result Validation
- Result Import
- Registry proposal apply / reject
- Version promotion / rollback
- Index rebuild

全eventを同一巨大logへ保存する物理方式は本タスクでは決めない。

### AUD-02 — manual / automatic originを区別可能にする

処理が人間操作、deterministic rule、scheduled job等のどのtriggerから開始されたかを後から識別できる設計とする。

### AUD-03 — External Exportはdestinationとartifact identityを監査可能にする

少なくとも標準Package Exportでは、

- package ID / hash
- destination profile
- timestamp
- export outcome

を追跡可能にすることを目指す。

外部サービス側の実際の保持・削除状態までSGOKBが保証するものではない。

---

## 15. 標準Workflowの具体例

### 15.1 Sourceを追加する

```text
[Human]
Webページを「保存する価値がある」と判断
 ↓
Captureを実行
 ↓
[Auto Local]
Bundle検証 → Import → Snapshot → Normalize → Evidence → Search Index
 ↓
[Human only if needed]
Source Identity ambiguity / warningをreview
```

### 15.2 新しいObjectを登録する

```text
[Human]
Object candidateを確認
 ↓
Object作成を承認
 ↓
[Auto Local]
object_id発行 / Registry record作成
```

### 15.3 Object Knowledgeを新規生成する

```text
[Human]
対象Objectを指定
 ↓
[Auto Local]
Evidence Retrieval → Package Build → preflight
 ↓
[Human]
Package Exportを実行
 ↓
[External Manual]
Drive → ChatGPT → result.json取得
 ↓
[Auto Local]
Result Validation / Diff
 ↓
[Human]
Importを実行
 ↓
[Auto Local]
Version保存 → current化 → Embedding / Index / Markdown更新
```

### 15.4 Object Knowledgeを更新する

```text
[Human]
Object更新を開始
 ↓
[Auto Local]
current Version + grounding Evidence + new EvidenceからPackage構築
 ↓
[Human / External]
Export → ChatGPT再分析 → Result返却
 ↓
[Auto Local]
base Version / package / Evidence validation + Diff
 ↓
[Human]
Import
 ↓
[Auto Local]
新Version作成 → current切替 → Incremental Embedding / Index更新
```

### 15.5 Resultがpartialだった場合

```text
Result validation
 ↓
partial / limited detected
 ↓
Review Required
 ↓
[Human]
current Versionとの差分・不足理由を確認
 ├─ reject / regenerate
 └─ explicitly accept
       ↓
     Import / current promotion
```

### 15.6 Resultがstaleだった場合

```text
Result(base v3)
Current = v4
 ↓
Stale detected
 ↓
通常Import block
 ↓
[Human]
Package再生成 / 再分析 / 将来rebase workflow
```

---

## 16. 自動化しないことを標準とする項目

B-06時点の標準Workflowでは、次を無人自動処理へしない。

1. Web全体からのSource自動採用。
2. AIによるPersistent Object Identityの自動確定。
3. ambiguous Source / Object merge。
4. Packageの外部export（明示reusable policy設定時を除く）。
5. ChatGPT Web/Desktopの標準自動操作。
6. Result検出だけをtriggerとする正本Knowledgeのsilent import。
7. stale Resultのsilent merge / rebase。
8. Registry proposalの自動適用。
9. unresolved referenceからの自動Object / Relation作成。
10. validation errorの意味推測修復。

これらを将来optional automationへ拡張する場合も、正本・外部送信・Identityのboundaryを明示的に再設計する。

---

## 17. 自動化を推奨する項目

人間の反復作業を減らすため、標準Workflowでは次の自動化を推奨する。

1. Capture済みBundleのlocal Import / integrity check。
2. Normalize / Evidence generation。
3. FTS / Evidence Embedding更新。
4. Object Evidence Retrieval。
5. Package selection / manifest / instructions生成。
6. Package preflight生成。
7. Result parse / machine Validation。
8. current Versionとの差分生成。
9. 明示Import後のVersion transaction。
10. Search Representation生成。
11. Object / Facet / Statement Embeddingのincremental更新。
12. Vector / Lexical Index更新。
13. Markdown等のderived rendering。
14. Index retry / rebuild等のlocal maintenance。

---

## 18. 既存Prototypeからの変更点

旧Prototypeでは、

```text
Capture
 ↓
Import
 ↓
全EvidenceをLocal Generative LLMへ投入
 ↓
大量Fragment生成
 ↓
Final Document生成
```

という「自動生成Pipeline自体」が中心だった。

新Workflowでは、

```text
Curated Source / Object selection
 ↓ Human
Deterministic local processing
 ↓ Auto
Evidence Package
 ↓ Human-controlled external boundary
High-capability AI analysis
 ↓ Human-controlled return
Machine Validation
 ↓ Human-controlled authoritative import
Versioned Knowledge + Derived Search Index
 ↓ Auto
```

とする。

変更の中心は、**自動化率を最大化するのではなく、意味判断・外部送信・正本更新のdecision boundaryを明示したうえで、その間の反復処理を最大限自動化すること**である。

---

## 19. 後続Phaseへの引き継ぎ

### B-07 Non-functional requirements

- local / offlineで成立する最低限機能。
- External processing / data egressのsecurity / privacy要件。
- Source / Result / Package / Indexのintegrity。
- 10分目標のbenchmark条件、通常 / 大規模workload、p95等のAcceptance。
- Background job failure / retry / recovery。
- Index stale時のgraceful degradation。
- backup / retention / hard delete。

### Phase F

- Capture済みBundleのautomatic Import境界。
- effective Snapshot / Normalized Run選択policy。
- candidate / confirmed / excluded Source↔Object association workflow。
- Package Retrieval selection reason / manual override。

### Phase G

- local Package stagingとExternal Exportを分離するdirectory / command設計。
- Google Drive sync directoryへのexport operation。
- export preflight / manifest / destination profile。
- Result incoming layout。
- ChatGPT手動運用手順。

### Phase H

- validation state machine。
- normal / stale / partial / review-required ResultのImport policy。
- explicit Import operation。
- Diff / Review UI。
- Registry proposalの別review queue。
- Import transactionとpost-import derived processing境界。

### Phase I

- local Embedding Providerを標準benchmarkとする。
- 外部Embedding Providerを利用する場合のexternal processing境界。
- Version commit後のincremental Embedding / Index update job。
- stale / failed Indexの検出・rebuild。

### Phase M

- Build / Export / Validate / Import / Apply Proposalを別command / actionとして表現する。
- dry-run / preflight / status表示。
- external side effectの表示。

### Phase N

- manual timeとlocal automatic processing timeを別計測する。
- 1 Object automated segmentの10分目標をN-05で評価する。
- stale / partial / export boundary / Index failureのintegration / recovery testを追加する。

---

## 20. B-06で意図的に決めない事項

次は後続Taskへ延期する。

- 具体的CLI command名。
- GUI画面 / button配置。
- filesystem watcherの採否。
- background job queue実装。
- exact workflow state enum。
- Google Drive具体directory / sync方法。
- persistent export policyの最終Schema。
- sensitivity classificationの最終語彙。
- external provider credential管理。
- Result review severity / Diff threshold。
- partial Resultの最終status enum。
- stale Result rebase algorithm。
- operation audit logの物理table / file形式。
- 10分Acceptanceの最終hardware / dataset / p95条件。

---

## 21. 完了条件への対応

### 人間工程と自動工程を分離した

Source / Object選定、External Export、ChatGPT操作、Result authoritative Import、Registry変更をHuman Decisionとして分離した。

Import / Normalize / Evidence、Package Build、Validation、post-import Embedding / Index等をautomatic processingとして定義した。

### 1 Object自動処理10分の範囲を定義した

Package Buildまでのpre-analysis local segmentと、Result受領後のValidation / Import / Embedding / Index等post-analysis local segmentを対象とした。

ChatGPT操作、人間review、external network待ちは除外した。

### External Export境界を定義した

Capture / Importと外部送信許可を分離し、Package BuildとPackage Exportも別操作とした。

Google Drive同期directoryへのwriteや外部Embedding Provider利用もdata egressとして扱う。

### Human Reviewを過剰必須化しなかった

normal Resultではexplicit Importを人間decision boundaryとし、全Statement逐語reviewを必須にしない。

stale / partial / Registry proposal / Identity ambiguity等はreview-requiredへ送る。

---

## 22. 結論

SGOKBの標準Workflowは、**人間が選定・外部送信・正本更新という重要decisionを制御し、そのdecision間の再現可能なローカル処理をSGOKBが自動化する**方式とする。

この分離により、完全自動化のために低品質な生成AI判断を大量に組み込む必要をなくしつつ、Import / Retrieval / Validation / Versioning / Embedding / Index更新等の反復作業は自動化できる。

標準Knowledge生成ではGoogle Drive / ChatGPTを正式なHuman-in-the-loop工程として扱い、その人間・外部Service時間を1 ObjectあたりのSGOKB local automatic processing目標から分離する。

B-06は以上をもって完了とし、B-07非機能要件も完了したため、次はPhase Cへ進む。

**Status: Complete (2026-10-11)**
