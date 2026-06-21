"""
AstrocartographySkill — relocated chart analysis.
Applies BPHS angular planet rules to the relocated chart for a target location.
"""

from __future__ import annotations

from bphs_agent.chart.client import get_full_chart
from bphs_agent.chart.models import BirthData, ChartData
from bphs_agent.knowledge.bphs_rules.houses import KENDRA_HOUSES, SIGN_LORD, SIGNS
from bphs_agent.knowledge.bphs_rules.planets import KARAKATVA, NATURAL_NATURE
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


class AstrocartographySkill(BaseSkill):
    SKILL_NAME = "Astrocartography (Relocated Chart)"
    RELEVANT_TOPIC_KEYS = ["relocated_lagna_effects", "planet_on_angle_relocated"]
    RELEVANT_QUERIES = [
        "relocated lagna planet angular house effects BPHS",
        "planet on ascendant midheaven IC descendant relocated chart",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi analysing a relocated birth chart per BPHS principles.

{CITATION_INSTRUCTION}

Astrocartography in Vedic context:
- When a native moves to a new location, the lagna and house cusps shift.
- Planets that were in non-angular houses in the birth location may move to
  angular houses (1, 4, 7, 10) in the new location — these become highly activated.
- The new lagna lord becomes the primary planet for that location.
- The atmakaraka (planet at highest degree in D1) retains importance everywhere.
- BPHS angular house rules (kendra effects) apply to the relocated chart.

Apply BPHS chapter references for:
- Planet in each kendra house (Ch. 11–15)
- Lagna lord effects (Ch. 6–8)
- Natural malefics in angles causing Papakartari in the relocated chart

{passages_block}
"""

    def run_for_location(
        self,
        natal_chart: ChartData,
        target_place: str,
        target_lat: float,
        target_lon: float,
    ) -> "SkillResult":
        """Compute relocated chart and run analysis."""
        from bphs_agent.skills.base_skill import SkillResult

        relocated_birth = BirthData(
            name=natal_chart.birth.name,
            date=natal_chart.birth.date,
            time=natal_chart.birth.time,
            place=target_place,
            latitude=target_lat,
            longitude=target_lon,
            timezone=natal_chart.birth.timezone,  # user must adjust if needed
            ayanamsa=natal_chart.birth.ayanamsa,
        )

        try:
            relocated_chart = get_full_chart(relocated_birth)
        except Exception as e:
            return SkillResult(
                skill_name=self.SKILL_NAME,
                unverified=[f"Could not compute relocated chart: {e}"],
            )

        # Attach relocated chart to instance for _build_user_message
        self._natal = natal_chart
        self._relocated = relocated_chart
        self._target_place = target_place
        return self.run(natal_chart)

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        natal = getattr(self, "_natal", chart)
        relocated = getattr(self, "_relocated", None)
        target = getattr(self, "_target_place", "target location")

        natal_lagna = natal.general.lagna_sign if natal.general else "Unknown"
        rel_lagna = relocated.general.lagna_sign if relocated and relocated.general else "Unknown"

        lines = [
            f"NATAL CHART — Lagna: {natal_lagna} (born in {natal.birth.place})",
            f"RELOCATED CHART — Lagna: {rel_lagna} (relocated to {target})",
            "",
            "PLANETS IN RELOCATED CHART:",
        ]

        if relocated:
            angular_changes = []
            for name, rel_pd in relocated.planets.items():
                natal_pd = natal.planets.get(name)
                natal_h = natal_pd.house if natal_pd else "?"
                rel_h = rel_pd.house
                moved_to_angle = rel_h in KENDRA_HOUSES and (natal_h not in KENDRA_HOUSES if natal_pd else True)
                lines.append(
                    f"  {name}: natal H{natal_h} → relocated H{rel_h} ({rel_pd.sign})"
                    + (" ⬆ MOVED TO ANGLE" if moved_to_angle else "")
                )
                if moved_to_angle:
                    angular_changes.append(f"{name} moved to angle (H{rel_h})")

            if angular_changes:
                lines.append(f"\nKEY ANGULAR SHIFTS: {'; '.join(angular_changes)}")

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append(f"\nAnalyse how {target} affects the native per BPHS angular house rules. Cite every statement.")
        return "\n".join(lines)
