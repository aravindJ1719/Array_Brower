/**
 * ArrayNav Browser — Frontend Controller
 * ========================================
 * Responsibilities:
 *   1. Listen for user interactions (address bar, nav buttons, quick links).
 *   2. Send navigation requests to the FastAPI backend.
 *   3. Receive the new array state and render it in the monitor panel.
 *   4. Load the returned URL in the iframe (or show blocked-page overlay).
 *
 * Architecture:
 *   UI event → NavigationController → FastAPI → Array Algorithm Engine
 *           ↑                                                      ↓
 *           └──────────── state response ◄─────────────────────────┘
 *
 * The UI never decides where to navigate — that is always the backend engine.
 */

const API   = "http://localhost:8000/api";
const PROXY = "/api/proxy";  // same-origin proxy — strips X-Frame-Options/CSP

// ── DOM refs ──────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const btnBack       = $("btn-back");
const btnForward    = $("btn-forward");
const btnReload     = $("btn-reload");
const btnGo         = $("btn-go");
const btnReset      = $("btn-reset");
const addressBar    = $("address-bar");
const frame         = $("browser-frame");
const newTabPage    = $("new-tab-page");
const loadingOverlay= $("loading-overlay");
const blockedPage   = $("blocked-page");
const blockedUrlTxt = $("blocked-url-text");
const blockedLink   = $("blocked-open-link");
const codeDisplay   = $("code-display");
const arrayVisual   = $("array-visual");
const arrayEmptyMsg = $("array-empty-msg");
const statIndex     = $("stat-index");
const statLen       = $("stat-len");
const statBack      = $("stat-back");
const statForward   = $("stat-forward");
const actionLog     = $("action-log");
const statusText    = $("status-text");
const statusUrl     = $("status-url");
const algoToggleBtn = $("algo-toggle-btn");
const algoRulesPanel= $("algo-rules-panel");
const toast         = $("toast");
const lockIcon      = $("lock-icon");
const loadingText   = $("loading-text");

// ── State ─────────────────────────────────────────────────────────────────
let iframeLoadTimer = null;
let currentUrl = null;

// ── Toast ─────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg, duration = 2200) {
  toast.textContent = msg;
  toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), duration);
}

// ── Navigation Controller ─────────────────────────────────────────────────
/**
 * All navigation goes through this single function.
 * It posts to the FastAPI backend, then applies the state response.
 */
async function navigate(endpoint, body = null) {
  setStatus("Navigating…");
  try {
    const opts = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      ...(body ? { body: JSON.stringify(body) } : {}),
    };
    const res  = await fetch(`${API}/${endpoint}`, opts);
    const data = await res.json();

    if (!data.success) {
      setStatus(data.message);
      showToast(data.message);
      return;
    }

    applyState(data.state, data.action, data.message);
  } catch (err) {
    setStatus("Error: " + err.message);
    showToast("Backend unreachable — is the server running?", 3500);
  }
}

// ── Apply State (the single source of truth) ──────────────────────────────
function applyState(state, action, message) {
  const { history, current_index, current_page, can_go_back, can_go_forward } = state;

  // 1. Update address bar and lock icon
  addressBar.value = current_page || "";
  lockIcon.style.color = current_page?.startsWith("https://") ? "var(--clr-success)" : "var(--clr-warn)";

  // 2. Enable / disable nav buttons
  btnBack.disabled    = !can_go_back;
  btnForward.disabled = !can_go_forward;
  btnReload.disabled  = !current_page;

  // 3. Load page in iframe (skip for reload — already loaded)
  if (current_page && action !== "reload") {
    loadPage(current_page);
  } else if (current_page && action === "reload") {
    // Trigger reload by re-setting src
    reloadFrame(current_page);
  }

  // 4. Update monitor panel
  renderCodeBlock(history, current_index);
  renderArrayVisual(history, current_index);
  renderStats(current_index, history.length, can_go_back, can_go_forward);
  appendLog(action, message, current_page);
  setStatus(message, current_page);
}

// ── Page Loading ──────────────────────────────────────────────────────────
/**
 * All page loads go through the server-side proxy.
 * The proxy fetches the target URL and re-serves it from localhost,
 * which means the browser never sees the remote X-Frame-Options header.
 */
