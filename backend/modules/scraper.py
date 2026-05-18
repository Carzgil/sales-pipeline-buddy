import asyncio
import re
from typing import Optional

from duckduckgo_search import DDGS


FRANCHISE_INDICATORS = [
    "mcdonald", "subway", "chipotle", "starbucks", "domino", "pizza hut",
    "papa john", "taco bell", "chick-fil-a", "wendy", "burger king",
    "panera", "shake shack", "five guys", "wingstop", "chili", "applebee",
    "denny", "ihop", "olive garden", "red lobster", "cheesecake factory",
    "buffalo wild wings", "panda express", "popeyes", "kfc", "dunkin",
    "sonic", "dairy queen", "little caesars", "jersey mike", "jimmy john",
    "firehouse subs", "potbelly", "noodles & company", "einstein",
]


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


def _ddg_text(query: str, max_results: int = 10) -> list:
    try:
        return list(DDGS().text(query, max_results=max_results))
    except Exception:
        return []


def _find_competitors(name: str, city: str) -> list:
    results = _ddg_text(f"best restaurants {city}", max_results=15)
    competitors = []
    for result in results:
        title = result.get("title", "")
        body = result.get("body", "")
        if name.lower() in title.lower():
            continue
        if not any(
            kw in (title + body).lower()
            for kw in ["restaurant", "cafe", "bar", "grill", "kitchen", "bistro", "eatery", "diner", "pizza", "sushi", "taco"]
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


def _check_delivery_platforms(name: str, city: str) -> list:
    platforms = []
    checks = {
        "DoorDash": f'"{name}" {city} site:doordash.com',
        "Uber Eats": f'"{name}" {city} site:ubereats.com',
        "Grubhub": f'"{name}" {city} site:grubhub.com',
    }
    for platform_name, query in checks.items():
        results = _ddg_text(query, max_results=3)
        for r in results:
            href = r.get("href", "")
            domain = platform_name.lower().replace(" ", "").replace("uber", "uber").replace("eats", "eats")
            domain_map = {"DoorDash": "doordash.com", "Uber Eats": "ubereats.com", "Grubhub": "grubhub.com"}
            if domain_map[platform_name] in href:
                platforms.append(platform_name)
                break
    return platforms


def _check_search_rank(name: str, city: str) -> dict:
    results = _ddg_text(f"{name} {city} restaurant", max_results=10)
    for i, result in enumerate(results):
        title = result.get("title", "")
        href = result.get("href", "")
        body = result.get("body", "")
        if name.lower() in title.lower() or name.lower() in href.lower():
            review_count = _extract_review_count(body) or _extract_review_count(title)
            return {
                "rank": i + 1,
                "context": f"Ranked #{i + 1} in search results for '{name} {city}'",
                "snippet": body[:200] if body else "",
                "review_count": review_count,
            }
    return {"rank": None, "context": f"Could not determine search rank for {name}", "snippet": ""}


def _determine_fit_signal(name: str, is_franchise: bool, platforms: list, rank_info: dict) -> tuple[str, str]:
    if is_franchise:
        return "red", f"{name} appears to be a franchise chain — Owner.com serves independent restaurants only"
    if len(platforms) >= 2:
        platform_str = " and ".join(platforms)
        return "green", f"{name} is on {platform_str} — paying 20-30% commissions, strong ICP fit for Owner's direct ordering platform"
    if len(platforms) == 1:
        return "green", f"{name} is on {platforms[0]} — strong candidate for Owner's commission-free ordering platform"
    if rank_info.get("rank") is None:
        return "yellow", "Could not verify delivery presence or online visibility — confirm delivery setup in discovery"
    return "yellow", f"{name} has online visibility but no detected delivery platform presence — verify if they do online ordering"


async def search_restaurant_intelligence(name: str, city: str, website_url: Optional[str] = None) -> dict:
    is_franchise = _is_likely_franchise(name)

    competitors, platforms, rank_info = await asyncio.gather(
        asyncio.to_thread(_find_competitors, name, city),
        asyncio.to_thread(_check_delivery_platforms, name, city),
        asyncio.to_thread(_check_search_rank, name, city),
    )

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
