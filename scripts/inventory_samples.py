"""Inspect private bundles without copying their contents into tracked files."""

import collections
import hashlib
import json
import pathlib
import zipfile
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


def inventory(root):
    rows = []
    for path in sorted(pathlib.Path(root).rglob("*.webcapture.zip")):
        with zipfile.ZipFile(path) as z:
            manifest = json.loads(z.read("capture/manifest.json"))
            html = BeautifulSoup(z.read("capture/dom/main.html").decode("utf-8"), "html.parser")
            structured = json.loads(z.read("capture/metadata/structured-data.json"))
            frames = json.loads(z.read("capture/metadata/frames.json"))
            shadows = json.loads(z.read("capture/metadata/shadow-dom.json"))
            rows.append(
                {
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "capture_id": manifest["capture_id"],
                    "version": manifest["format_version"],
                    **manifest["page"],
                    "site": urlsplit(manifest["page"]["url"]).hostname,
                    "captured_at": manifest["captured_at"],
                    "artifacts": z.namelist(),
                    "components": manifest["components"],
                    "json_ld": len(structured["json_ld"]),
                    "frames": len(frames),
                    "successful_frames": sum(f["capture_status"] == "success" for f in frames),
                    "shadows": len(shadows),
                    "mhtml": "capture/archive/page.mhtml" in z.namelist(),
                    "structure": dict(
                        collections.Counter(
                            t.name
                            for t in html.find_all(
                                ["h1", "h2", "h3", "p", "li", "table", "blockquote", "article"]
                            )
                        )
                    ),
                    "roots": [
                        {"tag": t.name, "id": t.get("id"), "class": t.get("class")}
                        for t in html.select(
                            "main, article, #mw-content-text, #content, #body, .post"
                        )
                    ][:12],
                }
            )
    return rows


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    rows = inventory("sample")
    pathlib.Path(".local").mkdir(exist_ok=True)
    pathlib.Path(".local/sample-inventory.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "count": len(rows),
                "sites": dict(collections.Counter(r["site"] for r in rows)),
                "features": {
                    k: sum(bool(r[k]) for r in rows)
                    for k in ["json_ld", "frames", "shadows", "mhtml"]
                },
                "versions": dict(collections.Counter(r["version"] for r in rows)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
