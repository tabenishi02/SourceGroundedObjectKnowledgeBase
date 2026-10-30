from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "runtime" / "qdrant" / "windows" / "Register-SgokbQdrantAutoStart.ps1"
VERIFY = ROOT / "runtime" / "qdrant" / "windows" / "Test-SgokbQdrantAutoStart.ps1"
OPERATIONS = ROOT / "docs" / "operations" / "P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md"
DECISION = ROOT / "docs" / "decisions" / "P_RUNTIME_01_WINDOWS_QDRANT_RUNTIME_DECISION.md"


def test_registration_asset_preserves_external_native_windows_lifecycle_boundary() -> None:
    text = REGISTER.read_text(encoding="utf-8")

    assert "New-ScheduledTaskTrigger -AtLogOn" in text
    assert "New-ScheduledTaskAction" in text
    assert "New-ScheduledTaskPrincipal" in text
    assert "-LogonType Interactive" in text
    assert "-RestartCount $RestartCount" in text
    assert "-RestartInterval (New-TimeSpan -Seconds $RestartIntervalSeconds)" in text
    assert "-MultipleInstances IgnoreNew" in text
    assert "-ExecutionTimeLimit ([TimeSpan]::Zero)" in text
    assert "-StartWhenAvailable" in text
    assert 'New-Object -ComObject "Schedule.Service"' in text
    assert "Ensure-ScheduledTaskFolder -Path $normalizedTaskPath" in text
    assert 'ReadyUrl = "http://127.0.0.1:6333/readyz"' in text
    assert "Register-ScheduledTask" in text
    assert "Start-ScheduledTask" in text
    assert "docker" not in text.lower()
    assert "compose" not in text.lower()


def test_verification_asset_checks_task_contract_and_qdrant_readiness() -> None:
    text = VERIFY.read_text(encoding="utf-8")

    assert "Get-ScheduledTask" in text
    assert "Get-ScheduledTaskInfo" in text
    assert '"MSFT_TaskLogonTrigger"' in text
    assert '"IgnoreNew"' in text
    assert "RestartCount" in text
    assert "/readyz" in text
    assert '"sgokb.qdrant-windows-autostart-check/1.0"' in text


def test_native_windows_operations_and_decision_are_the_runtime_authority() -> None:
    operations = OPERATIONS.read_text(encoding="utf-8")
    decision = DECISION.read_text(encoding="utf-8")

    assert "Windows Task Scheduler" in operations
    assert "qdrant.exe" in operations
    assert "AtLogOn" in operations
    assert "P-RUNTIME-04" in operations
    assert "client / observer only" in operations
    assert "Docker Compose" in decision
    assert "optional" in decision.lower()
    assert "Windows Task Scheduler" in decision
    assert "native" in decision.lower()
