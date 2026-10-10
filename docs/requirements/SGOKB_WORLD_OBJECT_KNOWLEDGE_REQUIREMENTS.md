# Source Grounded Object Knowledge Base — World / Object Knowledge Layer要件

更新日: 2026-10-11

- Task: `C-01 [P0] SGOKBをWorld/Object Knowledge Layerとして定義する`
- Status: Accepted
- Related:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/requirements/SEARCH_REQUIREMENTS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_TASKS.md`
  - `docs/planning/KNOWLEDGE_BASE_REDESIGN_HANDOFF.md`

## 1. 本書の位置づけ

本書はPhase CにおけるSGOKB側の責務を要件として固定する。

SGOKBを **World / Object Knowledge Layer** と定義し、外部世界または作品世界に存在するObjectについて、Source / Evidenceへ遡れるKnowledgeを保持・検索・提供する責務を持たせる。

ここでいう「World」は現実世界だけを意味しない。Character、Work、Concept、Person、Organization、Place、Event等、SGOKBのClass RegistryでObjectとして扱う対象について、そのObject自体を説明するKnowledgeを意味する。

一方、「このユーザーが何を好むか」「なぜそれを選ぶか」といったユーザー固有の意味付け・傾向・仮説はSGOKBのKnowledge責務に含めない。

C-01はSGOKB側の境界だけを確定する。UPDS側の正式な所有データはC-02、Conceptの両システム間所有契約はC-03、MCPを含む連携契約はC-04で確定する。

---

## 2. 正式定義

SGOKBを次のように定義する。

> SGOKBは、Source / Evidenceを根拠として、ObjectそのもののIdentity、分類、属性、意味、Semantic Facet、他ObjectとのRelation、時間的状態、根拠および検索用表現を管理するWorld / Object Knowledge Layerである。Knowledgeは特定ユーザーの嗜好推論から独立して成立しなければならない。

SGOKBに保存するKnowledgeは、原則として次の問いへ答えるためのものとする。

> Xとは何か。Xにはどのような属性・意味・特徴・関係・根拠があるか。

次の問いへ答えるためのKnowledgeはSGOKBの責務外とする。

> このユーザーはXを好むか。なぜXを選ぶのか。複数の選択からどのような嗜好・価値観・関心傾向を推測できるか。

---

## 3. SGOKBが所有するKnowledge

### WOK-01 — Object Identity / Classification

SGOKBはObjectの安定Identityと分類を所有する。

対象には少なくとも次を含む。

- `object_id`
- name / aliases
- `primary_class`
- `additional_classes`
- Class Registry上の所属
- Object lifecycle / status
- Object Knowledge Versionとの対応

Object Identityはユーザーの好悪や利用頻度から変化させてはならない。

### WOK-02 — Object Attribute

SGOKBはObjectそのものを説明する構造化属性を保持できる。

例:

- Characterの所属、役割、外見上の属性
- Workの作者、媒体、公開時期
- Placeの所在地
- Organizationの関係主体
- Eventの発生時期

属性は可能な限りEvidenceへgrounding可能でなければならない。

### WOK-03 — Semantic Facet

SGOKBはObjectを意味的観点ごとに整理したSemantic Facetを保持できる。

例:

- Character: personality / values / motivation / behavior / relationships / role / themes
- Work: themes / worldview / narrative / tone
- Concept: definition / properties / implications / related concepts

FacetはObjectについての意味的記述であり、「そのFacetをユーザーが好む」という評価を含めない。

### WOK-04 — Object Relation

SGOKBはObject間のRelationを保持する。

例:

- CharacterがWorkに登場する
- PersonがWorkを制作した
- WorkがSeriesに属する
- Conceptが別Conceptと関連する
- EventがPlaceで発生する

Relationの意味はObject間の関係であり、ユーザーとObjectの嗜好関係をSGOKB Relationとして表現してはならない。

### WOK-05 — Knowledge Statement / Derivation

SGOKBはEvidence-groundedなKnowledge Statementを保持できる。

`direct_statement`、`synthesis`、`interpretation`、`reported_view`等、Object Result要件で認められたderivation kindを利用できる。

主観的な内容であっても、Sourceが誰かの評価・解釈・社会的認識を述べている場合は、attributionとEvidenceを保持した`reported_view`等のObject Knowledgeとして扱える。

これは「SGOKB利用者本人がその見解を持つ」と推論することを意味しない。

### WOK-06 — Source / Evidence / Provenance

SGOKBはObject Knowledgeの根拠となるSource、Snapshot、Raw Artifact、Normalized Run、EvidenceおよびProvenance chainを管理する。

Object Knowledgeは、可能な範囲で具体的なEvidenceまで追跡可能でなければならない。

### WOK-07 — Version / Temporal Scope

SGOKBはObject Knowledge Versionおよび必要なtemporal scopeを管理する。

時間によって変化するObjectの状態を、ユーザーの嗜好変化と混同してはならない。

### WOK-08 — Search Representation

SGOKBはObject / Facet / Knowledge Statement / Evidence等について、Lexical Search、Semantic Search、Similarity Search、Relation Searchに必要な検索表現を生成・保持できる。

Embedding、Vector Index、ranking score等は検索用の派生表現であり、ユーザーの好みを表すscoreとして解釈してはならない。

---

## 4. SGOKBが所有しないPersonal Inference

### WOK-NON-01 — Preference

次のようなユーザー固有の嗜好判断をSGOKB Object Knowledgeへ保存してはならない。

- 「ユーザーはCharacter Aが好きである」
- 「ユーザーは悲劇的な作品を好む」
- 「ユーザーはConcept Xを強く好む」
- like / dislike / preference score / affinity等のユーザー評価

### WOK-NON-02 — Selection Patternからの推論

Source Capture、Object登録、検索、閲覧、選択等の行動から、SGOKB自身が次のような意味を推論してはならない。

- 関心度
- 嗜好強度
- 価値観
- 性格傾向
- 心理傾向
- 選択理由
- 将来の選択予測

これらはPersonal Inference Layer側の責務候補であり、C-02以降で正式化する。

### WOK-NON-03 — User-specific Pattern / Hypothesis

複数Objectを横断して得られる「このユーザーについて」のPattern、Hypothesis、Alternative Explanation等をSGOKBのKnowledgeとして保持してはならない。

Object間の共通特徴や類似度自体はSGOKBで計算・提供できるが、その結果をユーザー特性へ変換する推論は行わない。

### WOK-NON-04 — User-to-Object Preference Relation

`likes`, `prefers`, `avoids`, `is_interested_in`等のユーザー固有Relationを、SGOKBの通常Object Relationとして登録してはならない。

SGOKBのRelation GraphはWorld / Object関係を表し、Personal Preference Graphとして利用しない。

### WOK-NON-05 — Preference専用Embedding / Profile

ユーザーの選択履歴を集約したPreference Embedding、taste vector、psychological profile等をSGOKB canonical / derived Knowledgeとして生成しない。

SGOKBのObject EmbeddingはObjectを表現するためのものであり、ユーザーを表現するためのものではない。

---

## 5. CurationとPersonal Inferenceの境界

SGOKBはCurated Knowledge Baseであるため、ユーザーの選択行為を完全に排除するわけではない。

重要なのは、**運用上の選択記録**と**選択から導く意味推論**を分離することである。

### WOK-09 — Curation metadataは保持可能

システム運用・監査・Provenanceに必要な場合、次のような事実的metadataは保持できる。

- SourceがいつCapture / Importされたか
- Objectがいつ作成されたか
- どのSourceをObject候補として関連付けたか
- Human DecisionによりSource / Result / Registry proposalがaccept / rejectされたか
- 誰またはどの処理主体が操作を実行したか（必要な範囲）

これらはObjectそのものを説明するKnowledgeではなく、workflow / provenance metadataとして扱う。

### WOK-10 — Curation eventを嗜好へ変換しない

次の変換をSGOKB内部で行ってはならない。

```text
Source Aを保存した
  ↓
