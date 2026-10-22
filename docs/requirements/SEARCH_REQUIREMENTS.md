# Source Grounded Object Knowledge Base — Search / Retrieval要件

更新日: 2026-10-23

- Task: `B-05 [P0] 検索要件を定義する`
- Status: Accepted / **R2-02 superseding amendment active**
- Parent: Phase B — 要件定義の全面更新
- Inputs:
  - `docs/requirements/KNOWLEDGE_BASE_PURPOSE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_TYPE_MODEL.md`
  - `docs/requirements/OBJECT_TYPE_BOUNDARIES.md`
  - `docs/requirements/SOURCE_EVIDENCE_REQUIREMENTS.md`
  - `docs/requirements/OBJECT_RESULT_REQUIREMENTS.md`
  - `docs/decisions/KNOWLEDGE_BASE_REDESIGN_DECISION.md`
  - `docs/reference/EMBEDDING_VECTOR_SEARCH_RESEARCH.md`
- R2-02 amendment: `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`
- B-06 result: `docs/requirements/WORKFLOW_RESPONSIBILITY_REQUIREMENTS.md`
- B-07 result: `docs/requirements/NON_FUNCTIONAL_REQUIREMENTS.md`

---

## 0. R2-02 superseding amendment — active Search requirements

This section is normative for the current R2 design. Where the historical B-05 / Phase I wording later in this file conflicts with this section, **this section takes precedence**. The older wording is retained to preserve the original requirement history.

### R2-SRH-01 — Active Object semantic family is hierarchical

Normal Object semantic retrieval MUST use the canonical semantic hierarchy:

```text
object_overview
+ facet
+ statement
```

`object_overview` is compact Object-level context. It is not a copy of all accepted Knowledge. Detailed Knowledge remains in Facet and Statement representations.

### R2-SRH-02 — `object_overall` is legacy-only

`object_overall` MUST NOT be used by normal active post-R2 Object Search, Hybrid Search, overall Object Similarity, new embedding memberships, or new Vector Index memberships.

It MAY remain readable only for migration, rollback, historical inspection, historical benchmark interpretation, or controlled cleanup.

`object_overview` is not a rename or semantic alias of `object_overall`; persisted v1 rows MUST NOT be relabeled in place.

### R2-SRH-03 — Exact Object overview semantic scope

The deterministic active `object_overview` MUST contain only:

- Object canonical name;
- aliases;
- Primary Class from the represented Version classification snapshot;
- Facet-less Summary Statements;
- content Facet key/name inventory, without those Facets' Statement bodies;
- known searchable Structured Attributes as canonical display text;
- deterministic Relation text.

It MUST NOT contain content-Facet Statement bodies, Evidence text, internal IDs, workflow/gap/unresolved/proposal/conflict-management metadata, or an LLM-generated synthetic summary.

Relation semantics remain part of the overview. If a canonical `relationships` content Facet exists, Relation semantics MAY also appear there under the Facet representation contract. R2 does not create an independent Relation representation kind.

### R2-SRH-04 — No arbitrary chunking or truncation

R2 MUST NOT repair oversized Object retrieval by fixed-token chunking, silent Statement dropping, prefix clipping, model-context truncation, or synthetic summarization that replaces canonical semantic boundaries.

Facet and Statement are the detailed semantic units. The Large-fixture engineering target is:

```text
object_overview <= 4096 tokens
```

without truncation. Exceeding this target requires design review.

### R2-SRH-05 — Hybrid Object Search remains bounded and Object-level

The active semantic channels are:

```text
semantic_object_overview
semantic_facet
semantic_statement
```

The accepted Phase I baseline remains the first R2 baseline:

```text
RRF k = 60
object_overview contribution cap = 1
facet contribution cap           = 2
statement contribution cap       = 3
knowledge lexical cap            = 3
```

Normal results remain `1 Object = 1 result`. Exact name/alias priority remains separate from fused semantic relevance.

Facet-scoped search MUST exclude `object_overview`; derivation/temporal conditions that are only valid at Statement granularity remain Statement-only. A broad Object representation MUST NOT silently satisfy a narrower semantic filter.

### R2-SRH-06 — Overall Object Similarity is hierarchical multi-vector

`find_similar_objects(..., facet=None)` MUST NOT define Object-wide similarity as one compact-overview cosine.

Overall similarity MUST combine, with bounded contribution and candidate work:

```text
overview <-> overview
same-Facet <-> same-Facet
bounded Statement-level evidence
```

The final Object-wide score is a derived aggregate:

```text
score_type = hierarchical_similarity
```

It MUST NOT be labeled raw cosine similarity, probability, truth, or confidence. The exact bounded formula/caps are selected and validated in R2-06, but any implementation MUST avoid unbounded all-Statement cross-products and Statement-count boost.

Facet-specific similarity remains same-Facet only and continues to return `cosine_similarity`; it MUST NOT silently fall back to overview/another Facet or treat missing Facet as zero similarity.

### R2-SRH-07 — Similarity explainability remains inspectable

Overall hierarchical Similarity MUST retain bounded contributing evidence sufficient to identify the compared overview/Facet/Statement memberships and their raw vector-pair scores. Existing Object-level public operations remain stable; callers are not required to know or send `object_overview`.

### R2-SRH-08 — Builder identity is content-contract identity

Keep `builder_key = sgokb-canonical-search`.

The active content-version policy is:

```text
object_overall  = historical builder_version 1
object_overview = builder_version 2
facet           = version 1 while content contract unchanged
statement       = version 1 while content contract unchanged
evidence        = version 1 / unaffected
```

Builder version MUST NOT be misused as whole-index generation identity. R2-03 defines a separate safe Derived Search generation/cutover identity.

### R2-SRH-09 — Canonical Knowledge and Embedding baseline stay unchanged

R2 changes derived representation/retrieval composition only. Canonical Object / Version / Facet / Statement / Attribute / Relation / Evidence / Provenance data are not rewritten.

The first R2 baseline retains Harrier OSS v1 0.6B / 1024-dim and does not concurrently introduce Harrier 270M, FlashAttention-2, a PyTorch/CUDA upgrade, CPU fallback, or truncation.

The complete R2-02 normative contract is `docs/planning/phases/N/N05/N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`.

---

## 1. 目的

本書は、SGOKBに保存されたObject KnowledgeとSource / Evidenceを、後から人間・CLI・MCP Client・LLM・UPDS等が検索・比較・取得するための論理要件を定義する。

B-05では、検索アルゴリズムそのものより先に次を固定する。

