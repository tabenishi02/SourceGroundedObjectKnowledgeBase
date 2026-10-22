import copy
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "rename_correlation",
    Path(__file__).resolve().parents[1] / "benchmark/tools/n05d01_correlate_rename_fallback.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SOURCE = r"C:\q\collections\n05test"
DEST = r"C:\q\.deleted\target"


def fixture():
    def event(operation, clock, result="SUCCESS", detail="", path=SOURCE):
        return {
            "PID": "10",
            "Time of Day": clock,
            "Operation": operation,
            "Result": result,
            "Detail": detail,
            "Path": path,
        }

    primary = event(
        "SetRenameInformationFile",
        "12:00:00.0000000",
        "ACCESS DENIED",
        "ReplaceIfExists: True, FileName: " + DEST,
    )
    events = [
        event("CreateFile", "12:00:00.0010000", detail="Desired Access: Delete, Disposition: Open"),
        event(
            "SetRenameInformationEx",
            "12:00:00.0020000",
            detail="Flags: FILE_RENAME_REPLACE_IF_EXISTS, FILE_RENAME_POSIX_SEMANTICS, FileName: "
            + DEST,
        ),
        event("CloseFile", "12:00:00.0030000", path=DEST),
    ]
    cycles = [
        {
            "cycle": 1,
            "started_at": "2026-10-22T11:59:59.999000+09:00",
            "ended_at": "2026-10-22T12:00:00.010000+09:00",
            "result": {"collection": "n05test", "status": "PASS", "cleanup": "PASS"},
        }
    ]
    return primary, events, cycles


def test_complete_exact_sequence_and_api_filesystem_prove_recovery():
    primary, events, cycles = fixture()
    result = MODULE.correlate(primary, events, cycles, {"source_exists": False}, [])
    assert result["classification"] == "RECOVERED_FALLBACK"
    assert result["fallback_delta_ms"] == 2
    assert result["delete_api_pass"] is True


@pytest.mark.parametrize(
    "change", ["pid", "destination", "source", "delete_open", "flags", "close"]
)
def test_time_proximity_without_exact_identity_and_sequence_is_ambiguous(change):
    primary, events, cycles = fixture()
    if change == "pid":
        events[1]["PID"] = "20"
    if change == "destination":
        events[1]["Detail"] = events[1]["Detail"].replace(DEST, DEST + "-other")
    if change == "source":
        events[1]["Path"] = SOURCE + "-other"
    if change == "delete_open":
        events.pop(0)
    if change == "flags":
        events[1]["Detail"] = events[1]["Detail"].replace("FILE_RENAME_POSIX_SEMANTICS", "NONE")
    if change == "close":
        events.pop()
    assert (
        MODULE.correlate(primary, events, cycles, {"source_exists": False}, [])["classification"]
        == "AMBIGUOUS"
    )


def test_failed_delete_api_is_unrecovered_despite_successful_native_event():
    primary, events, cycles = fixture()
    cycles[0]["result"]["cleanup"] = "FAIL"
    assert (
        MODULE.correlate(primary, events, cycles, {"source_exists": False}, [])["classification"]
        == "UNRECOVERED_FAILURE"
    )


@pytest.mark.parametrize(
    "filesystem,terminal",
    [({}, []), ({"source_exists": True}, []), ({"source_exists": False}, [{"error": "terminal"}])],
)
def test_filesystem_or_terminal_contradiction_blocks_promotion(filesystem, terminal):
    primary, events, cycles = fixture()
    assert (
        MODULE.correlate(primary, events, cycles, filesystem, terminal)["classification"]
        == "AMBIGUOUS"
    )


def test_duplicate_cycle_binding_is_not_resolved_by_nearby_success():
    primary, events, cycles = fixture()
    cycles.append(copy.deepcopy(cycles[0]))
    assert (
        MODULE.correlate(primary, events, cycles, {"source_exists": False}, [])["classification"]
        == "AMBIGUOUS"
    )
