import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "procmon_analysis",
    Path(__file__).resolve().parents[1] / "benchmark/tools/n05d01_analyze_procmon.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def event(pid, path, clock="12:00:00.0000000", result="SUCCESS"):
    return {
        "Time of Day": clock,
        "Process Name": "qdrant.exe" if pid == 10 else "other.exe",
        "PID": str(pid),
        "Operation": "CreateFile",
        "Path": path,
        "Result": result,
        "Detail": "ShareMode: Read, Write",
    }


def test_storage_filter_preserves_other_process_and_rejects_near_prefix():
    rows = [
        event(10, r"C:\data\q\index", result="ACCESS DENIED"),
        event(20, r"c:\DATA\q\index", "11:59:59.5000000"),
        event(30, r"C:\data\q-other\index"),
        event(40, r"C:\data\q\different\file"),
    ]
    scoped, report = MODULE.analyze(rows, r"C:\data\q", 10)
    assert len(scoped) == 3
    failure = report["failures"][0]
    assert [x["event"]["PID"] for x in failure["correlation_candidates"]] == ["20", "40"]
    assert failure["correlation_candidates"][0]["path_relation"] == "exact"
    assert failure["correlation_candidates"][0]["time_delta_seconds"] == -0.5
    assert failure["causal_contention_proven"] is False


def test_correlation_window_handles_midnight_without_promoting_causality():
    rows = [
        event(10, r"C:\q\index", "00:00:00.1000000", "SHARING VIOLATION"),
        event(20, r"C:\q\index", "23:59:59.9000000"),
        event(30, r"C:\q\index", "00:00:05.0000000"),
    ]
    _, report = MODULE.analyze(rows, r"C:\q", 10)
    assert len(report["failures"][0]["correlation_candidates"]) == 1
    assert report["status"] == "REQUIRES_MANUAL_REVIEW"


def test_correlation_keeps_window_boundary_and_excludes_unrelated_directories():
    rows = [
        event(10, r"C:\q\segment\index", result="ACCESS DENIED"),
        event(20, r"C:\q\segment\index", "12:00:03.0000000"),
        event(30, r"C:\q\segment\nested\file", "11:59:57.0000000"),
        event(40, r"C:\q\segment\index", "12:00:03.0000001"),
        event(50, r"C:\q\other\index"),
    ]
    _, report = MODULE.analyze(rows, r"C:\q", 10)
    assert [item["event"]["PID"] for item in report["failures"][0]["correlation_candidates"]] == [
        "20",
        "30",
    ]


def test_lookup_misses_remain_counted_without_expanding_correlation_payloads():
    rows = [
        event(10, r"C:\q\missing", result="NAME NOT FOUND"),
        event(10, r"C:\q\missing2", result="PATH NOT FOUND"),
    ]
    scoped, report = MODULE.analyze(rows, r"C:\q", 10)
    assert len(scoped) == 2
    assert report["qdrant_failure_count"] == 2
    assert report["qdrant_result_counts"]["NAME NOT FOUND"] == 1
    assert report["failures"] == []


def test_directory_rename_candidates_do_not_include_neighbor_collections():
    failure = event(10, r"C:\q\collections\one", result="ACCESS DENIED")
    failure["Operation"] = "SetRenameInformationFile"
    rows = [
        failure,
        event(20, r"C:\q\collections\one\index"),
        event(30, r"C:\q\collections\two\index"),
    ]
    _, report = MODULE.analyze(rows, r"C:\q", 10)
    assert [c["event"]["PID"] for c in report["failures"][0]["correlation_candidates"]] == ["20"]
