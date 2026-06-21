"""
TransitSkill — Gochar (planetary transit) analysis per BPHS Ch. 51–58.

Fetches current and upcoming planetary positions from VedAstro,
computes house from natal Moon, applies BPHS Gochar Phala rules,
checks Vedha (obstruction), and flags Sade Sati / Ashtama Shani.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TypedDict

import httpx

from bphs_agent import config
from bphs_agent.chart.models import BirthData, ChartData
from bphs_agent.knowledge.bphs_rules.houses import SIGNS
from bphs_agent.knowledge.bphs_rules.transits import (
    ASHTAMA_SHANI_NOTE,
    GOCHAR_FROM_MOON,
    JUPITER_TRANSIT_NOTE,
    SADE_SATI_NOTE,
    TRANSIT_DURATION_DAYS,
    VEDHA_PAIRS,
)
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


class TransitPlanet(TypedDict):
    planet: str
    current_sign: str
    house_from_moon: int
    result: str          # "good" | "bad" | "mixed"
    effect: str
    bphs_ref: str
    vedha_active: bool
    vedha_reason: str


def _get_current_positions() -> dict[str, str]:
    """Return current transit sign for all 9 planets via Swiss Ephemeris (offline, no rate limit)."""
    try:
        from bphs_agent.chart.ephemeris import get_current_positions
        return get_current_positions(config.DEFAULT_AYANAMSA)
    except Exception:
        return {}


def _get_future_positions(months_ahead: int = 12) -> dict[str, list[dict]]:
    """
    Sample planetary positions at monthly intervals for slow-moving planets.
    Uses Swiss Ephemeris — instant, no rate limits.
    """
    from bphs_agent.chart.models import BirthData
    from bphs_agent.chart.ephemeris import get_chart

    slow_planets = ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars"]
    future: dict[str, list[dict]] = {p: [] for p in slow_planets}
    today = datetime.utcnow()

    for months in range(1, months_ahead + 1):
        sample_date = today + timedelta(days=30 * months)
        transit_birth = BirthData(
            name="_transit",
            date=sample_date.strftime("%d/%m/%Y"),
            time="12:00",
            place="Greenwich",
            latitude=51.48,
            longitude=0.0,
            timezone="+00:00",
            ayanamsa=config.DEFAULT_AYANAMSA,
        )
        try:
            chart = get_chart(transit_birth)
            for planet in slow_planets:
                pd = chart.planets.get(planet)
                if pd:
                    future[planet].append({
                        "date": sample_date.strftime("%d/%m/%Y"),
                        "sign": pd.sign,
                    })
        except Exception:
            continue

    return future


def _house_from_moon(transit_sign: str, moon_sign: str) -> int:
    """Compute which house a transiting planet is in, counted from natal Moon sign."""
    if transit_sign not in SIGNS or moon_sign not in SIGNS:
        return 0
    moon_idx = SIGNS.index(moon_sign)
    transit_idx = SIGNS.index(transit_sign)
    return (transit_idx - moon_idx) % 12 + 1


def _check_vedha(planet: str, house_from_moon: int, all_transit_houses: dict[str, int]) -> tuple[bool, str]:
    """Check if a planet's good transit is obstructed (Vedha) by another planet."""
    vedha_map = VEDHA_PAIRS.get(planet, {})
    obstruct_house = vedha_map.get(house_from_moon)
    if obstruct_house is None:
        return False, ""

    # Which planets are NOT excluded from Vedha with this planet
    excluded_pairs = {("Sun", "Saturn"), ("Saturn", "Sun"), ("Moon", "Mercury"), ("Mercury", "Moon")}
    for other_planet, other_house in all_transit_houses.items():
        if other_planet == planet:
            continue
        if (planet, other_planet) in excluded_pairs or (other_planet, planet) in excluded_pairs:
            continue
        if other_house == obstruct_house:
            return True, (
                f"{other_planet} transiting house {obstruct_house} from Moon "
                f"obstructs (Vedha) {planet}'s beneficial transit from house {house_from_moon}."
            )
    return False, ""


def analyse_transits(chart: ChartData, months_ahead: int = 6) -> list[TransitPlanet]:
    """
    Core transit analysis:
    1. Fetch current planetary positions.
    2. Compute house from natal Moon for each planet.
    3. Apply BPHS Gochar Phala rules.
    4. Check Vedha obstructions.
    5. Flag Sade Sati / Ashtama Shani.
    """
    moon_pd = chart.planets.get("Moon")
    moon_sign = moon_pd.sign if moon_pd else ""
    if not moon_sign:
        return []

    current_positions = _get_current_positions()
    if not current_positions:
        return []

    # Compute house from Moon for all transiting planets
    all_transit_houses = {
        p: _house_from_moon(sign, moon_sign)
        for p, sign in current_positions.items()
        if sign
    }

    results: list[TransitPlanet] = []
    for planet, sign in current_positions.items():
        h = all_transit_houses.get(planet, 0)
        if not h:
            continue

        gochar = GOCHAR_FROM_MOON.get(planet, {}).get(h, {})
        result_str = gochar.get("result", "mixed")
        effect = gochar.get("effect", "")
        bphs_ref = gochar.get("bphs_ref", "BPHS Ch. 51–58")

        vedha_active, vedha_reason = _check_vedha(planet, h, all_transit_houses)

        # Vedha cancels a good transit result
        if vedha_active and result_str == "good":
            result_str = "mixed"
            effect += f" However, Vedha (obstruction) is active: {vedha_reason}"

        results.append(TransitPlanet(
            planet=planet,
            current_sign=sign,
            house_from_moon=h,
            result=result_str,
            effect=effect,
            bphs_ref=bphs_ref,
            vedha_active=vedha_active,
            vedha_reason=vedha_reason,
        ))

    return results


