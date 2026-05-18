# Sales Call Buddy

An internal tool for Owner.com's outbound sales reps. It solves two problems identified through analysis of 150 real call transcripts:

1. **Reps go into calls cold.** Top performers look up three specific things before every dial (delivery platforms, Google rank, local competitors) and reference them by name. Most reps don't. This brief generates that research automatically in ~15 seconds.

2. **There's no systematic way to know what's working.** Conversion rates range from 0% to 100% across reps — tenure explains none of it. The gap is behavioral. The scorecard evaluates each call against the five behaviors that consistently separate wins from losses in Owner's own data.

---

## What the data showed

- Won calls average **6.6 min**. Lost calls average **3.9 min** (68% difference).
- When reps earn a 6+ minute call, they convert at **53.8%**. The problem is getting there.
- **34% of lost calls end in under 2 minutes** — preparation failures, not execution failures.
- **28% of lost calls were structural non-fits** (franchises, dine-in only, pre-opening) that could be screened before dialing.

---

## Prerequisites

- **Python 3.11+** — check with `python3 --version`
- **Node.js 18+** — install from [nodejs.org](https://nodejs.org) (LTS version) if needed
- **Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)
- **Google Places API key** *(optional)* — enables restaurant search autocomplete; falls back to manual entry without it

---

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd sales-pipeline-buddy
```

### 2. Backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Open `backend/.env` and add your Anthropic key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Start the server:

```bash
uvicorn main:app --reload
# Running at http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env
```

Open `frontend/.env`. At minimum set:

```
VITE_API_URL=http://localhost:8000
```

If you have a Google Places key (see below), also add:

```
VITE_GOOGLE_PLACES_API_KEY=AIza...
```

Start the dev server:

```bash
npm run dev
# Running at http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) — the app is ready to use.

---

## Getting your API keys

### Anthropic API key (required)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Navigate to **API Keys** → **Create Key**
4. Copy the key and paste it into `backend/.env` as `ANTHROPIC_API_KEY`

### Google Places API key (optional — takes ~5 minutes)

Without this key, the restaurant search falls back to a clean manual entry form that works perfectly for the demo.

To enable the autocomplete dropdown:

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project (or select an existing one)
3. Go to **APIs & Services → Library** and enable the **Places API**
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
5. (Recommended) Click the key → **Application restrictions → HTTP referrers** → add `localhost:5173/*`
6. Copy the key and paste it into `frontend/.env` as `VITE_GOOGLE_PLACES_API_KEY`

Google provides $200/month of free usage, more than enough for any demo.

---

## Running tests

Tests live in `backend/tests/`. They mock all external calls (Claude API, DuckDuckGo) so they run instantly with no API keys required.

```bash
cd backend
source venv/bin/activate
python -m pytest                   # run all tests
python -m pytest -v                # verbose output
python -m pytest tests/test_scraper.py   # one file
```

**Test coverage:**
- `test_scraper.py` — franchise detection, review count parsing, fit signal logic (pure unit tests)
- `test_database.py` — SQLite save/retrieve/deduplication (async integration tests)
- `test_api.py` — all API endpoints: routing, validation, error handling, persistence (mocked external calls)

---

## How it works

### Pre-call flow

1. Rep types a restaurant name → Google Places autocomplete (or manual entry)
2. Backend runs three searches in parallel:
   - DuckDuckGo: local competitor names and review counts
   - DuckDuckGo: approximate search rank for this restaurant
   - DuckDuckGo `site:` queries: delivery platform presence (DoorDash, UberEats, Grubhub)
3. Results feed a Claude API call that generates the brief and fit signal
4. Brief renders in ~15 seconds

### Post-call flow

1. Rep pastes transcript or uploads `.txt` / `.pdf`
2. Single Claude API call evaluates the five behavioral dimensions against the transcript
3. Scorecard renders in ~15 seconds with pass/fail per dimension, quoted evidence, and one coaching note

### Fit signal logic

