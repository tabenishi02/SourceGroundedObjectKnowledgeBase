# CharacterPageCollector — Knowledge Base 再設計 Decision Record

更新日: 2026-10-09

- Decision ID: `CPC-KB-001`
- Status: Accepted
- Scope: CharacterPageCollector Knowledge Base 再設計
- Related:
  - `docs/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`
  - `docs/KNOWLEDGE_BASE_REDESIGN_TASKS.md`

## 1. Decisionの目的

本書は、CharacterPageCollector（CPC）のKnowledge Base再設計について、「何を変更するか」だけでなく「なぜその判断を採用したか」を固定するDecision Recordである。

今後の要件定義・設計・実装では、本Decisionを再設計の前提として扱う。個別のデータモデル、DB schema、CLI、Google Drive交換形式、MCP仕様等の詳細は後続Phaseで決定し、本書では先行して固定しない。

---

## 2. Context — 旧Prototypeの構成

旧Prototypeは概ね次の処理を標準パイプラインとしていた。

```text
Web Capture Bundle
 ↓
Source / Snapshot / Evidence
 ↓
Local Generative LLM
 ↓
大量のFragment
 ↓
Embedding / Hybrid Search
 ↓
EntityごとのFinal Document
```

この方式では、Web上の一次資料をEvidenceとして保持し、Provenanceを維持する点には価値があった。一方、Knowledgeを作る中心処理として「全Evidenceを生成LLMで細粒度Fragment化すること」と「Fragment群から巨大なFinal Documentを生成すること」を採用していたため、処理量と最終成果物の双方が大きくなった。

---

## 3. Evidence — 再設計が必要になった理由

実データを用いたPrototype評価では、代表8 Captureだけで次の規模になった。

- Evidence: 737
- Fragment: 5,246
- AI呼び出し: 1,038
- AI応答待ち: 約5.1時間
- AI応答待ち: 全体処理時間の99%以上
- Character Final: 約50万文字
- Work Final: 約378万文字

この結果から、次の問題を確認した。

### 3.1 全Evidenceへの生成LLM適用コストが大きすぎる

全Evidenceを生成LLMで細粒度解析するため、Evidence数の増加がそのまま多数のAI呼び出しへつながる。実測ではAI応答待ちが全体処理時間の99%以上を占め、通常運用における主要ボトルネックとなった。

### 3.2 Fragment生成自体が目的化しやすい

Fragmentは最終用途へKnowledgeを届けるための中間表現であるが、大量Fragmentの生成・分類・Embedding・統合を維持すること自体のコストが大きくなった。

「必要なObject Knowledgeを取得・再利用する」という目的に対し、全Evidenceを事前に細粒度Fragmentへ変換することを必須条件とする合理性が不足している。

### 3.3 巨大Final DocumentはKnowledge正本として扱いにくい

数十万〜数百万文字へ成長したFinal Documentは、次の用途に不向きである。

- 人間による確認
- LLM Contextへの必要部分だけの投入
- 属性・Facet単位の比較
- Relation検索
- 差分管理
- Versioning
- 他システムからの構造化利用

文書として閲覧する価値は残るが、Knowledgeの正本として採用し続ける理由はない。

### 3.4 自動化率を優先しすぎてAIの役割分担が不適切になった

高性能なChatGPTを利用できる状況でも、APIによる完全自動化を前提とすると、ローカル生成LLMへ高度な意味理解・統合能力を要求する構成になりやすい。

CPCの目的は自動化率を最大化することではなく、品質、処理時間、追跡可能性、保守性を満たしたKnowledge Baseを構築することである。

### 3.5 CPCの本来の目的と成果物がずれていた

CPCの本質的な目的は「巨大なCharacter/Work文書を生成すること」ではなく、収集したWeb上の根拠から、再利用可能で追跡可能なObject Knowledgeを長期保存し、将来のAIから検索・比較・参照できるようにすることである。

---

## 4. Decision

