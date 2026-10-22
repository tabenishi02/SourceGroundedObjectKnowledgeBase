"""Filter local ProcMon CSV to Qdrant storage and enumerate correlation candidates.

Correlation is not proof of a competing open handle or a security-product cause.
Raw PML/CSV and full paths remain local; this tool never opens canonical SQLite.
"""

from __future__ import annotations

import argparse
import csv
import json
import ntpath
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED = {"Time of Day", "Process Name", "PID", "Operation", "Path", "Result", "Detail"}
FAILURES = {"ACCESS DENIED", "SHARING VIOLATION", "PATH NOT FOUND", "NAME NOT FOUND"}
DETAIL_RESULTS = {"ACCESS DENIED", "SHARING VIOLATION", "USER MAPPED FILE", "FILE LOCK CONFLICT"}


def beneath(path, root):
    path = ntpath.normcase(ntpath.normpath(path))
    root = ntpath.normcase(ntpath.normpath(root)).rstrip("\\")
    return path == root or path.startswith(root + "\\")


def seconds(value):
    """ProcMon time-of-day clock, retaining its raw timestamp in evidence."""
    hour, minute, second = value.split(":")
    return int(hour) * 3600 + int(minute) * 60 + float(second)


def delta(left, right):
    return (seconds(left) - seconds(right) + 43200) % 86400 - 43200


def analyze(rows, storage_root, qdrant_pid, window=3.0):
    scoped = [r for r in rows if beneath(r["Path"], storage_root)]
    failures = []
    counts = Counter(r["Result"] for r in scoped if r["PID"] == str(qdrant_pid))
    targets = [r for r in scoped if r["PID"] == str(qdrant_pid) and r["Result"] in DETAIL_RESULTS]

    def scope(event):
        path = (
            event["Path"]
            if event["Operation"] == "SetRenameInformationFile"
            else ntpath.dirname(event["Path"])
        )
        return ntpath.normcase(ntpath.normpath(path))

    needed = {scope(r) for r in targets}
    indexed = defaultdict(list)
    for number, other in enumerate(scoped):
        if other["PID"] == str(qdrant_pid):
            continue
        timestamp = seconds(other["Time of Day"])
        directory = ntpath.normcase(ntpath.normpath(other["Path"]))
        for key in needed:
            if directory == key or directory.startswith(key + "\\"):
                indexed[key].append((timestamp, number))
    for entries in indexed.values():
        entries.sort()
    for event in targets:
        parent = scope(event)
        entries = indexed.get(parent, [])
        selected = set()
        event_time = seconds(event["Time of Day"])
        for day_offset in (-86400, 0, 86400):
            center = event_time + day_offset
            start = bisect_left(entries, (center - window, -1))
            end = bisect_right(entries, (center + window, len(scoped)))
            selected.update(number for _, number in entries[start:end])
        candidates = []
        for number in sorted(selected):
            other = scoped[number]
            same = ntpath.normcase(other["Path"]) == ntpath.normcase(event["Path"])
            candidates.append(
                {
                    "event": other,
                    "time_delta_seconds": delta(other["Time of Day"], event["Time of Day"]),
                    "path_relation": "exact" if same else "same_directory_tree",
                }
            )
        failures.append(
            {
                "event": event,
                "correlation_candidates": candidates,
                "causal_contention_proven": False,
            }
        )
    return scoped, {
        "status": "REQUIRES_MANUAL_REVIEW",
        "storage_event_count": len(scoped),
        "qdrant_failure_count": sum(counts[result] for result in FAILURES),
        "qdrant_result_counts": dict(counts),
        "detailed_failure_count": len(failures),
        "failure_detail_results": sorted(DETAIL_RESULTS),
        "lookup_misses": (
            "NAME/PATH NOT FOUND retained in counts and full filtered CSV; "
            "not expanded into repeated correlation payloads"
        ),
        "failures": failures,
        "warning": "Time/path correlation alone does not establish an open-handle conflict",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--storage-root", required=True)
    parser.add_argument("--qdrant-pid", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("Analysis output already exists; preserve prior evidence")
    with args.csv.open("rb") as stream:
        encoding = "utf-16" if stream.read(2) in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    with args.csv.open(encoding=encoding, newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if not REQUIRED.issubset(fields):
            raise ValueError("ProcMon CSV missing required English column headers")
        scoped, result = analyze(reader, args.storage_root, args.qdrant_pid)
    args.output_dir.mkdir(parents=True)
    with (args.output_dir / "procmon-filtered.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(scoped)
    with (args.output_dir / "failure-summary.json").open("w", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
