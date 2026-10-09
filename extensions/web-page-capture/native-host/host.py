"""Native Messaging storage bridge. No CPC imports or page interpretation."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent.parent
HOST_NAME = "com.sgokb.web_page_capture"
MAX_MESSAGE = 300 * 1024
MAX_CHUNK = 192 * 1024
MAX_BUNDLE = 512 * 1024 * 1024
STATUSES = {"success", "partial", "failed", "not_requested", "not_supported", "permission_denied"}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
FILENAME = re.compile(r"\d{8}T\d{9}Z_(" + UUID + r")\.webcapture\.zip\Z")
REQUIRED = {
    "manifest.json", "checksums.json", "dom/main.html", "metadata/document.json",
    "metadata/html-metadata.json", "metadata/structured-data.json", "metadata/frames.json",
    "metadata/shadow-dom.json", "metadata/resources.json",
}


def require(condition, code="invalid_message"):
    if not condition:
        raise ValueError(code)


def validate_bundle(path, transfer_id, filename):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = {entry.filename for entry in entries}
        require(len(names) == len(entries) and len(entries) <= 10000, "invalid_bundle_entries")
        require({"capture/" + name for name in REQUIRED} <= names, "missing_artifact")
        for entry in entries:
            name = entry.filename
            require(name.startswith("capture/"), "invalid_artifact_path")
            relative = name[len("capture/"):]
            require(relative in REQUIRED or relative == "archive/page.mhtml" or re.fullmatch(r"dom/frames/frame-\d{4,}.html", relative), "invalid_artifact_path")
            require(entry.compress_type == zipfile.ZIP_STORED and not entry.flag_bits & 1, "unsupported_zip_encoding")
        require(sum(e.file_size for e in entries) <= MAX_BUNDLE, "bundle_too_large")
        manifest = json.loads(archive.read("capture/manifest.json"))
        checksums = json.loads(archive.read("capture/checksums.json"))
        require(isinstance(manifest, dict) and isinstance(checksums, dict), "invalid_bundle_schema")
        require(manifest.get("format") == "web-capture-bundle" and manifest.get("format_version") == "1.0", "unsupported_format")
        require(manifest.get("capture_id") == transfer_id, "capture_id_mismatch")
        timestamp = manifest.get("captured_at", "")
        from datetime import datetime
        require(isinstance(timestamp, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", timestamp), "invalid_timestamp")
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        require(filename == re.sub(r"[-:.]", "", timestamp) + "_" + transfer_id + ".webcapture.zip", "filename_mismatch")
        tool, page = manifest.get("capture_tool"), manifest.get("page")
        require(isinstance(tool, dict) and tool.get("name") == "WebPageCapture" and isinstance(tool.get("version"), str), "invalid_tool")
        require(isinstance(page, dict) and isinstance(page.get("url"), str) and isinstance(page.get("title"), str), "invalid_page")
        components = manifest.get("components")
        require(isinstance(components, dict) and set(components) == {"main_dom", "metadata", "structured_data", "frames", "shadow_dom", "mhtml"}, "invalid_components")
        require(all(isinstance(s, str) and s in STATUSES for s in components.values()), "invalid_status")
        require(components["main_dom"] == "success" and manifest.get("completeness") in {"success", "partial"}, "failed_main_dom")
        require(isinstance(manifest.get("warnings"), list), "invalid_warnings")
        require(("capture/archive/page.mhtml" in names) == (components["mhtml"] == "success"), "mhtml_status_mismatch")
        require(set(checksums) == {n[len("capture/"):] for n in names if n != "capture/checksums.json"}, "invalid_checksums")
        for name, expected in checksums.items():
            require(isinstance(expected, dict) and re.fullmatch(r"[0-9a-f]{64}", str(expected.get("sha256"))), "invalid_checksum")
            digest, size = hashlib.sha256(), 0
            with archive.open("capture/" + name) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
            require(digest.hexdigest() == expected["sha256"] and size == expected.get("bytes"), "checksum_mismatch")
        require(archive.getinfo("capture/dom/main.html").file_size > 0, "empty_main_dom")
        for name, expected_type in [("document", dict), ("html-metadata", dict), ("structured-data", dict), ("frames", list), ("shadow-dom", list), ("resources", list)]:
            require(isinstance(json.loads(archive.read("capture/metadata/" + name + ".json")), expected_type), "invalid_metadata")


class StorageSession:
    def __init__(self, destination=None):
        self.destination = Path(destination) if destination is not None else ROOT / "local-captures"
        self.state = None

    def cleanup(self):
        if self.state:
            state = self.state
            self.state = None
            try:
                state["stream"].close()
            finally:
                state["path"].unlink(missing_ok=True)

    def handle(self, message):
        try:
            return self._handle(message)
        except ValueError as error:
            self.cleanup()
            return {"success": False, "error": str(error)}
        except (OSError, zipfile.BadZipFile, TypeError, KeyError, OverflowError):
            self.cleanup()
            return {"success": False, "error": "save_or_bundle_validation_failed"}

    def _handle(self, message):
        require(isinstance(message, dict))
        command = message.get("command")
        fields = {"hello": {"command"}, "begin": {"command", "transfer_id", "filename", "size"}, "chunk": {"command", "transfer_id", "sequence", "data"}, "finish": {"command", "transfer_id", "chunks"}}
        require(isinstance(command, str) and command in fields and set(message) == fields[command])
        if command == "hello":
            require(self.state is None, "transfer_in_progress")
            return {"success": True, "protocol_version": "1.0"}
        tid = message["transfer_id"]
        require(isinstance(tid, str) and re.fullmatch(UUID, tid), "invalid_transfer_id")
        if command == "begin":
            require(self.state is None, "transfer_in_progress")
            filename, size = message["filename"], message["size"]
            require(isinstance(filename, str) and FILENAME.fullmatch(filename) and FILENAME.fullmatch(filename).group(1) == tid, "invalid_filename")
            require(type(size) is int and 0 < size <= MAX_BUNDLE, "invalid_size")
            require(not self.destination.is_symlink(), "unsafe_destination")
            self.destination.mkdir(parents=True, exist_ok=True)
            require(not (self.destination / filename).exists(), "capture_exists")
            fd, path = tempfile.mkstemp(prefix=".transfer-", suffix=".tmp", dir=self.destination)
            self.state = {"id": tid, "filename": filename, "size": size, "received": 0, "sequence": 0, "path": Path(path), "stream": os.fdopen(fd, "wb", buffering=0), "digest": hashlib.sha256()}
            return {"success": True}
        state = self.state
        require(state is not None and state["id"] == tid, "unknown_transfer")
        if command == "chunk":
            require(type(message["sequence"]) is int and message["sequence"] == state["sequence"], "invalid_sequence")
            data = message["data"]
            require(isinstance(data, str) and len(data) <= MAX_CHUNK * 4 // 3, "invalid_chunk")
            try:
                block = base64.b64decode(data, validate=True)
            except (ValueError, base64.binascii.Error):
                raise ValueError("invalid_chunk") from None
            require(0 < len(block) <= MAX_CHUNK and state["received"] + len(block) <= state["size"], "invalid_chunk_size")
            state["stream"].write(block)
            state["digest"].update(block)
            state["received"] += len(block)
            state["sequence"] += 1
            return {"success": True, "sequence": message["sequence"]}
        require(type(message["chunks"]) is int and message["chunks"] == state["sequence"] and state["received"] == state["size"], "incomplete_transfer")
        state["stream"].flush()
        os.fsync(state["stream"].fileno())
        state["stream"].close()
        validate_bundle(state["path"], tid, state["filename"])
        target = self.destination / state["filename"]
        if os.name == "nt":
            os.rename(state["path"], target)  # Windows rename fails if destination exists.
        else:
            os.link(state["path"], target)  # Exclusive publication on other platforms.
            state["path"].unlink()
        result = {"success": True, "filename": state["filename"], "sha256": state["digest"].hexdigest()}
        self.state = None
        return result


def read_exact(stream, size):
    data = bytearray()
    while len(data) < size:
        block = stream.read(size - len(data))
        if not block:
            raise ValueError("truncated_message")
        data.extend(block)
    return bytes(data)


def read_message(stream):
    first = stream.read(1)
    if not first:
        return None
    size = struct.unpack("=I", first + read_exact(stream, 3))[0]
    require(0 < size <= MAX_MESSAGE, "message_too_large")
    return json.loads(read_exact(stream, size).decode("utf-8"))


def write_message(stream, message):
    data = json.dumps(message, ensure_ascii=True).encode("utf-8")
    stream.write(struct.pack("=I", len(data)) + data)
    stream.flush()


def main():
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    session = StorageSession()
    try:
        registration = json.loads((ROOT / ".local" / "host-manifest.json").read_text(encoding="utf-8-sig"))
        require(len(sys.argv) >= 2 and sys.argv[1] in registration["allowed_origins"], "origin_not_allowed")
        while True:
            message = read_message(sys.stdin.buffer)
            if message is None:
                break
            write_message(sys.stdout.buffer, session.handle(message))
    except (ValueError, OSError, KeyError, UnicodeError):
        write_message(sys.stdout.buffer, {"success": False, "error": "host_protocol_or_registration_failed"})
        return 1
    finally:
        session.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
