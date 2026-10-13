# Source Grounded Object Knowledge Base — Markdown Renderer

更新日: 2026-10-13

- Task: `H-03 [P1] Markdown Rendererを実装する`
- Status: Complete
- Parent: Phase H — Result Validation / Import / Rendering
- Canonical input: accepted Object Knowledge Version in SQLite
- JSON input: compatible render model / `current_object.json` shape
- Implementation:
  - `src/sgokb/rendering/markdown.py`
  - `src/sgokb/storage/markdown_repository.py`
- CLI: `sgokb-package render-markdown`
- Tests: `tests/test_markdown_renderer.py`
- Follow-up: H-04 Diff / Review表示

---

## 1. 目的

H-03は、canonical Object Knowledgeを人間が読みやすいMarkdownへ投影するderived rendererを提供する。

基本境界:

```text
canonical SQLite / structured JSON
  -> read-only render model
  -> deterministic Markdown serializer
  -> derived Markdown artifact
```

Markdownはcanonical Knowledgeではない。

```text
Markdown edit
  != canonical edit
```

Markdownを直接編集してもSQLiteへ逆Importしない。再render時はcanonical DB / JSONから再生成する。

---

## 2. Canonical / derived境界

H-03のMarkdownはE-04で定義した`rendering` derived artifactである。

canonical:

- Object identity
- accepted Version
- Classification snapshot
- Facet / Statement / Attribute / Relation
- temporal scope
- Evidence Link
- reported-view attribution
- H-02 Result review metadata / Import provenance

rebuildable derived:

- Markdown document

したがってMarkdown消失・破損・手編集はcanonical Knowledgeを壊さない。

---

## 3. DB read model

`MarkdownRenderReadRepository`は1つのaccepted Versionから表示専用モデルを構築する。

主要要素:

```text
object
version
classification
knowledge
  summary
  facets
  attributes
  relations
generation
review
provenance
evidence
```

Versionはcurrentに限定しない。過去accepted Versionもrenderできる。

ただしcandidate / abandonedをcanonical human documentとしてrenderしない。標準DB rendererはaccepted Versionだけを対象とする。

---

## 4. Version-aware projection

Version固有情報として次を表示する。

- Version ID
- Version number
- base Version ID
- created / accepted timestamp
- currentかどうか
- Version Classification snapshot

Object名・AliasはObject Registryの現在表示値を用いる。一方、ClassはVersion snapshotを用いるため、後日のClassification変更で過去Versionの意味を置き換えない。

---

## 5. Knowledge rendering

### Summary

summary Statementを表示し、必要に応じて次を併記する。

- derivation kind
- language
- temporal scope
- reported-view attribution
- Evidence reference

### Facet

全Version Facetを表示する。

Facet status:

```text
content
insufficient_evidence
not_applicable
not_analyzed
```

StatementがないFacetも省略せずstatusを表示する。

### Attribute

人間向けtableとして、

- Attribute名 / ID
- status
- typed value
- temporal scope
- Evidence

を表示する。

### Relation

人間向けtableとして、

- Subject Object
- Relation Type
- Object endpoint
- temporal scope
- Evidence

を表示する。

Relation endpointは可能な場合Object nameで表示し、canonical ID自体はread model内で保持する。

---

## 6. reported_view attribution

H-02でcanonical保存した`knowledge_statement_attributions`を失わず表示する。

対応kind:

```text
source
object
named_actor
community
```

Source / Object attributionは可能な場合display nameへ解決する。

これにより「Sourceが述べた見解」と「SGOKB利用者本人の見解」を混同しない。

---

## 7. Evidence表示

Statement / Attribute / Relationおよびreview metadataのEvidence referenceを集約する。

Knowledge本文では短い参照を表示する。

```text
E1
E2
...
```

文末のEvidence sectionでは、可能な範囲で次を表示する。

- Evidence ID
- Source ID / label
- Snapshot ID / title
- language
- locator
- location metadata
- Evidence content

Evidence contentは動的長のMarkdown code fence内へ入れる。

Evidence本文にbacktick列が含まれても、その最大長より長いfenceを選ぶことで本文を切断・変更しない。

---

## 8. H-02 review metadata

H-03はH-04のDiff algorithmを先取りしないが、H-02でVersionに固定保存されたreview metadataは人間向けdocumentへ表示できる。

対象:

```text
result_status
conflicts
gaps
unresolved_references
registry_proposals
class_extensions
```

Registry proposalを表示してもRegistryへ適用しない。

Import時の、

```text
review_acknowledged
package_id
receipt_id
result_sha256
manifest_sha256
```

等もImport provenanceとして表示する。

---

## 9. JSON renderer

`ObjectMarkdownRenderer`はDBに依存しないpure serializerである。

対応入力:

