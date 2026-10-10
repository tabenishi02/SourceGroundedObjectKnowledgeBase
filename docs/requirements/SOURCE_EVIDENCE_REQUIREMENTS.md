# Source Grounded Object Knowledge Base — Source / Evidence要件

更新日: 2026-10-10

- Task: `B-03 [P0] Source / Evidence要件を再確認する`
- Status: Accepted
- Parent: Phase B — 要件定義の全面更新
- Inputs:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
  - `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
  - `docs/reference/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`
  - `extensions/web-page-capture/docs/CAPTURE_BUNDLE_FORMAT.md`
- B-04 result: `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
- Next: `B-05 [P0] 検索要件を定義する`

---

## 1. 目的

本書は、SGOKBでObject Knowledgeの根拠となる **Source / Snapshot / Raw Artifact / Normalized Run / Evidence** の論理要件を定義する。

再設計後のSGOKBでは、Source / Evidenceを単なるLLM入力用中間データではなく、次の目的を持つ長期資産として扱う。

- Object Knowledgeの根拠を後から確認できる。
- Extractorや検索方式を変更してもRawから再処理できる。
- Source更新前後を比較できる。
- 異なるSourceの一致・相違・矛盾を保持できる。
- Evidence Retrievalを生成LLMなしで実行できる。
- ChatGPTが生成したKnowledgeと一次資料を混同しない。
- 将来の検索・監査・再生成で同じEvidenceを再利用できる。

本書は論理要件を定義する。SQL table / column、具体的ID形式、JSON Schema、Evidence Linkの物理schema、token budget、chunk size等は後続Phaseで決定する。

---

## 2. 結論

SGOKBは次のProvenance chainを採用する。

```text
Source
  ↓ 0..N
Snapshot
  ↓ 1..N
Raw Artifact
  ↓
Normalized Run
  ↓ 0..N
Evidence
  ↓
Evidence Link / Retrieval Selection
  ↓
Object Knowledge Version / Facet / Relation
```

それぞれの責務は次のように分離する。

| 概念 | 責務 |
|---|---|
| Source | 情報源・資料そのものの論理Identity |
| Snapshot | あるSourceを特定時点・特定方法で観測/取得した記録 |
| Raw Artifact | Capture / Importで得た原資料。原則不変 |
| Normalized Run | Rawから検索・解析可能な構造へ変換した処理世代 |
| Evidence | 1 Snapshotへ必ず遡れる、意味を書き換えない検索・引用単位 |
| Object Knowledge | Evidenceを根拠として統合・解釈したVersioned Knowledge |

**Source / EvidenceはObject Knowledgeの根拠であり、Object Knowledgeそのものではない。**

---

## 3. Sourceの定義

### SRC-01 — Sourceは情報源の論理Identityとする

Sourceは、ユーザーが資料として扱う情報源・文書・Resourceの論理的存在を表す。

Web Sourceの場合でもSource IdentityをURLそのものと同一視しない。

```text
Source Identity
  ├─ locator / URL 1
  ├─ locator / URL 2
  ├─ Snapshot A
  ├─ Snapshot B
  └─ Source metadata
```

SourceはObject、Snapshot、ファイルパス、Capture IDとは独立したIDを持つ。

### SRC-02 — `source_id`をURL・ファイルパス・titleから独立させる

`source_id`は少なくとも次を唯一のIdentity根拠としてはならない。

- URL
- canonical URL
- page title
- local file path
- capture filename
- content hash
- site名
- Source classification

URL変更、redirect、サイト移転、ローカル保存先変更があっても、同一論理Sourceであると確認できる場合は同じ`source_id`を維持できることを要件とする。

具体的ID形式は後続schema設計で決定する。

### SRC-03 — 同一URLをSource Identityの絶対条件にしない

現行Prototype DBでは`url UNIQUE`をSource Identityに近い制約として利用しているが、現行要件ではこれを論理正本とはしない。

次のケースを扱える必要がある。

- 同じ資料がURL変更・サイト移転する。
- canonical URLと実URLが異なる。
- tracking query等を含む複数URLが同じ資料を指す。
- 同一URLが後年まったく別内容へ再利用される。
- Web以外の書籍、PDF、Dataset、画像、音声等をSourceとして扱う。

URL一致だけでSourceを自動mergeしてはならず、URL不一致だけで必ず別Sourceと判定してもならない。

### SRC-04 — Sourceは0件以上のlocatorを持てる

Sourceは取得元・参照先を示すlocatorを0件以上持てる論理構造とする。

