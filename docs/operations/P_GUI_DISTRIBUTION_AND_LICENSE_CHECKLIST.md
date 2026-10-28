# P-GUI Distribution / License Checklist

Updated: 2026-10-28

- Status: **Accepted checklist / P-GUI-02**
- Applies to: PySide6 / Qt Desktop GUI distribution
- Decision: `docs/decisions/P_GUI_PYSIDE6_APPLICATION_PACKAGING_LICENSE_DECISION.md`
- Design: `docs/design/P_GUI_APPLICATION_ARCHITECTURE.md`

## 1. Purpose

This checklist is the minimum engineering gate before publishing or distributing a packaged SGOKB GUI build.

It is not legal advice. A final legal review remains recommended before public redistribution.

---

## 2. Build environment

- [ ] Build on the intended target platform; initial baseline is Windows x64.
- [ ] Use a clean virtual environment.
- [ ] Record Python version.
- [ ] Record SGOKB source commit.
- [ ] Install release build dependencies from pinned/locked requirements.
- [ ] Record PySide6 version.
- [ ] Record Qt version.
- [ ] Record `pyside6-deploy` / Nuitka version.
- [ ] Use controlled deployment without unexpected package installation during the release build.
- [ ] Keep deployment specification/configuration under version control.

---

## 3. Packaging baseline

- [ ] Use `pyside6-deploy` / Nuitka unless an explicit Decision amendment selected another tool.
- [ ] Use standalone directory mode.
- [ ] Do not use one-file mode for the baseline release.
- [ ] Do not statically link Qt.
- [ ] Confirm Qt shared libraries are separate components in the output.
- [ ] Confirm required Qt platform plugins are present.
- [ ] Confirm no unexpected Qt module was bundled.
- [ ] Confirm the application starts on a clean supported Windows machine/VM.
- [ ] Confirm CLI remains separately usable without the GUI dependency.

---

## 4. Qt module inventory

Initial approved baseline:

```text
QtCore
QtGui
QtWidgets
```

For each packaged release:

- [ ] Produce actual bundled Qt module/library inventory.
- [ ] Compare it with the approved baseline.
- [ ] Review license of every newly introduced Qt module.
- [ ] Review third-party licenses carried by bundled Qt components.
- [ ] Reject accidental large optional modules until reviewed.

---

## 5. LGPL / Qt / PySide6 notices

- [ ] Include the applicable LGPL license text.
- [ ] Explicitly acknowledge use of Qt / PySide6.
- [ ] Include Qt/PySide6 version information.
- [ ] Include required third-party license notices for bundled components.
- [ ] Provide durable corresponding-source availability / written-offer instructions appropriate to the bundled LGPL components.
- [ ] If Qt/PySide6 LGPL-covered source was modified, make the corresponding modified source available as required.
- [ ] Do not impose terms that prohibit user replacement/relinking of LGPL libraries.
- [ ] Do not prohibit reverse engineering where LGPL requires it for debugging modifications to the library.
- [ ] Verify the standalone package permits replacement of the separate Qt shared libraries in practice or provides the required relinking mechanism/information.

Suggested artifact files:

```text
LICENSES/
  LGPL-3.0.txt
  ... actually applicable third-party licenses ...
THIRD_PARTY_NOTICES.md
QT_PYSIDE_SOURCE_OFFER.md
BUILD_MANIFEST.json
```

Do not copy unrelated licenses merely because they exist upstream; inventory what is actually used/bundled.

---

## 6. SGOKB project license gate

Current repository state at P-GUI-02:

```text
root LICENSE file = absent
project OSS license = not formally selected
```

Before public OSS publication:

- [ ] Create an explicit project-license Decision.
- [ ] Add root `LICENSE`.
- [ ] Ensure README accurately names the SGOKB application license.
- [ ] Ensure application license is compatible with the selected Qt/PySide6 usage model and all shipped dependencies.
- [ ] Ensure source-distribution metadata includes the project license.

Private development and internal test packaging are not blocked by the absence of a public project license; public OSS publication is blocked.

---

## 7. Build manifest

Every formal GUI artifact should include or be accompanied by a build manifest containing at least:

```text
SGOKB version
Git commit SHA
build timestamp
build OS / architecture
Python version
PySide6 version
Qt version
Nuitka/deployment version
bundled Qt modules
bundled package inventory or SBOM reference
artifact SHA-256
```

- [ ] Manifest is generated from the actual build, not copied manually from expected versions.
- [ ] Artifact hash is computed after final packaging.

---

## 8. Functional smoke gate

- [ ] `SGOKB.exe` launches without a console dependency.
- [ ] Workspace DB can be opened.
- [ ] Read-only Object list/show works.
- [ ] One safe WRITE smoke operation works on disposable test data.
- [ ] GUI closes cleanly with no backend thread left running.
- [ ] Semantic-runtime-disabled GUI still launches.
- [ ] Missing Qdrant produces runtime/degradation UI rather than startup failure.
- [ ] CLI still operates on the same DB after GUI exit.

---

## 9. Threading / shutdown gate

- [ ] QWidget objects are only created/mutated on the Qt main thread.
- [ ] Backend Repository is created on the backend thread.
- [ ] No live SQLite connection crosses threads.
- [ ] No `check_same_thread=False` shared-connection workaround was introduced without a new Decision.
- [ ] No normal shutdown path calls `QThread.terminate()`.
- [ ] Non-cancellable mutation prevents unsafe application shutdown.
- [ ] Worker thread is stopped and joined/finished before application process exit.

---

## 10. Dependency / supply-chain gate

- [ ] Generate dependency inventory for the packaged artifact.
- [ ] Review licenses of newly introduced Python dependencies.
- [ ] Review licenses of build/runtime components that are actually redistributed.
- [ ] Verify no proprietary/commercial-only Qt package was accidentally mixed into a Community Edition build.
- [ ] Store dependency versions with the release evidence.

---

## 11. Release artifact gate

Initial acceptable public artifact form:

```text
sgokb-<version>-windows-x64.zip
  -> standalone SGOKB directory
```

- [ ] Archive opens without path corruption.
- [ ] Executable and Qt DLLs remain separate inside the archive.
- [ ] License/notice files are present.
- [ ] Build manifest is present.
- [ ] Release note states Windows support baseline and required external runtime components such as Qdrant where applicable.

Installer, code signing and auto-update are not required by P-GUI-02 and must not silently become release blockers unless a later Decision adds them.

---

## 12. Evidence retention

For each formal GUI release, retain:

- build command/config
- deployment spec
- exact dependency lock/constraints
- build manifest
- license inventory
- smoke-test result
- artifact SHA-256
- release commit/tag association

These artifacts support reproducibility and license compliance review.
