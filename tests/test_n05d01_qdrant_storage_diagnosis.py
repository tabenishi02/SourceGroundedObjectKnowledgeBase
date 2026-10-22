import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "benchmark" / "tools" / "n05d01_qdrant_storage_diagnosis.py"

spec = importlib.util.spec_from_file_location("n05d01_qdrant_storage_diagnosis", TOOL)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _report(
    *,
    server="PASS",
    direct_plain="PASS",
    direct_indexed="PASS",
    adapter_plain="PASS",
    adapter_indexed="PASS",
):
    return {
        "server": {"status": server},
        "probes": {
            "direct_plain": {"status": direct_plain},
            "direct_indexed": {"status": direct_indexed},
            "adapter_plain": {"status": adapter_plain},
            "adapter_indexed": {"status": adapter_indexed},
        },
    }


def test_unreachable_server_is_environment_defect():
    result = module.classify(_report(server="FAIL"))
    assert result["classification"] == "QDRANT_ENVIRONMENT_DEFECT"


def test_plain_direct_failure_is_environment_defect():
    result = module.classify(_report(direct_plain="FAIL"))
    assert result["classification"] == "QDRANT_ENVIRONMENT_DEFECT"


def test_payload_index_direct_failure_rules_out_adapter_as_primary_trigger():
    result = module.classify(_report(direct_indexed="FAIL"))
    assert result["classification"] == "OTHER_IDENTIFIED_CAUSE"
    assert result["subtype"] == "QDRANT_PAYLOAD_INDEX_STORAGE_PATH_REPRODUCED"


def test_adapter_only_failure_is_adapter_defect():
    result = module.classify(_report(adapter_indexed="FAIL"))
    assert result["classification"] == "SGOKB_ADAPTER_DEFECT"


def test_all_paths_pass_means_not_reproduced():
    result = module.classify(_report())
    assert result["classification"] == "NOT_REPRODUCED"
