# Source Grounded Object Knowledge Base — SGOKB目的再定義

更新日: 2026-10-09

- Task: `B-01 [P0] SGOKBの目的を再定義する`
- Status: Accepted
- Related:
  - `docs/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
  - `docs/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
  - `docs/KNOWLEDGE_BASE_DEPENDENCY_INVENTORY.md`
  - `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `CharacterPageCollector システム要件定義書 v0.2.md`（Rename前の歴史資料）

## 1. 本書の位置づけ

本書は、Knowledge Base再設計におけるSource Grounded Object Knowledge Base（SGOKB）の目的を要件として再定義する。

旧要件定義書 v0.2 の「1. システムの目的」は、Prototypeとして「Web上の情報を収集・整理し、LLMなどのAIが利用しやすい専用ドキュメントを生成する」ことを大目標としていた。

B-01以降は、この目的を本書の定義で置き換える。

ただし、B-01は要件定義書全体を完成させるタスクではない。Object、Source / Evidence、Object Result、検索、人間工程、非機能要件の詳細はB-02〜B-07で定義する。

---

## 2. SGOKBの新しい定義

正式名称は **Source Grounded Object Knowledge Base**、略称は **SGOKB**。選定したSource / Evidenceを根拠とするObject Knowledge Baseを構築・維持するためのローカルシステムである。

以下の「Curated Semantic Object Knowledge Base」は性質を説明する分類表現であり、正式名称ではない。

SGOKBの目的を一文で表すと、次のとおりとする。

> ユーザーが関心を持って選択・収集したWeb上の資料を追跡可能なSource / Evidenceとして保存し、Character・Work・Concept等について意味的に整理されたObject Knowledgeへ変換して長期保存し、将来のAIや他システムから検索・比較・参照・再利用できる外部知識記憶を構築する。

SGOKBは、単なるWebページ保存ツールでも、Markdown生成ツールでも、特定LLM向けの一時的Context生成ツールでもない。

---

## 3. 「Curated Semantic Object Knowledge Base」の意味

### 3.1 Curated

SGOKBが扱う情報は、無差別な自動収集を前提としない。

ユーザーが「この資料・対象を自分のKnowledge Baseへ残す価値がある」と判断したものを中心に扱う。

そのため、SGOKBは次を重視する。

- Source採用判断をユーザーが行えること。
- Objectとして管理する対象を明示的に選択できること。
- 自動処理結果より、ユーザーが選択した一次資料を優先的な根拠として保持すること。
- Knowledge生成後も元資料まで追跡できること。

「Curated」は、人間がすべて手入力することを意味しない。選定と重要な意味判断は人間または高能力AIへ委ねつつ、取得・検証・検索・Versioning等は可能な限りシステム化する。

### 3.2 Semantic

SGOKBは、文字列やページ単位で情報を保存するだけではなく、意味単位で再利用できるKnowledgeを保持する。

例として、Characterであれば性格、価値観、動機、行動、関係、役割等、Workであればテーマ、世界観、物語、トーン等を、後から検索・比較できる構造へ整理する。

ただし、具体的なFacet一覧・SchemaはB-02以降で確定する。

Semanticであることは、すべてのSourceを事前に生成LLMで細粒度解析することを意味しない。Source / Evidenceから必要な根拠を検索し、必要な時点で高度な意味統合を行う方式を採用する。

### 3.3 Object

Knowledgeの中心単位を、巨大DocumentではなくObjectとする。

初期対象はCharacter / Work / Conceptを想定するが、Object typeの詳細要件と将来拡張方式はB-02で定義する。

Objectは、単なる名前付きフォルダではなく、属性、意味的Facet、他ObjectとのRelation、Version、Evidence参照等を持てる論理単位とする。

### 3.4 Knowledge Base

SGOKBの成果物は、一度生成して終了する文書ではなく、長期的に蓄積・更新・検索・再利用できるKnowledge Baseである。

Knowledge Baseとして、少なくとも次の性質を目指す。

- 永続保存できる。
- Source / Evidenceまで遡れる。
- 更新履歴を保持できる。
- 必要な部分だけ取得できる。
- 複数Objectを比較できる。
- 意味的な類似性を検索できる。
- 特定のAI製品やモデルがなくても正本が失われない。
- 将来のChatGPT、ローカルLLM、MCP Client、他システムから利用できる。

---

## 4. 主要目的要件

### PUR-01 — 外部知識記憶として長期保存する

SGOKBは、ユーザーが収集したCharacter / Work / Concept等に関する知識を、個別チャットや特定AIのContext Windowへ閉じ込めず、独立したローカルKnowledge Baseへ長期保存しなければならない。

### PUR-02 — Web上の根拠を保持する

Object KnowledgeはSource / Evidenceと分離して保持しつつ、Knowledgeから根拠となったSource / Evidenceへ追跡可能でなければならない。

Raw Sourceを、LLMが生成した要約・解釈・Knowledgeで置換してはならない。

### PUR-03 — Object単位でKnowledgeを管理する

SGOKBは、Character / Work / Concept等をObjectとして管理し、Objectごとに必要なKnowledgeを蓄積・更新・取得できなければならない。

巨大な単一DocumentをObject Knowledgeの唯一の正本としてはならない。

### PUR-04 — AIが必要なKnowledgeだけ取得できるようにする

SGOKBは、保存済みKnowledgeを全文投入することを前提とせず、用途に応じて必要なObject、Facet、Relation、Evidence等を取得できる検索・アクセス基盤を提供しなければならない。

具体的な検索要件はB-05で定義する。

### PUR-05 — 検索・比較・再利用を可能にする

保存されたKnowledgeは、単なる閲覧だけでなく、次の用途へ再利用できなければならない。

- Object検索
- Object間比較
- 意味的類似性の検索
- Relationの参照
- Evidenceの監査・再分析
- AI向けContext構築
- 創作・分析・Roleplay等への材料提供

### PUR-06 — AI製品・モデルから正本を独立させる

SGOKBの正本Knowledgeは、特定のChatGPT model、OpenAI API、ローカルLLM、Embedding model、MCP Client等の存在を成立条件としてはならない。

AIやEmbeddingはKnowledgeの生成・検索・利用を支援する交換可能な能力として扱う。

### PUR-07 — 高度な意味統合ではHuman-in-the-loopを許容する

SGOKBは完全自動化率を最優先にしない。

高度な意味理解・統合については、ユーザーがChatGPT Web/Desktop等へ明示的に処理を依頼し、その結果をSGOKBへ戻すHuman-in-the-loop方式を標準運用として許容する。

標準Knowledge生成フローはChatGPT APIを必須としない。

### PUR-08 — 再生成・再評価できるようにする

Knowledge生成方式、Prompt、Embedding model、検索方式、Schema等が将来変更されても、保持しているSource / Evidenceから再処理・再評価できる構造を目指す。

一度生成されたKnowledgeだけを唯一の復元不能な成果物として扱ってはならない。

### PUR-09 — 人間とAIの双方から利用可能にする

SGOKBはAI専用の不可視データストアにはしない。

機械向けの構造化Knowledgeを正本としつつ、人間が確認できる派生表示やProvenance表示を提供できる構造とする。

具体的なJSON / Markdown形式はB-04以降で定義する。

---

## 5. Documentの位置づけ

旧Prototypeでは、AI向けFinal Document生成が処理の終点だった。

新SGOKBでは、DocumentをKnowledgeの目的・正本とはしない。

```text
旧:
Source / Evidence
  ↓
