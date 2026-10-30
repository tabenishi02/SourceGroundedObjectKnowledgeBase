"""Presentation-only safety metadata for desktop operations.

P-GUI-07 keeps these rules outside the canonical Application layer. They describe
how an already-public operator request should be presented in the GUI; they do not
change the operation's backend semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

EFFECT_READ = "READ"
EFFECT_DERIVED = "DERIVED"
EFFECT_WRITE = "WRITE"
EFFECT_EXTERNAL = "EXTERNAL"
EFFECT_MAINTENANCE = "MAINTENANCE"


@dataclass(frozen=True, slots=True)
class OperationUXPolicy:
    effect: str
    confirmation_required: bool
    cancellable: bool = False
    note: str = ""


_WRITE_OPERATIONS = frozenset(
    {
        "source.import",
        "source.process",
        "source.select-snapshot",
        "source.select-run",
        "object.add",
        "object.rename",
        "object.status",
        "object.alias.add",
        "object.class.set-primary",
        "object.class.add",
        "object.class.remove",
        "association.set",
        "association.clear",
        "registry.proposal.accept",
        "registry.proposal.reject",
        "registry.proposal.apply",
        "package.stage",
        "result.receive",
        "result.validate",
        "result.import",
    }
)

_DERIVED_OPERATIONS = frozenset({"package.build", "render"})
_EXTERNAL_OPERATIONS = frozenset({"package.export"})
_MAINTENANCE_OPERATIONS = frozenset(
    {
        "mcp.serve",
        "system.derived.sync",
        "system.index.rebuild",
        "system.backup.create",
        "system.backup.composite.create",
        "system.restore.apply",
        "system.restore.composite.apply",
        "generation.bootstrap",
        "generation.build",
        "generation.cutover",
        "generation.rollback",
        "generation.recover",
    }
)

# The accepted P-GUI-01 contract does not require a second modal dialog for every WRITE.
# Explicit Add/Apply/Import buttons already form a commit action. These higher-impact
# writes receive an additional common modal gate.
_STRONG_WRITE_CONFIRMATION_OPERATIONS = frozenset(
    {
        "source.select-snapshot",
        "source.select-run",
        "object.status",
        "association.clear",
        "result.validate",
        "result.import",
    }
)

# Registry Apply already has a dedicated impact confirmation in RegistryPage. Keeping
# that confirmation as the single interactive gate avoids two consecutive dialogs.
_DEDICATED_CONFIRMATION_OPERATIONS = frozenset({"registry.proposal.apply"})

_POSITIONAL_ARGUMENTS: dict[str, tuple[str, ...]] = {
    "source.import": ("path",),
    "object.alias.add": ("value",),
    "object.class.set-primary": ("class_ref",),
    "object.class.add": ("class_ref",),
    "object.class.remove": ("class_ref",),
    "evidence.show": ("evidence_id",),
    "evidence.provenance": ("evidence_id",),
    "evidence.search": ("query",),
    "registry.class.show": ("class_ref",),
    "registry.relation-type.show": ("relation_ref",),
    "registry.proposal.show": ("proposal_ref",),
    "registry.proposal.accept": ("proposal_ref",),
    "registry.proposal.reject": ("proposal_ref",),
    "registry.proposal.apply": ("proposal_ref",),
    "package.stage": ("source",),
    "package.preflight": ("package",),
    "package.export": ("package",),
    "result.receive": ("result",),
    "result.validate": ("receipt_id",),
    "result.review": ("receipt_id",),
    "result.import": ("receipt_id",),
    "version.show": ("version_id",),
    "version.diff": ("before_version_id", "after_version_id"),
    "search": ("query",),
    "system.backup.composite.verify": ("backup",),
    "system.restore.plan": ("backup",),
    "system.restore.apply": ("backup",),
    "system.restore.composite.plan": ("backup",),
    "system.restore.composite.apply": ("backup",),
    "generation.cutover": ("generation_id",),
    "generation.rollback": ("generation_id",),
}

_FLAG_NAMES = {
    "object_id": "object",
}


def operation_policy(operation_id: str) -> OperationUXPolicy:
    """Return the desktop safety presentation policy for one public/advanced operation."""

    if operation_id in _EXTERNAL_OPERATIONS:
        return OperationUXPolicy(
            EFFECT_EXTERNAL,
            True,
            note="This operation sends an artifact outside the local SGOKB workspace.",
        )
    if operation_id in _MAINTENANCE_OPERATIONS:
        note = "Maintenance operation; inspect targets and scope before continuing."
        if operation_id in {"system.restore.apply", "system.restore.composite.apply"}:
            note = (
                "Restore apply can overwrite existing targets and requires explicit "
                "acknowledgement."
            )
        elif operation_id.startswith("generation."):
            note = (
                "Advanced Search Generation maintenance can rebuild or switch the active "
                "Derived Search generation. Inspect generation identity and runtime state first."
            )
        return OperationUXPolicy(EFFECT_MAINTENANCE, True, note=note)
    if operation_id in _WRITE_OPERATIONS:
        confirmation_required = (
            operation_id in _STRONG_WRITE_CONFIRMATION_OPERATIONS
            and operation_id not in _DEDICATED_CONFIRMATION_OPERATIONS
        )
        return OperationUXPolicy(
            EFFECT_WRITE,
            confirmation_required,
            note="This operation can change canonical or audit state.",
        )
    if operation_id in _DERIVED_OPERATIONS:
        return OperationUXPolicy(
            EFFECT_DERIVED,
            False,
            note="Derived output is replaceable and is not GUI Undo for canonical state.",
        )
    return OperationUXPolicy(EFFECT_READ, False, note="Read-only operation.")


def _ps_quote(value: object) -> str:
    text = str(value)
    if text == "":
        return "''"
    special = set(" \t\r\n'\"`$;&|<>()[]{}")
    if any(char in special for char in text):
        return "'" + text.replace("'", "''") + "'"
    return text


def _flag_name(key: str) -> str:
    return "--" + _FLAG_NAMES.get(key, key).replace("_", "-")


def _append_arguments(
    tokens: list[str],
    operation_id: str,
    arguments: Mapping[str, object],
) -> None:
    positional_keys = _POSITIONAL_ARGUMENTS.get(operation_id, ())
    for key in positional_keys:
        value = arguments.get(key)
        if value is not None and value != "":
            tokens.append(_ps_quote(value))

    for key, value in arguments.items():
        if key in positional_keys or value is None:
            continue
        if operation_id.startswith("generation.") and key == "smoke":
            if value is False:
                tokens.append("--no-smoke")
            continue
        flag = _flag_name(key)
        if isinstance(value, bool):
            if value:
                tokens.append(flag)
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                tokens.extend((flag, _ps_quote(item)))
            continue
        tokens.extend((flag, _ps_quote(value)))


def equivalent_cli_command(
    workspace_path: str | Path,
    operation_id: str,
    arguments: Mapping[str, object] | None = None,
) -> str:
    """Render an executable-style CLI equivalent for a GUI operator request.

    The formatter follows the public CLI argument shape. Advanced generation actions
    retain their separate ``python -m sgokb.cli.generation`` entrypoint. The string is
    a presentation aid only; the GUI never uses it as its execution backend.
    """

    arguments = dict(arguments or {})
    if operation_id.startswith("generation."):
        action = operation_id.removeprefix("generation.")
        tokens = [
            "python",
            "-m",
            "sgokb.cli.generation",
            "--db",
            _ps_quote(Path(workspace_path)),
            action,
        ]
    else:
        tokens = ["sgokb", "--db", _ps_quote(Path(workspace_path)), *operation_id.split(".")]
    _append_arguments(tokens, operation_id, arguments)
    return " ".join(tokens)


def confirmation_text(
    workspace_path: str | Path,
    operation_id: str,
    arguments: Mapping[str, object] | None = None,
) -> str:
    """Return the common confirmation body for a safety-sensitive request."""

    policy = operation_policy(operation_id)
    cli = equivalent_cli_command(workspace_path, operation_id, arguments)
    return (
        f"Safety class: {policy.effect}\n"
        f"Operation: {operation_id}\n\n"
        f"{policy.note}\n\n"
        "GUI Undo/Redo only applies to unsubmitted form edits. It never reverses a "
        "submitted canonical operation.\n\n"
        "Equivalent CLI command:\n"
        f"{cli}"
    )
