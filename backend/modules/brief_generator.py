import json
import os
from anthropic import AsyncAnthropic

BRIEF_SYSTEM_PROMPT = """You are a sales intelligence assistant for Owner.com's outbound sales team.

Owner.com helps independent restaurants build their own branded online ordering system, replacing expensive third-party delivery platforms. DoorDash, UberEats, and Grubhub charge 20-30% commission on every order. Owner.com lets restaurants keep that margin and own their customer relationships.

IDEAL CUSTOMER PROFILE:
- Independent (non-franchise) restaurant
- Already doing delivery via DoorDash, UberEats, or Grubhub
- Has a digital presence
- NOT: franchise chains, dine-in only, pre-opening, delivery-only dark kitchens

WHAT TOP REPS ACTUALLY SAY IN WINNING CALLS (use these as models for tone):
- "I saw you're on DoorDash and Grubhub — at 25-30% commission, that's a big chunk of every order. Have you looked at what that's actually costing you monthly?"
- "I noticed [Competitor] a few blocks away has 400+ Google reviews while you have 89 — I think we can help you close that gap and turn those searches into direct orders"
- "You're ranking #4 for [cuisine] in [city] — the top three all have their own direct ordering. Here's how we'd get you there"

Based on the restaurant intelligence data provided, output ONLY a valid JSON object — no markdown, no explanation:
{
  "online_visibility": "Describe their search visibility and name 2-3 specific competitors with any available context. If data is limited, say what was found.",
  "delivery_setup": "Which delivery platforms they're on and what this means for the pitch. If none detected, note that and suggest verifying.",
  "fit_signal": "green" or "yellow" or "red",
  "fit_reason": "One sentence explaining the fit assessment, specific to this restaurant.",
  "opening_suggestion": "One natural, specific opening line a rep could use. Ground it in the actual data. Not a script — a starting point."
}

RULES:
- Be specific. Name actual competitors from the data. Reference actual platforms found.
- If a data point is null or empty, say "could not verify" rather than fabricating details.
- GREEN = independent restaurant with delivery platform presence (clear ICP).
- YELLOW = proceed but verify — mixed signals or missing data.
- RED = franchise, dine-in only, structural non-fit.
- opening_suggestion must sound like a real person talking, not a sales bot."""


async def generate_brief(restaurant_name: str, city: str, intelligence_data: dict) -> dict:
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    competitors = intelligence_data.get("competitors_above") or []
    platforms = intelligence_data.get("delivery_platforms") or []
    rank = intelligence_data.get("google_rank")
    raw = intelligence_data.get("raw_signals", {})

    user_prompt = f"""Generate a pre-call brief for this restaurant:

Restaurant: {restaurant_name}
City: {city}

Intelligence gathered:
- Search rank (approximate): {rank if rank else "Not determined"}
- Competitors found: {json.dumps(competitors) if competitors else "None found"}
- Delivery platforms detected: {platforms if platforms else "None detected"}
- Fit signal from scraper: {intelligence_data.get("fit_signal", "unknown")}
- Fit reason: {intelligence_data.get("fit_reason", "")}
- Is franchise: {raw.get("is_franchise", False)}
- Review count (if found): {raw.get("review_count") or "Not found"}

Generate the brief JSON now."""

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=BRIEF_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    content = message.content[0].text.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    return json.loads(content)
