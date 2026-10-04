export const HOST_NAME = "com.characterpagecollector.web_page_capture";
export const CHUNK_SIZE = 192 * 1024;
export function nativeConnection() {
  const port = chrome.runtime.connectNative(HOST_NAME);
  let pending, disconnected;
  port.onMessage.addListener(response => {
    if (!pending) return;
    clearTimeout(pending.timer);
    const {resolve, reject} = pending;
    pending = null;
    response.success ? resolve(response) : reject(new Error(response.error || "native_host_failed"));
  });
  port.onDisconnect.addListener(() => {
    disconnected = chrome.runtime.lastError?.message || "native_host_disconnected";
    if (pending) {clearTimeout(pending.timer); pending.reject(new Error(disconnected)); pending = null;}
  });
  return {
    request(message) {
      return new Promise((resolve, reject) => {
        if (disconnected) return reject(new Error(disconnected));
        if (pending) return reject(new Error("request_in_progress"));
        const timer = setTimeout(() => {pending = null; reject(new Error("native_host_timeout")); port.disconnect();}, 60000);
        pending = {resolve, reject, timer};
        try {port.postMessage(message);} catch (error) {clearTimeout(timer); pending = null; reject(error);}
      });
    },
    close() {port.disconnect();}
  };
}
export async function transferBundle(connection, bundle) {
  const transfer_id = bundle.manifest.capture_id;
  await connection.request({command: "begin", transfer_id, filename: bundle.filename, size: bundle.blob.size});
  let sequence = 0;
  for (let offset = 0; offset < bundle.blob.size; offset += CHUNK_SIZE) {
    const bytes = new Uint8Array(await bundle.blob.slice(offset, offset + CHUNK_SIZE).arrayBuffer());
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    await connection.request({command: "chunk", transfer_id, sequence: sequence++, data: btoa(binary)});
  }
  // Host computes a streaming SHA-256 and verifies all artifact checksums before publication.
  return connection.request({command: "finish", transfer_id, chunks: sequence});
}