例:

- Web URL
- canonical URL
- DOI
- ISBN + edition情報
- repository / release URL
- local import reference
- その他の外部識別子

locator自体をSGOKBのSource Identityとして再利用しない。

### SRC-05 — SourceとSnapshotを分離する

同一Sourceについて時間経過や取得方法の違いにより複数Snapshotを保持できなければならない。

```text
Source A
  ├─ Snapshot 2026-01-01
  ├─ Snapshot 2026-05-01
  └─ Snapshot 2026-10-10
```

Source更新によって過去Snapshotを上書きしてはならない。

### SRC-06 — Publication editionとSnapshotを混同しない

Snapshotは「同一論理Sourceを観測した時点」である。

内容・版・release自体が独立して引用・比較すべき別資料である場合は、単なるSnapshot差ではなく別Sourceとすることを許容する。

例:

- 同じWeb記事の更新前後 → 原則同一Sourceの複数Snapshot
- 書籍の初版と大幅改訂版 → 独立Sourceとして扱える
- Datasetの明示Versionが独立引用単位 → 別Sourceとして扱える

Source continuityの詳細判定をURLやhashだけで完全自動化してはならない。

### SRC-07 — SourceとObjectを多対多とする

Objectは特定Sourceに所有されず、Sourceも特定Object専用ではない。

```text
Object A ─┬─ Source 1
          ├─ Source 2
          └─ Source 3

Source 4 ─┬─ Object A
          ├─ Object B
          └─ Object C
```

SourceとObjectの関連は「このSourceがこのObjectについて関連資料である」ことを示し、特定のKnowledge claimが正しいことを直接意味しない。

### SRC-08 — Object関連候補と確認済み関連を区別できること

Page Contextや検索により推定された`subject_candidates`等を、確認済みObject関連へ自動昇格させない。

少なくとも論理上、次を区別可能とする。

- candidate: 自動検索・抽出等で関連候補となった
- confirmed: 人間または明示的規則で関連を採用した
- excluded: 関連候補から明示的に除外した

物理状態名とUIはPhase Fで決定する。

### SRC-09 — Source recordとObject recordを分離する

同じ実体がSource roleとObject roleの両方を持つことを許容するが、recordは分離する。

例:

- 書籍を参考資料として使う → Source
- その書籍自体を作品として分析する → Work Object
- Software repositoryを仕様根拠に使う → Source
- SoftwareそのものをKnowledge対象にする → Software Object

Source IDとObject IDを同一IDに強制しない。

---

## 4. Source classification要件

### SRC-10 — 1つの`source_type`へ異なる意味軸を混在させない

旧Prototypeの`source_type`には、`official`, `wiki`, `news_article`, `social_post`等、異なる分類軸が混在していた。

現行要件では少なくとも次の軸を分離する。

| 軸 | 答える質問 | 例 |
|---|---|---|
| `resource_type` | 何というResource形態か | web_page, publication, document, dataset, image, audio, video, software_resource |
| `media_type` | 実データ形式は何か | text/html, application/pdf, image/png |
| `document_genre` | どのような資料ジャンルか | profile, interview, news_report, encyclopedia, review, manual, academic_paper |
| `publisher_kind` | 発行主体はどの種類か | government, academic, editorial, organization, individual, community, anonymous, unknown |
| `subject_relationship` | **特定Objectとの関連において**発行主体が対象とどの関係か | first_party, affiliated, independent, community, unknown |
| `site` / provider | どのサイト・Providerか | wikipedia, official site, GitHub等 |
| `page_purpose` | そのページの主目的は何か | character_profile, guide, discussion, product_description等 |

`subject_relationship`だけはSource単体へ固定する普遍属性ではなく、Source↔Object association側のcontextual metadataとして扱う。同じSourceでもObject Aには`first_party`、Object Bには`independent`となり得る。その他の軸の物理field名やregistry方式は後続設計で決定する。

### SRC-11 — Source分類はObject Class hierarchyから独立させる

Character Source専用Type、Work Source専用TypeのようにObject Classへ密結合させない。

同じInterview SourceがPerson、Character、Work、Concept等の複数ObjectにEvidenceを提供できる構造とする。

### SRC-12 — 初期Source分類語彙を閉じたDB enumに固定しない

新しいSource genre / media / publisher categoryの追加でSource table schema変更を要求しない。

初期候補として少なくとも次を扱えることを想定する。

#### Resource type候補

