from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / "runtime" / "qdrant"
PROBE_PATH = RUNTIME_DIR / "verify-windows-login-readiness.ps1"
COMPOSE_PATH = RUNTIME_DIR / "compose.yaml"
OPS_PATH = REPO_ROOT / "docs" / "operations" / "P_RUNTIME_04_WINDOWS_LOGIN_AUTOSTART.md"


def test_login_readiness_probe_is_observer_only() -> None:
    probe = PROBE_PATH.read_text(encoding="utf-8")

    assert '"info", "--format"' in probe
    assert '"compose", "-f", $ComposePath, "-p", $ProjectName, "ps", "-q"' in probe
    assert '"inspect", "--format"' in probe
    assert "http://127.0.0.1:6333/readyz" in probe
    assert 'lifecycle_owner = "external"' in probe

    forbidden_invocations = (
        '"compose", "-f", $ComposePath, "-p", $ProjectName, "up"',
        '"compose", "-f", $ComposePath, "-p", $ProjectName, "start"',
        '"compose", "-f", $ComposePath, "-p", $ProjectName, "restart"',
        "Start-Process",
        "Register-ScheduledTask",
        "schtasks /",
    )
    for invocation in forbidden_invocations:
        assert invocation not in probe


def test_login_autostart_keeps_accepted_compose_contract() -> None:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "name: sgokb-qdrant" in compose
    assert "restart: unless-stopped" in compose
    assert '"127.0.0.1:6333:6333"' in compose
    assert '"127.0.0.1:6334:6334"' in compose
    assert "/readyz" in compose


def test_login_autostart_operations_document_safety_boundaries() -> None:
    operations = OPS_PATH.read_text(encoding="utf-8")

    assert "Start Docker Desktop when you sign in to your computer" in operations
    assert "Windows sign-in" in operations
    assert "Docker Engine" in operations
    assert "restart: unless-stopped" in operations
    assert "verify-windows-login-readiness.ps1" in operations
    assert "docker compose stop" in operations
    assert "docker kill" in operations
    assert "SGOKB does not start Docker Desktop or Qdrant" in operations
    assert "P-RUNTIME-05" in operations
