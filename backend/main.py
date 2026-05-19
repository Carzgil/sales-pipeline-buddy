import hashlib
import io
import os
from contextlib import asynccontextmanager
from typing import Optional

import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import get_recent_briefs, get_recent_scorecards, init_db, save_brief, save_scorecard
from modules.brief_generator import generate_brief
from modules.scraper import search_restaurant_intelligence, validate_restaurant
from modules.transcript_scorer import score_transcript

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Sales Call Buddy API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BriefRequest(BaseModel):
    restaurant_name: str
    city: str
    website_url: Optional[str] = None


@app.post("/api/brief")
async def generate_pre_call_brief(request: BriefRequest):
    is_restaurant, reason = await validate_restaurant(request.restaurant_name, request.city)
    if not is_restaurant:
        raise HTTPException(status_code=422, detail=reason)

    try:
        intelligence = await search_restaurant_intelligence(
            name=request.restaurant_name,
            city=request.city,
            website_url=request.website_url,
        )
        brief = await generate_brief(
            restaurant_name=request.restaurant_name,
            city=request.city,
            intelligence_data=intelligence,
        )
        await save_brief(
            restaurant_name=request.restaurant_name,
            city=request.city,
            brief_json=brief,
            fit_signal=brief.get("fit_signal", "yellow"),
        )
        return {"status": "success", "brief": brief, "intelligence": intelligence}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/score")
async def score_call(
    transcript_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    restaurant_name: Optional[str] = Form(None),
):
    transcript = None

    if transcript_text and transcript_text.strip():
        transcript = transcript_text.strip()
    elif file:
        content = await file.read()
        if file.filename and file.filename.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                transcript = "\n".join(page.extract_text() or "" for page in pdf.pages)
        else:
            transcript = content.decode("utf-8", errors="ignore")

    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript provided")

    try:
        scorecard = await score_transcript(transcript)
        transcript_hash = hashlib.sha256(transcript.encode()).hexdigest()
        await save_scorecard(
            restaurant_name=restaurant_name or "Unknown",
            transcript_hash=transcript_hash,
            scorecard_json=scorecard,
            coaching_note=scorecard.get("coaching_note", ""),
        )
        return {"status": "success", "scorecard": scorecard}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/briefs")
async def list_briefs():
    return await get_recent_briefs()


@app.get("/api/scorecards")
async def list_scorecards():
    return await get_recent_scorecards()


@app.get("/health")
async def health():
    return {"status": "ok"}
