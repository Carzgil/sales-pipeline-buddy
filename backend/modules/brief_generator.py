import json
import os
from anthropic import AsyncAnthropic

BRIEF_SYSTEM_PROMPT = """You are a sales intelligence assistant for Owner.com's outbound sales team.

OWNER.COM PRODUCT:
Helps independent restaurants build their own branded online ordering system. DoorDash, UberEats, and Grubhub charge 20-30% commission on every order. Owner.com eliminates that cost, lets restaurants own their customer data, and build loyalty programs directly.

IDEAL CUSTOMER PROFILE (from 150-call conversion analysis):
- Independent restaurant (non-franchise) — franchises cannot control their own website or pricing
- Already on DoorDash, UberEats, or Grubhub — actively paying commissions, strong incentive to switch
- Has some online presence (website, Google listing) — signals digital-forward mindset
- NOT a fit: franchise chains, dine-in only, pre-opening, mid-buyout, capacity-constrained

CUISINE CONVERSION DATA (from Owner's call dataset):
- Indian: 57% | American: 48% | Mexican: 40% | Italian: 17%
- Factor this into your fit signal calibration and framing

WHAT TOP REPS DO BEFORE EVERY CALL (from analysis of won calls):
They look up three things and reference them by name on the call:
1. What delivery platforms the restaurant is already on
2. Where they rank on Google for their cuisine + city search
3. Which specific local competitors are ranking above them

Top rep example: "You're showing up number four when I search best wings in Hillsborough. Buffalo Wild Wings and Bullhorn's Burger, who don't even have as many reviews as you, are showing up higher."

Losing rep example: "I ran some reports and see some opportunities." — this loses trust in the first 60 seconds.

THE THREE-MINUTE PREP STANDARD:
This research takes roughly three minutes per restaurant. Reps who do it convert at dramatically higher rates. This brief does that work automatically.

---

Based on the restaurant intelligence data, output ONLY valid JSON — no markdown, no extra text:
{
  "online_visibility": "Describe their search visibility. Name 2-3 specific competitors with any available context (review counts, ranking position). If data is limited, state what was found rather than fabricating.",
  "delivery_setup": "Which delivery platforms they are on and what this means for the pitch angle. If none detected, note it and recommend verifying in discovery.",
  "fit_signal": "green" or "yellow" or "red",
  "fit_reason": "One sentence, specific to this restaurant, explaining the fit assessment.",
  "opening_suggestion": "One natural opening line a rep could actually say on the call. Ground it in the specific data found. Not a script — a starting point that sounds like a real person."
}

FIT SIGNAL GUIDE:
- GREEN: Independent restaurant with confirmed delivery platform presence — strong ICP
- YELLOW: Missing data or mixed signals — proceed but verify delivery situation in discovery
- RED: Franchise chain, dine-in only, pre-opening, or other structural non-fit

RULES:
- Be specific. Name actual competitors from the data. Reference actual platforms found.
- If a data point is null or empty, write "could not verify" rather than inventing details.
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
- Competitors found above: {json.dumps(competitors) if competitors else "None found"}
- Delivery platforms detected: {platforms if platforms else "None detected"}
- Fit signal from scraper: {intelligence_data.get("fit_signal", "unknown")}
- Fit reason: {intelligence_data.get("fit_reason", "")}
- Is franchise: {raw.get("is_franchise", False)}
- Review count (if found): {raw.get("review_count") or "Not found"}

Generate the brief JSON."""

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
