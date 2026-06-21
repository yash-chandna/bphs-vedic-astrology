"""
BPHS Vimshottari Dasha — sequence, years, and period fractions.
Sources: BPHS Ch. 46 (Vimshottari Dasha), Ch. 47–50 (Dasha Phala).

Total cycle = 120 years across 9 planets, ordered by nakshatra at birth (Moon's nakshatra).
"""

# fmt: off

# 27 nakshatras with their dasha lords (in nakshatra order, 1-indexed)
NAKSHATRA_LORDS = [
    "Ketu",     # 1  Ashwini
    "Venus",    # 2  Bharani
    "Sun",      # 3  Krittika
    "Moon",     # 4  Rohini
    "Mars",     # 5  Mrigashira
    "Rahu",     # 6  Ardra
    "Jupiter",  # 7  Punarvasu
    "Saturn",   # 8  Pushya
    "Mercury",  # 9  Ashlesha
    "Ketu",     # 10 Magha
    "Venus",    # 11 Purva Phalguni
    "Sun",      # 12 Uttara Phalguni
    "Moon",     # 13 Hasta
    "Mars",     # 14 Chitra
    "Rahu",     # 15 Swati
    "Jupiter",  # 16 Vishakha
    "Saturn",   # 17 Anuradha
    "Mercury",  # 18 Jyeshtha
    "Ketu",     # 19 Mula
    "Venus",    # 20 Purva Ashadha
    "Sun",      # 21 Uttara Ashadha
    "Moon",     # 22 Shravana
    "Mars",     # 23 Dhanishtha
    "Rahu",     # 24 Shatabhisha
    "Jupiter",  # 25 Purva Bhadrapada
    "Saturn",   # 26 Uttara Bhadrapada
    "Mercury",  # 27 Revati
]

# Vimshottari dasha sequence (starting from the Moon's birth nakshatra lord)
DASHA_SEQUENCE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Mahadasha durations in years
MAHADASHA_YEARS = {
    "Ketu":    7,
    "Venus":   20,
    "Sun":     6,
    "Moon":    10,
    "Mars":    7,
    "Rahu":    18,
    "Jupiter": 16,
    "Saturn":  19,
    "Mercury": 17,
}

TOTAL_DASHA_YEARS = sum(MAHADASHA_YEARS.values())  # 120

def bhukti_years(mahadasha_lord: str, bhukti_lord: str) -> float:
    """Sub-period duration = (Mahadasha years × Bhukti years) / 120."""
    return (MAHADASHA_YEARS[mahadasha_lord] * MAHADASHA_YEARS[bhukti_lord]) / TOTAL_DASHA_YEARS

def antaram_years(maha: str, bhukti: str, antara: str) -> float:
    """Antaram duration = Bhukti duration × (Antara years / 120)."""
    b = bhukti_years(maha, bhukti)
    return b * MAHADASHA_YEARS[antara] / TOTAL_DASHA_YEARS

# ── DASHA PHALA PRINCIPLES (BPHS Ch. 47–50) ──────────────────────────────────
# General interpretive rules for dasha lords — the RAG / SearchSourceText layer
# will add specific sloka-level detail. These are structural rules.

DASHA_GENERAL_PRINCIPLES = {
    "benefic_lord_in_kendra_trikona": (
        "When the dasha lord is a functional or natural benefic placed in a kendra or trikona, "
        "its period brings prosperity, health, and advancement per BPHS Ch. 47."
    ),
    "malefic_lord_in_dusthana": (
        "When the dasha lord is in a dusthana (6, 8, 12) or is a natural malefic owning a dusthana, "
        "its period may bring disease, obstacles, loss, or separation per BPHS Ch. 47."
    ),
    "dasha_lord_debilitated": (
        "A debilitated dasha lord (unless Neecha Bhanga applies) gives difficulty, "
        "frustration, and failure of significations during its period per BPHS Ch. 47."
    ),
    "dasha_lord_exalted_or_own": (
        "An exalted or own-sign dasha lord gives excellent results proportional to its "
        "Shadbala and house placement per BPHS Ch. 47."
    ),
    "dasha_lord_combust": (
        "A combust dasha lord loses strength and gives reduced results or confusion "
        "during its period per BPHS Ch. 47."
    ),
    "dasha_bhukti_enmity": (
        "When the Mahadasha and Antardasha lords are mutual enemies, the sub-period "
        "tends to bring conflict, contradiction, and mixed results per BPHS Ch. 49."
    ),
    "dasha_bhukti_friendship": (
        "When Mahadasha and Antardasha lords are friends or in the same sign/nakshatra, "
        "the sub-period gives synergistic, harmonious results per BPHS Ch. 49."
    ),
    "maraka_dasha": (
        "When the dasha lord is the lord of the 2nd or 7th house (Maraka), and the native "
        "is in the appropriate age window for death, serious health threats may arise "
        "per BPHS Ch. 44–45."
    ),
}

# ── DASHA LAGNA ───────────────────────────────────────────────────────────────
# The dasha lagna is the sign occupied by the dasha lord — treated as a temporary lagna.
# Houses are counted from the dasha lagna to give nuanced period predictions.
DASHA_LAGNA_NOTE = (
    "Per BPHS, each planet's dasha activates the house it sits in as a temporary lagna. "
    "Results are interpreted from both the natal lagna AND the dasha lagna."
)
