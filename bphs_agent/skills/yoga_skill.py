"""
YogaSkill — detects and assesses all yogas present in the chart per BPHS Ch. 35–40.
Uses hardcoded yoga trigger conditions. Strength and cancellations are evaluated.
"""

from __future__ import annotations

from bphs_agent.chart.models import ChartData
from bphs_agent.knowledge.bphs_rules.houses import (
    KENDRA_HOUSES, TRIKONA_HOUSES, DUSTHANA_HOUSES, SIGN_LORD, SIGNS,
)
from bphs_agent.knowledge.bphs_rules.planets import (
    EXALTATION, OWN_SIGNS, NATURAL_NATURE,
)
from bphs_agent.knowledge.bphs_rules.yogas import YOGAS
from bphs_agent.skills.base_skill import CITATION_INSTRUCTION, BaseSkill


def _detect_yogas(chart: ChartData) -> list[dict]:
    """
    Structural yoga detection using hardcoded BPHS rules.
    Returns list of {yoga, present: bool, reason: str} dicts.
    """
    g = chart.general
    lagna_sign = g.lagna_sign if g else ""
    planets = chart.planets
    houses = chart.houses

    if not lagna_sign or lagna_sign not in SIGNS:
        return []

    lagna_idx = SIGNS.index(lagna_sign)

    def house_of(sign: str) -> int:
        if sign not in SIGNS:
            return 0
        return (SIGNS.index(sign) - lagna_idx) % 12 + 1

    def planet_house(pname: str) -> int:
        pd = planets.get(pname)
        return pd.house if pd else 0

    def planet_sign(pname: str) -> str:
        pd = planets.get(pname)
        return pd.sign if pd else ""

    def lords_of_houses(*hnums: int) -> list[str]:
        lords = []
        for h in hnums:
            hd = houses.get(h)
            if hd:
                lords.append(hd.lord)
        return lords

    def in_same_house(*pnames: str) -> bool:
        hs = [planet_house(p) for p in pnames if p]
        return len(set(hs)) == 1 and hs[0] != 0

    def mutual_aspect(p1: str, p2: str) -> bool:
        h1, h2 = planet_house(p1), planet_house(p2)
        return h1 != 0 and h2 != 0 and abs(h1 - h2) == 6  # 7th aspect (opposition)

    def sign_exchange(p1: str, p2: str) -> bool:
        s1, s2 = planet_sign(p1), planet_sign(p2)
        return s1 in OWN_SIGNS.get(p2, []) and s2 in OWN_SIGNS.get(p1, [])

    detected = []

    # ── Raja Yoga (Kendra + Trikona lord association) ─────────────────────
    kendra_lords = set(lords_of_houses(*KENDRA_HOUSES))
    trikona_lords = set(lords_of_houses(*TRIKONA_HOUSES))
    kendra_lords.discard("")
    trikona_lords.discard("")
    raja_found = False
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:  # same planet rules both
                detected.append({
                    "yoga": "Raja Yoga (Kendra-Trikona)",
                    "bphs_ref": "BPHS Ch. 36",
                    "present": True,
                    "reason": f"{kl} rules both a kendra and a trikona.",
                })
                raja_found = True
            elif in_same_house(kl, tl) or sign_exchange(kl, tl) or mutual_aspect(kl, tl):
                detected.append({
                    "yoga": "Raja Yoga (Kendra-Trikona)",
                    "bphs_ref": "BPHS Ch. 36",
                    "present": True,
                    "reason": f"{kl} (kendra lord) associated with {tl} (trikona lord).",
                })
                raja_found = True

    # ── Dharma-Karmadhipati Yoga ──────────────────────────────────────────
    l9 = lords_of_houses(9)
    l10 = lords_of_houses(10)
    for a in l9:
        for b in l10:
            if a and b and (in_same_house(a, b) or sign_exchange(a, b) or mutual_aspect(a, b)):
                detected.append({
                    "yoga": "Dharma-Karmadhipati Yoga",
                    "bphs_ref": "BPHS Ch. 36",
                    "present": True,
                    "reason": f"9th lord {a} and 10th lord {b} are associated.",
                })

    # ── Pancha Mahapurusha Yoga ───────────────────────────────────────────
    pmpy_planets = {
        "Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
        "Venus": "Malavya", "Saturn": "Sasa",
    }
    for p, yoga_name in pmpy_planets.items():
        pd = planets.get(p)
        if pd and pd.house in KENDRA_HOUSES:
            if pd.dignity in ("exalted", "own", "mooltrikona"):
                detected.append({
                    "yoga": f"Pancha Mahapurusha — {yoga_name}",
                    "bphs_ref": "BPHS Ch. 39",
                    "present": True,
                    "reason": f"{p} in {pd.dignity} in kendra (house {pd.house}).",
                })

    # ── Gajakesari Yoga ───────────────────────────────────────────────────
    jup = planet_house("Jupiter")
    moon = planet_house("Moon")
    if jup and moon:
        diff = (jup - moon) % 12
        if diff in (0, 3, 6, 9):  # kendra from Moon
            detected.append({
                "yoga": "Gajakesari Yoga",
                "bphs_ref": "BPHS Ch. 36",
                "present": True,
                "reason": f"Jupiter in house {jup} is in kendra from Moon (house {moon}).",
            })

    # ── Kemadruma Yoga ────────────────────────────────────────────────────
    moon_h = planet_house("Moon")
    if moon_h:
        h2_from_moon = (moon_h % 12) + 1
        h12_from_moon = (moon_h - 2) % 12 + 1
        planets_near_moon = [
            p for p, pd in planets.items()
            if p not in ("Sun", "Rahu", "Ketu", "Moon")
            and pd.house in (h2_from_moon, h12_from_moon)
        ]
        if not planets_near_moon:
            detected.append({
                "yoga": "Kemadruma Yoga",
                "bphs_ref": "BPHS Ch. 38",
                "present": True,
                "reason": f"No planet (except Sun/nodes) in 2nd or 12th from Moon (house {moon_h}).",
            })

    # ── Viparita Raja Yoga ────────────────────────────────────────────────
    dusthana_lords = set(lords_of_houses(*DUSTHANA_HOUSES))
    dusthana_lords.discard("")
    all_in_dusthana = all(planet_house(p) in DUSTHANA_HOUSES for p in dusthana_lords)
    if len(dusthana_lords) >= 2 and all_in_dusthana:
        detected.append({
            "yoga": "Viparita Raja Yoga",
            "bphs_ref": "BPHS Ch. 36",
            "present": True,
            "reason": f"Dusthana lords {dusthana_lords} all placed in dusthana houses.",
        })

    # ── Kuja Dosha ────────────────────────────────────────────────────────
    mars_h = planet_house("Mars")
    if mars_h in (1, 2, 4, 7, 8, 12):
        detected.append({
            "yoga": "Kuja Dosha (Mangal Dosha)",
            "bphs_ref": "BPHS Ch. 38",
            "present": True,
            "reason": f"Mars in house {mars_h} from lagna.",
        })

    # ── Neecha Bhanga check ───────────────────────────────────────────────
    for name, pd in planets.items():
        if pd.dignity == "debilitated":
            deb_sign = pd.sign
            deb_lord = SIGN_LORD.get(deb_sign, "")
            lord_pd = planets.get(deb_lord)
            if lord_pd and lord_pd.house in KENDRA_HOUSES:
                detected.append({
                    "yoga": "Neecha Bhanga Raja Yoga",
                    "bphs_ref": "BPHS Ch. 36",
                    "present": True,
                    "reason": (
                        f"{name} debilitated in {deb_sign}; "
                        f"its dispositor {deb_lord} is in kendra (house {lord_pd.house}). "
                        f"Neecha Bhanga applies."
                    ),
                })

    return detected