- 何を検索対象とするか。
- 通常検索で何を1件の結果として返すか。
- Lexical / Semantic / Hybrid Searchの責務境界。
- Object Similarity / Facet Similarityの意味。
- Relation Searchの意味。
- Evidence Searchの意味。
- Class / Facet / Version / temporal / Source metadata等のfilter semantics。
- current / historical Knowledgeを混在させない既定動作。
- conflict / gap / unresolved informationを通常Knowledge検索へどう扱うか。
- Ranking scoreをconfidenceやtruth scoreと混同しないこと。
- Search Indexを再生成可能な派生物とすること。
- 検索結果からKnowledge Version / Evidence / Sourceへ追跡できること。

本書は論理要件を定義する。最終FTS tokenizer、Embedding model、Vector Index、RRF等のfusion方式、score weight、reranker、SQL index、MCP Tool schemaはPhase I / Jで決定する。

---

## 2. 結論

SGOKBは検索を1種類の「全文検索」に縮約せず、少なくとも次を別の責務として扱う。

```text
Search / Retrieval
├─ Object Identity Lookup
├─ Object Lexical Search
├─ Object Semantic Search
├─ Hybrid Object Search
├─ Object Similarity Search
├─ Facet Similarity Search
├─ Relation Search / Traversal
├─ Evidence Lexical Search
├─ Evidence Semantic Search
└─ Audit / Historical Retrieval
```

標準的な自然言語Object検索では、**Hybrid Object Searchを基本経路**とする。

検索対象の正本は、MarkdownやGoogle Drive上のPackageではなく、Object Registry、accepted Object Knowledge Version、Relation、Evidence Store等の構造化データである。

通常のObject検索は、内部candidate generationでStatement等を利用しても、**結果単位を原則1 Objectに集約する。**

```text
query
 ↓
identity / lexical / semantic candidate generation
 ↓
Facet / Statement / Attribute / Relation matches
 ↓
Object単位へ集約
 ↓
1 Object = 1 search result
```

これにより、旧PrototypeのFragment検索のように、1 Objectが大量の細粒度hitで検索結果を占有する状態を標準動作にしない。

---

## 3. SearchとGetを分離する

### SRH-01 — 既知ID取得とSearchを区別する

既知の`object_id` / `evidence_id` / Version IDを指定して取得する操作は、Rankingを伴うSearchとは別責務とする。

例えばMCP / Applicationでは概念上次を分離できる。

```text
get_object(object_id)
search_objects(query)
find_similar_objects(object_id)
search_evidence(query)
```

既知ID取得でSemantic Searchを経由して対象を再同定しない。

### SRH-02 — Search CoreをCLI / MCPから独立させる

Search / Retrieval semanticsはCLI、MCP、GUI、Package Builder等のadapterごとに別実装しない。

同じApplication / Retrieval Coreを利用し、adapter差でrankingやfilter意味が変わらないことを基本とする。

---

## 4. 検索対象レイヤ

### SCOPE-01 — Object RegistryをIdentity検索対象とする

少なくとも次はObject Identity discoveryへ利用できる。

- `object_id`
- `name`
- `aliases`
- `primary_class`
- `additional_classes`
- ancestor Class
- Object lifecycle `status`

`current_version = null`のObjectでもname / alias / classによる発見は可能でなければならない。

Knowledge未生成ObjectをSemantic Knowledgeがないという理由で検索不能にしない。

### SCOPE-02 — accepted Object Knowledge Versionだけを通常Knowledge検索対象とする

ChatGPTから返却された未Import Result、Validation失敗Result、staging candidateを通常Knowledge検索へ混ぜない。

通常検索対象はValidation / Import済みのaccepted Object Knowledge Versionとする。

### SCOPE-03 — Object Knowledgeの主要検索対象を定義する

accepted Knowledge Version内の少なくとも次を検索可能とする。

- summary
- Facet content / Knowledge Statement
- textual structured attribute
- structured attributeのkey/value（型に応じたfilterを含む）
- Relation
- derivation metadata（明示filter用途）
- temporal scope（明示filter用途）

ただしすべてを同じFTS fieldや同じEmbeddingへ無差別に連結することは要求しない。

### SCOPE-04 — Knowledge Statementを既定のtop-level結果単位にしない

Knowledge Statementは、lexical match location、semantic candidate generation、snippet生成等に利用できる。

しかし通常Object検索ではStatementごとに独立hitを返さず、Objectへ集約する。

例:

```text
Object A
  personality Statement 1  match
  personality Statement 2  match
  values Statement 4       match

→ 通常結果では Object A = 1件
   matched_facets = [personality, values]
   matched_items = 上位数件
```

これによりStatementを旧Fragmentと同じ大量検索単位へ戻さない。

Statement単位の監査・詳細取得が必要な場合は、Object / Facet内のmatch detailまたは明示的な詳細retrievalとして提供できる。

### SCOPE-05 — Structured Attributeは型に応じて検索方法を分ける

文字列attributeはLexical / Semantic対象になり得る。

日付、数値、boolean、enum、identifier等は自然言語類似だけに依存せず、exact / range / set等のtyped filterを利用可能にする。

例えば次を表現できることを目指す。

```text
release_date >= 2020-01-01
language = ja
component_number between 1 and 10
```

具体的attribute query syntaxはPhase I / J / Mで決定する。

### SCOPE-06 — RelationはGraph構造とtext representationを分離する

Relationの正本はsubject / predicate / object等の構造化edgeである。

Relation labelやendpoint nameをLexical / Semantic candidate textへ利用することは許容するが、Graph traversalを自然言語検索だけに置き換えない。

### SCOPE-07 — Evidence Storeを独立検索対象として維持する

EvidenceはObject Knowledgeとは別に、監査・再分析・Package構築用途でLexical / Semantic Search可能でなければならない。

Evidence Search結果をaccepted Object Knowledgeと同じ意味の結果として混在表示しない。

---

## 5. Object Identity Lookup

### ID-01 — `object_id`完全一致を最優先する

利用者がstable `object_id`を指定した場合、文字列類似検索ではなく直接Lookupする。

### ID-02 — exact name / alias matchをSemantic matchより優先可能にする

Object名やaliasがqueryと正確に一致する場合、通常Object discoveryではSemantic similarityだけの候補より上位に扱えることを要件とする。

ただし同名Objectを許容しているため、exact name一致だけで1件へ自動決定しない。

### ID-03 — 表記正規化をIdentity mergeと混同しない

検索用にcase、Unicode、空白等のdeterministic normalizationを利用できる。

ただしnormalized string一致をObject merge判定には利用しない。

### ID-04 — 日本語短語・固有名詞を検索不能にしない

Prototypeのtrigram FTSは1〜2文字の日本語queryにliteral fallbackを必要としている。

