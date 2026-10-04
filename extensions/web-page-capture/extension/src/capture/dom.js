// Self-contained: Chrome serializes this function into an isolated world.
export function captureDocument() {
  const frames = [], shadows = [], resources = [], documents = [];
  const warnings = [{code: "closed_shadow_dom_unobservable", component: "shadow_dom"}];
  const attrs = el => Object.fromEntries(Array.from(el.attributes, a => [a.name, a.value]));
  function capture(doc, frameId) {
    const win = doc.defaultView;
    const dt = doc.doctype;
    const doctype = dt ? new XMLSerializer().serializeToString(dt) : "";
    const data = {
      frame_id: frameId,
      html: doctype + (doctype ? "\n" : "") + doc.documentElement.outerHTML,
      document: {
        url: doc.URL, canonical_url: doc.querySelector('link[rel~="canonical"]')?.href ?? null,
        title: doc.title, base_uri: doc.baseURI, referrer: doc.referrer,
        language: doc.documentElement.lang, charset: doc.characterSet,
        content_type: doc.contentType, ready_state: doc.readyState, doctype,
        captured_at: new Date().toISOString(),
        viewport: {width: win.innerWidth, height: win.innerHeight, device_pixel_ratio: win.devicePixelRatio},
        size: {width: doc.documentElement.scrollWidth, height: doc.documentElement.scrollHeight},
        scroll: {x: win.scrollX, y: win.scrollY}
      },
      html_metadata: {meta: Array.from(doc.querySelectorAll("meta"), attrs), links: Array.from(doc.querySelectorAll("link"), attrs)},
      structured_data: {
        json_ld: Array.from(doc.querySelectorAll('script[type="application/ld+json"]'), (el, index) => ({index, raw: el.textContent})),
        microdata: Array.from(doc.querySelectorAll("[itemscope], [itemprop], [itemtype], [itemid]"), attrs),
        rdfa: Array.from(doc.querySelectorAll("[typeof], [property], [vocab], [prefix]"), attrs)
      }
    };
    documents.push(data);
    function walk(root, prefix) {
      Array.from(root.children).forEach((el, index) => {
        const path = `${prefix}/${el.localName}[${index}]`;
        for (const attribute of ["src", "href", "poster", "srcset", "data"]) {
          if (el.hasAttribute(attribute)) resources.push({frame_id: frameId, element_path: path, element: el.localName, attribute, raw: el.getAttribute(attribute), url: attribute === "srcset" ? null : (el[attribute] || el.getAttribute(attribute))});
        }
        if (el.shadowRoot) {
          shadows.push({frame_id: frameId, host_path: path, mode: "open", html: el.shadowRoot.innerHTML});
          walk(el.shadowRoot, path + "/#shadow-root");
        }
        if (el.localName === "iframe" || el.localName === "frame") {
          const id = `frame-${String(frames.length + 1).padStart(4, "0")}`;
          const record = {frame_id: id, parent_frame_id: frameId, element_path: path, url: el.src || "about:blank", attributes: attrs(el)};
          frames.push(record);
          try {
            const child = el.contentDocument;
            if (!child?.documentElement) {
              record.capture_status = "permission_denied";
              record.reason = "cross_origin_or_unavailable";
            } else {
              capture(child, id);
              record.url = child.URL;
              record.capture_status = "success";
              record.file = `dom/frames/${id}.html`;
            }
          } catch {
            record.capture_status = "failed";
            record.reason = "frame_capture_failed";
          }
          if (record.capture_status !== "success") warnings.push({code: record.reason, component: "frames", frame_id: id});
        }
        walk(el, path);
      });
    }
    walk(doc, "");
  }
  capture(document, "main");
  return {documents, frames, shadows, resources, warnings};
}
