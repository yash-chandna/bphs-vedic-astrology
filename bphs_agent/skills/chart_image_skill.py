"""
ChartImageSkill — wraps image_reader.py to extract chart data from a North Indian
diamond chart image, then validates the extracted data.
"""

from __future__ import annotations

from pathlib import Path

from bphs_agent.chart.image_reader import read_chart_image
from bphs_agent.chart.models import BirthData, ChartData
from bphs_agent.skills.base_skill import SkillResult, Finding

EXPECTED_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}


class ChartImageSkill:
    """
    Not a sub-agent skill in the traditional sense — it does not call Claude for
    interpretation. It uses Claude Vision to extract chart positions, validates the
    result, and returns a ChartData for downstream skills.
    """

    SKILL_NAME = "Chart Image Reader"

    def run_image(self, image_path: str | Path, birth: BirthData | None = None) -> tuple[ChartData, SkillResult]:
        """
        Extract chart data from image and return (ChartData, SkillResult with findings/warnings).
        """
        chart = read_chart_image(image_path, birth)
        findings: list[Finding] = []
        unverified: list[str] = []

        # Validate extraction
        found_planets = set(chart.planets.keys())
        missing = EXPECTED_PLANETS - found_planets
        if missing:
            unverified.append(f"Could not identify: {', '.join(sorted(missing))}. Chart may be unclear.")

        lagna_sign = chart.general.lagna_sign if chart.general else ""
        if not lagna_sign:
            # Try to infer from house 1
            h1 = chart.houses.get(1)
            lagna_sign = h1.sign if h1 else ""

        if lagna_sign:
            findings.append(Finding(
                statement=f"Lagna (Ascendant) identified as {lagna_sign}.",
                bphs_citation="Chart image extraction",
                is_verified=True,
            ))

        for name, pd in chart.planets.items():
            findings.append(Finding(
                statement=f"{name} in {pd.sign} (house {pd.house}).",
                bphs_citation="Chart image extraction",
                is_verified=True,
            ))

        result = SkillResult(
            skill_name=self.SKILL_NAME,
            findings=findings,
            unverified=unverified,
        )
        return chart, result
