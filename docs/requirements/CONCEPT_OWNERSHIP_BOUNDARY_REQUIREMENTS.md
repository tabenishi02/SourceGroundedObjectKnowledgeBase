# Source Grounded Object Knowledge Base — Concept Ownership Boundary要件

更新日: 2026-10-12

- Task: `C-03 [P1] Conceptの所有境界を確定する`
- Status: Accepted
- Related:
  - `docs/requirements/SGOKB_WORLD_OBJECT_KNOWLEDGE_REQUIREMENTS.md`
  - `docs/requirements/UPDS_PERSONAL_INFERENCE_LAYER_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`

## 1. 本書の位置づけ

C-01ではSGOKBをWorld / Object Knowledge Layer、C-02ではUPDSをPersonal Inference Layerとして定義した。

C-03では、その境界上で特に重複所有が起こりやすい **Concept** の正本責務を確定する。

本書でいうConceptは、SGOKB Class Registry上の`Concept`およびその下位ClassとしてObject化される意味対象を指す。B-02Dでは少なくとも次を正式Classとして採用済みである。

```text
Concept
├─ Theme
├─ Ideology
├─ Trait
├─ Emotion
├─ Motivation
├─ StateConcept
├─ RoleConcept
└─ ArtifactTypeConcept
```

C-03では、これらConcept ObjectのIdentity・定義・Relation・Evidence・Version・検索表現をどちらのプロジェクトが正本として所有するかを固定する。

SGOKBからUPDSへConceptをどのAPI / MCP Toolで渡すか、Version参照をどのfieldで持つか等の具体的な連携契約はC-04で確定する。

---

## 2. 正式決定

Conceptの所有境界を次のように確定する。

> **Conceptそのもののcanonical identity、classification、definition、Semantic Facet、Relation、Source / Evidence、Knowledge Version、Search Representation / EmbeddingはSGOKBが所有する。UPDSはSGOKBのConcept Object IDを参照し、そのConceptに対するユーザー固有のSemantic Observation、Pattern、Preference Hypothesis、User-oriented Evidenceを所有する。**

したがって、基本構造は次とする。

```text
SGOKB
Concept: self-sacrifice
├─ object_id
├─ class = Theme / Trait等
├─ definition
├─ properties
├─ relations
├─ evidence
├─ version
└─ concept embedding
        │
        │ stable Concept reference
        ▼
UPDS
├─ Selection Event
├─ Semantic Observation
│  └─ concept_ref = SGOKB Concept ID
├─ Pattern
└─ Preference Hypothesis
   └─ 「ユーザーはself-sacrificeを含む対象に惹かれる可能性」
```

---

## 3. SGOKBが所有するConcept責務

### CON-01 — Concept Identity

Concept Objectの永続IdentityはSGOKBが所有する。

対象には少なくとも次を含む。

- `object_id`
- name / aliases
- `primary_class`
- `additional_classes`
- lifecycle status
- current Knowledge Version

UPDSは同じ意味対象に独自のcanonical Concept IDを発行して第二の正本を作ってはならない。

Conceptの名称変更、alias追加、Class訂正等があってもSGOKBの安定`object_id`を維持する。

### CON-02 — Concept Classification

Conceptが`Theme`、`Trait`、`Emotion`、`Motivation`等のどのClassに属するかはSGOKB Class Registry側で管理する。

UPDSはPersonal Inference上便利だからという理由だけでSGOKBのConcept Classを独自に再定義してはならない。

UPDS固有の分析カテゴリが必要な場合は、SGOKB Concept Classとは別のUPDS内部vocabularyとして扱う。

### CON-03 — Definition / Semantic Facet

Conceptそのものについての次のようなWorld KnowledgeはSGOKBが所有する。

- definition
- properties
- implications
- examples
- related concepts
- historical / contextual meaning
- 必要に応じたその他Semantic Facet

例えば「自己犠牲とは何か」「ノスタルジアとは何か」「反英雄という概念はどのような特徴を持つか」はSGOKB側の問いである。

### CON-04 — Concept Relation

Concept間またはConceptと他Object間のWorld / Object RelationはSGOKBが所有する。

例:

- Concept A is related to Concept B
- Ideology A opposes Ideology B
- Theme A appears in Work B
- Trait A characterizes Character B

具体的Relation Type vocabularyは後続Data Model設計で確定するが、Relationの意味がWorld / Object側にある限り正本はSGOKBとする。

### CON-05 — Source / Evidence / Provenance

Concept definition、property、Relation、Knowledge Statement等の根拠となるSource / EvidenceはSGOKBが管理する。

UPDSはConceptについて独自のSource / Evidence正本を再構築しない。

