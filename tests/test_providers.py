import json

import httpx

from sgokb.providers import CompatibleEmbedder


def test_compatible_embedding_order_and_document_prefix():
    requests = []

    def handle(request):
        assert request.url.path.endswith("/embeddings")
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={"data": [{"index": 1, "embedding": [0, 1]}, {"index": 0, "embedding": [1, 0]}]},
        )

    transport = httpx.MockTransport(handle)
    embedding = CompatibleEmbedder(
        "https://example.test/v1", "embed", document_prefix="doc: ", transport=transport
    )
    assert embedding.embed(["a", "b"]) == [[1, 0], [0, 1]]
    assert requests[0]["input"] == ["doc: a", "doc: b"]