現行要件では、利用するFTS tokenizerにかかわらず、短いObject名、略称、日本語語句、記号を含むalias等をIdentity / Lexical検索できなければならない。

具体的tokenizerはPhase Iで比較・決定する。

---

## 6. Object Lexical Search

### LEX-01 — Lexical Searchを必須とする

Embedding modelが利用不能でも、Object name / aliasと保存済みKnowledge textを文字列ベースで検索できなければならない。

### LEX-02 — Identity fieldとKnowledge fieldの一致を区別する

少なくとも次のmatch originを区別できることを要件とする。

- exact / normalized name match
- alias match
- summary match
- Facet / Statement match
- attribute match
- Relation label / endpoint match

検索結果では、なぜそのObjectがhitしたかを説明可能にする。

### LEX-03 — name / alias一致をKnowledge本文一致より優先可能にする

Object discoveryでは、同じqueryが本文中に偶然出現したObjectより、Object自身のname / aliasが一致するObjectを優先できるようにする。

具体的weightはPhase Iの評価で決定する。

### LEX-04 — Phrase / token / literal検索を表現可能にする

自然言語queryだけでなく、固有名称や引用語句を探す用途に対応する。

最終query syntaxは後続Phaseへ延期するが、完全一致をSemantic similarityだけへ変換しない。

### LEX-05 — scoreを真実性やconfidenceとして扱わない

BM25等のLexical scoreはquery relevanceのranking signalであり、Knowledgeの正しさ・Sourceの信頼性・AI confidenceを意味しない。

---

## 7. Object Semantic Search

### SEM-01 — Semantic Searchを必須とする

queryと文字列が一致しなくても意味的に関連するObject Knowledgeを取得できなければならない。

例:

```text
query: 「自分より仲間を優先する人物」

候補:
  personality / valuesで自己犠牲・他者優先を記述するCharacter
```

### SEM-02 — Object overall representationを持てること

Object全体の意味検索・Similarityのため、accepted current KnowledgeからObject-level semantic representationを生成できることを要件とする。

具体的にsummaryだけを使うか、複数Facetを統合するか、Relationsを含めるかはI-01で評価する。

> **R2-02 superseded:** active Object-level representation is now the compact `object_overview` defined in Section 0. It is not a whole-Knowledge concatenation and is not sufficient by itself to define detailed overall Similarity.

### SEM-03 — Facet representationを独立して持てること

Facet単位で意味検索・類似比較できるよう、少なくともFacetごとのsemantic representationを生成可能にする。

これにより、例えばCharacterについて次を区別できる。

```text
personality similarity
values similarity
motivation similarity
```

### SEM-04 — Knowledge Statement個別Embeddingを標準要件とする

accepted Object Knowledgeに含まれる**検索可能なKnowledge Statement**は、原則として個別Semantic Representationを生成可能とし、標準実装ではStatement-level Embeddingを生成する。

この変更は2026-10-11のEmbedding / Vector Search追加調査を反映したものである。Facet全体を1 Vectorへ集約すると、条件・例外・時間限定情報・少数派特徴等の細粒度Knowledgeが意味空間で薄まり、Semantic Searchから発見しにくくなる可能性があるためである。

Statement Embeddingは旧Fragment Pipelineを復活させるものではない。Knowledge Statementはaccepted Object Knowledge Version内ですでに構造化されたKnowledge単位であり、Search Representation / Embeddingはそこから決定論的に生成する派生Indexとする。

次の管理情報はObject自身の意味Knowledgeではないため、通常Statement Semantic Indexへ混ぜない。

- gap
- insufficient evidence
- unresolved reference
- Registry proposal

conflict中でもaccepted / grounded Statement自体は検索可能とし、conflict状態を結果detailで示せるようにする。

### SEM-05 — Embedding Spaceを混在させない

異なるmodel / revision / dimension / preprocessing / configurationのVectorを同じ空間として比較してはならない。

Prototypeの`EmbeddingSpace`分離思想を維持する。

Embedding Space変更時はIndexを再構築可能とする。

### SEM-06 — Semantic scoreを確率とみなさない

cosine similarity等のscoreはsemantic ranking signalであり、「同じ意味である確率」「正しい確率」ではない。

異なるEmbedding Space間のscoreを直接比較しない。

### SEM-07 — Semantic Indexの入力を正本Knowledgeと分離する

Embedding用text representationは再生成可能な派生物であり、Object Knowledgeの新しい正本にしない。

Embedding textを変更してもObject Knowledge Versionを書き換える必要がない設計とする。

### SEM-08 — Object / Facet / Statementのmulti-representation retrievalを採用する

Semantic Retrievalでは、用途の異なる次の表現を併用できることを要件とする。

```text
Object overall representation
  → Object全体の意味検索・Similarity

Facet representation
  → personality / values / themes等の観点別検索・Similarity

Statement representation
  → 細粒度Knowledge、条件、例外、時間限定情報の意味検索
```

> **R2-02 superseded:** the active family is `object_overview + facet + statement`. `object_overview` supplies broad Object context; detailed overall Similarity is hierarchical and also consumes bounded Facet/Statement evidence.

Statement Embeddingを導入してもObject / Facet Embeddingを廃止しない。細粒度検索と全体・観点別Similarityは別の検索目的だからである。

### SEM-09 — Statement Search Representationへ必要な文脈を付与可能にする

Statement単体が代名詞・省略・短文等で意味検索に不十分な場合、Embedding入力にはObject / Facet / temporal scope等の必要な文脈を決定論的に付加できるようにする。

Search Representationは正本Statementとは別の派生表現とし、representation builder version / content hashを追跡できるようにする。

同一Embedding Space + 同一representation contentである場合にVector reuseを可能にしてよいが、Knowledge Versionごとのmembership / current-historical scopeは別に保持しなければならない。

### SEM-10 — Vector backendを交換可能にする

SQLiteをcanonical Knowledge Storeとして維持し、Vector検索backendは再構築可能なDerived Search Indexとして扱う。

Phase Iでは`VectorIndexAdapter`相当の境界を定義し、SQLite拡張、embedded Vector DB、外部Vector service等をSGOKB Coreから交換可能にする。

Vector backend固有のID / schema / APIをObject Knowledge正本へ持ち込まない。

---

## 8. Hybrid Object Search

### HYB-01 — 通常free-text検索はHybridを基本とする

固有名詞・略称・Exact matchに強いLexical channelと、意味的関連に強いSemantic channelを組み合わせる。

```text
Query
 ├─ Identity / Lexical candidates
 └─ Semantic candidates
        ↓
Candidate fusion / reranking
        ↓
Object-level results
```

