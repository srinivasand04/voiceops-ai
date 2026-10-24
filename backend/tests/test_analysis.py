from app.services.analysis import analyze_turns
from app.services.nlp import detect_intents, extract_entities, extract_keywords
from app.services.roles import assign_roles
from app.services.sentiment import analyze_sentiment, label_for


TURNS = [
    {"start": 0, "end": 7, "speaker": "SPEAKER_01",
     "text": "Good afternoon. I'm calling about my online order. It was supposed to arrive yesterday, but I haven't received it yet."},
    {"start": 7, "end": 18, "speaker": "SPEAKER_00",
     "text": "I'm sorry to hear that. Could you please give me your order number?"},
    {"start": 18, "end": 28, "speaker": "SPEAKER_01",
     "text": "Yes, the order number is over D1045. I ordered a wireless headset last week."},
    {"start": 28, "end": 38, "speaker": "SPEAKER_00",
     "text": "Let me check. Your order was shipped three days ago, but the courier reported a delay."},
    {"start": 38, "end": 52, "speaker": "SPEAKER_01",
     "text": "Can you refund it to me please?"},
    {"start": 52, "end": 60, "speaker": "SPEAKER_00",
     "text": "Yes, sure. I will initiate the refund. You will get it in two days. Thank you for calling Amazon."},
]


def test_roles_identify_agent_and_customer():
    roles = assign_roles(TURNS)

    assert roles == {"SPEAKER_01": "customer", "SPEAKER_00": "agent"}


def test_label_thresholds():
    assert label_for(0.6) == "positive"
    assert label_for(-0.6) == "negative"
    assert label_for(0.0) == "neutral"


def test_sentiment_has_every_speaker_and_turn():
    roles = assign_roles(TURNS)
    result = analyze_sentiment(TURNS, roles)

    assert set(result["speakers"]) == {"SPEAKER_00", "SPEAKER_01"}
    assert len(result["turns"]) == len(TURNS)
    assert result["customer_trend"] in {"improving", "flat", "worsening"}


def test_negative_text_scores_negative():
    turns = [{"start": 0, "end": 3, "speaker": "A", "text": "This is terrible and I am furious."}]

    result = analyze_sentiment(turns, {"A": "customer"})

    assert result["speakers"]["A"]["label"] == "negative"


def test_intents_prefer_customer_words():
    result = detect_intents("my order has not arrived, I want a refund", "")

    assert result["primary"] in {"delivery_delay", "refund_request"}
    assert "refund_request" in result["all"]


def test_intent_defaults_to_general_inquiry():
    assert detect_intents("hello there", "hello there")["primary"] == "general_inquiry"


def test_entities_fix_misheard_order_id():
    entities = extract_entities(
        "The order number is over D1045. I ordered a wireless headset last week. "
        "It ships in two days. Thank you for calling Amazon."
    )

    assert entities["order_ids"] == ["ORD1045"]
    assert "headset" in entities["products"]
    assert "two days" in entities["durations"]
    assert entities["organizations"] == ["Amazon"]


def test_keywords_exclude_stop_words():
    keywords = [k["keyword"] for k in extract_keywords("the refund the refund order order order")]

    assert "the" not in keywords
    assert "order" in keywords


def test_full_analysis_without_llm_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = analyze_turns(TURNS)

    assert result["summary_source"] == "rules"
    assert result["intents"]["primary"] == "delivery_delay"
    assert "ORD1045" in result["summary"]
    assert any("refund" in item.lower() for item in result["action_items"])