### D1. 全Evidenceを生成LLMでFragment化する方式を標準パイプラインから外す

旧Prototypeの次の流れを、通常運用の必須工程とはしない。

```text
Evidence
 ↓
Generative LLM
 ↓
Fragment
```

再設計後は、Source / Evidenceを一次資料として保持したうえで、Objectに関連するEvidenceを通常プログラム・FTS・Embedding等で高Recallに検索・選択し、高度な意味理解・統合が必要な段階だけをChatGPTへ渡す方向とする。

Fragmentという概念・既存実装を完全削除するか、research-only / legacy read-onlyとして残すかは、このDecisionでは確定しない。Phase F / Phase Lで決定する。

### D2. 巨大Final DocumentをKnowledgeの正本としない

Final Markdown等の長文Documentを、Knowledgeの唯一の正本として扱う方式を廃止する。

再設計後の正本は、Object / Facet / Relation / Version / Evidence Link等を構造化して保持できるObject Knowledge Storeとする。

機械向け交換形式はStructured JSONを基本候補とし、Markdown等の人間向け文書は正本から生成可能な派生表示とする。具体的Schemaは後続Phaseで決定する。

既存Final Document実装を完全削除するか、Renderer等として再利用するかはPhase Lで決定する。

### D3. ChatGPT APIを標準処理に使用しない

CPCの標準Knowledge生成フローは、ChatGPT APIによる自動呼び出しを必須としない。

基本フローは次のHuman-in-the-loop方式とする。

```text
CPC
 ↓
Object Evidence Package
 ↓
Google Drive等の交換領域
 ↓
ユーザーがChatGPT Web/Desktopへ明示的に処理を依頼
 ↓
Structured Object Result
 ↓
CPC Validation / Import / Versioning
```

これにより、CPC Coreを特定のクラウドAI API、料金体系、API model名、認証方式へ強く依存させない。

これは「ChatGPT APIを永久に禁止する」というDecisionではない。研究用途、任意機能、将来の別運用としてAPI adapterを追加する余地は残す。ただし、標準パイプラインと正本Knowledgeの成立条件にAPI利用を含めない。

### D4. 自動化率より責務分離を優先する

再設計では、処理を次のように分担する。

- 通常プログラム: Capture、Import、Normalize、Validation、Versioning、決定論的処理
- FTS / Embedding: 検索、候補抽出、類似度計算
- ChatGPT: 高度な意味理解、統合、構造化Object Result生成
- 人間: 対象選択、ChatGPTへの明示依頼、必要なレビュー・判断

CPC側の自動処理時間は1 Objectあたり概ね10分以内を目標とするが、Google Drive → ChatGPT → Result返却の人間工程はこの時間目標から除外する。

### D5. Source / EvidenceとProvenanceは維持する

今回のDecisionは「LLM処理を減らすために一次資料を捨てる」というものではない。

Raw Source / Snapshot / Evidence、およびそれらのchecksum・Provenanceは、Object Knowledgeの根拠と再生成可能性を支える重要資産として維持する方向とする。

具体的な既存資産のKeep / Modify / Replace / Retire分類はA-02で実施する。

---

## 5. 再設計後の基本境界

本Decisionが採用する基本境界は次のとおりとする。

```text
Web
 ↓
Source Capture / Import
 ↓
Source / Evidence Store
 ↓
Retrieval（metadata / name / alias / FTS / Semantic）
 ↓
Object Evidence Package
 ↓
Human-in-the-loop ChatGPT
 ↓
Structured Object Result
 ↓
Validation / Import / Versioning
 ↓
Object Knowledge Store
 ↓
Lexical / Semantic / Similarity / Relation Retrieval
 ↓
MCP / CLI / Other Clients
```

この図は責務境界を示すものであり、DB table、ファイル形式、CLI command、MCP Tool等の詳細仕様を確定するものではない。

---

## 6. 採用しなかった基本案