### HYB-02 — FusionアルゴリズムをB-05で固定しない

PrototypeにはRRF相当のrank fusionがあるが、B-05ではRRF / weighted score / rerankerのどれかを最終固定しない。

Phase Iでgold queryを用いて比較する。

### HYB-03 — raw scoreを異種channel間で単純加算しないことを基本とする

BM25 scoreとcosine similarityは意味・尺度が異なる。

融合する場合はrank fusion、normalization、学習済みreranker等、尺度差を考慮した方法を利用する。

### HYB-04 — filterを可能な限りcandidate generation前に適用する

Class、Object status、Version scope、Facet等のhard filterは、後から上位結果を削るだけでなくcandidate集合そのものを制限できることを要件とする。

これによりfilter対象が少数の場合のRecall低下を防ぐ。

### HYB-05 — exact identity matchをsemantic rankingで埋没させない

name / aliasの強い一致がある場合、それをSemantic channelだけの高score候補より優先可能にする。

ただし同名Objectはdisambiguation可能な複数候補として返す。

### HYB-06 — channel contributionを説明可能にする

結果について少なくとも論理上、次を返せるようにする。

- lexicalでhitしたか
- semanticでhitしたか
- exact name / alias matchか
- matched Facet
- matched attribute / Relation等

最終score breakdown形式はPhase I / Jで決定する。

---

## 9. Object Search結果単位

### HIT-01 — 通常Object Searchは1 Object = 1結果とする

複数Facet / Statementがmatchしても、通常search result listでは同じObjectを重複して大量表示しない。

Objectごとにmatch evidenceを集約する。

### HIT-02 — match detailを失わない

Objectへ集約しても、どの部分がqueryへ一致したかを確認可能にする。

少なくとも次を返せる設計とする。

- matched field / Facet
- representative snippet / value
- match channel
- Knowledge Version
- derivation kind（該当する場合）
- conflict flag（該当する場合）
- grounding Evidenceへ辿るための参照

### HIT-03 — snippetを新しい正本Knowledgeにしない

検索用highlight / excerpt / concatenated contextは派生表示であり、Knowledge Storeの正本ではない。

### HIT-04 — deterministic tie-breakを持つ

同score候補の順序が毎回不必要に変動しないよう、最終rankingにはstable ID等によるdeterministic tie-breakを設ける。

具体的方法はPhase Iで決定する。

### HIT-05 — rankとscoreの意味を明示する

返却scoreがLexical / Semantic / fused / rerankedのどれであるかを識別可能にする。

異なるsearch modeのscoreを同一の普遍尺度として扱わない。

---

## 10. Object Similarity Search

### SIM-01 — Object-to-Object Similarityを必須とする

既存Objectをqueryとして、意味的に近い別Objectを取得できなければならない。

主要利用例:

- Characterに似るCharacterを探す。
- Workに似るWorkを探す。
- Conceptに近いConceptを探す。

### SIM-02 — 既定candidate scopeは同じPrimary Classを基本とする

`find_similar_objects(object_id)`の既定動作では、対象Objectと同じPrimary Classをcandidate scopeとすることを基本とする。

理由:

- CharacterとWork等、表現構造が大きく異なるObject間の偶然のvector近接を抑える。
- 「似たCharacter」「似たWork」という主要利用目的に一致する。

ただし利用者が明示した場合は、Additional / ancestor Classやcross-class候補へscopeを拡張できる設計とする。

### SIM-03 — self matchを除外する

同一`object_id`の同一VersionをSimilarity resultとして返さない。

### SIM-04 — SimilarityをRelationとみなさない

Vector similarityは派生的な近さであり、`related_to`等の確定Semantic Relationを自動作成しない。

### SIM-05 — Similarity scoreを永続Knowledgeへ保存しないことを基本とする

Embedding model変更で値が変わり得るため、Similarity scoreはquery-time derived valueとする。

評価結果やcacheを保存する場合もObject Knowledge正本とは分離する。

### SIM-06 — historical target Versionを明示指定可能にする

既定ではcurrent VersionをSimilarity queryとして利用する。

過去Versionの意味表現を比較したい場合は、target Versionを明示できる設計とする。

### SIM-07 — overall Similarityはhierarchical multi-vectorとする

R2-02以降、Facetを指定しないObject-wide Similarityは単一Object representationのraw cosineではなく、overview / same-Facet / bounded Statement evidenceを組み合わせたbounded hierarchical aggregateとする。

最終scoreは`hierarchical_similarity`と識別し、component raw cosineと区別する。

### SIM-08 — hierarchical Similarityの根拠を追跡可能にする

overall resultは、最終scoreへ寄与したoverview / Facet / Statement pairをboundedな説明情報として追跡できなければならない。

---

## 11. Facet Similarity Search

### FSIM-01 — Facet単位Similarityを設計対象ではなく正式要件とする

SGOKBの主要利用目的に「性格は似るが価値観は違う」等の比較があるため、Facet-level similarityを正式要件とする。

### FSIM-02 — 同一Facet key比較を標準とする

例えば`personality`でqueryした場合、candidate側も`personality` representationを持つObjectを比較する。

別FacetやObject-wide representationへsilent fallbackしない。

### FSIM-03 — Facetが存在しないObjectを0 similarityとして扱わない

専用Facet未実装、not analyzed、not applicable、insufficient evidenceは意味が異なる。

Facet representationがない場合は「比較不能 / unavailable」とし、意味的に遠いObjectと同一視しない。

### FSIM-04 — cross-class Facet比較を許容可能にする

同じFacet semanticsを共有するClassであれば、明示的scope指定によりcross-class比較できる設計を許容する。

具体的Facet compatibilityはE-02 / I-01で定義する。

### FSIM-05 — matched facetを結果へ必ず示す

Similarity resultがoverallか特定Facetかを利用者が識別できなければならない。

---

## 12. Relation Search / Traversal

### RELSRH-01 — Relation Searchを構造化Queryとして提供する

少なくとも次でRelationを検索できることを要件とする。

- subject Object
- predicate / Relation Type
- object Object
- direction
- endpoint Class
- temporal scope（存在する場合）

### RELSRH-02 — 1-hop traversalを必須とする

例えば次を決定論的に取得できなければならない。

```text
Character A --appears_in--> ?
? --member_of--> Organization B
Work A --has_part--> ?
```

### RELSRH-03 — bounded multi-hop traversalを拡張可能にする

複数hop traversalは有用だが、無制限recursive traversalを標準にしない。

導入する場合はmax depth / Relation Type / direction等を明示して範囲を制限する。

初期MVPで何hopまで実装するかはPhase Jで決定する。

### RELSRH-04 — Classification edgeとSemantic Relationを混同しない

