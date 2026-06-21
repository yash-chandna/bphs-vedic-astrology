"""
HouseSkill — analyses each bhava (house): lord, occupants, karaka, aspects.
BPHS Ch. 11–15.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData
from bphs_agent.knowledge.bphs_rules.houses import (
    HOUSE_KARAKA,
    HOUSE_SIGNIFICATIONS,
    KARAKA_BHAVA_NASHAYA_NOTE,
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    DUSTHANA_HOUSES,
)
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


class HouseSkill(BaseSkill):
    SKILL_NAME = "Bhava (House) Analysis"
    RELEVANT_TOPIC_KEYS = ["bhava_lord_results", "house_occupant_effects"]
    RELEVANT_QUERIES = [
        "lord of house placed in house results BPHS bhava",
        "planet occupying house bhava phala BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi analysing each of the 12 bhavas (houses) per BPHS Ch. 11–15.

{CITATION_INSTRUCTION}

For each house analyse:
1. The house lord — where it is placed and what BPHS says about that lord's placement.
2. Planets occupying the house and their effects on the house significations.
3. The natural karaka of the house and whether Karaka Bhava Nashaya applies.
4. Planets aspecting the house — benefic aspects strengthen, malefic aspects afflict.
5. Whether the house is strong or weak overall.

{KARAKA_BHAVA_NASHAYA_NOTE}

Focus on houses directly relevant to the query (if given). Otherwise cover all 12.

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        lagna_sign = chart.general.lagna_sign if chart.general else ""

        lines = [f"LAGNA: {lagna_sign}", "", "HOUSES:"]
        for h_num in range(1, 13):
            hd = chart.houses.get(h_num)
            if not hd:
                continue
            lord_planet = chart.planets.get(hd.lord)
            lord_house = lord_planet.house if lord_planet else "?"
            lord_dignity = lord_planet.dignity if lord_planet else "?"
            lord_sign = lord_planet.sign if lord_planet else "?"

            karaka = HOUSE_KARAKA.get(h_num, "")
            karaka_planet = chart.planets.get(karaka)
            karaka_in_own_house = karaka_planet and karaka_planet.house == h_num

            house_type = (
                "Kendra" if h_num in KENDRA_HOUSES else
                "Trikona" if h_num in TRIKONA_HOUSES else
                "Dusthana" if h_num in DUSTHANA_HOUSES else "Neutral"
            )
            sigs = ", ".join(HOUSE_SIGNIFICATIONS.get(h_num, [])[:4])

            lines += [
                f"\nHouse {h_num} ({house_type}) — Sign: {hd.sign}",
                f"  Significations: {sigs}",
                f"  Lord: {hd.lord} → in {lord_sign} (house {lord_house}), dignity: {lord_dignity}",
                f"  Occupants: {', '.join(hd.occupants) or 'none'}",
                f"  Aspects received from: {', '.join(hd.aspecting_planets) or 'none'}",
                f"  Natural karaka: {karaka}" + (" ⚠ KARAKA IN OWN BHAVA" if karaka_in_own_house else ""),
            ]

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nAnalyse bhavas per BPHS. Cite every statement.")
        return "\n".join(lines)
