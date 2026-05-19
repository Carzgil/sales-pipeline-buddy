"""
Restaurant intelligence scraper.

Delivery platform detection: scrapes the restaurant's own website for
DoorDash/UberEats/Grubhub links — most reliable signal, zero rate-limit risk.
Falls back to Google Places (for website URL) + Brave Search when no URL provided.

Competitor / ranking data: Brave Search API — reliable, no rate limiting,
2,000 free queries/month. Falls back to empty results if key not configured.
"""

import asyncio
import os
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

RESTAURANT_VALIDATION_SITES = [
    "doordash.com", "ubereats.com", "grubhub.com",
    "yelp.com", "tripadvisor.com", "opentable.com", "resy.com",
    "toasttab.com", "chownow.com",
]

# Maps Google Places cuisine types → human-readable label for search queries
CUISINE_TYPE_MAP = {
    "french_restaurant": "French", "italian_restaurant": "Italian",
    "chinese_restaurant": "Chinese", "japanese_restaurant": "Japanese",
    "mexican_restaurant": "Mexican", "indian_restaurant": "Indian",
    "thai_restaurant": "Thai", "american_restaurant": "American",
    "mediterranean_restaurant": "Mediterranean", "greek_restaurant": "Greek",
    "spanish_restaurant": "Spanish", "korean_restaurant": "Korean",
    "vietnamese_restaurant": "Vietnamese", "seafood_restaurant": "seafood",
    "pizza_restaurant": "pizza", "sushi_restaurant": "sushi",
    "steak_house": "steakhouse", "burger_restaurant": "burger",
    "barbecue_restaurant": "BBQ", "ramen_restaurant": "ramen",
}

# Inferred from restaurant name when Places types aren't specific enough
NAME_CUISINE_KEYWORDS: dict[str, str] = {
    "pizza": "pizza", "sushi": "sushi", "ramen": "ramen", "pho": "Vietnamese",
    "taco": "Mexican", "tacos": "Mexican", "taqueria": "Mexican", "burrito": "Mexican",
    "bbq": "BBQ", "chinese": "Chinese", "thai": "Thai", "indian": "Indian",
    "italian": "Italian", "burger": "burger", "wings": "wings",
    "seafood": "seafood", "steakhouse": "steakhouse", "steak": "steakhouse",
    "soba": "Japanese", "izakaya": "Japanese",
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

# The three that charge the 20-30% commissions (highest-urgency pitch angle)
COMMISSION_PLATFORMS = {"DoorDash", "Uber Eats", "Grubhub"}

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

    commission_platforms = [p for p in platforms if p in COMMISSION_PLATFORMS]
    other_platforms = [p for p in platforms if p not in COMMISSION_PLATFORMS]

    if len(commission_platforms) >= 2:
        names = " and ".join(commission_platforms)
        return "green", f"{name} is on {names} — paying commissions on multiple channels, confirmed high-value ICP"
    if len(commission_platforms) == 1:
        return "yellow", (
            f"{name} is on {commission_platforms[0]} — paying commissions, likely strong ICP "
            "but verify ordering volume in discovery before pitching hard"
        )
    if other_platforms:
        return "yellow", (
            f"{name} uses {other_platforms[0]} for ordering — already invested in online ordering, "
            "open to direct platform conversation but different pitch angle than marketplace commission"
        )
    if rank_info.get("rank") is None:
        return "yellow", "Could not verify delivery presence — confirm online ordering setup in discovery"
    return "yellow", f"{name} has online visibility but no detected delivery platform presence — verify ordering setup in discovery"


def _infer_cuisine(name: str, google_types: list | None = None) -> Optional[str]:
    if google_types:
        for gt in google_types:
            if gt in CUISINE_TYPE_MAP:
                return CUISINE_TYPE_MAP[gt]
    name_lower = name.lower()
    for kw, cuisine in NAME_CUISINE_KEYWORDS.items():
        if kw in name_lower:
            return cuisine
    return None


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _brave_search(query: str, max_results: int = 8) -> list:
    """Search using Brave Search API. Returns [] if key not configured."""
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return []
    try:
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": min(max_results, 20), "search_lang": "en"},
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            timeout=8,
        )
        results = resp.json().get("web", {}).get("results", [])
        return [
            {"title": r.get("title", ""), "href": r.get("url", ""), "body": r.get("description", "")}
            for r in results
        ]
    except Exception:
        return []