function loadPage(url) {
  currentUrl = url;
  newTabPage.classList.remove("visible");
  blockedPage.classList.add("hidden");
  frame.classList.add("hidden");
  loadingOverlay.classList.remove("hidden");
  loadingText.textContent = `Loading ${url}\u2026`;
  statusUrl.textContent = url;

  clearTimeout(iframeLoadTimer);

  // Route through the server-side proxy (strips X-Frame-Options / CSP)
  const proxyUrl = `${PROXY}?url=${encodeURIComponent(url)}`;
  frame.src = proxyUrl;

  // 12-second timeout — proxy fetch can be slow for heavy sites
  iframeLoadTimer = setTimeout(() => {
    handlePossiblyBlocked(url);
  }, 12000);
}

function reloadFrame(url) {
  loadingOverlay.classList.remove("hidden");
  loadingText.textContent = `Reloading\u2026`;
  const proxyUrl = `${PROXY}?url=${encodeURIComponent(url)}`;
  frame.src = "";
  setTimeout(() => { frame.src = proxyUrl; }, 50);
  iframeLoadTimer = setTimeout(() => handlePossiblyBlocked(url), 12000);
}

frame.addEventListener("load", () => {
  clearTimeout(iframeLoadTimer);

  // Detect if the iframe has navigated away from our proxy
  // (e.g. JS-driven navigation inside Google escaping the rewritten links).
  try {
    const iframeSrc = frame.src || "";
    const isOnProxy = iframeSrc.startsWith(window.location.origin + "/api/proxy") ||
                      iframeSrc === "" ||
                      iframeSrc === "about:blank";

    if (!isOnProxy && currentUrl) {
      // Escaped the proxy — redirect the iframe back through it.
      console.warn("[ArrayNav] iframe escaped proxy, redirecting back:", iframeSrc);
      const proxyUrl = `${PROXY}?url=${encodeURIComponent(currentUrl)}`;
      frame.src = proxyUrl;
      return;
    }
  } catch (e) {
    // Cross-origin access to frame.src — that itself means the iframe
    // navigated to a real external page; redirect back through proxy.
    if (currentUrl) {
      console.warn("[ArrayNav] cross-origin iframe detected, redirecting via proxy");
      frame.src = `${PROXY}?url=${encodeURIComponent(currentUrl)}`;
      return;
    }
  }

  // The proxy always returns a valid HTML document — even for errors it
  // returns our styled error page.  So reaching here always means success.
  loadingOverlay.classList.add("hidden");
  frame.classList.remove("hidden");
  setStatus("Done");
});

frame.addEventListener("error", () => {
  clearTimeout(iframeLoadTimer);
  // A network-level error (e.g. localhost proxy is down)
  handlePossiblyBlocked(currentUrl);
});

function handlePossiblyBlocked(url) {
  clearTimeout(iframeLoadTimer);
  loadingOverlay.classList.add("hidden");
  frame.classList.add("hidden");
  blockedPage.classList.remove("hidden");
  blockedUrlTxt.textContent = url;
  blockedLink.href = url;
  setStatus("Could not load page — open it directly in a new tab.");
}

// ── Monitor Panel Renderers ───────────────────────────────────────────────
function renderCodeBlock(history, currentIndex) {
  const histStr  = JSON.stringify(history, null, 0)
    .replace("[", "[\n  ")
    .replace("]", "\n]")
    .replace(/,/g, ",\n  ");
  codeDisplay.textContent =
    `history       = ${histStr}\ncurrent_index = ${currentIndex}`;
}

