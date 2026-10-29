# P-GUI-08 — Package / Result GUI Acceptance

Status: **PASS / Complete / Accepted**

Date: 2026-10-30

## Accepted implementation source

```text
branch source SHA        = 3015c01aaaecfe5800032ef25b7c9d92cb30e635
PR synthetic merge SHA  = 4010fd93efe4e04f20acff8b98068593d0ac44b5
GitHub Actions PR run    = 40945757254
GitHub Actions push run  = 40945748017
```

The temporary acceptance workflow was removed after the evidence below was captured and is not part of the intended main-branch deliverable.

## Environment

```text
OS             = Microsoft Windows Server 2025
runner image   = windows-2025-vs2026
image version  = 20261021.278.1
Python         = 3.10.11
Qt platform    = offscreen
```

## Final gate

PR synthetic merge run `40945757254`:

```text
P-GUI-08 focused acceptance = 4 / 4 PASS      (4.12s)
GUI regression              = 38 / 38 PASS    (21.88s)
Ruff src/tests              = PASS
full repository regression  = 837 / 837 PASS  (801.44s / 13:21)
warnings                    = 2 known local-Qdrant warnings
```

The independent branch-source run `40945748017` also completed successfully:

```text
P-GUI-08 focused acceptance = 4 / 4 PASS      (4.37s)
GUI regression              = 38 / 38 PASS    (23.75s)
Ruff src/tests              = PASS
full repository regression  = 837 / 837 PASS  (898.58s / 14:58)
warnings                    = 2 known local-Qdrant warnings
```

Known warnings are the existing local-Qdrant warnings:

1. payload indexes have no effect in local Qdrant except supported text-index behavior;
2. local-mode exact search ignores `search_params` except `idf`.

No P-GUI-08 failure remains.

## Focused acceptance coverage

### A1 — explicit Package version routing

PASS.

The GUI selects the accepted Raw-grounded v2 path explicitly and can explicitly select the v1 compatibility path. The shared omitted-version Application/CLI default remains unchanged.

### A2 — Raw and grounding identity presentation

PASS.

The GUI projection exposes `raw_artifact_id`, Raw package path, hash/materialization metadata, and Raw grounding reference changes.

### A3 — MainWindow integration

PASS.

The real desktop MainWindow hosts concrete Package and Result pages in place of the former placeholders.

### A4 — real GUI round trip

PASS.

The focused acceptance executes:

```text
Package v2 build
  -> Raw inclusion / binding presentation
  -> stage
  -> preflight allow
  -> acknowledged external export
  -> Result detect
  -> receive
  -> validate
  -> review / Raw grounding diff
  -> import
  -> accepted Version
```

The imported v2 Version is required to contain Raw grounding links and zero synthesized Evidence claim links.

## Historical remediation record

Three non-product or presentation-only issues were discovered while constructing the gate:

1. Receipt refresh overwrote the explicit post-receive lifecycle label. The GUI lifecycle presentation was corrected.
2. The first Result v2 test fixture used an invalid text-quote locator shape. It was corrected to the accepted `kind=text_quote` / `exact` locator contract. Validation itself behaved correctly.
3. The first lint-complete attempt contained five line-length-only findings in the Package/Result presentation module. A narrowly scoped per-file E501 exception was added, consistent with existing contract-heavy module exceptions; no global lint rule was weakened.

None of these changes altered the accepted P-RAW Package v2 / Result v2 semantic contract.

## Acceptance disposition

```text
P-GUI-08 = Complete / Accepted
```

The accepted P-RAW Package / Result workflow is now available through the desktop GUI while preserving the shared CLI/Application compatibility boundary.

This acceptance is automated functional/contract acceptance. Final GUI-wide parity and usability closure remains owned by P-GUI-10; no separate P-GUI-08 manual interactive-smoke claim is made here.
