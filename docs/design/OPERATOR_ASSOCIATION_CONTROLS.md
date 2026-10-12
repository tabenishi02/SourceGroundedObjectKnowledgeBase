# Operator Association / Evidence Selection Controls

更新日: 2026-10-12

## 1. 目的

F-05では、F-03 Object Evidence RetrievalとF-04 bounded Evidence Selectionに対して、人間が明示的にSource↔Object associationとEvidence include / excludeを操作できる標準Application / CLI境界を定義する。

対象は次の2種類であり、同一概念として扱わない。

1. **Source↔Object association**: `source_object_associations`に永続化するObjectごとのSource関係。
2. **Evidence selection override**: 1回のRetrieval / Package Selection入力として与える`manual_include / manual_exclude`。

Knowledge Version内のStatement / Attribute / Relationを根拠Evidenceへ結ぶ`evidence_links`は別責務であり、F-05 operator controlから直接編集しない。

## 2. Source↔Object association

既存schemaをそのまま正本とする。

```text
source_id + object_id
  status = candidate | confirmed | excluded
  subject_relationship
  origin_kind
  note
  created_at / updated_at
```

### status semantics

- `candidate`: 関連候補。F-03ではexplicit association signalとして利用する。
- `confirmed`: operatorまたは一意なdeterministic ruleで関連確認済み。F-03でcandidateより強いsignalとして利用する。
- `excluded`: 当該Objectの通常自動RetrievalからSourceを除外する。

`clear`はassociation rowを解除し、「関係なし」を意味する。`excluded`とは異なる。明示的に除外したい場合はstatusを`excluded`にする。

CLIから作成・更新するassociationは`origin_kind=manual`に固定する。opaqueな生成AI判断だけで`confirmed`へ昇格させない。

## 3. subject_relationship

`subject_relationship`はSource全体の固定属性ではなく、Source↔Object associationごとのcontextual metadataとして保持する。

例:

```text
main_subject
mentioned_subject
first_party
independent
reference
```

F-05ではclosed enumを導入しない。既存要件どおり自由文字列として保持し、将来registry化が必要になった場合は別Taskで行う。

## 4. 自動候補と人間判断の境界

`association suggest`はF-03 retrieval結果をSource単位へ集約して候補を表示する。

候補生成signal:

- name / alias
- Source metadata
- lexical FTS
- semantic retrieval（明示指定時）
- 既存candidate / confirmed association

suggestionは**read-only**である。検索候補を表示しただけでは`source_object_associations`へ書き込まない。

operatorは候補確認後、`association set`で`candidate / confirmed / excluded`を明示保存する。

## 5. Evidence manual include / exclude

Evidence単位のoperator overrideはPackage selection controlとして扱う。

```text
--include-evidence <evidence_id>
--exclude-evidence <evidence_id>
```

- includeはF-03の`manual` selection reasonを追加する。
- historical Evidenceも明示include可能。
- F-04ではinclude対象をprotected Evidenceとして扱う。
- excludeは自動candidateであっても今回のselectionから除外する。
- override集合は`controls.manual_include / manual_exclude`として出力へ残す。

このoverrideをcanonical Evidence StoreやKnowledge `evidence_links`へ永続書き込みしない。Packageはderived artifactであり、Packageごとに再指定・再構築できることを優先する。

## 6. Application API

F-05で追加する標準API:

```text
Application.list_source_object_associations(object_id)
Application.set_source_object_association(
    object_id,
    source_id,
    status,
    subject_relationship=None,
    note=None,
)
Application.clear_source_object_association(object_id, source_id)
Application.suggest_source_associations(
    object_id,
    max_candidates=500,
    semantic=None,
    semantic_batch_size=32,
)
```

Evidence operator overrideは既存F-03/F-04 APIを利用する。

```text
Application.retrieve_object_evidence(..., manual_include=..., manual_exclude=...)
Application.select_object_evidence(..., manual_include=..., manual_exclude=...)
```

将来GUIを追加する場合もSQLiteを直接編集せず、このApplication APIを利用する。

## 7. CLI contract

### Association一覧

```text
sgokb association list --object <object_id>
```

### 自動候補表示

```text
sgokb association suggest --object <object_id>
sgokb association suggest --object <object_id> --semantic
```

semanticは明示指定時だけEmbedderを必要とし、provider failure時にcloudへsilent fallbackしない。

### Association保存 / 更新

```text
sgokb association set \
  --object <object_id> \
  --source <source_id> \
  --status confirmed \
  --subject-relationship main_subject \
  --note "operator verified"
```

### Association解除

```text
sgokb association clear --object <object_id> --source <source_id>
```

### Evidence candidate確認

```text
sgokb evidence candidates \
  --object <object_id> \
  --include-evidence <evidence_id> \
  --exclude-evidence <evidence_id>
```

### bounded selection確認

```text
sgokb evidence select \
  --object <object_id> \
  --include-evidence <evidence_id> \
  --exclude-evidence <evidence_id> \
  --max-estimated-tokens 12000 \
  --max-bytes 65536 \
  --max-items 64
```

## 8. UI境界

F-05では新しいdesktop GUI frameworkは導入しない。

理由:

- Phase MでObject中心CLI / 操作フローを再編する予定がある。
- 現時点で必要なのはoperator semanticsとApplication APIの確定である。
- GUIを先に作ると旧Prototype Entity操作とcanonical Object操作を二重実装しやすい。

したがってF-05の初期operator surfaceはCLIとし、将来GUIは同じApplication APIへ接続する。

## 9. Legacy Entityとの境界

既存`entity link`は旧PrototypeのEntity↔legacy Evidence操作であり、F-05 canonical associationとは別物である。

F-05ではこれを削除・再利用しない。Phase L / Mでlegacy CLIを整理するまで明示的に共存させる。

canonical F-05操作は必ず次を使用する。

```text
association ...
evidence candidates ...
evidence select ...
```

## 10. 検証条件

F-05完了時に次を満たす。

1. operatorがSource↔Object associationをlist / set / clearできる。
2. `candidate / confirmed / excluded`を保存・更新できる。
3. `subject_relationship` / note / timestampを確認できる。
4. `association suggest`がF-03候補をSource単位で提示する。
5. suggestion表示だけではassociationを永続化しない。
6. `confirmed / candidate`がF-03 explicit association signalとして働く。
7. `excluded`が通常RetrievalからSourceを除外する。
8. Evidence manual include / excludeをCLIからF-03/F-04へ渡せる。
9. manual includeがF-04 protected Evidenceとして保持される。
10. Source associationとKnowledge `evidence_links`を混同しない。
11. legacy `entity link`へcanonical処理を依存させない。
12. Generative LLMを必要としない。

F-05完了によりPhase FのTaskはすべて完了する。次TaskはG-01 `Object Evidence Package formatを確定する` とする。