- `web_page`
- `collection`
- `publication`
- `document`
- `dataset`
- `image`
- `audio`
- `video`
- `software_resource`
- `physical_reference`
- `other`

#### Document genre候補

- `profile`
- `portal`
- `reference`
- `encyclopedia`
- `wiki`
- `interview`
- `news_report`
- `article`
- `blog`
- `review`
- `criticism`
- `discussion`
- `social_post`
- `specification`
- `manual`
- `documentation`
- `academic_paper`
- `dataset_record`
- `chronology`
- `map`
- `store_listing`
- `generic`

この一覧は外部Ontology全体を取り込むものではなく、B-03時点の初期語彙候補である。

### SRC-13 — Sourceへ単一の「信頼度スコア」を正本として持たせない

Sourceの有用性・権威性は、対象Object、claim、時点、資料の性質によって変化する。

そのため、Source全体に`trust = 0.93`等の普遍的真実性スコアを付け、それだけでEvidence採否を決定する方式は採用しない。

代わりに、publisher / genre / publication date / provenance等のSource metadataと、Objectごとのsubject relationship等のassociation metadataを保持し、後段のEvidence Selectionや人間判断で利用する。

### SRC-14 — 観測値・推定値・overrideを区別する

Source / Page Context metadataは、少なくとも次の由来を区別可能とする。

- captured / observed: Rawから直接取得した値
- deterministic: 明示規則で導出した値
- inferred: heuristic / model等で推定した値
- override: 人間が明示的に修正した値

`inferred`や`override`で元観測値を消去してはならない。

現行`page_contexts`のdeterministic / inferred / overrides / effectiveという考え方は継続利用できる。

### SRC-15 — GlobalなPrimary / Secondary Source判定をSource identityへ固定しない

「一次資料か二次資料か」はclaimや用途に依存する場合があるため、Source recordの普遍的Identity属性として単純化しない。

必要な場合はSource genre / Source↔Objectのsubject relationship / Evidence Link側の利用目的等から後段で判断する。

### SRC-16 — Source metadataは基本的な書誌・記述情報を保持できる

Source種別に応じ、論理上少なくとも次の情報を保持可能とする。

- human-readable title / label
- creator / author表記
- publisher表記
- language
- published / updated time
- external identifier
- locator
- resource / genre分類
- rights / license等、Rawから取得可能な利用条件metadata

すべてを必須fieldとはしない。値が不明な場合に推測で埋めず、Raw観測・deterministic・inferred・overrideの由来を維持する。

Creator / PublisherがSGOKB Objectとして登録済みでも、Source metadata上の原表記を失わない。必要に応じて別途Object参照を付けられる設計とする。

### SRC-17 — 発見候補と採用済みSourceを分離する

検索結果、LLM提示URL、外部リンク等でSource候補を発見しても、それだけで保存済みSource / Evidenceと同等に扱わない。

SGOKBへ明示的にCapture / Import / 登録され、Provenanceを保持できる状態になって初めてSource Storeの正式Sourceとして扱う。候補提示機能を将来追加する場合も、採用済みSourceと状態を分離する。

---

## 5. Snapshot / Raw Artifact要件

### SNP-01 — Snapshotは取得時点の観測記録とする

Snapshotは1 Sourceに対する1回の取得・観測を表す。

最低限、論理上次を追跡できることを要件とする。

- `snapshot_id`
- `source_id`
- captured / observed timestamp
- import timestamp
- capture / import method
- capture tool / format version
- observed locator / URL
- title等の取得時metadata
- completeness / warnings
- Raw Artifact参照
- Raw content hash

### SNP-02 — Snapshotを不変履歴として保持する

正常に登録されたSnapshotのRaw内容を後から直接書き換えてはならない。

Sourceを再取得した場合は新Snapshotを追加する。

Metadata訂正が必要な場合も、Raw観測内容と人間による訂正を区別できることを優先する。

### SNP-03 — 同一content hashでも別Captureを自動統合しない

同一内容を異なる時点で取得した事実自体に価値があるため、Raw hashが一致してもSnapshotを自動削除・統合しない。

content hashは次に利用できる。

- integrity check
- duplicate候補検出
- change detection
- regression test

ただしIdentityそのものにはしない。

### SNP-04 — 同一Capture Bundleの二重Importを防止する

Web Capture Bundleでは`capture_id`を利用して同一Bundleの重複Importを防止する既存方針を維持する。

同一URLを別時点にCaptureしたBundleは別Snapshotとして保持する。

