import {captureDocument} from "../capture/dom.js";
import {buildBundle} from "../shared/bundle.js";
import {nativeConnection, transferBundle} from "./native.js";

const MENU = "capture-page";
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => chrome.contextMenus.create({id: MENU, title: "このページをキャプチャ", contexts: ["all"], documentUrlPatterns: ["http://*/*", "https://*/*", "file:///*"]}));
});
const running = new Set();
async function notify(success, message) {
  await chrome.notifications.create({type: "basic", iconUrl: "public/icons/capture.png", title: "Web Page Capture", message: `${success ? "キャプチャを保存しました。" : "キャプチャに失敗しました。"}\n${message}`});
}
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU) return;
  let connection;
  if (running.has(tab?.id)) {await notify(false, "このタブのキャプチャは処理中です。"); return;}
  running.add(tab?.id);
  try {
    if (!tab?.id || !tab.active) throw new Error("active_tab_unavailable");
    // Keep the worker alive while capturing and transferring via connectNative.
    connection = nativeConnection();
    await connection.request({command: "hello"});
    const results = await chrome.scripting.executeScript({target: {tabId: tab.id}, func: captureDocument});
    const raw = results[0]?.result;
    if (!raw) throw new Error("main_dom_failed");
    let mhtml, mhtmlError;
    try {mhtml = await chrome.pageCapture.saveAsMHTML({tabId: tab.id});} catch {mhtmlError = "page_capture_api_failed";}
    const current = await chrome.tabs.get(tab.id);
    if (current.url !== raw.documents[0].document.url) throw new Error("page_navigated_during_capture");
    const bundle = await buildBundle(raw, mhtml, mhtmlError, chrome.runtime.getManifest().version);
    await transferBundle(connection, bundle);
    await notify(true, `${bundle.filename}\n一部情報は取得できません。詳細はmanifest.jsonを確認してください。`);
  } catch (error) {
    await notify(false, error.message || "capture_failed");
  } finally {
    connection?.close();
    running.delete(tab?.id);
  }
});
