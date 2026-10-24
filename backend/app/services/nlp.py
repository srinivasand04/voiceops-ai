"""Intent detection, entity extraction and keywords (rule based, no model)."""
import re
from collections import Counter

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

INTENT_RULES: dict[str, list[str]] = {
    "refund_request": [r"\brefund", r"\bmoney back\b", r"\breimburse"],
    "delivery_delay": [
        r"\b(hasn't|haven't|not|never) (been )?(arrived|received|delivered)",
        r"\bsupposed to arrive\b",
        r"\bwhere is my (order|package)\b",
        r"\bdelay(ed)?\b",
        r"\bexpecting it\b",
        r"\bstill (haven't|have not)\b",
    ],
    "order_status": [r"\bstatus of\b", r"\btrack(ing)?\b", r"\bwhen will\b"],
    "cancellation": [r"\bcancel", r"\bunsubscribe\b"],
    "billing_issue": [r"\bcharged\b", r"\bbilling\b", r"\binvoice\b", r"\bdouble charge"],
    "technical_support": [r"\bnot working\b", r"\bbroken\b", r"\berror\b", r"\bcan't (log|sign)"],
    "complaint": [r"\bunacceptable\b", r"\bfrustrat", r"\bcomplain", r"\bdisappointed\b"],
}

PRODUCTS = [
    "headset", "headphones", "earbuds", "laptop", "phone", "charger", "tablet",
    "keyboard", "mouse", "monitor", "camera", "watch", "speaker", "router",
]

STOP = set(ENGLISH_STOP_WORDS) | {
    "yeah", "okay", "ok", "hello", "thank", "thanks", "please", "sure", "alright",
    "good", "afternoon", "morning", "just", "like", "will", "can", "know", "let",
    "going", "got", "really", "want", "need", "yes", "call", "calling", "madam", "sir",
}

NUMBER_WORDS = r"(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)"


def detect_intents(customer_text: str, full_text: str) -> dict:
    """Score every intent; words said by the customer count double."""
    scores: dict[str, int] = {}

    for intent, patterns in INTENT_RULES.items():
        total = 0

        for pattern in patterns:
            total += 2 * len(re.findall(pattern, customer_text, re.I))
            total += len(re.findall(pattern, full_text, re.I))

        if total:
            scores[intent] = total

    if not scores:
        return {"primary": "general_inquiry", "all": [], "scores": {}}

    ranked = sorted(scores, key=scores.get, reverse=True)

    return {"primary": ranked[0], "all": ranked, "scores": scores}


def extract_entities(text: str) -> dict:
    order_ids: list[str] = []

    # Whisper often hears "ORD1045" as "over D1045" or "or D 1045".
    for match in re.finditer(r"\b(?:ORD|OVER\s*D|OR\s*D)[-\s]?(\d{3,})\b", text, re.I):
        order_id = f"ORD{match.group(1)}"
        if order_id not in order_ids:
            order_ids.append(order_id)

    for match in re.finditer(r"\border (?:number|id) is\s+([A-Z]{0,4}-?\d{3,})", text, re.I):
        value = match.group(1).upper()
        if not any(value.endswith(o[3:]) for o in order_ids) and value not in order_ids:
            order_ids.append(value)

    products = [p for p in PRODUCTS if re.search(rf"\b{p}s?\b", text, re.I)]

    for match in re.finditer(
        r"\bordered (?:a|an|the|my)?\s*((?:[a-z]+\s){0,2}[a-z]+?)(?= (?:last|yesterday|on|and|but)\b|[.,])",
        text,
        re.I,
    ):
        phrase = match.group(1).strip().lower()
        if phrase and not any(phrase.endswith(p) for p in products):
            products.append(phrase)

    durations = sorted(
        {
            m.group(0).lower()
            for m in re.finditer(
                rf"\b{NUMBER_WORDS}(?: business)? (?:minute|hour|day|week|month)s?(?: ago)?\b",
                text,
                re.I,
            )
        }
    )
    amounts = sorted(set(re.findall(r"[$€£₹]\s?\d[\d,]*(?:\.\d+)?", text)))
    organizations = sorted(
        {o.title() for o in re.findall(r"\b(Amazon|Flipkart|FedEx|UPS|DHL|Walmart)\b", text, re.I)}
    )
    relative_dates = sorted(
        {d.lower() for d in re.findall(r"\b(yesterday|today|tomorrow|last week)\b", text, re.I)}
    )

    return {
        "order_ids": order_ids,
        "products": products,
        "durations": durations,
        "amounts": amounts,
        "organizations": organizations,
        "relative_dates": relative_dates,
    }


def extract_keywords(text: str, limit: int = 10) -> list[dict]:
    words = [w for w in re.findall(r"[a-z][a-z']+", text.lower()) if w not in STOP and len(w) > 2]
    counts: Counter = Counter(words)

    for (first, second), count in Counter(zip(words, words[1:])).items():
        if count >= 2:
            counts[f"{first} {second}"] = count * 2

    return [{"keyword": k, "count": c} for k, c in counts.most_common(limit)]