class YogaSkill(BaseSkill):
    SKILL_NAME = "Yoga Analysis"
    RELEVANT_TOPIC_KEYS = ["raja_yoga_conditions", "dhana_yoga_conditions", "arista_yoga_conditions"]
    RELEVANT_QUERIES = [
        "Raja Yoga conditions cancellation strength BPHS",
        "Dhana Yoga wealth combinations BPHS",
        "Arista Yoga affliction cancellation BPHS",
    ]

    def _system_prompt(self, passages_block: str) -> str:
        return f"""You are a Jyotishi identifying and assessing yogas (planetary combinations) per BPHS Ch. 35–40.

{CITATION_INSTRUCTION}

For each detected yoga:
1. Confirm or reject it based on the chart data.
2. State the BPHS chapter and sloka that defines this yoga.
3. Assess its strength: is the yoga lord strong (exalted, own sign) or weak (debilitated, combust)?
4. Check for yoga cancellations (e.g. Kemadruma cancelled if Moon in kendra).
5. State when the yoga is most likely to manifest (which dasha/antardasha).

For yogas NOT detected, do not mention them.
For all yogas detected, be precise about what BPHS says — do not embellish.

{passages_block}
"""

    def _build_user_message(self, chart: ChartData, query: str | None) -> str:
        detected = _detect_yogas(chart)
        g = chart.general
        lagna_sign = g.lagna_sign if g else ""

        lines = [f"LAGNA: {lagna_sign}", "", "DETECTED YOGAS (from structural analysis):"]
        if detected:
            for item in detected:
                lines.append(f"\n• {item['yoga']} ({item['bphs_ref']})")
                lines.append(f"  Reason: {item['reason']}")
        else:
            lines.append("  No major yogas detected from structural rules.")

        lines.append("\nFULL PLANET POSITIONS:")
        for name, pd in chart.planets.items():
            lines.append(f"  {name}: {pd.sign} H{pd.house} ({pd.dignity})")

        if query:
            lines.append(f"\nUser question: {query}")
        lines.append("\nAssess each yoga per BPHS. Cite every statement. Evaluate strength and cancellations.")
        return "\n".join(lines)
