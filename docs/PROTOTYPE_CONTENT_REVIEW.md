# CPCプロトタイプ文章構成レビュー

## 1. 目的

本書は、初回CPCプロトタイプで生成されたEvidence、Fragment、Final Documentを確認した結果から得られた、**文章構成・情報抽出品質に関する改善要求**を整理する。

対象は主に以下である。

- Evidenceの本文品質と文脈情報
- Fragmentの量・抽出方針・情報種別
- Final Documentの情報量・構造・AI利用適性

本書は初回プロトタイプを否定するものではない。初回プロトタイプはVertical Slice成立を目的としており、本書はその実データ評価から得られた**次段階の設計改善方針**である。

Codexが次の改善実装を行う際は、本書を既存の要件定義書・`docs/PROTOTYPE.md` と併せて参照すること。

---

# 2. 全体方針

初回プロトタイプでは、処理量を抑えるためにEvidenceを絞り、そこから少数Fragmentを生成し、さらに検索上位のFragmentからFinal Documentを生成している。

この方式では、パイプラインを進むごとに情報量が大きく減少する。

```text
Raw
 ↓
Normalized Data
 ↓
Evidence
 ↓  強い選択
Fragment
 ↓  さらに選択
Final Document
```

CPCの目的を考えると、Fragment生成段階ではPrecisionよりRecallを優先する方が適切である。

今後は次の考え方を基本とする。

> **保存・知識化段階では高Recall、利用・生成段階では高Precision。**

すなわち、意味のあるEvidenceから可能な限りFragmentを回収し、重複や重要度の調整は検索・統合・Final Document生成側で行う。

推奨する全体像：

```text
Raw Web Capture
      ↓
Source / Snapshot
      ↓
Page Context Analysis
      ↓
Main Content Extraction
      ↓
Normalized Document
      ↓
Evidence + Page Context
      ↓
High-Recall Fragment Extraction
      ↓
Fragment Store
      ↓
Facet / Information Type別検索・統合
      ↓
Final Document Builder
      ↓
AI向け構造化Document
```

---

# 3. Evidence

## 3.1 Evidence ID

### 指摘

表示上のEvidence IDとして `E01933` のような連番を利用する場合、長期運用では桁数や採番体系に依存した問題が生じる可能性がある。

### 現行実装の確認

現行PrototypeのDB上のEvidence正式IDはUUIDであり、`E01933` のような連番は永続Identityではない。

このため、**正式IDは現行のUUIDを維持する**。

必要であれば、人間・LLM向けには短い表示ラベルを別途割り当ててよい。

例：

```text
persistent_id:
  53f2d5e0-....

display_id:
  E01933
```

`display_id` は一時的・局所的な参照ラベルであり、DB上の外部キーや永続Identityには使用しない。

---

## 3.2 Evidence本文に周辺情報が多く混入する問題

### 指摘

現行Evidenceには、本来抽出したい記事本文以外の要素が多く含まれる場合がある。

例：

- navigation
- footer
- sidebar
- 関連記事一覧
- 商品リンク
- ランキング
- 投稿UI
- サイト共通説明
- 広告・宣伝要素

Raw Web Captureではこれらを保持する必要があるが、EvidenceはRawそのものではない。

### 方針

各層の役割を明確に分離する。

```text
Raw
= ページに存在した情報を可能な限り保存

Normalized Data
= 本文・記事構造を抽出し、不要UIを除去した派生データ

Evidence
= 後段の意味抽出に利用する価値のある原文単位
```

したがってEvidence生成前のMain Content Extractionを強化する。

### 改善候補

- Site-specific Extractorの追加・改善
- Generic Main Content Extractionの改善
- Trafilatura / Readability等の既存本文抽出技術の評価
- DOM構造、`main`、`article`、見出し階層等の利用
- 明らかなnavigation / footer / sidebar / related-contentの除外

ただし、削除した情報はRaw Bundleに残るため、Normalized/Evidence側ではRawより積極的にノイズ除去してよい。

本文抽出アルゴリズムによる情報欠落を検出できるよう、Rawへのprovenanceは維持する。

---

## 3.3 Evidenceへページ文脈を付与する

### 指摘

Evidence本文だけを切り出してLLMへ渡すと、その記述がどのような文脈・立場・目的で書かれたものか判断できない。

