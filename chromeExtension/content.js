var activeMuteTimeout = null;
var muteUntilEpochMs = 0;
var overlayEl = null;
var overlayHideTimeout = null;

if (!window.__musicWordFilterListenerRegistered) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.mute) {
            const [start, end] = message.mute;
            const matchedWord = message.word || "";
            muteAudio(start, end, matchedWord, message.showDebugOverlay === true);
        }
    });
    window.__musicWordFilterListenerRegistered = true;
}

function getOrCreateOverlay() {
    if (overlayEl && document.body.contains(overlayEl)) {
        return overlayEl;
    }

    overlayEl = document.createElement("div");
    overlayEl.style.position = "fixed";
    overlayEl.style.top = "12px";
    overlayEl.style.right = "12px";
    overlayEl.style.zIndex = "2147483647";
    overlayEl.style.background = "rgba(17, 24, 39, 0.92)";
    overlayEl.style.color = "#f9fafb";
    overlayEl.style.border = "1px solid #4b5563";
    overlayEl.style.borderRadius = "8px";
    overlayEl.style.padding = "8px 10px";
    overlayEl.style.fontFamily = "Arial, sans-serif";
    overlayEl.style.fontSize = "12px";
    overlayEl.style.lineHeight = "1.3";
    overlayEl.style.maxWidth = "320px";
    overlayEl.style.boxShadow = "0 8px 16px rgba(0, 0, 0, 0.3)";
    overlayEl.style.pointerEvents = "none";
    overlayEl.style.opacity = "0";
    overlayEl.style.transition = "opacity 120ms ease-in-out";
    document.body.appendChild(overlayEl);
    return overlayEl;
}

function showOverlay(matchedWord, durationMs, muteUntilMs) {
    const el = getOrCreateOverlay();
    const safeWord = matchedWord || "<no-word>";
    el.textContent = `Mute ${durationMs}ms | word: ${safeWord} | until: ${new Date(
        muteUntilMs
    ).toLocaleTimeString()}`;
    el.style.opacity = "1";

    if (overlayHideTimeout) {
        clearTimeout(overlayHideTimeout);
    }

    overlayHideTimeout = setTimeout(() => {
        if (overlayEl) {
            overlayEl.style.opacity = "0";
        }
    }, 1800);
}

function muteAudio(start, end, matchedWord, showDebugOverlay) {
    const mediaEl = document.querySelector("video, audio");
    if (!mediaEl) {
        return;
    }

    const durationMs = Math.max(0, (end - start) * 1000);
    if (durationMs === 0) {
        return;
    }

    const now = Date.now();
    const proposedMuteUntil = now + durationMs;
    muteUntilEpochMs = Math.max(muteUntilEpochMs, proposedMuteUntil);

    if (showDebugOverlay) {
        showOverlay(matchedWord, durationMs, muteUntilEpochMs);
    }

    mediaEl.muted = true;

    if (activeMuteTimeout) {
        clearTimeout(activeMuteTimeout);
    }

    const remainingMs = Math.max(0, muteUntilEpochMs - Date.now());
    activeMuteTimeout = setTimeout(() => {
        // Only unmute if no newer mute window extended the deadline.
        if (Date.now() >= muteUntilEpochMs) {
            mediaEl.muted = false;
            activeMuteTimeout = null;
        }
    }, remainingMs);
}