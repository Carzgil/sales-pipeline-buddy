"""
Unit tests for scraper logic — no network calls, pure function tests.
"""

import pytest
from modules.scraper import (
    _determine_fit_signal,
    _extract_review_count,
    _is_likely_franchise,
)


# ---------------------------------------------------------------------------
# Franchise detection
# ---------------------------------------------------------------------------

class TestFranchiseDetection:
    def test_known_chains_detected(self):
        assert _is_likely_franchise("McDonald's") is True
        assert _is_likely_franchise("Subway Sandwich Co.") is True
        assert _is_likely_franchise("Pizza Hut Express") is True
        assert _is_likely_franchise("KFC") is True
        assert _is_likely_franchise("Chipotle Mexican Grill") is True
        assert _is_likely_franchise("Domino's Pizza") is True
        assert _is_likely_franchise("Taco Bell") is True

    def test_independent_restaurants_not_flagged(self):
        assert _is_likely_franchise("Tony's Pizza") is False
        assert _is_likely_franchise("Maria's Kitchen") is False
        assert _is_likely_franchise("The Blue Duck") is False
        assert _is_likely_franchise("Golden Bowl") is False
        assert _is_likely_franchise("Hillside Grill") is False

    def test_case_insensitive(self):
        assert _is_likely_franchise("MCDONALD'S") is True
        assert _is_likely_franchise("mcdonald's") is True


# ---------------------------------------------------------------------------
# Review count extraction
# ---------------------------------------------------------------------------

class TestReviewCountExtraction:
    def test_standard_format(self):
        assert _extract_review_count("4.5 stars, 234 reviews") == 234

    def test_parenthetical_format(self):
        assert _extract_review_count("(1,234 reviews)") == 1234

    def test_google_reviews_format(self):
        assert _extract_review_count("500 Google reviews") == 500

    def test_ratings_format(self):
        assert _extract_review_count("1,500 ratings") == 1500

    def test_no_review_count(self):
        assert _extract_review_count("Great food, no numbers here") is None
        assert _extract_review_count("") is None

    def test_comma_separated_thousands(self):
        assert _extract_review_count("2,847 reviews") == 2847


# ---------------------------------------------------------------------------
# Fit signal determination
# ---------------------------------------------------------------------------

class TestFitSignal:
    def test_franchise_is_red(self):
        sig, reason = _determine_fit_signal("McDonald's", True, [])
        assert sig == "red"
        assert "franchise" in reason.lower()

    def test_two_platforms_is_green(self):
        sig, reason = _determine_fit_signal("Tony's Pizza", False, ["DoorDash", "Uber Eats"])
        assert sig == "green"
        assert "DoorDash" in reason

    def test_one_platform_is_yellow(self):
        # 1 commission platform = yellow (verify volume) — needs 2+ for confirmed green
        sig, reason = _determine_fit_signal("Maria's Kitchen", False, ["Grubhub"])
        assert sig == "yellow"
        assert "Grubhub" in reason

    def test_no_platforms_is_red(self):
        # 0 commission platforms = red — no delivery pain to solve
        sig, reason = _determine_fit_signal("Unknown Restaurant", False, [])
        assert sig == "red"

    def test_no_commission_platform_with_ordering_tool_is_red(self):
        # Toast only = no commission exposure = red
        sig, reason = _determine_fit_signal("Visible Place", False, ["Toast"])
        assert sig == "red"

    def test_franchise_overrides_platform_presence(self):
        # Even if platforms are found, a franchise is still a non-fit
        sig, reason = _determine_fit_signal("Subway", True, ["DoorDash"])
        assert sig == "red"

    def test_reason_is_nonempty_string(self):
        for platforms in [[], ["DoorDash"], ["DoorDash", "Uber Eats"]]:
            _, reason = _determine_fit_signal("Test", False, platforms)
            assert isinstance(reason, str)
            assert len(reason) > 0
