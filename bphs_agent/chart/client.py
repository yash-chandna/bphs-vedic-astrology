"""
VedAstro API wrapper — used ONLY for ephemeris / chart position data.
Interpretation is done by our skills using hardcoded BPHS rules, not
by VedAstro's prediction engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from bphs_agent import config
from bphs_agent.chart.models import (
    AshtakvargaData,
    BirthData,
    ChartData,
    DashaData,
    GeneralData,
    HouseData,
    PlanetData,
)
from bphs_agent.knowledge.bphs_rules.planets import EXALTATION, OWN_SIGNS, MOOLTRIKONA
from bphs_agent.knowledge.bphs_rules.houses import SIGN_LORD, SIGNS

BASE_URL = "https://api.vedastro.org/api"
PLANETS_LIST = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if config.VEDASTRO_API_KEY:
        h["x-api-key"] = config.VEDASTRO_API_KEY
    return h


def _time_body(birth: BirthData) -> dict:
    return {
        "Time": {
            "StdTime": birth.vedastro_std_time(),
            "Location": {
                "Name": birth.place,
                "Longitude": birth.longitude,
                "Latitude": birth.latitude,
            },
        },
        "Ayanamsa": birth.ayanamsa,
    }


def _time_path(birth: BirthData) -> str:
    """Build the GET URL time+location segment."""
    t = birth.vedastro_std_time()  # "HH:MM DD/MM/YYYY +HH:MM"
    parts = t.split()
    hhmm, date_str, tz = parts[0], parts[1], parts[2]
    dd, mm, yyyy = date_str.split("/")
    return f"{hhmm}/{dd}/{mm}/{yyyy}/{tz}/Location/{birth.place}/{birth.longitude}/{birth.latitude}/Ayanamsa/{birth.ayanamsa}"


def _get(calc: str, planet: str, birth: BirthData) -> dict:
    """GET /api/Calculate/{calc}/PlanetName/{planet}/Time/.../Location/.../Ayanamsa/..."""
    url = f"{BASE_URL}/Calculate/{calc}/PlanetName/{planet}/Time/{_time_path(birth)}"
    resp = httpx.get(url, headers=_headers(), timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("Status") != "Pass":
        raise RuntimeError(f"VedAstro GET error {calc}/{planet}: {data.get('Payload')}")
    return data["Payload"]


def _get_planet_raw(planet: str, birth: BirthData) -> dict:
    """Fetch all data for a single planet via GET AllPlanetData."""
    payload = _get("AllPlanetData", planet, birth)
    return payload.get("AllPlanetData", payload)


def _dignity(planet: str, sign: str, degree: float) -> str:
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return "exalted"
    deb_sign = {
        "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
        "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
        "Saturn": "Aries", "Rahu": "Sagittarius", "Ketu": "Gemini",
    }
    if deb_sign.get(planet) == sign:
        return "debilitated"
    mt = MOOLTRIKONA.get(planet)
    if mt and mt[0] == sign:
        lo, hi = mt[1]
        if lo <= degree <= hi:
            return "mooltrikona"
    if sign in OWN_SIGNS.get(planet, []):
        return "own"
    return "neutral"  # friend/enemy requires chart context; skills assess this


def _name_from(val) -> str:
    if isinstance(val, dict):
        return val.get("Name", "")
    return str(val) if val else ""


def _degree_from(sign_dict) -> float:
    if isinstance(sign_dict, dict):
        deg = sign_dict.get("DegreesIn", {})
        if isinstance(deg, dict):
            return float(deg.get("TotalDegrees", 0) or 0)
    return 0.0


def _parse_planet(raw: dict, lagna_sign: str) -> PlanetData:
    name = raw.get("Name", "")

    # VedAstro AllPlanetData structure: planet name is the key, data is nested dict
    # The raw dict here is the inner planet data dict
    rasi = raw.get("PlanetRasiD1Sign") or raw.get("RasiSign") or raw.get("Sign") or {}
    sign = _name_from(rasi)
    degree = _degree_from(rasi)

    house_raw = raw.get("HousePlanetOccupiesBasedOnSign") or raw.get("HousePlanetOccupiesBasedOnLongitudes") or raw.get("House", "House1")
    house = int(str(house_raw).replace("House", "") or 1) if house_raw else 1

    nak_raw = raw.get("PlanetConstellation") or raw.get("Nakshatra") or {}
    nakshatra = _name_from(nak_raw) if isinstance(nak_raw, dict) else str(nak_raw)
    pada = int(raw.get("NakshatraPada", raw.get("PlanetConstellationQuarter", 1)) or 1)

    def _to_bool(val) -> bool:
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() == "true"

    retro = _to_bool(raw.get("IsPlanetRetrograde", raw.get("IsRetrograde", False)))
    combust = _to_bool(raw.get("IsPlanetCombust", raw.get("IsCombust", False)))
    sign_lord = SIGN_LORD.get(sign, "")

    # Determine which houses this planet rules
    lagna_idx = SIGNS.index(lagna_sign) if lagna_sign in SIGNS else 0
    ruled = []
    for own_sign in OWN_SIGNS.get(name, []):
        if own_sign in SIGNS:
            h = (SIGNS.index(own_sign) - lagna_idx) % 12 + 1
            ruled.append(h)

    return PlanetData(
        name=name,
        sign=sign,
        house=house,
        degree=degree,
        nakshatra=nakshatra,
        nakshatra_pada=pada,
        retrograde=retro,
        combust=combust,
        dignity=_dignity(name, sign, degree),
        sign_lord=sign_lord,
        house_lord_of=ruled,
    )


def _post(endpoint: str, body: dict) -> dict:
    resp = httpx.post(
        f"{BASE_URL}/Calculate/{endpoint}",
        headers=_headers(),
        json=body,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("Status") != "Pass":
        raise RuntimeError(f"VedAstro error on {endpoint}: {data.get('Payload')}")
    return data["Payload"]


def _try_general_data(body: dict) -> dict:
    """
    Try several VedAstro endpoints for general chart data (lagna, tithi, etc.).
    Different API tiers expose different endpoint names — fall back gracefully.
    """
    for endpoint in ("AllGeneralData", "GeneralAstroData", "HoroscopeData"):
        try:
            return _post(endpoint, body)
        except Exception:
            continue
    return {}


def get_full_chart(birth: BirthData) -> ChartData:
    """
    Compute a full Vedic chart.

    Primary: Swiss Ephemeris (pyswisseph) — offline, no rate limits, accurate.
    Fallback: VedAstro REST API (GET per planet, rate-limited at 5/min).
    """
    try:
        from bphs_agent.chart.ephemeris import get_chart as _se_chart
        return _se_chart(birth)
    except Exception as e:
        print(f"[chart] Swiss Ephemeris failed ({e}), falling back to VedAstro API")

    body = _time_body(birth)

    # Houses first (POST, 1 call, reliable)
    house_payload = _post("AllHouseData", {**body, "HouseName": "All"})

    # Derive lagna from house 1 immediately (needed for planet dignities/house lordship)
    lagna_sign = ""
    # AllHouseData: list of 12 single-key dicts [{"House1":{...}}, {"House2":{...}}, ...]
    h_dict_raw: dict = {}
    if isinstance(house_payload, dict) and "AllHouseData" in house_payload:
        all_h = house_payload["AllHouseData"]
        if isinstance(all_h, list):
            for item in all_h:
                if isinstance(item, dict):
                    h_dict_raw.update(item)
    elif isinstance(house_payload, dict):
        h_dict_raw = house_payload

    h1 = h_dict_raw.get("House1", {})
    if h1:
        sign_raw = h1.get("HouseRasiSign") or h1.get("Sign") or {}
        lagna_sign = (sign_raw.get("Name", "") if isinstance(sign_raw, dict) else str(sign_raw)).strip()

    # Planets: GET AllPlanetData per planet (9 calls, each returns full data dict)
    planets: dict[str, PlanetData] = {}
    for p_name in PLANETS_LIST:
        try:
            raw = _get_planet_raw(p_name, birth)
            if "Name" not in raw:
                raw = {"Name": p_name, **raw}
            planets[p_name] = _parse_planet(raw, lagna_sign)
        except Exception as e:
            print(f"[chart] Warning: failed to fetch {p_name}: {e}")
            continue

    # Parse houses using already-extracted h_dict_raw
    houses: dict[int, HouseData] = {}
    for h_key, h_data in h_dict_raw.items():
        # h_key = "House1" … "House12"
        try:
            num = int(h_key.replace("House", ""))
        except ValueError:
            continue
        if not isinstance(h_data, dict):
            continue

        rasi = h_data.get("HouseRasiSign") or h_data.get("Sign") or {}
        sign = rasi.get("Name", "") if isinstance(rasi, dict) else str(rasi)

        lord_raw = h_data.get("LordOfHouse") or {}
        lord = lord_raw.get("Name", "") if isinstance(lord_raw, dict) else SIGN_LORD.get(sign, "")

        occupants_raw = h_data.get("PlanetsInHouseBasedOnSign") or h_data.get("PlanetsInHouseBasedOnLongitudes") or []
        occupants = [p if isinstance(p, str) else p.get("Name", "") for p in occupants_raw if p]

        benefic_asp = h_data.get("BeneficPlanetsAspectingHouse") or []
        malefic_asp = h_data.get("AllPlanetsInBadAspectToHouse") or []
        aspecting = list({(p if isinstance(p, str) else p.get("Name", "")) for p in benefic_asp + malefic_asp if p})

        # Fallback occupants from planet house numbers if VedAstro list is empty
        if not occupants:
            occupants = [p for p, pd in planets.items() if pd.house == num]

        houses[num] = HouseData(
            number=num,
            sign=sign,
            lord=lord,
            occupants=occupants,
            aspecting_planets=aspecting,
        )

    # Fallback lagna from parsed houses
    if not lagna_sign and 1 in houses:
        lagna_sign = houses[1].sign

    moon_pd = planets.get("Moon")
    sun_pd = planets.get("Sun")

    general = GeneralData(
        lagna_sign=lagna_sign,
        lagna_degree=0.0,
        moon_sign=moon_pd.sign if moon_pd else "",
        moon_nakshatra=moon_pd.nakshatra if moon_pd else "",
        sun_sign=sun_pd.sign if sun_pd else "",
        tithi="",
        weekday="",
        yoga="",
        karana="",
        ayanamsa_degree=0.0,
        sunrise="",
        sunset="",
    )

    # Ashtakvarga (best-effort — not all VedAstro plans return this)
    avarga = None
    try:
        av_payload = _post("AshtakvargaData", body)
        sarva = av_payload.get("SarvashtakavargaPoints", [0] * 12)
        bhinnas = {k: v for k, v in av_payload.items() if k != "SarvashtakavargaPoints" and isinstance(v, list)}
        avarga = AshtakvargaData(sarva=sarva, bhinnas=bhinnas)
    except Exception:
        pass

    return ChartData(
        birth=birth,
        planets=planets,
        houses=houses,
        general=general,
        ashtakvarga=avarga,
        source="vedastro",
    )


def _compute_dasha_local(birth: BirthData, moon_nak: str, moon_sign: str, moon_degree: float) -> DashaData:
    """
    Compute Vimshottari dasha entirely from local BPHS rules (BPHS Ch. 46).
    Uses Moon nakshatra + degree to find elapsed fraction at birth.
    """
    from bphs_agent.knowledge.bphs_rules.dasha import (
        NAKSHATRA_LORDS, DASHA_SEQUENCE, MAHADASHA_YEARS, bhukti_years, antaram_years
    )

    # Nakshatra names in order (27 nakshatras)
    NAKSHATRA_NAMES = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushyami", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyesta",
        "Mula", "Poorvashada", "Uttarashada", "Sravana", "Dhanishta", "Shatabhisha",
        "Poorvabhadra", "Uttara Bhadrapada", "Revati",
    ]
    # Alternate spellings map
    NAK_ALIASES = {
        "Jyeshtha": "Jyesta", "Jyestha": "Jyesta",
        "Uttara Ashadha": "Uttarashada", "Purva Ashadha": "Poorvashada",
        "Poorvabhadra": "Poorvabhadra", "Purva Bhadrapada": "Poorvabhadra",
        "Uttara Bhadra": "Uttara Bhadrapada",
        "Shravana": "Sravana", "Shravan": "Sravana",
        "Dhanishtha": "Dhanishta",
        "Ashlesha": "Ashlesha",
        "Aswini": "Ashwini", "Aswani": "Ashwini",
        "Pushya": "Pushyami",
    }
    nak_norm = NAK_ALIASES.get(moon_nak, moon_nak)
    try:
        nak_idx = NAKSHATRA_NAMES.index(nak_norm)
    except ValueError:
        # Fuzzy match first word
        for i, n in enumerate(NAKSHATRA_NAMES):
            if n.lower().startswith(moon_nak.lower().split()[0]):
                nak_idx = i
                break
        else:
            nak_idx = 0

    birth_lord = NAKSHATRA_LORDS[nak_idx]

    # Degree within nakshatra (each = 13°20' = 13.333...°)
    nak_span = 360.0 / 27
    # Moon degree in nakshatra (0-indexed position within the nakshatra)
    deg_in_nak = moon_degree % nak_span
    elapsed_fraction = deg_in_nak / nak_span

    # Remaining fraction of birth nakshatra's dasha at birth
    birth_lord_years = MAHADASHA_YEARS[birth_lord]
    remaining_at_birth = birth_lord_years * (1 - elapsed_fraction)

    # Parse birth date
    from datetime import date, timedelta as td
    dd, mm, yyyy = birth.date.split("/")
    birth_date = date(int(yyyy), int(mm), int(dd))

    # Build the full dasha sequence starting from birth_lord
    seq_start_idx = DASHA_SEQUENCE.index(birth_lord)
    dasha_periods = []
    current_date = birth_date
    # First dasha: only the remaining portion
    first_end = birth_date + td(days=int(remaining_at_birth * 365.25))
    dasha_periods.append((birth_lord, birth_date, first_end))
    current_date = first_end
    # Subsequent dashas: full periods
    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(seq_start_idx + i) % 9]
        yrs = MAHADASHA_YEARS[lord]
        end_d = current_date + td(days=int(yrs * 365.25))
        dasha_periods.append((lord, current_date, end_d))
        current_date = end_d

    today = datetime.today().date()

    # Find current mahadasha
    maha = bhu = ant = ""
    maha_end = bhu_end = ant_end = ""
    for lord, start_d, end_d in dasha_periods:
        if start_d <= today <= end_d:
            maha = lord
            maha_end = end_d.strftime("%d/%m/%Y")
            # Bhukti periods within this mahadasha
            bhu_start = start_d
            for b_lord in DASHA_SEQUENCE[DASHA_SEQUENCE.index(lord):] + DASHA_SEQUENCE[:DASHA_SEQUENCE.index(lord)]:
                b_yrs = bhukti_years(lord, b_lord)
                b_end = bhu_start + td(days=int(b_yrs * 365.25))
                if bhu_start <= today <= b_end:
                    bhu = b_lord
                    bhu_end = b_end.strftime("%d/%m/%Y")
                    # Antaram
                    ant_start = bhu_start
                    for a_lord in DASHA_SEQUENCE[DASHA_SEQUENCE.index(b_lord):] + DASHA_SEQUENCE[:DASHA_SEQUENCE.index(b_lord)]:
                        a_yrs = antaram_years(lord, b_lord, a_lord)
                        a_end = ant_start + td(days=int(a_yrs * 365.25))
                        if ant_start <= today <= a_end:
                            ant = a_lord
                            ant_end = a_end.strftime("%d/%m/%Y")
                            break
                        ant_start = a_end
                    break
                bhu_start = b_end
            break

    # Build raw list for reference
    raw = [{"Lord": l, "StartTime": s.strftime("%d/%m/%Y"), "EndTime": e.strftime("%d/%m/%Y")}
           for l, s, e in dasha_periods]

    return DashaData(
        mahadasha=maha, mahadasha_end=maha_end,
        bhukti=bhu, bhukti_end=bhu_end,
        antaram=ant or None, antaram_end=ant_end or None,
        raw=raw,
    )


def get_dasha(birth: BirthData, moon_nak: str = "", moon_sign: str = "", moon_degree: float = 0.0,
              start: str | None = None, end: str | None = None) -> DashaData:
    """
    Compute Vimshottari dasha locally from Moon nakshatra (BPHS Ch. 46).
    moon_nak, moon_sign, moon_degree come from get_full_chart() planet data.
    Falls back to empty DashaData if nakshatra is unknown.
    """
    if moon_nak:
        return _compute_dasha_local(birth, moon_nak, moon_sign, moon_degree)
    return DashaData(mahadasha="", mahadasha_end="", bhukti="", bhukti_end="",
                     antaram=None, antaram_end=None, raw=[])


def get_divisional_chart(birth: BirthData, division: str) -> ChartData:
    """
    Fetch a divisional chart (D9, D10, etc.).
    Returns a ChartData with planets only (no house/general data for divisionals).
    """
    body = {**_time_body(birth), "PlanetName": "All"}
    # VedAstro endpoint naming: PlanetRasiD9Sign, PlanetRasiD10Sign, etc.
    d_num = division.lstrip("D")
    endpoint = f"PlanetRasiD{d_num}Sign"

    try:
        payload = _post(endpoint, body)
    except Exception:
        return ChartData(birth=birth, planets={}, houses={}, source="vedastro")

    planet_list = payload if isinstance(payload, list) else list(payload.values())
    # For divisionals we don't know lagna easily without a separate call
    planets = {}
    for raw in planet_list:
        name = raw.get("Name", "")
        sign = raw.get("Sign", {}).get("Name", "") if isinstance(raw.get("Sign"), dict) else raw.get("Sign", "")
        if name and sign:
            planets[name] = PlanetData(
                name=name, sign=sign, house=0, degree=0.0,
                nakshatra="", nakshatra_pada=1,
                retrograde=False, combust=False,
                dignity=_dignity(name, sign, 0),
                sign_lord=SIGN_LORD.get(sign, ""),
                house_lord_of=[],
            )

    return ChartData(birth=birth, planets=planets, houses={}, source="vedastro")