Class descendant filteringのための`subclass_of`相当処理と、Object Relation Searchを別契約とする。

### RELSRH-05 — current accepted Relationを既定対象とする

通常Relation Searchはcurrent accepted Object Knowledgeに属するRelationを対象とする。

historical Relationは明示Version scopeで検索する。

### RELSRH-06 — Relationからgroundingへ遡れること

AI生成Relation等について、Relation resultからEvidence Link / Evidence / Sourceへ追跡できるようにする。

---

## 13. Class / Facet Filter

### FLT-01 — Primary Class filterを必須とする

指定Primary ClassのObjectだけを検索可能にする。

### FLT-02 — Additional Class filterを必須とする

Additional Class membershipを利用して横断分類で検索できるようにする。

例:

```text
Additional Class = FictionalEntity
```

### FLT-03 — ancestor Classによるdescendant-inclusive filterを可能にする

例えば`Agent`を指定してCharacter / Person / Organization等を検索対象にできることを要件とする。

ただし「exact Class」と「descendant-inclusive Class」を区別可能にし、暗黙にどちらかへ固定しない。

### FLT-04 — Facet filterを必須とする

queryを特定Facetへ限定できるようにする。

例えばCharacter全体ではなく`values`だけをSemantic Searchできる。

### FLT-05 — 専用検索機能の未実装を理由にClassを検索不能にしない

B-02Dで初期Class RegistryへseedされたClassは、専用Facet / UIが未実装でも、少なくともIdentity検索と共通Knowledge contractによる検索対象にならなければならない。

---

## 14. Object lifecycle filter

### LIFE-01 — active Objectを通常検索の既定対象とする

通常利用では`active` Objectを返す。

### LIFE-02 — archived Objectは明示指定で検索可能にする

Archiveは削除ではないため、監査・履歴・再利用目的で明示的に検索できる。

### LIFE-03 — archived Objectを通常Similarity候補へ混ぜない

明示指定がない限り、archived ObjectをSimilarity / recommendation的結果へ含めない。

---

## 15. Knowledge Version scope

### VERSEARCH-01 — current Versionを通常検索の既定とする

Objectが複数Knowledge Versionを持っても、通常Object Searchでは`current_version`だけを対象とする。

同じObjectのv1 / v2 / v3を通常結果に重複表示しない。

### VERSEARCH-02 — historical Versionを明示scopeで検索可能にする

監査・比較・過去状態調査のため、過去accepted Versionを明示的に検索できることを要件とする。

historical searchでは結果を`object_id + version_id`で識別できるようにする。

### VERSEARCH-03 — currentとhistoricalをsilent混合しない

検索resultやsemantic representationを作る際、異なるKnowledge VersionのStatementを1つのcurrent Object表現へ無断混合しない。

### VERSEARCH-04 — Version作成時刻とKnowledge temporal scopeを分離する

次の2種類を別filterとして扱えるようにする。

```text
Version history:
  どのKnowledge Versionを検索するか

Knowledge valid time:
  Statement / attribute / Relationがいつ成立する内容か
```

例えば「2024年時点のSoftware仕様」を検索する際、2026年に作成されたVersion内の`valid_at=2024` Knowledgeもあり得る。

`as_of`等の曖昧な単一fieldへ両概念を混在させない。

### VERSEARCH-05 — current_versionなしObjectの扱いを明示する

Knowledge text検索やSimilarityでは対象Knowledgeがないため通常candidateにはならないが、Identity検索では発見可能とする。

---

## 16. Derivation / Conflict / Gapの検索扱い

### EPISEARCH-01 — derivation kindをfilter可能にする

必要に応じて次を区別して検索できることを要件とする。

- direct statement
- synthesis
- interpretation
- reported view

### EPISEARCH-02 — reported viewのattributionを失わない

`reported_view`が検索hitした場合、その評価をObject自身の客観属性のように表示しない。

検索結果detailでattributionへ追跡できるようにする。

### EPISEARCH-03 — conflict中のgrounded Statementは通常検索可能とする

conflictがあるからといって、両方のEvidence-grounded Statementを通常Knowledgeから削除しない。

ただし検索結果でconflict状態を表示可能にする。

### EPISEARCH-04 — conflict record自体を通常semantic contentへ混ぜない

「AとBが矛盾している」という管理recordを、Objectの通常semantic representationへ無条件に埋め込まない。

監査filter / audit retrievalで検索できるようにする。

### EPISEARCH-05 — gap / insufficient evidence / unresolved reference / Registry proposalを通常Knowledge検索から除外する

これらは確定Knowledge assertionではないため、通常Lexical / Semantic / Similarity Indexへ混ぜない。

ただし管理・監査目的では明示的に検索・一覧可能にする。

これにより「情報がない」という記録がObjectの性質としてSemantic similarityへ影響することを防ぐ。

---

## 17. Evidence Search

### ESEARCH-01 — Evidence Lexical Searchを必須とする

Evidence contentを文字列で検索できなければならない。

### ESEARCH-02 — Evidence Semantic Searchを必須とする

Object Knowledge生成前でも、意味的に関連するEvidenceを検索できなければならない。

これはObject Evidence Package構築の主要入力となる。

### ESEARCH-03 — Evidence検索結果は1 Evidenceを基本単位とする

Object Searchとは異なり、Evidence Searchでは具体的な根拠位置を探すため`evidence_id`単位のhitを返せる。

ただしoverlap chunkや同一Source内近接EvidenceをUI / Package selection時にgroup / collapseできることを許容する。

Store上のEvidenceを破壊的dedupしない。

### ESEARCH-04 — Evidence resultはProvenanceを返せること

少なくとも次へ追跡できるようにする。

- evidence_id
- content / excerpt
- Source ID
- Snapshot ID
- Normalized Run
- Source内location
- extraction mode
- Source locator / title等の表示情報

### ESEARCH-05 — Source分類filterを利用可能にする

B-03で定義した軸の少なくとも次をfilter対象にできることを要件とする。

- resource type
- media type
- document genre
- publisher kind
- site / provider
- page purpose
- language

### ESEARCH-06 — Source↔Object association metadataをfilter可能にする

特定Object向けEvidence Retrievalでは、少なくとも次を利用可能にする。

- associated Object
- candidate / confirmed / excluded
- subject relationship

`excluded` associationは、そのObject向け自動Package candidateへ通常含めない。

candidate / confirmedの既定利用方針はF-03 / F-05で決定する。

### ESEARCH-07 — 時刻filterを区別する

Source / Evidence Searchでは少なくとも次を混同しない。

- Source published time
- Source updated time
- Snapshot captured time
- SGOKB import time
- Evidence generation time

