import test from "node:test";
import assert from "node:assert/strict";
import {nativeConnection} from "../../extension/src/background/native.js";

function event() {
  const listeners = [];
  return {addListener: listener => listeners.push(listener), emit: value => listeners.forEach(listener => listener(value))};
}
test("native connection rejects host failure and disconnect with its reason", async () => {
  let port;
  globalThis.chrome = {runtime: {connectNative() {port = {onMessage: event(), onDisconnect: event(), postMessage() {}, disconnect() {}}; return port;}}};
  const connection = nativeConnection();
  let pending = connection.request({command: "hello"});
  port.onMessage.emit({success: false, error: "invalid_message"});
  await assert.rejects(pending, /invalid_message/);
  pending = connection.request({command: "hello"});
  chrome.runtime.lastError = {message: "Specified native messaging host not found."};
  port.onDisconnect.emit();
  await assert.rejects(pending, /host not found/);
  await assert.rejects(connection.request({command: "hello"}), /host not found/);
});
test("background captures the active tab and reports save, MHTML partial and failed captures", async () => {
  let clicked, installed, mode = "success", target, disconnected = 0;
  const notifications = [], messages = [];
  const raw = () => ({documents: [{frame_id: "main", html: "<!DOCTYPE html><html><body>synthetic</body></html>", document: {url: "https://example.invalid/", title: "Synthetic", captured_at: "2026-10-04T10:20:30.123Z"}, html_metadata: {meta: [], links: []}, structured_data: {json_ld: []}}], frames: [], shadows: [], resources: [], warnings: [{code: "closed_shadow_dom_unobservable", component: "shadow_dom"}]});
  globalThis.chrome = {
    runtime: {
      onInstalled: {addListener(fn) {installed = fn;}}, getManifest: () => ({version: "0.1.0"}),
      connectNative() {
        const port = {onMessage: event(), onDisconnect: event(), disconnect() {disconnected++;}, postMessage(message) {
          messages.push(message);
          queueMicrotask(() => port.onMessage.emit(mode === "save-failed" && message.command === "finish" ? {success: false, error: "save_or_bundle_validation_failed"} : {success: true}));
        }};
        return port;
      }
    },
    contextMenus: {removeAll(fn) {fn();}, create(item) {assert.equal(item.title, "このページをキャプチャ");}, onClicked: {addListener(fn) {clicked = fn;}}},
    scripting: {async executeScript(options) {target = options.target; if (mode === "dom-failed") throw new Error("Cannot access page"); return [{result: raw()}];}},
    pageCapture: {async saveAsMHTML() {if (mode === "mhtml-failed") throw new Error("synthetic"); return new Blob(["MIME-Version: 1.0"]);}},
    tabs: {async get() {return {url: mode === "navigation" ? "https://example.invalid/other" : "https://example.invalid/"};}},
    notifications: {async create(options) {notifications.push(options);}}
  };
  await import("../../extension/src/background/service-worker.js");
  installed();
  const tab = {id: 42, active: true};
  await clicked({menuItemId: "unrelated"}, tab);
  assert.equal(notifications.length, 0);
  await clicked({menuItemId: "capture-page", srcUrl: "https://example.invalid/image"}, tab);
  assert.deepEqual(target, {tabId: 42});
  assert.ok(notifications.at(-1).message.includes("キャプチャを保存しました"));
  assert.equal(messages.at(-1).command, "finish");
  for (const failed of ["dom-failed", "save-failed", "navigation"]) {
    mode = failed;
    await clicked({menuItemId: "capture-page"}, tab);
    assert.ok(notifications.at(-1).message.includes("キャプチャに失敗しました"), failed);
  }
  mode = "mhtml-failed";
  await clicked({menuItemId: "capture-page"}, tab);
  assert.ok(notifications.at(-1).message.includes("キャプチャを保存しました"));
  assert.equal(disconnected, 5);
});
