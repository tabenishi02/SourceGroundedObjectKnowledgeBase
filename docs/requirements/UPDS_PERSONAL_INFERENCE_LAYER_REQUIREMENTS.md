# Source Grounded Object Knowledge Base — UPDS Personal Inference Layer要件

更新日: 2026-10-12

- Task: `C-02 [P0] UPDSをPersonal Inference Layerとして定義する`
- Status: Accepted
- Related:
  - `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`

## 1. 本書の位置づけ

本書はPhase CにおけるUserPreferenceDiscoverySystem（UPDS）側の責務を要件として固定する。

C-01では、SGOKBをWorld / Object Knowledge Layerとして定義し、ObjectそのもののIdentity・分類・属性・意味・Relation・Evidence等を扱う一方、特定ユーザーの嗜好・価値観・関心傾向に関する推論をSGOKBの責務外とした。

C-02ではその反対側として、UPDSを **Personal Inference Layer** と定義する。

UPDSは、ユーザーが選択・保存・収集した対象やその他の観測可能な行動をEvidenceとして、複数のSelection Eventを横断し、ユーザー自身が明示的には言語化していない可能性のある嗜好・関心・価値観・選択傾向について仮説を構築する。

ただし、観測された事実と推論された仮説を同一視してはならない。また、SGOKBのObject KnowledgeをUPDS内部へ第二の正本として複製してはならない。

C-02はUPDSが所有する論理責務を確定する。Concept自体の所有契約はC-03、SGOKBからObject / Facet / Relation等を取得する具体的な連携契約はC-04で確定する。

---

## 2. 正式定義

UPDSを次のように定義する。

> UPDSは、ユーザーに紐づくSelection Event等の観測事実と、必要に応じて外部Knowledge Providerから取得したObject Knowledgeを組み合わせ、Semantic Observation、Cross-object Pattern、Preference Hypothesis、Alternative Explanation、User-oriented Evidence Setを構築・維持するPersonal Inference Layerである。

UPDSが中心的に答える問いは次とする。

> ユーザーは何を選んできたか。複数の選択にはどのような意味的共通性があるか。その共通性から、どのような嗜好・関心・価値観・選択傾向が仮説として考えられるか。

UPDSは次の問いの正本を所有しない。

> Object Xとは何か。Xの正しい属性・定義・Relation・Evidenceは何か。

この種のWorld / Object KnowledgeはSGOKB等のKnowledge Provider側の責務である。

---

## 3. UPDSが所有するデータ・Knowledge

### PIL-01 — Selection Event

UPDSは、Personal Inferenceの入力となる観測可能なユーザー行動をSelection Eventとして所有する。

Selection Eventは推論ではなく、原則として「何が起きたか」を表す観測事実である。

例:

- Character / Work / Source等を保存・選択した。
- 収集対象として明示的に採用した。
- 特定の対象を継続的に蓄積した。
- UPDSへ分析対象として明示的に投入した。

Selection Eventは少なくとも論理上、次を区別可能でなければならない。

- event identity
- event type
- target reference
- observed timestamp
- acquisition / observation provenance
- event context
- 必要に応じたsource system

Selection Eventの物理schemaはUPDS側設計で確定する。

### PIL-02 — Selection EventはPreferenceそのものではない

Selection Eventを直接Preference factへ変換してはならない。

```text
Character Aを保存した
  ≠
Character Aが好きである
```

保存理由には、好意以外にも調査、批評、比較、資料収集、偶然、網羅目的等があり得る。

Selection EventはPreference HypothesisのEvidence候補であり、Preferenceそのものではない。

### PIL-03 — Semantic Observation

UPDSはSelection EventとObject Knowledgeを組み合わせて得られる、ユーザー文脈に結びついたSemantic Observationを所有できる。

例:

```text
Selection Event:
  Character Aを選択した

SGOKB Knowledge:
  Character Aのthemesに「自己犠牲」が含まれる

Semantic Observation:
  選択対象Aには「自己犠牲」というthemeが存在する
```

Semantic Observationは、Object Knowledge自体の複製ではなく、Selection Eventと外部Knowledge参照の組み合わせを示すPersonal Inference用の派生観測である。

Objectの定義やFacet本文をUPDSの独立正本として再所有してはならない。

### PIL-04 — Cross-source / Cross-object Pattern

UPDSは複数のSelection EventおよびSemantic Observationを横断し、反復する意味的Patternを構築できる。

例:

- 選択した複数Characterで`values`に自己犠牲が繰り返し現れる。
- 選択した複数Workで悲劇的結末や特定の世界観が共通する。
- 異なる作品・Sourceにまたがって同種のRelation構造が繰り返される。

Patternは「複数観測に共通する構造」であり、まだユーザーのPreference factではない。

### PIL-05 — Preference Hypothesis

UPDSはPatternや個別Evidenceから、ユーザーについてのPreference Hypothesisを構築できる。

例:

- ユーザーは自己犠牲を含むCharacter像に惹かれる可能性がある。
- ユーザーは家族関係を主要テーマとするWorkを選ぶ傾向がある可能性がある。
- ユーザーは特定の価値観の衝突を描く作品に関心を持つ可能性がある。

Preference Hypothesisは必ず **仮説** として扱い、観測事実やObject Knowledgeと同等の確定Factへ昇格させてはならない。

### PIL-06 — Hypothesis scope

Preference Hypothesisは対象範囲を区別可能でなければならない。

少なくとも次のようなscopeを論理的に表現できることを想定する。

- 特定Object
- Object Class
- Semantic Facet
- Concept / theme相当の意味単位
- Relation pattern
- 時間範囲
- 特定のSelection Event集合

単一の「ユーザーの好み」scoreへすべてを圧縮することを標準要件としない。

### PIL-07 — Alternative Explanation

UPDSはPreference Hypothesisに対してAlternative Explanationを保持できなければならない。

例:

```text
Observation:
  同一SeriesのCharacterを多数保存している

Hypothesis:
  このSeriesのCharacterデザインを好む

Alternative Explanation:
  Seriesを網羅的に収集しているだけかもしれない
```

別の合理的説明を無視し、最も魅力的な一つの解釈だけを確定事実として保存してはならない。

### PIL-08 — Supporting / Contradicting Evidence

Preference Hypothesisは、その根拠となるEvidence Setへ追跡可能でなければならない。

Evidence Setには少なくとも次を含められる。

- Selection Event
- Semantic Observation
- Pattern
- 参照したSGOKB Object / Facet / Statement / Relation
- 必要に応じてcontradicting observation

支持Evidenceだけでなく反証・例外も表現可能にする。

### PIL-09 — User-oriented Evidence Set

UPDSはPersonal Inferenceの根拠集合をUser-oriented Evidence Setとして所有する。

このEvidence SetはSGOKBのSource / Evidence Storeとは別責務である。

```text
SGOKB Evidence
= Objectについて何が根拠か

UPDS Evidence Set
= ユーザーについての仮説を何が支持・反証するか
```

UPDS Evidence SetからSGOKB Knowledgeを参照する場合は、論理的にはObject ID等の安定参照を利用し、Object Knowledge本文の無管理コピーを正本化しない。

具体的な参照契約はC-04で確定する。

### PIL-10 — Temporal Personal Inference

UPDSはユーザーの嗜好・関心・傾向が時間によって変化し得ることを前提とする。

過去のSelection Eventだけから現在のPreferenceを永久に固定してはならない。

Preference Hypothesisは必要に応じて、観測期間・有効期間・更新時刻等を区別可能にする。

---

## 4. 推論上の安全装置

### PIL-11 — Non-selectionを原則Negative Evidenceとみなさない

「選ばなかった」という事実だけを、嫌い・関心がないというEvidenceとして扱ってはならない。

ユーザーが対象を認知・閲覧する機会があったことまで確認できない場合、non-selectionは通常missing observationとして扱う。

### PIL-12 — FrequencyはPreference strengthそのものではない

選択回数や出現頻度はEvidenceになり得るが、そのままPreference strengthへ変換してはならない。

例えば10回選択したことは1回選択したことより強いsignalになり得るが、対象への露出頻度、Series網羅、収集方針等の交絡要因を考慮する必要がある。

### PIL-13 — Similarity / Search scoreをPreference probabilityとみなさない

SGOKBから取得したSimilarity score、Semantic Search score、ranking score等を、ユーザーがその対象を好む確率として扱ってはならない。

これらはObject間またはQueryとの意味的近さを表す補助signalであり、Personal Preferenceの確率ではない。

### PIL-14 — Causal explanationをFact化しない

Selection Patternから「なぜユーザーが選んだか」を推論する場合、その結果は原則としてHypothesisまたはAlternative Explanationとして保持する。

直接的な根拠がない限り、因果関係を確定Factとして保存しない。

### PIL-15 — 不明を許容する

