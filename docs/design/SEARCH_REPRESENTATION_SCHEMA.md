# Search Representation Schema Design

更新日: 2026-10-13  
対象: Phase I / I-01 `Search Representation / Embedding対象`

## 1. 目的

Search Representationは、accepted canonical Knowledge / canonical Evidenceを検索・Embedding向けの決定論的な文字列表現へ変換した**再構築可能な派生物**である。

```text
canonical SQLite data
  ↓ deterministic builder
Search Representation
  ↓ I-02 Embedding Provider
Embedding
  ↓ I-03 VectorIndexAdapter
Vector Index
```

Search Representation、Embedding、Vector Indexはいずれもcanonical Knowledgeではない。生成失敗・削除・再構築によってaccepted Object Knowledge Versionを変更またはrollbackしてはならない。

## 2. Representation kind

I-01では次の4種類を確定する。

| kind | 意味 | canonical membership |
|---|---|---|
| `object_overall` | Object Version全体の意味表現 | Object + Version |
| `facet` | 1 Facetの意味表現 | Object + Version + Facet |
| `statement` | 1 accepted Knowledge Statementの意味表現 | Object + Version + optional Facet + Statement |
| `evidence` | 1 canonical Evidenceの意味表現 | Evidence + Source + Snapshot + Normalization Run |

旧`object` kindはdomain API上のみ`object_overall`の互換aliasとして残す。永続値は`object_overall`で統一する。

### Relation

I-01では独立した`relation` representation kindを作らない。

RelationはObjectの意味構造の一部として`object_overall`へ統合する。`relationships` Facetが存在する場合はFacet表現にもRelation textを含められる。I-07のgoldでRelation単独retrievalに不足が確認された場合のみ、将来独立kindを再評価する。

## 3. Content identityとMembership identity

同じ意味表現を複数Versionから再利用できるよう、content identityとmembership identityを分離する。

### 3.1 Content identity

`search_representations`:

```text
id
kind
builder_key
builder_version
content
content_hash = SHA-256(UTF-8 content)
created_at
```

一意性:

```text
(kind, builder_key, builder_version, content_hash)
```

同一builder contractで同一contentになった場合、異なるObject Versionでも同じSearch Representationを再利用できる。

Embedding Space identityはI-02で定義する。I-01ではSearch Representation IDを、将来の`representation_id × embedding_space_id` reuse境界として扱う。

### 3.2 Knowledge membership

`knowledge_search_representation_memberships`は次を保持する。

```text
representation_id
object_id
version_id
target_kind
facet_id?
statement_id?
```

contentが同一でも、Version membershipは統合しない。

例:

```text
Version 1 ─┐
           ├─ same Search Representation
Version 2 ─┘
```

Vector再利用は可能だが、Version 1がhistoricalでVersion 2がcurrentである事実はmembership側で保持される。

### 3.3 Evidence membership

EvidenceはObject Knowledgeと別membership familyとする。

`evidence_search_representation_memberships`:

```text
representation_id
evidence_id
source_id
snapshot_id
run_id
```

`source_id / snapshot_id / run_id`はembedding textへstable IDとして注入せず、filter / provenance / generation identityとして保持する。

## 4. current / historical scope

通常Object Searchの既定scope:

```text
Object.status = active
AND Version.state = accepted
AND Object.current_version_id = membership.version_id
```

Historical Search:

```text
Version.state = accepted
AND explicit version scope
```

同じrepresentation/vectorがold/new Versionで共有されても、old membershipをcurrentとして扱ってはならない。

低レベルmembership persistenceは再構築・staging互換性のためVersion所属を検証する。正式なBuilderはaccepted Versionだけを入力として受理し、通常retrieval APIもaccepted/current条件を適用する。

## 5. Deterministic Search Representation Builder

BuilderはLLMを使用しない。入力canonical dataが同一なら、同じ`builder_version`でbyte-identical UTF-8 contentを生成する。

共通規則:

- UnicodeをNFCへ正規化する。
- 連続whitespaceを単一spaceへ正規化する。
- field順序を固定する。
- DB rowidやUUID等のstable IDをsemantic textへ入れない。
- 順序を持たない集合は明示的にsortする。
- builder contract変更時は`builder_version`を更新する。

現行builder:

```text
builder_key     = sgokb-canonical-search
builder_version = 1
```

## 6. Statement representation

Statementは単独textだけでは主語・Facet・時点を失いやすいため、次の順序でsemantic contextを付与する。

```text
Object: <canonical name>
Primary Class: <class key> (<class display name>)
Facet: <facet name> (<facet key>)        # Facet所属時のみ
Temporal Scope: <normalized scope>       # 存在時のみ
Derivation: <derivation kind>            # direct_statement以外
Statement: <statement text>
```

例:

```text
Object: 架空太郎
Primary Class: character (Character)
Facet: Personality (personality)
Temporal Scope: 2026 arc; as_of=2026-01-01
Derivation: interpretation
Statement: 仲間を優先する。
```

Version ID、Statement ID、Facet IDは意味contextではないためcontentへ入れない。

## 7. Facet representation

Facet representationは`object_version_facets.status = content`だけを対象とする。

```text
Object
Primary Class
Facet
Statements (deterministic order)
```

次は通常Semantic representationを生成しない。

- `insufficient_evidence`
- `not_applicable`
- `not_analyzed`

Facet statementは`local_key, id`の固定順で並べる。

## 8. Object overall representation

`object_overall`は新しいsummaryをLLM生成せず、canonical Knowledgeを決定論的に組み立てる。

現行v1の順序:

1. Object canonical name
2. aliases
3. Version classification snapshotのPrimary Class
4. FacetなしSummary Statement
5. `content` FacetごとのStatement
6. known structured Attribute
7. Relation text

Relationは次の形でObject overallへ統合する。

```text
<subject name> <relation display name> <target name>
```

これにより独立Relation embeddingを持たなくてもObject similarityへRelation semanticsを反映できる。

## 9. Evidence representation

EvidenceはObject-result scopeへ混ぜず、独立index familyとして扱う。

semantic textには、検索意味として有効なものだけを含める。

```text
Source label          # 存在時
Snapshot title        # 存在時
Language              # 存在時
Source classification # resource/site/genre等、存在時
Evidence content
```

次のgeneration/provenance情報はmembership/canonical joinで保持し、embedding textへIDとして入れない。

- `evidence_id`
- `source_id`
- `snapshot_id`
- `run_id`
- locator / provenance identity
- extractor version等の技術的管理情報

これによりEvidence generationを失わず、semantic embeddingへの管理ノイズを抑える。

## 10. 通常Semantic Indexから除外する情報

次は検索対象Knowledge Statementではなく、review / workflow / uncertainty metadataであるため通常Statement Semantic Indexへ入れない。

- gap
- insufficient evidence Facet
- unresolved reference
- Registry proposal
- conflict record metadataそのもの

これらは`object_version_result_metadata`等の別canonical recordとして保持される。Builderは`knowledge_statements`と`content` FacetのみからStatement/Facet contentを構築し、これらmetadata tableをsemantic textへ展開しない。

一方、Conflictに関与していてもaccepted Version内に存在するgrounded `knowledge_statements`自体は検索可能である。

## 11. Reuse rule

Search Representation reuse条件:

```text
same kind
AND same builder_key
AND same builder_version
AND same SHA-256(content)
```

reuseしてよいもの:

- Search Representation content record
- I-02以降の同一Embedding Space内Vector

reuseしてはいけないもの:

- Version membership
- current/historical判定
- Evidence generation identity
- filter scope

## 12. Failure domain / rebuild

Search派生層:

```text
Search Representation
Embedding
Vector Index
```

はSQLite canonical Knowledge/Evidenceからfull rebuild可能である。

失敗時:

- accepted Versionをrollbackしない。
- canonical Statement/Evidenceを削除しない。
- external providerへsilent fallbackしない。
- stale/failed derived stateをready扱いしない。

Object側は既存`object_derived_states`の

```text
search_representation
embedding
vector_index
```

で`pending / ready / failed / stale` lifecycleを管理する。

## 13. I-01実装

- `src/sgokb/migrations/014_search_representations.sql`
  - E-02由来のderived search tablesのみrebuild。
  - canonical Knowledge/Evidence schemaは変更しない。
  - Knowledge/Evidence membershipを分離。
- `src/sgokb/domain/knowledge.py`
  - 4 representation kindsをdomain contract化。
- `src/sgokb/storage/semantic_repository.py`
  - content dedup、Knowledge membership、Evidence membership API。
  - accepted/current retrieval boundary。
- `src/sgokb/retrieval/search_representation.py`
  - deterministic builder。
  - Object / Facet / Statement / Evidence materialization。
- `tests/test_search_representation.py`
  - deterministic output、4 kinds、membership reuse、current/historical isolation、Evidence generation、Relation integration、failure-domainを検証。

## 14. I-01で決めない事項

I-02へ送る:

- Embedding model
- dimension
- provider library
- normalization方式
- multilingual / cross-lingual model
- Embedding Space schema詳細

I-03へ送る:

- final Vector backend
- ANN / HNSW parameters
- quantization
- server process採否

I-04へ送る:

- lexical/semantic fusion式
- Statement → Object aggregation式
- channel weight
- final Search result schema

I-06へ送る:

- reranker採否
- cross encoder model

I-01の確定事項は、これら後続比較の入力contractとして固定する。
