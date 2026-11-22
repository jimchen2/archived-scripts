/* Runs in Chrome's isolated world, once per top-level page. */
(() => {
  "use strict";
  if (window !== window.top) return;
  if (globalThis.__annoyingWebsitesController) {
    globalThis.__annoyingWebsitesController.refresh();
    return;
  }

  const Config = globalThis.AnnoyConfig;
  let settings = Config.normalizeSettings();
  let allowed = false;
  let phase = "off"; // off | blocked | browsing
  let remainingMs = 0;
  let lastTick = 0;
  let ticker = null;
  let host = null;
  let previousFocus = null;
  let lockedElements = [];
  let lastSecond = null;
  let refreshVersion = 0;

  function isPageActive() {
    return document.visibilityState === "visible" && document.hasFocus();
  }

  function clearTicker() {
    if (ticker !== null) clearInterval(ticker);
    ticker = null;
  }

  function lockScrolling() {
    lockedElements = [document.documentElement, document.body].filter(Boolean).map((element) => {
      const snapshot = {
        element,
        value: element.style.getPropertyValue("overflow"),
        priority: element.style.getPropertyPriority("overflow"),
      };
      element.style.setProperty("overflow", "hidden", "important");
      return snapshot;
    });
    // Also ensure body overflow hidden like the primitive userscript
    try {
      document.body.style.overflow = "hidden";
    } catch {}
  }

  function removeOverlay() {
    host?.remove();
    host = null;
    for (const { element, value, priority } of lockedElements) {
      if (element.style.getPropertyValue("overflow") !== "hidden") continue;
      if (value) element.style.setProperty("overflow", value, priority);
      else element.style.removeProperty("overflow");
    }
    lockedElements = [];
    if (previousFocus?.isConnected && typeof previousFocus.focus === "function") {
      try {
        previousFocus.focus({ preventScroll: true });
      } catch {}
    }
    previousFocus = null;
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function styleButton(btn, color) {
    btn.style.display = "block";
    btn.style.boxSizing = "border-box";
    btn.style.textAlign = "center";
    btn.style.textDecoration = "none";
    btn.style.padding = "12px 20px";
    btn.style.fontSize = "16px";
    btn.style.fontWeight = "bold";
    btn.style.fontFamily = "inherit";
    btn.style.cursor = "pointer";
    btn.style.backgroundColor = color;
    btn.style.color = "white";
    btn.style.border = "none";
    btn.style.borderRadius = "8px";
    btn.style.width = "100%";
    
    // Prevent host page CSS from truncating the text
    btn.style.whiteSpace = "normal";
    btn.style.wordWrap = "break-word";
    btn.style.overflow = "visible";
    btn.style.textOverflow = "clip";
    btn.style.height = "auto";
    btn.style.maxHeight = "none";
    btn.style.lineHeight = "1.4";
  }

  function showOverlay() {
    clearTicker();
    removeOverlay();
    phase = "blocked";
    previousFocus = document.activeElement;
    lockScrolling();

    host = document.createElement("div");
    host.id = "annoying-websites-overlay";
    host.style.position = "fixed";
    host.style.top = "0";
    host.style.left = "0";
    host.style.width = "100vw";
    host.style.height = "100vh";
    host.style.backgroundColor = "rgba(0, 0, 0, 0.95)";
    host.style.zIndex = "2147483647";
    host.style.display = "flex";
    host.style.flexDirection = "column";
    host.style.justifyContent = "center";
    host.style.alignItems = "center";
    host.style.color = "white";
    host.style.fontFamily = "Arial, sans-serif";
    host.style.textAlign = "center";

    const message = element("h1", "", "ЭТОТ САЙТ ЗАБЛОКИРОВАН");
    message.style.marginBottom = "0";
    message.style.marginTop = "0";
    message.style.fontSize = "clamp(38px, 8vw, 96px)";
    message.style.padding = "0 24px";
    message.style.lineHeight = "1.15";
    message.style.color = "white";
    message.style.fontWeight = "700";
    message.style.fontFamily = "Arial, sans-serif";
    message.style.letterSpacing = "1px";
    message.style.maxWidth = "1200px";
    message.style.textTransform = "uppercase";

    const actions = document.createElement("div");
    actions.style.display = "flex";
    actions.style.flexDirection = "column";
    actions.style.gap = "15px";
    actions.style.width = "80%";
    actions.style.maxWidth = "300px";
    actions.style.marginTop = "28px";

    // Restore the papers destination from the pre-8836cdb overlay.
    const papersLink = document.createElement("a");
    papersLink.href = "https://github.com/jimchen2/randompapers/tree/main";
    papersLink.textContent = "Go to papers";
    papersLink.rel = "noopener noreferrer";
    styleButton(papersLink, "#4CAF50");
    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.textContent = "Close the computer and go for a walk.";
    closeButton.setAttribute("aria-disabled", "true");
    styleButton(closeButton, "#455A64");

    actions.append(papersLink, closeButton);
    host.append(message, actions);
    (document.body || document.documentElement).appendChild(host);

    if (document.visibilityState === "visible") {
      try {
        papersLink.focus({ preventScroll: true });
      } catch {}
    }
  }

  function startMainTimer() {
    clearTicker();
    removeOverlay();
    phase = "browsing";
    remainingMs = settings.intervalMinutes * 60000;
    lastTick = Date.now();
    lastSecond = null;
    if (settings.showTimerInConsole) console.log(`[Annoy] Timer started. Next break in ${settings.intervalMinutes} minutes.`);
    tick();
    ticker = setInterval(tick, 250);
  }

  function tick() {
    if (!allowed) return;
    const now = Date.now();
    if (isPageActive()) {
      remainingMs = Math.max(0, remainingMs - (now - lastTick));
    }
    lastTick = now;

    if (phase !== "browsing") return;
    const seconds = Math.max(0, Math.ceil(remainingMs / 1000));
    if (seconds <= 0) {
      showOverlay();
      return;
    }
    if (settings.showTimerInConsole && seconds !== lastSecond) console.log(`[Annoy] Time remaining: ${seconds}s`);
    lastSecond = seconds;
  }

  function applyContext(context) {
    const previous = settings;
    const previouslyAllowed = allowed;
    settings = Config.normalizeSettings(context.settings);
    allowed = Boolean(context.allowed) && settings.enabled && Config.matchesAny(settings.websites, location.href);
    if (!allowed) {
      clearTicker();
      removeOverlay();
      phase = "off";
      return;
    }
    if (!previouslyAllowed || phase === "off") showOverlay();
    else if (phase === "browsing" && previous.intervalMinutes !== settings.intervalMinutes) startMainTimer();
    else tick();
  }

  async function refresh() {
    const version = ++refreshVersion;
    try {
      const response = await chrome.runtime.sendMessage({ type: "AW_GET_CONTEXT" });
      if (version !== refreshVersion) return;
      if (!response?.ok) throw new Error(response?.error || "Extension unavailable.");
      applyContext(response);
    } catch (error) {
      if (version !== refreshVersion) return;
      // Never leave a page permanently blocked after extension reload/removal.
      allowed = false;
      clearTicker();
      removeOverlay();
      phase = "off";
      console.warn("[Annoy] Reminder stopped. Reload this page if the extension was updated.", error);
    }
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "AW_REFRESH") return false;
    refresh();
    sendResponse({ ok: true });
    return false;
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "sync" && Config.KEYS.some((key) => key in changes)) refresh();
  });
  document.addEventListener("visibilitychange", tick);
  window.addEventListener("focus", tick);
  window.addEventListener("blur", tick);
  window.addEventListener("pageshow", tick);
  window.addEventListener("popstate", refresh);
  window.navigation?.addEventListener("navigatesuccess", refresh);
  globalThis.__annoyingWebsitesController = { refresh };
  refresh();
})();
