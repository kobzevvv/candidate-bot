"""FastAPI entrypoint — POST /join, GET /health."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.bot import run_candidate_bot
from src.config import Settings
from src.persona import CandidatePersona

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="candidate-bot")
settings = Settings()

PERSONAS_DIR = Path(__file__).parent.parent / "personas"


class JoinRequest(BaseModel):
    room_url: str
    candidate_name: str = "Alex"
    resume_text: str = ""
    job_slug: str = "software-engineer"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/join")
async def join(req: JoinRequest):
    if not req.room_url:
        raise HTTPException(status_code=400, detail="room_url is required")

    resume = req.resume_text or _load_persona_file(req.job_slug)

    persona = CandidatePersona(
        name=req.candidate_name,
        job_title=_slug_to_title(req.job_slug),
        resume_text=resume,
    )

    asyncio.create_task(_run(req.room_url, persona))
    return {"status": "joining", "room_url": req.room_url, "candidate": req.candidate_name}


async def _run(room_url: str, persona: CandidatePersona) -> None:
    try:
        await run_candidate_bot(room_url, persona, settings)
    except Exception:
        logger.exception("Candidate bot error for room %s", room_url)


def _load_persona_file(job_slug: str) -> str:
    """Try to load resume text from personas/<job_slug>.md."""
    path = PERSONAS_DIR / f"{job_slug}.md"
    if path.exists():
        return path.read_text()
    # Fallback: try positive-junior persona
    fallback = PERSONAS_DIR / "positive-junior.md"
    if fallback.exists():
        return fallback.read_text()
    return ""


def _slug_to_title(slug: str) -> str:
    return slug.replace("-", " ").title()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=False)
