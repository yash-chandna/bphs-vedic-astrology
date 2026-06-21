"""
DivisionalSkill — D9 (Navamsha) always; other divisions on demand.
BPHS Ch. 6–7.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData
from bphs_agent.knowledge.bphs_rules.divisionals import (
    DIVISIONAL_CHARTS,
    NAVAMSA_RULES,
    VARGA_VISESHA,
)
from bphs_agent.knowledge.bphs_rules.planets import EXALTATION, OWN_SIGNS
from bphs_agent.knowledge.bphs_rules.houses import SIGNS
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


def _check_vargottama(d1_chart: ChartData, d9_chart: ChartData) -> list[str]:
    vargottama = []
    for name, pd1 in d1_chart.planets.items():
        pd9 = d9_chart.planets.get(name)
        if pd9 and pd1.sign == pd9.sign:
            vargottama.append(name)
    return vargottama


class DivisionalSkill(BaseSkill):
    SKILL_NAME = "Divisional Chart Analysis"
    RELEVANT_TOPIC_KEYS = ["navamsha_interpretation", "varga_strength"]
    RELEVANT_QUERIES = [
        "Navamsha D9 interpretation spouse dharma BPHS",
        "Varga Visesha Shodashavarga planet strength BPHS",
    ]

    def __init__(self, divisions: list[str] | None = None):
        self.divisions = divisions or ["D9"]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi analysing divisional charts per BPHS Ch. 6–7.

{CITATION_INSTRUCTION}

Rules you MUST apply:
1. Never interpret a divisional chart in isolation — always read in context of D1.
2. D9 (Navamsha) is the most important divisional; analyse it first and always.
3. Vargottama planets (same sign in D1 and D9) are significantly strengthened per BPHS Ch. 7.
4. A planet strong in D1 but weak in D9 has its promise diminished.
5. A planet weak in D1 but strong in D9 is better than it appears.
6. Assess Varga Visesha (special dignity from multiple varga positions) where data allows.

Divisional purposes per BPHS:
{chr(10).join(f"  {k}: {v['purpose']}" for k, v in DIVISIONAL_CHARTS.items())}

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        lines = [f"D1 (Rasi) LAGNA: {chart.general.lagna_sign if chart.general else 'Unknown'}", ""]

        for div in self.divisions:
            div_chart = chart.divisionals.get(div)
            info = DIVISIONAL_CHARTS.get(div, {})
            lines.append(f"\n=== {div} — {info.get('name', div)} ===")
            lines.append(f"Purpose: {info.get('purpose', 'See BPHS')}")

            if div_chart and div_chart.planets:
                if div == "D9":
                    vargottama = _check_vargottama(chart, div_chart)
                    if vargottama:
                        lines.append(f"VARGOTTAMA planets (same sign in D1 + D9): {', '.join(vargottama)}")

                for name, pd in div_chart.planets.items():
                    d1_pd = chart.planets.get(name)
                    d1_dignity = d1_pd.dignity if d1_pd else "unknown"
                    lines.append(
                        f"  {name}: {pd.sign} (dignity: {pd.dignity}) | D1 dignity: {d1_dignity}"
                    )
            else:
                lines.append(f"  No {div} data available.")

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nAnalyse per BPHS Ch. 6–7. Cite every statement.")
        return "\n".join(lines)
