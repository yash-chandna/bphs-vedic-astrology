"""
Data models for birth data and chart data.
All downstream skills work with these models — format-agnostic
whether data comes from VedAstro API or chart image reader.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BirthData:
    name: str
    date: str           # DD/MM/YYYY
    time: str           # HH:MM (24h)
    place: str          # city name
    latitude: float
    longitude: float
    timezone: str       # +HH:MM or -HH:MM
    ayanamsa: str = "LAHIRI"

    def vedastro_std_time(self) -> str:
        """Format accepted by VedAstro API: 'HH:MM DD/MM/YYYY +HH:MM'"""
        return f"{self.time} {self.date} {self.timezone}"


@dataclass
class PlanetData:
    name: str           # Sun, Moon, Mars …
    sign: str           # Aries, Taurus …
    house: int          # 1–12
    degree: float       # 0–30 within the sign
    nakshatra: str
    nakshatra_pada: int  # 1–4
    retrograde: bool
    combust: bool
    dignity: str        # exalted / own / mooltrikona / friendly / neutral / enemy / debilitated
    sign_lord: str
    house_lord_of: list[int] = field(default_factory=list)  # which houses does this planet rule
    longitude: float = 0.0  # absolute sidereal longitude 0–360 (for dasha calculation)


@dataclass
class HouseData:
    number: int         # 1–12
    sign: str
    lord: str           # planet that rules this house
    occupants: list[str] = field(default_factory=list)   # planets in this house
    aspecting_planets: list[str] = field(default_factory=list)


@dataclass
class GeneralData:
    lagna_sign: str
    lagna_degree: float
    moon_sign: str
    moon_nakshatra: str
    sun_sign: str
    tithi: str
    weekday: str
    yoga: str           # panchanga yoga (not astrological yoga)
    karana: str
    ayanamsa_degree: float
    sunrise: str
    sunset: str


@dataclass
class AshtakvargaData:
    # Sarvashtakavarga: total bindus per sign (sign order Aries=0 … Pisces=11)
    sarva: list[int] = field(default_factory=lambda: [0] * 12)
    # Bhinnashtakavarga per planet: {planet: [bindus per sign]}
    bhinnas: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class DashaData:
    mahadasha: str
    mahadasha_end: str      # ISO date string
    bhukti: str
    bhukti_end: str
    antaram: str | None
    antaram_end: str | None
    # Full dasha tree as returned by VedAstro (raw list for detailed display)
    raw: list[dict] = field(default_factory=list)


@dataclass
class ChartData:
    birth: BirthData
    planets: dict[str, PlanetData]      # keyed by planet name
    houses: dict[int, HouseData]        # keyed by house number 1–12
    general: GeneralData | None = None
    ashtakvarga: AshtakvargaData | None = None
    dasha: DashaData | None = None
    # Divisional charts keyed by division string: "D9", "D10", etc.
    divisionals: dict[str, "ChartData"] = field(default_factory=dict)
    source: str = "vedastro"            # "vedastro" | "image"
