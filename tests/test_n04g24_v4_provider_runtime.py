from __future__ import annotations

import pytest

from sgokb.grounding.v4_contracts import (
    PROVIDER_COMPLETE,
    PROVIDER_INCOMPLETE,
    PROVIDER_UNAVAILABLE,
    V4ProviderRuntimeError,
    require_complete_provider_response,
)


def test_complete_provider_response_returns_raw_output() -> None:
    raw = '{"candidates":[]}'
    result = require_complete_provider_response(
        {"status": PROVIDER_COMPLETE, "raw_output": raw}
    )
    assert result == raw


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (PROVIDER_INCOMPLETE, "PROVIDER_INCOMPLETE"),
        (PROVIDER_UNAVAILABLE, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_incomplete_or_unavailable_provider_response_fails_closed(
    status: str,
    code: str,
) -> None:
    with pytest.raises(V4ProviderRuntimeError) as error:
        require_complete_provider_response({"status": status})
    assert error.value.code == code


def test_complete_provider_response_requires_payload() -> None:
    with pytest.raises(V4ProviderRuntimeError) as error:
        require_complete_provider_response({"status": PROVIDER_COMPLETE})
    assert error.value.code == "PROVIDER_MISSING_PAYLOAD"