| Signal | Meaning |
|--------|---------|
| 🟢 Green | Independent restaurant on delivery platforms — strong ICP |
| 🟡 Yellow | Missing data or mixed signals — proceed, verify in discovery |
| 🔴 Red | Franchise chain, dine-in only, pre-opening, or structural non-fit |

### Five scored behavioral dimensions

Derived from Owner's own transcript data — not generic sales best practices:

| Dimension | What it measures |
|-----------|-----------------|
| Specific pre-call research | Did the rep name competitors, rankings, or platforms for *this* restaurant? |
| Discovery before pitch | Did the rep ask at least one meaningful question before explaining Owner's product? |
| Named local social proof | Did the rep cite a *specific nearby restaurant by name* with concrete numbers? |
| Established contact identity | Did the rep learn and use the prospect's name and role? |
| ICP qualification before features | Did the rep confirm delivery/ordering volume before pitching the full product? |

---

## Architecture

```
backend/
  main.py                     # FastAPI app — 4 routes
  database.py                 # SQLite (briefs + scorecards tables)
  seed.py                     # Batch-score existing transcripts (optional)
  modules/
    scraper.py                # DuckDuckGo-based restaurant intelligence
    brief_generator.py        # Claude API → pre-call brief JSON
    transcript_scorer.py      # Claude API → 5-dimension scorecard JSON
  tests/
    conftest.py               # Shared fixtures (test client, temp DB)
    test_scraper.py           # Unit tests — pure logic, no network
    test_database.py          # Async integration tests — SQLite operations
    test_api.py               # API tests — mocked external calls

frontend/src/
  App.tsx                     # State machine: search → brief → postcall → scorecard
  api.ts                      # Typed fetch wrappers for backend endpoints
  types.ts                    # Shared TypeScript types
  components/
    RestaurantSearch.tsx      # Google Places autocomplete + manual entry fallback
    BriefCard.tsx             # Pre-call brief display (4 sections + fit badge)
    PostCallEvaluation.tsx    # Transcript paste / file upload
    ScorecardView.tsx         # 5-dimension scorecard + coaching note
```

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/brief` | Generate pre-call brief · body: `{restaurant_name, city, website_url?}` |
| `POST` | `/api/score` | Score transcript · form data: `transcript_text` or `file`, `restaurant_name` |
| `GET` | `/api/briefs` | Most recent 20 briefs from the database |
| `GET` | `/api/scorecards` | Most recent 20 scorecards from the database |
| `GET` | `/health` | Health check |

### Database schema (SQLite)

```sql
briefs(id, restaurant_name, city, brief_json, fit_signal, created_at)
scorecards(id, restaurant_name, transcript_hash, scorecard_json, coaching_note, created_at)
```

Raw transcripts are never stored — only the SHA-256 hash (for deduplication) and the scored output.

---

## Seeding the database with existing transcripts (optional)

If you want to pre-populate the database with scored transcripts for a demo:

```bash
cd backend
source venv/bin/activate
python seed.py /path/to/your/transcripts/
# Accepts .txt and .pdf files
# Scores each one and saves to the database
# Skips duplicates automatically
```

---

## Deployment (optional)

The app is designed to run locally and that's sufficient for a GitHub-based submission. If you want a live URL:

**Backend → Railway**
1. Create a Railway project pointed at the `backend/` directory
2. Set env var: `ANTHROPIC_API_KEY`
3. Railway auto-detects the `Procfile` → deploys at a `*.up.railway.app` URL

**Frontend → Vercel**
1. Connect your repo to Vercel, set root to `frontend/`
2. Set env vars:
   - `VITE_API_URL` = your Railway backend URL
   - `VITE_GOOGLE_PLACES_API_KEY` = your key (update HTTP referrer to your Vercel domain)

---

## Fixing the VS Code Python interpreter warning

If VS Code shows "package not found" warnings, point it to the venv:

1. `Cmd+Shift+P` → **Python: Select Interpreter**
2. Choose the interpreter at `backend/venv/bin/python`

The packages are installed in the venv — they work fine at runtime.