class TransitSkill(BaseSkill):
    SKILL_NAME = "Gochar (Transit) Analysis"
    RELEVANT_TOPIC_KEYS = ["gochar_phala_moon", "sade_sati_effects", "transit_vedha"]
    RELEVANT_QUERIES = [
        "Gochar planet transit results from Moon sign BPHS",
        "Sade Sati Saturn transit Moon effects BPHS",
        "Vedha obstruction transit planet BPHS Gochar",
    ]

    def __init__(self, months_ahead: int = 6):
        self.months_ahead = months_ahead

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi interpreting upcoming planetary transits (Gochar) per BPHS Ch. 51–58.

{CITATION_INSTRUCTION}

Transit interpretation methodology per BPHS:
1. Primary reference: house from natal MOON sign (Janma Rashi). This is BPHS's main transit frame.
2. Secondary reference: house from natal lagna (for modifying factors).
3. The transit result given by BPHS is further modified by:
   a. Vedha (obstruction): another planet simultaneously in the obstructing house cancels a good transit.
   b. Ashtakvarga bindus: if the transiting planet has 4+ own bindus in the transit sign → good; below 4 → bad.
   c. The dasha period: transit results manifest most strongly when the transit planet is also the dasha/bhukti lord.
4. Sade Sati: {SADE_SATI_NOTE}
5. Ashtama Shani: {ASHTAMA_SHANI_NOTE}
6. Jupiter transit: {JUPITER_TRANSIT_NOTE}

For each planet, state:
- Current transit sign and house from Moon.
- BPHS result (good/bad/mixed) with citation.
- Whether Vedha is active and its effect.
- Any special flags (Sade Sati, Ashtama Shani).
- When the transit ends (approximate, based on duration).

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        moon_pd = chart.planets.get("Moon")
        moon_sign = moon_pd.sign if moon_pd else "Unknown"
        lagna_sign = chart.general.lagna_sign if chart.general else "Unknown"

        transit_data = analyse_transits(chart, self.months_ahead)

        lines = [
            f"NATAL MOON SIGN (Janma Rashi): {moon_sign}",
            f"NATAL LAGNA: {lagna_sign}",
            f"CURRENT DATE: {datetime.utcnow().strftime('%d/%m/%Y')}",
            "",
            "CURRENT PLANETARY TRANSITS:",
        ]

        # Flags
        saturn_entry = next((t for t in transit_data if t["planet"] == "Saturn"), None)
        if saturn_entry:
            h = saturn_entry["house_from_moon"]
            if h in (12, 1, 2):
                lines.append(f"\n⚠ SADE SATI ACTIVE — Saturn in house {h} from Moon ({moon_sign})")
                lines.append(f"  {SADE_SATI_NOTE}")
            elif h == 8:
                lines.append(f"\n⚠ ASHTAMA SHANI — Saturn in house 8 from Moon ({moon_sign})")
                lines.append(f"  {ASHTAMA_SHANI_NOTE}")

        lines.append("")
        for t in transit_data:
            duration = TRANSIT_DURATION_DAYS.get(t["planet"], "?")
            lines += [
                f"{t['planet']}: {t['current_sign']} → House {t['house_from_moon']} from Moon",
                f"  Result: {t['result'].upper()} ({t['bphs_ref']})",
                f"  Effect: {t['effect']}",
                f"  Approx. transit duration: ~{duration} days" if isinstance(duration, int) else "",
                f"  Vedha: {'YES — ' + t['vedha_reason'] if t['vedha_active'] else 'none'}" if t['vedha_active'] else "",
                "",
            ]

        # Dasha context
        if chart.dasha:
            lines += [
                f"CURRENT DASHA: {chart.dasha.mahadasha} / {chart.dasha.bhukti}",
                f"  Transits of the dasha lord ({chart.dasha.mahadasha}) and bhukti lord ({chart.dasha.bhukti})",
                f"  are most significant for timing events.",
                "",
            ]

        if query:
            lines.append(f"User question: {query}")
        lines.append("\nInterpret these transits per BPHS Ch. 51–58. Cite every statement.")
        return "\n".join(lines)