function renderArrayVisual(history, currentIndex) {
  if (history.length === 0) {
    arrayVisual.innerHTML = "";
    arrayEmptyMsg.style.display = "block";
    return;
  }
  arrayEmptyMsg.style.display = "none";
  arrayVisual.innerHTML = history.map((url, i) => {
    const isCurrent = i === currentIndex;
    const shortUrl  = url.replace(/^https?:\/\//, "").replace(/\/$/, "");
    return `
      <div class="array-item ${isCurrent ? "is-current" : ""}">
        <span class="array-idx">[${i}]</span>
        <span class="array-url" title="${url}">${shortUrl}</span>
        ${isCurrent ? '<span class="current-pointer">◄ current</span>' : ""}
      </div>`;
  }).join("");
}

function renderStats(index, len, canBack, canFwd) {
  statIndex.textContent = index;
  statLen.textContent   = len;
  statBack.innerHTML    = canBack
    ? '<span class="pill pill-yes">YES</span>'
    : '<span class="pill pill-no">NO</span>';
  statForward.innerHTML = canFwd
    ? '<span class="pill pill-yes">YES</span>'
    : '<span class="pill pill-no">NO</span>';
}

function appendLog(action, message, url) {
  const entry = document.createElement("div");
  entry.className = "log-entry";
  const shortMsg = url
    ? url.replace(/^https?:\/\//, "").replace(/\/$/, "").slice(0, 38)
    : message.slice(0, 42);
  entry.innerHTML = `
    <span class="log-action ${action}">${action}</span>
    <span class="log-msg">${shortMsg}</span>`;
  actionLog.prepend(entry);
  // Keep max 20 log entries
  while (actionLog.children.length > 20) {
    actionLog.removeChild(actionLog.lastChild);
  }
}

function setStatus(text, url = "") {
  statusText.textContent = text;
  if (url) statusUrl.textContent = url;
}

// ── Event Listeners ───────────────────────────────────────────────────────

// Address bar — Enter key
addressBar.addEventListener("keydown", e => {
  if (e.key === "Enter") triggerVisit();
});
addressBar.addEventListener("focus", () => addressBar.select());

// Go button
btnGo.addEventListener("click", triggerVisit);

function normalizeUrl(raw) {
  raw = raw.trim();
  if (!raw) return "";
  // If no scheme is present, default to https://
  if (!/^https?:\/\//i.test(raw)) {
    raw = "https://" + raw;
  }
  return raw;
}

function triggerVisit() {
  const url = normalizeUrl(addressBar.value);
  if (!url) return;
  addressBar.value = url;  // show the normalised URL immediately
  navigate("visit", { url });
}

// Back
btnBack.addEventListener("click", () => navigate("back"));

// Forward
btnForward.addEventListener("click", () => navigate("forward"));

// Reload — add spinning animation
btnReload.addEventListener("click", () => {
  btnReload.classList.add("spinning");
  navigate("reload").finally(() => {
    setTimeout(() => btnReload.classList.remove("spinning"), 500);
  });
});

// Reset
btnReset.addEventListener("click", async () => {
  if (!confirm("Clear all navigation history?")) return;
  await navigate("reset");
  newTabPage.classList.add("visible");
  frame.src = "";
  frame.classList.add("hidden");
  blockedPage.classList.add("hidden");
  addressBar.value = "";
  statusUrl.textContent = "";
  actionLog.innerHTML = "";
  codeDisplay.textContent = "history       = []\ncurrent_index = -1";
  showToast("Navigation history cleared");
});

// Quick links on new tab page
document.querySelectorAll(".quick-link").forEach(btn => {
  btn.addEventListener("click", () => {
    addressBar.value = btn.dataset.url;
    triggerVisit();
  });
});

// Algorithm rules toggle
algoToggleBtn.addEventListener("click", () => {
  const isOpen = !algoRulesPanel.classList.contains("hidden");
  algoRulesPanel.classList.toggle("hidden", isOpen);
  algoToggleBtn.querySelector(".toggle-chevron").classList.toggle("open", !isOpen);
});

// ── Keyboard shortcuts ────────────────────────────────────────────────────
document.addEventListener("keydown", e => {
  if ((e.altKey || e.metaKey) && e.key === "ArrowLeft"  && !btnBack.disabled)    navigate("back");
  if ((e.altKey || e.metaKey) && e.key === "ArrowRight" && !btnForward.disabled) navigate("forward");
  if (e.key === "F5" || (e.metaKey && e.key === "r")) {
    e.preventDefault();
    if (!btnReload.disabled) navigate("reload");
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "l") {
    e.preventDefault();
    addressBar.focus();
    addressBar.select();
  }
});

// ── Boot: fetch current state from backend ────────────────────────────────
(async () => {
  try {
    const res  = await fetch(`${API}/history`);
    const data = await res.json();
    const s    = data.array_state;

    if (s.current_page) {
      applyState(s, "visit", `Restored: ${s.current_page}`);
    } else {
      // Initial empty state
      renderCodeBlock([], -1);
      renderArrayVisual([], -1);
      renderStats(-1, 0, false, false);
      setStatus("Ready — enter a URL to start browsing");
    }
  } catch {
    setStatus("Backend offline — start the server with: uvicorn backend.main:app");
    showToast("Cannot reach backend — is uvicorn running?", 4000);
  }
})();
