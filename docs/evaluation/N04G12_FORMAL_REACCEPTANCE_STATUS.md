# N-04G-12 Formal Re-Acceptance Status

更新日: 2026-10-18

- Phase: `Phase N — Test / Evaluation / Acceptance`
- Task: `N-04G-12 [P0] Reference WorkstationでN-04を正式再受入する`
- Status: **Blocked before formal start — Reference Workstation execution pending**
- N-04 status: **Failed / not Complete**
- Frozen acceptance spec: `benchmark/n04-ai-use-cases-v2.json`
- Frozen harness: `benchmark/n04-v2-formal-harness-v1.json`
- Codex handoff: `docs/planning/N04G12_CODEX_REFERENCE_WORKSTATION_HANDOFF.md`

---

## 1. Decision

2026-10-18、このChatGPT sessionからReference Workstation上でG-12 formal re-acceptanceを開始しようとした。

Desktop Commander device:

```text
FNB1Main
Status: Online
```

は確認できたが、remote command execution時にDesktop Commanderの月間利用上限へ到達しており、ローカルcommand実行は開始できなかった。

そのため、G-11でFreezeしたReference Workstation / local LM Studio / local Qdrant / local evaluation DB条件を満たすformal runは**未開始**である。

これは:

- N-04 Case failure
- generator failure
- validator failure
- MCP failure
- SGOKB defect

のいずれでもない。

Formal start boundaryはG-11で「全preflight PASS後、start evidenceを書き終えた後のCase 1最初のMCP request直前」と定義されているため、その境界には到達していない。

---

## 2. Why no substitute environment was used

G-12をGitHub Actions等へ置き換えて実行しない。

G-11ではformal harnessとして次がFreezeされている。

- Reference Workstation Windows 11
- Python 3.10.6
- RTX 4090 24GB
- local LM Studio 0.4.25.0
- frozen generator `sgokb-n04-mistral32`
- frozen semantic validator `sgokb-n04-phi4`
- local N-03 evaluation DB
- local Harrier/Qdrant profile
- MCP stdio read boundary

別環境での代替実行はG-11 harness violationとなり、formal N-04 v2 resultとして扱えない。

---

## 3. Action taken

Reference Workstation上のCodexへ引き渡せる実行指示を作成した。

```text
docs/planning/N04G12_CODEX_REFERENCE_WORKSTATION_HANDOFF.md
```

このhandoffには次を含む。

- repository sync / preflight
- Frozen runtime values
- formal start boundary
- local-only generator / semantic validator
- structured-output schema
- MCP public read path
- Case 1 / 2 / 3 exact flow
- single retry policy
- evidence tree
- canonical SHA-256 before/after
- system integrity before/after
- Reference Workstation focused/full regression
- final rubric
- PASS/FAIL時のpost-run documentation update
- ChatGPTへ返すresult payload

---

## 4. State preservation

G-12未実行のため、次は変更しない。

```text
N-04 = Failed / open
N-04G-12 = not Complete
N-05 = blocked
PR #39 = Draft / unmerged
```

G-07 / G-08 / G-11 Frozen semanticsも変更しない。

---

## 5. Next action

Reference Workstation上のCodexへ:

```text
docs/planning/N04G12_CODEX_REFERENCE_WORKSTATION_HANDOFF.md
```

の「Codexへ渡す指示文」を渡し、formal runを実行する。

Codexからformal resultとpost-run commit SHAが返った後、ChatGPTがGitHub上の更新とevidence summaryを照合してN-04の最終状態を確認する。
