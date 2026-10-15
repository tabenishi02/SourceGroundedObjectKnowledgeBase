import hashlib
import json
import uuid
import zipfile

import pytest

HTML = """<!DOCTYPE html><html><head><meta charset="shift_jis"><script>SECRET UI</script></head>
<body><nav>REMOVE NAV</nav><main><h1>架空太郎</h1><p>架空太郎は勇敢で強い人物。</p>
<h2>能力</h2><p>strength and power. 架空太郎は氷を操る。</p>
<ul><li>仲間を助ける</li><li>冷静に判断する</li></ul>
<table><tr><th>所属</th><th>役割</th></tr><tr><td>架空団</td><td>隊長</td></tr></table>
<blockquote>架空太郎は優しいという意見。</blockquote>
<div class="post" data-post-id="1">投稿一 <a href="#2">返信先</a>
<time datetime="2026-01-01">時刻</time></div>
<div class="post" data-post-id="2">投稿二</div></main>
<footer>REMOVE FOOTER</footer></body></html>"""


@pytest.fixture
def make_bundle(tmp_path):
    def make(
        url="https://example.test/hero",
        html=HTML,
        capture_id=None,
        version="1.0",
        timestamp="2026-01-01T00:00:00.000Z",
        completeness="partial",
        warnings=None,
        mutate=None,
        extra=None,
    ):
        capture_id = capture_id or str(uuid.uuid4())
        manifest = {
            "format": "web-capture-bundle",
            "format_version": version,
            "capture_id": capture_id,
            "captured_at": timestamp,
            "page": {"url": url, "title": "架空太郎"},
            "capture_tool": {"name": "WebPageCapture", "version": "0.1.0"},
            "components": {
                k: "success"
                for k in ("main_dom", "metadata", "structured_data", "frames", "shadow_dom")
            },
            "completeness": completeness,
            "warnings": list(warnings or []),
        }
        manifest["components"]["mhtml"] = "failed"
        artifacts = {
            "manifest.json": json.dumps(manifest).encode(),
            "dom/main.html": html.encode("utf-8"),
            "metadata/document.json": json.dumps({"url": url, "title": "架空太郎"}).encode(),
            "metadata/html-metadata.json": b'{"meta":[],"links":[]}',
            "metadata/structured-data.json": b'{"json_ld":[],"microdata":[],"rdfa":[]}',
            "metadata/frames.json": b"[]",
            "metadata/shadow-dom.json": b"[]",
            "metadata/resources.json": b"[]",
        }
        if extra:
            artifacts.update(extra)
        artifacts["checksums.json"] = json.dumps(
            {
                k: {"sha256": hashlib.sha256(v).hexdigest(), "bytes": len(v)}
                for k, v in artifacts.items()
            }
        ).encode()
        if mutate:
            mutate(artifacts)
        name = timestamp.replace("-", "").replace(":", "").replace(".", "")
        path = tmp_path / (name + "_" + capture_id + ".webcapture.zip")
        with zipfile.ZipFile(path, "w") as z:
            for k, v in artifacts.items():
                z.writestr("capture/" + k, v)
        return path

    return make