### SNP-05 — Raw Artifactは可能な限り原形を保持する

Web Captureの場合、Raw Artifactには少なくとも利用可能な範囲で次を含める。

- Rendered DOM
- manifest
- HTML metadata
- structured data raw representation
- frame情報
- shadow DOM情報
- MHTML
- checksum

Capture Bundle format自体はSGOKBのSource分類・Evidence schemaへ依存させない。

### SNP-06 — Raw pathをIdentityとしない

Raw BundleやArtifactの保存先は変更可能でなければならない。

Snapshot/Evidenceからの参照はstable ID + checksum等で追跡できる設計とし、絶対path変更だけでSource/Snapshot/Evidence identityを失わない。

### SNP-07 — Capture completenessを保存する

partial captureをsuccessと同一視しない。

Main DOM、Frame、MHTML、Shadow DOM等の取得可否・warningを後から確認できなければならない。

ただしCaptureがpartialであることだけを理由に自動的にEvidence利用不可とする必要はない。利用可能範囲と欠落範囲を追跡できることを優先する。

### SNP-08 — 「最新Snapshot = 正しいSnapshot」と自動決定しない

通常処理で利用するSnapshotを選択する場合、単純なcapture timestamp最大値だけを唯一の基準にしない。

例えば最新Captureがerror page、ログイン切れ、部分取得等である可能性を考慮する。

どのSnapshotを既定処理対象とするかのselection policyはPhase F / schema設計で具体化するが、過去Snapshotを破壊せず選択を変更できなければならない。

---

## 6. Normalized Run要件

### NOR-01 — Normalized RunをRawとは別の派生世代とする

NormalizationはRaw Artifactから本文・構造・metadataを検索・Evidence生成しやすい形へ変換する処理である。

Raw Artifactそのものを書き換えない。

```text
Raw Snapshot
  ↓ extractor/config v1
Normalized Run A

Raw Snapshot
  ↓ extractor/config v2
Normalized Run B
```

### NOR-02 — 再処理で旧Runを破壊しない

Extractor、noise filter、chunking、parser等を変更して再処理する場合、新Normalized Runを作成する。

旧RunとそのEvidenceを監査・比較できるように保持する。

### NOR-03 — 処理構成を追跡できること

Normalized Runは少なくとも次を再現可能な程度に記録できることを要件とする。

- Snapshot ID
- Extractor / parser identity
- implementation / configuration version
- normalization options
- created_at
- output structure / blocks
- processing status

具体的SchemaはPhase Fで決定する。

### NOR-04 — 失敗した再処理で正常世代を置き換えない

新Normalized Runが失敗・不完全となった場合、既存の正常なactive/effective runを不可逆に失わない。

現行`active_run`思想は維持できる。

### NOR-05 — Raw位置との対応を保持する

Normalized blockから元Raw Artifactの位置へ可能な限り遡れることを要件とする。

Web HTMLならDOM path / section / block order等、PDFならpage等、Source種別に応じたlocation情報を保持できる設計とする。

---

## 7. Evidenceの定義

### EVD-01 — Evidenceは単一Snapshotへ遡れる根拠単位とする

Evidenceは、Source中の情報を検索・引用・Object Evidence Packageへ利用できる単位に分割したものとする。

Evidenceは必ず1つのNormalized Run / Snapshot / Source chainへ遡れなければならない。

```text
Evidence
  → Normalized Run
  → Snapshot
  → Raw Artifact
  → Source
```

1つのEvidence recordの中で複数Sourceを統合しない。

### EVD-02 — Evidenceは意味を書き換えない

Evidenceは原資料の意味を保持した抽出・正規化単位でなければならない。

許容例:

- 原文引用相当のtext block
- whitespace / line breakの正規化
- heading階層を保持した本文block
- tableを意味を保って構造化した表現
- HTML metadata / JSON-LDから取得した明示値
- OCR / transcription結果（変換由来を明示できる場合）

Evidenceそのものとして扱わないもの:

- LLMによる要約
- 複数Sourceの統合説明
- 推論した性格・テーマ・因果関係
- 生成翻訳を原文Evidenceの代替として扱うこと
- ChatGPTが生成したObject Knowledge

### EVD-03 — Generative LLM出力を一次Evidenceとしない

ChatGPTやローカル生成LLMが返した文章は、SGOKBが保持する一次資料Evidenceへ自動昇格させない。

LLM出力はObject Result / Derived Data / Analysisとして管理し、根拠は保存済みEvidence IDを参照する。

