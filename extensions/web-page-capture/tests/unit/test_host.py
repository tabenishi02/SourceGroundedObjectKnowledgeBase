import base64
import hashlib
import importlib.util
import io
import json
import os
import struct
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("host", ROOT / "native-host" / "host.py")
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


def bundle(tid, timestamp="2026-10-04T10:20:30.123Z", transform=None):
    manifest = {
        "format": "web-capture-bundle",
        "format_version": "1.0",
        "capture_id": tid,
        "captured_at": timestamp,
        "capture_tool": {"name": "WebPageCapture", "version": "0.1.0"},
        "page": {"url": "https://example.invalid/", "title": "Synthetic"},
        "completeness": "partial",
        "components": {
            "main_dom": "success",
            "metadata": "success",
            "structured_data": "success",
            "frames": "partial",
            "shadow_dom": "partial",
            "mhtml": "failed",
        },
        "warnings": [{"code": "mhtml_failed"}],
    }
    if transform:
        transform(manifest)
    files = {
        "manifest.json": json.dumps(manifest).encode(),
        "dom/main.html": b"<!DOCTYPE html><html><body>synthetic</body></html>",
    }
    for name in ["document", "html-metadata", "structured-data"]:
        files["metadata/" + name + ".json"] = b"{}"
    for name in ["frames", "shadow-dom", "resources"]:
        files["metadata/" + name + ".json"] = b"[]"
    files["checksums.json"] = json.dumps(
        {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in files.items()
        }
    ).encode()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in files.items():
            archive.writestr("capture/" + name, data)
    return stream.getvalue()


class HostTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.destination = Path(self.directory.name) / "captures"
        self.session = host.StorageSession(self.destination)
        self.tid = str(uuid.uuid4())
        self.filename = "20261004T102030123Z_" + self.tid + ".webcapture.zip"
        self.data = bundle(self.tid)

    def tearDown(self):
        self.session.cleanup()
        self.directory.cleanup()

    def begin(self, data=None, filename=None):
        return self.session.handle(
            {
                "command": "begin",
                "transfer_id": self.tid,
                "filename": filename or self.filename,
                "size": len(data if data is not None else self.data),
            }
        )

    def chunk(self, data=None, sequence=0):
        return self.session.handle(
            {
                "command": "chunk",
                "transfer_id": self.tid,
                "sequence": sequence,
                "data": base64.b64encode(self.data if data is None else data).decode(),
            }
        )

    def finish(self, chunks=1):
        return self.session.handle({"command": "finish", "transfer_id": self.tid, "chunks": chunks})

    def assert_no_files(self):
        self.assertFalse(list(self.destination.glob("*")) if self.destination.exists() else [])

    def test_save_partial_bundle_and_stream_checksum(self):
        self.assertTrue(self.begin()["success"])
        self.assertTrue(self.chunk()["success"])
        result = self.finish()
        self.assertTrue(result["success"])
        self.assertEqual(result["sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertEqual((self.destination / self.filename).read_bytes(), self.data)

    def test_duplicate_never_overwrites(self):
        self.begin()
        self.chunk()
        self.finish()
        before = (self.destination / self.filename).read_bytes()
        self.assertEqual(self.begin()["error"], "capture_exists")
        self.assertEqual((self.destination / self.filename).read_bytes(), before)

    def test_same_url_distinct_capture_ids(self):
        self.begin()
        self.chunk()
        self.finish()
        self.tid = str(uuid.uuid4())
        self.filename = "20261004T102030123Z_" + self.tid + ".webcapture.zip"
        self.data = bundle(self.tid)
        self.begin()
        self.chunk()
        self.assertTrue(self.finish()["success"])
        self.assertEqual(len(list(self.destination.glob("*.webcapture.zip"))), 2)

    def test_path_traversal_and_invalid_filenames(self):
        for filename in [
            "../" + self.filename,
            "..\\" + self.filename,
            "C:\\" + self.filename,
            "CON",
            "a/b.zip",
            "a:stream",
            "title.webcapture.zip",
            self.filename + " ",
        ]:
            with self.subTest(filename=filename):
                self.assertEqual(self.begin(filename=filename)["error"], "invalid_filename")
        self.assert_no_files()

    def test_invalid_message_types_fields_commands(self):
        for message in [
            [],
            None,
            {"command": []},
            {"command": "exec"},
            {"command": "hello", "path": "../"},
            {"command": "begin"},
        ]:
            self.assertFalse(self.session.handle(message)["success"])
        self.assert_no_files()

    def test_invalid_sizes_and_ids(self):
        for size in [True, -1, 0, host.MAX_BUNDLE + 1, "10"]:
            self.assertFalse(
                self.session.handle(
                    {
                        "command": "begin",
                        "transfer_id": self.tid,
                        "filename": self.filename,
                        "size": size,
                    }
                )["success"]
            )
        self.tid = "../escape"
        self.assertFalse(self.begin()["success"])
        self.assert_no_files()

    def test_missing_and_out_of_order_chunks(self):
        self.begin()
        self.assertEqual(self.chunk(sequence=1)["error"], "invalid_sequence")
        self.assert_no_files()

    def test_duplicate_chunk(self):
        self.begin()
        self.chunk()
        self.assertEqual(self.chunk()["error"], "invalid_sequence")
        self.assert_no_files()

    def test_missing_bytes_and_finish_count(self):
        for count in [0, 1, True]:
            self.begin()
            self.chunk(data=self.data[:10])
            self.assertEqual(self.finish(count)["error"], "incomplete_transfer")
            self.assert_no_files()

    def test_invalid_base64_and_oversize_chunk(self):
        for data in [
            "!",
            "あ",
            "A" * (host.MAX_CHUNK * 4 // 3 + 1),
            base64.b64encode(self.data + b"x").decode(),
        ]:
            self.begin()
            self.assertFalse(
                self.session.handle(
                    {"command": "chunk", "transfer_id": self.tid, "sequence": 0, "data": data}
                )["success"]
            )
            self.assert_no_files()

    def test_disconnect_cleans_temporary_data(self):
        self.begin()
        self.chunk(data=self.data[:10])
        self.session.cleanup()
        self.assert_no_files()

    def test_invalid_zip_has_no_final_bundle(self):
        self.begin()
        self.chunk(data=b"x" * len(self.data))
        self.assertFalse(self.finish()["success"])
        self.assert_no_files()

    def test_checksum_corruption(self):
        corrupted = self.data.replace(b"synthetic", b"corrupted", 1)
        self.begin()
        self.chunk(data=corrupted)
        self.assertFalse(self.finish()["success"])
        self.assert_no_files()

    def test_invalid_format_and_failed_main_dom(self):
        for transform in [
            lambda m: m.update(format_version="2.0"),
            lambda m: m["components"].update(main_dom="failed"),
            lambda m: m.update(completeness="failed"),
            lambda m: m["components"].update(mhtml="success"),
            lambda m: m.update(capture_id=str(uuid.uuid4())),
        ]:
            data = bundle(self.tid, transform=transform)
            self.begin(data)
            self.chunk(data)
            self.assertFalse(self.finish()["success"])
            self.assert_no_files()

    def test_zip_path_traversal(self):
        stream = io.BytesIO(self.data)
        with zipfile.ZipFile(stream, "a") as archive:
            archive.writestr("capture/../../escape", "bad")
        data = stream.getvalue()
        self.begin(data)
        self.chunk(data)
        self.assertEqual(self.finish()["error"], "invalid_artifact_path")
        self.assert_no_files()

    def test_write_flush_and_rename_failures_leave_no_final_bundle(self):
        for operation in ["fsync", "rename" if os.name == "nt" else "link"]:
            self.begin()
            self.chunk()
            with patch.object(host.os, operation, side_effect=OSError("synthetic failure")):
                self.assertFalse(self.finish()["success"])
            self.assert_no_files()

    def test_destination_write_failure(self):
        with patch.object(host.tempfile, "mkstemp", side_effect=PermissionError()):
            self.assertFalse(self.begin()["success"])
        self.assert_no_files()

    def test_publication_race_never_overwrites_existing_file(self):
        self.begin()
        self.chunk()
        target = self.destination / self.filename
        target.write_bytes(b"existing")
        self.assertFalse(self.finish()["success"])
        self.assertEqual(target.read_bytes(), b"existing")
        self.assertEqual(len(list(self.destination.iterdir())), 1)

    def test_multichunk_bundle(self):
        self.begin()
        count = 0
        for offset in range(0, len(self.data), 100):
            self.assertTrue(self.chunk(self.data[offset : offset + 100], count)["success"])
            count += 1
        self.assertTrue(self.finish(count)["success"])

    def test_native_binary_framing_and_malformed_messages(self):
        stream = io.BytesIO()
        host.write_message(stream, {"command": "hello", "text": "日本語"})
        stream.seek(0)
        self.assertEqual(host.read_message(stream)["text"], "日本語")
        for data in [
            b"\x01",
            struct.pack("=I", host.MAX_MESSAGE + 1),
            struct.pack("=I", 5) + b"{}",
            struct.pack("=I", 1) + b"x",
        ]:
            with self.assertRaises(ValueError):
                host.read_message(io.BytesIO(data))
        self.assertIsNone(host.read_message(io.BytesIO()))


if __name__ == "__main__":
    unittest.main()