UPDSがConceptの意味をPersonal Inferenceに利用した場合、必要に応じて利用時点のSGOKB参照を追跡できるようにする。

### CON-06 — Knowledge Version

Concept Knowledgeの更新履歴・current VersionはSGOKBが所有する。

Conceptの定義やRelationが更新されても、Concept ObjectのIdentityとKnowledge Versionを分離する。

UPDSはConceptのコピーを独自にversion管理するのではなく、必要に応じて「どのSGOKB Concept / Versionを参照して推論したか」を記録できる構造とする。

Version参照の具体契約はC-04で確定する。

### CON-07 — Concept Search Representation / Embedding

Concept Object、Concept Facet、Concept Knowledge Statement等のSemantic Search / Similarity用EmbeddingはSGOKBが所有する派生検索表現とする。

SGOKB Concept Embeddingは、

> 「このConceptが意味空間上どのようなConceptか」

を表す。

これは、

> 「このユーザーがそのConceptをどの程度好むか」

を表すPreference Embeddingではない。

---

## 4. UPDSがConceptについて所有する責務

### CON-UPDS-01 — Concept Reference

UPDSはPersonal Inferenceの対象としてSGOKB Concept IDを参照できる。

例:

```text
Semantic Observation
├─ selection_event_id = ...
├─ selected_object_id = Character A
└─ concept_ref = SGOKB Concept「self-sacrifice」
```

UPDSが保存するのは「ConceptをPersonal Inferenceでどう参照したか」であり、Conceptそのものの正本ではない。

### CON-UPDS-02 — User-to-Concept Semantic Observation

次のようなユーザー文脈に結び付いた観測はUPDSが所有する。

```text
ユーザーが選択したCharacter Aには
Concept「self-sacrifice」が関連している
```

これは、

```text
Concept「self-sacrifice」の定義
```

とは別物である。

前者はPersonal side、後者はWorld / Object sideである。

### CON-UPDS-03 — User-to-Concept Pattern

複数Selection Eventで同じConceptが反復するというPatternはUPDSが所有する。

例:

```text
Character A → self-sacrifice
Character B → self-sacrifice
Work C      → self-sacrifice

Pattern:
  選択対象群でself-sacrificeが反復している
```

Concept自体の意味はSGOKB、反復して選択対象へ現れたというユーザー文脈はUPDSである。

### CON-UPDS-04 — Preference Hypothesis

Conceptに対するユーザー固有のPreference HypothesisはUPDSが所有する。

例:

- ユーザーはself-sacrificeを含むCharacter像に惹かれる可能性がある。
- ユーザーはfamilyというThemeを扱うWorkに関心を持つ傾向がある可能性がある。
- ユーザーはIdeology Aそのものより、Ideology AとBの対立構造に惹かれる可能性がある。

これらをSGOKB Concept Knowledgeへ書き戻してはならない。

### CON-UPDS-05 — User-oriented Evidence Set

Concept Preference Hypothesisを支持・反証するSelection Event、Semantic Observation、Pattern等はUPDSのUser-oriented Evidence Setとして管理する。

SGOKB Evidenceと役割を分離する。

```text
SGOKB Evidence
= Concept Xとは何かの根拠

UPDS Evidence
= ユーザーがConcept Xを好む可能性の根拠
```

---

## 5. ConceptとUPDS内部vocabularyの境界

### CON-08 — すべての分析ラベルをConcept Object化しない

UPDS内部で用いる分析用status、処理分類、推論状態等は、自動的にSGOKB Concept Objectへ昇格させない。

例:

- `weak / moderate / strong`
- `insufficient_evidence`
- `competing_explanations`
- `recent_interest`
- `selection_frequency_high`

これらが単なるUPDS schema / status / analytic labelである限り、SGOKB Conceptではない。

### CON-09 — 一般概念として独立Knowledge価値がある場合のみConcept候補とする

ある語がUPDS分析で頻繁に出現することだけを理由にConcept Objectを新規作成しない。

独立Concept Objectとするかは、B-02DのObject境界原則に従う。

少なくとも次のような条件を考慮する。

- ユーザー固有でなく一般的意味対象として成立する。
- 長期的に安定したIdentityを持つ。
- 複数Objectから参照する価値がある。
- 定義・Relation・Evidence・Versionを独立管理する価値がある。
- 単なる一時的分析ラベルやscalar valueではない。

### CON-10 — 同じ語でも役割を分ける

同じ文字列がSGOKB ConceptとUPDS推論ラベルの双方に現れることを許容するが、Identityを同一視しない。

例:

```text
SGOKB Concept:
  nostalgia
  = 一般概念としてのノスタルジア

UPDS Hypothesis:
  「ユーザーはnostalgiaを喚起するWorkを好む可能性」
```

また、

