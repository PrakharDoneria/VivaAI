/**
 * Adds X-API-Key when VIVAAI_API_KEY is set server-side (injected as __VIVAAI_API_KEY__).
 * For multipart/form-data requests, omit Content-Type so the browser sets the boundary.
 */
function vivaaiApiHeaders(extra) {
    const h = Object.assign({}, extra || {});
    if (typeof window.__VIVAAI_API_KEY__ === "string" && window.__VIVAAI_API_KEY__.length > 0) {
        h["X-API-Key"] = window.__VIVAAI_API_KEY__;
    }
    return h;
}
