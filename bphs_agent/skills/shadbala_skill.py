"""
ShabdalaSkill — interprets planetary strength from VedAstro's Shadbala data.
Hardcoded Shadbala components per BPHS Ch. 27–28.

Note: we ask VedAstro for raw Shadbala values and interpret them ourselves
using BPHS minimum-strength thresholds. We do NOT use VedAstro's own
interpretations.
"""

from __future__ import annotations

import httpx

from bphs_agent import config
from bphs_agent.chart.models import BirthData, ChartData
from bphs_agent.knowledge.bphs_rules.shadbala import (
    DIG_BALA_HOUSE,
    MINIMUM_SHADBALA,
    NAISARGIKA_BALA_RUPAS,
    ISHTA_KASHTA_NOTE,
    house_to_kendra_type,
    KENDRA_BALA,
)
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


def _fetch_shadbala_mcp(birth: BirthData) -> str | None:
    """Try to fetch Shadbala via VedAstro MCP (richer, plain-text result)."""
    try:
        from bphs_agent.chart.vedastro_mcp import get_context_data
        return get_context_data(birth, "Give me the complete Shadbala strength in Rupas for all 9 planets")
    except Exception:
        return None


def _fetch_shadbala(birth: BirthData) -> dict | None:
    """Try to fetch Shadbala data from VedAstro REST API."""
    body = {
        "PlanetName": "All",
        "Time": {
            "StdTime": birth.vedastro_std_time(),
            "Location": {
                "Name": birth.place,
                "Longitude": birth.longitude,
                "Latitude": birth.latitude,
            },
        },
        "Ayanamsa": birth.ayanamsa,
    }
    headers = {"Content-Type": "application/json"}
    if config.VEDASTRO_API_KEY:
        headers["x-api-key"] = config.VEDASTRO_API_KEY
    try:
        resp = httpx.post(
            "https://api.vedastro.org/api/Calculate/PlanetShadbalaPinda",
            headers=headers,
            json=body,
            timeout=20,
        )
        data = resp.json()
        if data.get("Status") == "Pass":
            return data["Payload"]
    except Exception:
        pass
    return None


class ShabdalaSkill(BaseSkill):
    SKILL_NAME = "Shadbala (Planetary Strength)"
    RELEVANT_TOPIC_KEYS = ["shadbala_minimum_strength", "dig_bala_directional"]
    RELEVANT_QUERIES = [
        "Shadbala minimum required strength planet BPHS",
        "Dig Bala directional strength planet house BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi assessing planetary strength via Shadbala per BPHS Ch. 27–28.

{CITATION_INSTRUCTION}

Your scope:
1. For each planet with Shadbala data provided, state whether it meets the BPHS
   minimum required strength (Rupas) and what this means for its dasha results.
2. Comment on Dig Bala (directional strength) — planets strongest in specific houses.
3. Comment on Naisargika Bala (natural hierarchy: Sun strongest … Saturn weakest).
4. Compute Ishta/Kashta Phala implications where data is available.
5. Rank planets from strongest to weakest — this ranking informs the planet-by-planet
   interpretation order in the full reading.

Ishta/Kashta note: {ISHTA_KASHTA_NOTE}

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        # Attempt to get Shadbala from VedAstro
        shadbala_raw = _fetch_shadbala(chart.birth)
        shadbala_mcp_text = None
        if not shadbala_raw:
            shadbala_mcp_text = _fetch_shadbala_mcp(chart.birth)

        lines = ["SHADBALA DATA:"]
        if shadbala_mcp_text:
            lines.append("(Via VedAstro MCP — raw Shadbala output):")
            lines.append(shadbala_mcp_text)
            lines.append("")
        elif shadbala_raw:
            lines.append("(Values in Rupas from VedAstro)")
            for planet, value in shadbala_raw.items():
                minimum = MINIMUM_SHADBALA.get(planet)
                naisargika = NAISARGIKA_BALA_RUPAS.get(planet)
                pd = chart.planets.get(planet)
                dig_best = DIG_BALA_HOUSE.get(planet)
                dig_note = ""
                if pd and dig_best:
                    if pd.house == dig_best:
                        dig_note = f"✓ Full Dig Bala (in house {dig_best})"
                    else:
                        dig_note = f"In house {pd.house}; best Dig Bala at house {dig_best}"
                lines.append(
                    f"  {planet}: {value} Rupas"
                    + (f" | minimum {minimum}" if minimum else "")
                    + (f" | Naisargika {naisargika}" if naisargika else "")
                    + (f" | {dig_note}" if dig_note else "")
                )
        else:
            lines.append("Shadbala API data unavailable. Use chart position proxies:")
            for name, pd in chart.planets.items():
                kendra_type = house_to_kendra_type(pd.house)
                kendra_bala = KENDRA_BALA[kendra_type]
                naisargika = NAISARGIKA_BALA_RUPAS.get(name, "N/A")
                dig_best = DIG_BALA_HOUSE.get(name)
                dig_note = "Full Dig Bala" if pd.house == dig_best else f"Dig Bala best at house {dig_best}"
                lines.append(
                    f"  {name}: dignity={pd.dignity}, kendra_bala={kendra_bala},"
                    f" naisargika={naisargika}, {dig_note}"
                )

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nInterpret planetary strengths per BPHS Ch. 27–28. Cite every statement.")
        return "\n".join(lines)