### ESEARCH-08 — active / effective Evidence generationを通常既定とする

通常Evidence Search / Package Retrievalでは、Phase Fで選択されたactive / effective Snapshot / Normalized Run世代を既定対象とする。

Extractor再処理で旧Evidenceが残っていても、通常結果へ全世代を重複表示しない。

### ESEARCH-09 — historical Evidenceを明示検索可能にする

過去Snapshot / Normalized Run / Evidence generationを監査・比較のため検索できることを要件とする。

historical hitではgeneration / Snapshotを明示する。

### ESEARCH-10 — Provenance integrity状態をfilter可能にする

Provenance chain破損、Raw欠落、checksum不一致等を通常Evidenceと同一扱いにしない。

通常Knowledge生成用retrievalではintegrity正常なEvidenceを基本とし、破損Evidenceは監査用途で明示検索できるようにする。

### ESEARCH-11 — Source件数をtruth scoreとして扱わない

同じ記述を多数Sourceが含むことだけを理由に真実性scoreへ変換しない。

mirror / syndicated / derived Sourceが存在し得るためである。

検索rankingとtruth judgementを分離する。

---

## 18. Evidence Package Retrievalとの境界

### PKGSEARCH-01 — Search結果とPackage selectionを分離する

Evidence Searchが上位K件を返したからといって、そのままK件をPackageへ採用するとは限らない。

Package BuilderはF-03 / F-04で次を追加考慮できる。

- explicit Object association
- Source diversity
- Source independence metadata
- duplicate / near-duplicate suppression
- token / size budget
- current Knowledge carry-forward evidence
- manual include / exclude

### PKGSEARCH-02 — Evidence selection reasonを追跡できること

Packageへ採用されたEvidenceについて、少なくとも次のselection channelを追跡可能にする。

- explicit association
- name / alias match
- lexical retrieval
- semantic retrieval
- Relation / metadata由来
- manual include

Search rankingだけをselection理由の全てにしない。

---

## 19. Search filter semantics

### FILTER-01 — filterとboostを区別する

「Characterだけ」のようなfilterはcandidateを除外するhard conditionであり、「Characterをやや優先する」というboostとは別概念とする。

API / UIで意味を混同しない。

### FILTER-02 — 複数filterの組合せを可能にする

例:

```text
primary_class = Work
ancestor_class = CreativeWork
facet = themes
knowledge_valid_at = 2025-01-01
status = active
```

具体的AND / OR query syntaxは後続Phaseで決定する。

### FILTER-03 — filter適用後0件を別Classへのfallbackで埋めない

「Placeだけ」を指定して0件なら、WorkやConceptを自動的に返さない。

Classification fallback禁止方針を検索にも維持する。

### FILTER-04 — unknown filter valueをsilent無視しない

存在しないClass、Facet、Relation Type等をfilterへ指定した場合、無視して全件検索するのではなくvalidation errorまたは明示的empty semanticsとする。

最終API仕様はPhase J / Mで決定する。

---

## 20. Search result explainability / provenance

### EXP-01 — 検索結果理由を説明可能にする

Object Search結果は少なくとも次の一部を返せるようにする。

- rank
- search mode
- match channel
- matched name / alias / Facet / attribute / Relation
- matched Knowledge Version
- representative snippet
- matched facet
- score / score type

### EXP-02 — Knowledge hitからEvidenceへ遡れること

検索hitしたStatement / attribute / RelationがEvidence groundingを持つ場合、検索結果または詳細取得を通してEvidence IDへ到達できなければならない。

さらにEvidenceからSource / Snapshot / Rawまで追跡可能なB-03契約を維持する。

### EXP-03 — query-time scoreをKnowledgeへ書き戻さない

relevance score、similarity score、reranker score等をObject Knowledgeのconfidenceとして保存しない。

### EXP-04 — scoreなしのdeterministic結果を許容する

Object ID lookupやRelation traversal等、ranking不要な取得を無理に0〜1 scoreへ変換しない。

---

## 21. Search Index lifecycle

### IDX-01 — Search Indexを派生物とする

FTS table、Vector Index、reranker cache等はObject Knowledge / Evidenceの正本ではない。

正本DBから再構築可能でなければならない。

### IDX-02 — accepted Version promotion後にcurrent indexを更新する

未Validation Resultをcurrent Search Indexへ投入しない。

新Versionがaccepted / currentへ昇格した後にcurrent検索用indexを更新する。

### IDX-03 — 過去Versionを失わない

current index更新のために、過去Object Knowledge Version自体を削除してはならない。

historical searchを実現するためのindex方式はPhase Iで決定する。

### IDX-04 — content/version mismatchを検出可能にする

VectorがどのObject Version / Facet / Evidence generationから作られたか追跡できなければならない。

古いVectorを新KnowledgeのVectorとしてsilent利用しない。

### IDX-05 — Embedding model metadataを保存する

少なくとも次をIndex metadataとして識別できるようにする。

- model
- revision
- dimension
- preprocessing / configuration
- representation version

### IDX-06 — Embedding model変更時に再構築可能にする

新modelへ切り替えてもObject / Evidence identityを変更せず、新しいEmbedding Spaceを構築できることを要件とする。

### IDX-07 — Lexical Indexも再構築可能にする

tokenizerやFTS設定変更をKnowledge migrationと同一視しない。

---

## 22. Ranking原則

### RANK-01 — Relevance rankingとKnowledge qualityを分離する

rankingは「queryにどれだけ関連するか」を主目的とし、Knowledgeが客観的に真かどうかをscore化するものではない。

### RANK-02 — Source trust単一scoreをranking正本にしない

B-03で禁止したglobal trust scoreを、Search rankingの絶対尺度として再導入しない。

Publisher / genre等を将来ranking featureへ利用する場合も、用途別評価を行う。

### RANK-03 — Evidence数だけでObject rankingを決めない

Evidenceが多いObjectを単純に高品質・高関連とみなさない。

有名Objectや重複Sourceが不当に有利になるためである。

### RANK-04 — exact identity relevanceとsemantic relevanceを両立する

固有名詞queryで正しいObjectを上位へ出しつつ、概念queryでは意味的なObjectを取得できることを評価する。

### RANK-05 — rerankerを必須依存にしない

初期MVPはLexical + Semantic + fusionだけで成立可能にする。

rerankerはI-06で品質改善が確認された場合に追加する。

---

## 23. Pagination / result size

### PAGE-01 — result limitを指定可能にする

無制限全件返却を通常APIの既定にしない。

### PAGE-02 — 大量結果をページング可能にする

Object / Evidence / Relationの件数増加に対応できるよう、offsetまたはcursor等でページングできる設計を目指す。