def _get_places_info(name: str, city: str) -> dict:
    """
    Call Google Places Text Search to get the restaurant's website URL and
    review count. Used when no website URL is available from the frontend.
    Silently returns {} if the API key is missing or the call fails.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return {}
    try:
        resp = httpx.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": f"{name} restaurant {city}", "type": "restaurant", "key": api_key},
            timeout=6,
            headers=HEADERS,
        )
        results = resp.json().get("results", [])
        if not results:
            return {}
        place = results[0]
        info: dict = {
            "review_count": place.get("user_ratings_total"),
            "rating": place.get("rating"),
            "types": place.get("types", []),
        }
        place_id = place.get("place_id")
        if place_id:
            detail = httpx.get(
                "https://maps.googleapis.com/maps/api/place/details/json",
                params={"place_id": place_id, "fields": "website", "key": api_key},
                timeout=6,
                headers=HEADERS,
            ).json().get("result", {})
            info["website"] = detail.get("website")
        return info
    except Exception:
        return {}


def _validate_is_restaurant_sync(name: str, city: str) -> tuple[bool, str]:
    """
    Returns (True, "") when the input looks like a real restaurant.
    Returns (False, reason) when it clearly isn't — or can't be verified.
    Fails open (returns True) when neither API key is configured.
    """
    google_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    brave_key = os.environ.get("BRAVE_SEARCH_API_KEY")

    if not google_key and not brave_key:
        return True, ""

    # Google Places with type=restaurant is the most reliable signal
    if google_key:
        try:
            resp = httpx.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={"query": f"{name} {city}", "type": "restaurant", "key": google_key},
                timeout=6,
                headers=HEADERS,
            )
            data = resp.json()
            status = data.get("status")
            if status == "ZERO_RESULTS":
                return False, (
                    f'"{name}" in {city} doesn\'t appear to be a restaurant. '
                    "Please check the name and try again."
                )
            if status == "OK" and data.get("results"):
                return True, ""
        except Exception:
            pass  # Fall through to Brave

    # Brave fallback: name must appear alongside restaurant-platform signals
    if brave_key:
        results = _brave_search(f"{name} restaurant {city}", max_results=8)
        if not results:
            return True, ""  # Brave returned nothing — allow through rather than false-block

        name_lower = name.lower()
        for result in results:
            title = result.get("title", "").lower()
            href = result.get("href", "").lower()
            body = result.get("body", "")[:300].lower()
            combined = title + " " + href + " " + body
            if name_lower not in combined:
                continue
            if any(site in href for site in RESTAURANT_VALIDATION_SITES):
                return True, ""
            if any(kw in combined for kw in ["menu", "restaurant", "dining", "cuisine", "reservations", "takeout", "delivery"]):
                return True, ""

        return False, (
            f'"{name}" doesn\'t appear to be a restaurant. '
            "Please check the name and try again."
        )

    return True, ""


async def validate_restaurant(name: str, city: str) -> tuple[bool, str]:
    """Async entry point for restaurant validation. Import this in main.py."""
    return await asyncio.to_thread(_validate_is_restaurant_sync, name, city)


def _scrape_website_for_platforms(url: str) -> list:
    """
    Scrape the restaurant's own website for delivery platform links.
    First checks static HTML content, then follows ordering-related links
    one level deep to catch redirect-based "Order Now" buttons.
    """
    try:
        resp = httpx.get(url, timeout=8, follow_redirects=True, headers=HEADERS)
        content = resp.text.lower()
        all_platforms = {**DELIVERY_PLATFORMS, **ORDERING_PLATFORMS}
        found = set()

        for platform, domains in all_platforms.items():
            if any(domain in content for domain in domains):
                found.add(platform)

        if found:
            return list(found)

        # Follow ordering links one level deep to catch JS-redirect buttons
        base = f"{urlparse(str(resp.url)).scheme}://{urlparse(str(resp.url)).netloc}"
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', resp.text)
        order_links = [
            h for h in hrefs
            if any(kw in h.lower() for kw in ["order", "delivery", "pickup"])
            and not h.startswith(("#", "javascript", "mailto", "tel:"))
        ][:4]

        for href in order_links:
            target = href if href.startswith("http") else urljoin(base, href)
            try:
                r2 = httpx.get(target, timeout=5, follow_redirects=True, headers=HEADERS)
                final_url = str(r2.url).lower()
                content2 = r2.text.lower()
                for platform, domains in all_platforms.items():
                    if any(domain in final_url or domain in content2 for domain in domains):
                        found.add(platform)
            except Exception:
                continue

        return list(found)
    except Exception:
        return []


EDITORIAL_TITLE_PATTERNS = [
    "best restaurants", "top restaurants", "best places to eat",
    "food guide", "dining guide", "where to eat", "best eats",
    "top 10", "top 25", "top 50", "top 100", "restaurants in ",
    "best bars", "best brunch", "best lunch", "best dinner",
]

def _find_competitors(name: str, city: str, cuisine: Optional[str] = None) -> list:
    """Find local competitors using Brave Search, filtered to actual restaurants."""
    query = f"best {cuisine} restaurants {city}" if cuisine else f"best restaurants {city}"
    results = _brave_search(query, max_results=15)

    competitors = []
    name_lower = name.lower()

    for result in results:
        title = result.get("title", "")
        body = result.get("body", "")
        title_lower = title.lower()
        combined_lower = title_lower + " " + body.lower()

        # Skip the restaurant itself
        if name_lower in title_lower:
            continue

        # Skip editorial aggregation pages (the real problem)
        if any(ep in title_lower for ep in EDITORIAL_TITLE_PATTERNS):
            continue

        # Require actual restaurant-type keywords
        if not any(kw in combined_lower for kw in [
            "restaurant", "cafe", "café", "bar", "grill", "kitchen",
            "bistro", "pizza", "sushi", "taco", "diner", "eatery",
        ]):
            continue

        clean_name = re.split(r"\s*[\|\-–—]\s*", title)[0].strip()
        # Long titles are editorial pages that slipped through
        if not clean_name or len(clean_name) > 55 or clean_name.lower() == name_lower:
            continue

        review_count = _extract_review_count(body) or _extract_review_count(title)
        competitors.append({"name": clean_name, "review_count": review_count})
        if len(competitors) >= 3:
            break

    return competitors


def _find_platforms_via_search(name: str, city: str) -> list:
    """
    Fallback: search Brave for delivery platform presence when no website URL
    is available.
    """
    results = _brave_search(f'"{name}" {city} order delivery', max_results=10)
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


def _check_search_rank(name: str, city: str, cuisine: Optional[str] = None) -> dict:
    """Approximate brand + category search rank using Brave Search."""
    name_lower = name.lower()

    # Brand rank: how the restaurant shows up for its own name
    brand_results = _brave_search(f"{name} {city}", max_results=8)
    brand_rank = None
    snippet = ""
    review_count = None
    for i, result in enumerate(brand_results):
        title = result.get("title", "")
        href = result.get("href", "")
        body = result.get("body", "")
        if name_lower in title.lower() or name_lower in href.lower():
            brand_rank = i + 1
            snippet = body[:200]
            review_count = _extract_review_count(body) or _extract_review_count(title)
            break

    # Category rank: where the restaurant appears in cuisine-specific searches
    category_rank = None
    category_query = None
    if cuisine:
        category_query = f"best {cuisine} restaurant {city}"
        cat_results = _brave_search(category_query, max_results=10)
        for i, result in enumerate(cat_results):
            if name_lower in result.get("title", "").lower() or name_lower in result.get("href", "").lower():
                category_rank = i + 1
                break

    context_parts = []
    if brand_rank:
        context_parts.append(f"#{brand_rank} in brand search for '{name} {city}'")
    if category_rank and category_query:
        context_parts.append(f"#{category_rank} for '{category_query}'")
    elif category_query and category_rank is None:
        context_parts.append(f"Not found in top results for '{category_query}'")

    return {
        "rank": brand_rank,
        "category_rank": category_rank,
        "category_query": category_query,
        "context": " | ".join(context_parts) if context_parts else f"Could not determine search rank for {name}",
        "snippet": snippet,
        "review_count": review_count,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def search_restaurant_intelligence(
    name: str, city: str, website_url: Optional[str] = None
) -> dict:
    """
    Gather restaurant intelligence for the pre-call brief.

    Strategy:
    1. Google Places: get website URL + review count (reliable, no rate limits).
    2. Delivery platforms: scrape restaurant's website first; fall back to Brave Search.
    3. Competitors + rank: run in parallel via Brave Search (no rate limiting).
    """
    is_franchise = _is_likely_franchise(name)

    # --- Google Places: website URL, review count, and cuisine types ---
    places_info = await asyncio.to_thread(_get_places_info, name, city)
    effective_url = website_url or places_info.get("website")

    # Cuisine inferred from Places types first, restaurant name as fallback
    cuisine = _infer_cuisine(name, places_info.get("types", []))

    # --- Delivery platforms ---
    if effective_url:
        platforms = await asyncio.to_thread(_scrape_website_for_platforms, effective_url)
        if not platforms:
            platforms = await asyncio.to_thread(_find_platforms_via_search, name, city)
    else:
        platforms = await asyncio.to_thread(_find_platforms_via_search, name, city)

    # --- Competitors + rank in parallel, both cuisine-aware ---
    competitors, rank_info = await asyncio.gather(
        asyncio.to_thread(_find_competitors, name, city, cuisine),
        asyncio.to_thread(_check_search_rank, name, city, cuisine),
    )

    review_count = rank_info.get("review_count") or places_info.get("review_count")
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
            "review_count": review_count,
            "category_rank": rank_info.get("category_rank"),
            "category_query": rank_info.get("category_query"),
            "cuisine": cuisine,
        },
    }
