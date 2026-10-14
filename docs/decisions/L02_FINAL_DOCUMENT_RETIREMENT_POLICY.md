# L-02 Final Document Retirement Policy

更新日: 2026-10-15

- Status: Accepted
- Task: `L-02 [P0] Final Document table / code / CLIの移行方針を確定する`
- Baseline: `1cef5f6bc0e72f28469e523926144131cf903e43`
- Related:
  - `docs/decisions/L01_FRAGMENT_RETIREMENT_POLICY.md`
  - `docs/planning/PHASE_L_PREPARATION.md`
  - `docs/reference/KNOWLEDGE_BASE_ASSET_CLASSIFICATION.md`
  - `docs/design/STANDARD_PIPELINE_BOUNDARY.md`
  - `docs/design/MARKDOWN_RENDERER.md`

---

## 1. Decision

旧PrototypeのFragment-based Final Document機能はactive schema / active package / standard CLIから完全に退役させる。

> **`documents` / `structured_documents`、`src/sgokb/final.py`、Final専用Prompt、`legacy-generate` / `generate` alias、および旧Document保存・参照APIを削除対象とする。旧Final Document dataはcanonical Knowledgeへmigrationせず、恒久archiveもしない。人間向けMarkdown表示はPhase Hで実装済みのcanonical `ObjectMarkdownRenderer`を唯一の現行RendererとしてKeepする。**

L-01でFragment自体を削除すると確定しており、旧FinalはFragmentを入力・citation単位としているため、独立した現行用途を持たない。

---

## 2. 調査結果

### 2.1 `final.py`はFragment専用である

`StructuredFinal.build()`は`related_fragments()`を入力にclusterを作り、必要に応じ`final_order` Promptで並び替え、`documents` / `structured_documents`へ保存する。

したがってcanonical Evidence / Object Result / Object Version workflowとは独立した旧Prototype経路である。

### 2.2 `Application.legacy_generate()`もFragment専用である

`legacy_generate()`は旧Hybrid Searchから`kind == "fragment"`だけを選択し、`final_document` Promptへ渡してMarkdownを生成する。

`generate()`は単なるcompatibility aliasである。

### 2.3 DB tableは旧Finalの保存専用である

- `documents`: legacy Entity、AI run、Markdown、citation、configurationを保存する。
- `structured_documents`: `documents`へ1:1で紐づき、旧Final representation / clusterを保存する。

canonical Object Version / Result Import / Rendererはこれらを正本として利用しない。

### 2.4 canonical Markdown Rendererは別実装である

`src/sgokb/rendering/markdown.py::ObjectMarkdownRenderer`はaccepted Object Knowledge / compatible structured JSONから決定論的にMarkdownを生成する。

このRendererは、

- Fragmentを入力にしない。
- `documents` / `structured_documents`をKnowledge正本にしない。
- Markdownをderived read-only viewとして扱う。
- canonical Object Version / Evidence / Import provenanceを表示する。

したがって旧Final削除の影響を受けずKeepする。

---

## 3. Asset classification

| Asset | L-02 Decision |
|---|---|
| `documents` | Delete from active schema |
| `structured_documents` | Delete from active schema |
| existing rows in those tables | Do not migrate / do not permanently archive |
| `src/sgokb/final.py` / `StructuredFinal` | Delete from active package |
| `final_document.md` / schema | Delete from active package data |
| `final_order.md` / schema | Delete from active package data |
| `Application.legacy_build_document()` | Delete |
| `Application.build_document()` | Delete |
| `Application.legacy_generate()` | Delete |
| `Application.generate()` | Delete |
| `Application.legacy_render_document()` | Delete if no remaining legacy caller |
| Repository `save_document()` / `document()` | Delete |
| `KnowledgeRepository.save_structured()` / `structured_document()` | Delete |
| CLI `legacy-generate` | Delete |
| CLI `generate` alias | Delete |
| CLI `provenance document` branch | Delete |
| Final-only tests / scripts | Delete or L-04 archive according to historical value |
| `ObjectMarkdownRenderer` | Keep |
| canonical Markdown repository / renderer tests | Keep |
| `docs/design/MARKDOWN_RENDERER.md` | Keep |

---

## 4. DB policy

### 4.1 existing Final rows are not migration source

2026-10-14のruntime auditによりproduction移行対象dataが存在しないことを確認済みである。

したがって、

```text
legacy documents / structured_documents
  -> canonical Object Version
```

というdata migrationは行わない。

旧Final Markdownを解析してObject Result / Knowledge Statementへ戻す処理も作らない。

### 4.2 L-03 clean baselineから除外する

L-03ではfresh canonical DBに次を作成しない。

```text
documents
structured_documents
```

historical migration 001/002をGit履歴として保持する場合も、active canonical bootstrapでは旧Final tableを再導入しない。

