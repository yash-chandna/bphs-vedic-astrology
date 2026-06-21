"""
Birth time rectification engine — BPHS-driven dasha inversion.

How it works
============
BPHS Ch. 46 anchors the Vimshottari dasha cycle entirely to Moon's sidereal
longitude at birth.  Moon moves ~0.549°/hour, so every candidate minute on the
birth date maps to a unique Moon longitude and therefore a unique dasha tree.

BPHS Ch. 11–15 (Bhava Phala) tells us which house governs each life-event type,
and hence which planet (the house lord in *that* candidate chart) should be running
as Mahadasha or Bhukti lord when the event occurred.

Algorithm
---------
1. Sweep every `resolution_minutes` of the birth date (local time 00:00–23:59).
2. For each candidate minute:
   a. Compute sidereal Moon longitude via pyswisseph.
   b. Compute sidereal Ascendant (lagna sign) via pyswisseph.
   c. Build the Vimshottari dasha tree (maha + bhukti) from Moon longitude.
   d. For each supplied LifeEvent:
        - Look up EVENT_HOUSES[event_type] → (primary_house, secondary_house,
          natural_karaka)
        - Derive the house lord(s) from the candidate lagna sign.
        - Score: 1.0 if event_date is in that planet's Mahadasha or Bhukti;
                 0.5 if it matches only the natural karaka (not the house lord).
   e. Total score = mean of per-event scores.
3. Keep candidates whose total score >= min_score.
4. Within the winning lagna window, do a 1-minute fine sweep to find the single
   best-scoring minute (highest score, and if tied, closest Moon longitude to the
   midpoint of the winning Moon arc).

No LLM is used for the core computation.  The skill wrapper calls the LLM only
to interpret the top candidates against BPHS appearance descriptions (Ch. 6–8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date, timedelta
from typing import Sequence

import swisseph as swe

from bphs_agent.chart.models import BirthData
from bphs_agent.knowledge.bphs_rules.dasha import (
    DASHA_SEQUENCE,
    MAHADASHA_YEARS,
    NAKSHATRA_LORDS,
    TOTAL_DASHA_YEARS,
    bhukti_years,
)
from bphs_agent.knowledge.bphs_rules.houses import SIGN_LORD, SIGNS

# ── BPHS event-type → house mapping ──────────────────────────────────────────
# (primary_house, secondary_house_or_None, natural_karaka_planet)
# Sources: BPHS Ch. 11–15 (Bhava Phala), Ch. 32 (Karaka), Ch. 47–50 (Dasha Phala)

EVENT_HOUSES: dict[str, tuple[int, int | None, str]] = {
    "marriage":          (7,  None, "Venus"),    # Ch. 7, Sl. 32–34
    "divorce":           (7,  None, "Venus"),
    "child_birth":       (5,  None, "Jupiter"),  # Ch. 5, Sl. 1–6
    "child_death":       (5,  None, "Jupiter"),
    "father_death":      (9,  None, "Sun"),      # Ch. 9, Sl. 11–14
    "mother_death":      (4,  None, "Moon"),     # Ch. 4, Sl. 1–4
    "career_start":      (10, 6,   "Sun"),       # Ch. 10, Sl. 5–9; 6th = service
    "career_loss":       (10, 6,   "Saturn"),
    "promotion":         (10, None, "Sun"),
    "business":          (7,  10,  "Mercury"),   # 7th = partnerships
    "property":          (4,  None, "Mars"),     # Ch. 4, Sl. 12–16
    "foreign_travel":    (12, 9,   "Rahu"),      # Ch. 12 + Ch. 9 long journeys
    "serious_illness":   (6,  8,   "Saturn"),    # Ch. 6 (disease), Ch. 8 (chronic)
    "surgery":           (8,  None, "Mars"),
    "accident":          (8,  None, "Mars"),
    "education":         (4,  5,   "Mercury"),   # 4th = schooling, 5th = intellect
    "graduation":        (4,  5,   "Jupiter"),
    "spiritual":         (9,  12,  "Jupiter"),   # Ch. 9 (dharma), Ch. 12 (moksha)
    "inheritance":       (8,  None, "Jupiter"),
    "financial_gain":    (11, 2,   "Jupiter"),   # Ch. 11 (gains), Ch. 2 (wealth)
    "financial_loss":    (12, 8,   "Saturn"),
    "legal":             (6,  None, "Saturn"),   # Ch. 6 (litigation)
    "sibling_event":     (3,  None, "Mars"),
    "relocation":        (4,  12,  "Rahu"),
}

# Human-readable labels for the CLI menu
EVENT_LABELS: dict[str, str] = {
    "marriage":        "Marriage / partnership",
    "divorce":         "Divorce / separation",
    "child_birth":     "Birth of child",
    "child_death":     "Death / loss of child",
    "father_death":    "Death / serious illness of father",
    "mother_death":    "Death / serious illness of mother",
    "career_start":    "Career start / new job",
    "career_loss":     "Job loss / forced career change",
    "promotion":       "Promotion / major career rise",
    "business":        "Business started / major partnership",
    "property":        "Property purchase / house",
    "foreign_travel":  "Foreign travel / relocation abroad",
    "serious_illness": "Serious illness",
    "surgery":         "Surgery / hospitalisation",
    "accident":        "Accident / injury",
    "education":       "Formal education milestone",
    "graduation":      "Graduation / degree completion",
    "spiritual":       "Spiritual initiation / renunciation",
    "inheritance":     "Inheritance / unexpected windfall",
    "financial_gain":  "Major financial gain",
    "financial_loss":  "Major financial loss / debt",
    "legal":           "Legal dispute / litigation",
    "sibling_event":   "Major event involving sibling",
    "relocation":      "Relocation / change of residence",
}

# ── helpers ───────────────────────────────────────────────────────────────────

_NAKSHATRA_SPAN = 360.0 / 27


def _tz_offset_hours(tz_str: str) -> float:
    s = 1 if tz_str[0] == "+" else -1
    parts = tz_str.replace(":", "")
    return s * (int(parts[1:3]) + int(parts[3:5]) / 60.0)


def _set_ayanamsa(ayanamsa: str) -> None:
    a = ayanamsa.upper()
    if a == "LAHIRI":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    elif a == "RAMAN":
        swe.set_sid_mode(swe.SIDM_RAMAN)
    else:
        swe.set_sid_mode(swe.SIDM_LAHIRI)


def _birth_jd(birth: BirthData, local_hour: float) -> float:
    dd, mm, yyyy = birth.date.split("/")
    ut = local_hour - _tz_offset_hours(birth.timezone)
    return swe.julday(int(yyyy), int(mm), int(dd), ut)


def _moon_lon(jd: float) -> float:
    result, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
    return result[0] % 360


def _lagna_sign(jd: float, lat: float, lon: float) -> str:
    ayan_val = swe.get_ayanamsa(jd)
    _cusps, ascmc = swe.houses(jd, lat, lon, b"W")
    asc_sid = (ascmc[0] - ayan_val) % 360
    return SIGNS[int(asc_sid / 30) % 12]


def _lagna_degree(jd: float, lat: float, lon: float) -> float:
    ayan_val = swe.get_ayanamsa(jd)
    _cusps, ascmc = swe.houses(jd, lat, lon, b"W")
    return (ascmc[0] - ayan_val) % 360


def _house_lord(lagna_sign: str, house_num: int) -> str:
    lagna_idx = SIGNS.index(lagna_sign)
    sign_idx = (lagna_idx + house_num - 1) % 12
    return SIGN_LORD[SIGNS[sign_idx]]


# ── Vimshottari dasha tree ────────────────────────────────────────────────────

@dataclass
class DashaPeriod:
    lord: str
    start: _date
    end: _date
    level: int          # 1 = maha, 2 = bhukti
    parent: str = ""


def _build_dasha_tree(birth_date: _date, moon_lon: float) -> list[DashaPeriod]:
    nak_idx = int(moon_lon / _NAKSHATRA_SPAN) % 27
    first_lord = NAKSHATRA_LORDS[nak_idx]
    fraction_done = (moon_lon % _NAKSHATRA_SPAN) / _NAKSHATRA_SPAN
    years_elapsed = fraction_done * MAHADASHA_YEARS[first_lord]
    remaining_first = MAHADASHA_YEARS[first_lord] - years_elapsed

    seq_idx = DASHA_SEQUENCE.index(first_lord)
    periods: list[DashaPeriod] = []
    cutoff = birth_date + timedelta(days=120 * 365.25)
    current = birth_date

    def _add(lord: str, start: _date, dur_years: float) -> _date:
        end = start + timedelta(days=dur_years * 365.25)
        end = min(end, cutoff)
        periods.append(DashaPeriod(lord=lord, start=start, end=end, level=1))
        bhu_start = start
        bhi = DASHA_SEQUENCE.index(lord)
        for i in range(9):
            bl = DASHA_SEQUENCE[(bhi + i) % 9]
            bd = bhukti_years(lord, bl)
            be = bhu_start + timedelta(days=bd * 365.25)
            if bhu_start > cutoff:
                break
            periods.append(DashaPeriod(lord=bl, start=bhu_start, end=min(be, end), level=2, parent=lord))
            bhu_start = be
        return end

    end = _add(first_lord, current, remaining_first)
    current = end
    for i in range(1, 9):
        lord = DASHA_SEQUENCE[(seq_idx + i) % 9]
        if current > cutoff:
            break
        end = _add(lord, current, MAHADASHA_YEARS[lord])
        current = end

    return periods


def _dasha_balance_str(moon_lon: float, birth_date: _date) -> str:
    nak_idx = int(moon_lon / _NAKSHATRA_SPAN) % 27
    first_lord = NAKSHATRA_LORDS[nak_idx]
    fraction_done = (moon_lon % _NAKSHATRA_SPAN) / _NAKSHATRA_SPAN
    remaining = MAHADASHA_YEARS[first_lord] * (1 - fraction_done)
    y = int(remaining)
    m = int((remaining - y) * 12)
    d = int(((remaining - y) * 12 - m) * 30.44)
    return f"{y}y {m}m {d}d of {first_lord}"


# ── scoring ───────────────────────────────────────────────────────────────────

def _score_event(
    event_date: _date,
    event_type: str,
    lagna_sign: str,
    periods: list[DashaPeriod],
) -> float:
    """
    Return score in [0, 1] for a single event against the dasha tree.

    Scoring per BPHS Ch. 47–50:
      1.0  — event_date falls in Mahadasha of the primary house lord
      1.0  — event_date falls in Bhukti of the primary house lord
      0.75 — same for secondary house lord
      0.5  — matches only the natural karaka (not house lord)
      0.0  — no match
    """
    if event_type not in EVENT_HOUSES:
        return 0.0

    primary_h, secondary_h, karaka = EVENT_HOUSES[event_type]
    primary_lord = _house_lord(lagna_sign, primary_h)
    secondary_lord = _house_lord(lagna_sign, secondary_h) if secondary_h else None

    def _in_period(planet: str, level: int) -> bool:
        for p in periods:
            if p.lord == planet and p.level == level and p.start <= event_date <= p.end:
                return True
        return False

    if _in_period(primary_lord, 1) or _in_period(primary_lord, 2):
        return 1.0
    if secondary_lord and (_in_period(secondary_lord, 1) or _in_period(secondary_lord, 2)):
        return 0.75
    if _in_period(karaka, 1) or _in_period(karaka, 2):
        return 0.5
    return 0.0


# ── public API ────────────────────────────────────────────────────────────────

@dataclass
class LifeEvent:
    """
    A known life event.  event_type must be a key from EVENT_HOUSES.
    The engine derives the expected dasha lord from the candidate lagna — the
    user never needs to specify a planet manually.
    """
    description: str        # free-text label shown in output
    event_date: _date
    event_type: str         # key from EVENT_HOUSES / EVENT_LABELS


@dataclass
class CandidateTime:
    local_time: str          # HH:MM
    lagna_sign: str
    lagna_lon: float         # full sidereal longitude of ascendant (for fine ordering)
    moon_lon: float
    moon_nakshatra: str
    moon_nakshatra_lord: str
    dasha_balance: str
    event_scores: list[float]   # per-event score (same order as input events)
    total_score: float
    periods: list[DashaPeriod] = field(default_factory=list, repr=False)

    @property
    def events_matched(self) -> int:
        return sum(1 for s in self.event_scores if s >= 1.0)

    @property
    def events_total(self) -> int:
        return len(self.event_scores)


def find_birth_time(
    birth: BirthData,
    events: Sequence[LifeEvent],
    known_lagna: str | None = None,
    resolution_minutes: int = 4,
    min_score: float = 1.0,
) -> list[CandidateTime]:
    """
    Sweep the birth date and return candidate birth times consistent with events.

    After the coarse sweep, if any lagna window contains the best score, the
    function does a 1-minute fine sweep within that window to pin the closest time.

    Returns candidates sorted by total_score descending, then local_time ascending.
    """
    _set_ayanamsa(birth.ayanamsa)

    dd, mm, yyyy = birth.date.split("/")
    birth_date = _date(int(yyyy), int(mm), int(dd))

    from bphs_agent.chart.ephemeris import NAKSHATRAS

    def _candidate(local_minutes: int) -> CandidateTime | None:
        local_hour = local_minutes / 60.0
        jd = _birth_jd(birth, local_hour)
        m_lon = _moon_lon(jd)
        lagna = _lagna_sign(jd, birth.latitude, birth.longitude)
        l_lon = _lagna_degree(jd, birth.latitude, birth.longitude)

        if known_lagna and lagna != known_lagna:
            return None

        periods = _build_dasha_tree(birth_date, m_lon)

        scores = [
            _score_event(e.event_date, e.event_type, lagna, periods)
            for e in events
        ] if events else [1.0]

        total = sum(scores) / len(scores)

        nak_idx = int(m_lon / _NAKSHATRA_SPAN) % 27
        hh, mm_part = divmod(local_minutes, 60)
        return CandidateTime(
            local_time=f"{hh:02d}:{mm_part:02d}",
            lagna_sign=lagna,
            lagna_lon=round(l_lon, 4),
            moon_lon=round(m_lon, 4),
            moon_nakshatra=NAKSHATRAS[nak_idx],
            moon_nakshatra_lord=NAKSHATRA_LORDS[nak_idx],
            dasha_balance=_dasha_balance_str(m_lon, birth_date),
            event_scores=scores,
            total_score=round(total, 4),
            periods=periods,
        )

    # ── coarse sweep ──────────────────────────────────────────────────────────
    steps = (24 * 60) // resolution_minutes
    coarse: list[CandidateTime] = []
    for step in range(steps):
        c = _candidate(step * resolution_minutes)
        if c is not None and c.total_score >= min_score:
            coarse.append(c)

    # Relax if nothing passed
    if not coarse and min_score > 0:
        best_score = 0.0
        for step in range(steps):
            c = _candidate(step * resolution_minutes)
            if c is not None:
                best_score = max(best_score, c.total_score)
        if best_score > 0:
            for step in range(steps):
                c = _candidate(step * resolution_minutes)
                if c is not None and c.total_score >= best_score - 1e-6:
                    coarse.append(c)

    if not coarse:
        return []

    # ── fine sweep within each lagna window that has the best score ───────────
    best_score = max(c.total_score for c in coarse)
    best_lagnas = {c.lagna_sign for c in coarse if c.total_score >= best_score - 1e-6}

    fine: list[CandidateTime] = []
    for step in range(24 * 60):          # every minute
        c = _candidate(step)
        if c is not None and c.lagna_sign in best_lagnas and c.total_score >= best_score - 1e-6:
            fine.append(c)

    result = fine if fine else coarse
    result.sort(key=lambda c: (-c.total_score, c.local_time))
    return result