1. `sgokb.markdown-render-model/1.0`相当の表示モデル
2. `PackageBuildReadRepository.current_object_snapshot()` / `current_object.json`互換shape

JSON renderingはSQLiteを更新しない。

そのため、

```text
JSON -> Markdown preview
```

をcanonical mutationと分離できる。

JSON rendererはResult ImportやValidationの代替ではない。未import JSONをMarkdown化してもcanonical Knowledgeにはならない。

---

## 10. Managed artifact path

標準CLI:

```text
sgokb-package render-markdown --version <version_id>
sgokb-package render-markdown --object <object_id>
```

標準root:

```text
derived/rendered/
```

配置:

```text
derived/rendered/<encoded_object_id>/<encoded_version_id>.md
```

Windowsで禁止される`:`等を含むIDでも安全に扱えるようpath componentをpercent encodeする。

`--output-root`または`SGOKB_RENDER_ROOT`でderived rootを変更できる。

---

## 11. Atomic file write

managed Markdownは同一directoryのtemporary fileへ完全writeした後、`os.replace()`で置換する。

```text
render text
  -> temp write
  -> flush / fsync
  -> atomic replace
```

途中失敗で既存Markdownを半端な内容へtruncateしない。

---

## 12. derived state coordination

accepted/current promotion時、E-04/H-02によって、

```text
object_derived_states(kind='rendering')
```

は新current Versionをtargetに`pending`となる。

H-03 managed render成功時:

```text
pending / failed -> ready
```

render失敗時:

```text
pending -> failed
last_error = error text
```

ただしVersionがhistoricalであり、現在の`rendering.target_version_id`でなければderived stateを変更しない。

---

## 13. revision CAS / stale worker protection

rendererは処理開始時点の`rendering.revision`を保持する。

例:

```text
revision 1 -> v1 rendering
accept v2
revision 2 -> v2 pending
late v1 renderer completes
```

late v1 workerはrevision 1で`ready`更新を試みるがCASに失敗する。

結果:

```text
v1 Markdown artifact = historical artifactとして残せる
v2 rendering state    = pendingのまま
```

旧workerが新currentを誤って`ready`にしない。

---

## 14. Human-readable safety boundary

canonical textをMarkdown syntaxとして無制限に再解釈させないため、表示場所に応じて次を行う。

- heading内改行を除去
- inline text内改行を空白化
- table cellの`|`をescape
- inline code delimiter衝突を避ける
- Evidence本文はdynamic fenceで囲む

これは意味内容の修正ではなくpresentation boundaryの安全化である。

---

## 15. Markdown冒頭warning

全managed Markdownへ次の意味を持つwarningを付与する。

```text
Derived read-only view.
Editing this file does not update the database.
```

さらにHTML commentとしてderived artifactであることを埋め込む。

これにより人間が生成Markdownを正本と誤認しにくくする。

---

## 16. H-03で行わないこと

- MarkdownからSQLiteへの逆Import
- Markdownを編集正本にすること
- candidate / invalid Resultのcanonical化
- Registry proposal自動適用
- semantic truth判定
- v1→v2 Diff計算
- destructive omission判定
- manual approval state machine
- Search / Embedding / Vector生成

Diff / Review表示はH-04へ引き継ぐ。

---

## 17. Test contract

H-03 focused testでは少なくとも次を固定する。

1. DB accepted VersionからObject文書を生成できる。
2. Summary / Facet / Attribute / Relation / temporal scope / attributionを表示する。
3. Evidence provenance / contentを表示する。
4. Import provenanceを表示する。
5. H-02 review metadataを表示するがRegistry proposalを適用しない。
6. Markdown手編集がcanonical DBを変更しない。
7. rerenderでcanonical DBから元の内容を再生成する。
8. JSON rendererがdeterministicでDBを変更しない。
9. historical Version renderがcurrent derived stateを変更しない。
10. current render成功で`rendering=ready`となる。
11. render失敗で`rendering=failed`となる。
12. revision CASでlate old workerがnew targetを`ready`にしない。
13. candidate Versionをcanonical Markdownとしてrenderしない。
14. Windows unsafe IDをmanaged pathでpercent encodeする。

---

## 18. 完了条件

H-03は次を満たしたためCompleteとする。

- canonical DB / accepted Versionから人間向けMarkdownを生成できる。
- JSONから同じserializerを利用できる。
- Markdownを正本へ昇格させるreverse pathを持たない。
- Evidence-grounded / attribution / review provenanceを失わない。
- managed artifactをatomic writeする。
- E-04 derived state / revision CASと接続した。
- rendering failureをcanonical acceptanceと分離した。
- historical renderingをcurrent stateから分離した。

次Task:

```text
H-04 [P1] Diff / Review表示を実装する
```