```text
UPDS internal label:
  recent_interest
```

が分析statusとして使われているだけなら、同名・類似概念をSGOKBへ登録する必要はない。

---

## 6. 未登録Conceptが必要になった場合

### CON-11 — UPDSはcanonical Conceptを勝手にmintしない

Personal Inference中に、SGOKBに存在しない意味Conceptが必要になった場合、UPDSはその場でcanonical SGOKB Concept IDを発行してはならない。

次のような状態として扱える設計を前提とする。

- unresolved concept reference
- provisional semantic label
- Concept proposal

### CON-12 — Concept proposalとConcept adoptionを分離する

UPDSやLLMが「このConceptをSGOKBへ追加すると有用」と提案することは許容する。

ただし、提案とSGOKB canonical Concept作成は別操作とする。

```text
UPDS detects semantic need
        ↓
Concept proposal
        ↓
SGOKB-side review / normal Object registration process
        ↓
SGOKB Concept Object created
        ↓
UPDS unresolved referenceをstable Concept IDへ解決
```

UPDSのInference処理を成功させるためだけに、意味的に不明確なConceptをSGOKBへsilent登録しない。

Concept proposalの具体的な交換契約・MCP write方針はC-04および後続Phaseで具体化する。

### CON-13 — 未登録Conceptを既存Conceptへ無理にfallbackしない

該当するConceptが存在しない場合、近い既存Conceptへ自動的に丸め込んではならない。

例えば「自己犠牲」と「献身」が近いからという理由だけで、同一Concept IDへ自動統合しない。

必要ならunresolved / proposal状態を維持する。

---

## 7. Concept RelationとPersonal Relationの境界

次の二種類を明確に分離する。

### SGOKB側

```text
Concept A related_to Concept B
Concept A contrasts_with Concept C
Theme A appears_in Work X
Trait A characterizes Character Y
```

これらはWorld / Object Relationである。

### UPDS側

```text
User may_prefer Concept A
User shows_repeated_selection_for Concept B
Hypothesis H is_supported_by Concept C occurrence
```

これらはPersonal Inference上の関係であり、SGOKB Relation Graphへ保存しない。

### CON-14 — UserをSGOKB Concept Relationの主体にしない

SGOKB Relation Graphへ、次のようなPersonal relationを追加してはならない。

- `user_likes_concept`
- `user_avoids_concept`
- `user_affinity`
- `user_interest_score`

これらが必要ならUPDS schemaで表現する。

---

## 8. Embeddingの境界

### CON-15 — Concept EmbeddingはSGOKB所有

Conceptそのものを表すEmbeddingはSGOKBのSearch Representationである。

用途:

- Concept Semantic Search
- Concept Similarity
- Object ↔ Concept retrieval支援
- Concept clusteringの補助

### CON-16 — Preference EmbeddingはUPDS所有

将来UPDSがユーザー嗜好の派生Embeddingを導入する場合、そのEmbeddingはUPDS所有とする。

例:

```text
SGOKB Concept embedding
= self-sacrificeの意味表現

UPDS Preference embedding
= ユーザーの選択傾向を表す派生表現
```

UPDS Preference EmbeddingがSGOKB Concept Embeddingを入力として利用することは許容するが、両者を同一vectorとして扱ってはならない。

### CON-17 — Preference EmbeddingでConcept Knowledgeを上書きしない

UPDSのPreference vectorやConcept affinityが変化しても、SGOKBのConcept definition / embedding / relationを更新する理由にはならない。

---

## 9. Version / Referential Boundary

### CON-18 — Stable Concept IDを参照の基本単位とする

UPDSからConceptを参照する際の基本IdentityはSGOKBの安定`object_id`とする。

名称・alias・Embedding nearest neighborのみを永続参照として利用してはならない。

### CON-19 — 推論再現性のためVersion参照を許容する

Concept Knowledgeの意味内容がVersion更新で変化し得るため、UPDSのSemantic Observation / Hypothesis生成時に、必要に応じて参照したSGOKB Knowledge Versionを記録できることを要件とする。

ただし、

```text
Concept identity = stable object_id
Concept knowledge state = version
```

を分離する。

具体的な`object_id` / `version_id` / retrieval timestamp等の連携payloadはC-04で確定する。

### CON-20 — Concept Version更新でUPDS Identity参照を壊さない

SGOKB ConceptのKnowledge Versionが更新されても、UPDS Selection Event / Semantic Observation / Hypothesisが参照するConcept Identityが別Objectへ変わってはならない。

必要に応じてUPDS側でSemantic Observation再評価・stale検出を行う設計は許容する。

---

## 10. 具体例

