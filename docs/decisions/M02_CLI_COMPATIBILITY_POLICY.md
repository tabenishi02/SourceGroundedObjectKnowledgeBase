# M-02 CLI Compatibility Policy

更新日: 2026-10-16

- Status: **Accepted — M-02 Complete**
- Phase: `Phase M — CLI / 操作フロー`
- Task: `M-02 [P1] 旧CLIとの互換性を決定する`
- Depends on: `docs/decisions/M01_CLI_NAMESPACE_TAXONOMY.md`
- Related legacy cleanup: `docs/decisions/L05_LEGACY_COMPATIBILITY_CLEANUP_POLICY.md`

---

## 1. Decision

新しいSGOKB CLIへの移行では、**deprecated warning期間を伴う長期互換を設けず、置換commandが成立した時点で旧CLIを明示的に切る**。

ただし、移行途中でcanonical capabilityを失わないように、次の原則を採用する。

> **新しいDomain namespace commandを実装・検証した変更と同じcutoverで、対応する旧command / alias / entrypointを削除する。**

つまり、旧CLIを先に削除して機能欠落を作ることはしない一方、新旧CLIを長期間並存させるdeprecated compatibility layerも作らない。

---

## 2. Compatibility scope

M-02でいう「旧CLI」は、Phase Lで既に退役したFragment / Final Document / old benchmark等のPrototype CLIを意味しない。

それらはL-05で明示的に削除済みであり、M-02で復活させない。

M-02の移行対象は、現在active treeに残るcanonical操作面である。

```text
sgokb
  import
  process / extract
  association ...
  evidence ...
  provenance evidence
  status
  snapshots

sgokb-package
  build
  stage
  preflight
  export
  detect
  receive
  receipts
  pending-validation
  validate-result
  import-result
  render-markdown
  review-result
  diff-versions
```

これらの**domain semanticsは再利用するが、command path自体を永続互換contractとはしない**。

---

## 3. Public entrypoint policy

Phase M後のpublic CLI entrypointは次の1本を正本とする。

```text
sgokb
```

`sgokb-package`はPhase G/H実装時の専用entrypointであり、将来のpublic contractとして維持しない。

Package / Result / Render / Version操作が新しい`sgokb` Domain namespaceへ移行できた時点で、同じcutoverで`pyproject.toml`の`sgokb-package` script entrypointを削除する。

`package_cli.py`の内部ロジックを一時的なrefactor sourceとして利用することは許可するが、`sgokb-package`をdeprecated wrapperとして残さない。

---

## 4. Migration mapping

現行commandから新Domain namespaceへの責務mappingは次を基準とする。

| Current CLI | Target responsibility |
|---|---|
| `sgokb import` | `sgokb source ...` |
| `sgokb process` | `sgokb source ...` |
| `sgokb extract` | `source`側のcanonical processへ統合し、`extract` aliasは廃止 |
| `sgokb association ...` | `sgokb association ...` |
| `sgokb evidence ...` | `sgokb evidence ...` |
| `sgokb provenance evidence` | `sgokb evidence ...` |
| `sgokb status` | `source`または`system`の適切なread操作へ移動 |
| `sgokb snapshots` | `sgokb source ...` |
| `sgokb-package build/stage/preflight/export` | `sgokb package ...` |
| `sgokb-package detect/receive/receipts/pending-validation` | `sgokb result ...` |
| `sgokb-package validate-result/review-result/import-result` | `sgokb result ...` |
| `sgokb-package render-markdown` | `sgokb render ...` |
| `sgokb-package diff-versions` | `sgokb version ...` |

この表は**responsibility mapping**を確定するものであり、M-01で未承認の最終subcommand名・option名を先取りして確定しない。

---

## 5. No deprecation execution layer

cutover後は次を行わない。

