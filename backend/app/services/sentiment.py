"""Lexicon based sentiment per turn and per speaker (VADER)."""
import re
from functools import lru_cache

POSITIVE = 0.25
NEGATIVE = -0.25


@lru_cache(maxsize=1)
def _analyzer():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    return SentimentIntensityAnalyzer()


def label_for(score: float) -> str:
    if score >= POSITIVE:
        return "positive"
    if score <= NEGATIVE:
        return "negative"
    return "neutral"


# Politeness is scripted in support calls and says nothing about mood, so it is
# removed before scoring (VADER would read "sorry to hear that" as positive).
COURTESY = re.compile(
    r"thank you(?: very much| so much)?|thanks|you(?:'re| are) welcome|"
    r"(?:i(?:'m| am)|we(?:'re| are)) (?:very |so |really )?sorry(?: to hear that| for [a-z ]+)?|"
    r"sorry to hear that|apologi[sz]e[sd]?(?: for [a-z ]+)?|(?:for|about) the inconvenience|"
    r"have a (?:nice|good|great|lovely) day|good (?:morning|afternoon|evening)|please|"
    r"(?:is there )?anything else(?: i can help (?:you )?with)?",
    re.IGNORECASE,
)


def score_text(text: str) -> float:
    cleaned = COURTESY.sub(" ", text)

    if not re.search(r"[A-Za-z]{2}", cleaned):
        return 0.0

    return round(_analyzer().polarity_scores(cleaned)["compound"], 3)


def analyze_sentiment(turns: list[dict], roles: dict[str, str]) -> dict:
    """Score each turn, then summarise per speaker and for the whole call."""
    scored = []

    for turn in turns:
        score = score_text(turn["text"])
        scored.append(
            {
                "start": turn["start"],
                "end": turn["end"],
                "speaker": turn["speaker"],
                "role": roles.get(turn["speaker"], "customer"),
                "score": score,
                "label": label_for(score),
            }
        )

    speakers: dict[str, dict] = {}

    for speaker in dict.fromkeys(t["speaker"] for t in turns):
        own = [s for s in scored if s["speaker"] == speaker]
        average = round(sum(s["score"] for s in own) / len(own), 3)
        speakers[speaker] = {
            "role": roles.get(speaker, "customer"),
            "average": average,
            "label": label_for(average),
            "turns": len(own),
            "lowest": min(s["score"] for s in own),
            "highest": max(s["score"] for s in own),
        }

    customer_turns = [s for s in scored if s["role"] == "customer"]
    trend = "flat"

    if len(customer_turns) >= 2:
        change = customer_turns[-1]["score"] - customer_turns[0]["score"]
        trend = "improving" if change > 0.15 else "worsening" if change < -0.15 else "flat"

    overall = round(sum(s["score"] for s in scored) / len(scored), 3) if scored else 0.0

    return {
        "overall": {"score": overall, "label": label_for(overall)},
        "speakers": speakers,
        "customer_trend": trend,
        "turns": scored,
    }
