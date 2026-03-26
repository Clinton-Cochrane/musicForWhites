const FILTER_STATE_KEY = "censorNWord";
const BLOCKLIST_TERMS_KEY = "blocklistTerms";
const ALLOWLIST_TERMS_KEY = "allowlistTerms";
const DEBUG_OVERLAY_KEY = "showDebugOverlay";
const DEFAULT_BLOCKLIST_TERMS = ["nigg"];

const toggle = document.getElementById("censorToggle");
const label = document.getElementById("toggleLabel");
const debugOverlayToggle = document.getElementById("debugOverlayToggle");
const blocklistEl = document.getElementById("blocklistTerms");
const allowlistEl = document.getElementById("allowlistTerms");
const saveButton = document.getElementById("saveButton");
const saveStatus = document.getElementById("saveStatus");

function updateLabel(isEnabled) {
    label.textContent = isEnabled ? "Censor N-word" : "Allow N-word";
}

function parseTerms(rawText) {
    return rawText
        .split(",")
        .map((part) => part.trim().toLowerCase())
        .filter(Boolean);
}

function setStatus(message) {
    saveStatus.textContent = message;
    if (!message) {
        return;
    }
    setTimeout(() => {
        saveStatus.textContent = "";
    }, 1500);
}

chrome.storage.sync.get(
    [FILTER_STATE_KEY, BLOCKLIST_TERMS_KEY, ALLOWLIST_TERMS_KEY, DEBUG_OVERLAY_KEY],
    (result) => {
    const isEnabled = result[FILTER_STATE_KEY] !== false;
    const blocklistTerms = Array.isArray(result[BLOCKLIST_TERMS_KEY])
        ? result[BLOCKLIST_TERMS_KEY]
        : DEFAULT_BLOCKLIST_TERMS;
    const allowlistTerms = Array.isArray(result[ALLOWLIST_TERMS_KEY])
        ? result[ALLOWLIST_TERMS_KEY]
        : [];
    const showDebugOverlay = result[DEBUG_OVERLAY_KEY] === true;

    toggle.checked = isEnabled;
    updateLabel(isEnabled);
    debugOverlayToggle.checked = showDebugOverlay;
    blocklistEl.value = blocklistTerms.join(", ");
    allowlistEl.value = allowlistTerms.join(", ");
});

toggle.addEventListener("change", () => {
    const isEnabled = toggle.checked;
    chrome.storage.sync.set({ [FILTER_STATE_KEY]: isEnabled }, () => {
        updateLabel(isEnabled);
        setStatus("Toggle saved.");
    });
});

debugOverlayToggle.addEventListener("change", () => {
    chrome.storage.sync.set({ [DEBUG_OVERLAY_KEY]: debugOverlayToggle.checked }, () => {
        setStatus("Overlay setting saved.");
    });
});

saveButton.addEventListener("click", () => {
    const blocklistTerms = parseTerms(blocklistEl.value);
    const allowlistTerms = parseTerms(allowlistEl.value);

    chrome.storage.sync.set(
        {
            [BLOCKLIST_TERMS_KEY]: blocklistTerms,
            [ALLOWLIST_TERMS_KEY]: allowlistTerms
        },
        () => {
            setStatus("Terms saved.");
        }
    );
});
