import json
import os
from anthropic import AsyncAnthropic

BRIEF_SYSTEM_PROMPT = """You are a sales intelligence assistant for Owner.com's outbound sales team.

OWNER.COM PRODUCT:
Helps independent restaurants build their own branded online ordering system. DoorDash, UberEats, and Grubhub charge 20-30% commission on every order. Owner.com eliminates that cost, lets restaurants own their customer data, and build direct loyalty programs.

IDEAL CUSTOMER PROFILE (from 150-call conversion analysis):
- Independent restaurant (non-franchise) — franchises cannot control their own website or pricing
- Already doing online ordering through ANY platform
- DoorDash/UberEats/Grubhub = paying 20-30% commission = strongest incentive to switch
- ChowNow/Toast/Slice/Olo = already invested in online ordering = knows the value, easier conversion
- NOT a fit: franchise chains, dine-in only, pre-opening, mid-buyout, capacity-constrained

CUISINE CONVERSION RATES (from Owner's call dataset):
- Indian: 57% | American: 48% | Mexican: 40% | Italian: 17%
- Use this to set urgency — a confirmed Indian restaurant on DoorDash is a premium lead

WHAT TOP REPS DO (from won-call analysis):
They reference three things by name on the call:
1. Exactly which delivery platforms the restaurant is on
2. Where they rank when someone searches their cuisine + city
3. Which specific local competitors show up above them

Top rep: "You're showing up number four when I search best wings in Hillsborough. Buffalo Wild Wings and Bullhorn's Burger — who have fewer reviews than you — are showing up higher."
Losing rep: "I ran some reports and see some opportunities." — kills trust in 60 seconds.

---

Output ONLY valid JSON — no markdown, no extra text:
{
  "online_visibility": "...",
  "delivery_setup": "...",
  "fit_signal": "green" | "yellow" | "red",
  "fit_reason": "...",
  "opening_suggestion": "..."
}

FIELD REQUIREMENTS — read these carefully:

online_visibility:
- State the exact search query competitors were measured against (e.g., "searching 'best pizza Austin, TX'")
- Name specific competitors from the data — use the names exactly as provided
- Include review counts if available (e.g., "Tony's has 340 reviews vs their 89")
- If category rank was provided, lead with it — that is the most actionable signal
- If the competitors data contains only editorial list pages ("The 100 Best Restaurants in NYC"), say so explicitly: state it as a data limitation, not as a ranking advantage
- Never invent competitor names or review counts not in the data

delivery_setup:
- List every platform detected by name
- For DoorDash/Uber Eats/Grubhub: state the commission implication plainly ("paying ~25% per order to DoorDash")
- For ChowNow/Toast/etc: note they're already invested in ordering infrastructure
- If nothing detected: write "No delivery platform presence detected — verify in discovery whether they take online orders at all"
- Do not say "could not verify" in isolation — state what IS known, then flag the gap

fit_signal:
- "green": Independent restaurant confirmed on 2 or more of DoorDash/Uber Eats/Grubhub
- "yellow": 1 commission platform, or ordering tools only, or meaningful data gaps — needs discovery
- "red": Franchise chain, confirmed dine-in only, or structural non-fit

fit_reason:
- One sentence, specific to this restaurant
- Reference the exact signal driving the assessment (platform name, missing data, franchise flag)
- Do not use the phrase "strong fit" — use a factual statement about what was found

opening_suggestion:
- Must reference at least one specific data point: a named competitor, a platform, a rank position, or a review count comparison
- Must sound like something a real person would say on the phone — not a sales template
- The goal is a "wait, how do you know that?" moment that signals the rep did their homework
- If the data is too thin to be specific, write a discovery-first opener that asks about their delivery setup rather than pretending to know it

BANNED PHRASES — never use these:
"strong fit", "great opportunity", "strong ICP", "I ran some reports", "I noticed some opportunities"
Any opener that starts with "Hi, I'm calling from Owner.com" or "I'm reaching out because"

ANTI-PATTERNS TO AVOID:
- Do not write a positive-sounding brief when the underlying data is thin
- Do not upgrade a yellow to a green based on vibes — the signal tiers are defined above
- Do not call editorial list pages ("The 100 Best Restaurants in NYC") actual competitors"""


async def generate_brief(restaurant_name: str, city: str, intelligence_data: dict) -> dict:
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    competitors = intelligence_data.get("competitors_above") or []
    platforms = intelligence_data.get("delivery_platforms") or []
    rank = intelligence_data.get("google_rank")
    raw = intelligence_data.get("raw_signals", {})

    brand_rank_str = f"#{rank} in brand search for '{restaurant_name} {city}'" if rank else "Not found in brand search"
    if raw.get("category_rank") and raw.get("category_query"):
        category_rank_str = f"#{raw['category_rank']} for '{raw['category_query']}'"
    elif raw.get("category_query"):
        category_rank_str = f"Not found in top results for '{raw['category_query']}'"
    else:
        category_rank_str = "Category search not performed (cuisine unknown)"

    competitors_str = (
        json.dumps(competitors, indent=2) if competitors
        else "None found — search returned no matching restaurant results"
    )
    platforms_str = ", ".join(platforms) if platforms else "None detected"

    user_prompt = f"""Generate a pre-call brief for:

Restaurant: {restaurant_name}
City: {city}
Cuisine: {raw.get("cuisine") or "Unknown"}

Intelligence gathered:
- Brand search rank: {brand_rank_str}
- Category search rank: {category_rank_str}
- Competitors found: {competitors_str}
- Delivery platforms confirmed: {platforms_str}
- Is franchise: {raw.get("is_franchise", False)}
- Review count: {raw.get("review_count") if raw.get("review_count") else "Not found"}
- Scraper fit signal: {intelligence_data.get("fit_signal", "unknown")} — {intelligence_data.get("fit_reason", "")}

Generate the JSON brief. Work from the data above — do not invent details not present here."""

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        thinking={"type": "enabled", "budget_tokens": 3000},
        system=BRIEF_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extended thinking returns a mix of thinking + text blocks; extract the text block
    content = next(
        (block.text.strip() for block in message.content if block.type == "text"),
        "",
    )
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    return json.loads(content)