具体方式はPhase J / Mで決定する。

### PAGE-03 — page間の順序安定性を考慮する

同一Index state / query / filter条件では、同rank候補の順序が無作為に変わらないことを目指す。

---

## 24. Multilingual / language要件

### LANG-01 — 日本語を第一級利用言語として扱う

日本語Object名、alias、Knowledge、Evidence、queryをLexical / Semantic Searchできることを必須とする。

### LANG-02 — 多言語Knowledgeを扱えること

Object Knowledge languageとEvidence original languageをB-04 / B-03契約どおり区別し、language filterを利用可能にする。

### LANG-03 — cross-lingual Semantic Searchを評価対象とする

日本語queryで英語Knowledge / Evidence、またはその逆を意味検索できる多言語EmbeddingをPhase Iで評価する。

ただし具体的Embedding modelはB-05では固定しない。

### LANG-04 — 翻訳Artifactを原Evidenceと混同しない

検索支援用翻訳があっても、Evidence Search resultは原Evidence provenanceを維持する。

---

## 25. Temporal Search

### TIME-01 — temporal scopeをfilter可能にする

B-04で定義したStatement / attribute / Relationのvalid timeを検索条件へ利用可能にする。

### TIME-02 — unknown temporal scopeを誤って除外しない選択肢を持つ

時間情報のないKnowledgeを、`valid_at` queryでどう扱うかは明示policyにする。

silentに「現在有効」と推定しない。

### TIME-03 — Continuity / Timelineを単なる日付filterにしない

作品内continuityやTimeline Objectはcalendar dateとは異なるため、Object Relation / explicit temporal metadataとして扱えるようにする。

---

## 26. Derived / Administrative dataの扱い

### ADM-01 — unresolved referenceを一般Object Searchへ混ぜない

未登録候補名が通常Objectのようにhitしないようにする。

### ADM-02 — Registry proposalを一般Knowledge検索へ混ぜない

提案されたalias / Class変更等は採用前に正本Identity検索を変更しない。

### ADM-03 — 管理情報を明示検索できること

運用上必要なら、次をadmin / audit retrievalとして一覧・filterできるようにする。

- unresolved references
- registry proposals
- conflicts
- gaps
- insufficient evidence
- stale / failed indexes
- provenance integrity problems

これらを通常semantic Object rankingへ混ぜない。

---

## 27. Existing Prototype Searchから維持する事項

次の思想は再利用価値が高いため維持する。

- SQLite FTS系のLexical Search基盤。
- Embedding provider abstraction。
- Embedding Spaceをmodel / revision / dimension / configurationで分離すること。
- Lexical / Semanticのcandidateを分けて取得する構造。
- filterをcandidate取得前に適用する思想。
- cosine等のVector similarityをadapterで交換可能にすること。
- fusion / rerankerを交換可能にすること。
- EvidenceをLexical / Semantic Search対象として維持すること。

ただし実装そのものをそのまま現行仕様とみなさない。

---

## 28. Existing Prototype Searchから変更する事項

### 28.1 Search target

旧:

```text
search_items
├─ evidence
└─ fragment
```

新:

```text
Object Search
├─ Object Identity
├─ current accepted Object Knowledge
│  ├─ summary
│  ├─ Facet
│  ├─ attributes
│  └─ Relations
└─ Object / Facet semantic representation

Evidence Search
└─ Evidence Store
```

Fragmentは標準検索対象の中心から外す。

### 28.2 Search result granularity

旧PrototypeではFragmentがtop-level hitになり得た。

新Object SearchではStatement等のmatchをObjectへ集約し、1 Object = 1通常結果とする。

### 28.3 Filter vocabulary

旧`entity / source / snapshot / site / source_type / facet`中心filterを、次へ再設計する。

```text
Object side:
- object_id
- active / archived
- primary / additional / ancestor Class
- facet
- version scope
- derivation kind
- typed attributes
- temporal scope
- Relation constraints

Evidence side:
- Source / Snapshot / Normalized generation
- resource / media / genre / publisher / provider / purpose
- Object association / subject relationship
- publication / capture / import times
- language / extraction mode
- active/effective / historical generation
- provenance integrity
```

### 28.4 Hybrid search

PrototypeのRRF + literal bonusは有用なbaselineだが、最終ranking契約ではない。

Phase Iのgold評価でfusion / rerankingを決定する。

---

## 29. Phase I / J / Nへの引き継ぎ

### I-01 Embedding対象

Historical Phase-I baseline:

- Object overall representation
- Facet representation
- Knowledge Statement representation
- Evidence representation
- 必要ならRelation text representation

R2-02 active amendment:

- `object_overall` is legacy-only;
- active Object-level representation is compact `object_overview`;
- Facet / Statement / Evidence remain first-class under the contracts above;
- Relation stays in `object_overview` and may also participate in a canonical relationships Facet; no independent Relation kind is introduced by R2.

Statement Search Representationには必要に応じObject / Facet / temporal contextを決定論的に付加し、representation builder version / content hashを追跡する。

### I-02 Embedding Model

- 日本語性能。
- multilingual / cross-lingual性能。
- model / revision / dimension / preprocessing分離。

### I-03 Vector storage / backend

- IndexはSQLite canonical Knowledgeから再構築可能な派生物とする。
- Embedding Space isolationを維持する。
- `VectorIndexAdapter`相当の交換境界を設ける。
- SQLite系Float32 Exact / FlatをANN Recall基準として用意する。
- sqlite-vec、sqlite-vector系、LanceDB ANN、Qdrant HNSW + groupingを同一gold / workloadで比較する。
- backendはPhase Iの品質・速度・容量・運用実測前に固定しない。

### I-04 Hybrid Search

- exact name / alias優先。
- lexical + Object / Facet / Statement semantic candidate fusion。
- hard filter pre-application。
- Statement-level hitを通常結果へ直接並べず、`object_id`単位へ集約するObject Aggregatorを設ける。
- 同一ObjectのStatement数を単純合計して無制限にboostしない。best hit / top-N capped contribution / Facet diversity等をgoldで比較する。
- Object-level resultは代表Statement / matched Facet / channel / Version / groundingをdetailとして保持する。
- explainable match channels。
- R2 active Object semantic channel is `semantic_object_overview` rather than `semantic_object_overall`.

### I-05 Similarity

- overall similarity。
- same-primary-class default candidate scope。
- explicit cross-class scope。
- facet-specific similarity。
- missing facetを0 similarity扱いしない。
- R2 overall mode is hierarchical multi-vector and returns `hierarchical_similarity`; Facet mode remains direct same-Facet cosine.