Evidenceが不足している場合、UPDSは「判断不能」「insufficient evidence」「competing explanations」等の状態を許容しなければならない。

常に何らかのPreference Hypothesisを生成することを成功条件としない。

### PIL-16 — Confidenceを未校正確率として扱わない

Hypothesisの確からしさを表現する場合、未校正の`0.93`等を真の確率として扱うことを標準としない。

初期要件では、必要に応じて次のような離散状態を利用できる設計を優先する。

- weak
- moderate
- strong

または、supporting / contradicting EvidenceとAlternative Explanationを併記する。

具体的なHypothesis評価方式はUPDS側設計で確定する。

---

## 5. UPDSが所有しないもの

### PIL-NON-01 — Object canonical Knowledge

UPDSはCharacter / Work / Concept等のObject Identity、正式属性、Facet、Relation、Knowledge Statement、Source / EvidenceをWorld Knowledgeの正本として所有しない。

それらが必要な場合はSGOKB等のKnowledge Providerを参照する。

### PIL-NON-02 — Object Class Registry

Object Class hierarchy、Class Registry、Relation Type Registry等をUPDS独自に複製して第二の正本として維持しない。

Personal Inference向けの分類が必要な場合も、World/Object分類との境界を明示する。

### PIL-NON-03 — Object Knowledgeの無断修正

UPDSの推論結果を理由にSGOKB Object Knowledgeを書き換えてはならない。

例えば、

```text
ユーザーがCharacter Aを好む可能性が高い
```

から、

```text
Character Aは一般に好まれるCharacterである
```

というWorld Knowledgeへ変換してはならない。

### PIL-NON-04 — SGOKB内部依存

UPDSはSGOKBのSQLite table構造や内部repository classへ直接依存することを標準契約としない。

具体的なアクセス方法はC-04で確定するが、SGOKB内部schemaをUPDSの公開契約とみなさない。

### PIL-NON-05 — 単一Universal Preference Score

UPDSはユーザー全体を単一の好みscore、単一vector、単一ランキングへ必ず圧縮するシステムとして定義しない。

必要に応じてPreference Embedding等の派生表現を将来導入できるが、それはUPDS内の派生表現であり、Evidence・Pattern・Hypothesisを置き換える正本とはしない。

---

## 6. SGOKBとの責務境界

C-01とC-02を合わせ、基本境界を次のように定義する。

```text
World / Object side

SGOKB
├─ Object Identity
├─ Classification
├─ Attribute
├─ Semantic Facet
├─ Relation
├─ Knowledge Statement
├─ Source / Evidence
└─ Object Search / Similarity
        │
        │ Knowledge reference
        ▼
Personal side

UPDS
├─ Selection Event
├─ Semantic Observation
├─ Cross-object Pattern
├─ Preference Hypothesis
├─ Alternative Explanation
└─ User-oriented Evidence Set
```

### PIL-17 — 依存方向

基本依存方向は次とする。

```text
SGOKB
  ↓
UPDS
```

SGOKBはUPDSを知らなくてもWorld / Object Knowledge Baseとして単独成立しなければならない。

SGOKB CoreがUPDSのPreference schema、Pattern schema、Hypothesis schemaへ依存してはならない。

### PIL-18 — UPDSはKnowledge Consumer

UPDSはSGOKBに対してKnowledge Consumerとして振る舞う。

UPDSの都合でSGOKBのWorld Knowledge schemaへPreference専用fieldを追加することを前提としない。

汎用Object / Facet / Relation取得だけでは不足する場合に、専用Context/Profileを追加するかは後続Phaseで評価する。

### PIL-19 — SGOKB停止時の意味

UPDSがSemantic Observation生成のためSGOKB Knowledgeを必要とする場合、SGOKBが利用不能ならSemantic enrichmentは一時停止・degradeしてよい。

その場合でも、既に観測済みのSelection EventをWorld Knowledgeへ変換したり、推測でObject属性を補完したりしてはならない。

---

## 7. Conceptに関するC-02時点の境界

C-02ではConceptの最終所有契約を確定しない。

ただし次の二つは別物として扱うことを確定する。

```text
Concept「自己犠牲」とは何か
= World / Object Knowledge

ユーザーは「自己犠牲」というConceptを好む可能性がある
= Personal Inference
```

Conceptそのもののdefinition / Relation / EmbeddingをSGOKBが所有し、UPDSがConcept IDを参照する案を第一候補とするが、正式確定はC-03で行う。

