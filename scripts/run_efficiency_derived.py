"""Check derived views on a private SQLite backup without modifying the source DB."""

import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path

from cpc.claims import build_claims
from cpc.domain import digest, json_text
from cpc.repository import Repository
from cpc.views import build_view


def fingerprint(path):
    result = {}
    for file in (path, Path(str(path) + "-wal")):
        if file.exists():
            checksum = hashlib.sha256()
            with file.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    checksum.update(block)
            result[file.name] = [checksum.hexdigest(), file.stat().st_mtime_ns]
    return result


def run(source, out):
    out.mkdir(parents=True, exist_ok=True)
    target = out / "derived.sqlite"
    if target.exists():
        raise ValueError("Use a new output directory; existing backup will not be overwritten")
    before = fingerprint(source)
    original = sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True)
    copy = sqlite3.connect(target)
    try:
        original.backup(copy)
    finally:
        original.close()
        copy.close()
    repo = Repository(target)
    results = []
    try:
        entities = repo.rows(
            "SELECT DISTINCT e.id,e.type FROM entities e JOIN fragments f ON f.entity_id=e.id "
            "JOIN fragment_runs r ON r.id=f.run_id WHERE r.active=1"
        )
        for entity in entities:
            rows = repo.related_fragments(entity["id"])
            if not rows:
                continue
            initial = digest(json_text(rows))
            start = time.perf_counter()
            claims = build_claims(repo, entity["id"])
            view = build_view(repo, entity["id"], budget=4000)
            prefix = out / entity["type"]
            prefix.with_suffix(".txt").write_text(view["markdown"], encoding="utf-8")
            prefix.with_suffix(".omitted.json").write_text(
                json.dumps(view["omission_manifest"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            results.append(
                {
                    "type": entity["type"],
                    "fragments": len(rows),
                    "claims": len(claims["claims"]),
                    "selected": len(view["structured"]["claims"]),
                    "omitted": len(view["omission_manifest"]["omitted"]),
                    "output_budget_units": view["output_tokens"],
                    "counter": view["configuration"]["counter"],
                    "seconds": time.perf_counter() - start,
                    "fragments_unchanged": digest(json_text(repo.related_fragments(entity["id"])))
                    == initial,
                }
            )
        result = {
            "entities": results,
            "source_db_unchanged": before == fingerprint(source),
            "integrity": repo.one("PRAGMA integrity_check")["integrity_check"],
            "foreign_key_errors": len(repo.rows("PRAGMA foreign_key_check")),
            "semantic_quality": "human_gold_missing",
        }
        (out / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False))
        if (
            not result["source_db_unchanged"]
            or result["integrity"] != "ok"
            or result["foreign_key_errors"]
            or not all(r["fragments_unchanged"] for r in results)
        ):
            raise ValueError("Derived acceptance contract failed")
    finally:
        repo.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("sample/efficiency-derived"))
    args = parser.parse_args()
    run(args.source, args.out)