LLMが新しいURLや引用を提示しても、そのResourceをSGOKBへ明示的にImport/CaptureしEvidence化するまでは既存Evidenceと同等に扱わない。

### EVD-04 — EvidenceはObjectから独立して再利用可能とする

Evidenceは特定Object専用に生成しない。

同じEvidenceを複数ObjectのEvidence Retrieval / Evidence Linkで利用できる。

```text
Evidence E1
  ├─ relevant to Character A
  ├─ relevant to Work B
  └─ relevant to Theme C
```

Object削除・ArchiveによってEvidence自体を削除してはならない。

### EVD-05 — `evidence_id`をcontent hashと同一視しない

Evidenceはstable reference可能なIDを持つが、content hash自体をEvidence Identityとしてはならない。

同じ文字列が異なるSource・Snapshot・位置に存在する場合、それぞれ異なるEvidenceとしてProvenanceを保持できなければならない。

### EVD-06 — 再NormalizationでEvidence IDの永続一致を要求しない

Extractor / chunking変更によりEvidence境界が変わるため、新Normalized Runで生成されたEvidenceは新世代として扱う。

旧Evidence IDを新Evidenceへ無理に再利用しない。

既存Evidence IDは過去Version / legacy provenanceのため保持する。

### EVD-07 — Evidence位置を人間が検証できること

EvidenceはSource種別に応じて元資料内位置を示せなければならない。

例:

- HTML: heading path, block order, DOM path等
- PDF / book: page / section
- audio / video: timestamp range
- dataset: record / row / key
- image: region / caption / associated metadata
- structured metadata: JSON path / metadata field

具体的locator schemaはPhase F / E-03で決定する。

### EVD-08 — Evidence granularityをSource構造に沿わせる

Evidenceは固定文字数だけで機械的に分割することを要件としない。

section、paragraph、list、table、post、reply等の意味構造を優先し、必要に応じてsize budgetでchunk化する。

Evidenceが大きすぎて検索不能、または小さすぎて文脈を失う状態を避ける。

具体的token / character budgetはF-04で決定する。

### EVD-09 — chunk overlapを許容するがProvenanceを失わない

文脈維持のためEvidence間に内容重複を許容する。

重複がある場合もsection / order / source locationを保持し、検索結果で同一Source由来の近接chunkをまとめられる設計を可能とする。

### EVD-10 — Evidence content hashを保持できること

Evidence content hashは次の用途に利用可能とする。

- integrity確認
- 同一/近似Evidence候補検出
- Embedding再生成判定
- regression比較

hash一致を理由に別SourceのEvidenceを破壊的mergeしてはならない。

### EVD-11 — Evidence extraction modeを区別できること

Evidenceがどの変換を経たかを追跡できることを要件とする。

少なくとも論理上、次のような区別を表現可能とする。

- `verbatim`: 原文をそのまま抽出
- `normalized`: 空白・構造等だけを正規化
- `structured`: table / metadata等を意味を保って構造化
- `transcribed`: OCR / ASR等で文字化

実際の名称やSchemaはPhase Fで決定する。

transcription等に不確実性がある場合、その処理方法・engine・warningを追跡できなければならない。

### EVD-12 — Translationは原Evidenceを置換しない

検索支援等で翻訳表現を生成することは許容するが、翻訳文を原Evidenceそのものとして原文と置き換えない。

翻訳を保存する場合は原Evidenceを参照する派生Artifactとして区別する。

### EVD-13 — Evidenceは「Sourceがそう記述している」ことの根拠であり、真実性そのものではない

Evidence recordが存在することは、その内容が客観的事実として正しいことを意味しない。

SGOKBは、誤情報・意見・主観・作品内設定・相互に矛盾する記述であっても、Sourceがその内容を実際に記述しているならEvidenceとして保持できる。

真実性、採用claim、矛盾解決、Fact / interpretation等の判断はEvidence Store自体へ不可逆に埋め込まず、Object Result / Evidence Link /後段分析で根拠付きに扱う。

---

## 8. Provenance要件

### PRV-01 — Object KnowledgeからRawまで追跡可能にする

最終的に次の追跡経路を構築できなければならない。

```text
Object Knowledge Version / Facet / Relation
  ↓ Evidence Link
Evidence
  ↓
Normalized Run
  ↓
Snapshot
  ↓
Raw Artifact
  ↓
Source
```

Evidence Linkの具体的SchemaはE-03、Object Result側の参照契約はB-04で決定する。

### PRV-02 — Provenanceの途中をLLM生成文で置換しない

