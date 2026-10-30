# GUI CLI Capability Matrix — P-GUI-09 Amendment

Date: 2026-10-30
Status: **Normative P-GUI-09 amendment**
Baseline: `docs/reference/GUI_CLI_CAPABILITY_MATRIX.md`
Decision authority: `docs/decisions/P_GUI_09_MCP_STDIO_LIFECYCLE_DECISION.md`

## Purpose

The P-GUI-01 baseline capability matrix intentionally deferred the exact MCP lifecycle design to P-GUI-09 and described row 53 using the placeholder phrase `start/stop lifecycle support`.

P-GUI-09 has now resolved the actual transport/lifecycle semantics. This amendment supersedes only the lifecycle wording of MCP row 53; it does not change the public operation inventory or the 67-operation parity count.

## Amended MCP row 53

| # | CLI operation | Key controls | Side effect | GUI surface | Required GUI capability |
|---:|---|---|---|---|---|
| 53 | `mcp serve` | semantic-runtime | READ service / runtime | System / MCP | read-only MCP lifecycle/ownership state, external-client-owned stdio serve configuration/command, semantic mode display |

MCP parity remains **1 / 1 assigned**.

## Lifecycle interpretation

```text
transport                     = stdio
server process owner          = external MCP client / launcher
GUI observes/configures       = yes
GUI displays serve command    = yes
GUI detached start            = no
GUI stop external client      = no
GUI close stops MCP           = no implied relationship
semantic runtime option       = configurable
canonical MCP write surface   = none
```

For stdio, the useful MCP client connection is the server child process's stdin/stdout. A detached GUI-started process would not expose a later-connectable endpoint and therefore must not be represented as a running MCP daemon.

## P-GUI-10 use

P-GUI-10 must evaluate MCP row 53 against this amendment together with the P-GUI-01 baseline matrix. The remaining 66 public rows and the separate six-action Advanced Search Generation inventory are unchanged by this amendment.
