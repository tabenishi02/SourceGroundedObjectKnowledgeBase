"""Standalone, read-only v1.0 bundle reader. Does not depend on the extension host."""

import json
import re
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from ..domain import Bundle, digest

REQUIRED = {
    "manifest.json",
    "dom/main.html",
    "metadata/document.json",
    "metadata/html-metadata.json",
    "metadata/structured-data.json",
    "metadata/frames.json",
    "metadata/shadow-dom.json",
    "metadata/resources.json",
    "checksums.json",
}
MAX_BYTES = 512 * 1024 * 1024
STATES = {"success", "partial", "failed", "not_requested", "not_supported", "permission_denied"}


def classify(url):
    site = (urlsplit(url).hostname or "").lower()
    if site in {"dic.pixiv.net", "dic.nicovideo.jp", "ja.wikipedia.org"}:
        kind = "encyclopedia"
    elif any(x in site for x in ("wiki", "fandom.com")):
        kind = "wiki"
    elif site == "x.com":
        kind = "social_post"
    elif any(x in site for x in ("5ch.", "2chan.", "bbs.", "shitaraba", "bakusai", "reddit")):
        kind = "bbs"
    elif any(x in site for x in ("blog", "note.com", "hatenablog", "rakuten.co.jp")):
        kind = "blog"
    elif any(
        x in site
        for x in (
            "4gamer",
            "gamespark",
            "gigazine",
            "ign.",
            "oricon",
            "webnewtype",
            "famitsu",
            "news.",
        )
    ):
        kind = "news_article"
    else:
        kind = "generic_web"
    return site, kind


class WebCaptureImporter:
    version = "webcapture-1.0-reader-v1"

    def read(self, path):
        path = Path(path).resolve()
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Bundle exceeds size limit")
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [i.filename for i in entries]
            if len(entries) > 10000 or len(names) != len(set(names)):
                raise ValueError("Excessive or duplicate ZIP entries")
            if sum(i.file_size for i in entries) > MAX_BYTES:
                raise ValueError("Uncompressed bundle exceeds size limit")
            for name in names:
                parts = PurePosixPath(name).parts
                if (
                    "\\" in name
                    or ":" in name
                    or ".." in parts
                    or name.startswith("/")
                    or not name.startswith("capture/")
                    or name.endswith("/")
                ):
                    raise ValueError("Unsafe ZIP entry")
                relative = name[len("capture/") :]
                if (
                    relative not in REQUIRED
                    and relative != "archive/page.mhtml"
                    and not re.fullmatch(r"dom/frames/frame-\d{4}\.html", relative)
                ):
                    raise ValueError("Unknown v1.0 artifact")
            artifacts = {n[len("capture/") :]: archive.read(n) for n in names}
        if not REQUIRED <= artifacts.keys():
            raise ValueError("Missing required artifact")
        checksums = json.loads(artifacts["checksums.json"])
        if set(checksums) != set(artifacts) - {"checksums.json"}:
            raise ValueError("Checksum coverage mismatch")
        for name, expected in checksums.items():
            data = artifacts[name]
            if expected.get("sha256") != digest(data) or expected.get("bytes") != len(data):
                raise ValueError("Artifact checksum mismatch")
        manifest = json.loads(artifacts["manifest.json"])
        if (
            manifest.get("format") != "web-capture-bundle"
            or manifest.get("format_version") != "1.0"
        ):
            raise ValueError("Unsupported Web Capture format")
        capture_id = manifest["capture_id"]
        parsed = uuid.UUID(capture_id)
        if parsed.version != 4 or str(parsed) != capture_id:
            raise ValueError("capture_id must be lowercase UUID v4")
        timestamp = manifest["captured_at"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", timestamp):
            raise ValueError("Invalid capture timestamp")
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        expected_name = timestamp.replace("-", "").replace(":", "").replace(".", "") + "_"
        if path.name != expected_name + capture_id + ".webcapture.zip":
            raise ValueError("Bundle filename does not match manifest")
        page = manifest["page"]
        url = urlsplit(page["url"])
        if url.scheme not in {"http", "https", "file"} or not isinstance(page["title"], str):
            raise ValueError("Invalid page URL or title")
        if url.scheme != "file" and not url.hostname:
            raise ValueError("Page URL host required")
        components = manifest["components"]
        if components.get("main_dom") != "success" or any(
            components.get(k) not in STATES
            for k in ("main_dom", "metadata", "structured_data", "frames", "shadow_dom", "mhtml")
        ):
            raise ValueError("Invalid component states")
        if (components["mhtml"] == "success") != ("archive/page.mhtml" in artifacts):
            raise ValueError("MHTML status and artifact mismatch")
        metadata = {
            Path(n).stem: json.loads(v) for n, v in artifacts.items() if n.startswith("metadata/")
        }
        if metadata["document"].get("url") != page["url"]:
            raise ValueError("Document URL and manifest mismatch")
        for frame in metadata["frames"]:
            if frame.get("capture_status") == "success" and frame.get("file") not in artifacts:
                raise ValueError("Successful frame artifact missing")
        return Bundle(str(path), digest(path.read_bytes()), manifest, artifacts, metadata)