- 旧commandを新commandへ内部転送するwrapperを残さない。
- `argparse` aliasとして旧command名を残さない。
- `sgokb-package`をwarningだけ出して実行継続するwrapperとして残さない。
- Fragment / Final / old Search等のL-05削除済みcommandをmigration helperとして復活させない。
- 旧JSON出力shape、stdout/stderr配置、exit codeを互換目的だけで固定しない。

新しいOutput / Error / Exit contractはM-01で別途確定し、それをPhase M以降の正本contractとする。

---

## 6. Atomic cutover rule

各旧operationは、対応する新operationについて次を満たした後に削除する。

1. 新しいDomain namespace routeが実装されている。
2. 既存canonical Application / Service semanticsを再利用している。
3. 旧operationと同等以上の必要capabilityを持つ。
4. focused regression testが成功する。
5. help / operation documentationが新commandを参照する。

この5条件を満たす変更と同じcommit / PR単位で旧routeを削除する。

新command未実装の状態で旧routeだけを削除することは禁止する。

---

## 7. Semantic compatibility that must be preserved

CLI pathをbreaking changeとして切っても、canonical domain contractまで変更してよいことを意味しない。

特に次は維持する。

- Source / Snapshot / Evidence semantics
- Source↔Object association semantics
- Package Build / Stage / Preflight / Exportの安全境界
- External Exportのexplicit acknowledgement
- Result Receipt / Validation / Review / Import境界
- accepted Object Versionのimmutability
- review-required Resultのexplicit acknowledgement
- Search / Similarityのcanonical Application boundary
- MCP read-only boundary

M-02は**operator-facing command routingの移行方針**であり、Domain / Exchange / Versioning contractの再設計ではない。

---

## 8. Configuration compatibility

`SGOKB_DB`、Package / Incoming / Render root、Embedding provider等の現在有効なenvironment variableは、意味が変わらない限りM-02を理由にrenameしない。

ただし、これは旧CLI command pathを互換維持するという意味ではない。Configuration contractの変更が必要になった場合は、M-01または別Decisionで明示的に判断する。

---

## 9. Migration support

実行互換layerの代わりに、移行支援はdocumentationとtestで行う。

- M-03の標準手順は新CLIだけを使用する。
- Phase OのREADME / Release Noteには旧→新command mappingを記載する。
- O-06では今回のCLI変更をBreaking Changeとして明示する。
- CLI regression testでは、新commandが利用可能であることと、削除対象旧alias / `sgokb-package`が最終状態で残っていないことを確認する。

旧commandを実行可能なまま残すことをmigration supportとはしない。

---

## 10. Rationale

長期deprecated互換を採用しない理由は次の通り。

1. 現在はPrototypeからcanonical SGOKBへ移行している段階であり、CLI構造を整理できる時期である。
2. M-01でDomain namespace方式を正本taxonomyとして採用しており、旧flat / specialized entrypointを並存させると操作面が再び二重化する。
3. 旧CLIと新CLIの両方を維持すると、help、test、documentation、error handling、automation contractを二重管理する必要がある。
4. L-05ですでに不要なPrototype compatibility surfaceを削除しており、Phase Mだけ長期互換layerを再導入するのは方針が不整合になる。
5. atomic cutover ruleを採用すれば、長期互換layerなしでも移行途中のcapability lossを防げる。

---

## 11. M-01との境界

M-02で確定するのは**compatibility / cutover policy**である。

次は引き続きM-01の未確定事項とする。

- 各namespace配下の最終command名
- option名
- Output / Error / Exit code contract
- Object selector contract
- Registry proposal review / apply semantics
- Relation write boundary
- Search runtime composition
- MCP composition root
- system / backup / restore operation contract

M-02の完了は、これらを暗黙に承認・確定したことを意味しない。

---

## 12. Completion

M-02の判断は次で確定する。

> **旧CLIはdeprecated execution compatibilityを長期維持せず、新Domain namespace側の同等operationが実装・検証された時点で原子的に切り替える。将来のpublic entrypointは`sgokb` 1本とし、`sgokb-package`は移行完了時に削除する。**

このDecisionをもってM-02をCompleteとする。