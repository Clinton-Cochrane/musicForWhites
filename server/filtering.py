DEFAULT_BLOCKLIST_TERMS = ["nigg"]


def _normalize_terms(terms):
    return [str(term).lower().strip() for term in terms if str(term).strip()]


def should_mute_word(word_text, blocklist_terms=None, allowlist_terms=None):
    normalized_word = str(word_text).lower().strip()
    if not normalized_word:
        return False

    blocklist = _normalize_terms(blocklist_terms or DEFAULT_BLOCKLIST_TERMS)
    allowlist = _normalize_terms(allowlist_terms or [])

    if any(term in normalized_word for term in allowlist):
        return False

    return any(term in normalized_word for term in blocklist)
