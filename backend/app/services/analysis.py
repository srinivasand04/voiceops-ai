from app.services.nlp import detect_intents, extract_entities, extract_keywords
from app.services.roles import assign_roles
from app.services.sentiment import analyze_sentiment
from app.services.summarizer import summarize


def analyze_turns(turns: list[dict]) -> dict:
    """Run sentiment, intent, entities, keywords and summary over speaker turns."""
    roles = assign_roles(turns)
    full_text = " ".join(t["text"] for t in turns)
    customer_text = " ".join(
        t["text"] for t in turns if roles[t["speaker"]] == "customer"
    )

    sentiment = analyze_sentiment(turns, roles)
    intents = detect_intents(customer_text, full_text)
    entities = extract_entities(full_text)
    keywords = extract_keywords(full_text)
    summary = summarize(turns, roles, intents, entities, sentiment)

    return {
        "roles": roles,
        "sentiment": sentiment,
        "intents": intents,
        "entities": entities,
        "keywords": keywords,
        "summary": summary["summary"],
        "action_items": summary["action_items"],
        "summary_source": summary["source"],
    }