### 4.3 `ai_runs`等の共有legacy tableはL-02だけで一括削除しない

Final生成に使われた`ai_runs` row自体は新DBへmigrationしない。

ただし`ai_runs` / `ai_observations`等はFragment / benchmark等との共有legacy資産なので、table全体の最終処遇はL-03 / L-04 / L-05の依存確認に従う。

---

## 5. Code / Prompt policy

### 5.1 `final.py`

active packageから削除する。

`_legacy/`へ移して実行可能状態を維持する方式は採用しない。必要な歴史的実装はGit履歴から参照する。

### 5.2 Final Prompt

次をactive package dataから削除する。

```text
final_document.md
final_document.schema.json
final_order.md
final_order.schema.json
```

これらをObject Result用`object_analysis.md`へrename / mergeして流用しない。

### 5.3 Application / Repository API

旧Final生成専用methodはL-05で削除する。

canonical Rendererは`rendering/` + canonical storage/read modelを利用し、旧`document()` APIへ依存させない。

---

## 6. CLI policy

次をstandard CLIから削除する。

```text
legacy-generate
generate
provenance document
```

`generate`という名前を将来別意味へ暗黙再利用しない。

Phase Mの現行Object中心CLIでは人間向け派生表示を`render`として扱う方針を維持する。将来`generate`を再導入する場合は別Decisionでsemanticsを定義する。

---

## 7. Canonical Markdown Renderer boundary

次は旧Finalと明確に区別してKeepする。

```text
src/sgokb/rendering/markdown.py
src/sgokb/storage/markdown_repository.py
tests/test_markdown_renderer.py
docs/design/MARKDOWN_RENDERER.md
```

原則:

```text
accepted Object Knowledge
  -> deterministic render
  -> derived Markdown
```

禁止:

```text
Fragments
  -> Final synthesis
  -> canonical Markdown
```

Markdownは引き続き編集正本ではない。

---

## 8. Tests / benchmark / sample outputs

### 8.1 active tests

旧Final generationを直接検証するtestはactive suiteから削除する。

例:

- `test_core.py`の旧`generate()` / `documents` persistence test
- legacy Final error rollback test
- legacy CLI alias contract testのFinal部分

一方、canonical renderer / Object Version / Result Import regressionはKeepする。

### 8.2 benchmark

Final Document生成速度・文字数・section数等をcurrent acceptance KPIとして使用しない。

`benchmark.py`や`run_evaluation.py`等に残るFinal benchmarkはL-04で、具体的な歴史的価値がある結果だけarchiveし、それ以外は削除する。

### 8.3 generated/sample output

旧Final出力を「将来使うかもしれない」という理由だけで維持しない。

ただし`sample/` Raw Capture corpusはL-01 / L-03方針どおり保持し、旧Final派生出力と混同しない。

---

## 9. Generative LLM providerへの影響

L-01でFragment generation、L-02でFinal generationをDelete対象としたため、standard runtimeがGenerative LLM providerを必要とする理由はさらに減る。

ただしL-04でlegacy benchmark用途を確認する前にprovider実装を先行削除しない。

最終cleanupはL-05で行い、Embedding providerは現行Searchに必要なので維持する。

---

## 10. Follow-up tasks

### L-03

- `documents` / `structured_documents`をcanonical baselineへ含めない。
- existing rowsをmigrationしない。
- clean DBに旧Final tableが存在しないことをtestする。
- canonical `ObjectMarkdownRenderer`がclean DB上のaccepted Object Knowledgeから動作することを確認する。

### L-04

- Final speed / generation benchmarkをarchive / delete分類する。
- 必要な歴史的結果がruntime DBにしかない場合、DB全体ではなく必要最小限のresult / manifest /条件だけをarchiveする。

### L-05

実際に次を削除する。

```text
src/sgokb/final.py
Final prompt files
Application Final compatibility methods
Repository legacy document methods
legacy-generate / generate alias
provenance document branch
Final-only tests / scripts
不要になったGenerative LLM compatibility surface
```

---

## 11. Acceptance Criteria

- [x] 旧Final Documentとcanonical Markdown Rendererを分離した。
- [x] `documents` / `structured_documents`をDelete対象と確定した。
- [x] 旧Final dataをcanonical Knowledgeへmigrationしないと確定した。
- [x] 旧Final dataを恒久archiveしないと確定した。
- [x] `final.py` / Final Prompt / Application / Repository legacy APIをDelete対象と確定した。
- [x] `legacy-generate` / `generate` / `provenance document`をDelete対象と確定した。
- [x] `ObjectMarkdownRenderer`とcanonical renderer関連資産をKeepすると確定した。
- [x] DB clean rebuildはL-03、benchmark整理はL-04、物理code cleanupはL-05へ分離した。

**L-02: Complete.**
