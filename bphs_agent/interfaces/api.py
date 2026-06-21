"""
FastAPI REST interface.

Run:
    uvicorn bphs_agent.interfaces.api:app --reload
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile, shutil
from pathlib import Path

from bphs_agent.chart.client import get_full_chart, get_dasha, get_divisional_chart
from bphs_agent.chart.models import BirthData
from bphs_agent.coordinator.orchestrator import run_full_reading, run_targeted
from bphs_agent.coordinator.synthesis import synthesise
from bphs_agent.skills.chart_image_skill import ChartImageSkill
from bphs_agent.skills.astrocartography_skill import AstrocartographySkill
from bphs_agent.skills.transit_skill import TransitSkill

app = FastAPI(title="BPHS Vedic Astrology Agent", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class BirthInput(BaseModel):
    name: str
    date: str           # DD/MM/YYYY
    time: str           # HH:MM
    place: str
    latitude: float
    longitude: float
    timezone: str       # +HH:MM
    ayanamsa: str = "LAHIRI"


class ReadingRequest(BaseModel):
    birth: BirthInput
    query: Optional[str] = None
    divisions: Optional[list[str]] = None


class QuestionRequest(BaseModel):
    birth: BirthInput
    question: str


class DashaRequest(BaseModel):
    birth: BirthInput
    start: Optional[str] = None   # DD/MM/YYYY
    end: Optional[str] = None


class AstroRequest(BaseModel):
    birth: BirthInput
    location: str
    latitude: float
    longitude: float


def _to_birth(b: BirthInput) -> BirthData:
    return BirthData(**b.model_dump())


@app.post("/reading")
async def full_reading(req: ReadingRequest):
    """Full BPHS reading in BPHS sequence. Returns reading text + skill summaries."""
    birth = _to_birth(req.birth)
    try:
        chart = get_full_chart(birth)
        if req.divisions:
            for div in req.divisions:
                chart.divisionals[div] = get_divisional_chart(birth, div)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VedAstro error: {e}")

    orch = run_full_reading(chart, query=req.query, divisions=req.divisions)
    reading = synthesise(chart, orch, query=req.query)
    return {
        "reading": reading,
        "skill_summaries": [sr.cited_summary() for sr in orch.skill_results],
        "unverified_count": len(orch.all_unverified),
    }


@app.post("/question")
async def targeted_question(req: QuestionRequest):
    """Targeted Q&A — only runs skills relevant to the question."""
    birth = _to_birth(req.birth)
    try:
        chart = get_full_chart(birth)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VedAstro error: {e}")

    orch = run_targeted(chart, req.question)
    reading = synthesise(chart, orch, query=req.question)
    return {
        "answer": reading,
        "skills_used": [sr.skill_name for sr in orch.skill_results],
        "findings_count": sum(len(sr.findings) for sr in orch.skill_results),
    }


@app.post("/dasha")
async def dasha_report(req: DashaRequest):
    """Vimshottari dasha report for a date range."""
    birth = _to_birth(req.birth)
    try:
        chart = get_full_chart(birth)
        chart.dasha = get_dasha(birth, req.start, req.end)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VedAstro error: {e}")

    orch = run_targeted(chart, "dasha timing", skill_names=["DashaSkill"])
    reading = synthesise(chart, orch, query="Dasha period analysis")
    return {"dasha_reading": reading}


@app.post("/chart-image")
async def chart_from_image(
    file: UploadFile = File(...),
    name: str = "Native",
):
    """Upload a North Indian chart image → extract + full reading."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "chart.jpg").suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        skill = ChartImageSkill()
        birth_placeholder = BirthData(name=name, date="01/01/1900", time="00:00",
                                       place="Unknown", latitude=0.0, longitude=0.0, timezone="+00:00")
        chart, image_result = skill.run_image(tmp_path, birth_placeholder)
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Image parsing error: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)

    orch = run_full_reading(chart)
    reading = synthesise(chart, orch)
    return {
        "extracted_planets": {n: {"sign": p.sign, "house": p.house} for n, p in chart.planets.items()},
        "reading": reading,
        "image_warnings": image_result.unverified,
    }


class TransitRequest(BaseModel):
    birth: BirthInput
    months_ahead: int = 6


@app.post("/transits")
async def transit_report(req: TransitRequest):
    """Gochar (transit) analysis for current and upcoming planetary transits per BPHS Ch. 51–58."""
    birth = _to_birth(req.birth)
    try:
        chart = get_full_chart(birth)
        chart.dasha = get_dasha(birth)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VedAstro error: {e}")

    orch = run_targeted(chart, "transit gochar upcoming", skill_names=["TransitSkill"])
    reading = synthesise(chart, orch, query=f"Gochar transit analysis for next {req.months_ahead} months")
    return {"transit_reading": reading}


@app.post("/astrocartography")
async def astrocartography(req: AstroRequest):
    """Relocated chart analysis for a target location."""
    birth = _to_birth(req.birth)
    try:
        chart = get_full_chart(birth)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VedAstro error: {e}")

    astro_skill = AstrocartographySkill()
    sr = astro_skill.run_for_location(chart, req.location, req.latitude, req.longitude)
    from bphs_agent.coordinator.orchestrator import OrchestratorResult
    orch = OrchestratorResult(skill_results=[sr])
    orch.all_findings = [f.statement for f in sr.findings]
    reading = synthesise(chart, orch, query=f"Relocation to {req.location}")
    return {"astrocartography_reading": reading}
