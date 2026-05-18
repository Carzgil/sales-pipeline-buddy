# Sales Call Buddy · Owner.com

An internal tool for Owner.com's outbound sales reps built as part of the Applied AI case study.

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
git clone <repo-url>
cd sales-pipeline-buddy
```

### 2. Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
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

### Pre-call brief

1. Rep searches for a restaurant by name (Google Places autocomplete, or manual entry)
2. The backend runs three DuckDuckGo searches in parallel: local competitors, approximate search rank, and delivery platform presence (DoorDash, UberEats, Grubhub)
3. Results are passed to Claude, which generates a structured brief in ~15 seconds
4. The brief includes: online visibility, delivery setup, a fit signal (green/yellow/red), and a personalized opening suggestion

### Post-call scorecard

1. Rep pastes a transcript or uploads a `.txt` / `.pdf` file
2. Claude evaluates the transcript against five behavioral dimensions in ~15 seconds
3. Each dimension returns a pass/fail with a direct quote from the transcript as evidence
4. A single coaching note surfaces the most important thing to do differently — specific to this call, not generic advice

### Five scored behavioral dimensions

Derived from Owner's own transcript data — not generic sales best practices:

| Dimension | What it measures |
|-----------|-----------------|
| Specific pre-call research referenced | Did the rep name competitors, rankings, or platforms specific to *this* restaurant? |
| Discovery before pitch | Did the rep ask at least one meaningful question before explaining Owner's product? |
| Named local social proof | Did the rep cite a *specific nearby restaurant by name* with concrete numbers? |
| Established contact identity | Did the rep learn and use the prospect's name and role? |
| ICP qualification before features | Did the rep confirm delivery/ordering volume before pitching the full product? |

### Fit signal

| Signal | Meaning |
|--------|---------|
| 🟢 Green | Independent restaurant with delivery platform presence — strong ICP |
| 🟡 Yellow | Missing data or mixed signals — proceed, verify in discovery |
| 🔴 Red | Franchise chain, dine-in only, pre-opening, or structural non-fit |

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
