from __future__ import annotations

from pathlib import Path

from sgokb.cli.main import parser


def test_current_project_version_is_2_1_0() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'version = "2.1.0"' in pyproject


def test_package_build_defaults_to_raw_grounded_v2() -> None:
    args = parser().parse_args(["package", "build", "--object", "object:test"])

    assert args.package_version == "v2"


def test_package_build_retains_explicit_v1_legacy_compatibility() -> None:
    args = parser().parse_args(
        ["package", "build", "--object", "object:test", "--package-version", "v1"]
    )

    assert args.package_version == "v1"
