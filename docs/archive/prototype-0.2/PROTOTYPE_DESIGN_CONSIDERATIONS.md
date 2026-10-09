# CPCプロトタイプ追加設計観点

> **Archived / Historical** — Rename前のPrototypeの記録です。旧名称・コマンド・パスは当時の事実を保持しており、現行操作は[README](../../../README.md)を参照してください。

## 1. 目的

本書は、`docs/archive/prototype-0.2/PROTOTYPE_CONTENT_REVIEW.md` で整理したEvidence / Fragment / Final Documentの改善方針に加え、初回プロトタイプの次段階で設計上意識すべき追加観点をまとめる。

本書の内容は、初回プロトタイプのVertical Sliceを否定するものではない。実データを用いた評価から得られた追加改善要求であり、今後Codexが設計・実装を更新する際の検討基準とする。

特に以下を重視する。

- Fragmentを独立して評価可能な細粒度知識として扱うこと
- Source / Evidence / Fragmentそれぞれの性質を混同しないこと
- 矛盾・時系列・推論を不可逆に潰さないこと
- Final DocumentをMarkdownだけでなく構造化知識として扱うこと
- LLMによる推論や信頼度表現を過度に確定的に扱わないこと

---

# 2. Fragmentの原子性

原則として、**1 Fragment = 1つの独立して評価可能な主張**を目標とする。

例：

```text
原文:
Aは温厚な性格だが、戦闘時には冷酷になり、Bとは幼少期から親しい。
```

望ましいFragment例：

```text
F1: Aは温厚な性格である。
F2: Aは戦闘時には冷酷になる。
F3: AとBは幼少期から親しい。
```

ただし、因果関係や条件関係を分割すると意味が壊れる場合は、一つのFragmentとして保持してよい。

例：

```text
Aという出来事を契機として、Bの立場へ変化した。
```

Fragment生成LLMには、単なる要約ではなく、独立して再利用・検索・検証できる最小限の主張へ分解することを求める。

---

# 3. EvidenceとFragmentは多対多とする

次の両方を通常状態として扱う。

```text
1 Evidence → 複数Fragment
```

および、

```text
1 Fragment ← 複数Evidence
```

同じ主張を複数Sourceが支持する場合、Fragmentは複数Evidenceを根拠として参照できるようにする。

FragmentとEvidenceの関係を1対1へ制限しない。

---

# 4. 独立した裏付けと転載を区別する

複数Sourceに同じ内容が存在しても、それらが独立した情報源とは限らない。

例：

```text
Source A: 一次情報
Source B: Source Aの転載
Source C: Source Aを参照した二次記事
```

この3件を「3つの独立した証拠」と同等には扱わない。

将来的には、少なくとも次を区別可能な構造を検討する。

- primary / first-party
- secondary
- community
- individual
- anonymous
- quoted / copied / derived
- unknown

完全な依存関係推定は初期要件としないが、Source数だけを信頼度として扱わないことを原則とする。

---

# 5. Source AuthorityとFragmentの性質を分離する

Sourceの権威性と、そのSource内の個々の主張の性質は別物として扱う。

例：

```text
source_authority: official
epistemic_type: promotional_claim
```

や、

```text
source_authority: anonymous_community
epistemic_type: factual_claim
```

はどちらも成立し得る。

したがって、公式Sourceだから全Fragmentをfactとみなす、匿名Sourceだから全Fragmentをpublic_perceptionとみなす、といった単純な規則は採用しない。

---

# 6. 矛盾情報を不可逆に統合しない

異なるSource間で矛盾する情報が存在する場合、抽出時点で一方を削除・上書きしない。

例：

```text
Source A: Aは17歳である。
Source B: Aは18歳である。
```

望ましい扱い：

```text
Fragment 1: Aは17歳と記載されている。
Fragment 2: Aは18歳と記載されている。
```

必要に応じて、後段で同一論点の矛盾候補としてグループ化する。

Final Documentでは、資料間に相違があること自体を情報として提示できるようにする。

CPCは「唯一の正解を確定するDB」ではなく、**出典付き情報を保持し、後から比較・判断可能にする知識基盤**として扱う。

---

# 7. 時系列を第一級情報として扱う

同一Entityの属性は時期・作品・章・時点によって変化し得る。

例：

```text
序盤: 組織Xに所属
終盤: 組織Xを離脱
続編: 組織Yに所属
```

Fragmentには必要に応じて次のようなTemporal Contextを付与可能にする。

- story_phase
- work_context
- valid_from
- valid_to
- temporal_note

具体Schemaは後続設計で決定する。

---

# 8. 公開日時・取得日時・物語内時系列を分離する

以下を混同しない。

```text
captured_at
published_at / updated_at
claim temporal context / story time
```

2026年の記事が「物語開始時点ではAは学生だった」と記述する場合、Source公開日時とFragmentが指す物語上の時点は異なる。

---

# 9. Entity Resolution

同一Entityには複数表記が存在する。

例：

```text
櫻木真乃
真乃
真乃ちゃん
Mano Sakuragi
```

