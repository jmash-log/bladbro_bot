"""Turn natural language into a structured intent.

Rule-based, no ML. We match keywords and return an intent dict.
If nothing matches, we return 'unknown' — we never guess.
"""
import re


def parse_message(text):
    """Convert a message into an intent.

    Returns a dict like:
        {"intent": "NEXT_PERIOD", "date": None}
    """
    text = text.strip().lower()

    # --- Period started ---
    if re.search(r"\b(period|she|it)\s+(started|began|came|arrived)\b", text) \
       or re.search(r"\bgot my period\b", text) \
       or re.search(r"\bshe's here\b", text) \
       or text.startswith("started"):
        return {"intent": "START_PERIOD", "date": None}

    # --- Period ended ---
    if re.search(r"\b(period|it)\s+(ended|finished|stopped)\b", text) \
       or re.search(r"\bfinished\b", text) \
       and "period" in text:
        return {"intent": "END_PERIOD", "date": None}

    # --- Next period ---
    if re.search(r"\b(next|when).*(period|cycle)\b", text) \
       or re.search(r"\bperiod.*(next|due|coming)\b", text) \
       or text in ("next period?", "next?", "when?"):
        return {"intent": "NEXT_PERIOD", "date": None}

    # --- Current status / where am I ---
    if re.search(r"\b(status|where am i|cycle day|current)\b", text) \
       or text in ("status", "where am i?"):
        return {"intent": "STATUS", "date": None}

    # --- Stats ---
    if re.search(r"\b(stats|statistics|average|typical)\b", text) \
       or text == "stats":
        return {"intent": "STATS", "date": None}

    # --- Am I late? ---
    if re.search(r"\b(late|overdue)\b", text) \
       or text in ("am i late?", "late?"):
        return {"intent": "LATE", "date": None}
        # --- History with optional count ---
    
    m = re.search(r"\b(history|past|previous)\b.*?(\d+)", text)
    if m or re.search(r"\b(history|past|previous)\b", text):
        count = int(m.group(2)) if m else 5
        return {"intent": "HISTORY", "count": count}

    return {"intent": "UNKNOWN", "date": None}
