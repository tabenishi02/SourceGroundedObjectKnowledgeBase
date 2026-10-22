"""Correlate existing Windows rename fallback evidence; never run a new workload.

Recovery requires matching PID, exact source/destination, DELETE-access reopen,
POSIX rename SUCCESS, matching close, delete API PASS and filesystem outcome.
Time proximity alone never promotes an event. Raw paths remain in local output.
"""

from __future__ import annotations

import argparse
import csv
import json
import ntpath
import re
from collections import Counter
from pathlib import Path

DAY = 86400 * 10**9


def ticks(clock):
    hour, minute, rest = clock.split(":")
    second, _, fraction = rest.partition(".")
    return (int(hour) * 3600 + int(minute) * 60 + int(second)) * 10**9 + int(
        (fraction + "000000000")[:9]
    )


def elapsed(after, before):
    return (ticks(after) - ticks(before) + DAY // 2) % DAY - DAY // 2


def key(path):
    return ntpath.normcase(ntpath.normpath(path))


def destination(event):
    return event["Detail"].split("FileName: ", 1)[-1] if "FileName: " in event["Detail"] else None


def cycle_collection(cycle):
    result = cycle["result"]
    if "collection" in result:
        return result["collection"]
    return result["prefix"] + "_" + result["space_id"][:24]


def correlate(primary, events, cycles, filesystem, terminal_errors, window_ns=100_000_000):
    source = key(primary["Path"])
    dest = destination(primary)
    collection = ntpath.basename(source)
    result = {
        "primary": primary,
        "source": primary["Path"],
        "destination": dest,
        "collection": collection,
        "classification": "AMBIGUOUS",
        "reasons": [],
    }
    matching_cycles = [c for c in cycles if cycle_collection(c).lower() == collection]
    result["cycle_matches"] = len(matching_cycles)
    result["filesystem"] = filesystem
    if len(matching_cycles) != 1 or not dest:
        result["reasons"].append("Missing/ambiguous exact collection/API binding")
        return result
    cycle = matching_cycles[0]
    api_ok = cycle["result"].get("status") == "PASS" and cycle["result"].get("cleanup") == "PASS"
    result.update(
        cycle=cycle["cycle"],
        delete_api_pass=api_ok,
        cycle_started_at=cycle["started_at"],
        cycle_ended_at=cycle["ended_at"],
    )
    begin = cycle["started_at"].split("T")[1].split("+")[0]
    end = cycle["ended_at"].split("T")[1].split("+")[0]
    if not 0 <= elapsed(primary["Time of Day"], begin) <= elapsed(end, begin):
        result["reasons"].append("Primary event is outside its API cycle")
        return result
    nearby = [
        e
        for e in events
        if e["PID"] == primary["PID"]
        and 0 < elapsed(e["Time of Day"], primary["Time of Day"]) <= window_ns
    ]
    successes = [
        e
        for e in nearby
        if e["Operation"] == "SetRenameInformationEx"
        and e["Result"] == "SUCCESS"
        and key(e["Path"]) == source
        and destination(e)
        and key(destination(e)) == key(dest)
        and "FILE_RENAME_REPLACE_IF_EXISTS" in e["Detail"]
        and "FILE_RENAME_POSIX_SEMANTICS" in e["Detail"]
    ]
    if not api_ok:
        result.update(classification="UNRECOVERED_FAILURE", reasons=["Delete API did not PASS"])
        return result
    if len(successes) != 1:
        result["reasons"].append("No unique exact POSIX rename success")
        return result
    success = successes[0]
    opens = [
        e
        for e in nearby
        if e["Operation"] == "CreateFile"
        and e["Result"] == "SUCCESS"
        and key(e["Path"]) == source
        and "Desired Access:" in e["Detail"]
        and re.search(r"\bDelete\b", e["Detail"].split("Disposition:")[0])
        and elapsed(success["Time of Day"], e["Time of Day"]) > 0
    ]
    closes = [
        e
        for e in nearby
        if e["Operation"] == "CloseFile"
        and e["Result"] == "SUCCESS"
        and key(e["Path"]) == key(dest)
        and elapsed(e["Time of Day"], success["Time of Day"]) > 0
    ]
    result.update(
        fallback_success=success,
        delete_access_opens=opens,
        destination_closes=closes,
        fallback_delta_ms=elapsed(success["Time of Day"], primary["Time of Day"]) / 10**6,
    )
    if not opens or not closes:
        result["reasons"].append("DELETE reopen / destination close sequence incomplete")
    if filesystem.get("source_exists") is not False:
        result["reasons"].append("Source survives after delete API PASS")
    if terminal_errors:
        result["reasons"].append("Terminal server log evidence must be resolved")
    result["terminal_error_count"] = len(terminal_errors)
    source_ids = [
        e["Detail"]
        for e in nearby
        if e["Operation"] == "QueryFileInternalInformationFile"
        and key(e["Path"]) == source
        and elapsed(success["Time of Day"], e["Time of Day"]) > 0
    ]
    dest_ids = [
        e["Detail"]
        for e in nearby
        if e["Operation"] == "QueryFileInternalInformationFile"
        and key(e["Path"]) == key(dest)
        and elapsed(e["Time of Day"], success["Time of Day"]) > 0
    ]
    result["file_identity_match"] = (
        bool(set(source_ids) & set(dest_ids)) if source_ids and dest_ids else None
    )
    if source_ids and dest_ids and not result["file_identity_match"]:
        result["reasons"].append("Source/destination file identity contradicts rename")
    if not result["reasons"]:
        result["classification"] = "RECOVERED_FALLBACK"
    return result


def run(source_root):
    csv_path = source_root / "procmon/procmon-filtered.csv"
    cycles = json.loads((source_root / "stress-cycles.json").read_text(encoding="utf-8"))
    runtime = json.loads((source_root / "external-runtime.json").read_text(encoding="utf-8"))
    pid = str(runtime["pid"])
    primary = []
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        for event in csv.DictReader(stream):
            if (
                event["PID"] == pid
                and event["Operation"] == "SetRenameInformationFile"
                and event["Result"] == "ACCESS DENIED"
            ):
                primary.append(event)
    wanted = {key(e["Path"]) for e in primary} | {
        key(destination(e)) for e in primary if destination(e)
    }
    events = []
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        for event in csv.DictReader(stream):
            if event["PID"] == pid and key(event["Path"]) in wanted:
                events.append(event)
    terminal = []
    pattern = re.compile(
        r"Failed to remove|Can't delete collection from disk|Access is denied|"
        r"os error [35]|service error",
        re.I,
    )
    for name in ("qdrant-diagnostic.stdout.log", "qdrant-diagnostic.stderr.log"):
        for number, line in enumerate(
            (source_root / name).read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if pattern.search(line):
                terminal.append({"log": name, "line": number, "text": line})
    cases = []
    for event in primary:
        dest = destination(event)
        fs = {
            "source_exists": Path(event["Path"]).exists(),
            "destination_exists": Path(dest).exists() if dest else None,
        }
        cases.append(correlate(event, events, cycles, fs, terminal))
    counts = Counter(c["classification"] for c in cases)
    unique_binding = len({c.get("cycle") for c in cases}) == 50 and len(cycles) == 50
    passed = (
        len(primary) == 50
        and counts["RECOVERED_FALLBACK"] == 50
        and unique_binding
        and not terminal
    )
    return {
        "source_run": source_root.name,
        "status": "PASS" if passed else "BLOCKED",
        "primary_access_denied_count": len(primary),
        "counts": dict(counts),
        "unique_50_cycle_binding": unique_binding,
        "terminal_errors": terminal,
        "window_ms": 100,
        "cases": cases,
        "stack_limit": (
            "API stack not decoded; explicit POSIX event flags/path/sequence "
            "and API/filesystem evidence used"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve prior analysis; choose a fresh output path")
    report = run(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k not in ("cases", "terminal_errors")}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
