# M-03 Acceptance Result Template

Use only after the Reference Workstation run.

```text
実施日時:
OS / Python:
branch / commit:
DB path (isolated):
input fixture:

sgokb entrypoint: PASS/FAIL
Object → Evidence: PASS/FAIL
Package build/stage/preflight/export: PASS/FAIL
Result receive/validate/review/import: PASS/FAIL
accepted Object read: PASS/FAIL
Render: PASS/FAIL
Lexical Search: PASS/FAIL
MCP stdio read: PASS/FAIL
Semantic Search: PASS / SKIP / FAIL
Similarity: PASS / SKIP / FAIL
Focused integration test: <result>
Ruff changed files: <result>
Known unrelated baseline: <result>

Findings / fixes:
- ...
```
