# ruff: noqa: I001 - sibling test fixture imports intentionally precede project imports.
from __future__ import annotations

import pytest
from test_hybrid_search import _accepted, _class, _engine
from test_hybrid_search_r2 import _activate_r2_generation

from sgokb.application_operator import OperatorSession
from sgokb.application_read import KnowledgeReadApplication, RetrievalRuntimeUnavailableError
from sgokb.domain import EmbeddingSpaceSpec, ObjectSearchChannel, ObjectSearchFilters
from sgokb.operation_contracts import OperationFailure, OperationRequest
from sgokb.repository import Repository
from sgokb.runtime import RuntimeFactory


@pytest.fixture
def repo(tmp_path):
    value = Repository(tmp_path / "p-gui-06-range-contract.sqlite")
    yield value
    value.close()


@pytest.fixture
def space():
    return EmbeddingSpaceSpec(
        provider_key="fake",
        provider_version="1",
        model="fake-model",
        model_revision="rev-1",
        dimension=3,
        native_dimension=3,
        preprocessing_key="sgokb-search-representation",
        preprocessing_version="2",
        normalize_embeddings=True,
        max_sequence_length=1024,
        overflow_policy="reject",
        output_dtype="float32",
        provider_configuration="{}",
    )


def test_from_to_does_not_hide_registry_identity_when_statements_do_not_overlap(repo, space):
    object_id = repo.object_store.create_object(
        "Temporal Identity Hero",
        _class(repo, "character"),
    )
    _accepted(
        repo,
        object_id,
        "temporal-identity-v1",
        statements=[
            {
                "facet": "personality",
                "text": "2026年だけ有効な知識",
                "temporal": {"valid_from": "2026-01-01", "valid_to": "2026-12-31"},
            }
        ],
    )
    engine, _ = _engine(repo, space)

    response = engine.search(
        "Temporal Identity Hero",
        mode="lexical",
        filters=ObjectSearchFilters(knowledge_valid_at="2100-01-01..2200-01-01"),
    )

    matching = [result for result in response.results if result.object_id == object_id]
    assert matching
    assert ObjectSearchChannel.EXACT_NAME in matching[0].channels
    assert all(match.statement_id is None for match in matching[0].matches)


def test_from_to_keeps_unversioned_registry_identity_through_production_r2_application(repo):
    object_id = repo.object_store.create_object(
        "Unversioned Temporal Identity",
        _class(repo, "character"),
    )
    _activate_r2_generation(repo, generation_id="range-contract-production-r2")
    repo.db.commit()

    response = KnowledgeReadApplication(repo).search_objects(
        "Unversioned Temporal Identity",
        mode="lexical",
        filters=ObjectSearchFilters(knowledge_valid_at="2100-01-01..2200-01-01"),
    )

    matching = [result for result in response.results if result.object_id == object_id]
    assert matching
    assert matching[0].version_id is None
    assert ObjectSearchChannel.EXACT_NAME in matching[0].channels


def _broken_nn_runtime():
    raise NameError("name 'nn' is not defined")


def test_runtime_factory_normalizes_transformers_nn_nameerror():
    factory = RuntimeFactory(semantic_builder=_broken_nn_runtime)
    with pytest.raises(RetrievalRuntimeUnavailableError, match=r"PyTorch >=2\.6"):
        factory.semantic_runtime()


def test_operator_reports_nn_dependency_failure_as_runtime_unavailable(tmp_path):
    factory = RuntimeFactory(semantic_builder=_broken_nn_runtime)
    session = OperatorSession(tmp_path / "runtime-nn.sqlite", runtime_factory=factory)

    with pytest.raises(OperationFailure) as exc:
        session.execute(
            OperationRequest(
                "search",
                {
                    "query": "runtime probe",
                    "mode": "semantic",
                    "semantic_runtime": True,
                },
            )
        )

    assert exc.value.category == "runtime"
    assert exc.value.code == "retrieval_runtime_unavailable"
    assert "PyTorch >=2.6" in exc.value.message