少なくとも以下を扱える構造を維持する。

- canonical_name
- aliases
- entity_type
- optional external identifiers

LLMが同一Entity候補を提示しても、自動的に不可逆な統合を行うことは避ける。

候補提示と確定処理を分離できる設計を優先する。

---

# 10. 省略主語・代名詞のContext Resolution

日本語では主語省略や代名詞が多いため、Evidence単独ではSubjectが不明になる場合がある。

例：

```text
一護は尸魂界へ向かった。
そこで彼はルキアと再会した。
```

Fragment生成時には、Sectionや前後文脈を用いて「彼 = 黒崎一護」と解決できることが望ましい。

ただし原文自体は変更せず、必要なら次のように分離する。

```text
original_text
resolved_context
```

Context Resolutionの結果もLLMによる推定である場合は、その事実を追跡可能にする。

---

# 11. Fragmentの主張主体を保持する

同じ内容でも誰が主張しているかによって意味が異なる。

例：

```text
「Aは作品中最強である」
```

候補属性として、次のような主張主体を保持可能にする。

- official
- author / creator
- interviewee
- article_author
- reviewer
- community
- anonymous_user
- derived_by_cpc
- unknown

最終的な分類名は後続設計で決定する。

---

# 12. Source由来の考察とCPC生成の考察を分離する

`interpretation` を一種類として扱わない。

少なくとも概念的には、次を区別する。

```text
source_interpretation
= Source本文に明示されている考察・分析

derived_interpretation
= CPCのLLMがEvidenceから新たに導出した考察
```

例えばSource本文に、

```text
この場面はAの孤独を象徴していると思われる。
```

と書かれていれば `source_interpretation` である。

一方、Sourceには直接書かれておらず、複数EvidenceからCPCが導いた場合は `derived_interpretation` とする。

将来的な `epistemic_type` 候補：

- fact
- source_interpretation
- derived_interpretation
- public_perception
- promotional_claim

分類は拡張可能にする。

---

# 13. Web Contentを命令として扱わない

Webページ本文をLLMへ入力するため、Prompt Injectionを設計上のリスクとして扱う。

原則：

```text
System / Developer Prompt = Instruction
Web Content              = Untrusted Data
```

Web本文に「以前の指示を無視せよ」等の命令文が含まれていても、CPCの処理指示として解釈しない。

Prompt、Structured Input、Provider Adapter、Validationの各段階でこの責務境界を維持する。

---

# 14. Fragment重複は生成直後に破壊的統合しない

High-Recall抽出では類似Fragmentが多数発生することを許容する。

例：

```text
F1: Aは優しい。
F2: Aは優しい性格である。
F3: Aは他者への思いやりが強い。
```

Extraction直後に一つへ不可逆統合すると、出典・ニュアンス・時系列・主張主体を失う可能性がある。

推奨構造：

```text
Evidence
  ↓
Raw Fragment Store
  ↓
Similarity / Relation Analysis
  ↓
Cluster / Consolidated Knowledge
```

統合結果は派生成果物として扱い、元Fragmentを保持する。

---

# 15. Fragment Confidence / Evidence Strength

## 15.1 Fragment Confidenceとは

Fragment Confidenceとは、**生成されたFragmentの内容が、根拠Evidenceからどの程度直接・明確に支持されているかを表すための補助情報**を指す。

これは「そのFragmentが世界において真である確率」と同じ意味ではない。

例えばEvidenceが、

```text
Aは第3部隊の隊長を務めている。
```

であり、Fragmentが、

```text
Aは第3部隊の隊長である。
```

なら、Evidenceからほぼ直接読み取れる。

一方、Evidenceが、

```text
Aは戦闘後も負傷した仲間を気遣い、自分の休息を後回しにした。
```

で、Fragmentが、

```text
Aは他者への思いやりが強い。
```

なら、合理的ではあるが一段の解釈を含む。

さらに、Evidenceが一度の行動しか示していないのに、

```text
Aは常に自己犠牲的な人物である。
```

と一般化すれば、より強い推論を含む。

この違いを表すのがFragment Confidence / Evidence Strengthの目的である。

## 15.2 数値確率を安易に使用しない

LLMへ次のような値を自己申告させても、校正された確率とは限らない。

```text
confidence = 0.93
```

この値を「93%の確率で正しい」と解釈してはならない。

初期設計では、数値Confidenceよりも、**EvidenceからFragmentまでの推論距離・根拠形式を分類する方式**を優先する。

有力候補：

```text
direct_statement
strong_inference
weak_inference
```

意味の例：

### direct_statement

Evidence本文にFragmentとほぼ同じ主張が直接記述されている。

```text
Evidence:
Aは17歳である。

Fragment:
Aは17歳である。
```

### strong_inference

Evidenceに直接同じ文言はないが、通常の読解で比較的明確に導ける。

```text
Evidence:
Aは毎回、負傷した仲間を優先して救助している。

Fragment:
Aは仲間を優先する傾向がある。
```

### weak_inference

複数の解釈が可能であり、FragmentはEvidenceを越えた一般化・心理推定・意味付けを強く含む。

