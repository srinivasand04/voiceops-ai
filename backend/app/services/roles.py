"""Guess which diarized speaker is the support agent and which the customer."""
import re

AGENT_CUES = [
    r"\bthank you for calling\b",
    r"\bhow (can|may) i (help|assist)\b",
    r"\bi('m| am) sorry (to hear|for)\b",
    r"\blet me (check|look|see|pull)\b",
    r"\bi can (see|help|check|submit|initiate|process)\b",
    r"\bi will (initiate|submit|process|escalate)\b",
    r"\bcould you (please )?(give|provide|confirm)\b",
    r"\bapologi[sz]e\b",
    r"\bfor the inconvenience\b",
    r"\bis there anything (else|i can)\b",
    r"\bmay i have\b",
]

CUSTOMER_CUES = [
    r"\bi('m| am) calling (about|regarding)\b",
    r"\bmy (order|package|refund|account|delivery)\b",
    r"\bi (haven't|have not) received\b",
    r"\bi (want|need|would like) (a|to|my)\b",
    r"\bcan i (get|have)\b",
    r"\bcan you (tell|refund|cancel)\b",
    r"\bwhy (wasn't|didn't|isn't|is)\b",
]


def _score(text: str, cues: list[str]) -> int:
    lowered = text.lower()
    return sum(len(re.findall(cue, lowered)) for cue in cues)


def assign_roles(turns: list[dict]) -> dict[str, str]:
    """Return {speaker_label: "agent" | "customer"}."""
    speakers = list(dict.fromkeys(t["speaker"] for t in turns))
    margin: dict[str, int] = {}

    for speaker in speakers:
        text = " ".join(t["text"] for t in turns if t["speaker"] == speaker)
        margin[speaker] = _score(text, AGENT_CUES) - _score(text, CUSTOMER_CUES)

    if len(speakers) < 2:
        return {s: "customer" for s in speakers}

    agent = max(speakers, key=lambda s: margin[s])
    return {s: ("agent" if s == agent else "customer") for s in speakers}