例えば、同じ「人気が高い」という記述でも、次では意味が異なる。

- 公式サイト
- Wikipedia等の百科事典
- 個人ブログ
- 商品レビュー
- 匿名掲示板
- SNS投稿

また、`blog` や `wiki` といったWebページ種別だけでも不十分である。

同じblogでも、作品考察、商品レビュー、日記、攻略記事等が存在する。

### 方針

Source / SnapshotとEvidenceの間に、ページ全体の性質を表す **Page Context** を導入する方向を推奨する。

概念例：

```text
PageContext
├─ source_type
├─ publisher_type
├─ page_purpose
├─ page_summary
├─ subject_candidates
└─ optional metadata
```

### source_type

Web上の形式・媒体の種類。

例：

- official
- encyclopedia
- wiki
- blog
- news_article
- bbs
- social_post
- commerce
- generic_web

### publisher_type

誰の立場から発信されているか。

候補：

- official
- editorial
- community
- individual
- anonymous
- commercial
- unknown

これは最終分類ではなく、Prototype改善時の候補とする。

### page_purpose

そのページが何について、何の目的で書かれたページか。

候補：

- work_introduction
- character_profile
- concept_explanation
- product_description
- product_review
- news_report
- opinion
- analysis
- discussion
- daily_post
- fan_creation
- guide
- unknown

必要に応じて追加可能とする。

### page_summary

ページ全体が何について記述しているかを簡潔に表した説明。

例：

```text
櫻木真乃について、プロフィール、性格、作中での活動、人物関係を解説する百科事典ページ。
```

### subject_candidates

ページの主要Subject候補。

例：

```text
- 櫻木真乃
- イルミネーションスターズ
- アイドルマスター シャイニーカラーズ
```

### 保存方法

Page ContextをEvidenceごとに重複保存する必要はない。

```text
Source
  ↓
Snapshot
  ↓
PageContext
  ↓
Evidence
```

のように参照関係を持たせる方法を優先する。

Fragment生成LLMへは、最低でも次を同時に渡す。

```text
Page Context
+
Section Context
+
Evidence本文
```

これによりEvidenceがページ全体のどのような背景の中に存在した記述なのかをLLMが判断できるようにする。

---

# 4. Fragment

## 4.1 Fragment数が少ない問題

### 指摘

現在のFragment数は期待より大幅に少ない。

CPCではFragmentを蓄積すること自体が中核機能であり、Final Documentの品質はFragmentの量と質に強く依存する。

初回PrototypeではFragment生成前に少数Evidenceを選択しているため、入力段階ですでに多くの情報が失われている。

### 現行Prototypeの問題

概念的には現在、次の処理に近い。

```text
大量Evidence
   ↓
関連度上位の少数Evidence
   ↓
LLM
   ↓
少数の重要Fact
```

これはRAGの検索処理としては合理的だが、知識収集・蓄積を目的とするCPCのFragment生成にはRecallが低すぎる。

### 方針

Fragment生成を以下へ変更する。

```text
Evidence
   ↓
可能な意味情報をできるだけ抽出
   ↓
多数のFragment
   ↓
保存
   ↓
後段で検索・分類・統合
```

Fragment抽出Promptも「重要情報を選択・要約する」方向ではなく、**再利用可能な意味情報を可能な限り列挙する**方向へ変更する。

---

## 4.2 1 Evidenceから複数Fragmentを生成する

1 Evidenceから複数Fragmentが生成されることを通常状態とする。

例：

Evidence：

```text
真乃は穏やかな性格で、周囲への気遣いができる。一方で自分に自信がなく、アイドルとして成長する中で徐々に積極性を身につけていく。
```

期待されるFragment例：

```text
F1: 櫻木真乃は穏やかな性格である。
F2: 櫻木真乃は周囲への気遣いができる。
F3: 櫻木真乃は自分に自信を持てない面がある。
F4: 櫻木真乃はアイドル活動を通じて積極性を身につけていく。
```

LLMが文章を一つの要約Fragmentへ圧縮しすぎないようにする。

---

## 4.3 「Evidence 1件 = 必ず1 Fragment以上」はハード制約にしない

有用なEvidenceからは原則1件以上のFragmentを期待する。

ただし、次のようなEvidenceから無理にFragmentを作る必要はない。