```text
Evidence:
Aは会議中ほとんど発言しなかった。

Fragment:
Aは対人関係に強い不安を抱えている。
```

この場合、後者はEvidenceだけから断定するには根拠が弱い。

## 15.3 Source Authorityとは別軸である

Fragment Confidence / Evidence StrengthはSourceの信頼性評価ではない。

例えば公式Sourceであっても、EvidenceからFragmentへの推論が強ければ `weak_inference` になり得る。

逆に匿名掲示板の投稿でも、

```text
投稿本文: 「私は第5話を見た。AはBに剣を渡した」
Fragment: 「投稿者はAがBに剣を渡したと述べている」
```

という「投稿者がそう主張した」というFragment自体は `direct_statement` と分類できる。

したがって、次は分離して保持する。

```text
source_authority
≠
evidence_strength
≠
epistemic_type
```

## 15.4 Final Documentでの利用

Final Document生成時には、Evidence Strengthを材料選択や表現強度の調整に使用できる。

例：

```text
direct_statement
→ 「Aは第3部隊の隊長である」

strong_inference
→ 「Aは仲間を優先する傾向があると考えられる」

weak_inference
→ 「Aの行動を対人不安の表れと解釈する余地がある」
```

ただし、機械的な文章テンプレートとして固定する必要はない。

---

# 16. Final Documentは構造化表現を内部正本とする

Markdownだけを最終知識表現の正本にしない方向を推奨する。

内部的には例えば次のような構造を持てる。

```text
FinalKnowledgeDocument
├─ overview
├─ facts[]
├─ source_interpretations[]
├─ derived_interpretations[]
├─ public_perception[]
├─ relationships[]
├─ timeline[]
├─ conflicts[]
└─ source_notes[]
```

そこから用途別に、

- Markdown
- JSON
- AI Context
- 将来のAPI Response

等を生成する。

```text
Fragment Store
      ↓
Structured Final Representation
      ↓
Renderer
 ├─ Markdown
 ├─ JSON
 └─ AI Context
```

---

# 17. 大量Fragmentを前提とした階層生成

High-Recall化後は一Entityに数千～数万Fragmentが存在する可能性がある。

すべてを一度にLLM Contextへ投入する設計を前提としない。

候補：

```text
Entity
 ↓
Facet / Information Type分割
 ↓
各グループ内で検索・Cluster・重複整理
 ↓
Facet単位のStructured Result
 ↓
Final Merge
```

Hierarchical Generationは文章品質だけでなくContext Window制約への対応としても扱う。

---

# 18. 情報が存在しない場合は補完しない

Final Documentに予定されたSectionがあっても根拠Fragmentが存在しない場合、LLMの学習済み知識で埋めない。

例：

```text
能力:
根拠情報なし
```

またはSection自体を省略する。

「Evidenceに存在する意味を独立して理解できる形へ補完する」ことと、「Evidenceに存在しない知識を追加する」ことを明確に分離する。

---

# 19. AI Benchmarkの評価データを固定・Version管理する

モデル・Prompt比較を継続するため、評価対象の変更によって過去結果が比較不能にならないようにする。

候補：

```text
benchmark/
├─ fragment/
├─ final/
└─ retrieval/
```

評価データには `benchmark_version` を付与する。

可能であれば、Promptや方式の調整に使うValidation Setと、最終確認用Test Setを分離する。

ただし実Webページ由来データをGitへ含める場合は権利・機密性を考慮し、必要ならローカルのみでVersion manifestを管理する。

---

# 20. AI評価を一つのJudgeへ依存させない

モデル比較では可能な範囲で次を併用する。

```text
自動Metric
+
LLM Judge
+
人間確認
```

特にFragment Recall、Unsupported Fragment、Final Documentの事実忠実性等は、LLM Judgeだけを唯一の正解判定としない。

最終的なモデル・Prompt採用判断では代表サンプルを人間が確認する。

---

# 21. 再現性

AI比較・生成結果について、可能な限り以下を記録する。

- model name
- model revision
- 配布Artifact / GGUF filename
- quantization
- runtime
- runtime version
- GPU / VRAM条件
- context length
- temperature
- reasoning mode / effort
- seed（利用可能な場合）
- prompt hash / version
- schema hash / version
- embedding configuration
- reranker configuration

同一モデル名でも量子化・Runtime・Prompt設定が異なれば結果が変化するため、モデル名だけを実験Identityにしない。

---

# 22. 優先順位

次段階の設計・実装では特に以下を優先する。

1. Fragmentの原子性
2. Source Authority / Page Context / Epistemic Type / Evidence Strengthの分離
3. 矛盾・時系列を破棄しないデータ構造
4. Entity Resolution / Context Resolution
5. Source由来考察とCPC由来考察の分離
6. Raw Fragmentと統合知識の分離
7. Structured Final Representation
8. 大量Fragmentを扱うHierarchical Generation
9. Benchmark Versioningと再現性

これらの詳細Schemaは実装前にすべて固定する必要はない。Prototype改善では変更可能な形で導入し、実データ評価後に正式化する。
