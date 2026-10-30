from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT / "runtime" / "qdrant" / "windows" / "Invoke-PRuntime04Acceptance.ps1"
)
COMPOSE_PATH = REPO_ROOT / "runtime" / "qdrant" / "compose.yaml"


def _script() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_acceptance_harness_covers_login_ordering_and_bounded_readiness() -> None:
    script = _script()

    for mode in (
        "Observe",
        "PrepareReboot",
        "VerifyAfterLogin",
        "ExerciseUnexpectedStop",
    ):
        assert f'"{mode}"' in script

    assert "Get-CimInstance Win32_OperatingSystem" in script
    assert 'docker @Arguments' in script
    assert '@("version", "--format", "{{.Server.Version}}")' in script
    assert 'http://127.0.0.1:6333/readyz' in script
    assert "[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)" in script
    assert "Start-Sleep -Seconds $PollSeconds" in script
    assert "A newer Windows boot was not observed" in script
    assert "manual_runtime_start_command_required = $false" in script


def test_harness_validates_accepted_runtime_identity() -> None:
    script = _script()
    compose = COMPOSE_PATH.read_text(encoding="utf-8")

    assert 'expected \'unless-stopped\'' in script
    assert 'qdrant/qdrant:v1.20.0' in script
    assert 'sgokb_qdrant_storage' in script
    assert 'restart: unless-stopped' in compose
    assert 'image: qdrant/qdrant:v1.20.0' in compose
    assert 'name: sgokb_qdrant_storage' in compose


def test_harness_is_observer_only_for_login_recovery() -> None:
    script = _script()

    assert "observer_only = $true" in script
    assert "lifecycle_start_command_issued = $false" in script

    # The login/reboot acceptance harness must never become the Qdrant or
    # Docker Desktop supervisor. Explicit start/reconcile operations belong
    # to documented operator troubleshooting, not automatic acceptance flow.
    forbidden = (
        '@("desktop", "start")',
        '@("desktop", "restart")',
        '@("compose", "up")',
        '@("compose", "start")',
        '@("start", $containerId)',
        "Start-Process",
    )
    for token in forbidden:
        assert token not in script


def test_harness_does_not_mutate_docker_desktop_settings_store() -> None:
    script = _script()

    assert 'Docker\\settings-store.json' in script
    assert "docker_desktop_settings_present" in script
    assert "Set-Content -LiteralPath $settingsPath" not in script
    assert "Add-Content -LiteralPath $settingsPath" not in script
    assert "Remove-Item -LiteralPath $settingsPath" not in script
    assert "ConvertTo-Json | Set-Content" not in script


def test_unexpected_stop_exercise_proves_restart_policy_recovery_without_start() -> None:
    script = _script()

    assert '@("kill", $containerId)' in script
    assert "restart_count" in script
    assert "RestartCount" in script
    assert "restart count did not increase" in script.lower()
    assert "start_command_issued_after_kill = $false" in script
    assert "10 - $ageSeconds" in script
