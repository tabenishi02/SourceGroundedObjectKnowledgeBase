# M-05 Historical Derived Reconciliation

更新日: 2026-10-27

- 対象: SGOKB happy-path acceptance / Section M
- 種別: M-05 blocker remediation / operator contract
- 関連: `SGOKB_HAPPY_PATH_ACCEPTANCE_TEST_PROCEDURES.md`
- CLI surface: `system derived sync --object <object-id>`

---

## 1. 問題

accepted Knowledge Versionはimmutableであり、explicit `search --version <version-id>`によってhistorical scopeを指定できる。

一方、従来のincremental derived maintenanceは、Objectのmutable `object_derived_states`が指すcurrent VersionだけをSearch Representationへmaterializeしていた。

そのため、次の正常系でもhistorical accepted VersionがLexical Search不能になり得た。

```text
V1 accepted
  -> derived syncを実行しない
V2 accepted/current
  -> mutable derived targetがV2へ進む
V2 derived sync
  -> V2 membershipのみ生成
  -> V1 acceptedだがmembershipなし
```

これはcanonical Knowledgeやhistorical search filterの破損ではなく、derived maintenance coverageの不足である。

---

## 2. 修正後contract

`system derived sync --object <object-id>`は、mutable lifecycle stateをcurrent Version revisionへanchorしたまま、そのObjectに属する**全accepted Version履歴**をreconcileする。

対象Version:

- `accepted`: 対象
- `candidate`: 対象外
- `abandoned`: 対象外

Search Representation stageは、各accepted Versionをactive generation contractに従ってidempotentにmaterializeする。

```text
Object
├─ V1 accepted       -> reconcile
├─ V2 accepted/current -> reconcile
└─ V3 candidate      -> ignore
```

current mutable derived stateがすでに`ready`でも、historical membership欠落の可能性があるため、Search Representation reconciliationそのものは実行する。

同一membershipがすでに存在する場合は再利用し、重複を生成しない。

`changed`は、current derived stateが未READYだった場合、またはaccepted-history membership setが実際に変化した場合にtrueとなる。完全reconcile済みの再実行ではfalseとなる。

---

## 3. Semantic contract

`--semantic-runtime`付きderived syncでは、Search Representationだけでなく、active generationに属する全accepted-history membershipのRepresentationをEmbedding対象とする。

これにより、historical Search Representationを後からbackfillしても、Vector maintenanceがmissing historical Embeddingによって失敗しない。

Vector Index stageは既存contractどおり、そのObjectのaccepted membershipsをupsertし、historical pointを保持しつつ`is_current` metadataを更新する。

---

## 4. 保持するinvariant

今回の修正では次を変更しない。

- canonical Knowledge Versionはimmutable。
- Result Import transaction内でderived artifactを生成しない。
- `object_derived_states.target_version_id`はcurrent Versionを指す。
- revision guardはcurrent revisionを基準にする。
- active Search generation境界を越えてmembershipを混在させない。
- historical syncのために新しいCLI `--version`は追加しない。

したがって、derived stateの`ready`は次の意味として扱う。

> current Version revisionに対して、そのObjectのaccepted Knowledge historyが現在のderived contractへreconcile済みである。

---

## 5. Existing acceptance DBのbackfill

M-05 blockerが発生した既存acceptance DBでは、canonical SQLite stateを手動編集しない。

修正版CLIでOBJ-Aを再syncする。

```powershell
$DerivedBackfillM05 = .\.venv\Scripts\sgokb.exe --db $Db system derived sync `
  --object $ObjectAId | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
  throw "M-05 historical derived backfill failed"
}

$DerivedBackfillM05.data
```

Core Lexical acceptanceでは`--semantic-runtime`は不要である。

確認:

- current derived targetは`$Version2Id`のまま。
- `search_representation.status = ready`。
- V1/V2 canonical Knowledgeは変更されない。
- `$Version1Id`のSearch Representation membershipが生成される。
- 再度同じsyncを実行してもmembership duplicateを生成しない。

---

## 6. Revised M-05 acceptance procedure

V1-only searchable termの存在をfixture要件にはしない。

### M-05A common Knowledge termでscopeを比較

V1とV2双方のaccepted searchable Knowledgeに存在するtermを選ぶ。

```powershell
$CommonTermM05 = "<term present in both V1 and V2 searchable Knowledge>"

$CurrentM05 = .\.venv\Scripts\sgokb.exe --db $Db search `
  $CommonTermM05 --mode lexical | ConvertFrom-Json

$HistoricalM05 = .\.venv\Scripts\sgokb.exe --db $Db search `
  $CommonTermM05 --mode lexical --version $Version1Id | ConvertFrom-Json
```

PASS:

- normal searchのOBJ-A resultは`version_id = $Version2Id`。
- explicit historical searchのOBJ-A resultは`version_id = $Version1Id`。
- historical resultがcurrent V2へ解決されない。

### M-05B current-specific Knowledge termの非漏洩を確認

V2 searchable Knowledgeに存在し、V1 searchable Knowledgeには存在しないtermを選ぶ。

```powershell
$CurrentSpecificTermM05 = "<term present in V2 but not V1 searchable Knowledge>"

$CurrentSpecificM05 = .\.venv\Scripts\sgokb.exe --db $Db search `
  $CurrentSpecificTermM05 --mode lexical | ConvertFrom-Json

$HistoricalSpecificM05 = .\.venv\Scripts\sgokb.exe --db $Db search `
  $CurrentSpecificTermM05 --mode lexical --version $Version1Id | ConvertFrom-Json
```

PASS:

- normal searchは期待するV2 Knowledgeを返す。
- explicit V1 searchはV2-only KnowledgeをV1 resultとして返さない。

この2試験によって、normal search=current accepted scope、explicit `--version`=historical accepted scope、かつcurrent Knowledgeのhistorical leakageなしを確認する。

---

## 7. Regression requirements

自動回帰試験では最低限、次を固定する。

1. V1 accepted / unsynced -> V2 accepted後のsyncでV1/V2双方をmaterializeする。
2. reconciliation再実行はidempotentでduplicate membershipを生成しない。
3. candidate / abandoned Versionをmaterializeしない。
4. explicit V1 lexical searchがV1を返す。
5. V2-only Knowledgeがexplicit V1 searchへ漏れない。
6. semantic syncがbackfilled accepted-history RepresentationすべてにEmbeddingを用意する。
7. Vector syncがV1/V2双方をindexし、`is_current` metadataを正しく表す。
