"""
Seed the database with scored versions of existing Owner call transcripts.

Usage:
  python seed.py ./path/to/transcripts/

The directory should contain .txt or .pdf transcript files.
Each file will be scored and saved to the SQLite database.
"""

import asyncio
import hashlib
import io
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from database import init_db, save_scorecard
from modules.transcript_scorer import score_transcript


async def seed(directory: str):
    await init_db()

    transcript_dir = Path(directory)
    if not transcript_dir.exists():
        print(f"Directory not found: {directory}")
        sys.exit(1)

    files = sorted(list(transcript_dir.glob("*.txt")) + list(transcript_dir.glob("*.pdf")))
    if not files:
        print("No .txt or .pdf files found")
        sys.exit(1)

    print(f"Found {len(files)} transcript files — scoring now...\n")

    success, skipped, failed = 0, 0, 0

    for i, file_path in enumerate(files):
        print(f"[{i+1}/{len(files)}] {file_path.name}", end=" ... ", flush=True)

        try:
            if file_path.suffix == ".pdf":
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    transcript = "\n".join(p.extract_text() or "" for p in pdf.pages)
            else:
                transcript = file_path.read_text(errors="ignore")

            if not transcript.strip():
                print("SKIP (empty)")
                skipped += 1
                continue

            transcript_hash = hashlib.sha256(transcript.encode()).hexdigest()
            restaurant_name = file_path.stem.replace("_", " ").replace("-", " ").title()

            scorecard = await score_transcript(transcript)
            await save_scorecard(
                restaurant_name=restaurant_name,
                transcript_hash=transcript_hash,
                scorecard_json=scorecard,
                coaching_note=scorecard.get("coaching_note", ""),
            )
            print("OK")
            success += 1

        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print(f"\nDone — {success} scored, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "transcripts"
    asyncio.run(seed(directory))
