# M-01 CLI Namespace Taxonomy Decision

更新日: 2026-10-16

- Status: **Accepted (partial M-01 decision)**
- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-01 [P0] 新しいObject中心CLIを設計する`
- Scope: CLI top-level taxonomy only

---

## Decision

新しいSGOKB CLIのtop-level構成には、**Domain namespace方式（案A）**を採用する。

基本形は次とする。

```text
sgokb source ...
sgokb object ...
sgokb association ...
sgokb evidence ...
sgokb registry ...
sgokb package ...
sgokb result ...
sgokb version ...
sgokb search ...
sgokb similar ...
sgokb render ...
sgokb mcp ...
sgokb system ...
```

操作対象となるdomain / responsibilityを先に選び、そのdomain内でactionを選ぶ構造とする。

例:

```text
sgokb object show
sgokb package build
sgokb result import
sgokb system integrity
```

---

## Rationale

SGOKBにはSource / Evidence / Object / Package / Result / Registry / Search / MCP / Systemなど、責務と副作用境界が異なる複数の領域が存在する。

Domain namespace方式は、それらの責務境界をCLI構造へそのまま反映できる。

主な利点:

- command数が増えても同種操作を同じnamespaceへまとめられる。
- `sgokb <domain> <action>`という一貫した読み方ができる。
- Object中心の運用を維持しつつ、MCPやSystemのように特定Objectへ属さない操作を不自然にObject配下へ置かずに済む。
- Flat command方式よりcommand discoveryとhelp構造を整理しやすい。
- domainごとのside-effect boundaryを明確にしやすく、自動化・運用手順・将来の権限制御へ発展させやすい。

---

## Rejected alternatives

### Object配下へ集中する方式

例:

```text
sgokb object evidence select
sgokb object package build
sgokb object result import
```

Object中心であることは明確になるが、`mcp serve`、backup、integrity check等のObject非依存操作までObject配下に置くと責務が不自然になるため不採用とする。

### Flat command方式

例:

```text
sgokb add-object
sgokb build-package
sgokb import-result
```

少数commandでは単純だが、Phase M以降にcommand数が増えると一覧性と分類性が低下するため不採用とする。

---

## Non-decisions

このDecisionで確定するのは**top-level CLI taxonomyのみ**である。

次の事項はM-01内の別判断として未確定のまま残す。

- 各namespace配下の最終command名・option名
- `sgokb-package`の互換性・廃止時期（M-02で最終判断）
- Output / Error / Exit code contract
- Object selector contract
- Registry proposal review / apply semantics
- `object relate`の最終semantics
- Search runtime composition
- MCP composition rootの詳細
- system / backup / restoreの具体的なoperation contract

これらはユーザー承認を得ながら順次確定する。
