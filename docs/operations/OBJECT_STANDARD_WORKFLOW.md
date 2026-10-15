# 1 Object Standard Workflow

更新日: 2026-10-16

- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-03 [P1] 1 Object標準手順を1ページで実行可能にする`
- Status: **Workflow specified / CLI implementation pending**
- Depends on: `M-01` target CLI implementation, `M-02` compatibility cutover policy

> 目的: 1 Objectを、内部SQLite操作やPython REPLを使わず、Object登録からKnowledge確認まで一貫して処理できる標準運用を1ページに固定する。

---

## 標準フロー

| # | Operator action | Target CLI responsibility | Gate / output |
|---:|---|---|---|
| 1 | Objectを登録・確認する | `sgokb object ...` | stable `object_id`を取得する |
| 2 | Web Capture Bundleを取り込む | `sgokb source ...` | canonical Source / Snapshotを作成する |
| 3 | SnapshotをNormalizeする | `sgokb source ...` | canonical Evidenceを作成する |
| 4 | Source↔Object関連を確認・修正する | `sgokb association ...` | candidate / confirmed / excludedを確定する |
| 5 | Object Evidence候補・選択結果を確認する | `sgokb evidence ...` | Packageへ入れるEvidence集合を確認する |
| 6 | Object Evidence Packageをbuildする | `sgokb package ...` | local derived Packageを生成する |
| 7 | stage / preflight / exportする | `sgokb package ...` | 外部送信前に内容・destination・warningを確認し、明示exportする |
| 8 | ChatGPTで手動分析する | 外部Human step | Packageだけを入力し、`result.json`を返却する |
| 9 | Resultをdetect / receiveする | `sgokb result ...` | immutable local receiptを作成する |
| 10 | Resultをvalidate / reviewする | `sgokb result ...` | invalid / blocked / review-requiredを確認する |
| 11 | Resultを明示importする | `sgokb result ...` | 新しいaccepted Object Versionを作成する |
| 12 | 派生Markdownを生成する | `sgokb render ...` | human-readable artifactを生成する |
| 13 | Object / Search / Similarityで確認する | `sgokb object ...`, `sgokb search ...`, `sgokb similar ...` | current accepted Knowledgeが取得・検索できることを確認する |
| 14 | 必要ならMCPで確認する | `sgokb mcp ...` | read-only MCP経由で同じKnowledgeを取得する |

---

## Human decision boundaries

次は自動継続しない。

1. **Object Identity確定** — Object登録時にstable identity / Classをoperatorが確認する。
2. **External Export** — Package buildだけではDrive等へ送信しない。preflight後に明示exportする。
3. **ChatGPT工程** — SGOKB runtime内で生成LLMを自動実行しない。
4. **Authoritative Result Import** — Result検出・Validation成功だけではcurrent Knowledgeへ昇格しない。明示importする。
5. **Review-required Result** — partial / stale / destructive omission / Registry proposal等はreview結果を確認してから承認する。
6. **Registry proposal** — Object Result内proposalをKnowledge Importの副作用として自動適用しない。

---

## 異常時の停止位置

- Source Import / Normalize失敗: Package工程へ進まない。
- Evidence不足: association / Evidence selectionへ戻る。
- Package preflightが`blocked`: exportしない。
- Result Validationがinvalid/error: importしない。
- Reviewがblocked: importしない。
- review-required: operator acknowledgementなしでimportしない。
- stale Result: current Versionへsilent promotionしない。
- Derived render / index失敗: accepted canonical Versionは保持し、派生処理だけ再試行する。
- MCP停止: canonical DB / CLI readは利用可能であり続ける。

---

## 実行可能化Gate

このworkflowを「1ページだけで実行可能」と判定するには、M-01実装で少なくとも次を満たす必要がある。

- Object登録・表示CLIが存在する。
- Source Import / ProcessがDomain namespaceへ移行している。
- Association / Evidence操作が新CLIから利用できる。
- Package / Result / Render / Version操作が`sgokb`へ統合され、`sgokb-package`依存がない。
- Search / Similarity CLIが存在する。
- `mcp serve`相当のoperator-facing composition rootが存在する。
- M-01で確定するselector / output / error / exit contractに従っている。
- workflow全体のfocused integration testが成功する。

M-01の未承認subcommand名・option名をこの文書だけで確定しない。M-01 implementation cutover後、この表の`Target CLI responsibility`を確定command lineへ置換し、M-03をCompleteとする。
