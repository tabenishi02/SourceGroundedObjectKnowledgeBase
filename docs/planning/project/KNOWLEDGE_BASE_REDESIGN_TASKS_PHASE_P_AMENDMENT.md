# Knowledge Base Redesign Tasks — Phase P Amendment

Updated: 2026-10-28

- Status: **Historical Phase P kickoff amendment**
- Applies after: Phase O closure and SGOKB v1.1.0 happy-path acceptance
- Supersedes: project-wide task masterの「Next = Phase O」等の古いnext-task記述
- Detailed plan: `../phases/P/PHASE_P_MODERNIZATION_PLAN.md`
- Detailed tasks: `../phases/P/PHASE_P_TASKS.md`
- Current-state authority: `../phases/P/PHASE_P_STATUS.md`
- Note: Phase P is now complete/released as `v2.0.0`; the kickoff state below is retained as historical planning context and is not the current task state.

## Historical kickoff project-state snapshot

```text
Phase A ... Phase M = Complete
Phase N = Complete / PASS
Phase N closure audit = Complete / PASS
Phase O = Complete
Happy-path operational acceptance = Complete / FULL SGOKB PASS
Current formal release = v1.1.0
Phase P = Planned / Ready to Start
Next = P-GUI-01 — GUI requirements / compatibility contract
```

Project-wide `KNOWLEDGE_BASE_REDESIGN_TASKS.md`にはPhase O以前のhistorical next-task記述が残っている。本amendment以後、Phase Pのcurrent task stateについては本書と`docs/planning/phases/P/`配下を優先する。

## Phase P scope

Phase Pは次の3 Workstreamを実施する。

1. **GUI — highest priority**
   - PySide6 Desktop GUI
   - public `sgokb` CLIとのsemantic compatibility
   - CLI / GUI共通Application / Service boundary
   - GUI-specific workflow / preview / progress / safety機能

2. **RAW Grounding — second priority**
   - Evidenceをselection単位として維持
   - Evidence provenanceからRaw Artifactを解決
   - Raw ArtifactをExternal AIへ渡すPackageへ変更
   - Package / Result / Validation / Review / Import grounding contractを更新

3. **Runtime — third priority**
   - Windowsログイン後のQdrant自動起動
   - independent shared runtimeとして運用
   - runtime health/status boundary
   - GUI Runtime Dashboard

## Phase P task families

```text
P-GUI-01 .. P-GUI-10
P-RAW-01 .. P-RAW-06
P-RUNTIME-01 .. P-RUNTIME-06
P-CLOSE-01
```

個別Taskのscope / dependency / completion criteriaは`PHASE_P_TASKS.md`を正本とする。

## Priority / dependency rule

優先度はGUI > RAW Grounding > Runtimeとする。

ただしPackage / Result GUIはRAW contractに依存するため、GUI foundation / Object / Source / Evidence / Search等を先行し、Package / Result GUIはP-RAW完了後に実装する。

## First task

```text
P-GUI-01 [P0] GUI requirements / compatibility contract
```
