# P-GUI-09 — MCP stdio Lifecycle Decision

Date: 2026-10-30
Status: **Decision / P-GUI-09 implementation authority**

## Decision

The current SGOKB MCP server uses stdio transport. For this transport, the MCP server process lifecycle is owned by the external MCP client/launcher that creates the child process and connects to its stdin/stdout.

P-GUI-09 therefore does not create a detached GUI-owned `mcp serve` process and does not expose misleading Start/Stop controls for such a process.

The GUI System / MCP surface provides:

- current Workspace binding;
- semantic-runtime configuration;
- current lifecycle/ownership explanation;
- exact `sgokb --db <workspace> mcp serve [--semantic-runtime]` launch command;
- copy-to-clipboard support for client configuration.

The MCP read-only capability contract is unchanged. No canonical write tool is added.

## Rationale

With stdio, the process's stdin/stdout are the transport connection. A detached process started by the SGOKB GUI would not expose a network/socket endpoint to which an unrelated MCP client could later attach. Reporting such a process as a useful running MCP server would therefore be incorrect lifecycle semantics.

This decision resolves the earlier P-GUI-01 requirement to finalize MCP lifecycle in P-GUI-09. It interprets the initial capability-matrix `start/stop lifecycle support` placeholder according to the actual current transport rather than inventing a second transport or supervisor.

## Lifecycle contract

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

## Future change boundary

A future socket/HTTP MCP transport or explicit process-supervisor protocol may support meaningful GUI-owned Start/Stop controls. Such a change requires a separate transport/lifecycle contract and is not introduced by P-GUI-09.

## Compatibility

This decision preserves:

- the public `mcp serve` CLI operation;
- the public 67-operation parity count;
- the current read-only MCP adapter;
- GUI-R-141 no hidden canonical capability;
- GUI-R-151 Equivalent CLI is presentation only;
- the transport-specific separation of `mcp.serve` from synchronous `OperatorSession`.
