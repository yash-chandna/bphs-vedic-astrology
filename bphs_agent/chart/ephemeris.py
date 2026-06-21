"""
Swiss Ephemeris chart calculator — primary source for all planet/house positions.
Uses pyswisseph (Swiss Ephemeris) with Lahiri ayanamsa for Vedic astrology.

Replaces VedAstro REST API calls for planet positions. No rate limits, fully offline.
VedAstro is still used for: Ashtakvarga, transit data via MCP.
"""

from __future__ import annotations

from datetime import datetime, timezone

import swisseph as swe

from bphs_agent.chart.models import (
    BirthData,
    ChartData,
    DashaData,
    GeneralData,
    HouseData,
    PlanetData,
)
from bphs_agent.knowledge.bphs_rules.houses import SIGN_LORD, SIGNS
from bphs_agent.knowledge.bphs_rules.planets import EXALTATION, MOOLTRIKONA, OWN_SIGNS

# Swiss Ephemeris planet IDs
_SE_PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.MEAN_NODE,   # North Node (Rahu); Ketu = Rahu + 180°
}

# 27 Nakshatras in order
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushyami", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyesta", "Mula", "Poorvashada", "Uttarashada", "Sravana", "Dhanishta",
    "Shatabhisha", "Poorvabhadra", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]


def _to_jd(birth: BirthData) -> float:
    """Convert birth data to Julian Day Number (UT)."""
    dd, mm, yyyy = birth.date.split("/")
    hh, mn = birth.time.split(":")
    # Parse timezone offset "+05:30" or "-05:30"
    tz_str = birth.timezone.replace(":", "")
    sign = 1 if tz_str[0] == "+" else -1
    tz_h = int(tz_str[1:3])
    tz_m = int(tz_str[3:5])
    tz_offset = sign * (tz_h + tz_m / 60.0)

    local_hour = int(hh) + int(mn) / 60.0
    ut_hour = local_hour - tz_offset

    jd = swe.julday(int(yyyy), int(mm), int(dd), ut_hour)
    return jd


def _dignity(planet: str, sign: str, degree: float) -> str:
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return "exalted"
    deb = {
        "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
        "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
        "Saturn": "Aries", "Rahu": "Sagittarius", "Ketu": "Gemini",
    }
    if deb.get(planet) == sign:
        return "debilitated"
    mt = MOOLTRIKONA.get(planet)
    if mt and mt[0] == sign:
        lo, hi = mt[1]
        if lo <= degree <= hi:
            return "mooltrikona"
    if sign in OWN_SIGNS.get(planet, []):
        return "own"
    return "neutral"


def _lon_to_sign_deg(lon: float) -> tuple[str, float]:
    """Convert ecliptic longitude (0-360) to (sign_name, degree_in_sign)."""
    sign_idx = int(lon / 30) % 12
    deg_in_sign = lon % 30
    return SIGNS[sign_idx], deg_in_sign


def _nakshatra_pada(lon: float) -> tuple[str, int]:
    """Return (nakshatra_name, pada 1-4) for an ecliptic longitude."""
    nak_span = 360.0 / 27          # 13°20'
    pada_span = nak_span / 4       # 3°20'
    nak_idx = int(lon / nak_span) % 27
    pada = int((lon % nak_span) / pada_span) + 1
    return NAKSHATRAS[nak_idx], pada


