"""
North Indian diamond chart image reader.
Uses Claude Vision to extract planet placements from a chart image,
then returns a ChartData so all downstream skills work identically
regardless of whether data came from VedAstro or an image.
"""

from __future__ import annotations

import base64
from pathlib import Path

import anthropic

from bphs_agent import config
from bphs_agent.chart.models import BirthData, ChartData, HouseData, PlanetData
from bphs_agent.knowledge.bphs_rules.houses import SIGN_LORD, SIGNS
from bphs_agent.knowledge.bphs_rules.planets import OWN_SIGNS

# Abbreviated planet names seen in North Indian charts
ABBREV_MAP = {
    "su": "Sun",  "sun": "Sun",
    "mo": "Moon", "moon": "Moon",
    "ma": "Mars", "mar": "Mars",  "kuj": "Mars",
    "me": "Mercury", "mer": "Mercury", "bud": "Mercury",
    "ju": "Jupiter", "jup": "Jupiter", "gu": "Jupiter", "guru": "Jupiter",
    "ve": "Venus", "ven": "Venus", "shu": "Venus", "shuk": "Venus",
    "sa": "Saturn", "sat": "Saturn", "sha": "Saturn", "shani": "Saturn",
    "ra": "Rahu",   "rahu": "Rahu",
    "ke": "Ketu",   "ketu": "Ketu",
    "asc": "Lagna", "lag": "Lagna", "lagn": "Lagna", "lagna": "Lagna",
    "as": "Lagna",
}

_VISION_SYSTEM = """
You are a Vedic astrology chart parser. You will receive an image of a
North Indian horoscope chart (diamond/kite format with 12 triangular cells).

The North Indian chart has a FIXED HOUSE layout (not fixed signs):
- House 1 (Lagna) is always the TOP DIAMOND cell
- Counting clockwise: 1(top), 2(upper-right), 3(right), 4(lower-right),
  5(bottom-right), 6(bottom), 7(lower-left), 8(left), 9(upper-left),
  10(upper), 11(upper-left-corner), 12(upper-right-corner)

Wait — the standard North Indian layout clockwise from top:
Houses: 12(top-left), 1(top-center), 2(top-right), 3(right-top),
        4(right-bottom), 5(bottom-right), 6(bottom-center),
        7(bottom-left), 8(left-bottom), 9(left-top), 10(top-left-center), 11(?)

Actually use the most common North Indian layout:
The fixed house positions are:
  Top-center cell = House 1 (Ascendant/Lagna)
  Going CLOCKWISE from top: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12

Your task:
1. Identify the sign number or abbreviation written in each cell (if any).
   Signs: Ar=Aries, Ta=Taurus, Ge=Gemini, Ca=Cancer, Le=Leo, Vi=Virgo,
          Li=Libra, Sc=Scorpio, Sa=Sagittarius, Cp=Capricorn, Aq=Aquarius, Pi=Pisces
2. Identify which planets are in each cell.
   Planet abbreviations: Su=Sun, Mo=Moon, Ma=Mars, Me=Mercury, Ju/Gu=Jupiter,
                         Ve/Sh=Venus, Sa/Sha=Saturn, Ra=Rahu, Ke=Ketu,
                         As/Lag=Ascendant marker
3. Note the lagna sign (the sign number in the Ascendant cell).

Respond ONLY with a JSON object in this exact format (no prose):
{
  "lagna_sign": "<sign name or empty string>",
  "houses": {
    "1": {"sign": "<sign name>", "planets": ["Sun", "Mars", ...]},
    "2": {"sign": "<sign name>", "planets": [...]},
    ... all 12 houses ...
  },
  "notes": "<any ambiguities or illegible areas>"
}

If a cell is empty, include it with an empty planets list.
If you cannot read a cell clearly, include it with what you can see and note it.
"""


def _encode_image(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for the image."""
    suffix = path.suffix.lower()
    media = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media


def _normalise_planet(raw: str) -> str | None:
    """Map abbreviated name to canonical planet name."""
    return ABBREV_MAP.get(raw.strip().lower())


def read_chart_image(
    image_path: str | Path,
    birth: BirthData | None = None,
) -> ChartData:
    """
    Parse a North Indian chart image into ChartData.

    Args:
        image_path: Path to the chart image (JPG/PNG).
        birth: Optional BirthData for the native (used for context only;
               planetary positions come from the image).

    Returns:
        ChartData with planets and houses populated from the image.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Chart image not found: {path}")

    img_data, media_type = _encode_image(path)

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=config.COORDINATOR_MODEL,
        max_tokens=1024,
        system=_VISION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Parse this North Indian horoscope chart and return the JSON.",
                    },
                ],
            }
        ],
    )

    raw_text = msg.content[0].text.strip()

    # Extract JSON block if wrapped in markdown
    if "```" in raw_text:
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    import json
    parsed = json.loads(raw_text)

    lagna_sign = parsed.get("lagna_sign", "")
    house_data_raw = parsed.get("houses", {})

    # Build lagna sign index for house → sign mapping
    if lagna_sign and lagna_sign in SIGNS:
        lagna_idx = SIGNS.index(lagna_sign)
    else:
        lagna_idx = 0

    planets: dict[str, PlanetData] = {}
    houses: dict[int, HouseData] = {}

    for h_str, h_info in house_data_raw.items():
        h_num = int(h_str)
        sign = h_info.get("sign", "")
        if not sign and lagna_sign:
            sign = SIGNS[(lagna_idx + h_num - 1) % 12]

        raw_planets = h_info.get("planets", [])
        occupants = []
        for rp in raw_planets:
            canonical = _normalise_planet(rp)
            if canonical and canonical != "Lagna":
                occupants.append(canonical)

        lord = SIGN_LORD.get(sign, "")
        houses[h_num] = HouseData(
            number=h_num,
            sign=sign,
            lord=lord,
            occupants=occupants,
        )

        # Build PlanetData for each planet in this house
        for p_name in occupants:
            if p_name not in planets:
                ruled = []
                for own_sign in OWN_SIGNS.get(p_name, []):
                    if own_sign in SIGNS and lagna_sign in SIGNS:
                        li = SIGNS.index(lagna_sign)
                        hh = (SIGNS.index(own_sign) - li) % 12 + 1
                        ruled.append(hh)
                planets[p_name] = PlanetData(
                    name=p_name,
                    sign=sign,
                    house=h_num,
                    degree=0.0,
                    nakshatra="",
                    nakshatra_pada=1,
                    retrograde=False,
                    combust=False,
                    dignity="neutral",
                    sign_lord=lord,
                    house_lord_of=ruled,
                )

    dummy_birth = birth or BirthData(
        name="Unknown", date="01/01/1900", time="00:00",
        place="Unknown", latitude=0.0, longitude=0.0, timezone="+00:00",
    )

    return ChartData(
        birth=dummy_birth,
        planets=planets,
        houses=houses,
        source="image",
    )
