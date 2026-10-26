# Source / Evidence Canonical Ingestion Pipeline

> **L-05現行境界（2026-10-15）:** canonical ingestionは維持している。本文のF-01時点の旧`import_path()` / `process()`・legacy table共存に関する記述は履歴であり、そのcompatibility runtimeはL-05で削除済み。現行APIは`import_source_path()` / `process_source_snapshot()`を使用する。詳細は[L-05 Decision](../decisions/L05_LEGACY_COMPATIBILITY_CLEANUP_POLICY.md)。

更新日: 2026-10-12

- Status: Implemented
- Task: `F-01 [P0] 既存Capture / Import / Normalize / Evidenceを新設計へ接続する`
- Base contract: `docs/design/SOURCE_EVIDENCE_SCHEMA.md`

## 1. 目的

既存Web Capture / Extractor資産を再利用しつつ、生成LLMを介さずに次のcanonical chainを成立させる。

```text
Web Capture Bundle
  -> SourceRecord + SourceLocator
  -> SourceSnapshot
  -> RawArtifact 1..N
  -> NormalizationRun
  -> EvidenceRecord 0..N
  -> EvidenceLocation 0..N
```

旧Prototypeの`import_path()` / `process()`はPhase Lまでcompatibility pathとして残し、canonical pathへの常時dual-writeは行わない。

## 2. Application use case

F-01では既存`Application`へ明示的なcanonical use caseを追加した。

- `import_source_path(path, source_id=None, label=None)`
  - Web Capture Bundleを検証してcanonical Source / Snapshot / Rawへ保存する。
- `process_source_snapshot(snapshot_id, ...)`
  - canonical Snapshotを既存ExtractorでNormalizeし、canonical Run / Evidence / Locationへ保存する。

旧`import_path()` / `process()`の意味は変更しない。

## 3. Source resolution policy

CaptureをSourceへbindする順序は次とする。

1. callerが`source_id`を明示した場合、そのSourceを最優先する。
2. 明示IDがない場合、page URL / canonical URL locatorからactive Source候補を雀める。
3. 候補が1 Sourceだけならresolution signalとして再利用する。
4. 候補が複数Sourceならsilent mergeせずrejectする。
5. 候補が0なら新しいSourceを作成する。

URL / canonical URLはSource Identityそのものではない。同じlocatorを複数Sourceが保持できるE-03契約を維持する。

## 4. Capture idempotency

Web Capture `capture_id`をcanonical `snapshot_id`として維持する。

同一`capture_id`の再Importでは、ZIPコンテナbyte列ではなくBundle内の`logical_path + SHA-256 + bytes`集合から計算した`artifact_set_sha256`を比較する。

- artifact集合が同じ: idempotent retryとして既存Snapshotを返す。
- artifact集合が異なる: 同一Snapshot IDでRawが変化したものとしてrejectする。

ZIP再pack等でコンテナbyte列だけが変わっても、Raw Artifact集合が同じならSnapshot内容は同一と判定できる。`bundle_sha256`自体もimport metadataとして保持する。

## 5. Web Capture mapping

### Locator

- `manifest.page.url` -> `kind=url`
- `metadata/document.json.canonical_url` -> `kind=canonical_url`

canonical URLが実URLと同値でも別kindとして保持する。

### Snapshot

- `capture_id` -> `snapshot_id`
- `captured_at` -> capture timestamp
- `capture_method=web_capture`
- capture tool name/version
- title
- manifest / capture metadata / warnings
- `success -> complete`, `partial -> partial`

### Raw Artifact

Bundle内の全Artifactを個別Raw Artifactとして登録する。

- `storage_ref`: `.webcapture.zip`の保存参照
- `logical_path`: Bundle内path
- SHA-256 / bytes
- artifact kind
- media type

初期kindは`capture_manifest / rendered_dom / frame_dom / metadata / mhtml / checksums`等とし、意味Identityには`logical_path`も必ず残す。

## 6. Source classification / metadata mapping

Import時に次を保存する。

- `resource_type=web_page` — deterministic
- `site=<hostname>` — deterministic
- `document_genre=<legacy classify result>` — deterministic
- `media_type=<document.content_type>` — captured
- `canonical_url` — captured metadata
- `language` — captured metadata

Normalize後にPage Contextから次をbest-effort mappingする。

