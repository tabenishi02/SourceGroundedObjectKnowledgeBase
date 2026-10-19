"""Windows process/pipe regression tests; no Chrome or registry changes."""

import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from test_host import ROOT, bundle, host


@unittest.skipUnless(os.name == "nt", "Windows launcher requires .NET Framework")
class WindowsLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        (cls.root / "native-host").mkdir()
        (cls.root / ".local").mkdir()
        script = cls.root / "native-host" / "host.py"
        shutil.copyfile(ROOT / "native-host" / "host.py", script)
        cls.origin = "chrome-extension://" + "a" * 32 + "/"
        (cls.root / ".local" / "host-manifest.json").write_text(
            json.dumps({"allowed_origins": [cls.origin]}), encoding="utf-8"
        )
        compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        if not compiler.exists():
            raise unittest.SkipTest(".NET Framework C# compiler unavailable")
        source = (
            (ROOT / "native-host" / "Launcher.cs")
            .read_text()
            .replace("__PYTHON__", sys.executable.replace('"', '""'))
            .replace("__HOST__", str(script).replace('"', '""'))
        )
        source_path = cls.root / "Launcher.cs"
        source_path.write_text(source, encoding="utf-8")
        cls.exe = cls.root / "host.exe"
        result = subprocess.run(
            [str(compiler), "/nologo", "/target:exe", "/out:" + str(cls.exe), str(source_path)],
            capture_output=True,
            timeout=15,
        )
        if result.returncode:
            raise AssertionError("Windows launcher compile failed")

    def launch(self, origin=None):
        process = subprocess.Popen(
            [str(self.exe), origin or self.origin],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        def cleanup():
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

        self.addCleanup(cleanup)
        return process

    def test_persistent_handshake_and_actual_multichunk_save(self):
        process = self.launch()
        responses = queue.Queue()

        def read():
            try:
                while True:
                    message = host.read_message(process.stdout)
                    if message is None:
                        return
                    responses.put(message)
            except Exception as error:
                responses.put(error)

        threading.Thread(target=read, daemon=True).start()

        def request(message):
            host.write_message(process.stdin, message)
            response = responses.get(timeout=5)
            self.assertIsInstance(response, dict)
            return response

        for _ in range(2):
            self.assertTrue(request({"command": "hello"})["success"])
        tid = "11111111-1111-4111-8111-111111111111"
        filename = "20261004T102030123Z_" + tid + ".webcapture.zip"
        data = bundle(tid)
        begin = {"command": "begin", "transfer_id": tid, "filename": filename, "size": len(data)}
        self.assertTrue(request(begin)["success"])
        import base64

        count = 0
        for offset in range(0, len(data), 512):
            self.assertTrue(
                request(
                    {
                        "command": "chunk",
                        "transfer_id": tid,
                        "sequence": count,
                        "data": base64.b64encode(data[offset : offset + 512]).decode(),
                    }
                )["success"]
            )
            count += 1
        self.assertTrue(
            request({"command": "finish", "transfer_id": tid, "chunks": count})["success"]
        )
        self.assertEqual((self.root / "local-captures" / filename).read_bytes(), data)
        self.assertEqual(request(begin)["error"], "capture_exists")

    def test_unapproved_origin_fails(self):
        process = self.launch("chrome-extension://" + "b" * 32 + "/")
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 1)
        self.assertIn(b"host_protocol_or_registration_failed", stdout)
        self.assertEqual(stderr, b"")
