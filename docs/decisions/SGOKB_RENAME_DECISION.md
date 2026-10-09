# Source Grounded Object Knowledge Base — Rename Decision

更新日: 2026-10-09

- Decision ID: `SGOKB-NAME-001`
- Status: Accepted
- Old name: `CharacterPageCollector` / `CPC` / `cpc`
- New name: `Source Grounded Object Knowledge Base` / `SGOKB` / `sgokb`

## 1. Decision

CharacterPageCollectorの現行プロジェクト名・略称・コード上のnamespaceを廃止し、新しい正式名称を **Source Grounded Object Knowledge Base**、略称を **SGOKB** とする。

新名称は、現在のシステムがCharacterやWeb Pageの収集だけを目的とせず、ユーザーが選択したSource / Evidenceを根拠としてCharacter / Work / Concept等のObject Knowledgeを構造化・保存・検索・比較・再利用するKnowledge Baseであることを表す。

## 2. Naming contract

| 対象 | 新名称 |
|---|---|
| 正式名称 | `Source Grounded Object Knowledge Base` |
| 略称 | `SGOKB` |
| GitHub Repository | `SourceGroundedObjectKnowledgeBase` |
| Python distribution | `source-grounded-object-knowledge-base` |
| Python package | `sgokb` |
| CLI command | `sgokb` |
| `python -m` entry | `python -m sgokb` |
| Environment prefix | `SGOKB_` |
| Default SQLite DB | `.local/sgokb.sqlite` |
| Native Messaging Host | `com.sgokb.web_page_capture` |
| Structured-output schema name | `sgokb_response` |
| Local repository directory candidate | `C:\codex\SourceGroundedObjectKnowledgeBase` |

Web Capture componentの固有名 `Web Page Capture` / `WebPageCapture` は、旧プロジェクト名を含まず独立した責務を表しているため変更しない。

## 3. Compatibility policy

今回のRenameはBreaking Changeとして扱い、旧名称を現行インターフェースの互換aliasとして維持しない。

したがって、最終状態では次を現行インターフェースとして提供しない。

- `cpc` CLI
- `python -m cpc`
- `src/cpc`
- `CPC_*` environment variables
- `.local/cpc.sqlite` を既定DB名とする動作
- `com.characterpagecollector.web_page_capture` Native Messaging Host
- `character-page-collector` Python distribution

ただし、旧Prototypeの歴史的資料、Rename Decision、Migration/Runbookでは旧名称を説明のため保持してよい。旧名称を歴史資料から機械的に置換して過去の事実を改変しない。

## 4. Stable ID policy

Object / Source / Snapshot / Evidence等の永続IDはプロジェクト名から独立させる。

既存の安定IDを名称変更だけを理由に変更しない。もしProject-name由来のprefixを持つ単なる表示名・metadata・runtime identifierが存在する場合はSGOKBへ変更するが、UUID等のIdentityそのものは維持する。

## 5. Why now

Knowledge Base再設計はA-01〜A-03およびB-01まで完了している一方、B-02以降のObject schema、CLI、MCP、Google Drive exchange、Result schema等はまだ確定していない。

そのため現在が、旧名称を新しい設計へ持ち込まずにBreaking Renameできる最も安全な時点である。

B-02以降は原則としてSGOKB名称のみを使用する。

## 6. Historical terminology

- `CharacterPageCollector` / `CPC` は旧PrototypeまたはRename前状態を明示的に説明する場合だけ使用する。
- 現行システムを指す名称としては `Source Grounded Object Knowledge Base` / `SGOKB` を使用する。
- `Curated Semantic Object Knowledge Base` は旧B-01で使用した分類表現であり、新しい正式名称ではない。必要であればSGOKBの性質を説明する一般表現としてのみ使用する。

## 7. Implementation rule

Rename作業では、Entity→Object、Fragment廃止、新DB schema、MCP実装等の再設計ロジック変更を混在させない。

Rename完了後に旧Prototypeと同等の現行テストを通し、名称・namespace・runtime identifierだけを変更した基準点を作ってからB-02へ進む。