def get_chart(birth: BirthData) -> ChartData:
    """
    Compute a full Vedic chart using Swiss Ephemeris.
    Returns ChartData with all 9 planets, 12 houses (Whole Sign), general data.
    """
    # Set Lahiri ayanamsa (or whichever is configured)
    aya = birth.ayanamsa.upper()
    if aya == "LAHIRI":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    elif aya == "RAMAN":
        swe.set_sid_mode(swe.SIDM_RAMAN)
    elif aya == "KP":
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
    else:
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    jd = _to_jd(birth)
    ayanamsa_val = swe.get_ayanamsa(jd)

    # Compute planet positions
    planets: dict[str, PlanetData] = {}
    planet_lons: dict[str, float] = {}

    for name, se_id in _SE_PLANETS.items():
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result, _ = swe.calc_ut(jd, se_id, flags)
        lon = result[0] % 360
        speed = result[3]  # deg/day; negative = retrograde
        planet_lons[name] = lon

    # Ketu = Rahu + 180
    rahu_lon = planet_lons["Rahu"]
    ketu_lon = (rahu_lon + 180.0) % 360
    planet_lons["Ketu"] = ketu_lon

    # Compute Lagna (Ascendant) using house cusps
    lat = birth.latitude
    lon_place = birth.longitude
    # Whole Sign houses: lagna sign = sign of ascendant
    cusps, ascmc = swe.houses(jd, lat, lon_place, b"W")  # W = Whole Sign
    # ascmc[0] = tropical ascendant; convert to sidereal
    asc_tropical = ascmc[0]
    asc_sidereal = (asc_tropical - ayanamsa_val) % 360
    lagna_sign, lagna_deg = _lon_to_sign_deg(asc_sidereal)
    lagna_sign_idx = SIGNS.index(lagna_sign)

    # Build planet data
    for name, lon in planet_lons.items():
        sign, deg = _lon_to_sign_deg(lon)
        nak, pada = _nakshatra_pada(lon)

        # House number in Whole Sign (1-indexed from Lagna)
        sign_idx = SIGNS.index(sign)
        house_num = (sign_idx - lagna_sign_idx) % 12 + 1

        # Retrograde: planets except Rahu/Ketu based on speed
        se_id = _SE_PLANETS.get(name)
        if name in ("Rahu", "Ketu"):
            retro = True  # always retrograde by convention in Vedic
        elif se_id is not None:
            flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
            result, _ = swe.calc_ut(jd, se_id, flags)
            retro = result[3] < 0
        else:
            retro = False

        # Combust: within orb of Sun (standard Vedic orbs)
        COMBUST_ORBS = {
            "Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11,
            "Venus": 10, "Saturn": 15,
        }
        sun_lon = planet_lons.get("Sun", 0)
        orb = COMBUST_ORBS.get(name, 0)
        if orb > 0:
            diff = abs(lon - sun_lon) % 360
            if diff > 180:
                diff = 360 - diff
            combust = diff <= orb
        else:
            combust = False

        # Ruled houses (signs this planet owns)
        ruled = []
        for own_sign in OWN_SIGNS.get(name, []):
            if own_sign in SIGNS:
                h = (SIGNS.index(own_sign) - lagna_sign_idx) % 12 + 1
                ruled.append(h)

        planets[name] = PlanetData(
            name=name,
            sign=sign,
            house=house_num,
            degree=round(deg, 4),
            nakshatra=nak,
            nakshatra_pada=pada,
            retrograde=retro,
            combust=combust,
            dignity=_dignity(name, sign, deg),
            sign_lord=SIGN_LORD.get(sign, ""),
            house_lord_of=ruled,
            longitude=round(lon, 4),
        )

    # Build Whole Sign houses
    houses: dict[int, HouseData] = {}
    for h_num in range(1, 13):
        sign_idx = (lagna_sign_idx + h_num - 1) % 12
        sign = SIGNS[sign_idx]
        lord = SIGN_LORD.get(sign, "")
        occupants = [p for p, pd in planets.items() if pd.house == h_num]
        houses[h_num] = HouseData(
            number=h_num,
            sign=sign,
            lord=lord,
            occupants=occupants,
            aspecting_planets=[],
        )

    moon_pd = planets.get("Moon")
    sun_pd = planets.get("Sun")

    general = GeneralData(
        lagna_sign=lagna_sign,
        lagna_degree=round(lagna_deg, 4),
        moon_sign=moon_pd.sign if moon_pd else "",
        moon_nakshatra=moon_pd.nakshatra if moon_pd else "",
        sun_sign=sun_pd.sign if sun_pd else "",
        tithi="",
        weekday="",
        yoga="",
        karana="",
        ayanamsa_degree=round(ayanamsa_val, 4),
        sunrise="",
        sunset="",
    )

    return ChartData(
        birth=birth,
        planets=planets,
        houses=houses,
        general=general,
        ashtakvarga=None,
        source="swisseph",
    )


def get_current_positions(ayanamsa: str = "LAHIRI") -> dict[str, str]:
    """Return current transit signs for all 9 planets."""
    now = datetime.now(timezone.utc)
    transit = BirthData(
        name="_transit",
        date=now.strftime("%d/%m/%Y"),
        time=now.strftime("%H:%M"),
        place="Greenwich",
        latitude=51.48,
        longitude=0.0,
        timezone="+00:00",
        ayanamsa=ayanamsa,
    )
    chart = get_chart(transit)
    return {name: pd.sign for name, pd in chart.planets.items()}