Object Xに関心がある
  ↓
Concept Yを好む
```

最初の「保存した」は事実的なCuration Eventとして必要に応じて記録できる。

後段の「関心がある」「好む」はPersonal Inferenceであり、SGOKB Knowledgeへ昇格させない。

### WOK-11 — 頻度・順位をPreference scoreとして扱わない

Capture回数、Object数、検索回数、閲覧回数、Similarity score、Search ranking等を、そのままユーザーのPreference scoreとみなしてはならない。

これらの値を他システムがEvidenceの一部として利用するかは、そのシステム側の責務で判断する。

---

## 6. 境界判定ルール

新しいKnowledge種別をSGOKBへ追加する際は、次の順序で判定する。

1. **その情報の主語は何か。**
   - Object / Source / Evidence / World内Relationを説明する → SGOKB候補。
   - 「このユーザー」を説明する → 原則SGOKB外。
2. **ユーザーが変わっても意味が成立するか。**
   - 成立する → World / Object Knowledge候補。
   - ユーザーごとに意味が変わる → Personal Inference候補。
3. **Source / Evidenceまたは明示的なObject管理事実へgroundingできるか。**
   - できる → SGOKB候補。
   - 選択履歴からユーザー特性を推定した結果である → SGOKB外。
4. **検索scoreや操作回数を意味的主張へ変換していないか。**
   - 変換している → SGOKB外。
5. **Objectについての第三者の見解か、利用者本人についての推論か。**
   - 第三者の見解をattribution付きで保持する → SGOKBで扱える。
   - 利用者本人の嗜好・心理・価値観を推論する → SGOKB外。

### 6.1 判定例

| 情報 | SGOKB | 理由 |
|---|---|---|
| Character Aは自己犠牲的に行動する | 対象 | CharacterについてのKnowledge |
| Work Bは家族愛を主要テーマとして扱う | 対象 | WorkについてのKnowledge |
| Source CはCharacter Aを「反英雄」と評している | 対象 | attribution付きreported view |
| Character AとCharacter Dはvalues Facetが類似する | 対象 | Object間Similarity |
| ユーザーはCharacter Aを保存した | metadataとして可 | Curation事実でありObject Knowledgeではない |
| ユーザーはCharacter Aが好きだ | 対象外 | Personal Preference |
| Character AとDを両方保存したため、ユーザーは自己犠牲を好む | 対象外 | Cross-object Personal Inference |
| Character Aの検索scoreが高いのでユーザーの好みである | 対象外 | Search scoreの意味誤用 |

---

## 7. 他コンポーネントとの責務関係

### 7.1 Object Result

Object ResultはWorld / Object Knowledgeの候補を生成する。

Validator / Importerは、少なくともSchema上Personal Inference専用fieldをSGOKB Object Knowledgeへ混在させない設計とする。

Personal Inferenceらしき自由文がObject Resultへ混入した場合の機械的検出範囲は、最終Schema / Validation設計で具体化する。

### 7.2 Search / Retrieval

SGOKB RetrievalはObject / Facet / Statement / Relation / Evidenceを検索・比較する。

検索結果を特定ユーザー向けに意味解釈してPreference Hypothesisへ変換することはSGOKB Retrievalの責務ではない。

### 7.3 MCP

将来MCPはSGOKB Knowledge Access LayerとしてWorld / Object Knowledgeを外部Clientへ提供する。

MCP ClientがそのKnowledgeをPersonal Inferenceへ利用できる設計は許容するが、SGOKB CoreがそのClient固有推論を所有しない。

具体的なSGOKB → UPDS取得契約はC-04で確定する。

### 7.4 Concept

ConceptもWorld / Object Knowledgeとして表現可能なClassである。

ただし、Conceptそのものの定義・Relation・EmbeddingをSGOKBが正式所有し、UPDSがそのIDを参照するというプロジェクト間契約の最終確定はC-03で行う。

C-01では、Concept Knowledgeと「ユーザーがConceptを好む」というPersonal Inferenceが別責務であることだけを確定する。

---

## 8. 不変条件

C-01以降、SGOKB Coreは次を不変条件とする。

1. SGOKB canonical KnowledgeはWorld / Object Knowledgeとして成立する。
2. Object Knowledgeは特定ユーザーのPreference Profileを必要としない。
3. `object_id`のIdentityはユーザー嗜好から独立する。
4. Object Attribute / Facet / Relation / StatementはユーザーPreferenceを暗黙に表現しない。
5. Source / Evidenceの採用・保存事実をPreferenceそのものとみなさない。
6. Object / Facet / Statement EmbeddingをUser Preference Embeddingとして再解釈しない。
7. SGOKBはPersonal Inference機能が存在しなくてもKnowledge Baseとして単独成立する。
8. Personal Inferenceを必要とするClientはSGOKBの外側で実行する。

---

## 9. C-01で確定したこと

C-01では次を確定した。

1. SGOKBをWorld / Object Knowledge Layerとする。
2. SGOKBの中心的な問いを「Xとは何か。Xにはどのような属性・意味・関係・根拠があるか」とする。
3. Object Identity / Classification / Attribute / Semantic Facet / Relation / Statement / Source / Evidence / Provenance / Version / Search RepresentationをSGOKB責務とする。
4. 第三者の主観的見解も、attributionとEvidenceを保持するObject KnowledgeであればSGOKBで扱える。
5. 「ユーザーが何を好むか」「なぜ選ぶか」「複数選択から何を推測できるか」はSGOKB責務外とする。
6. Curation metadataは必要に応じてSGOKBが保持できるが、それをPreferenceへ意味変換しない。
7. Search / Similarity / Embedding scoreをPreference scoreとして扱わない。
8. SGOKBはPersonal Inference Layerなしで単独成立する。
9. Conceptのプロジェクト間所有契約はC-03へ、SGOKB → UPDS連携契約はC-04へ引き継ぐ。

---

## 10. C-01完了判定

C-01の完了条件を次のように判定する。

- [x] SGOKBをWorld / Object Knowledge Layerとして正式定義した。
- [x] SGOKBが所有するKnowledge種別を明文化した。
- [x] Personal Preference / Pattern / HypothesisをSGOKBへ保存しない境界を明文化した。
- [x] Curation metadataとPersonal Inferenceを分離した。
- [x] Object Similarity / EmbeddingとUser Preferenceを分離した。
- [x] Concept所有の最終判断をC-03へ残した。
- [x] SGOKB → UPDSの具体的連携契約をC-04へ残した。

以上により、`C-01 [P0] SGOKBをWorld/Object Knowledge Layerとして定義する` は要件上完了とする。
