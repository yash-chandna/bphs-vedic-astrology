"""
PlanetSkill — analyses each planet individually: sign, house, dignity, aspects.
BPHS Ch. 3–5, 16–25.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData, PlanetData
from bphs_agent.knowledge.bphs_rules.planets import (
    ALL_PLANETS_ASPECT,
    KARAKATVA,
    NATURAL_NATURE,
    PERMANENT_FRIENDS,
    PERMANENT_ENEMIES,
)
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill, SkillResult, _parse_response


class PlanetSkill(BaseSkill):
    SKILL_NAME = "Planetary Analysis"
    RELEVANT_TOPIC_KEYS = ["planet_house_effects", "planet_sign_effects"]
    RELEVANT_QUERIES = [
        "planet in house results effects BPHS",
        "planet in sign results dignity BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi analysing INDIVIDUAL planets in a birth chart per BPHS.

{CITATION_INSTRUCTION}

For each planet analyse:
1. Its sign placement and what BPHS says about it.
2. Its house placement and BPHS results for that planet in that house.
3. Its dignity (exalted/own/moolatrikona/enemy/debilitated) and implications.
4. Whether it is retrograde or combust and what BPHS says about this.
5. Which planets aspect it and whether those aspects are benefic or malefic.
6. Its natural karakatva (significations) and how its placement affects those.

Analyse planets in order of Shadbala strength (strongest first, as provided).
Do NOT diagnose yogas here — that is the Yoga Skill's job.

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        lagna_sign = chart.general.lagna_sign if chart.general else ""

        # Sort planets by a rough strength proxy (exalted > own > neutral > debilitated)
        dignity_order = {"exalted": 0, "mooltrikona": 1, "own": 2, "neutral": 3, "enemy": 4, "debilitated": 5}

        def sort_key(item):
            _, pd = item
            return dignity_order.get(pd.dignity, 3)

        sorted_planets = sorted(chart.planets.items(), key=sort_key)

        lines = [f"LAGNA: {lagna_sign}", "", "PLANETS:"]
        for name, pd in sorted_planets:
            aspected_by = [
                p for p, apd in chart.planets.items()
                if p != name and pd.house in [
                    (apd.house + h - 1) % 12 + 1 for h in ALL_PLANETS_ASPECT.get(p, [7])
                ]
            ]
            lines += [
                f"\n{name}:",
                f"  Sign: {pd.sign} | House: {pd.house} | Dignity: {pd.dignity}",
                f"  Degree: {pd.degree:.1f}° | Nakshatra: {pd.nakshatra} pada {pd.nakshatra_pada}",
                f"  Retrograde: {pd.retrograde} | Combust: {pd.combust}",
                f"  Rules houses: {pd.house_lord_of}",
                f"  Aspected by: {aspected_by or 'none detected'}",
                f"  Natural karakatva: {', '.join(KARAKATVA.get(name, [])[:3])}",
            ]

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nAnalyse each planet per BPHS. Cite every statement.")
        return "\n".join(lines)
