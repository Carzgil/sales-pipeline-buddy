"""
Restaurant intelligence scraper.

Delivery platform detection: scrapes the restaurant's own website for
DoorDash/UberEats/Grubhub links — most reliable signal, zero rate-limit risk.

Competitor / ranking data: DuckDuckGo text search with sequential calls and
backoff to avoid rate limiting.
"""

import asyncio
import re
import time
from typing import Optional

import httpx
from duckduckgo_search import DDGS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FRANCHISE_INDICATORS = [
    "mcdonald", "subway", "chipotle", "starbucks", "domino", "pizza hut",
    "papa john", "taco bell", "chick-fil-a", "wendy", "burger king",
    "panera", "shake shack", "five guys", "wingstop", "chili", "applebee",
    "denny", "ihop", "olive garden", "red lobster", "cheesecake factory",
    "buffalo wild wings", "panda express", "popeyes", "kfc", "dunkin",
    "sonic", "dairy queen", "little caesars", "jersey mike", "jimmy john",
    "firehouse subs", "potbelly", "noodles & company", "einstein",
]

# Primary delivery marketplaces (paying 20-30% commission — core Owner ICP signal)
DELIVERY_PLATFORMS = {
    "DoorDash": ["doordash.com"],
    "Uber Eats": ["ubereats.com", "uber.com/eats"],
    "Grubhub": ["grubhub.com"],
}

# Other online ordering platforms (signal: restaurant does online ordering,
# knows what it costs, and is open to digital solutions)
ORDERING_PLATFORMS = {
    "ChowNow": ["chownow.com", "chownow-order"],
    "Toast": ["toasttab.com", "pos.toasttab"],
    "Slice": ["slicelife.com"],
    "Olo": ["oloapp.com", "olo.com"],
    "Bopple": ["bopple.com"],
}


# ---------------------------------------------------------------------------
# Pure logic helpers (tested, no I/O)
# ---------------------------------------------------------------------------

def _is_likely_franchise(name: str) -> bool:
    name_lower = name.lower()
    return any(indicator in name_lower for indicator in FRANCHISE_INDICATORS)