- navigationのみ
- 更新日時だけ
- 関連リンク一覧だけ
- 意味内容を持たないUI
- 対象Entityと無関係な断片

そのため、次の状態を明示できるようにする。

```text
Substantive Evidence
    → 原則 1..N Fragment

Non-substantive Evidence
    → 0 Fragment + discard_reason
```

`discard_reason` 候補例：

- navigation_only
- metadata_only
- unrelated
- duplicate
- insufficient_context
- no_extractable_claim

これにより、「LLMが抽出を忘れた」のか「意図的に不要と判断した」のかを区別できる。

---

## 4.4 Fragment Coverageを品質指標にする

Fragment生成品質を件数だけで評価しない。

例えば次の指標を記録可能にすることを推奨する。

```text
Evidence総数
Substantive Evidence数
Fragment生成済Evidence数
Fragment総数
0 Fragment Evidence数
0 Fragment理由別件数
Fragment Coverage
```

例：

```text
Evidence:                6000
Substantive Evidence:    4200
Fragment generated:      3900
Fragments:               9800
Coverage:                92.8%
```

最終的なCoverageの定義・閾値は実データ評価後に決定する。

---

# 5. Fragmentの情報種別

## 5.1 事実・考察・パブリックイメージを分離する

Final Documentで初めて分類するのではなく、Fragment生成段階から情報の性質を保持することを推奨する。

暫定的に以下の3分類を有力候補とする。

### fact

公式設定、作中描写、歴史的出来事、観測可能な出来事等。

例：

```text
櫻木真乃はイルミネーションスターズに所属している。
```

### interpretation

事実・描写・複数情報から導かれる考察、分析、意味付け。

例：

```text
自信のなさと成長の対比が人物像の中心的テーマとして描かれている。
```

### public_perception

ファン、コミュニティ、レビュー、世間等で共有される評価・イメージ・受け止め方。

例：

```text
ファンの間では癒やし系のキャラクターとして認識される傾向がある。
```

Fragment例：

```text
Fragment
├─ subject
├─ facet
├─ epistemic_type
│  ├─ fact
│  ├─ interpretation
│  └─ public_perception
├─ content
├─ evidence_ids
└─ qualifiers / metadata
```

`epistemic_type` という名称自体は暫定であり、より適切な名称があれば変更してよい。

---

## 5.2 Source TypeだけでFragment種別を決めない

次のような単純ルールは禁止する。

```text
公式サイト → 全部fact
掲示板     → 全部public_perception
```

理由：

- 公式インタビューにも制作者の解釈がある。
- Wikiにもコミュニティによる評価が含まれる。
- 掲示板にも客観的な出来事の記述がある。
- 商品ページにも宣伝表現と客観的仕様が混在する。

Fragmentの情報種別は、Page Context、Section Context、Evidence本文を組み合わせて判断する。

Sourceの性質は判断材料・qualifierとして保持する。

---

# 6. Final Document

## 6.1 情報量が少ない問題

Final Documentの情報量不足は、主に以下の2段階で情報を絞りすぎていることが原因と考える。

```text
Evidence → 少数Fragment
Fragment → 検索Top-NだけでDocument生成
```

したがってFinal Documentだけを長文化するのではなく、まずFragment生成量・Coverageを改善する必要がある。

---

## 6.2 Final Document生成方式

単純な「検索上位N FragmentをLLMへ渡して要約」から、**Facet × 情報種別**を意識した構築へ変更することを推奨する。

概念：

```text
Entity
  ↓
関連Fragment集合
  ↓
Facet別分類
  ↓
情報種別別分類
  ↓
各分類内で重複整理
  ↓
矛盾・不確実性保持
  ↓
Final Document
```

例えばCharacterであれば、性格だけが検索上位を独占して外見・能力・経歴等が欠落することを避ける。

---

## 6.3 推奨するFinal Document構造

AIへ渡すことを前提に、情報の種類を明示的に分離した構造を推奨する。

暫定例：

```markdown
# Entity Name

## Overview
対象の全体像。

## Facts

### 基本情報

### 性格

### 外見

### 能力・技能

### 経歴

### 人間関係

## Interpretations

### 人物像

### 成長・テーマ

### 行動・設定の解釈

## Public Perception

### 一般的イメージ

### ファンからの評価

### 評価の傾向・論点

## Relationships

## Timeline

## Conflicts / Uncertainty

## Source Notes
```