---

## 8. 具体例

### 8.1 Character選択

```text
Selection Event:
  Character Aを保存

SGOKB:
  Character A
  ├─ values: self-sacrifice
  └─ themes: family

UPDS Semantic Observation:
  選択対象Aにはself-sacrifice / familyが含まれる
```

この時点ではPreferenceを確定しない。

### 8.2 Cross-object Pattern

```text
Character A → self-sacrifice
Character B → self-sacrifice
Character C → self-sacrifice
```

複数Selection Eventで同一意味要素が反復する場合、UPDSはPatternを形成できる。

```text
Pattern:
  self-sacrificeが複数の選択対象で反復している
```

### 8.3 Preference Hypothesis

Patternから次を生成できる。

```text
Hypothesis:
  ユーザーは自己犠牲的なCharacter像に惹かれる可能性がある
```

ただしAlternative Explanationとして、

```text
- 同一Seriesを網羅的に集めているだけかもしれない
- 最近そのthemeを含む作品を集中的に調査しているだけかもしれない
```

等を保持できる。

### 8.4 Work横断

```text
Work A → theme: 家族愛
Work B → theme: 家族愛
Work C → theme: 家族愛
```

これらを選択した事実と組み合わせて、

```text
Hypothesis:
  家族関係を中心に扱うWorkへ関心を持つ傾向がある可能性
```

と推論できる。

これはWork A/B/CのWorld Knowledgeではなく、ユーザーについてのPersonal Inferenceである。

---

## 9. 不変条件

C-02以降、UPDS側の責務境界について次を不変条件とする。

1. Selection EventとPreference Hypothesisを同一視しない。
2. PatternとPreference factを同一視しない。
3. Preference Hypothesisは根拠となるSelection Event / Semantic Observation / Patternへ追跡可能にする。
4. Alternative Explanationおよびcontradicting evidenceを表現可能にする。
5. Object canonical KnowledgeをUPDSの第二の正本として複製しない。
6. SGOKBのSimilarity / Search scoreをPreference probabilityとして再解釈しない。
7. non-selectionを原則としてdislike evidenceへ変換しない。
8. ユーザー嗜好が時間変化し得ることを許容する。
9. SGOKBはUPDSなしで単独成立し、UPDS専用schemaへ依存しない。
10. UPDSからSGOKBへの逆向き推論書き込みを標準責務としない。

---

## 10. C-02で確定したこと

C-02では次を確定する。

1. UPDSをPersonal Inference Layerとする。
2. Selection EventをUPDS所有の観測事実とする。
3. Selection Eventと外部Object Knowledgeを組み合わせたSemantic ObservationをUPDSが所有できる。
4. Cross-source / Cross-object PatternをUPDSが所有する。
5. Preference HypothesisをUPDSが所有し、確定Factとは区別する。
6. Alternative Explanationとsupporting / contradicting Evidenceを保持可能にする。
7. User-oriented Evidence SetをSGOKB Source / Evidenceとは別責務として定義する。
8. non-selection、頻度、Similarity / Search scoreを単純にPreferenceへ変換しない。
9. Object canonical Knowledge / Class Registry / Relation RegistryはUPDSの正本責務としない。
10. SGOKB → UPDSを基本依存方向とし、SGOKBはUPDSなしで単独成立させる。
11. Concept自体の最終所有契約をC-03へ残す。
12. SGOKBからの具体的な取得方式・ID / Version参照・MCP契約をC-04へ残す。

---

## 11. C-02完了判定

C-02の完了条件を次のように判定する。

- [x] UPDSをPersonal Inference Layerとして正式定義した。
- [x] Selection Eventを観測事実としてUPDS所有にした。
- [x] Semantic Observation / Pattern / Preference Hypothesisの責務を分離した。
- [x] Alternative Explanation / supporting / contradicting Evidenceを扱える要件を定義した。
- [x] User-oriented Evidence SetをSGOKB Evidenceと分離した。
- [x] Selection EventやSimilarity scoreを直接Preferenceへ変換しない境界を定義した。
- [x] UPDSがObject canonical Knowledgeを重複所有しない境界を定義した。
- [x] SGOKBがUPDSなしで単独成立する依存方向を確認した。
- [x] Concept所有の最終判断をC-03へ残した。
- [x] SGOKB → UPDSの具体的連携契約をC-04へ残した。

以上により、`C-02 [P0] UPDSをPersonal Inference Layerとして定義する` は要件上完了とする。
