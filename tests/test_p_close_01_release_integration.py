from __future__ import annotations

from sgokb.cli.main import parser


def test_package_build_defaults_to_raw_grounded_v2() -> None:
    args = parser().parse_args(["package", "build", "--object", "object:test"])

    assert args.package_version == "v2"


def test_package_build_retains_explicit_v1_legacy_compatibility() -> None:
    args = parser().parse_args(
        ["package", "build", "--object", "object:test", "--package-version", "v1"]
    )

    assert args.package_version == "v1"
