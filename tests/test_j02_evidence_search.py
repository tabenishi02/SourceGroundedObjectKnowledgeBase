import pytest

from sgokb.application_read import (
    KnowledgeReadApplication,
    RetrievalRuntimeUnavailableError,
)
from sgokb.repository import Repository


class EvidenceEmbedder:
    def embed(self, texts, *, query=False):
        if query:
            return [[1.0, 0.0] for _ in texts]
        return [
            [1.0, 0.0] if "winter protector" in text.casefold() else [0.0, 1.0]
            for text in texts
        ]


def _evidence(repo, source_id, snapshot_id, text, *, language="en"):
    artifact_id = repo.source_store.add_raw_artifact(
        snapshot_id,
        "html",
        f"memory://{snapshot_id}",
        (snapshot_id[-1] * 64)[:64],
        10,
    )
    run_id = repo.source_store.create_normalization_run(
        snapshot_id,
        "fixture",
        "1",
        [artifact_id],
    )
    evidence_id = repo.source_store.add_evidence(
        run_id,
        text,
        "normalized",
        language=language,
    )
    return run_id, evidence_id


def test_evidence_search_uses_effective_generation_by_default(tmp_path):
    repo = Repository(tmp_path / "j02-evidence.sqlite")
    try:
        source_id = repo.source_store.create_source("Evidence source")
        current_snapshot = repo.source_store.create_snapshot(
            source_id,
            "2026-10-01T00:00:00Z",
            "fixture",
            title="Current",
            snapshot_id="snap-current",
        )
        current_run, current_evidence = _evidence(
            repo,
            source_id,
            current_snapshot,
            "The winter protector watches the northern gate.",
        )
        repo.source_store.select_effective_snapshot(
            source_id, current_snapshot, reason="fixture"
        )
        repo.source_store.select_effective_run(
            current_snapshot, current_run, reason="fixture"
        )

        old_snapshot = repo.source_store.create_snapshot(
            source_id,
            "2026-09-01T00:00:00Z",
            "fixture",
            title="Historical",
            snapshot_id="snap-history",
        )
        _, historical_evidence = _evidence(
            repo,
            source_id,
            old_snapshot,
            "Obsolete phrase only present in historical evidence.",
        )

        app = KnowledgeReadApplication(repo)
        current = app.search_evidence("winter protector", mode="lexical")
        assert [item.evidence_id for item in current.results] == [current_evidence]

        hidden = app.search_evidence("Obsolete phrase", mode="lexical")
        assert hidden.results == ()

        historical = app.search_evidence(
            "Obsolete phrase",
            mode="lexical",
            include_historical=True,
        )
        assert [item.evidence_id for item in historical.results] == [historical_evidence]
        assert historical.include_historical is True
    finally:
        repo.close()


def test_evidence_search_object_association_scope_excludes_unassociated_sources(tmp_path):
    repo = Repository(tmp_path / "j02-association.sqlite")
    try:
        object_id = repo.object_store.create_object("Hero", "class:character")
        evidence_by_source = {}
        for suffix, status in (("confirmed", "confirmed"), ("other", None)):
            source_id = repo.source_store.create_source(suffix)
            snapshot_id = repo.source_store.create_snapshot(
                source_id,
                "2026-10-01T00:00:00Z",
                "fixture",
                snapshot_id=f"snap-{suffix}",
            )
            run_id, evidence_id = _evidence(
                repo,
                source_id,
                snapshot_id,
                "Shared searchable phrase.",
            )
            repo.source_store.select_effective_snapshot(source_id, snapshot_id, reason="fixture")
            repo.source_store.select_effective_run(snapshot_id, run_id, reason="fixture")
            evidence_by_source[source_id] = evidence_id
            if status:
                repo.source_store.associate_object(source_id, object_id, status)

        app = KnowledgeReadApplication(repo)
        result = app.search_evidence(
            "Shared searchable phrase",
            mode="lexical",
            object_id=object_id,
        )
        assert len(result.results) == 1
        assert result.results[0].source_id in {
            row["source_id"]
            for row in repo.source_store.associations_for_object(object_id)
            if row["status"] == "confirmed"
        }
    finally:
        repo.close()


def test_evidence_hybrid_degrades_but_semantic_only_fails_without_embedder(tmp_path):
    repo = Repository(tmp_path / "j02-degrade.sqlite")
    try:
        source_id = repo.source_store.create_source("Source")
        snapshot_id = repo.source_store.create_snapshot(
            source_id,
            "2026-10-01T00:00:00Z",
            "fixture",
            snapshot_id="snap-degrade",
        )
        run_id, _ = _evidence(repo, source_id, snapshot_id, "winter protector")
        repo.source_store.select_effective_snapshot(source_id, snapshot_id, reason="fixture")
        repo.source_store.select_effective_run(snapshot_id, run_id, reason="fixture")
        app = KnowledgeReadApplication(repo)

        hybrid = app.search_evidence("winter protector", mode="hybrid")
        assert hybrid.results
        assert hybrid.degraded_channels == ("semantic:RuntimeError",)

        with pytest.raises(RetrievalRuntimeUnavailableError):
            app.search_evidence("winter protector", mode="semantic")
    finally:
        repo.close()


def test_semantic_evidence_search_returns_provenance(tmp_path):
    repo = Repository(tmp_path / "j02-semantic.sqlite")
    try:
        source_id = repo.source_store.create_source("Source")
        snapshot_id = repo.source_store.create_snapshot(
            source_id,
            "2026-10-01T00:00:00Z",
            "fixture",
            title="Semantic source",
            snapshot_id="snap-semantic",
        )
        run_id, expected = _evidence(
            repo,
            source_id,
            snapshot_id,
            "The winter protector guards a remote place.",
        )
        repo.source_store.add_evidence(
            run_id,
            "Completely unrelated material.",
            "normalized",
            language="en",
        )
        repo.source_store.select_effective_snapshot(source_id, snapshot_id, reason="fixture")
        repo.source_store.select_effective_run(snapshot_id, run_id, reason="fixture")

        app = KnowledgeReadApplication(repo, evidence_embedder=EvidenceEmbedder())
        result = app.search_evidence("guardian in winter", mode="semantic", limit=1)
        assert result.results[0].evidence_id == expected
        assert result.results[0].semantic_score == pytest.approx(1.0)
        assert result.results[0].provenance["source_id"] == source_id
    finally:
        repo.close()
