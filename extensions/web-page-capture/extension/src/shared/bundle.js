const encoder = new TextEncoder();
export const FORMAT_VERSION = "1.0";
export async function sha256(bytes) {
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), b => b.toString(16).padStart(2, "0")).join("");
}
export function captureFilename(id, timestamp) {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id) || !Number.isFinite(Date.parse(timestamp))) throw new Error("invalid_capture_identity");
  return `${new Date(timestamp).toISOString().replace(/[-:.]/g, "")}_${id}.webcapture.zip`;
}
// Standard ZIP (STORE), UTF-8 names, CRC-32 and central directory. No remote code.
export function zipStore(files) {
  const local = [], central = [];
  let offset = 0;
  const header = size => {const bytes = new Uint8Array(size); return [bytes, new DataView(bytes.buffer)];};
  for (const [name, data] of files) {
    const path = encoder.encode(`capture/${name}`);
    let crc = 0xffffffff;
    for (const byte of data) {
      crc ^= byte;
      for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
    }
    crc = (crc ^ 0xffffffff) >>> 0;
    const [lh, lv] = header(30);
    lv.setUint32(0, 0x04034b50, true); lv.setUint16(4, 20, true); lv.setUint16(6, 0x800, true);
    lv.setUint16(12, 33, true); lv.setUint32(14, crc, true);
    lv.setUint32(18, data.length, true); lv.setUint32(22, data.length, true); lv.setUint16(26, path.length, true);
    local.push(lh, path, data);
    const [ch, cv] = header(46);
    cv.setUint32(0, 0x02014b50, true); cv.setUint16(4, 20, true); cv.setUint16(6, 20, true); cv.setUint16(8, 0x800, true);
    cv.setUint16(14, 33, true); cv.setUint32(16, crc, true); cv.setUint32(20, data.length, true); cv.setUint32(24, data.length, true); cv.setUint16(28, path.length, true); cv.setUint32(42, offset, true);
    central.push(ch, path);
    offset += lh.length + path.length + data.length;
  }
  const centralSize = central.reduce((n, b) => n + b.length, 0);
  if (files.size > 65535 || offset + centralSize > 0xffffffff) throw new Error("zip_size_limit");
  const [end, ev] = header(22);
  ev.setUint32(0, 0x06054b50, true); ev.setUint16(8, files.size, true); ev.setUint16(10, files.size, true); ev.setUint32(12, centralSize, true); ev.setUint32(16, offset, true);
  return new Blob([...local, ...central, end], {type: "application/zip"});
}
export async function buildBundle(raw, mhtml, mhtmlError, version, id = crypto.randomUUID()) {
  const main = raw.documents.find(d => d.frame_id === "main");
  if (!main?.html) throw new Error("main_dom_failed");
  const files = new Map();
  const json = (name, value) => files.set(name, encoder.encode(JSON.stringify(value, null, 2)));
  for (const doc of raw.documents) files.set(doc.frame_id === "main" ? "dom/main.html" : `dom/frames/${doc.frame_id}.html`, encoder.encode(doc.html));
  json("metadata/document.json", main.document);
  json("metadata/html-metadata.json", main.html_metadata);
  json("metadata/structured-data.json", main.structured_data);
  json("metadata/frames.json", raw.frames.map(f => {
    const doc = raw.documents.find(d => d.frame_id === f.frame_id);
    return {...f, metadata: doc?.document ?? null, html_metadata: doc?.html_metadata ?? null, structured_data: doc?.structured_data ?? null};
  }));
  json("metadata/shadow-dom.json", raw.shadows);
  json("metadata/resources.json", raw.resources);
  const warnings = [...raw.warnings];
  if (mhtml) files.set("archive/page.mhtml", new Uint8Array(await mhtml.arrayBuffer()));
  else warnings.push({code: "mhtml_failed", component: "mhtml", reason: mhtmlError || "empty_archive"});
  const components = {main_dom: "success", metadata: "success", structured_data: "success", frames: raw.frames.some(f => f.capture_status !== "success") ? "partial" : "success", shadow_dom: "partial", mhtml: mhtml ? "success" : "failed"};
  const manifest = {format: "web-capture-bundle", format_version: FORMAT_VERSION, capture_id: id, captured_at: main.document.captured_at, capture_tool: {name: "WebPageCapture", version}, page: {url: main.document.url, title: main.document.title}, completeness: "partial", components, warnings};
  json("manifest.json", manifest);
  const checksums = {};
  for (const [name, data] of files) checksums[name] = {sha256: await sha256(data), bytes: data.length};
  json("checksums.json", checksums);
  return {blob: zipStore(files), filename: captureFilename(id, manifest.captured_at), manifest};
}
