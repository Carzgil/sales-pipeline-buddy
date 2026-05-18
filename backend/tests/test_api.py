"""
API integration tests using FastAPI's TestClient.
Claude API and scraper calls are mocked — tests verify routing, validation,
request/response contracts, and database persistence.
"""

import pytest
from unittest.mock import AsyncMock, patch

MOCK_INTELLIGENCE = {
    "google_rank": 3,
    "competitors_above": [{"name": "Competitor A", "review_count": 450}],
    "delivery_platforms": ["DoorDash", "Uber Eats"],
    "fit_signal": "green",
    "fit_reason": "Independent restaurant on two delivery platforms.",
    "raw_signals": {"is_franchise": False, "rank_context": "Ranked #3", "review_count": 89},
}

MOCK_BRIEF = {
    "online_visibility": "Ranked #3 for pizza in Austin, losing to Competitor A (450 reviews).",
    "delivery_setup": "On DoorDash and Uber Eats — paying ~25% commission per order.",
    "fit_signal": "green",
    "fit_reason": "Independent restaurant on two delivery platforms — strong ICP fit.",
    "opening_suggestion": "I saw you're on DoorDash and Uber Eats — you're probably handing over 25% on every order. Have you looked at what that costs monthly?",
}

MOCK_SCORECARD = {
    "dimensions": [
        {"name": "Specific pre-call research referenced", "passed": True, "evidence": "You're ranking #4 for pizza in Austin..."},
        {"name": "Discovery before pitch", "passed": False, "evidence": "Not found in transcript"},
        {"name": "Named local social proof", "passed": True, "evidence": "Nadir at Maka Indian, a few miles from you..."},
        {"name": "Established contact identity", "passed": True, "evidence": "So John, here's what I'd suggest..."},
        {"name": "ICP qualification before features", "passed": False, "evidence": "Not found in transcript"},
    ],
    "coaching_note": "You confirmed they were on DoorDash but never asked their commission rate — that single question is the most common pivot point in won calls on delivery-active restaurants.",
}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Brief generation
# ---------------------------------------------------------------------------

class TestBriefEndpoint:
    @patch("main.search_restaurant_intelligence", new_callable=AsyncMock, return_value=MOCK_INTELLIGENCE)
    @patch("main.generate_brief", new_callable=AsyncMock, return_value=MOCK_BRIEF)
    def test_success(self, _mock_brief, _mock_intel, client):
        response = client.post(
            "/api/brief",
            json={"restaurant_name": "Tony's Pizza", "city": "Austin, TX"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["brief"]["fit_signal"] == "green"
        assert "opening_suggestion" in data["brief"]
        assert "intelligence" in data

    @patch("main.search_restaurant_intelligence", new_callable=AsyncMock, return_value=MOCK_INTELLIGENCE)
    @patch("main.generate_brief", new_callable=AsyncMock, return_value=MOCK_BRIEF)
    def test_optional_website_url(self, _mock_brief, _mock_intel, client):
        response = client.post(
            "/api/brief",
            json={"restaurant_name": "Tony's Pizza", "city": "Austin, TX", "website_url": "https://tonys.com"},
        )
        assert response.status_code == 200

    def test_missing_city_is_rejected(self, client):
        response = client.post("/api/brief", json={"restaurant_name": "Tony's Pizza"})
        assert response.status_code == 422

    def test_missing_name_is_rejected(self, client):
        response = client.post("/api/brief", json={"city": "Austin, TX"})
        assert response.status_code == 422

    @patch("main.search_restaurant_intelligence", new_callable=AsyncMock, side_effect=Exception("Scraper error"))
    def test_scraper_failure_returns_500(self, _mock_intel, client):
        response = client.post(
            "/api/brief",
            json={"restaurant_name": "Tony's Pizza", "city": "Austin, TX"},
        )
        assert response.status_code == 500

    @patch("main.search_restaurant_intelligence", new_callable=AsyncMock, return_value=MOCK_INTELLIGENCE)
    @patch("main.generate_brief", new_callable=AsyncMock, return_value=MOCK_BRIEF)
    def test_brief_is_persisted(self, _mock_brief, _mock_intel, client):
        client.post("/api/brief", json={"restaurant_name": "Tony's Pizza", "city": "Austin, TX"})
        briefs = client.get("/api/briefs").json()
        assert len(briefs) == 1
        assert briefs[0]["restaurant_name"] == "Tony's Pizza"


# ---------------------------------------------------------------------------
# Transcript scoring
# ---------------------------------------------------------------------------

class TestScoreEndpoint:
    @patch("main.score_transcript", new_callable=AsyncMock, return_value=MOCK_SCORECARD)
    def test_score_with_pasted_text(self, _mock_scorer, client):
        response = client.post(
            "/api/score",
            data={
                "transcript_text": "Rep: Hello, I wanted to talk about your online presence. Prospect: Sure, go ahead.",
                "restaurant_name": "Tony's Pizza",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["scorecard"]["dimensions"]) == 5
        assert "coaching_note" in data["scorecard"]

    def test_empty_transcript_is_rejected(self, client):
        response = client.post("/api/score", data={"transcript_text": "   "})
        assert response.status_code == 400

    def test_no_transcript_is_rejected(self, client):
        response = client.post("/api/score", data={"restaurant_name": "Tony's Pizza"})
        assert response.status_code == 400

    @patch("main.score_transcript", new_callable=AsyncMock, return_value=MOCK_SCORECARD)
    def test_scorecard_is_persisted(self, _mock_scorer, client):
        client.post(
            "/api/score",
            data={"transcript_text": "This is a call transcript.", "restaurant_name": "Tony's Pizza"},
        )
        scorecards = client.get("/api/scorecards").json()
        assert len(scorecards) == 1

    @patch("main.score_transcript", new_callable=AsyncMock, return_value=MOCK_SCORECARD)
    def test_duplicate_transcript_not_double_saved(self, _mock_scorer, client):
        payload = {"transcript_text": "Same transcript text.", "restaurant_name": "Tony's Pizza"}
        client.post("/api/score", data=payload)
        client.post("/api/score", data=payload)  # same content → same hash

        scorecards = client.get("/api/scorecards").json()
        assert len(scorecards) == 1


# ---------------------------------------------------------------------------
# List endpoints
# ---------------------------------------------------------------------------

class TestListEndpoints:
    def test_briefs_empty(self, client):
        assert client.get("/api/briefs").json() == []

    def test_scorecards_empty(self, client):
        assert client.get("/api/scorecards").json() == []
