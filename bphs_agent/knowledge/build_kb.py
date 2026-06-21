"""
Knowledge base builder — pre-populates learned.py by querying VedAstro's
BPHS SearchSourceText API for all skill topics.

Run this once (or re-run to add new topics) to hardcode BPHS passages:
    python -m bphs_agent.knowledge.build_kb

Free tier: 5 searches/minute → ~15 minutes for 72 topics.
Premium ($1/mo, set VEDASTRO_API_KEY in .env): unlimited → completes in seconds.
Each topic is only fetched once; already-learned topics are skipped.
After running, all skill lookups hit local learned.py instantly — zero API calls.
"""

from __future__ import annotations

import sys
import time

# Force UTF-8 output on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from bphs_agent import config
from bphs_agent.knowledge.retriever import get_or_fetch, get_learned

# All topics used by the 11 skills, keyed by topic_key → query string
TOPICS: list[tuple[str, str]] = [

    # ── LAGNA ────────────────────────────────────────────────────────────────
    ("lagna_lord_effects",          "lagna lord placement effects on native per BPHS"),
    ("rising_sign_characteristics", "rising sign ascendant body personality BPHS characteristics"),
    ("papakartari_yoga",            "Papakartari Yoga malefics hemming lagna or Moon BPHS"),
    ("shubhakartari_yoga",          "Shubhakartari Yoga benefics hemming lagna BPHS"),

    # ── PLANETS ───────────────────────────────────────────────────────────────
    ("planet_house_effects",        "planet placed in house results effects phala BPHS"),
    ("planet_sign_effects",         "planet in sign dignity results BPHS"),
    ("planet_retrograde_effects",   "retrograde planet Vakri effects results BPHS"),
    ("planet_combust_effects",      "combust planet Asta effects results BPHS"),
    ("sun_house_results",           "Sun in each house results BPHS"),
    ("moon_house_results",          "Moon in each house results BPHS"),
    ("mars_house_results",          "Mars in each house results BPHS"),
    ("mercury_house_results",       "Mercury in each house results BPHS"),
    ("jupiter_house_results",       "Jupiter in each house results BPHS"),
    ("venus_house_results",         "Venus in each house results BPHS"),
    ("saturn_house_results",        "Saturn in each house results BPHS"),
    ("rahu_ketu_house_results",     "Rahu Ketu in each house results BPHS"),

    # ── HOUSES ────────────────────────────────────────────────────────────────
    ("bhava_lord_results",          "lord of house placed in house results BPHS bhava phala"),
    ("house_occupant_effects",      "planet occupying house bhava phala effects BPHS"),
    ("karaka_bhava_nashaya",        "Karaka Bhava Nashaya karaka in own house BPHS"),
    ("second_house_wealth",         "second house wealth speech family BPHS"),
    ("fourth_house_mother",         "fourth house mother property happiness BPHS"),
    ("fifth_house_children",        "fifth house children intelligence purva punya BPHS"),
    ("seventh_house_marriage",      "seventh house marriage spouse partner BPHS"),
    ("eighth_house_longevity",      "eighth house longevity death obstacles BPHS"),
    ("ninth_house_dharma",          "ninth house dharma fortune father BPHS"),
    ("tenth_house_career",          "tenth house career profession karma BPHS"),
    ("twelfth_house_moksha",        "twelfth house moksha loss expenses BPHS"),

    # ── SHADBALA ──────────────────────────────────────────────────────────────
    ("shadbala_minimum_strength",   "Shadbala minimum required strength planet BPHS Rupas"),
    ("dig_bala_directional",        "Dig Bala directional strength planet house BPHS"),
    ("ishta_kashta_phala",          "Ishta Phala Kashta Phala planet benefic malefic score BPHS"),
    ("sthana_bala_positional",      "Sthana Bala positional strength exaltation own sign BPHS"),
    ("kala_bala_temporal",          "Kala Bala temporal strength day night planet BPHS"),
    ("cheshta_bala_motional",       "Cheshta Bala motional strength retrograde planet BPHS"),

    # ── YOGAS ────────────────────────────────────────────────────────────────
    ("raja_yoga_conditions",        "Raja Yoga conditions kendra trikona lord BPHS"),
    ("dhana_yoga_conditions",       "Dhana Yoga wealth combination 2nd 11th lord BPHS"),
    ("arista_yoga_conditions",      "Arista Yoga affliction malefic cancellation BPHS"),
    ("pancha_mahapurusha_yoga",     "Pancha Mahapurusha Yoga Ruchaka Bhadra Hamsa Malavya Sasa BPHS"),
    ("gajakesari_yoga",             "Gajakesari Yoga Jupiter kendra Moon BPHS"),
    ("kemadruma_yoga",              "Kemadruma Yoga Moon no planet 2nd 12th cancellation BPHS"),
    ("viparita_raja_yoga",          "Viparita Raja Yoga dusthana lord BPHS"),
    ("neecha_bhanga_raja_yoga",     "Neecha Bhanga Raja Yoga debilitated planet cancelled BPHS"),
    ("parivartana_yoga",            "Parivartana Yoga sign exchange mutual BPHS"),
    ("nabhasa_yoga",                "Nabhasa Yoga all planets movable fixed dual BPHS"),
    ("chandra_yogas",               "Sunapha Anapha Durudhara Yoga Moon BPHS"),
    ("kuja_dosha",                  "Kuja Dosha Mangal Dosha Mars marriage BPHS cancellation"),
    ("yoga_cancellation",           "Yoga cancellation Bhanga conditions BPHS"),
    ("yoga_strength_assessment",    "assessing yoga strength planet dignity BPHS"),

    # ── DIVISIONALS ──────────────────────────────────────────────────────────
    ("navamsha_interpretation",     "Navamsha D9 interpretation spouse dharma soul BPHS"),
    ("varga_strength",              "Varga Visesha Shodashavarga planet strength BPHS"),
    ("vargottama_planet",           "Vargottama planet same sign D1 D9 strength BPHS"),
    ("dasamsha_career",             "Dasamsha D10 career profession BPHS"),
    ("saptamsha_children",          "Saptamsha D7 children progeny BPHS"),
    ("navamsha_marriage",           "Navamsha spouse marriage partner BPHS D9"),

    # ── ASHTAKVARGA ──────────────────────────────────────────────────────────
    ("ashtakvarga_bindus",          "Ashtakvarga bindu points house transit strength BPHS"),
    ("sarvashtakavarga_transit",    "Sarvashtakavarga total points weak strong house transit BPHS"),
    ("prashtara_ashtakvarga",       "Prashtara Ashtakvarga detailed grid favourable transit BPHS"),

    # ── DASHA ────────────────────────────────────────────────────────────────
    ("mahadasha_results",           "Vimshottari Mahadasha results planet BPHS dasha phala"),
    ("bhukti_antara_results",       "Bhukti Antardasha sub-period planet results BPHS"),
    ("dasha_lord_placement",        "dasha lord in house effects period results BPHS"),
    ("maraka_dasha",                "Maraka dasha 2nd 7th lord death inflicting BPHS"),
    ("dasha_lagna",                 "Dasha Lagna temporary ascendant period interpretation BPHS"),
    ("vimshottari_sequence",        "Vimshottari dasha sequence nakshatra Moon BPHS"),

    # ── TRANSITS / GOCHAR ────────────────────────────────────────────────────
    ("gochar_phala_moon",           "Gochar planet transit results from Moon sign BPHS"),
    ("sade_sati_effects",           "Sade Sati Saturn transit 7.5 years Moon BPHS effects"),
    ("transit_vedha",               "Vedha obstruction transit planet good house BPHS Gochar"),
    ("ashtama_shani",               "Ashtama Shani Saturn 8th from Moon BPHS transit"),
    ("jupiter_transit_good_houses", "Jupiter transit good houses from Moon 2 5 7 9 11 BPHS"),
    ("sun_transit_gochar",          "Sun transit Gochar house from Moon results BPHS"),
    ("saturn_transit_gochar",       "Saturn transit Gochar house results BPHS"),
    ("rahu_ketu_transit",           "Rahu Ketu transit Gochar effects BPHS"),

    # ── ASTROCARTOGRAPHY ─────────────────────────────────────────────────────
    ("relocated_lagna_effects",     "relocated lagna planet angular house effects BPHS"),
    ("planet_on_angle_relocated",   "planet on ascendant midheaven descendant IC relocated chart Vedic"),
]


