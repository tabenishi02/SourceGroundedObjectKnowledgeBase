"""Exercise the standard workflow exclusively through the installed public CLI."""

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


class WorkflowCLI:
    def __init__(self, root):
        self.root = root
        self.db = root / "acceptance.sqlite"
        local_cli = Path(sys.executable).with_name("sgokb.exe" if os.name == "nt" else "sgokb")
        self.executable = str(local_cli) if local_cli.is_file() else shutil.which("sgokb")
        assert self.executable, "Install the project editable before CLI integration tests"
        self.records = []

    def __call__(self, *args, code=0):
        command = [self.executable, "--db", str(self.db), *map(str, args)]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45,
            cwd=self.root,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        self.records.append(
            {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        (self.root / "commands.json").write_text(
            json.dumps(self.records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        assert result.returncode == code, self.records[-1]
        payload = json.loads(result.stdout if code == 0 else result.stderr)
        assert payload["schema_version"] == "sgokb.cli/1.0"
        return payload["data"] if code == 0 else payload["error"]


def _result(manifest, instructions):
    # Deterministic transport fixture, not a claim about ChatGPT analysis quality.
    target = manifest["target"]
    result_schema = manifest["binding"]["expected_result_schema_version"]
    binding = {
        "package_id": manifest["package_id"],
        "package_schema_version": manifest["schema_version"],
        "manifest_sha256": manifest["integrity"]["manifest_sha256"],
        "package_created_at": manifest["created_at"],
        "base_version_id": manifest["binding"]["base_version_id"],
    }
    summary = {
        "local_key": "summary-1",
        "text": "M03 Example is a brave fictional character.",
        "derivation_kind": "direct_statement",
    }
    if result_schema == "sgokb.object-result/2.0":
        raw_grounding = manifest["raw_grounding"]
        binding.update(
            {
                "grounding_contract": manifest["binding"]["grounding_contract"],
                "grounding_set_sha256": raw_grounding["integrity"]["grounding_set_sha256"],
            }
        )
        summary["grounding"] = [
            {"raw_artifact_id": raw_id, "role": "supports"}
            for raw_id in raw_grounding["included_raw_artifact_ids"]
        ]
    else:
        summary["evidence"] = [
            {"evidence_id": eid, "role": "supports"}
            for eid in manifest["evidence"]["included_evidence_ids"]
        ]
    return {
        "schema_version": result_schema,
        "result_status": "complete",
        "target": {
            key: target[key] for key in ("object_id", "primary_class_id", "additional_class_ids")
        },
        "binding": binding,
        "generation": {
            "instructions_version": manifest["binding"]["instructions_version"],
            "generator_kind": "interactive_ai",
            "application": "M03 deterministic fixture",
            "generated_at": manifest["created_at"],
        },
        "knowledge": {
            "default_language": "en",
            "summary": [summary],
            "facets": [
                {"facet_id": facet_id, "status": "not_analyzed", "statements": []}
                for facet_id in re.findall(r"^- `(facet:[^`]+)`", instructions, re.MULTILINE)
            ],
            "attributes": [],
            "relations": [],
        },
        "conflicts": [],
        "gaps": [],
        "unresolved_references": [],
        "registry_proposals": [],
        "class_extensions": [],
    }


@pytest.fixture
def workflow(tmp_path, make_bundle, request):
    acceptance_root = os.environ.get("M03_ACCEPTANCE_ROOT")
    root = (Path(acceptance_root) / request.node.name if acceptance_root else tmp_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    assert not (root / "acceptance.sqlite").exists(), "Acceptance requires a fresh DB"
    cli = WorkflowCLI(root)
    assert cli("system", "integrity")["schema_migrations"] == list(range(3, 21))
    cli("registry", "class", "show", "character")
    obj = cli("object", "add", "--name", "M03 Example", "--primary-class", "character")
    oid = obj["object_id"]
    assert cli("object", "show", "--object", oid)["object_id"] == oid
    bundle = make_bundle(
        html=(
            "<html><body><main><h1>M03 Example</h1>"
            "<p>M03 Example is a brave fictional character.</p></main></body></html>"
        )
    )
    local_bundle = root / "raw" / bundle.name
    local_bundle.parent.mkdir()
    shutil.copyfile(bundle, local_bundle)
    source = cli("source", "import", local_bundle)[0]
    processed = cli("source", "process", "--snapshot", source["snapshot"])[0]
    assert processed["evidence"] > 0
    cli("association", "list", "--object", oid)
    cli(
        "association", "set", "--object", oid, "--source", source["source"], "--status", "confirmed"
    )
    cli("evidence", "candidates", "--object", oid)
    cli("evidence", "select", "--object", oid)
    built = cli("package", "build", "--object", oid, "--build-root", root / "build")
    assert built["evidence_count"] > 0
    staged = cli("package", "stage", built["path"], "--staging-root", root / "staging")
    destination = root / "external-destination"
    preflight = cli("package", "preflight", staged["path"], "--destination", destination)
    assert preflight["disposition"] == "allow", preflight
    exported = cli("package", "export", staged["path"], "--destination", destination)
    manifest = json.loads(Path(exported["path"], "manifest.json").read_text(encoding="utf-8"))
    incoming = root / "incoming"
    result_path = incoming / "drop" / built["package_id"] / "result.json"
    result_path.parent.mkdir(parents=True)
    instructions = Path(exported["path"], "instructions.md").read_text(encoding="utf-8")
    result_path.write_text(json.dumps(_result(manifest, instructions)), encoding="utf-8")
    assert cli("result", "detect", "--incoming-root", incoming)
    receipt = cli(
        "result",
        "receive",
        result_path,
        "--package-id",
        built["package_id"],
        "--incoming-root",
        incoming,
    )
    rid = receipt["receipt_id"]
    validation = cli("result", "validate", rid, "--incoming-root", incoming)
    assert validation["validation_state"] == "valid", validation
    review = cli(
        "result", "review", rid, "--incoming-root", incoming, "--review-format", "markdown"
    )
    assert isinstance(review, str) and review
    imported = cli("result", "import", rid, "--incoming-root", incoming)
    vid = imported["version_id"]
    knowledge = cli("object", "show", "--object", oid, "--knowledge")["knowledge"]
    assert knowledge["resolved_version_id"] == vid
    cli("object", "relations", "--object", oid)
    rendered = cli("render", "--object", oid, "--output-root", root / "render")
    assert "M03 Example" in Path(rendered["output_path"]).read_text(encoding="utf-8")
    search = cli("search", "M03 Example", "--mode", "lexical")
    assert any(item["object_id"] == oid for item in search["results"]), search
    assert cli("registry", "proposal", "list", "--decision", "pending") == []
    assert cli("system", "integrity")["ok"] is True
    ids = {
        "object_id": oid,
        "source_id": source["source"],
        "snapshot_id": source["snapshot"],
        "package_id": built["package_id"],
        "receipt_id": rid,
        "version_id": vid,
    }
    (root / "ids.json").write_text(json.dumps(ids, indent=2), encoding="utf-8")
    return cli, knowledge, ids


def test_standard_workflow(workflow):
    _, knowledge, ids = workflow
    assert knowledge["object_id"] == ids["object_id"]


def test_standard_workflow_mcp_read(workflow):
    mcp = pytest.importorskip("mcp", reason="MCP SDK v2 optional extra is required")
    cli, knowledge, ids = workflow

    async def read():
        params = mcp.StdioServerParameters(
            command=cli.executable,
            args=["--db", str(cli.db), "mcp", "serve"],
            env={**os.environ, "PYTHONUTF8": "1"},
        )
        async with mcp.Client(params) as client:
            tools = (await client.list_tools()).tools
            assert {tool.name for tool in tools} == {
                "search_objects",
                "find_similar_objects",
                "get_object",
                "get_objects",
                "get_object_relations",
                "get_object_evidence",
                "search_evidence",
                "build_context",
            }
            assert all(tool.annotations.read_only_hint is True for tool in tools)
            response = await client.call_tool("get_object", {"object_id": ids["object_id"]})
            assert response.is_error is False
            data = response.structured_content["data"]
            assert data == knowledge
            (cli.root / "mcp-read.json").write_text(
                json.dumps(response.structured_content, indent=2), encoding="utf-8"
            )

    before = hashlib.sha256(cli.db.read_bytes()).hexdigest()
    asyncio.run(asyncio.wait_for(read(), timeout=45))
    assert hashlib.sha256(cli.db.read_bytes()).hexdigest() == before
    assert (
        cli("object", "show", "--object", ids["object_id"], "--knowledge")["knowledge"] == knowledge
    )
