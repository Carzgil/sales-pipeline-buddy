"""
Async integration tests for database operations.
Uses a temp SQLite file via monkeypatching so tests never touch the real DB.
"""

import pytest
import database


@pytest.fixture(autouse=True)
async def test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    await database.init_db()


# ---------------------------------------------------------------------------
# Briefs
# ---------------------------------------------------------------------------

class TestBriefs:
    async def test_save_and_retrieve_brief(self):
        await database.save_brief(
            restaurant_name="Tony's Pizza",
            city="Austin, TX",
            brief_json={"fit_signal": "green", "fit_reason": "On DoorDash and Uber Eats"},
            fit_signal="green",
        )
        briefs = await database.get_recent_briefs()
        assert len(briefs) == 1
        assert briefs[0]["restaurant_name"] == "Tony's Pizza"
        assert briefs[0]["city"] == "Austin, TX"
        assert briefs[0]["fit_signal"] == "green"
        assert briefs[0]["brief"]["fit_reason"] == "On DoorDash and Uber Eats"

    async def test_returns_most_recent_first(self):
        await database.save_brief("First", "City A", {}, "green")
        await database.save_brief("Second", "City B", {}, "yellow")
        await database.save_brief("Third", "City C", {}, "red")

        briefs = await database.get_recent_briefs()
        assert briefs[0]["restaurant_name"] == "Third"
        assert briefs[-1]["restaurant_name"] == "First"

    async def test_limit_is_respected(self):
        for i in range(5):
            await database.save_brief(f"Restaurant {i}", "City", {}, "green")
        briefs = await database.get_recent_briefs(limit=2)
        assert len(briefs) == 2

    async def test_empty_returns_empty_list(self):
        briefs = await database.get_recent_briefs()
        assert briefs == []


# ---------------------------------------------------------------------------
# Scorecards
# ---------------------------------------------------------------------------

class TestScorecards:
    async def test_save_and_retrieve_scorecard(self):
        scorecard = {
            "dimensions": [{"name": "Discovery before pitch", "passed": True, "evidence": "..."}],
            "coaching_note": "You did well but never asked about commission rates.",
        }
        await database.save_scorecard(
            restaurant_name="Maria's Kitchen",
            transcript_hash="abc123",
            scorecard_json=scorecard,
            coaching_note=scorecard["coaching_note"],
        )
        scorecards = await database.get_recent_scorecards()
        assert len(scorecards) == 1
        assert scorecards[0]["restaurant_name"] == "Maria's Kitchen"
        assert scorecards[0]["coaching_note"] == scorecard["coaching_note"]

    async def test_duplicate_hash_is_skipped(self):
        scorecard = {"dimensions": [], "coaching_note": "Test"}
        await database.save_scorecard("Rest A", "same-hash", scorecard, "Test")
        await database.save_scorecard("Rest B", "same-hash", scorecard, "Test")

        scorecards = await database.get_recent_scorecards()
        assert len(scorecards) == 1  # second write was ignored

    async def test_different_hashes_both_saved(self):
        scorecard = {"dimensions": [], "coaching_note": "Test"}
        await database.save_scorecard("Rest A", "hash-1", scorecard, "Test")
        await database.save_scorecard("Rest B", "hash-2", scorecard, "Test")

        scorecards = await database.get_recent_scorecards()
        assert len(scorecards) == 2