「ChatGPTがそう判断した」をSource Provenanceとして扱わない。

ChatGPTによるsynthesisと、synthesisに使ったEvidence IDを別に記録できる構造とする。

### PRV-03 — Publication time / Capture time / Import timeを分離する

少なくとも次の時間概念を混同しない。

- Sourceが公開された時刻
- Sourceが更新された時刻
- Snapshotを取得した時刻
- SGOKBへImportした時刻
- Normalized Runを生成した時刻
- Evidenceを生成した時刻

取得時刻を公開日時の代わりに使用してはならない。

### PRV-04 — Source metadataの由来を保持する

publication date、publisher、genre等がRaw観測値かdeterministic inferenceかmanual overrideか追跡可能とする。

### PRV-05 — Source間の依存関係を記録可能にする

複数Sourceが独立情報源とは限らないため、判明している場合はSource間に次のような関係を表現できる設計とする。

- cites
- quotes
- derived_from
- mirror_of
- syndicated_from
- transcript_of
- reproduction_of

Relation名と物理schemaは後続設計で確定する。

不明なSource independenceを推測で確定しない。

---

## 9. 重複・矛盾・変更の扱い

### CON-01 — 異なるSourceの重複Evidenceを不可逆に統合しない

複数Sourceが同じ内容を記述していても、Source provenanceを失う形で1件へ統合しない。

検索結果・Evidence Packageで重複抑制することは許容するが、Store上のSource/Evidence provenanceは保持する。

### CON-02 — Source間の矛盾をEvidence層で解決しない

異なるSourceが異なる内容を記述している場合、Evidence生成時に一方を削除・上書きしない。

```text
Source A → Evidence: X
Source B → Evidence: not X
```

を保持し、Object Knowledge生成時にEvidence参照付きで判断できるようにする。

### CON-03 — 同一Sourceの時間変化を保持する

Source内容が更新された場合、新Snapshotを追加し、旧SnapshotとEvidenceを保持する。

Knowledge生成時にどのSnapshot generationを使用したか追跡可能にする。

### CON-04 — 削除済みWeb内容も過去Snapshotとして保持できる

元URLが404や削除状態になっても、過去に正当にCaptureしたSnapshotを自動削除しない。

Source availabilityとSnapshot preservationを別問題として扱う。

---

## 10. Source / Evidence lifecycle

### LIFE-01 — Source ArchiveでEvidence履歴を破壊しない

Sourceを通常利用対象から外しても、過去Object Knowledgeが参照するSnapshot / Evidenceを保持できなければならない。

### LIFE-02 — Hard deleteを通常操作にしない

Raw Artifact / Snapshot / EvidenceがKnowledge Versionから参照されている場合、通常操作で破壊的削除しない。

retention / backup / hard deleteの具体方針はB-07および後続運用設計で決定する。

### LIFE-03 — Provenance破損を検出可能にする

DB recordが存在するのにRaw Artifactが失われた、checksum不一致、Evidence親Runが欠落した等の状態を検出可能にする。

Provenanceが壊れたEvidenceを正常Evidenceと同一扱いで新規Knowledge生成へ利用しない。

---

## 11. Evidence StoreとEvidence Packageを分離する

### PKG-01 — Evidence Storeは保持層、Packageは選択結果とする

Source / Evidence Storeは取得・生成されたEvidenceを保持する。

Object Evidence Packageは特定Objectの分析のために、そのStoreから選択した一時的/再生成可能な集合である。

```text
Evidence Store
  ↓ Retrieval / Selection
Object Evidence Package
```

Packageに含まれなかったEvidenceを削除・低品質と断定してはならない。

### PKG-02 — Package selection理由を追跡可能にする

F-03 / F-04では、name / alias / explicit link / FTS / semantic similarity / manual include等、EvidenceがPackageへ選ばれた理由を追跡可能にする。

size budgetによって除外した場合も、少なくとも選択処理の設定・理由を監査できることを目指す。

### PKG-03 — Evidence Packageは新しいSource of truthではない

Google Drive等へexportしたPackageは交換用派生物であり、Source / Evidence Storeの正本にならない。

Package fileが失われてもDB + Rawから再生成可能であることを目指す。

---

## 12. Class family別Source coverage

B-02Dで採用したClassが少数のSource genreへ偏らないよう、少なくとも次のSource候補を想定する。

