"""
BPHS Shadbala — six sources of planetary strength.
Sources: BPHS Ch. 27 (Shadbala), Ch. 28 (Ishta/Kashta Phala).

Shadbala is the primary BPHS framework for judging whether a planet
is strong enough to deliver its promised results. A planet may promise
a yoga but fail to produce it if its Shadbala is below the minimum.
"""

# ── 1. STHANA BALA (Positional strength) ─────────────────────────────────────
# Uccha Bala: max strength at exact exaltation degree, zero at debilitation degree
# Saptavargiya Bala: strength derived from position in 7 divisional charts (D1–D9)
# Ojha-Yugma Rasi-Amsa Bala: odd/even sign placement

STHANA_BALA_COMPONENTS = [
    "Uccha Bala (exaltation/debilitation)",
    "Saptavargiya Bala (7 divisional charts D1,D2,D3,D7,D9,D12,D30)",
    "Ojha-Yugma Rasi-Amsa Bala (odd/even sign strength for odd/even planets)",
    "Kendra Bala (angular house placement: kendra=full, succedent=half, cadent=quarter)",
    "Drekkana Bala (1st/2nd/3rd drekkana for Sun/Jupiter/Saturn gender rule)",
]

# Kendra Bala values (Rupas)
KENDRA_BALA = {
    "kendra": 60,       # houses 1, 4, 7, 10
    "succedent": 30,    # houses 2, 5, 8, 11
    "cadent": 15,       # houses 3, 6, 9, 12
}

def house_to_kendra_type(house: int) -> str:
    if house in [1, 4, 7, 10]:
        return "kendra"
    if house in [2, 5, 8, 11]:
        return "succedent"
    return "cadent"

# ── 2. DIG BALA (Directional strength) ───────────────────────────────────────
# Each planet is strongest in a specific house (directional strength house)
DIG_BALA_HOUSE = {
    "Sun":     10,   # strongest in 10th house
    "Moon":    4,    # 4th house
    "Mars":    10,   # 10th house
    "Mercury": 1,    # 1st house
    "Jupiter": 1,    # 1st house
    "Venus":   4,    # 4th house
    "Saturn":  7,    # 7th house
    "Rahu":    None,
    "Ketu":    None,
}

# ── 3. KALA BALA (Temporal strength) ─────────────────────────────────────────
# Multiple sub-components based on time of birth
KALA_BALA_COMPONENTS = [
    "Nathonnatha Bala (day/night: Sun, Jupiter, Venus strong in day; Moon, Mars, Saturn in night)",
    "Paksha Bala (Moon strong in bright fortnight; malefics in dark fortnight)",
    "Tribhaga Bala (day/night divided into thirds; each planet rules one third)",
    "Abda Bala (yearly lord based on birth year)",
    "Masa Bala (monthly lord)",
    "Vara Bala (weekday lord — that planet gets extra strength)",
    "Hora Bala (hourly planetary ruler)",
    "Ayana Bala (northern/southern course of Sun)",
    "Yuddha Bala (planetary war — planet with lower longitude loses strength)",
]

# Day/night rulership for Nathonnatha Bala
DAY_STRONG = ["Sun", "Jupiter", "Venus"]
NIGHT_STRONG = ["Moon", "Mars", "Saturn"]
# Mercury strong in both

# ── 4. CHESHTA BALA (Motional strength) ──────────────────────────────────────
# Based on apparent motion of planets
CHESHTA_BALA_NOTES = {
    "retrograde": "Retrograde planets get full Cheshta Bala (60 Rupas) — behave like exalted",
    "stationary": "Stationary (before/after retrograde) gets 30 Rupas",
    "direct_fast": "Fast direct motion gets 7.5 Rupas",
    "combustion": "Combust planets (within a few degrees of Sun) lose Cheshta Bala",
    "Sun_Moon": "Sun and Moon do not have Cheshta Bala; instead use Ayana/Paksha Bala",
}

# ── 5. NAISARGIKA BALA (Natural strength) ─────────────────────────────────────
# Fixed hierarchy — does not change with chart
NAISARGIKA_BALA_RUPAS = {
    "Sun":     60.0,
    "Moon":    51.43,
    "Venus":   42.86,
    "Jupiter": 34.29,
    "Mercury": 25.71,
    "Mars":    17.14,
    "Saturn":  8.57,
    "Rahu":    None,   # not included in classical Shadbala
    "Ketu":    None,
}

# ── 6. DRIK BALA (Aspectual strength) ────────────────────────────────────────
# Strength from aspects received: benefic aspects add, malefic aspects subtract
DRIK_BALA_NOTES = (
    "Full aspect from benefic = +15 Rupas. "
    "Full aspect from malefic = −15 Rupas. "
    "¾ aspect: ±11.25; ½ aspect: ±7.5; ¼ aspect: ±3.75."
)

# ── MINIMUM REQUIRED SHADBALA (Rupas) ────────────────────────────────────────
# Per BPHS — a planet below these values is considered weak
MINIMUM_SHADBALA = {
    "Sun":     390,
    "Moon":    360,
    "Mars":    300,
    "Mercury": 420,
    "Jupiter": 390,
    "Venus":   330,
    "Saturn":  300,
    "Rahu":    None,
    "Ketu":    None,
}

# ── ISHTA / KASHTA PHALA ──────────────────────────────────────────────────────
# Per BPHS Ch. 28
# Ishta Phala = benefic effect score (0–60); derived from Uchcha Bala and Cheshta Bala
# Kashta Phala = malefic/suffering score (0–60); inverse
ISHTA_KASHTA_NOTE = (
    "Ishta Phala = sqrt(Uccha Bala × Cheshta Bala). "
    "Kashta Phala = sqrt((60 − Uccha Bala) × (60 − Cheshta Bala)). "
    "High Ishta → planet delivers good results. "
    "High Kashta → planet causes suffering in its periods."
)

# ── BHAVA BALA (House strength) ───────────────────────────────────────────────
# Separate from Shadbala — measures how strong each house is
BHAVA_BALA_COMPONENTS = [
    "Bhavadhipati Bala (strength of house lord)",
    "Bhava Digbala (house angular position)",
    "Bhava Drishti Bala (aspects on the house cusp — benefics add, malefics subtract)",
]
