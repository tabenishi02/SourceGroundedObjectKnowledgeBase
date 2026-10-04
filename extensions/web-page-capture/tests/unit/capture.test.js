import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {spawnSync} from "node:child_process";
import {JSDOM} from "jsdom";
import {captureDocument} from "../../extension/src/capture/dom.js";
import {buildBundle, captureFilename, sha256} from "../../extension/src/shared/bundle.js";
import {CHUNK_SIZE, transferBundle} from "../../extension/src/background/native.js";

const id = "11111111-1111-4111-8111-111111111111";
function snapshot() {
  const dom = new JSDOM(readFileSync(new URL("../fixtures/page.html", import.meta.url), "utf8"), {url: "https://example.invalid/page", runScripts: "dangerously"});
  dom.window.document.getElementById("more").click();
  globalThis.document = dom.window.document;
  globalThis.XMLSerializer = dom.window.XMLSerializer;
  const raw = captureDocument();
  dom.window.close();
  return raw;
}
test("Rendered DOM preserves raw elements, expansion, nested shadow and excludes property-only values", () => {
  const raw = snapshot(), main = raw.documents[0];
  for (const text of ["<!DOCTYPE html>", "<script", "<style", "<nav", "Advertisement", "<footer", "JavaScript content", "attribute-only"]) assert.ok(main.html.includes(text), text);
  assert.ok(!main.html.includes('id="extra" hidden'));
  // Script source includes the synthetic values; only check serialized input attributes.
  assert.match(main.html, /<input id="input" value="attribute-only">/);
  assert.match(main.html, /<input type="password" id="password">/);
  assert.equal(main.document.url, "https://example.invalid/page");
  assert.equal(main.document.canonical_url, "https://example.invalid/canonical");
  assert.equal(main.structured_data.json_ld[0].raw, '{"@type":"Thing","name":"Fixture"}');
  assert.equal(raw.shadows.length, 2);
  assert.match(raw.shadows[1].html, /Nested shadow/);
  assert.equal(raw.frames.length, 2);
  assert.ok(raw.warnings.some(w => w.code === "closed_shadow_dom_unobservable"));
});
test("Bundle v1.0 round-trips through independent Python ZIP/checksum/schema validation", async () => {
  const raw = snapshot();
  raw.documents[0].document.captured_at = "2026-10-04T10:20:30.123Z";
  const bundle = await buildBundle(raw, new Blob(["MIME-Version: 1.0\r\nsynthetic MHTML"]), null, "0.1.0", id);
  assert.equal(bundle.manifest.format_version, "1.0");
  assert.equal(bundle.manifest.components.mhtml, "success");
  const code = `import sys, tempfile, pathlib, importlib.util\nspec=importlib.util.spec_from_file_location('host','native-host/host.py'); h=importlib.util.module_from_spec(spec); spec.loader.exec_module(h)\nwith tempfile.TemporaryDirectory() as d:\n p=pathlib.Path(d)/'bundle.zip'; p.write_bytes(sys.stdin.buffer.read()); h.validate_bundle(p,'${id}','${bundle.filename}')\n`;
  const result = spawnSync("python", ["-c", code], {input: Buffer.from(await bundle.blob.arrayBuffer()), encoding: "utf8"});
  assert.equal(result.status, 0, result.stderr);
});
test("MHTML failure remains a partial capture; missing main DOM fails", async () => {
  const bundle = await buildBundle(snapshot(), null, "api_failed", "0.1.0");
  assert.equal(bundle.manifest.completeness, "partial");
  assert.equal(bundle.manifest.components.mhtml, "failed");
  assert.ok(bundle.manifest.warnings.some(w => w.code === "mhtml_failed"));
  assert.equal(Buffer.from(await bundle.blob.arrayBuffer()).includes(Buffer.from("capture/archive/page.mhtml")), false);
  await assert.rejects(buildBundle({documents: []}, null, null, "0.1.0"), /main_dom_failed/);
});
test("filename uses timestamp and UUID, rejects unsafe names, SHA-256 is standard", async () => {
  assert.equal(captureFilename(id, "2026-10-04T10:20:30.123Z"), `20261004T102030123Z_${id}.webcapture.zip`);
  for (const unsafe of ["../escape", "CON", "a/b", "a\\b", ""]) assert.throws(() => captureFilename(unsafe, new Date().toISOString()));
  assert.throws(() => captureFilename(id, "not-a-date"));
  assert.equal(await sha256(new TextEncoder().encode("abc")), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
});
test("large bundle is transferred with ordered acknowledged bounded chunks", async () => {
  const bytes = new Uint8Array(CHUNK_SIZE * 3 + 17).fill(123), messages = [];
  const connection = {request: async message => {messages.push(message); return {success: true};}};
  await transferBundle(connection, {blob: new Blob([bytes]), filename: "test", manifest: {capture_id: id}});
  const chunks = messages.filter(m => m.command === "chunk");
  assert.deepEqual(chunks.map(m => m.sequence), [0, 1, 2, 3]);
  assert.deepEqual(Buffer.concat(chunks.map(m => Buffer.from(m.data, "base64"))), Buffer.from(bytes));
  assert.ok(chunks.every(m => JSON.stringify(m).length < 300 * 1024));
  assert.equal(messages.at(-1).chunks, 4);
});
test("Manifest requires only explicit capture permissions and no permanent page scripts/UI", () => {
  const manifest = JSON.parse(readFileSync(new URL("../../extension/manifest.json", import.meta.url)));
  assert.equal(manifest.manifest_version, 3);
  assert.deepEqual(manifest.permissions, ["contextMenus", "activeTab", "scripting", "nativeMessaging", "pageCapture", "notifications"]);
  for (const key of ["host_permissions", "content_scripts", "action", "options_ui", "side_panel"]) assert.equal(manifest[key], undefined);
});