Fragment
  ↓
Final Document = 主要成果物

新:
Source / Evidence
  ↓
Object Knowledge Store = 正本
  ├─ Search / Similarity / Relation
  ├─ MCP / Application API
  └─ Markdown / AI Context / Report = 派生表示
```

Markdown、レポート、AI Context等は、特定用途のためにObject Knowledgeから生成される**Derived Representation（派生表現）**として扱う。

したがって、Document生成機能自体を禁止するものではない。Documentを編集正本・唯一のKnowledge表現・更新単位として扱わないことが要件である。

---

## 6. Source / Evidenceの位置づけ

SGOKBの目的がDocument生成からObject Knowledgeへ変わっても、一次資料の重要性は変わらない。

Source / Evidenceは次の役割を持つ。

1. Object Knowledgeの根拠。
2. Knowledge更新時の再評価材料。
3. AI出力の監査材料。
4. Schemaや分析方式変更時の再生成元。
5. Knowledgeに不確実性・矛盾がある場合に原資料へ戻るための参照点。

このため、Source / EvidenceをObject Knowledge内部へ埋め込んで消失させたり、要約のみ残してRawを破棄したりしない。

詳細要件はB-03で定義する。

---

## 7. SGOKBの標準的な利用イメージ

再設計後の標準フローは概念的に次のようになる。

```text
ユーザーがWeb資料を選択
 ↓
Capture / Import
 ↓
Raw Source / Evidence保存
 ↓
対象Objectに関係するEvidenceを検索・選択
 ↓
Object Evidence Package作成
 ↓
ユーザーがChatGPTへ意味統合を依頼
 ↓
