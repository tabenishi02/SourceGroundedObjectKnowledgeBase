# P-GUI-06 — Derivation Kind Selector Improvement

Updated: 2026-10-29

- Phase: `Phase P — GUI / RAW Grounding / Runtime Modernization`
- Task: `P-GUI-06 [P0] Search / Similarity / Registry / Version GUI`
- Status: **Implemented / Automated Verification Refresh Pending / Interactive Smoke Pending**
- Previous automated authority: `P_GUI_06_DYNAMIC_VERIFICATION_ATTEMPT_02.md`

## Request

Replace the free-text Search Hard Filter for `Derivation kind` with a dropdown because the
search contract accepts a fixed vocabulary.

## Fixed values

The selector contains:

```text
Any
 direct_statement
 synthesis
 interpretation
 reported_view
```

`Any` means that no `derivation_kind` argument is sent to the Search operation.

The four non-empty values are the schema-defined Derivation Kind vocabulary used by accepted
Knowledge Statements:

- `direct_statement`
- `synthesis`
- `interpretation`
- `reported_view`

The selector is intentionally non-editable so an operator cannot submit an unsupported value from
the GUI.

## Implementation

Added:

```text
src/sgokb/gui/views/search_page_derivation.py
```

The amendment subclasses the existing P-GUI-06 Search page and replaces only the Derivation Kind
field with a fixed `QComboBox`. The existing `run_search()` implementation and operator argument
contract remain unchanged.

Updated:

```text
src/sgokb/gui/views/__init__.py
```

The views package patches the Search page module symbol before importing `MainWindow`, so the
normal `sgokb-gui` entry path and `from sgokb.gui.views import SearchPage` both receive the amended
page without duplicating Search behavior.

No Repository query, new public operation, canonical write path, or Search semantic change was
introduced.

## Regression coverage

Added:

```text
tests/test_p_gui_06_derivation_kind_selector.py
```

The test verifies:

1. the Derivation Kind control is a non-editable `QComboBox`;
2. the candidates are exactly `Any` plus the four allowed values;
3. choosing `interpretation` submits `derivation_kind=interpretation`;
4. choosing `Any` omits the `derivation_kind` argument.

## Verification state

The previous P-GUI-06 automated PASS was measured before this amendment:

```text
focused regression = 18 / 18 PASS
Ruff               = PASS
full pytest         = 813 / 813 PASS
known local-Qdrant warnings = 2
```

That result remains historical evidence but does not certify the Derivation Kind selector code
added here. Until refreshed automated verification passes, this amendment is the current status
authority for P-GUI-06 and supersedes the earlier automated-PASS disposition for closure purposes.

Current disposition:

```text
implementation                 = Complete
desk audit                     = Complete
automated verification refresh = Pending
interactive smoke              = Pending
```

Therefore:

```text
P-GUI-06 = Automated Verification Refresh Pending / Interactive Smoke Pending
```