### 6.1 旧Fragment Pipelineをそのまま高速化する

不採用理由:

- 主問題は単一モデルの速度だけではなく、全Evidenceへ生成LLMを適用する処理量そのものにある。
- 高速なモデルへ交換しても、Evidence増加に伴うAI call数と中間Fragment数の増大という構造は残る。
- Final Document巨大化の問題を解決しない。

### 6.2 ChatGPT APIへ全面移行して完全自動化する

標準方式としては不採用とする。

理由:

- 自動化率の最大化は本プロジェクトの最優先要件ではない。
- CPC Coreが特定APIの料金・model・認証・仕様変更へ依存する。
- 人間が対象を選び、高性能なChatGPTへ明示的に処理を依頼する運用を許容すれば、Knowledge品質とシステム単純性を両立できる。

API自体の利用可能性を否定するものではなく、将来optional adapterとして再評価可能とする。

### 6.3 Final Markdownを正本のまま維持し、検索だけ改善する

不採用理由:

- Object属性、Facet、Relation、Evidence Link、Versionを機械的に扱いにくい。
- 必要な部分だけを取得するContext構築に不向きである。
- 類似検索や他システムとの連携で、毎回巨大文書を再解釈する必要が生じる。

---

## 7. Consequences

### Positive

- 生成LLM呼び出し回数をEvidence数へ直接比例させない設計へ移行できる。
- Knowledge正本を長文Documentから構造化Objectへ変更できる。
- Object / Facet単位のSemantic Search・Similarity Searchを設計できる。
- Source / EvidenceまでProvenanceを追跡しながら、LLMが利用しやすいKnowledgeを提供できる。
- CPC Coreを特定の生成AI APIから独立させやすい。
- ChatGPT、ローカルLLM、UPDS、その他Clientへ同一Knowledgeを再利用しやすくなる。

### Trade-offs

- Knowledge生成に人間の明示操作が入る。
- 完全無人処理ではなくなる。
- Evidence Package export / Result importという交換工程が必要になる。
- Object Schema、Versioning、Validation、Retrieval等を新たに設計する必要がある。
- 旧PrototypeとのBreaking Changeが生じる可能性が高い。

これらは、自動化率より品質・追跡可能性・保守性・実用的処理時間を優先するという再設計方針上、受容する。

---

## 8. このDecisionで確定しない事項

以下は後続Phaseへ委ねる。

- Object / Facet / Relationの詳細Schema
- DB migrationの具体的方法
- Fragment実装の完全削除 / legacy保持 / research-only化
- Final Document実装の削除 / Renderer転用
- Embedding modelとVector backend
- Google Drive交換ディレクトリ・同期方式
- ChatGPT用instructions / result schemaの詳細
- MCP Tool / Resource仕様
- CPC / UPDS間の詳細契約
- Repository / docs / source folderの物理再編

A-01では、これらを先行決定しない。

---

## 9. Decision変更ルール

今後、本Decisionを覆す必要が生じた場合は、既存文書を暗黙に書き換えず、次のいずれかで扱う。

1. 本Decisionへ明示的なAmendmentを追加する。
2. 新しいDecision Recordを作成し、本Decisionを`Superseded`とする。

特に次の方針を変更する場合は、変更理由と実測根拠を必須とする。

- 全Evidenceへの生成LLM Fragment化を標準工程へ戻す。
- 巨大Final DocumentをKnowledge正本へ戻す。
- ChatGPT APIを標準パイプラインの必須依存へ変更する。

---

## 10. A-01完了判定

A-01で要求された次の判断を本書へ記録した。

- [x] 旧Prototypeの問題点と再設計理由
- [x] 全Evidenceを生成LLMでFragment化する方式を標準パイプラインから外す
- [x] 巨大Final DocumentをKnowledgeの正本としない
- [x] ChatGPT APIを標準処理に使用しない

したがって、A-01 `再設計Decision Recordを作成する` は完了とする。