Structured Object Result
 ↓
Validation / Versioning / Import
 ↓
Object Knowledge Store
 ↓
Search / Compare / Similarity / Relation / MCP
 ↓
ChatGPT / Local LLM / Other Clientsで再利用
```

これはB-01時点の責務境界を示すものであり、具体的なUI、CLI、Google Drive layout、JSON Schema、MCP Tool名を確定するものではない。

---

## 8. SGOKBが目的としないもの

B-01では、SGOKBのスコープ拡大を防ぐため、次を主要目的から除外する。

### NON-01 — Web全体の自動Crawler

SGOKBは、Web上の情報源を無差別に自動発見・大量収集するCrawlerを主要目的としない。

### NON-02 — 特定AI向けDocument Generator

SGOKBは、特定のLLMへ投入する巨大Documentを生成すること自体を主要目的としない。

### NON-03 — 完全自動の生成AI Pipeline

すべてのEvidenceを生成LLMへ通し、無人で最終Knowledgeを完成させることを必須要件としない。

### NON-04 — ChatGPT API依存サービス

ChatGPT APIを利用しないとKnowledge Baseが成立しない構造にはしない。

### NON-05 — ユーザー嗜好推論システム

「ユーザーが何を好むか」「どの価値観を持つか」等のPersonal InferenceはSGOKBの主要責務としない。

SGOKBは外部世界に存在するObjectそのもののKnowledgeを扱う。UserPreferenceDiscoverySystem（UPDS）との詳細責務境界はPhase Cで定義する。

### NON-06 — Raw Sourceの代替

Object KnowledgeやAI要約を理由に、元のRaw Source / Evidenceを不要とみなさない。

---

## 9. 成功状態

SGOKBが目的を達成している状態は、単に「Documentを生成できた」状態ではない。

少なくとも次が成立している状態を目指す。

1. ユーザーが採用したSourceを安全に保存できる。
2. Sourceから検索可能なEvidenceを構築できる。
3. Character / Work / Concept等をObjectとして長期管理できる。
4. Object KnowledgeからSource / Evidenceまで根拠を追跡できる。
5. Object Knowledgeを更新・版管理できる。
6. 必要なObject / Facet / Relation / Evidenceを検索できる。
7. 意味的に近いObjectを検索・比較できる。
8. 保存済みKnowledgeをChatGPT・ローカルLLM・他Clientから再利用できる。
9. 特定生成AI APIが利用できなくても、保存済み正本KnowledgeとEvidenceを失わない。
10. 文書が必要な場合は、正本Knowledgeから用途別に生成できる。

各項目の詳細な受入条件はB-02〜B-07およびPhase Nで具体化する。

---

## 10. 旧要件 v0.2 からの変更点

| 観点 | v0.2 Prototype | B-01以降 |
|---|---|---|
| 大目標 | AI向け専用Document生成 | Curated Semantic Object Knowledge Base構築 |
| 中心単位 | Evidence → Fragment → Document | Source / Evidence → Object Knowledge |
| 正本 | Rawを保持しつつFinal Documentが主要成果物 | Source/Evidence + 構造化Object Knowledge |
| Document | 処理の終点 | Derived Representation |
| 生成LLM | Fragment / Final生成の主要処理 | 標準自動Pipelineの必須要素ではない |
| ChatGPT API | 将来の自動化手段になり得る | 標準Knowledge生成の必須依存にしない |
| 人間 | Source選定中心 | Source/Object選定 + 高度意味統合の明示操作を許容 |
| 検索 | Fragment/EvidenceからFinal生成を支援 | Knowledgeそのものの検索・比較・再利用が主要機能 |
| 長期利用 | AI向けDocumentを利用 | モデル非依存の外部知識記憶として利用 |

旧要件定義書 v0.2はPrototypeの設計・検証履歴として保持する。ただし「1. システムの目的」については、本書がKnowledge Base再設計の現行要件として優先される。

---

## 11. B-01で確定しない事項

以下は後続タスクへ委ねる。

- Object共通属性・Object type・ID設計: B-02
- Source / Evidence詳細要件: B-03
- Structured Object Result / JSON / Markdown契約: B-04
- Lexical / Semantic / Similarity / Relation検索要件: B-05
- 人間工程と自動工程の詳細: B-06
- 性能・オフライン・Versioning等の非機能要件: B-07
- SGOKB / UPDS詳細責務境界: Phase C
- Repository / docs / source directory構成: Phase D
- DB schema: Phase E
- Fragment / Final Documentの物理削除: Phase L

B-01では、後続設計を拘束する目的・優先順位・非目的だけを固定する。