| Object Class family | 主なSource候補 |
|---|---|
| Agent / Character / Person / Organization | official profile, biography, interview, organization page, encyclopedia, news |
| CreativeWork / Series / Franchise / Component | official work page, series portal, credits, episode guide, publication, store/distribution listing, review, criticism |
| Place / World | official lore, map, geographic DB, municipal/institutional page, encyclopedia |
| Event | official record, timeline, news report, event page, archive |
| Artifact / Product | specification, manual, official product page, museum/catalog record, lore |
| Taxon / Creature | taxonomy DB, scientific reference, encyclopedia, official creature guide |
| Concept / Theme / Ideology / Trait等 | dictionary, encyclopedia, academic paper, criticism, reference work |
| Ability / Skill / Process | rulebook, manual, official guide, technical documentation, reference |
| Period / Era / Timeline / Continuity | chronology, historical reference, official timeline, archive |
| System / Software / Service | official documentation, repository, release notes, specification, service page |
| Material / Substance / Phenomenon | scientific paper, technical reference, government/institutional source, encyclopedia |
| Language / WritingSystem | dictionary, grammar, linguistic reference, official setting material |

この表はSource classificationの固定enumではなく、収集設計のcoverage checklistである。

同じSourceが複数Class familyを同時に支えてよい。

---

## 13. Page Context / inferred metadataの位置付け

### CTX-01 — Page ContextはEvidenceではなくRetrieval metadataとする

現行`page_contexts`が保持する次の情報は、Source/Evidence検索やPackage selectionの補助metadataとして再利用する。

- source / document genre候補
- publisher type候補
- page purpose
- page summary extract
- subject candidates
- published / updated timestamp候補
- source independence metadata

ただしheuristic / inferredな値そのものをSource本文のEvidenceとして扱わない。

### CTX-02 — Extract summaryとAI summaryを区別する

meta descriptionやlead paragraphから機械的に切り出したsummaryは検索補助metadataとして利用できる。

生成LLMが作成したsummaryを同じoriginとして保存してはならない。

---

## 14. Security / Export境界

### SEC-01 — Capture/Importしたことを外部送信許可とみなさない

Raw Snapshotにはログイン後ページ、個人情報、著作物等が含まれ得る。

SourceをSGOKBへ保存したことだけを理由に、Google Drive / ChatGPT等の外部交換先へ自動exportしてはならない。

外部exportの確認・sensitivity policyはB-06 / B-07 / Phase Gで具体化する。

### SEC-02 — Browser資格情報をSource Knowledgeとして保存しない

Web Page Capture Extensionの既存方針どおり、Cookie、認証Token、LocalStorage等のブラウザ資格情報を意図的なSource取得対象にしない。

Raw DOM/MHTMLにページ本文として機密情報が含まれ得る点は別途扱う。

---

## 15. 既存Prototypeから維持する事項

次は現行設計でも維持する。

- Source / Snapshot分離
- Web Capture BundleをRaw原資料として保持
- Capture IDによる同一Bundle二重Import防止
- Raw checksum / Evidence content hash
- Raw不変性
- Normalized Runの世代管理
- DOM位置・section等のProvenance
- EvidenceをSource / Snapshotへ直接追跡可能にする構造
- FTS / Embeddingの対象としてEvidenceを利用すること
- Page Contextのdeterministic / inferred / override分離
- Source間の重複・矛盾を不可逆に消さないこと

---

## 16. 既存Prototypeから変更する事項

### 16.1 Source Identity

旧:

```text
sources.url = UNIQUE
```

新:

```text
stable source_id
+ 0..N locators
+ Snapshot history
```

URLは重要なlocatorだがIdentityそのものではない。

### 16.2 Source classification

旧:

```text
source_type = official / wiki / news_article / social_post / ...
```

新:

```text
Source本体:
  resource_type
  media_type
  document_genre
  publisher_kind
  site/provider
  page_purpose

Source↔Object association:
  subject_relationship
```

Source本体の分類軸と、特定Objectとの関係に依存するassociation metadataへ論理的に分離する。

旧`source_type`はmigration時のlegacy metadataとして保持・best-effort mapping可能とするが、現行要件の正本概念にはしない。

### 16.3 Evidenceの役割

旧PrototypeではEvidenceの後に全件Fragment生成を行うことが標準であった。

新SGOKBではEvidence自体をSource-grounded retrievalの主要単位として維持し、Fragment生成をEvidence成立条件としない。

```text
Source / Snapshot
  ↓
Normalized Run
  ↓
Evidence
  ├─ FTS / Embedding
  ├─ Object Evidence Retrieval
  └─ Object Evidence Package
```

