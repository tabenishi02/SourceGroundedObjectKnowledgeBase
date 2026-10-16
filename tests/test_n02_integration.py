import json
from pathlib import Path

from test_result_validation import _valid_result

from sgokb.application import Application
from sgokb.application_read import KnowledgeReadApplication
from sgokb.domain import EmbeddingSpaceSpec, ObjectSearchFilters
from sgokb.exchange import (
    ObjectEvidencePackageBuilder,
    ObjectVersionImportService,
    PackageTransferService,
    ResultReceiptService,
    ResultValidationService,
)
from sgokb.mcp import MCPReadAdapter
from sgokb.repository import Repository
from sgokb.retrieval import (
    ExactVectorIndexAdapter,
    KnowledgeVectorIndexBuilder,
    SearchRepresentationBuilder,
)
from sgokb.storage import PackageExchangeAuditRepository


class DeterministicEmbeddingProvider:
    def __init__(self):
        self.embedded_documents = []
        self._space = EmbeddingSpaceSpec(
            provider_key="n02-deterministic",
            provider_version="1",
            model="n02-fixture",
            model_revision="1",
            dimension=3,
            native_dimension=3,
            preprocessing_key="sgokb-search-representation",
            preprocessing_version="2",
            query_instruction="",
            document_instruction="",
            normalize_embeddings=True,
            max_sequence_length=4096,
            overflow_policy="reject",
            output_dtype="float32",
            provider_configuration="{}",
        )

    @property
    def space(self):
        return self._space

    @staticmethod
    def _vector(_text):
        return [1.0, 0.0, 0.0]

    def embed_documents(self, texts):
        self.embedded_documents.extend(texts)
        return [self._vector(text) for text in texts]

    def embed_queries(self, texts):
        return [self._vector(text) for text in texts]


def _capture_and_associate(repository, tmp_path, make_bundle):
    application = Application(repository)
    object_id = repository.object_store.create_object(
        "N02 Character",
        "class:character",
        aliases=("N02 Hero",),
        object_id="object-n02-character",
    )
    bundle = make_bundle(
        url="https://example.test/n02-character",
        html=(
            "<html><body><main><h1>N02 Character</h1>"
            "<p>N02 Character is a brave fictional character used for integration testing.</p>"
            "</main></body></html>"
        ),
    )
    imported = application.import_source_path(bundle)
    processed = application.process_source_snapshot(imported["snapshot"])
    repository.source_store.associate_object(
        imported["source"],
        object_id,
        "confirmed",
        subject_relationship="primary_subject",
    )
    return {
        "object_id": object_id,
        "source_id": imported["source"],
        "snapshot_id": imported["snapshot"],
        "run_id": processed["run"],
        "evidence_ids": tuple(processed["evidence_ids"]),
    }


def _roundtrip_result(repository, object_id, tmp_path, suffix):
    built = ObjectEvidencePackageBuilder(repository).build(
        object_id,
        build_root=tmp_path / f"build-{suffix}",
        semantic=False,
    )
    transfer = PackageTransferService()
    staged = transfer.stage_from_directory(
        built.path,
        tmp_path / f"staging-{suffix}",
    )
    manifest = json.loads(Path(staged.path, "manifest.json").read_text(encoding="utf-8"))

    audit = PackageExchangeAuditRepository(repository.db)
    audit.record_staged(manifest, staged.path, staged.preflight.to_dict())
    exported = transfer.export(staged.path, tmp_path / f"external-{suffix}")
    audit.record_export(
        exported.package_id,
        exported.manifest_sha256,
        exported.destination_root,
        exported.path,
        acknowledged_review=False,
        already_present=exported.already_present,
    )

    result = _valid_result(repository, manifest)
    result["knowledge"]["summary"][0]["text"] = (
        "N02 Character is a brave fictional character used for integration testing."
    )
    result["knowledge"]["summary"][0]["evidence"] = [
        {"evidence_id": eid, "role": "supports"}
        for eid in manifest["evidence"]["included_evidence_ids"]
    ]
    result_path = tmp_path / f"result-{suffix}" / "result.json"
    result_path.parent.mkdir()
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    incoming = tmp_path / f"incoming-{suffix}"
    receipt = ResultReceiptService(audit).receive(
        result_path,
        manifest["package_id"],
        incoming,
    )
    validation = ResultValidationService(repository, audit).validate_receipt(
        receipt.receipt_id,
        incoming_root=incoming,
    )
    assert validation.validation_state == "valid", validation.to_dict()
    imported = ObjectVersionImportService(repository, audit).import_receipt(
        receipt.receipt_id,
        incoming_root=incoming,
    )
    return {
        "built": built,
        "manifest": manifest,
        "receipt": receipt,
        "validation": validation,
        "imported": imported,
    }


def _materialize_and_embed(repository, version_id, provider):
    representation_ids = SearchRepresentationBuilder(repository).materialize_version(version_id)
    repository.embedding_store.ensure_space(provider.space)
    existing = {
        row["representation_id"]
        for row in repository.embedding_store.embedding_rows(provider.space.space_id)
    }
    created = 0
    for representation_id in sorted(set(representation_ids)):
        if representation_id in existing:
            continue
        representation = repository.semantic_store.search_representation(representation_id)
        vector = provider.embed_documents([representation.content])[0]
        created += int(
            repository.embedding_store.save_representation_embedding(
                provider.space,
                representation_id,
                vector,
            )
        )
    return representation_ids, created


