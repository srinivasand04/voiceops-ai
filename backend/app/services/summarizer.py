"""Call summary and action items: Claude when a key is set, rules otherwise."""
import json
import os
import re

MODEL = os.getenv("VOICEOPS_LLM_MODEL", "claude-sonnet-5-5")

INTENT_TITLES = {
    "refund_request": "a refund",
    "delivery_delay": "a delayed delivery",
    "order_status": "an order status update",
    "cancellation": "a cancellation",
    "billing_issue": "a billing issue",
    "technical_support": "technical support",
    "complaint": "a complaint",
    "general_inquiry": "a general inquiry",
}


def _transcript_text(turns: list[dict], roles: dict[str, str]) -> str:
    return "\n".join(
        f"{roles.get(t['speaker'], 'customer').title()}: {t['text']}" for t in turns
    )


def _customer(roles: dict[str, str]) -> str:
    return next((s for s, r in roles.items() if r == "customer"), "")


def _rule_based(turns, roles, intents, entities, sentiment) -> dict:
    primary = intents["primary"]
    extra = [INTENT_TITLES[i] for i in intents["all"][1:3] if i in INTENT_TITLES]
    order = entities["order_ids"][0] if entities["order_ids"] else None
    product = entities["products"][0] if entities["products"] else None

    agent_text = " ".join(
        t["text"] for t in turns if roles.get(t["speaker"]) == "agent"
    ).lower()
    refund_done = bool(
        re.search(
            r"(initiate|submit|process)\w* (the |your |a )?refund|refund (request|has been|is)",
            agent_text,
        )
    )

    subject = f"order {order}" if order else "an order"
    if product:
        subject += f" ({product})"

    summary = (
        f"The customer called about {INTENT_TITLES.get(primary, 'an issue')} "
        f"regarding {subject}."
    )
    if extra:
        summary += f" They also raised {' and '.join(extra)}."
    if refund_done:
        timing = next(
            (d for d in entities["durations"] if "day" in d and not d.endswith("ago")),
            None,
        )
        summary += " The agent initiated a refund" + (
            f", expected within {timing}." if timing else "."
        )

    customer = sentiment["speakers"].get(_customer(roles), {})
    summary += (
        f" Customer sentiment was {customer.get('label', 'neutral')} "
        f"and {sentiment['customer_trend']} over the call."
    )

    actions = []
    if "delivery_delay" in intents["all"]:
        actions.append(f"Follow up with the courier about the delayed {subject}.")
    if refund_done or primary == "refund_request":
        actions.append(
            f"Confirm the refund for {subject} is processed and the customer is notified."
        )
    if "delivery_delay" in intents["all"]:
        actions.append("Review why the customer was not notified about the delay.")
    if not actions:
        actions.append("Review the call and follow up with the customer if needed.")

    return {"summary": summary, "action_items": actions, "source": "rules"}


def _claude(turns, roles, intents, entities, sentiment) -> dict | None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None

    try:
        import anthropic

        message = anthropic.Anthropic().messages.create(
            model=MODEL,
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Summarise this customer support call in 2-3 sentences and list "
                        "concrete follow-up action items. Reply with JSON only: "
                        '{"summary": str, "action_items": [str]}.\n\n'
                        f"Detected intent: {intents['primary']}\n"
                        f"Entities: {json.dumps(entities)}\n\n"
                        f"Transcript:\n{_transcript_text(turns, roles)}"
                    ),
                }
            ],
        )
        text = message.content[0].text
        data = json.loads(text[text.index("{") : text.rindex("}") + 1])
        return {
            "summary": str(data["summary"]),
            "action_items": [str(a) for a in data["action_items"]],
            "source": "claude",
        }
    except Exception:
        return None


def summarize(turns, roles, intents, entities, sentiment) -> dict:
    return _claude(turns, roles, intents, entities, sentiment) or _rule_based(
        turns, roles, intents, entities, sentiment
    )
