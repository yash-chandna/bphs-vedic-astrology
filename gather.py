"""
BPHS Chart Data Gatherer
------------------------
Run this to produce structured chart data + BPHS rules for Claude Code to interpret.

Usage:
    python gather.py "31/01/2000" "19:35" "Gurgaon" 28.4595 77.0266 "+05:30"
    python gather.py "31/01/2000" "19:35" "Gurgaon" 28.4595 77.0266 "+05:30" --transits
    python gather.py "31/01/2000" "19:35" "Gurgaon" 28.4595 77.0266 "+05:30" --question "career prospects"
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

# Force UTF-8 on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from bphs_agent.chart.models import BirthData
from bphs_agent.chart.ephemeris import get_chart, get_current_positions
from bphs_agent.chart.client import get_dasha
from bphs_agent.knowledge.retriever import get_learned, get_or_fetch
from bphs_agent.knowledge.bphs_rules.planets import (
    NATURAL_NATURE, KARAKATVA, SPECIAL_ASPECTS, ALL_PLANETS_ASPECT,
    EXALTATION, OWN_SIGNS, PERMANENT_FRIENDS, PERMANENT_ENEMIES,
)
from bphs_agent.knowledge.bphs_rules.houses import (
    HOUSE_SIGNIFICATIONS, HOUSE_KARAKA,
    KENDRA_HOUSES as KENDRA, TRIKONA_HOUSES as TRIKONA, DUSTHANA_HOUSES as DUSTHANA,
    UPACHAYA_HOUSES as UPACHAYA, MARAKA_HOUSES as MARAKA,
    KARAKA_BHAVA_NASHAYA_NOTE, get_functional_nature,
)
from bphs_agent.knowledge.bphs_rules.yogas import get_yogas_by_type
from bphs_agent.knowledge.bphs_rules.shadbala import (
    DIG_BALA_HOUSE, NAISARGIKA_BALA_RUPAS, MINIMUM_SHADBALA,
    KENDRA_BALA, house_to_kendra_type,
)
from bphs_agent.knowledge.bphs_rules.dasha import (
    DASHA_GENERAL_PRINCIPLES, MAHADASHA_YEARS, DASHA_LAGNA_NOTE,
)
from bphs_agent.knowledge.bphs_rules.divisionals import (
    DIVISIONAL_CHARTS, NAVAMSA_RULES, VARGA_VISESHA,
)
from bphs_agent.knowledge.bphs_rules.transits import (
    GOCHAR_FROM_MOON, VEDHA_PAIRS, SADE_SATI_NOTE, ASHTAMA_SHANI_NOTE,
    JUPITER_TRANSIT_NOTE, TRANSIT_DURATION_DAYS,
)
from bphs_agent import config as cfg


def sep(title: str) -> str:
    return f"\n{'='*60}\n{title.upper()}\n{'='*60}"


def detect_yogas(chart) -> list[dict]:
    """Structural yoga detection from chart positions."""
    from bphs_agent.knowledge.bphs_rules.houses import SIGNS
    planets = chart.planets
    houses  = chart.houses
    lagna   = chart.general.lagna_sign

    detected = []

    def sign_of_house(h: int) -> str:
        return houses[h].sign if h in houses else ""

    def house_of_planet(p: str) -> int:
        return planets[p].house if p in planets else 0

    def sign_of_planet(p: str) -> str:
        return planets[p].sign if p in planets else ""

    def lord_of_house(h: int) -> str:
        return houses[h].lord if h in houses else ""

    # ── Raja Yoga: kendra + trikona lords conjunct/mutual aspect ─────────────
    kendra_lords = {lord_of_house(h) for h in KENDRA if lord_of_house(h)}
    trikona_lords = {lord_of_house(h) for h in TRIKONA if lord_of_house(h)}
    raja = kendra_lords & trikona_lords  # same planet lords both
    for p in raja:
        if p:
            detected.append({
                "name": "Raja Yoga",
                "condition": f"{p} lords both a kendra and trikona",
                "planets": [p],
                "bphs_ch": "BPHS Ch. 35-36",
            })
    # Conjunction of kendra + trikona lords
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl and tl and kl != tl and house_of_planet(kl) == house_of_planet(tl):
                detected.append({
                    "name": "Raja Yoga",
                    "condition": f"{kl} (kendra lord) conjunct {tl} (trikona lord) in H{house_of_planet(kl)}",
                    "planets": [kl, tl],
                    "bphs_ch": "BPHS Ch. 35",
                })

    # ── Gajakesari: Jupiter in kendra from Moon ───────────────────────────────
    moon_house = house_of_planet("Moon")
    jup_house  = house_of_planet("Jupiter")
    if moon_house and jup_house:
        diff = (jup_house - moon_house) % 12
        if diff in (0, 3, 6, 9):
            detected.append({
                "name": "Gajakesari Yoga",
                "condition": f"Jupiter in H{jup_house} ({diff or 12} houses from Moon in H{moon_house})",
                "planets": ["Jupiter", "Moon"],
                "bphs_ch": "BPHS Ch. 37, Sl. 1",
            })

    # ── Pancha Mahapurusha ────────────────────────────────────────────────────
    PMY = {
        "Mars":    ("Ruchaka",  ["Aries", "Scorpio", "Capricorn"]),
        "Mercury": ("Bhadra",   ["Gemini", "Virgo"]),
        "Jupiter": ("Hamsa",    ["Sagittarius", "Pisces", "Cancer"]),
        "Venus":   ("Malavya",  ["Taurus", "Libra", "Pisces"]),
        "Saturn":  ("Sasa",     ["Capricorn", "Aquarius", "Libra"]),
    }
    for planet, (yoga_name, signs) in PMY.items():
        if planet in planets:
            pd = planets[planet]
            if pd.sign in signs and pd.house in KENDRA:
                detected.append({
                    "name": f"Pancha Mahapurusha — {yoga_name}",
                    "condition": f"{planet} in {pd.sign} (own/exalted) in kendra H{pd.house}",
                    "planets": [planet],
                    "bphs_ch": "BPHS Ch. 35, Sl. 40-60",
                })

    # ── Kemadruma Yoga ────────────────────────────────────────────────────────
    moon_sign_idx = list(HOUSE_SIGNIFICATIONS.keys()).index(sign_of_planet("Moon")) if sign_of_planet("Moon") in HOUSE_SIGNIFICATIONS else -1
    if moon_house:
        neighbors = {(moon_house % 12) + 1, ((moon_house - 2) % 12) + 1}
        planets_near_moon = {p for p, pd in planets.items() if pd.house in neighbors and p not in ("Sun", "Rahu", "Ketu")}
        if not planets_near_moon:
            detected.append({
                "name": "Kemadruma Yoga",
                "condition": "No planet in 2nd or 12th from Moon",
                "planets": ["Moon"],
                "bphs_ch": "BPHS Ch. 36, Sl. 13",
            })

    # ── Viparita Raja Yoga: dusthana lords in dusthanas ──────────────────────
    dusthana_lords = {lord_of_house(h) for h in DUSTHANA if lord_of_house(h)}
    for p in dusthana_lords:
        if p and house_of_planet(p) in DUSTHANA:
            detected.append({
                "name": "Viparita Raja Yoga",
                "condition": f"{p} (dusthana lord) placed in dusthana H{house_of_planet(p)}",
                "planets": [p],
                "bphs_ch": "BPHS Ch. 36, Sl. 24-27",
            })

    # ── Neecha Bhanga Raja Yoga ───────────────────────────────────────────────
    DEB_SIGN = {
        "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
        "Mercury": "Pisces", "Jupiter": "Capricorn",
        "Venus": "Virgo", "Saturn": "Aries",
    }
    for planet, deb_sign in DEB_SIGN.items():
        if planet not in planets:
            continue
        if planets[planet].sign != deb_sign:
            continue
        # Check: lord of deb sign in kendra from lagna or Moon
        deb_lord = lord_of_house(list(HOUSE_SIGNIFICATIONS.keys()).index(deb_sign) + 1) if deb_sign in list(HOUSE_SIGNIFICATIONS.keys()) else ""
        if deb_lord and house_of_planet(deb_lord) in KENDRA:
            detected.append({
                "name": "Neecha Bhanga Raja Yoga",
                "condition": f"{planet} debilitated in {deb_sign}; dispositor {deb_lord} in kendra H{house_of_planet(deb_lord)}",
                "planets": [planet, deb_lord],
                "bphs_ch": "BPHS Ch. 36, Sl. 28-32",
            })

    # ── Kuja Dosha ────────────────────────────────────────────────────────────
    mars_house = house_of_planet("Mars")
    if mars_house in (1, 2, 4, 7, 8, 12):
        detected.append({
            "name": "Kuja Dosha (Mangal Dosha)",
            "condition": f"Mars in H{mars_house}",
            "planets": ["Mars"],
            "bphs_ch": "BPHS Ch. 73",
        })

    # ── Parivartana (sign exchange) ───────────────────────────────────────────
    for p1, pd1 in planets.items():
        for p2, pd2 in planets.items():
            if p1 >= p2:
                continue
            if pd1.sign in OWN_SIGNS.get(p2, []) and pd2.sign in OWN_SIGNS.get(p1, []):
                detected.append({
                    "name": "Parivartana Yoga",
                    "condition": f"{p1} in {pd1.sign} (owned by {p2}) and {p2} in {pd2.sign} (owned by {p1})",
                    "planets": [p1, p2],
                    "bphs_ch": "BPHS Ch. 36, Sl. 7-12",
                })

    return detected


def shadbala_proxy(chart) -> list[str]:
    """Proxy Shadbala assessment from chart position (no API call)."""
    lines = []
    for name, pd in chart.planets.items():
        kendra_type = house_to_kendra_type(pd.house)
        kendra_bala = KENDRA_BALA[kendra_type]
        naisargika  = NAISARGIKA_BALA_RUPAS.get(name, "N/A")
        minimum     = MINIMUM_SHADBALA.get(name, "N/A")
        dig_best    = DIG_BALA_HOUSE.get(name)
        dig_note    = f"Full Dig Bala (H{pd.house})" if pd.house == dig_best else f"Dig Bala best at H{dig_best}"
        dignity_note = pd.dignity.upper()
        lines.append(
            f"  {name}: dignity={dignity_note}, kendra_bala={kendra_bala} Rupas, "
            f"naisargika={naisargika}, minimum_required={minimum}, {dig_note}"
            + (" [RETROGRADE]" if pd.retrograde else "")
            + (" [COMBUST]" if pd.combust else "")
        )
    return lines


def bphs_rules_block(topics: list[str]) -> str:
    """Pull relevant BPHS passages from learned.py for a list of topic keys."""
    passages_all = []
    for key in topics:
        passages = get_learned(key)
        if passages:
            for p in passages[:3]:  # max 3 per topic to stay focused
                text = p.get("text", "") if isinstance(p, dict) else str(p)
                ref  = p.get("chapter", "") if isinstance(p, dict) else ""
                if text:
                    passages_all.append(f"[{ref}] {text}" if ref else text)
    return "\n".join(passages_all) if passages_all else "(No cached BPHS passages — run build_kb.py first)"


def gather(birth: BirthData, include_transits: bool = False, question: str = "") -> str:
    out = []

    # ── Chart ─────────────────────────────────────────────────────────────────
    chart = get_chart(birth)
    moon  = chart.planets.get("Moon")
    dasha = get_dasha(
        birth,
        moon_nak=moon.nakshatra if moon else "",
        moon_sign=moon.sign if moon else "",
        moon_degree=moon.longitude if moon else 0.0,
    )

    out.append(sep("BIRTH DETAILS"))
    out.append(f"Name : {birth.name}")
    out.append(f"Date : {birth.date}  Time: {birth.time}  TZ: {birth.timezone}")
    out.append(f"Place: {birth.place} ({birth.latitude}°N, {birth.longitude}°E)")
    out.append(f"Ayanamsa: {birth.ayanamsa} ({chart.general.ayanamsa_degree}°)")
    out.append(f"Source: Swiss Ephemeris (pyswisseph)")

    out.append(sep("CHART OVERVIEW"))
    out.append(f"Lagna (Ascendant): {chart.general.lagna_sign} ({chart.general.lagna_degree}°)")
    out.append(f"Moon Sign        : {chart.general.moon_sign}  Nakshatra: {chart.general.moon_nakshatra}")
    out.append(f"Sun Sign         : {chart.general.sun_sign}")

    out.append(sep("PLANETARY POSITIONS"))
    out.append(f"{'Planet':<10} {'Sign':<14} {'Deg':>6} {'H':>2}  {'Dignity':<12} {'Nak':<22} {'Pd'} Flags")
    out.append("-" * 80)
    for name, pd in chart.planets.items():
        flags = []
        if pd.retrograde: flags.append("R")
        if pd.combust:    flags.append("C")
        flag_str = " ".join(flags)
        out.append(
            f"{name:<10} {pd.sign:<14} {pd.degree:>6.2f} {pd.house:>2}  {pd.dignity:<12} "
            f"{pd.nakshatra:<22} {pd.nakshatra_pada}  {flag_str}"
        )
        if pd.house_lord_of:
            out.append(f"           Lords houses: {pd.house_lord_of}")

    out.append(sep("HOUSE MAP (WHOLE SIGN)"))
    for num in range(1, 13):
        h = chart.houses.get(num)
        if not h:
            continue
        nature = ("kendra" if num in KENDRA else "trikona" if num in TRIKONA else
                  "dusthana" if num in DUSTHANA else "upachaya" if num in UPACHAYA else
                  "maraka" if num in MARAKA else "neutral")
        sigs   = ", ".join(HOUSE_SIGNIFICATIONS.get(num, [])[:4])
        karaka = HOUSE_KARAKA.get(num, "")
        out.append(
            f"H{num:02d} {h.sign:<14} Lord: {h.lord:<10} "
            f"[{nature}] Occ: {h.occupants or '—'}  Karaka: {karaka}"
        )
        if sigs:
            out.append(f"     Signifies: {sigs}")

    out.append(sep("VIMSHOTTARI DASHA  [BPHS Ch. 46]"))
    out.append(f"Mahadasha : {dasha.mahadasha} (ends {dasha.mahadasha_end}) — {MAHADASHA_YEARS.get(dasha.mahadasha,'')} year period")
    out.append(f"Bhukti    : {dasha.bhukti} (ends {dasha.bhukti_end})")
    out.append(f"Antaram   : {dasha.antaram} (ends {dasha.antaram_end})")
    out.append("\nFull Mahadasha sequence from birth:")
    for p in dasha.raw:
        out.append(f"  {p['Lord']:<10} {p['StartTime']}  →  {p['EndTime']}")
    out.append(f"\n{DASHA_LAGNA_NOTE}")
    out.append("\nGeneral Dasha Principles:")
    for key, principle in list(DASHA_GENERAL_PRINCIPLES.items())[:5]:
        out.append(f"  • {key}: {principle}")

    out.append(sep("SHADBALA (STRENGTH PROXY)  [BPHS Ch. 27-28]"))
    out.append("(Full Shadbala requires complex calculation; below are proxy indicators)")
    for line in shadbala_proxy(chart):
        out.append(line)
    out.append("\nNaisargika Bala hierarchy (Sun strongest → Saturn weakest per BPHS):")
    for p, r in NAISARGIKA_BALA_RUPAS.items():
        out.append(f"  {p}: {r} Rupas  (minimum required: {MINIMUM_SHADBALA.get(p, 'N/A')})")

    out.append(sep("DETECTED YOGAS  [BPHS Ch. 35-40]"))
    yogas = detect_yogas(chart)
    if yogas:
        for y in yogas:
            out.append(f"\n► {y['name']}  ({y['bphs_ch']})")
            out.append(f"  Condition: {y['condition']}")
    else:
        out.append("No major yogas structurally detected from positions alone.")
    out.append("\nNote: Assess each yoga for (1) strength of planets involved, (2) cancellation conditions, (3) dasha activation.")

    out.append(sep("KARAKATVA (NATURAL SIGNIFICATORS)  [BPHS Ch. 32]"))
    for planet, karakas in KARAKATVA.items():
        out.append(f"  {planet:<10}: {', '.join(karakas[:5])}")

    out.append(sep("KARAKA BHAVA NASHAYA WARNING  [BPHS Ch. 32]"))
    out.append(KARAKA_BHAVA_NASHAYA_NOTE)

    out.append(sep("NAVAMSHA D9 KEY RULES  [BPHS Ch. 6-7]"))
    for rule_name, rule_text in NAVAMSA_RULES.items():
        out.append(f"  {rule_name}: {rule_text}")

    if include_transits:
        out.append(sep("CURRENT TRANSITS (GOCHAR)  [BPHS Ch. 51-58]"))
        try:
            current = get_current_positions(birth.ayanamsa)
            moon_sign = chart.general.moon_sign
            from bphs_agent.knowledge.bphs_rules.houses import SIGNS
            out.append(f"Moon sign in natal chart: {moon_sign} (transits counted FROM this)")
            out.append(f"\n{'Planet':<10} {'Transit Sign':<14} {'H from Moon':>11}  Result  BPHS Ref  Vedha?")
            out.append("-" * 70)
            for planet, t_sign in current.items():
                if moon_sign in SIGNS and t_sign in SIGNS:
                    moon_idx = SIGNS.index(moon_sign)
                    t_idx    = SIGNS.index(t_sign)
                    h_from_moon = (t_idx - moon_idx) % 12 + 1
                    gochar = GOCHAR_FROM_MOON.get(planet, {}).get(h_from_moon, {})
                    result = gochar.get("result", "")
                    effect = gochar.get("effect", "")
                    bref   = gochar.get("bphs_ref", "")
                    # Vedha check
                    vedha_pairs = VEDHA_PAIRS.get(planet, [])
                    vedha_active = False
                    for good_h, bad_h in vedha_pairs:
                        if h_from_moon == good_h:
                            for op, op_sign in current.items():
                                if op != planet and op in SIGNS:
                                    op_idx = SIGNS.index(op_sign)
                                    op_h   = (op_idx - moon_idx) % 12 + 1
                                    if op_h == bad_h:
                                        vedha_active = True
                    out.append(
                        f"{planet:<10} {t_sign:<14} H{h_from_moon:>2} from Moon  "
                        f"{result:<7} {bref:<12} {'VEDHA' if vedha_active else ''}"
                    )
                    if effect:
                        out.append(f"           Effect: {effect}")
            out.append(f"\n{SADE_SATI_NOTE}")
            out.append(f"\n{ASHTAMA_SHANI_NOTE}")
            out.append(f"\n{JUPITER_TRANSIT_NOTE}")
        except Exception as e:
            out.append(f"(Transit calculation error: {e})")

    out.append(sep("BPHS KNOWLEDGE BASE PASSAGES"))
    core_topics = [
        "lagna_lord_effects", "planet_house_effects", "bhava_lord_results",
        "raja_yoga_conditions", "mahadasha_results", "gochar_phala_moon",
        "shadbala_minimum_strength", "navamsha_interpretation",
    ]
    if question:
        out.append(f"Question context: {question}")
        # Add question-specific topics
        q = question.lower()
        if any(w in q for w in ["career", "profession", "job", "work"]):
            core_topics += ["tenth_house_career", "dasamsha_career"]
        if any(w in q for w in ["marriage", "spouse", "partner", "relationship"]):
            core_topics += ["seventh_house_marriage", "navamsha_marriage"]
        if any(w in q for w in ["child", "children", "progeny"]):
            core_topics += ["fifth_house_children", "saptamsha_children"]
        if any(w in q for w in ["wealth", "money", "finance"]):
            core_topics += ["second_house_wealth", "dhana_yoga_conditions"]
        if any(w in q for w in ["health", "disease", "illness"]):
            core_topics += ["eighth_house_longevity", "arista_yoga_conditions"]
        if any(w in q for w in ["dasha", "period", "timing"]):
            core_topics += ["bhukti_antara_results", "dasha_lord_placement"]
        if any(w in q for w in ["transit", "gochar", "saturn", "sade sati"]):
            core_topics += ["sade_sati_effects", "transit_vedha", "saturn_transit_gochar"]
    out.append(bphs_rules_block(list(dict.fromkeys(core_topics))))  # deduplicate

    out.append(sep("INSTRUCTIONS FOR CLAUDE CODE"))
    out.append("""Using the chart data above, provide a BPHS-based reading following this sequence:

