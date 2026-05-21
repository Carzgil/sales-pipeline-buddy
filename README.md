# Sales Call Buddy · Owner.com

An internal tool for Owner.com's outbound sales reps.

It solves the two root causes of a 0–100% conversion rate variance identified across 150 real call transcripts:

- **Reps go into calls cold.** Top performers reference specific competitors, Google rankings, and delivery platforms by name in the first 60 seconds. Most reps don't. This brief generates that research automatically.
- **No systematic way to know what works.** The 10x variance in conversion rates across reps is behavioral, not tenure-related. The scorecard evaluates each call against the five behaviors that consistently separate wins from losses in Owner's own data.

---

## How to run it

### Requirements

- Python 3.11+
- Node.js 18+

### 1. Clone the repo

```bash
git clone https://github.com/Carzgil/sales-pipeline-buddy.git
cd sales-pipeline-buddy
```

### 2. Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at **http://localhost:8000**.

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the app is ready.

> **Note:** API keys are pre-configured in `.env.example` in both `backend/` and `frontend/`. The setup above copies them automatically via the `.env` files. No additional configuration needed.

---

## Running after initial setup

Once you've done the one-time install, starting the app each time only takes two commands (one per terminal):

**Terminal 1 — backend:**
```bash
cd backend
source venv/bin/activate   # Windows: venv\Scripts\activate
uvicorn main:app --reload
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

The `source venv/bin/activate` step is required every time you open a new terminal — `uvicorn` and all Python dependencies live inside the virtual environment and aren't available globally without it.

---

## Running the tests

```bash
cd backend
source venv/bin/activate
python -m pytest -v
```

37 tests across three files. All external calls (Claude API, DuckDuckGo) are mocked — no API keys needed to run tests.

---

## How it works

### ICP evaluation (pre-call brief)

The tool collects three types of intelligence before generating the brief:

1. **Platform detection** — scrapes the restaurant's own website for DoorDash, Uber Eats, Grubhub, ChowNow, Toast, and similar links. If nothing is found on the site, falls back to a Brave Search query to check for listings.
2. **Visibility** — runs a Google Places search to find the restaurant's review count and local competitors, plus a category search (e.g. "best Thai restaurant Brooklyn") to surface which competitors rank above them and by how much.
3. **Franchise check** — name-matches against a list of known chains. Franchises can't control their own website or ordering, so they're disqualified immediately.

Claude then receives all of this as structured data and writes the brief. It never invents details — if the data is thin, the brief says so explicitly.

#### Fit signal logic

The fit signal is determined by commission marketplace presence (DoorDash, Uber Eats, Grubhub — the platforms charging 20–30% per order):

| Signal | Rule |
|--------|------|
| 🟢 **Confirmed Fit** | 2 or more commission platforms detected |
| 🟡 **Verify in Discovery** | Exactly 1 commission platform detected |
| 🔴 **Likely Non-Fit** | No commission platforms detected, franchise match, or confirmed structural non-fit |

The logic is intentionally conservative on false negatives — a restaurant on one platform is yellow (call, verify volume) rather than green, because a single listing in search results doesn't confirm an active delivery operation.

---

### Transcript grader (post-call scorecard)

1. Rep pastes a transcript or uploads a `.txt` / `.pdf` file after the call
2. Claude scores it against five behavioral dimensions derived from 150 real Owner.com calls
3. Each dimension returns **pass or fail** with a **direct quote from the transcript** as the evidence — no paraphrasing, no inference beyond what was said
4. A single coaching note is generated at the end: one concrete, call-specific thing to do differently — never generic advice

#### The five dimensions

These came from the behavioral patterns that separate the 0% converters from the 100% converters in Owner's own data. Tenure explains almost none of the variance — it's all behavioral.

| # | Dimension | Pass condition |
|---|-----------|---------------|
| 1 | **Specific pre-call research** | Rep named a competitor, search rank, or platform specific to *this* restaurant — not "I ran some reports" |
| 2 | **Discovery before pitch** | Rep asked at least one meaningful question about the restaurant's situation *before* explaining Owner's product |
| 3 | **Named local social proof** | Rep cited a specific nearby restaurant by name with real numbers — not "our average customer sees $3,500/month" |
| 4 | **Established contact identity** | Rep confirmed the prospect's name and role, and used the name at least once after learning it |
| 5 | **ICP qualification before features** | Rep confirmed the restaurant does delivery or online ordering *before* pitching the full product |

---

## Architecture

```
backend/
  main.py                     # FastAPI — 4 routes
  database.py                 # SQLite (briefs + scorecards tables)
  seed.py                     # Batch-score existing transcripts (optional)
  modules/
    scraper.py                # DuckDuckGo restaurant intelligence
    brief_generator.py        # Claude → pre-call brief JSON
    transcript_scorer.py      # Claude → 5-dimension scorecard JSON
  tests/
    conftest.py               # Shared fixtures (test client, temp DB)
    test_scraper.py           # Unit tests — pure logic, no network
    test_database.py          # Async integration tests — SQLite
    test_api.py               # API tests — all endpoints, mocked externals

frontend/src/
  App.tsx                     # State machine: search → brief → postcall → scorecard
  api.ts                      # Typed fetch wrappers
  types.ts                    # Shared TypeScript types
  components/
    RestaurantSearch.tsx      # Google Places autocomplete + manual entry fallback
    BriefCard.tsx             # Pre-call brief (4 sections + fit badge)
    PostCallEvaluation.tsx    # Transcript paste / file upload
    ScorecardView.tsx         # 5-dimension scorecard + coaching note
```

### API

| Method | Path | Body / Params |
|--------|------|---------------|
| `POST` | `/api/brief` | `{restaurant_name, city, website_url?}` |
| `POST` | `/api/score` | form: `transcript_text` or `file`, `restaurant_name` |
| `GET` | `/api/briefs` | — |
| `GET` | `/api/scorecards` | — |
| `GET` | `/health` | — |

### Database (SQLite)

```sql
briefs(id, restaurant_name, city, brief_json, fit_signal, created_at)
scorecards(id, restaurant_name, transcript_hash, scorecard_json, coaching_note, created_at)
```

Raw transcripts are never stored — only the SHA-256 hash (deduplication) and the scored output.

---

## Seeding with existing transcripts (optional)

To pre-populate the database with scored historical transcripts:

```bash
cd backend
source venv/bin/activate
python seed.py /path/to/transcripts/   # accepts .txt and .pdf
```

---

## API keys

The `.env.example` files in `backend/` and `frontend/` contain working API keys for demo purposes:

- **Anthropic** — powers brief generation and transcript scoring (Claude Sonnet)
- **Google Places** — powers the restaurant search autocomplete

If you need to rotate these, replacements can be obtained from [console.anthropic.com](https://console.anthropic.com) and [console.cloud.google.com](https://console.cloud.google.com) (enable the Places API, create a key).
