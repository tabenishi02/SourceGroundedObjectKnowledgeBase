# Phase J — MCP Knowledge Access Layer Status

更新日: 2026-10-14

## Current status

- [x] **J-01 [P0] Retrieval CoreとMCP Adapterを分離する**
- [x] **J-02 [P0] MCP read toolsを定義する**
- [x] **J-03 [P1] MCP Resourcesを定義する**
- [x] **J-05 [P1] MCP write系はread系と分離する**
- [ ] **J-05 [P1] MCP write系はread系と分離する**
- [ ] **J-06 [P0] ローカルMCP Clientで受入試験する**

J-01の設計・実装・検証記録:

- `docs/decisions/J01_RETRIEVAL_MCP_APPLICATION_BOUNDARY.md`

J-02の設計・実装・検証記録:

- `docs/decisions/J02_MCP_READ_TOOL_CONTRACT.md`

J-03の設計・実装・検証記録:

- `docs/decisions/J03_MCP_RESOURCE_CONTRACT.md`

J-04の設計・実装・検証記録:

- `docs/decisions/J04_CONTEXT_BUILDER_CONTRACT.md`

Latest focused verification:

```text
Ruff: All checks passed
Pytest: 55 passed, 2 skipped
```

## Next task

```text
J-05 [P1] MCP write系はread系と分離する
```