1. SHADBALA ASSESSMENT: Which planets are strongest/weakest? (Use dignity, house type, Dig Bala)
2. LAGNA ANALYSIS: Rising sign nature, lagna lord placement, overall chart tone
3. PLANET-BY-PLANET: Each planet's sign, house, dignity, aspects, what it means for the native
4. HOUSE ANALYSIS: Key houses (1,4,5,7,9,10) — lords, occupants, afflictions
5. YOGA ASSESSMENT: Rate strength of detected yogas, check cancellation conditions
6. NAVAMSHA (D9): Vargottama planets, lagna lord in D9, spouse significators
7. DASHA READING: What the current Venus-Saturn-Sun period means based on planet placements
8. SYNTHESIS: Integrate everything into a coherent reading

STRICT RULES:
- Every interpretive statement MUST begin with [BPHS Ch.X, Sl.Y] or cite a passage above
- If BPHS does not address something, say so explicitly — do NOT speculate
- Do NOT confirm what the native hopes to hear — only what the chart shows
- Flag [UNVERIFIED] for anything not traceable to the passages provided""")

    if question:
        out.append(f"\nSPECIFIC QUESTION TO ANSWER: {question}")

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Gather BPHS chart data for Claude Code")
    parser.add_argument("date",      help="Birth date DD/MM/YYYY")
    parser.add_argument("time",      help="Birth time HH:MM (24h)")
    parser.add_argument("place",     help="Birth place name")
    parser.add_argument("latitude",  type=float, help="Latitude (N positive)")
    parser.add_argument("longitude", type=float, help="Longitude (E positive)")
    parser.add_argument("timezone",  help="Timezone offset e.g. +05:30")
    parser.add_argument("--name",    default="Native", help="Name")
    parser.add_argument("--ayanamsa", default="LAHIRI", help="Ayanamsa (default LAHIRI)")
    parser.add_argument("--transits", action="store_true", help="Include current transit analysis")
    parser.add_argument("--question", default="", help="Specific question for focused reading")
    args = parser.parse_args()

    birth = BirthData(
        name=args.name,
        date=args.date,
        time=args.time,
        place=args.place,
        latitude=args.latitude,
        longitude=args.longitude,
        timezone=args.timezone,
        ayanamsa=args.ayanamsa,
    )
    print(gather(birth, include_transits=args.transits, question=args.question))


if __name__ == "__main__":
    import sys
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
