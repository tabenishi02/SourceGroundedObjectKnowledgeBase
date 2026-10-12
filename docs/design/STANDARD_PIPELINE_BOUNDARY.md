# Standard Pipeline / Legacy Fragment Boundary

更新日: 2026-10-12

- Status: Implemented
- Task: `F-02 [P0] 標準パイプラインからFragment生成を外す`
- 前提: `F-01` canonical Source / Evidence ingestion

## 1. 目的

SGOKBの標準処理から旧PrototypeのFragment生成を除外し、canonical Evidenceを次工程へ渡す構造へ固定する。

F-02以降の標準経路は次とする。

```text
Web Capture Bundle
  -> canonical Source / Locator
  -> Snapshot / Raw Artifact
  -> Normalization Run
  -> Evidence
  -> Object Evidence Retrieval / Package（F-03以降）
```

この経路ではGenerative LLMを呼ばず、Fragmentを生成・保存しない。

## 2. Fragmentの扱い

旧Fragment機能はF-02で完全削除しない。Phase Lまで **legacy / research compatibility** として保持する。

保持対象には以下を含む。

- `capture.py` のHigh Recall Fragment生成
- `Application.fragment()` / `capture_fragments()` 互換API
- Fragment table / Fragment-Evidence link
- Fragment依存の旧Final Document生成
- Fragment / Final評価benchmarkとPrototype評価script
- Fragment / Final用prompt群

F-02ではこれらを`_legacy/`へ物理moveしない。`SGOKB_MODULE_MIGRATION_POLICY.md`の方針どおり、物理隔離・archive・削除判断はPhase Lで行う。behavior変更と大規模moveを同一Taskへ混在させないためである。

## 3. Application API境界

canonical standard API:

```text
Application.import_source_path()
Application.process_source_snapshot()
```

legacy / research API:

```text
Application.legacy_fragment()
Application.legacy_capture_fragments()
Application.legacy_generate()
Application.legacy_build_document()
```

既存利用者との互換性のため、次の旧method名は当面shimとして保持する。

```text
fragment()          -> legacy_fragment()
capture_fragments() -> legacy_capture_fragments()
generate()          -> legacy_generate()
build_document()    -> legacy_build_document()
```

新standard codeはこれら互換shimを呼び出してはならない。

## 4. CLI境界

`import` / `process` / `status` / `snapshots`はcanonical Source / Evidence側を標準動作とする。

旧Prototype tableを利用する必要がある場合だけ`--legacy`を明示する。

Fragment / Final /旧benchmarkは標準コマンドと区別するため、次を正式名とする。

```text
legacy-fragment
legacy-generate
legacy-benchmark
```

既存CLI互換のため、`fragment` / `generate` / `benchmark`は上記legacy commandのaliasとしてPhase Lまで受理する。

## 5. 標準処理で禁止すること

standard Capture / Import / Normalize / Evidence経路では以下を行わない。

- Generative LLM呼び出し
- `fragments` tableへのwrite
- `fragment_evidence`へのwrite
- `ai_runs`へのFragment/Final生成記録
- `structured_documents` / `documents`への旧Final生成
- Fragment coverageを標準Acceptance指標として利用

canonical EvidenceはF-03のObject Evidence Retrievalへ直接渡す。

## 6. 互換性

旧Prototypeの研究・再現試験を壊さないため、既存Fragment実装とtableは残す。

ただし、互換性は「標準経路の一部」という意味ではない。旧API・旧CLI aliasはPhase Lで利用状況を確認し、次のいずれかを決定する。

- `_legacy/`へ隔離してresearch-onlyで維持
- archiveへ移動
- 不要なら削除

既存legacy dataのcanonical migrationも引き続きPhase Lの責務とする。

## 7. Test Gate

F-02では少なくとも次を自動試験する。

1. 標準`import`がcanonical Source / Snapshotを作り、legacy Snapshotを作らない。
2. 標準`process`がcanonical Evidenceを作る。
3. 標準`process`後もFragment数が0のままである。
4. 標準処理で`ai_runs`が生成されない。
5. `--legacy`による旧Import / Normalizeが引き続き利用可能である。
6. `legacy-fragment`等の研究用commandが存在する。
7. 旧command名aliasが互換目的で解析可能である。

## 8. F-03への引き継ぎ

次Task `F-03 [P0] Object Evidence Retrievalを実装する`では、Fragmentをretrieval中間層として使用せず、canonical `evidence_records`を直接候補集合とする。

選択signalはname / alias / explicit Source↔Object association / Source metadata / lexical / semantic / manual includeを組み合わせ、選択理由を追跡可能にする。