### 16.4 LLM解析結果

旧Fragment / Final DocumentのようなLLM生成物をEvidenceと同じ一次資料層へ混在させない。

---

## 17. 既存DB migrationへの要件

B-03時点では物理migrationを実施しないが、後続migrationでは次を満たす。

1. 既存`source_id`を可能な限り維持する。
2. 既存`snapshot_id` / `evidence_id`を維持する。
3. 既存Raw path / checksum / manifestを保持する。
4. 既存Normalized Run履歴を破壊しない。
5. 現在のURLを新Source locatorへ移行できる。
6. 旧`source_type` / Page Context metadataを失わず新分類軸へ移行またはlegacy保持できる。
7. Entity-Evidence linkはObject Evidence Linkへ変換可能とする。
8. Evidence FTS / Embeddingは必要に応じ再構築可能とする。

既存IDをプロジェクト名称変更や新schema導入だけを理由に再発番しない。

---

## 18. B-04 / B-05 / Phase E-Fへの引き継ぎ

### B-04 Object Result

- Result中のclaim / Facet / Relationは保存済みEvidence IDを参照できること。
- Source IDだけでなく、可能な限り具体的Evidence IDをgrounding単位とすること。
- ChatGPT生成内容とEvidence引用を分離すること。
- 存在しないEvidence IDをResultが参照した場合にValidationできること。

### B-05 Search

- Evidence lexical searchを維持すること。
- Evidence semantic searchを維持すること。
- source / genre / publisher / date / Object association等でfilter可能な要件を検討すること。
- historical Evidenceとactive/effective generationを区別して検索可能にすること。

### E-03 Source / Evidence / Evidence Link / Provenance schema

- Object Version / Facet / RelationからEvidenceへのLink。
- Linkの用途・support relation・生成来歴。
- Snapshot / Rawまでの追跡。

### Phase F

- Source/Snapshot/Normalized Run/Evidenceの物理pipeline。
- active/effective generation selection。
- Evidence chunk budget。
- Object Evidence Retrieval。
- candidate / confirmed / excluded association。
- class/source coverageを利用したretrieval。

---

## 19. B-03で意図的に決めない事項

次は後続Taskへ延期する。

- Source / Snapshot / Evidence tableの最終column
- Source ID / Snapshot ID / Evidence IDの具体形式
- Source classification registryのDB表現
- Raw Artifactの最終保存directory
- Normalized block schema
- Evidence chunk最大token / character数
- overlap幅
- active Snapshot / Normalized Run選択アルゴリズム
- Evidence Linkのsupport / contradiction等の詳細semantics
- Search ranking / reranking
- Evidence Packageのtoken budget
- Google Drive export policyの具体UI
- retention / backup / hard deleteの詳細

---

## 20. 完了条件への対応

### SourceとObjectを多対多とする

SRC-07 / SRC-08で、SourceとObjectを独立Identityとした多対多関連を定義した。

### Raw / normalized / EvidenceのProvenanceを保持する

Snapshot、Raw Artifact、Normalized Run、Evidenceを分離し、PRV-01の追跡chainを定義した。

### LLM解析結果と一次資料を混同しない

EVD-02 / EVD-03 / PRV-02により、LLM summary / synthesis / inferenceをEvidenceへ自動昇格させないことを定義した。

### B-02D Class coverageをSource設計へ反映する

第12節で全主要Class familyに対応するSource coverage候補を整理した。

### 旧Prototypeからの移行可能性を維持する

既存Source / Snapshot / Evidence IDとRaw historyを保持しつつ、URL identityと`source_type`単一軸を改修する要件を定義した。

---

## 21. 結論

SGOKBでは、**Sourceを情報源の安定した論理Identity、Snapshotを特定時点の観測、Raw Artifactを不変の原資料、Normalized Runを再生成可能な処理世代、Evidenceを単一Source/Snapshotへ必ず遡れる意味非改変の検索・引用単位として分離する。**

EvidenceはObject Knowledgeの根拠であって、LLMによる解釈・要約・統合結果ではない。

ObjectとSource / Evidenceは多対多で再利用し、Source更新・Extractor変更・Knowledge再生成が起きても過去Provenanceを保持する。

B-03は以上をもって完了しており、B-04 Object Result要件も`OBJECT_RESULT_REQUIREMENTS.md`として完了した。次のTaskは `B-05 [P0] 検索要件を定義する` とする。

**Status: Complete (2026-10-10)**