### I-06 Reranker

- MVP必須ではない。
- gold evaluationで導入判断。

### I-07 Search quality gold

Character / Work / Conceptだけでなく、初期Class Registryの広さを反映し、少なくともPerson / Organization / Series / Place / Eventと、Later support Classから複数を含むqueryを用意する。

評価観点:

- exact object lookup accuracy
- Statement Recall@K
- Object Recall@K
- Exact baselineに対するANN Recall@K
- MRR
- nDCG
- class / facet filter correctness
- current / historical isolation
- Evidence retrieval recall
- similarity human judgment
- cross-lingual retrieval

### J-01 / J-02 MCP

MCPはSearch Coreのadapterとし、少なくとも次の論理機能を公開可能にする。

- search objects
- semantic / hybrid object search
- find similar objects
- facet similarity
- relation retrieval
- evidence search
- get by stable ID

Tool名・response schemaはPhase Jで確定する。

### N-06 Retrieval品質評価

単一aggregate scoreだけで採用判断せず、Lexical / Semantic / Hybrid / Similarity / Evidence Searchを別々に評価する。Statement Embeddingあり / なしのfine-grained Recall差と、Exact baselineに対するANN Statement / Object Recallも評価する。

R2後のN-06 inputは、active `object_overview + facet + statement` generationとhierarchical overall Similarityを前提に再評価する。

---

## 30. B-06 / B-07への引き継ぎ

### B-06

- 人間向け通常検索とPackage Builder用Evidence Retrievalの用途を分離する。
- manual include / exclude等の人間介入点を定義する。
- 外部AIへ送る検索結果 / Evidenceについてexport permissionを適用する。

### B-07

- FTS / Vector Indexが破損・欠落しても正本Knowledge / Evidenceを失わないこと。
- Index rebuild可能性。
- offlineで最低限Lexical / ID / Relation retrievalを継続できる要件の具体化。
- Search response time / index size / rebuild time等の性能要件。
- Embedding provider障害時のgraceful degradation。

---

## 31. B-05で意図的に決めない事項

次は後続Taskへ延期する。

- FTS tokenizer / stemming / morphological analyzerの最終選択。
- BM25 parameter。
- exact match bonusの数値。
- Lexical / Semantic fusion formula。
- RRFの`k`。
- reranker model / algorithm。
- Embedding model。
- Object overall representationの具体的text builder。
- Facet representationの具体的text builder。
- Statement Search Representationへ付与するcontextの具体構成。
- Vector Index library / ANN parameter。
- sqlite-vec / sqlite-vector / LanceDB / Qdrant等の最終backend採否。
- Statement → Object aggregation score式。
- representation hash / Vector reuseの具体的physical schema。
- score threshold。
- top-k default値。
- pagination実装方式。
- query DSL / CLI syntax。
- MCP Tool名 / argument schema。
- Source metadata ranking weight。
- bounded multi-hop Relation traversalの最大depth。
- historical semantic indexの具体的保存方式。

> **R2-02 superseding note:** Object-level representation semantics, R2 Hybrid baseline channel/caps, and overall hierarchical Similarity score semantics are no longer unresolved. They are frozen by Section 0 and `N05D04R2_REQUIREMENTS_REPRESENTATION_CONTRACT.md`. R2-06 still selects the bounded numerical overall-Similarity algorithm within that contract.

これらは本書のscope / semantics要件を壊さない形でPhase I / J / Mで具体化する。

---

## 32. 完了条件への対応

### Lexical Search

Object Identity / current accepted KnowledgeとEvidenceについてLexical Searchを必須とした。

### Semantic Search

R2 active Object overview / Facet / accepted検索可能Knowledge StatementとEvidenceについてSemantic Searchを必須とした。

### Object Similarity

Object-to-Object similarityを必須とし、同Primary Classを既定scope、cross-classを明示拡張とした。R2 overall modeはbounded hierarchical multi-vector、Facet modeはsame-Facet direct cosineとする。

### Facet Similarity

Facet単位Similarityを正式要件とし、missing FacetをObject-wide representationへsilent fallbackしないことを定義した。

### Relation Search

構造化Relationの1-hop検索を必須とし、bounded multi-hopを拡張可能にした。

### Evidence Search

Lexical / Semantic、Source metadata、Object association、active/effective / historical generation、Provenance filterを定義した。

### Search result granularity

Knowledge Statementを標準のsemantic match単位として個別Embeddingしつつ、通常Object SearchはStatement-level hitをObject単位へ集約して1 Object = 1結果とすると確定した。

### current / historical

current accepted Versionを通常既定とし、historicalを明示scopeへ分離した。Knowledge Version時刻とKnowledge temporal scopeも分離した。

### conflict / gap

conflict中のgrounded Knowledgeは検索可能だがflagを保持し、gap / unresolved / proposal等の管理情報は通常Semantic Searchから分離した。

### Index lifecycle

FTS / Vector等を再構築可能な派生物とし、Embedding Space分離・Search Representation builder version / hash・Knowledge Version membership・Vector backend交換可能性を要件化した。R2ではbuilder content-versionとDerived Search generation/cutover identityも分離する。

---

## 33. 結論

SGOKBの通常検索では、**Objectを発見・取得する検索と、Source-grounded Evidenceを監査・再分析する検索を分離し、Object KnowledgeについてはLexical + SemanticのHybrid Retrievalを基本とする。**

通常Object Searchは、active `object_overview` / Facet / Statementのmulti-representationをSemantic candidate generationへ利用し、accepted検索可能Statementには標準で個別Embeddingを生成する。一方、最終結果は原則`1 Object = 1件`へ集約し、matched Statement / Facetをdetailとして保持する。

Object-wide SimilarityはR2以降、compact overviewだけのcosineではなく、overview + same-Facet + bounded Statement evidenceからなるhierarchical multi-vector operationとする。Facet Similarityはsame-Facet direct cosineを維持する。Relationは構造化Graph検索、Evidenceは独立したLexical / Semantic Searchとして扱う。

通常検索はactive Object + current accepted Knowledge + active/effective Evidence generationを既定scopeとし、archived / historical / conflict audit / gap / unresolved等は明示的scopeへ分離する。

検索scoreはrelevance / similarityの派生値であり、truth、confidence、Source trustを意味しない。Search Indexは正本ではなく、Object Knowledge / Evidenceから再生成可能な派生資産とする。

B-05は完了済みであり、その後のN05D-04R2 / R2-02が、N-05実測で得た新しい資源制約 evidence に基づいてObject-level derived representation / overall Similarity contractを上書きした。

**Status: Complete / R2-02 hierarchical multi-vector amendment accepted (2026-10-23)**
