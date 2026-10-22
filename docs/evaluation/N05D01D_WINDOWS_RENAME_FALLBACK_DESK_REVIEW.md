# N05D-01D — Windows rename fallback desk review

更新日: 2026-10-22

- Parent: `N05D-01 — Qdrant storage/path diagnosis`
- Status: **Desk review complete; Reference Workstation correlation pending**
- Source run: `20261022T191928+0900`
- Source HEAD: `fd8746445f855ac0f6adfa905b9f3d9504b8316d`

## 1. Question

N05D-01Cでは、external storage `C:\Qdrant\SGOKB` 上のindexed lifecycle stressが50/50 API PASSした一方、ProcMonでは各collection cleanup時に `qdrant.exe SetRenameInformationFile -> ACCESS DENIED` を50件観測した。

この50件が未回復のQdrant defectなのか、Windows/Rust rename fallbackの途中経過なのかをdesk reviewする。

## 2. Qdrant 1.19.2 delete semantics

Qdrant v1.19.2の `safe_delete_in_tmp()` は、対象directoryをtemporary `.deleted` directoryへ `fs::rename(path, &to_delete)?` でrenameする。

Collection delete pathでも `safe_delete_in_tmp(&collection_path, &safe_delete_path)?` として呼び出されるため、この `fs::rename` が最終的にErrならdelete APIはその場でerrorへ伝播する。

その後の `to_delete.close()` はbackgroundで行われるが、collection rootから `.deleted` への最初のrename自体はAPI成功前に同期的に完了する必要がある。

したがって、N05D-01Cの50/50 delete API PASSは、50 cycleすべてで `fs::rename` が最終的にはOkを返したことを強く示す。

## 3. Rust Windows rename semantics

現行Rust標準ライブラリのWindows `std::fs::rename` は、まず `MoveFileExW(..., MOVEFILE_REPLACE_EXISTING)` を試す。

このprimary renameが `ERROR_ACCESS_DENIED` で失敗した場合、sourceをDELETE accessで開き、`SetFileInformationByHandle(FileRenameInfoEx)` と `FILE_RENAME_FLAG_REPLACE_IF_EXISTS | FILE_RENAME_FLAG_POSIX_SEMANTICS` を使用するfallback renameを試す。

fallbackが成功すれば `std::fs::rename` はOkを返す。fallbackまで失敗した場合のみ元のACCESS_DENIEDをErrとして返す。

この実装は、Windowsのtraditional rename semanticsがopen file/handle条件でACCESS_DENIEDになり得る問題を緩和するためのものである。

## 4. Interpretation of N05D-01C 50 ACCESS DENIED events

N05D-01Cでは:

- collection delete API: 50/50 PASS
- terminal API failure: 0
- surfaced client/server OS error 5: 0
- each cycleでcollection cleanup root renameにProcMon ACCESS DENIED: 1件
- Code.exe external storage access: 0

という組み合わせだった。

Qdrant v1.19.2の同期error propagationとRust Windows rename fallbackを合わせると、最有力説明は次である。

```text
Qdrant safe_delete_in_tmp
  -> Rust std::fs::rename
     -> MoveFileExW primary attempt
        -> ACCESS DENIED
     -> FileRenameInfoEx + POSIX semantics fallback
        -> SUCCESS
  -> Qdrant delete API PASS
```

50 cycleすべてで1件ずつACCESS DENIEDが観測され、APIは50/50 PASSしたという規則性は、random external-reader contentionだけよりもこのfallback sequenceと強く整合する。

## 5. Gate implication

現行N05D-01C acceptanceの

```text
ProcMon qdrant.exe ACCESS DENIED = 0
```

は、Windows/Rust内部で回復済みのprimary rename attemptまでfailure扱いするため、system correctness Gateとして過剰である可能性が高い。

Gateを変更する前にReference Workstation raw PML/CSVで、各ACCESS DENIED eventが同じcollection cleanupについて後続のsuccessful renameへ対応することを確認する。

確認後の候補Gate:

```text
unrecovered collection rename failure = 0
delete API failure = 0
surviving collection directory after successful delete = 0
Qdrant server error caused by cleanup rename = 0
surfaced OS error 3/5 = 0
```

ProcMonのrecoverable primary ACCESS DENIED件数はdiagnostic observationとして記録するが、それ単独をFAIL条件にはしない。

## 6. Original N-05 failureとの関係

このdesk reviewはN05D-01C cleanup renameの50件を説明するものであり、formal N-05のpayload-index preparation中にsurfaceしたOS error 3/5を直接説明したものではない。

Qdrant upstream issue #10806では、Windows上でpayload-index/segment fileへのexternal/security reader accessとrenameが競合し、Qdrant-levelで最終的なPermissionDeniedがsurfaceする事象が報告されている。

したがって次の2状態を区別する必要がある。

```text
A. primary Windows rename ACCESS DENIED -> Rust fallback SUCCESS
   = recovered internal event

B. primary rename ACCESS DENIED -> fallback/retry pathも失敗 -> Qdrant error
   = actual runtime defect
```

N05D-01CはAを50 cycleで観測した可能性が高い。Formal N-05の元障害はBまたはpath-length related OS error 3であった可能性が残る。

## 7. Required local validation

Reference Workstationでrun `20261022T191928+0900` のraw ProcMon evidenceを再解析し、50件それぞれについて次を相関する。

1. ACCESS DENIED eventのtimestamp/source/destination。
2. 同一source/destinationまたは同一collectionに対する直後のrename SUCCESS。
3. ACCESS DENIED直後のDELETE-access CreateFile等、Rust fallbackと整合するevent sequence。
4. delete API response timestamp/status。
5. collection source directory消滅と `.deleted` target lifecycle。
6. Qdrant server logにterminal delete errorがないこと。
7. 可能ならPML stackで `MoveFileExW` / `SetFileInformationByHandle` の区別。

50/50がrecoverable fallback sequenceと確認できれば、N05D-01C Gateをevidence-basedに修正し、external storage runtime cutover/post-switch Derived Search smokeへ進む候補とする。

確認できないeventがある場合はBLOCKEDを維持する。

## 8. Current verdict

- **N05D-01 = BLOCKED / Not Complete** を維持する。
- WSL2移行はまだ実施しない。
- 先にN05D-01D local rename-outcome correlationを行う。
- Security設定は変更しない。
- N05D-02 / formal N-05 rerunは開始しない。