def _extract_review_count(text: str) -> Optional[int]:
    patterns = [
        r"(\d{1,5}(?:,\d{3})*)\s+(?:google\s+)?reviews?",
        r"\((\d{1,5}(?:,\d{3})*)\s+reviews?\)",
        r"(\d{1,5}(?:,\d{3})*)\s+ratings?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    return None


def _determine_fit_signal(
    name: str, is_franchise: bool, platforms: list, rank_info: dict
) -> tuple[str, str]:
    if is_franchise:
        return "red", f"{name} appears to be a franchise chain — Owner.com serves independent restaurants only"
    if len(platforms) >= 2:
        return "green", f"{name} is on {' and '.join(platforms)} — paying 20-30% commissions, strong ICP fit for Owner's direct ordering platform"
    if len(platforms) == 1:
        return "green", f"{name} is on {platforms[0]} — strong candidate for Owner's commission-free ordering platform"
    if rank_info.get("rank") is None:
        return "yellow", "Could not verify delivery presence — confirm ordering setup in discovery"
    return "yellow", f"{name} has online visibility but no detected delivery platform presence — verify if they do online ordering"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _ddg_text(query: str, max_results: int = 8) -> list:
    """Single DDG search with retry on rate limit."""
    for attempt in range(2):
        try:
            if attempt > 0:
                time.sleep(3)
            results = list(DDGS().text(query, max_results=max_results))
            if results:
                return results
        except Exception:
            pass
    return []


def _scrape_website_for_platforms(url: str) -> list:
    """
    Scrape the restaurant's own website for delivery platform links.
    This is the most reliable detection method — restaurants link directly
    to their ordering pages.
    """
    try:
        resp = httpx.get(url, timeout=8, follow_redirects=True, headers=HEADERS)
        content = resp.text.lower()
        found = []
        # Check high-commission delivery marketplaces first
        for platform, domains in DELIVERY_PLATFORMS.items():
            if any(domain in content for domain in domains):
                found.append(platform)
        # Also check other ordering platforms — signals restaurant does online ordering
        for platform, domains in ORDERING_PLATFORMS.items():
            if any(domain in content for domain in domains):
                found.append(platform)
        return found
    except Exception:
        return []


def _find_competitors(name: str, city: str) -> list:
    """Find local competitors using a single DDG search."""
    results = _ddg_text(f"best restaurants {city} reviews", max_results=12)
    competitors = []
    for result in results:
        title = result.get("title", "")
        body = result.get("body", "")
        if name.lower() in title.lower():
            continue
        if not any(
            kw in (title + body).lower()
            for kw in ["restaurant", "cafe", "bar", "grill", "kitchen", "bistro", "pizza", "sushi", "taco", "diner"]
        ):
            continue
        clean_name = re.split(r"\s*[\|\-–—]\s*", title)[0].strip()
        if not clean_name or clean_name.lower() == name.lower():
            continue
        review_count = _extract_review_count(body) or _extract_review_count(title)
        competitors.append({"name": clean_name, "review_count": review_count})
        if len(competitors) >= 3:
            break
    return competitors


def _find_platforms_via_search(name: str, city: str) -> list:
    """
    Fallback: search DDG for delivery platform presence when no website URL
    is available. Uses a single combined query instead of 3 parallel site: queries.
    """
    results = _ddg_text(f'"{name}" {city} order delivery', max_results=10)
    found = []
    for result in results:
        href = result.get("href", "")
        body = result.get("body", "").lower()
        all_platforms = {**DELIVERY_PLATFORMS, **ORDERING_PLATFORMS}
        for platform, domains in all_platforms.items():
            if platform not in found:
                if any(domain in href or domain in body for domain in domains):
                    found.append(platform)
    return found


def _check_search_rank(name: str, city: str) -> dict:
    """Approximate search rank from DDG results."""
    results = _ddg_text(f"{name} {city}", max_results=8)
    for i, result in enumerate(results):
        title = result.get("title", "")
        href = result.get("href", "")
        body = result.get("body", "")
        if name.lower() in title.lower() or name.lower() in href.lower():
            review_count = _extract_review_count(body) or _extract_review_count(title)
            return {
                "rank": i + 1,
                "context": f"Appears in top {i + 1} search results for '{name} {city}'",
                "snippet": body[:200],
                "review_count": review_count,
            }
    return {"rank": None, "context": f"Could not determine search rank for {name}", "snippet": ""}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def search_restaurant_intelligence(
    name: str, city: str, website_url: Optional[str] = None
) -> dict:
    """
    Gather restaurant intelligence for the pre-call brief.

    Strategy:
    1. Delivery platforms: scrape the restaurant's own website first (most reliable).
       Fall back to a DDG search if no URL is available.
    2. Competitors + rank: sequential DDG calls with a delay between them to
       avoid rate limiting.
    """
    is_franchise = _is_likely_franchise(name)

    # --- Delivery platforms ---
    # Website scraping is done synchronously in a thread since httpx.get is blocking.
    # DDG fallback only fires when there's no website URL.
    if website_url:
        platforms = await asyncio.to_thread(_scrape_website_for_platforms, website_url)
        if not platforms:
            # Website didn't have obvious links — try a search too
            await asyncio.sleep(0.5)
            platforms = await asyncio.to_thread(_find_platforms_via_search, name, city)
    else:
        platforms = await asyncio.to_thread(_find_platforms_via_search, name, city)

    # --- Competitors (sequential, 1.5s after platform search) ---
    await asyncio.sleep(1.5)
    competitors = await asyncio.to_thread(_find_competitors, name, city)

    # --- Search rank (sequential, 1.5s after competitors) ---
    await asyncio.sleep(1.5)
    rank_info = await asyncio.to_thread(_check_search_rank, name, city)

    fit_signal, fit_reason = _determine_fit_signal(name, is_franchise, platforms, rank_info)

    return {
        "google_rank": rank_info.get("rank"),
        "competitors_above": competitors,
        "delivery_platforms": platforms,
        "fit_signal": fit_signal,
        "fit_reason": fit_reason,
        "raw_signals": {
            "is_franchise": is_franchise,
            "rank_context": rank_info.get("context", ""),
            "review_count": rank_info.get("review_count"),
        },
    }