- `publisher_kind` — deterministic
- `page_purpose` — deterministic
- `page_summary` — deterministic metadata
- `subject_candidates` — deterministic metadata
- `source_published_at` / `source_updated_at` — deterministic metadata
- `source_independence` — deterministic metadata

同じSnapshotから同一観測値を再記録する場合は`observe_classification()` / `observe_metadata()`で重複rowを抑止する。

## 7. Normalization / Evidence provenance

通常のmain DOM処理では`dom/main.html` Raw ArtifactだけをNormalization Run inputとする。

`include_auxiliary=True`では、main DOMに加えてframe selectionに用いるmetadata、Shadow DOM metadata、実際に取得できたframe DOMをinputへ追加する。

Evidenceは初期F-01では`extraction_mode=normalized`とする。既存`chunks()`の構造情報をEvidence metadataへ保持し、次を独立したEvidence Locationとして保存する。

- `positions[]` -> `dom_path`
- `section` -> `heading_path`
- Evidence ordinal / split start -> `block_order`

これにより、

```text
Evidence -> Normalization Run -> Raw Artifact -> Snapshot -> Source
```

を常に逆引きできる。

## 8. effective Snapshot / Run selection policy

`latest == effective`とはしない。Migration 008でappend-onlyの`source_selection_events`を追加した。

### Snapshot

- Sourceにeffective Snapshotがまだ存在しない場合のみ、最初のusable (`complete`または`partial`) Snapshotを`automatic_initial`として選択する。
- 後続Snapshotはtimestampや新しさだけではeffectiveへ昇格しない。
- `failed` Snapshotはeffectiveへ選択できない。
- operatorが確認した場合はmanual selection eventを追加して切り替える。

### Normalization Run

- effective Snapshotにeffective Runがまだ存在しない場合のみ、最初のsuccessful Runを`automatic_initial`として選択する。
- 後続Runはcompleteであっても自動で既存effective Runを置換しない。
- `failed` Runはeffectiveへ選択できない。
- manual selection eventで切替可能とする。

operator-facing public CLIでは、確認済み世代の切替を次で行う。

```text
sgokb source select-snapshot --source <source-id> --snapshot <snapshot-id> --reason <text>
sgokb source select-run --snapshot <snapshot-id> --run <run-id> --reason <text>
```

これらはRepositoryのmanual selection contractを利用し、SQLite直接操作を要求しない。`latest == effective`へ戻す自動昇格ではなく、operatorの明示判断をselection eventとして記録する。

Selection eventには`origin_kind / reason / created_at`を保持し、旧Snapshot / Run / Evidenceは削除しない。

## 9. Failure behavior

Extractor / chunking等が失敗した場合は、可能な範囲で`status=failed`のNormalization Runを履歴として記録し、既存effective Runは変更しない。

Raw Artifact、既存Run、既存Evidenceの更新・破壊は行わない。

## 10. Legacy coexistence

F-01では既存Prototype dataの意味migrationを行わない。

```text
legacy path:
  Application.import_path / process
  -> sources / snapshots / artifacts / normalized_runs / evidence / page_contexts

canonical path:
  Application.import_source_path / process_source_snapshot
  -> source_records / source_locators / source_snapshots / raw_artifacts
  -> normalization_runs / evidence_records / evidence_locations
```

既存IDのbulk migrationはPhase Lへ残す。

## 11. Test contract

`tests/test_canonical_ingestion.py`で少なくとも次を回帰試験する。

- Capture -> canonical Source / Snapshot / Raw / Run / Evidence成立
- `capture_id`のSnapshot ID維持
- retry idempotency / same ID different Raw reject
- ambiguous locator silent merge拒否 / explicit Source優先
- page URL / canonical URL分離
- completeness / warning /全Raw hash・bytes・logical path保持
- Evidence -> Run -> Raw -> Snapshot -> Source provenance
- DOM / heading / block-order location
- classification / metadata origin
- newer Snapshot / Runの非自動昇格
- failed Runの非昇格
- manual effective selection
- historical generation保持
- canonical処理が生成LLMなしで完了
- legacy ingestion regression維持

## 12. F-02への引継ぎ

canonical Capture -> Evidence経路が独立して成立したため、F-02では標準pipelineからFragment generationを外せる。

F-02では旧Fragment table / `capture.py`等を即時削除せず、Phase Lまで必要なlegacy / research compatibility範囲を決定して隔離する。
