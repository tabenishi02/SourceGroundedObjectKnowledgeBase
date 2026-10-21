"""Validate development-only corpora and lineage/family manifests without confirmation access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABELS = {
    "atomicity": {"ATOMIC", "NON_ATOMIC", "AMBIGUOUS"},
    "content_type": {
        "SOURCE_FACT_CONTENT",
        "INTERPRETATION_CONTENT",
        "CREATIVE_CONTENT",
        "CONTEXT_LIMIT_CONTENT",
        "MIXED_CONTENT",
        "AMBIGUOUS",
    },
}
COMPATIBILITY = {
    "SOURCE_FACT_CONTENT": "source_fact",
    "INTERPRETATION_CONTENT": "interpretation",
    "CREATIVE_CONTENT": "creative_addition",
    "CONTEXT_LIMIT_CONTENT": "context_limit",
}
ROLES = set(COMPATIBILITY.values())
FIELDS = {
    "case_id",
    "text",
    "label",
    "family_id",
    "lineage_id",
    "split_group",
    "source",
    "required",
    "critical_for_safety",
    "rationale",
    "split",
    "training_target",
}


def normalized(text: str) -> str:
    return re.sub(r"[\W_]+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def check(task: str, rows: list[dict], families: dict, split: dict) -> dict:
    if not rows:
        raise ValueError("Empty corpus")
    ids = set()
    groups = {key: defaultdict(set) for key in ["family_id", "lineage_id", "split_group"]}
    texts = defaultdict(set)
    norms = defaultdict(set)
    by_partition = defaultdict(Counter)
    for row in rows:
        if not FIELDS <= row.keys():
            raise ValueError("Missing required fields")
        cid = row["case_id"]
        if cid in ids:
            raise ValueError("Duplicate case_id")
        ids.add(cid)
        if row["label"] not in LABELS[task] or row["split"] not in {
            "train",
            "validation",
            "selection",
        }:
            raise ValueError("Invalid taxonomy or split")
        if (
            not isinstance(row["text"], str)
            or not row["text"].strip()
            or not row["rationale"].strip()
        ):
            raise ValueError("Empty text/rationale")
        if row["source"] not in {"synthetic_design_family", "independent_seed"}:
            raise ValueError("Unapproved source")
        for key in ["required", "critical_for_safety", "training_target"]:
            if not isinstance(row[key], bool):
                raise ValueError("Flag is not boolean")
        if row["label"] == "AMBIGUOUS" and (
            row["required"] or row["critical_for_safety"] or row["training_target"]
        ):
            raise ValueError("Ambiguous control cannot be required/critical/hard training target")
        family = families[row["family_id"]]
        if (family["task"], family["label"], family["split"], family["rationale"]) != (
            task,
            row["label"],
            row["split"],
            row["rationale"],
        ):
            raise ValueError("Family invariant mismatch")
        if (
            split["cases"].get(cid) != row["split"]
            or split["families"].get(row["family_id"]) != row["split"]
            or split["lineages"].get(row["lineage_id"]) != row["split"]
        ):
            raise ValueError("Split manifest mismatch")
        if task == "content_type":
            good, bad = (
                row["compatible_expected_roles"],
                row["critical_incompatible_expected_roles"],
            )
            expected = [COMPATIBILITY[row["label"]]] if row["label"] in COMPATIBILITY else []
            if good != expected or set(good) & set(bad) or not set(good + bad) <= ROLES:
                raise ValueError("Compatibility metadata invalid")
            if row["label"] != "AMBIGUOUS" and set(bad) != ROLES - set(expected):
                raise ValueError("Incomplete critical incompatible roles")
        for key, values in groups.items():
            values[row[key]].add(row["split"])
        texts[row["text"]].add(row["split"])
        norms[normalized(row["text"])].add(row["split"])
        by_partition[row["split"]][row["label"]] += 1
    if any(len(s) > 1 for values in groups.values() for s in values.values()):
        raise ValueError("Family/lineage/split_group leakage")
    if any(len(s) > 1 for s in texts.values()) or any(len(s) > 1 for s in norms.values()):
        raise ValueError("Exact/normalized duplicate across splits")
    counts = Counter(r["label"] for r in rows)
    if (
        len(rows) - counts["AMBIGUOUS"] < {"atomicity": 400, "content_type": 500}[task]
        or counts["AMBIGUOUS"] < 50
    ):
        raise ValueError("Minimum case count not met")
    if set(by_partition) != {"train", "validation", "selection"}:
        raise ValueError("Missing partition")
    if any(set(c) != LABELS[task] for c in by_partition.values()):
        raise ValueError("Missing class coverage in a partition")
    for fam in {r["family_id"] for r in rows}:
        if sum(r["family_id"] == fam for r in rows) != families[fam]["variant_count"]:
            raise ValueError("Family coverage count mismatch")
    return dict(
        total=len(rows),
        labels=dict(counts),
        partition_labels={k: dict(v) for k, v in by_partition.items()},
        family_count=len(groups["family_id"]),
        family_leakage=0,
        lineage_leakage=0,
        split_group_leakage=0,
        exact_cross_split_duplicates=0,
        normalized_cross_split_duplicates=0,
    )


def validate(root: Path = ROOT) -> dict:
    manifest = json.loads(
        (root / "benchmark/n04g25a-development-manifest-v1.json").read_text(encoding="utf-8")
    )
    split = json.loads(
        (root / "benchmark/n04g25a-split-manifest-v1.json").read_text(encoding="utf-8")
    )
    for name, digest in manifest["corpora"].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen development input hash mismatch")
    families = {f["family_id"]: f for f in manifest["families"]}
    if len(families) != len(manifest["families"]):
        raise ValueError("Duplicate family identity")
    all_ids = set()
    cross_task_lineages = defaultdict(set)
    report = {}
    for task, suffix in [("atomicity", "atomicity"), ("content_type", "content-type")]:
        rows = [
            json.loads(line)
            for line in (root / f"benchmark/n04g25a-{suffix}-development-v1.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        report[task] = check(task, rows, families, split)
        for r in rows:
            if r["case_id"] in all_ids:
                raise ValueError("Cross-task duplicate case_id")
            all_ids.add(r["case_id"])
            cross_task_lineages[r["lineage_id"]].add(r["split"])
    if any(len(v) > 1 for v in cross_task_lineages.values()):
        raise ValueError("Cross-task lineage leakage")
    if set(split["cases"]) != all_ids:
        raise ValueError("Unexpected/missing manifest cases")
    return dict(
        status="PASS", tasks=report, cross_task_lineage_leakage=0, confirmation_data_loaded=False
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate()
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
