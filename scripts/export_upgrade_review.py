"""Read-only before/after exports. Real page text stays in ignored sample/ and .local/."""

import argparse
import json
import sqlite3
from pathlib import Path


def rows(db, sql, args=()):
    return [dict(r) for r in db.execute(sql, args)]


def connect(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def snapshot_summary(db, snapshot_id):
    evidence = rows(
        db,
        "SELECT e.* FROM evidence e JOIN snapshots n ON n.active_run=e.run_id "
        "WHERE n.id=? ORDER BY e.rowid",
        (snapshot_id,),
    )
    fragments = rows(
        db,
        "SELECT f.* FROM fragments f JOIN fragment_runs r ON r.id=f.run_id "
        "JOIN snapshots n ON n.active_run=r.normalized_run WHERE r.active=1 "
        "AND r.snapshot_id=? ORDER BY f.rowid",
        (snapshot_id,),
    )
    referenced = set()
    for f in fragments:
        referenced.update(
            r["evidence_id"]
            for r in rows(
                db, "SELECT evidence_id FROM fragment_evidence WHERE fragment_id=?", (f["id"],)
            )
        )
    return (
        {
            "evidence": len(evidence),
            "fragments": len(fragments),
            "average_fragments_per_evidence": len(fragments) / len(evidence) if evidence else None,
            "all_evidence_reference_coverage": len(referenced & {e["id"] for e in evidence})
            / len(evidence)
            if evidence
            else None,
        },
        evidence,
        fragments,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=".local/evaluation.sqlite")
    parser.add_argument("--upgrade", default=".local/upgrade.sqlite")
    parser.add_argument("--manifest", default="benchmark/sample-v1.json")
    parser.add_argument("--out", type=Path, default=Path("sample/SGOKB_Upgrade_評価"))
    args = parser.parse_args()
    sample = Path("sample").resolve()
    if sample not in args.out.resolve().parents:
        raise ValueError("Private real-data exports must be under ignored sample/")
    args.out.mkdir(parents=True, exist_ok=True)
    baseline, upgrade = connect(args.baseline), connect(args.upgrade)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    report = {"dataset": manifest["benchmark_version"], "snapshots": [], "documents": []}
    overview = [
        "SGOKB Prototype Upgrade 比較",
        "",
        "内容の忠実性・分類・重要情報の網羅性は人間確認が必要です。",
        "件数と引用率は正しさや独立した裏付けの数を表しません。",
        "",
    ]
    for case in manifest["cases"]:
        if case["task"] != "fragment":
            continue
        sid = case["snapshot_id"]
        text = [case["id"], "Snapshot: " + sid, ""]
        comparison = {"case": case["id"], "snapshot_id": sid}
        for label, db in (("BEFORE 初回", baseline), ("AFTER Upgrade", upgrade)):
            snap = rows(
                db,
                "SELECT n.*,s.url FROM snapshots n JOIN sources s ON s.id=n.source_id WHERE n.id=?",
                (sid,),
            )[0]
            summary, evidence, fragments = snapshot_summary(db, sid)
            comparison["before" if db is baseline else "after"] = summary
            text.extend(
                [
                    "=" * 72,
                    label,
                    "=" * 72,
                    "Raw ZIP: " + snap["raw_path"],
                    "SHA256: " + snap["raw_sha256"],
                    "URL: " + snap["url"],
                    "Title: " + snap["title"],
                    "captured_at: " + snap["captured_at"],
                    "Normalized generation: " + snap["active_run"],
                    json.dumps(summary, indent=2),
                    "",
                ]
            )
            if db is upgrade:
                context = rows(
                    db,
                    "SELECT * FROM page_contexts WHERE normalized_run=? "
                    "ORDER BY rowid DESC LIMIT 1",
                    (snap["active_run"],),
                )
                if context:
                    text.extend(
                        [
                            "Page Context",
                            json.dumps(
                                {
                                    k: json.loads(context[0][k])
                                    for k in ("deterministic", "inferred", "overrides", "effective")
                                },
                                ensure_ascii=False,
                                indent=2,
                            ),
                            "",
                        ]
                    )
                jobs = rows(
                    db,
                    "SELECT id FROM extraction_jobs WHERE snapshot_id=? "
                    "ORDER BY rowid DESC LIMIT 1",
                    (sid,),
                )
                if jobs:
                    assessment = rows(
                        db, "SELECT * FROM evidence_assessments WHERE job_id=?", (jobs[0]["id"],)
                    )
                    text.extend(
                        [
                            "Evidence assessments（pending/failed/0件理由）",
                            json.dumps(assessment, ensure_ascii=False, indent=2),
                            "",
                        ]
                    )
            normalized = rows(
                db, "SELECT blocks FROM normalized_runs WHERE id=?", (snap["active_run"],)
            )[0]
            text.append("Normalized blocks")
            for i, block in enumerate(json.loads(normalized["blocks"]), 1):
                text.extend(
                    [
                        f"B{i:04} {block['kind']} {block['position']}",
                        "Section: " + " / ".join(block["section"]),
                        block["content"],
                        "",
                    ]
                )
            text.append("Evidence 全件")
            for i, e in enumerate(evidence, 1):
                text.extend([f"E{i:04} {e['id']}", "Metadata: " + e["metadata"], e["content"], ""])
            text.append("Fragment 全件")
            for i, f in enumerate(fragments, 1):
                text.extend([f"F{i:04} {f['id']}", f["content"], "Metadata: " + f["metadata"], ""])
        report["snapshots"].append(comparison)
        overview.extend([case["id"], json.dumps(comparison, ensure_ascii=False, indent=2), ""])
        (args.out / (case["id"] + ".txt")).write_text("\n".join(text), encoding="utf-8-sig")
    for case in manifest["cases"]:
        if case["task"] != "final":
            continue
        text, comparison = [], {"case": case["id"]}
        for label, db in (("before", baseline), ("after", upgrade)):
            docs = rows(
                db,
                "SELECT d.* FROM documents d "
                + ("JOIN structured_documents sd ON sd.document_id=d.id " if db is upgrade else "")
                + "WHERE d.entity_id=? ORDER BY d.rowid DESC LIMIT 1",
                (case["entity_id"],),
            )
            if not docs:
                comparison[label] = {"status": "not_generated"}
                continue
            d = docs[0]
            comparison[label] = {
                "document_id": d["id"],
                "characters": len(d["markdown"]),
                "sections": d["markdown"].count("\n## "),
                "citations": len(json.loads(d["citations"])),
            }
            text.extend([label.upper(), "Document: " + d["id"], d["markdown"], ""])
            if db is upgrade:
                structured = rows(
                    db,
                    "SELECT representation FROM structured_documents WHERE document_id=?",
                    (d["id"],),
                )[0]
                rep = json.loads(structured["representation"])
                comparison[label]["information_types"] = {
                    k: len(rep[k])
                    for k in (
                        "facts",
                        "source_interpretations",
                        "derived_interpretations",
                        "public_perception",
                        "promotional_claims",
                        "conflicts",
                    )
                }
                text.extend(
                    [
                        "Structured Final Representation",
                        json.dumps(rep, ensure_ascii=False, indent=2),
                    ]
                )
                (args.out / (case["id"] + ".json")).write_text(
                    json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                (args.out / (case["id"] + "-ai-context.txt")).write_text(
                    json.dumps(
                        {"trust": "untrusted_source_claims", "knowledge": rep},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8-sig",
                )
        report["documents"].append(comparison)
        overview.extend([case["id"], json.dumps(comparison, ensure_ascii=False, indent=2), ""])
        (args.out / (case["id"] + ".txt")).write_text("\n".join(text), encoding="utf-8-sig")
    (args.out / "比較サマリー.txt").write_text("\n".join(overview), encoding="utf-8-sig")
    Path(".local/upgrade-comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {"exported_snapshots": len(report["snapshots"]), "documents": len(report["documents"])}
        )
    )
    baseline.close()
    upgrade.close()


if __name__ == "__main__":
    main()
