"""
LagnaSkill — analyses the ascendant (lagna), lagna lord placement, and rising sign.
BPHS Ch. 6–8.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData
from bphs_agent.knowledge.bphs_rules.houses import HOUSE_SIGNIFICATIONS, SIGN_LORD
from bphs_agent.knowledge.bphs_rules.planets import NATURAL_NATURE, EXALTATION, KARAKATVA
from bphs_agent.skills.base_skill import BaseSkill, CITATION_INSTRUCTION


class LagnaSkill(BaseSkill):
    SKILL_NAME = "Lagna Analysis"
    RELEVANT_TOPIC_KEYS = ["lagna_lord_effects", "rising_sign_characteristics"]
    RELEVANT_QUERIES = [
        "lagna lord placement effects on native",
        "rising sign ascendant body personality BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi analysing ONLY the lagna (ascendant) of a birth chart per BPHS.

{CITATION_INSTRUCTION}

Your scope for this analysis:
1. The rising sign and what BPHS says about natives born with that lagna.
2. The lagna lord — its sign, house, dignity, and what BPHS says about that placement.
3. Any planets conjunct with or aspecting the lagna lord.
4. Whether the lagna is hemmed by malefics or benefics (Papakartari / Shubhakartari).
5. Strength of the lagna lord (retrograde, combust, dignity).

Do NOT analyse yogas, dashas, or other houses beyond what directly relates to lagna.

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        g = chart.general
        lagna_sign = g.lagna_sign if g else ""
        lagna_lord = SIGN_LORD.get(lagna_sign, "")
        ll_data = chart.planets.get(lagna_lord)

        lines = [
            f"LAGNA (Ascendant): {lagna_sign} ({g.lagna_degree:.1f}°)" if g else f"LAGNA: {lagna_sign}",
            f"Lagna Lord: {lagna_lord}",
        ]
        if ll_data:
            lines += [
                f"  Lagna Lord in sign: {ll_data.sign} (house {ll_data.house})",
                f"  Dignity: {ll_data.dignity}",
                f"  Retrograde: {ll_data.retrograde}",
                f"  Combust: {ll_data.combust}",
                f"  Nakshatra: {ll_data.nakshatra}",
            ]

        # Planets in lagna
        lagna_occupants = [p for p, pd in chart.planets.items() if pd.house == 1 and p != lagna_lord]
        if lagna_occupants:
            lines.append(f"Planets in lagna: {', '.join(lagna_occupants)}")

        # Planets in 2nd and 12th from lagna (for Papakartari check)
        in_2nd = [p for p, pd in chart.planets.items() if pd.house == 2]
        in_12th = [p for p, pd in chart.planets.items() if pd.house == 12]
        if in_2nd:
            lines.append(f"Planets in 2nd house: {', '.join(in_2nd)}")
        if in_12th:
            lines.append(f"Planets in 12th house: {', '.join(in_12th)}")

        if query:
            lines.append(f"\nUser question: {query}")

        lines.append("\nAnalyse per BPHS. Cite every statement.")
        return "\n".join(lines)
