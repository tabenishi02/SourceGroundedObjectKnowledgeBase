from __future__ import annotations

import pytest

from sgokb.application_operator import OperatorSession
from sgokb.application_read import RetrievalRuntimeUnavailableError
from sgokb.operation_contracts import OperationFailure, OperationRequest
from sgokb.runtime import RuntimeFactory


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
