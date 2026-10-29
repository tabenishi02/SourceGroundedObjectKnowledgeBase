from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = REPO_ROOT / "runtime" / "qdrant" / "compose.yaml"
ENV_EXAMPLE_PATH = REPO_ROOT / "runtime" / "qdrant" / ".env.example"


def test_qdrant_compose_matches_accepted_runtime_contract() -> None:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "name: sgokb-qdrant" in compose
    assert "image: qdrant/qdrant:v1.20.0" in compose
    assert ":latest" not in compose
    assert "restart: unless-stopped" in compose
    assert '"127.0.0.1:6333:6333"' in compose
    assert '"127.0.0.1:6334:6334"' in compose
    assert "6335" not in compose
    assert "qdrant-storage:/qdrant/storage" in compose
    assert "name: sgokb_qdrant_storage" in compose
    assert "/readyz" in compose
    assert "QDRANT__LOG_LEVEL" in compose


def test_qdrant_compose_avoids_windows_bind_mount_and_local_contract_overrides() -> None:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "./" not in compose
    assert "../" not in compose
    assert "C:\\" not in compose
    assert "QDRANT_IMAGE" not in compose
    assert "QDRANT_PORT" not in compose
    assert "QDRANT_VOLUME" not in compose
    assert "QDRANT_IMAGE" not in env_example
    assert "QDRANT_PORT" not in env_example
    assert "QDRANT_VOLUME" not in env_example
    assert "QDRANT_LOG_LEVEL=INFO" in env_example
