import pytest

from sgokb.domain import validate_vectors
from sgokb.ingestion.extraction import ExtractorRegistry, GenericExtractor, chunks
from sgokb.ingestion.importer import WebCaptureImporter


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a.pop("dom/main.html"),
        lambda a: a.update({"dom/main.html": b"CORRUPT"}),
        lambda a: a.update({"../escape": b"BAD"}),
        lambda a: a.update({"checksums.json": b"{}"}),
    ],
)
def test_bundle_integrity(make_bundle, mutation):
    with pytest.raises(ValueError):
        WebCaptureImporter().read(make_bundle(mutate=mutation))


def test_chunk_offsets_overlap_and_section():
    blocks = GenericExtractor().extract_html("<body><h2>Test</h2><p>" + "a" * 250 + "</p></body>")
    evidence = chunks(blocks, size=100, overlap=10)
    long = [e for e in evidence if e["kinds"] == ["paragraph"]]
    assert [e["start"] for e in long] == [0, 90, 180]
    assert all(e["section"] == ["Test"] for e in long)
    assert long[0]["content"][-10:] == long[1]["content"][:10]


@pytest.mark.parametrize("vectors", [[], [[0, 0]], [[float("nan"), 1]], [[1, 2], [1]]])
def test_vector_validation(vectors):
    with pytest.raises(ValueError):
        validate_vectors(vectors, 1)


def test_site_specific_roots():
    registry = ExtractorRegistry()
    html = (
        '<body><div>OUTSIDE UI</div><div id="mw-content-text">'
        '<div class="mw-parser-output"><h2>Topic</h2><p>Inside article</p></div></div></body>'
    )
    blocks = registry.select("ja.wikipedia.org").extract_html(html)
    assert "OUTSIDE" not in "\n".join(b.content for b in blocks)
    assert "Inside article" in "\n".join(b.content for b in blocks)
    assert registry.select("dic.pixiv.net").name == "pixiv-encyclopedia"
    assert registry.select("unknown.example").name == "generic"


def test_noise_widgets_keep_body_structure_and_provenance():
    from sgokb.ingestion.extraction import GenericExtractor

    html = (
        '<body><div class="site-header">NOISE</div><div id="content"><h1>主題</h1>'
        "<p>人物本文を保持する。長い説明と関連作品の解説。</p>"
        '<div class="related-posts">NOISE</div><table><tr><td>年齢</td><td>17</td></tr></table>'
        "<ul><li>本文リスト</li></ul><blockquote>引用本文</blockquote></div>"
        '<div class="ranking-widget">NOISE</div></body>'
    )
    blocks = GenericExtractor().extract_html(html)
    assert not any("NOISE" in b.content for b in blocks)
    assert {"heading", "paragraph", "table", "list", "quote"} <= {b.kind for b in blocks}
    assert all(b.position.startswith("/body[0]/div[1]") for b in blocks)
