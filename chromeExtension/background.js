const WS_URL = "ws://localhost:8000";
const RECONNECT_DELAY_MS = 1500;
let socket = null;
let reconnectTimer = null;
const FILTER_STATE_KEY = "censorNWord";
const BLOCKLIST_TERMS_KEY = "blocklistTerms";
const ALLOWLIST_TERMS_KEY = "allowlistTerms";
const DEBUG_OVERLAY_KEY = "showDebugOverlay";
const DEFAULT_BLOCKLIST_TERMS = ["nigg"];

function getFilterSettings(callback) {
    chrome.storage.sync.get(
        [FILTER_STATE_KEY, BLOCKLIST_TERMS_KEY, ALLOWLIST_TERMS_KEY, DEBUG_OVERLAY_KEY],
        (result) => {
            const blocklistTerms = Array.isArray(result[BLOCKLIST_TERMS_KEY])
                ? result[BLOCKLIST_TERMS_KEY]
                : DEFAULT_BLOCKLIST_TERMS;
            const allowlistTerms = Array.isArray(result[ALLOWLIST_TERMS_KEY])
                ? result[ALLOWLIST_TERMS_KEY]
                : [];

            callback({
                isCensorEnabled: result[FILTER_STATE_KEY] !== false,
                blocklistTerms,
                allowlistTerms,
                showDebugOverlay: result[DEBUG_OVERLAY_KEY] === true
            });
        }
    );
}

function normalizeTerm(term) {
    return String(term || "").toLowerCase().trim();
}

function isTermMatched(term, candidateWord) {
    return candidateWord.includes(term);
}

function shouldMuteWord(matchedWord, settings) {
    const normalizedWord = normalizeTerm(matchedWord);
    if (!normalizedWord) {
        return false;
    }

    const normalizedAllowlist = settings.allowlistTerms
        .map(normalizeTerm)
        .filter(Boolean);
    const normalizedBlocklist = settings.blocklistTerms
        .map(normalizeTerm)
        .filter(Boolean);

    const allowHit = normalizedAllowlist.some((term) => isTermMatched(term, normalizedWord));
    if (allowHit) {
        return false;
    }

    return normalizedBlocklist.some((term) => isTermMatched(term, normalizedWord));
}

function forwardMuteToActiveTab(start, end, word, showDebugOverlay) {
    chrome.tabs.query({}, (tabs) => {
        if (!tabs || tabs.length === 0) {
            return;
        }

        tabs.forEach((tab) => {
            const tabUrl = String(tab.url || "");
            const isSupportedTab =
                tabUrl.includes("youtube.com") ||
                tabUrl.includes("spotify.com") ||
                tabUrl.includes("pandora.com");

            if (!isSupportedTab || !tab.id) {
                return;
            }

            const payload = {
                mute: [start, end],
                word,
                showDebugOverlay: Boolean(showDebugOverlay)
            };

            chrome.tabs.sendMessage(tab.id, payload, () => {
                if (!chrome.runtime.lastError) {
                    return;
                }

                // Inject only when receiver does not exist, then retry once.
                chrome.scripting.executeScript(
                    {
                        target: { tabId: tab.id },
                        files: ["content.js"]
                    },
                    () => {
                        if (chrome.runtime.lastError) {
                            console.warn(
                                "Could not inject content script in tab:",
                                tab.id,
                                chrome.runtime.lastError.message
                            );
                            return;
                        }

                        chrome.tabs.sendMessage(tab.id, payload, () => {
                            if (chrome.runtime.lastError) {
                                console.warn(
                                    "Content script still not ready in tab:",
                                    tab.id,
                                    chrome.runtime.lastError.message
                                );
                            }
                        });
                    }
                );
            });
        });
    });
}

function handleMuteMessage(data) {
    const [start, end] = data.mute;
    const matchedWord = data.word || "";

    getFilterSettings((settings) => {
        // Default behavior is censor enabled.
        if (!settings.isCensorEnabled) {
            return;
        }

        // Backward compatibility: if server sends only mute times, apply while censor is enabled.
        if (!matchedWord) {
            forwardMuteToActiveTab(start, end, "", settings.showDebugOverlay);
            return;
        }

        if (shouldMuteWord(matchedWord, settings)) {
            forwardMuteToActiveTab(start, end, matchedWord, settings.showDebugOverlay);
        }
    });
}

function scheduleReconnect() {
    if (reconnectTimer) {
        return;
    }
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
    }, RECONNECT_DELAY_MS);
}

function connectWebSocket() {
    try {
        socket = new WebSocket(WS_URL);
    } catch (error) {
        console.warn("WebSocket init failed, retrying...", error);
        scheduleReconnect();
        return;
    }

    socket.onopen = () => {
        console.info("Connected to mute websocket server.");
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.mute) {
                handleMuteMessage(data);
            }
        } catch (error) {
            console.warn("Invalid websocket payload:", error);
        }
    };

    socket.onerror = () => {
        // onclose will also fire; keep this minimal.
    };

    socket.onclose = () => {
        console.warn("WebSocket disconnected. Retrying...");
        scheduleReconnect();
    };
}

connectWebSocket();