def build(dry_run: bool = False) -> None:
    total = len(TOPICS)
    fetched = 0
    skipped = 0
    failed = 0

    print(f"Building BPHS knowledge base — {total} topics\n")

    for i, (key, query) in enumerate(TOPICS, 1):
        prefix = f"[{i:02d}/{total}]"

        if get_learned(key) is not None:
            print(f"{prefix} SKIP (already learned): {key}")
            skipped += 1
            continue

        if dry_run:
            print(f"{prefix} DRY RUN: would fetch '{query}'")
            continue

        print(f"{prefix} Fetching: {key}")
        try:
            passages = get_or_fetch(key, query, k=5)
            if passages:
                print(f"         -> {len(passages)} passages encoded into learned.py")
                fetched += 1
            else:
                print(f"         -> No results returned (API may be throttled)")
                failed += 1
        except Exception as e:
            print(f"         -> ERROR: {e}")
            failed += 1

        # Free tier: 5/min → 12s delay. Premium (API key set): no delay needed.
        if not config.VEDASTRO_API_KEY:
            time.sleep(12)

    print(f"\nDone. Fetched: {fetched} | Skipped: {skipped} | Failed: {failed}")
    print("All results are permanently encoded in bphs_agent/knowledge/bphs_rules/learned.py")


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    build(dry_run=dry)
