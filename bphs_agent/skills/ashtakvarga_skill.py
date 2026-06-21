"""
AshtakvargaSkill — bindu analysis and transit strength.
BPHS Ch. 66–69.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData
from bphs_agent.knowledge.bphs_rules.houses import SIGNS
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill

# BPHS thresholds for Sarvashtakavarga bindus per sign
# A sign with 28+ bindus is strong; below 25 is weak
SAV_STRONG = 28
SAV_WEAK = 25


class AshtakvargaSkill(BaseSkill):
    SKILL_NAME = "Ashtakvarga Analysis"
    RELEVANT_TOPIC_KEYS = ["ashtakvarga_bindus", "sarvashtakavarga_transit"]
    RELEVANT_QUERIES = [
        "Ashtakvarga bindu points house transit strength BPHS",
        "Sarvashtakavarga total points weak strong house BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi analysing Ashtakvarga per BPHS Ch. 66–69.

{CITATION_INSTRUCTION}

Key rules per BPHS:
1. Sarvashtakavarga (SAV) — total bindus for each sign across all planets.
   28+ bindus: strong house, transits there bring good results.
   25–27: average.
   Below 25: weak house, transits there give difficulty.
2. Bhinnashtakavarga — each planet's individual bindu score per sign.
   A planet transiting a sign where it has 4+ own bindus gives good results.
   Below 4: transit gives poor results.
3. Prashtara Ashtakvarga — detailed grid used to identify favourable transit windows.
4. Ashtakvarga is primarily a TRANSIT tool, but also reflects natal chart strength.

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        av = chart.ashtakvarga
        lagna_sign = chart.general.lagna_sign if chart.general else ""
        lagna_idx = SIGNS.index(lagna_sign) if lagna_sign in SIGNS else 0

        lines = [f"LAGNA: {lagna_sign}", "", "ASHTAKVARGA DATA:"]

        if av and av.sarva:
            lines.append("\nSarvashtakavarga (total bindus per sign):")
            for i, bindus in enumerate(av.sarva):
                sign = SIGNS[(lagna_idx + i) % 12]
                house = i + 1
                strength = "STRONG" if bindus >= SAV_STRONG else ("WEAK" if bindus < SAV_WEAK else "average")
                lines.append(f"  H{house} ({sign}): {bindus} bindus — {strength}")

            if av.bhinnas:
                lines.append("\nBhinnashtakavarga (planet-wise bindus in own sign):")
                for planet, bindu_list in av.bhinnas.items():
                    if not bindu_list:
                        continue
                    pd = chart.planets.get(planet)
                    if pd and pd.sign in SIGNS:
                        sign_idx = SIGNS.index(pd.sign)
                        own_bindus = bindu_list[sign_idx] if sign_idx < len(bindu_list) else "?"
                        lines.append(f"  {planet} in {pd.sign}: {own_bindus} own bindus")
        else:
            lines.append("  Ashtakvarga data not available from VedAstro for this chart.")
            lines.append("  Provide general Ashtakvarga principles relevant to this lagna and query.")

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nInterpret per BPHS Ch. 66–69. Cite every statement.")
        return "\n".join(lines)