def test_capture_evidence_package_result_validate_import_version_chain(tmp_path, make_bundle):
    repository = Repository(tmp_path / "n02-roundtrip.sqlite")
    try:
        captured = _capture_and_associate(repository, tmp_path, make_bundle)
        roundtrip = _roundtrip_result(repository, captured["object_id"], tmp_path, "v1")
        imported = roundtrip["imported"]
        manifest = roundtrip["manifest"]

        assert captured["evidence_ids"]
        assert set(manifest["evidence"]["included_evidence_ids"]) & set(captured["evidence_ids"])
        assert manifest["binding"]["base_version_id"] is None
        assert (
            repository.version_store.current_version_id(captured["object_id"])
            == imported.version_id
        )
        assert repository.version_store.version_by_id(imported.version_id).state.value == "accepted"

        for included_evidence in manifest["evidence"]["included_evidence_ids"]:
            provenance = repository.source_store.evidence_provenance(included_evidence)
            assert provenance.source.source_id == captured["source_id"]
            assert provenance.snapshot.snapshot_id == captured["snapshot_id"]
            assert provenance.evidence.run_id == captured["run_id"]
    finally:
        repository.close()


def test_import_to_embedding_index_search_reuses_representation_and_isolates_versions(
    tmp_path, make_bundle
):
    repository = Repository(tmp_path / "n02-derived.sqlite")
    try:
        captured = _capture_and_associate(repository, tmp_path, make_bundle)
        first = _roundtrip_result(repository, captured["object_id"], tmp_path, "v1")["imported"]

        provider = DeterministicEmbeddingProvider()
        first_representations, first_created = _materialize_and_embed(
            repository,
            first.version_id,
            provider,
        )
        assert first_created == len(set(first_representations))
        assert len(provider.embedded_documents) == first_created
        first_embeddings = repository.embedding_store.embedding_rows(provider.space.space_id)

        vector_index = ExactVectorIndexAdapter()
        first_metadata = KnowledgeVectorIndexBuilder(repository, vector_index).rebuild(
            provider.space
        )
        assert first_metadata.points_count == len(first_representations)

        first_search = KnowledgeReadApplication(
            repository,
            embedding_provider=provider,
            vector_index=vector_index,
        ).search_objects("N02 semantic query", mode="semantic")
        assert first_search.results[0].version_id == first.version_id

        second_roundtrip = _roundtrip_result(repository, captured["object_id"], tmp_path, "v2")
        second = second_roundtrip["imported"]
        assert second.base_version_id == first.version_id

        second_representations, second_created = _materialize_and_embed(
            repository,
            second.version_id,
            provider,
        )
        assert set(second_representations) == set(first_representations)
        assert second_created == 0
        assert len(provider.embedded_documents) == first_created
        assert (
            repository.embedding_store.embedding_rows(provider.space.space_id) == first_embeddings
        )

        metadata = KnowledgeVectorIndexBuilder(repository, vector_index).rebuild(provider.space)
        memberships = repository.semantic_store.knowledge_search_memberships()
        assert metadata.points_count == len(memberships)
        assert metadata.points_count == len(first_representations) + len(second_representations)

        application = KnowledgeReadApplication(
            repository,
            embedding_provider=provider,
            vector_index=vector_index,
        )
        current = application.search_objects("N02 semantic query", mode="semantic")
        historical = application.search_objects(
            "N02 semantic query",
            mode="semantic",
            filters=ObjectSearchFilters(version_id=first.version_id),
        )
        assert current.results[0].version_id == second.version_id
        assert historical.results[0].version_id == first.version_id
        assert current.results[0].object_id == captured["object_id"]
        assert historical.results[0].object_id == captured["object_id"]
    finally:
        repository.close()


def test_mcp_adapter_reaches_real_application_and_retrieval_core(tmp_path, make_bundle):
    repository = Repository(tmp_path / "n02-mcp.sqlite")
    try:
        captured = _capture_and_associate(repository, tmp_path, make_bundle)
        imported = _roundtrip_result(repository, captured["object_id"], tmp_path, "v1")["imported"]
        SearchRepresentationBuilder(repository).materialize_version(imported.version_id)

        adapter = MCPReadAdapter(KnowledgeReadApplication(repository))
        object_payload = adapter.call_tool(
            "get_object",
            {"object_id": captured["object_id"]},
        )
        search_payload = adapter.call_tool(
            "search_objects",
            {"query": "N02 Character", "mode": "lexical", "limit": 10},
        )

        assert object_payload["data"]["object_id"] == captured["object_id"]
        assert object_payload["data"]["resolved_version_id"] == imported.version_id
        assert search_payload["data"]["results"][0]["object_id"] == captured["object_id"]
        assert search_payload["data"]["results"][0]["version_id"] == imported.version_id
    finally:
        repository.close()
