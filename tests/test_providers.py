import json

import httpx
import pytest

from cpc.providers import CompatibleEmbedder, CompatibleLLM


def test_compatible_requests_and_embedding_order():
    requests = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        if request.url.path.endswith("/embeddings"):
            return httpx.Response(
                200,
                json={
                    "data": [{"index": 1, "embedding": [0, 1]}, {"index": 0, "embedding": [1, 0]}]
                },
            )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}]},
        )

    transport = httpx.MockTransport(handle)
    embedding = CompatibleEmbedder(
        "https://example.test/v1", "embed", document_prefix="doc: ", transport=transport
    )
    assert embedding.embed(["a", "b"]) == [[1, 0], [0, 1]]
    assert requests[0]["input"] == ["doc: a", "doc: b"]
    llm = CompatibleLLM("https://example.test/v1", "llm", transport=transport)
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    assert json.loads(llm.complete("instruction", {"x": "text"}, schema=schema))["ok"]
    assert requests[1]["messages"][0]["role"] == "system"
    assert requests[1]["response_format"]["type"] == "json_schema"
    assert requests[1]["response_format"]["json_schema"]["schema"] == schema


def test_truncated_llm_output_rejected():
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200, json={"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
        )
    )
    with pytest.raises(ValueError, match="truncated"):
        CompatibleLLM("https://example.test/v1", "test", transport=transport).complete("", {})
