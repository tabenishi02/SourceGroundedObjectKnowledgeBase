"""Additive persistence operations for context, resumable capture and structured outputs."""

import json
from collections import Counter

from .context import VERSION, effective_context
from .domain import digest, json_text, now, uid


class KnowledgeRepository:
    def _insert_context(self, normalized_run, snapshot_id, deterministic, inferred, overrides):
        context_id = uid()
        effective = effective_context(deterministic, inferred, overrides)
        self.db.execute(
            "INSERT INTO page_contexts VALUES(?,?,?,?,?,?,?,?,?)",
            (
                context_id,
                normalized_run,
                snapshot_id,
                json_text(deterministic),
                json_text(inferred),
                json_text(overrides),
                json_text(effective),
                VERSION,
                now(),
            ),
        )
        return context_id

    def page_context(self, normalized_run, context_id=None):
        row = self.one(
            "SELECT * FROM page_contexts WHERE normalized_run=? "
            + ("AND id=?" if context_id else "ORDER BY rowid DESC LIMIT 1"),
            (normalized_run, context_id) if context_id else (normalized_run,),
        )
        if row:
            for key in ("deterministic", "inferred", "overrides", "effective"):
                row[key] = json.loads(row[key])
        return row

    def revise_context(self, normalized_run, overrides=None, inferred=None):
        previous = self.page_context(normalized_run)
        if not previous:
            raise ValueError("Process snapshot with context first")
        with self.db:
            context_id = self._insert_context(
                normalized_run,
                previous["snapshot_id"],
                previous["deterministic"],
                {**previous["inferred"], **(inferred or {})},
                {**previous["overrides"], **(overrides or {})},
            )
        return self.page_context(normalized_run, context_id)

    def start_extraction(self, snapshot, entity_id, context_id, configuration, evidence):
        job = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO extraction_jobs VALUES(?,?,?,?,?,?,?,NULL,?)",
                (
                    job,
                    snapshot["id"],
                    snapshot["active_run"],
                    entity_id,
                    context_id,
                    json_text(configuration),
                    "running",
                    now(),
                ),
            )
            self.db.executemany(
                "INSERT INTO evidence_assessments VALUES(?,?,?,?,NULL,NULL,0)",
                [(job, e["id"], int(e["substantive"]), "pending") for e in evidence],
            )
        return self.extraction_job(job)

    def extraction_job(self, job_id):
        row = self.one("SELECT * FROM extraction_jobs WHERE id=?", (job_id,))
        if not row:
            raise ValueError("Unknown extraction job")
        row["configuration"] = json.loads(row["configuration"])
        return row

    def assessments(self, job_id):
        return self.rows(
            "SELECT * FROM evidence_assessments WHERE job_id=? ORDER BY rowid", (job_id,)
        )

    def cached_window(self, job_id, key):
        row = self.one(
            "SELECT result FROM extraction_windows WHERE job_id=? AND window_key=?", (job_id, key)
        )
        return json.loads(row["result"]) if row else None

    def save_claims(self, generation, entity_id, configuration, input_hash, claims):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO claim_generations VALUES(?,?,?,?,?)",
                (generation, entity_id, json_text(configuration), input_hash, now()),
            )
            for claim in claims:
                self.db.execute(
                    "INSERT OR IGNORE INTO knowledge_claims VALUES(?,?,?)",
                    (generation, claim["id"], json_text(claim)),
                )
                self.db.executemany(
                    "INSERT OR IGNORE INTO claim_support VALUES(?,?,?)",
                    [(generation, claim["id"], f) for f in claim["fragment_ids"]],
                )

    def cached_vector(self, key):
        row = self.one("SELECT * FROM vector_cache WHERE cache_key=?", (key,))
        return json.loads(row["vector"]) if row else None

    def save_vector_cache(self, items):
        with self.db:
            self.db.executemany("INSERT OR IGNORE INTO vector_cache VALUES(?,?,?,?,?,?)", items)

    def save_window(self, job_id, key, membership, result, ai_run):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO extraction_windows VALUES(?,?,?,?,?)",
                (job_id, key, json_text(membership), json_text(result), ai_run),
            )

    def window_split(self, job_id, key, children=None):
        if children is not None:
            with self.db:
                self.db.execute(
                    "INSERT OR IGNORE INTO window_splits VALUES(?,?,?)",
                    (job_id, key, json_text(children)),
                )
        row = self.one(
            "SELECT children FROM window_splits WHERE job_id=? AND window_key=?", (job_id, key)
        )
        return json.loads(row["children"]) if row else None

    def record_batch(self, job_id, batch_key, evidence_ids, result=None, ai_run=None, error=None):
        batch_id = uid()
        status = "failed" if error else "success"
        counts = Counter(
            e for f in (result or {}).get("fragments", []) for e in set(f["evidence_ids"])
        )
        assessments = {a["evidence_id"]: a for a in (result or {}).get("assessments", [])}
        with self.db:
            # Failed attempts remain in ai_runs; only the batch checkpoint is replaced on resume.
            previous = self.one(
                "SELECT id FROM extraction_batches WHERE job_id=? AND batch_key=?",
                (job_id, batch_key),
            )
            if previous:
                batch_id = previous["id"]
                self.db.execute(
                    "UPDATE extraction_batches SET ai_run=?,result=?,status=?,error=? WHERE id=?",
                    (ai_run, json_text(result), status, error, batch_id),
                )
            else:
                self.db.execute(
                    "INSERT INTO extraction_batches VALUES(?,?,?,?,?,?,?)",
                    (
                        batch_id,
                        job_id,
                        batch_key,
                        ai_run,
                        json_text(result),
                        status,
                        error,
                    ),
                )
            for evidence_id in evidence_ids:
                reason = assessments.get(evidence_id, {}).get("discard_reason")
                assessment_status = "failed" if error else ("discarded" if reason else "success")
                self.db.execute(
                    "UPDATE evidence_assessments SET status=?,discard_reason=?,"
                    "batch_id=?,fragment_count=? WHERE job_id=? AND evidence_id=?",
                    (
                        assessment_status,
                        reason,
                        batch_id,
                        counts[evidence_id],
                        job_id,
                        evidence_id,
                    ),
                )
            for candidate in (result or {}).get("entity_candidates", []):
                self.db.execute(
                    "INSERT INTO entity_candidates VALUES(?,?,?,?,'unconfirmed')",
                    (uid(), job_id, batch_id, json_text(candidate)),
                )
            self.db.execute("UPDATE extraction_jobs SET status=? WHERE id=?", ("running", job_id))

    def promote_extraction(self, job_id):
        job = self.extraction_job(job_id)
        if job["status"] == "complete":
            return self.coverage(job_id)
        if any(a["status"] in {"pending", "failed"} for a in self.assessments(job_id)):
            with self.db:
                self.db.execute(
                    "UPDATE extraction_jobs SET status='incomplete' WHERE id=?", (job_id,)
                )
            return self.coverage(job_id)
        snapshot = self.snapshot(job["snapshot_id"])
        if snapshot["active_run"] != job["normalized_run"]:
            raise ValueError("Cannot promote an extraction for a superseded normalized generation")
        batches = self.rows(
            "SELECT * FROM extraction_batches WHERE job_id=? AND status='success' ORDER BY rowid",
            (job_id,),
        )
        items = []
        for batch in batches:
            for item in json.loads(batch["result"])["fragments"]:
                items.append(
                    {
                        **item,
                        "context_id": job["context_id"],
                        "ai_run": item.get("ai_run", batch["ai_run"]),
                        "extraction_job": job_id,
                    }
                )
        # A deterministic all-discard generation still needs a traceable processing ledger.
        ai_id = next((b["ai_run"] for b in batches if b["ai_run"]), None)
        if not ai_id:
            ai_id = self.begin_ai("deterministic_discard", "cpc-rule-engine", "1", "", "1", {})
            self.finish_ai(ai_id, json_text({"fragments": []}))
        with self.db:
            ids, run_id = self._insert_fragment_generation(
                snapshot,
                job["entity_id"],
                items,
                ai_id,
                {**job["configuration"], "extraction_job": job_id, "context_id": job["context_id"]},
            )
            self.db.execute(
                "UPDATE extraction_jobs SET status='complete',fragment_run=? WHERE id=?",
                (run_id, job_id),
            )
            referenced = Counter(e for item in items for e in set(item["evidence_ids"]))
            for evidence_id, count in referenced.items():
                self.db.execute(
                    "UPDATE evidence_assessments SET status='success',discard_reason=NULL,"
                    "fragment_count=? WHERE job_id=? AND evidence_id=?",
                    (count, job_id, evidence_id),
                )
        return {**self.coverage(job_id), "fragment_ids": ids}

    def coverage(self, job_id):
        job = self.extraction_job(job_id)
        rows = self.assessments(job_id)
        fragments = self.rows(
            "SELECT id,metadata FROM fragments WHERE run_id=?", (job["fragment_run"],)
        )
        referenced = Counter(
            e for f in fragments for e in set(json.loads(f["metadata"])["evidence_ids"])
        )
        substantive = [r for r in rows if r["substantive"]]
        # Completed batch checkpoints also expose partial coverage without promoting it.
        if not job["fragment_run"]:
            fragments = []
            for b in self.rows(
                "SELECT result FROM extraction_batches WHERE job_id=? AND status='success'",
                (job_id,),
            ):
                fragments.extend(json.loads(b["result"])["fragments"])
            referenced = Counter(e for f in fragments for e in set(f["evidence_ids"]))
        covered = sum(bool(referenced[r["evidence_id"]]) for r in substantive)
        return {
            "job_id": job_id,
            "status": job["status"],
            "evidence_total": len(rows),
            "substantive_evidence": len(substantive),
            "evidence_with_fragments": sum(bool(referenced[r["evidence_id"]]) for r in rows),
            "zero_reasons": dict(
                Counter(
                    r["discard_reason"]
                    for r in rows
                    if r["discard_reason"] and not referenced[r["evidence_id"]]
                )
            ),
            "unprocessed": sum(r["status"] == "pending" for r in rows),
            "failed": sum(r["status"] == "failed" for r in rows),
            "fragments": len(fragments),
            "fragment_coverage": covered / len(substantive) if substantive else None,
            "average_fragments_per_evidence": len(fragments) / len(rows) if rows else None,
            "definition": "coverage=referenced substantive/all substantive; "
            "avg=raw fragments/all evidence",
        }

    def related_fragments(self, entity_id):
        rows = self.rows(
            "SELECT f.* FROM fragments f JOIN fragment_runs r ON r.id=f.run_id "
            "JOIN snapshots n ON n.active_run=r.normalized_run "
            "WHERE f.entity_id=? AND r.active=1 ORDER BY f.rowid",
            (entity_id,),
        )
        for row in rows:
            row["metadata"] = json.loads(row["metadata"])
        return rows

    def save_structured(
        self,
        entity_id,
        ai_id,
        representation,
        clusters,
        markdown,
        citations,
        config,
        algorithm="facet-epistemic-cluster-v1",
    ):
        document_id = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?,?)",
                (
                    document_id,
                    entity_id,
                    ai_id,
                    markdown,
                    json_text(citations),
                    json_text(config),
                    now(),
                ),
            )
            self.db.execute(
                "INSERT INTO structured_documents VALUES(?,?,?,?)",
                (
                    document_id,
                    json_text(representation),
                    json_text(clusters),
                    algorithm,
                ),
            )
        return document_id

    def structured_document(self, document_id):
        row = self.one("SELECT * FROM structured_documents WHERE document_id=?", (document_id,))
        if not row:
            raise ValueError("This legacy document has no structured representation")
        return json.loads(row["representation"])

    def observe_ai(self, ai_id, observations):
        with self.db:
            self.db.execute(
                "INSERT INTO ai_observations VALUES(?,?)", (ai_id, json_text(observations))
            )

    def start_benchmark(self, manifest, configuration):
        run_id = uid()
        with self.db:
            self.db.execute(
                "INSERT INTO benchmark_runs VALUES(?,?,?,?,?)",
                (
                    run_id,
                    digest(json_text(manifest)),
                    json_text(configuration),
                    now(),
                    "running",
                ),
            )
            self.db.executemany(
                "INSERT INTO benchmark_cases VALUES(?,?,'pending',NULL,NULL)",
                [(run_id, c["id"]) for c in manifest["cases"]],
            )
        return run_id

    def benchmark_case(self, run_id, case_id, result=None, error=None):
        with self.db:
            self.db.execute(
                "UPDATE benchmark_cases SET status=?,result=?,error=? WHERE run_id=? AND case_id=?",
                ("failed" if error else "success", json_text(result), error, run_id, case_id),
            )

    def finish_benchmark(self, run_id):
        rows = self.rows("SELECT * FROM benchmark_cases WHERE run_id=?", (run_id,))
        status = "complete" if all(r["status"] == "success" for r in rows) else "incomplete"
        with self.db:
            self.db.execute("UPDATE benchmark_runs SET status=? WHERE id=?", (status, run_id))
        return {"run_id": run_id, "status": status, "cases": rows}
