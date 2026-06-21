"""
DashaSkill — Vimshottari dasha interpretation per BPHS Ch. 46–50.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData, DashaData
from bphs_agent.knowledge.bphs_rules.dasha import (
    DASHA_GENERAL_PRINCIPLES,
    DASHA_LAGNA_NOTE,
    MAHADASHA_YEARS,
)
from bphs_agent.knowledge.bphs_rules.planets import (
    PERMANENT_FRIENDS,
    PERMANENT_ENEMIES,
    KARAKATVA,
)
from bphs_agent.knowledge.bphs_rules.houses import MARAKA_HOUSES
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


class DashaSkill(BaseSkill):
    SKILL_NAME = "Vimshottari Dasha Analysis"
    RELEVANT_TOPIC_KEYS = ["mahadasha_results", "bhukti_antara_results"]
    RELEVANT_QUERIES = [
        "Vimshottari Mahadasha results planet BPHS",
        "Bhukti Antardasha sub-period planet results BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi interpreting Vimshottari Dasha periods per BPHS Ch. 46–50.

{CITATION_INSTRUCTION}

Dasha interpretation methodology per BPHS:
1. The Mahadasha lord's natal position (sign, house, dignity) determines the primary results.
2. The Bhukti (sub-period) lord's relationship to the Mahadasha lord (friend/enemy/neutral)
   modifies the results — friends give harmonious results, enemies bring conflict.
3. The houses owned by each dasha lord and the houses they occupy are activated.
4. Natural significations (karakatva) of the dasha lord are triggered in that period.
5. Maraka dashas (lords of 2nd or 7th): if the native is in the appropriate age window,
   health issues or life-threatening events may occur per BPHS Ch. 44–45.
6. Dasha Lagna: {DASHA_LAGNA_NOTE}

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        dasha = chart.dasha

        lines = [f"LAGNA: {chart.general.lagna_sign if chart.general else 'Unknown'}", ""]

        if dasha:
            maha = dasha.mahadasha
            bhu = dasha.bhukti
            ant = dasha.antaram

            maha_pd = chart.planets.get(maha)
            bhu_pd = chart.planets.get(bhu)

            maha_relationship = (
                "friends" if bhu in PERMANENT_FRIENDS.get(maha, []) else
                "enemies" if bhu in PERMANENT_ENEMIES.get(maha, []) else
                "neutral"
            )

            # Is maha lord a maraka?
            maha_is_maraka = bool(maha_pd and any(h in MARAKA_HOUSES for h in maha_pd.house_lord_of))

            lines += [
                "CURRENT DASHA PERIODS:",
                f"  Mahadasha: {maha} (ends {dasha.mahadasha_end})",
                f"    Position: {maha_pd.sign} H{maha_pd.house} ({maha_pd.dignity})" if maha_pd else f"    Position: unknown",
                f"    Rules houses: {maha_pd.house_lord_of}" if maha_pd else "",
                f"    Karakatva: {', '.join(KARAKATVA.get(maha, [])[:3])}",
                f"    Maraka lord: {'YES' if maha_is_maraka else 'no'}",
                f"",
                f"  Bhukti: {bhu} (ends {dasha.bhukti_end})",
                f"    Position: {bhu_pd.sign} H{bhu_pd.house} ({bhu_pd.dignity})" if bhu_pd else f"    Position: unknown",
                f"    Relationship to Mahadasha lord: {maha_relationship}",
            ]
            if ant:
                ant_pd = chart.planets.get(ant)
                lines += [
                    f"",
                    f"  Antaram: {ant} (ends {dasha.antaram_end})",
                    f"    Position: {ant_pd.sign} H{ant_pd.house} ({ant_pd.dignity})" if ant_pd else f"    Position: unknown",
                ]

            # Upcoming periods from raw dasha tree
            if dasha.raw and len(dasha.raw) > 1:
                lines.append("\nUPCOMING MAHADASHA PERIODS:")
                for item in dasha.raw[1:4]:  # next 3 main periods
                    lines.append(f"  {item.get('Lord', '?')} Mahadasha — starts {item.get('StartTime', '?')} ends {item.get('EndTime', '?')}")
        else:
            lines.append("Dasha data not available.")

        lines.append(f"\nGENERAL PRINCIPLES:\n{chr(10).join(f'  {v}' for v in DASHA_GENERAL_PRINCIPLES.values())}")

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nInterpret per BPHS Ch. 46–50. Cite every statement.")
        return "\n".join(lines)