Entity Typeによって不要・追加すべきSectionは異なるため、固定Sectionを最終仕様とはしない。

Work、Character、Concept等ごとにDocument Templateを交換可能にすることも検討する。

---

# 7. AI向けDocumentとしての補完

## 7.1 Self-containedな記述

Final Documentは、人間向けの記事をそのまま連結するのではなく、AIが単独で理解しやすい形へ補完する。

許容する補完例：

```text
「彼は穏やかである」
        ↓
「櫻木真乃は穏やかな性格である」
```

```text
略称 → 正式名称
相対的な代名詞 → Entity名
省略された作品名 → 文脈上明確な正式名
時系列的な相対表現 → 必要に応じて明示化
```

### 原則

> Evidenceに存在する意味を、単独でも理解できる形式へ補完する。

---

## 7.2 Sourceにない知識を追加しない

次は「補完」とみなさない。

- LLMの事前学習知識から設定を追加する。
- Evidenceにない因果関係を事実として追加する。
- 推測をFactへ昇格する。
- 複数Sourceの矛盾を根拠なく一方へ統一する。

Final DocumentはSelf-containedにはするが、Source-independentにはしない。

すべての実質的記述はFragment / Evidenceへ追跡可能であることを維持する。

---

# 8. Provenanceと文脈

既存の以下の追跡関係は維持する。

```text
Final Document
      ↓
Fragment
      ↓
Evidence
      ↓
Snapshot
      ↓
Source
      ↓
Raw Capture
```

今後Page Contextを追加する場合は、次の情報も追跡可能にする。

```text
Evidence
  ├─ Page Context
  ├─ Section Context
  └─ Raw Position
```

これにより、「何が書かれていたか」だけでなく、**どのような種類・目的・立場のページの、どの文脈で書かれていたか**を後段AIが参照できるようにする。

---

# 9. 実装優先順位

次の順序を推奨する。

## Priority 1 — Evidence本文品質

- Main Content Extraction改善
- ノイズ削減
- Site-specific / Generic Extractor改善
- Rawへのprovenance維持

## Priority 2 — Page Context

- source_type再検討
- publisher_type
- page_purpose
- page_summary
- subject candidates
- Fragment PromptへContextを供給

## Priority 3 — Fragment高Recall化

- 上位Evidenceだけを選択する現行方式の見直し
- 1 Evidence → 複数Fragment
- Substantive Evidence判定
- 0 Fragment理由保存
- Fragment Coverage計測

## Priority 4 — Fragment情報種別

- fact
- interpretation
- public_perception
- qualifier / confidence / source contextの検討

## Priority 5 — Final Document再構築

- Facetごとの材料確保
- 情報種別ごとの材料確保
- 重複整理
- 矛盾・不確実性保持
- AI向けSelf-contained化
- Entity Type別Template検討

---

# 10. 実装時の注意

本書の改善要求を実装する際も、以下の既存原則は変更しない。

- Raw Captureは書き換えない。
- Web Page Capture ExtensionへCPC解析責務を戻さない。
- AI処理と決定的処理を可能な限り分離する。
- Fragment / DocumentからRawまでprovenanceを維持する。
- Prototypeで新しく導入する分類やSchemaは、評価後に変更可能な構造にする。
- 情報を削る処理はRawではなく派生段階で行う。
- 追加したPrompt / Schema / Algorithm / Versionを追跡可能にする。

---

# 11. 次回評価で確認する項目

改善後は、少なくとも次を現行Prototypeと比較する。

### Evidence

- 記事本文以外のノイズ量
- 本文欠落の有無
- Page Contextの妥当性
- Page ContextがFragment判断に有用か

### Fragment

- EvidenceあたりFragment数
- Fragment総数
- Fragment Coverage
- 0 Fragment理由
- 重要情報の取りこぼし
- 過剰な細分化・重複
- fact / interpretation / public_perception分類精度

### Final Document

- 情報量
- Facetの網羅性
- Fact / Interpretation / Public Perceptionの分離
- Source間の矛盾保持
- AIが単独利用しやすい構造か
- すべての重要記述がEvidenceへ追跡できるか

最終的なSchema・閾値・Promptは、この評価結果をもとに決定する。
