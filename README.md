# Sales Call Buddy

Internal tool for Owner.com's outbound sales reps. Generates a pre-call restaurant intelligence brief and scores post-call transcripts against the five behavioral dimensions that drive demo bookings.

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create your .env
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 2. Frontend

Requires Node.js (install from https://nodejs.org if needed — LTS version).

```bash
cd frontend
npm install

# Create your .env
cp .env.example .env
# Set VITE_GOOGLE_PLACES_API_KEY (see below)
# VITE_API_URL defaults to http://localhost:8000

npm run dev
# Runs on http://localhost:5173
```

### 3. Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → APIs & Services → Enable **Places API**
3. Create an API key → add HTTP referrer restriction (`localhost:5173/*` for dev)
4. Add to `frontend/.env` as `VITE_GOOGLE_PLACES_API_KEY=your_key`

The app works without this key — it falls back to a manual entry form.

### 4. Seed the database with existing transcripts

```bash
cd backend
source venv/bin/activate
python seed.py /path/to/your/transcripts/
# Accepts .txt and .pdf files
```

---

## Deployment

### Backend → Railway

1. Create a Railway project, point it at the `backend/` directory
2. Set environment variable: `ANTHROPIC_API_KEY`
3. Railway auto-detects the `Procfile` and deploys

### Frontend → Vercel

1. Connect repo to Vercel, set root directory to `frontend/`
2. Set environment variables:
   - `VITE_API_URL` = your Railway backend URL
   - `VITE_GOOGLE_PLACES_API_KEY` = your Google Places key (update HTTP referrer to your Vercel domain)

---

## Architecture

```
backend/
  main.py                    # FastAPI app, 4 routes
  database.py                # SQLite (briefs + scorecards tables)
  seed.py                    # Batch-score existing transcripts
  modules/
    scraper.py               # DuckDuckGo-based restaurant intelligence
    brief_generator.py       # Claude API → pre-call brief JSON
    transcript_scorer.py     # Claude API → 5-dimension scorecard JSON

frontend/src/
  App.tsx                    # State machine: search → brief → postcall → scorecard
  components/
    RestaurantSearch.tsx     # Google Places autocomplete + manual entry fallback
    BriefCard.tsx            # Pre-call brief display
    PostCallEvaluation.tsx   # Transcript paste / file upload
    ScorecardView.tsx        # 5-dimension scorecard + coaching note
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/brief` | Generate pre-call brief `{restaurant_name, city, website_url?}` |
| POST | `/api/score` | Score transcript (form: `transcript_text` or `file`, `restaurant_name`) |
| GET | `/api/briefs` | Recent briefs from database |
| GET | `/api/scorecards` | Recent scorecards from database |