| 内容 | 所有 | 理由 |
|---|---|---|
| 「自己犠牲」というConceptの`object_id` | SGOKB | World / Object Identity |
| 自己犠牲のdefinition | SGOKB | Concept Knowledge |
| 自己犠牲と献身のRelation | SGOKB | Concept間World Relation |
| 自己犠牲ConceptのEmbedding | SGOKB | Concept Search Representation |
| Character Aに自己犠牲themeがある | SGOKB | Object / Concept Knowledge |
| ユーザーがCharacter Aを選択した | UPDS | Selection Event |
| 選択対象Aに自己犠牲Conceptが存在するという観測 | UPDS | Semantic Observation |
| 選択対象群で自己犠牲Conceptが反復する | UPDS | Cross-object Pattern |
| ユーザーは自己犠牲Conceptを好む可能性がある | UPDS | Preference Hypothesis |
| このHypothesisを支持するSelection Event集合 | UPDS | User-oriented Evidence Set |
| `insufficient_evidence` | UPDS内部 | Inference statusであり通常Conceptではない |
| 未登録の新しい意味テーマ候補 | unresolved / proposal | SGOKB review前はcanonical Conceptにしない |

---

## 11. C-01 / C-02 / C-03を合わせた境界

```text
                    SGOKB
              World / Object Layer

Concept Object
├─ stable identity
├─ class
├─ definition
├─ facet
├─ relation
├─ evidence
├─ version
└─ embedding
        │
        │ Concept ID / Knowledge reference
        ▼
                    UPDS
             Personal Inference Layer

Selection Event
        ↓
Semantic Observation ──→ Concept reference
        ↓
Cross-object Pattern
        ↓
Preference Hypothesis
├─ supporting evidence
├─ contradicting evidence
└─ alternative explanation
```

この構造により、同じConcept KnowledgeをSGOKBとUPDSの双方が別々に生成・更新することを防ぐ。

---

## 12. 不変条件

C-03以降、次を不変条件とする。

1. Concept Objectのcanonical identityはSGOKBが所有する。
2. Concept definition / Facet / Relation / Evidence / VersionはSGOKBが所有する。
3. Concept Search Representation / EmbeddingはSGOKB側の派生物とする。
4. UPDSはSGOKB Concept IDを参照し、Concept canonical Knowledgeを第二の正本として複製しない。
5. ユーザーとConceptのPreference関係はUPDSが所有する。
6. UPDS内部分析ラベルを自動的にSGOKB Concept Objectへ昇格させない。
7. 未登録Conceptが必要でもUPDSがcanonical SGOKB IDを勝手に発行しない。
8. Concept proposalとConcept adoptionを分離する。
9. Concept Knowledge Version更新でConcept Identity参照を壊さない。
10. Concept EmbeddingとUser Preference Embeddingを同一視しない。
11. SGOKBはUPDSなしでConcept Knowledge Baseとして単独成立する。
12. UPDS固有のPreference情報をSGOKB Concept Knowledgeへ逆流させない。

---

## 13. C-03で確定したこと

C-03では次を確定した。

1. Conceptそのものの正本所有者をSGOKBとする。
2. Concept Identity / Classification / Definition / Semantic Facet / Relation / Evidence / Version / EmbeddingをSGOKB責務とする。
3. UPDSはSGOKB Concept IDを参照してSemantic Observation / Pattern / Preference Hypothesisを構築する。
4. User-to-Concept PreferenceはUPDS責務とする。
5. UPDS内部vocabularyとSGOKB Concept Registryを分離する。
6. UPDSで未登録Conceptが必要になった場合はunresolved / provisional / proposalとして扱い、canonical Conceptのsilent作成を禁止する。
7. Concept proposalからSGOKB採用までは別のreview / Object registration boundaryとする。
8. Concept EmbeddingとPreference Embeddingの所有を分離する。
9. Stable Concept Object IDを参照基準とし、必要に応じKnowledge Version参照を併記できるようにする。
10. 具体的なMCP Tool、payload、Version / stale contractはC-04へ引き継ぐ。

---

## 14. C-03完了判定

- [x] Conceptのcanonical所有者をSGOKBへ確定した。
- [x] Concept Definition / Relation / Embeddingの所有境界を確定した。
- [x] UPDSがConcept IDを参照してPreference Evidence / Hypothesisを構築する責務を定義した。
- [x] UPDS内部分析vocabularyとSGOKB Conceptを分離した。
- [x] 未登録Conceptのproposal / unresolved境界を定義した。
- [x] Concept EmbeddingとPreference Embeddingを分離した。
- [x] Stable Concept IDとKnowledge Versionの責務を分離した。
- [x] 具体的なSGOKB → UPDS連携契約をC-04へ残した。

以上により、`C-03 [P1] Conceptの所有境界を確定する` は要件上完了とする。
