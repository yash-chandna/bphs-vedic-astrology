"""
Orchestrator — runs skills in BPHS-prescribed sequence and assembles results.

Sequence per BPHS methodology:
  1. ShabdalaSkill  → planet strength ranking
  2. LagnaSkill     → foundation
  3. PlanetSkill    → planet-by-planet
  4. HouseSkill     → bhava analysis
  5. YogaSkill      → yoga identification
  6. DivisionalSkill→ Navamsha + others
  7. AshtakvargaSkill
  8. DashaSkill     → current period
  9. AstrocartographySkill (if location provided)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from bphs_agent.chart.models import ChartData
from bphs_agent.skills.base_skill import SkillResult
from bphs_agent.skills.lagna_skill import LagnaSkill
from bphs_agent.skills.planet_skill import PlanetSkill
from bphs_agent.skills.house_skill import HouseSkill
from bphs_agent.skills.shadbala_skill import ShabdalaSkill
from bphs_agent.skills.yoga_skill import YogaSkill
from bphs_agent.skills.divisional_skill import DivisionalSkill
from bphs_agent.skills.ashtakvarga_skill import AshtakvargaSkill
from bphs_agent.skills.dasha_skill import DashaSkill
from bphs_agent.skills.astrocartography_skill import AstrocartographySkill
from bphs_agent.skills.transit_skill import TransitSkill
from bphs_agent.skills.rectification_skill import RectificationSkill


@dataclass
class OrchestratorResult:
    skill_results: list[SkillResult] = field(default_factory=list)
    # All verified findings across all skills
    all_findings: list[str] = field(default_factory=list)
    # Unverified statements (excluded from reading)
    all_unverified: list[str] = field(default_factory=list)

    def cited_block(self) -> str:
        """All verified findings as a single block for the synthesis pass."""
        return "\n\n".join(r.cited_summary() for r in self.skill_results)


def run_full_reading(
    chart: ChartData,
    query: str | None = None,
    target_location: tuple[str, float, float] | None = None,
    divisions: list[str] | None = None,
    include_transits: bool = False,
    transit_months: int = 6,
    on_skill_done: Callable[[str, SkillResult], None] | None = None,
) -> OrchestratorResult:
    """
    Run the complete BPHS reading sequence.

    Args:
        chart: Populated ChartData (from VedAstro or image reader).
        query: Optional user question to thread through all skills.
        target_location: (place_name, lat, lon) for astrocartography.
        divisions: Divisional charts to analyse (default: ["D9"]).
        on_skill_done: Optional callback called after each skill completes.
                       Signature: (skill_name, result) → None.
                       Useful for streaming progress to the CLI.
    """
    result = OrchestratorResult()

    def _run(skill, *args, **kwargs) -> SkillResult:
        sr = skill.run(*args, **kwargs)
        result.skill_results.append(sr)
        result.all_findings.extend(f.statement for f in sr.findings)
        result.all_unverified.extend(sr.unverified)
        if on_skill_done:
            on_skill_done(sr.skill_name, sr)
        return sr

    # 1. Shadbala — must run first to establish planet strength ordering
    _run(ShabdalaSkill(), chart, query)

    # 2. Lagna
    _run(LagnaSkill(), chart, query)

    # 3. Planets
    _run(PlanetSkill(), chart, query)

    # 4. Houses
    _run(HouseSkill(), chart, query)

    # 5. Yogas
    _run(YogaSkill(), chart, query)

    # 6. Divisional charts
    div_skill = DivisionalSkill(divisions=divisions or ["D9"])
    _run(div_skill, chart, query)

    # 7. Ashtakvarga
    _run(AshtakvargaSkill(), chart, query)

    # 8. Dasha
    _run(DashaSkill(), chart, query)

    # 9. Transits / Gochar (optional)
    if include_transits:
        _run(TransitSkill(months_ahead=transit_months), chart, query)

    # 10. Astrocartography (optional)
    if target_location:
        place, lat, lon = target_location
        astro_skill = AstrocartographySkill()
        sr = astro_skill.run_for_location(chart, place, lat, lon)
        result.skill_results.append(sr)
        result.all_findings.extend(f.statement for f in sr.findings)
        result.all_unverified.extend(sr.unverified)
        if on_skill_done:
            on_skill_done(sr.skill_name, sr)

    return result


def run_targeted(
    chart: ChartData,
    query: str,
    skill_names: list[str] | None = None,
) -> OrchestratorResult:
    """
    Run only the skills relevant to a specific question.
    skill_names: list of skill class names to run (e.g. ["DashaSkill", "YogaSkill"]).
    If None, infers relevant skills from the query keywords.
    """
    result = OrchestratorResult()

    skill_map = {
        "LagnaSkill": LagnaSkill,
        "PlanetSkill": PlanetSkill,
        "HouseSkill": HouseSkill,
        "ShabdalaSkill": ShabdalaSkill,
        "YogaSkill": YogaSkill,
        "DivisionalSkill": DivisionalSkill,
        "AshtakvargaSkill": AshtakvargaSkill,
        "DashaSkill": DashaSkill,
        "TransitSkill": TransitSkill,
        "RectificationSkill": RectificationSkill,
    }

    if not skill_names:
        skill_names = _infer_skills(query)

    for name in skill_names:
        cls = skill_map.get(name)
        if not cls:
            continue
        sr = cls().run(chart, query)
        result.skill_results.append(sr)
        result.all_findings.extend(f.statement for f in sr.findings)
        result.all_unverified.extend(sr.unverified)

    return result


def _infer_skills(query: str) -> list[str]:
    """Simple keyword-based skill selector for targeted queries."""
    q = query.lower()
    skills = []

    if any(w in q for w in ["dasha", "period", "mahadasha", "bhukti", "antaram", "timing", "when"]):
        skills.append("DashaSkill")
    if any(w in q for w in ["yoga", "combination", "raj yoga", "dhana", "arista"]):
        skills.append("YogaSkill")
    if any(w in q for w in ["lagna", "ascendant", "rising sign", "lagna lord"]):
        skills.append("LagnaSkill")
    if any(w in q for w in ["house", "bhava", "bhava phala"]):
        skills.append("HouseSkill")
    if any(w in q for w in ["planet", "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]):
        skills.append("PlanetSkill")
    if any(w in q for w in ["navamsha", "d9", "divisional", "d10", "dasamsha", "spouse", "career chart"]):
        skills.append("DivisionalSkill")
    if any(w in q for w in ["strength", "shadbala", "strong", "weak", "bala"]):
        skills.append("ShabdalaSkill")
    if any(w in q for w in ["ashtakvarga", "bindu"]):
        skills.append("AshtakvargaSkill")
    if any(w in q for w in ["transit", "gochar", "transiting", "current position", "upcoming", "future", "sade sati", "ashtama shani"]):
        skills.append("TransitSkill")
    if any(w in q for w in ["rectif", "birth time", "time of birth", "janma kala", "correct time", "verify time", "lagna correct", "ascendant correct"]):
        skills.append("RectificationSkill")

    # Default: run lagna + planet + house if nothing matched
    if not skills:
        skills = ["LagnaSkill", "PlanetSkill", "HouseSkill"]

    return skills
